#!/usr/bin/env python3
"""Pull USD/NGN exchange rates into Cloudflare KV for nairaview.com.

Sources:
  - Official rate: Frankfurter API (free, no key) -> https://api.frankfurter.dev/v2/rate/USD/NGN
  - Parallel (street) rate: Monierate API when MONIERATE_TOKEN is set,
    otherwise scraped from abokiforex.app (static HTML, no JS needed).

Usage:
    pull_fx.py pull     # fetch both rates -> KV (fx:latest, fx:hist)
    pull_fx.py latest   # print what /api/fx would serve (from KV)

KV keys read by the API worker:
    fx:latest  - {"official": 1329.04, "official_date": "2026-10-04",
                  "parallel": 1365, "parallel_updated_at": "2026-10-04T22:06:25Z",
                  "parallel_source": "abokiforex.app" | "monierate",
                  "pulled_at": "2026-10-04T22:10:00Z"}
    fx:hist    - [{"date": "2026-10-04", "official": 1329.04, "parallel": 1365}, ...]
                 one point per day, newest last, capped at 120.

Never invents numbers: if a source fails or parses to nothing, that leg is
left out and the failure is reported (the page renders "—" for missing legs).
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import (
    add_surrogate_to_request,
    ensure_allowed_url,
    read_json_response,
    DynamicCredentialError,
)

CF_API = "https://api.cloudflare.com/client/v4"
CF_HOSTS = ["api.cloudflare.com"]
CF_CRED = "custom.cloudflare"
CF_ACCOUNT = "78f7403e4711bd80041a4100bf94ca3b"
CF_KV_NS = "dce1bca7fcd34b3485791a2b3762974f"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

FRANKFURTER_URL = "https://api.frankfurter.dev/v2/rate/USD/NGN"
FRANKFURTER_HOSTS = ["api.frankfurter.dev"]
ABOKI_URL = ("https://abokiforex.app/currency-converter/"
             "black-market-usd-dollars-to-naira-rate")
ABOKI_HOSTS = ["abokiforex.app"]
MONIERATE_URL = "https://api.monierate.com/v1/rates?from=USD&to=NGN"
MONIERATE_HOSTS = ["api.monierate.com"]


def http_get(url, hosts, headers=None, timeout=40):
    ensure_allowed_url(url, hosts)
    merged = {"User-Agent": UA}
    merged.update(headers or {})
    req = urllib.request.Request(url, headers=merged)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_official():
    """Official USD/NGN from Frankfurter. Returns (rate, date) or (None, None)."""
    try:
        data = json.loads(http_get(FRANKFURTER_URL, FRANKFURTER_HOSTS,
                                   {"Accept": "application/json"}))
        rate = float(data["rate"])
        if rate > 0:
            return rate, data.get("date")
    except Exception as exc:  # noqa: BLE001 - never invent, just report
        print(f"official fetch failed: {exc}", file=sys.stderr)
    return None, None


def fetch_parallel_monierate(token):
    """Parallel USD/NGN from Monierate. Returns (rate, updated_at) or (None, None)."""
    try:
        data = json.loads(http_get(
            MONIERATE_URL, MONIERATE_HOSTS,
            {"Accept": "application/json",
             "Authorization": f"Bearer {token}"}))
        # payload: {"data": {"attributes": {"rate": ..., "updated_at": ...}}}
        attrs = data.get("data", {}).get("attributes", data)
        rate = float(attrs.get("rate") or attrs.get("mid") or 0)
        if rate > 0:
            return rate, attrs.get("updated_at")
    except Exception as exc:  # noqa: BLE001
        print(f"monierate fetch failed: {exc}", file=sys.stderr)
    return None, None


def fetch_parallel_aboki():
    """Parallel USD/NGN scraped from abokiforex.app. Returns (rate, updated_at)."""
    try:
        html = http_get(ABOKI_URL, ABOKI_HOSTS)
        m = re.search(r"1 US Dollar equals <strong>([\d,]+) Naira</strong>", html)
        if not m:
            print("aboki parse: rate pattern not found", file=sys.stderr)
            return None, None
        rate = float(m.group(1).replace(",", ""))
        tm = re.search(r'<time datetime="([^"]+)"', html)
        updated = tm.group(1) if tm else None
        if rate > 0:
            return rate, updated
    except Exception as exc:  # noqa: BLE001
        print(f"aboki fetch failed: {exc}", file=sys.stderr)
    return None, None


def kv_put(key: str, value: str, ttl: int = 172800) -> None:
    url = (f"{CF_API}/accounts/{CF_ACCOUNT}/storage/kv/namespaces/"
           f"{CF_KV_NS}/values/{key}?expiration_ttl={ttl}")
    ensure_allowed_url(url, CF_HOSTS)
    req = urllib.request.Request(url, data=value.encode("utf-8"), method="PUT",
                                 headers={"Content-Type": "text/plain"})
    add_surrogate_to_request(req, CF_CRED, allowed_hosts=CF_HOSTS)
    with urllib.request.urlopen(req, timeout=40) as resp:
        payload = read_json_response(resp)
    if not payload.get("success"):
        raise DynamicCredentialError(f"KV put {key} failed: {payload.get('errors')}")


def kv_get(key: str):
    url = (f"{CF_API}/accounts/{CF_ACCOUNT}/storage/kv/namespaces/"
           f"{CF_KV_NS}/values/{key}")
    ensure_allowed_url(url, CF_HOSTS)
    req = urllib.request.Request(url, method="GET")
    add_surrogate_to_request(req, CF_CRED, allowed_hosts=CF_HOSTS)
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def cmd_pull():
    now = datetime.now(timezone.utc)
    now_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    today = now.strftime("%Y-%m-%d")

    official, official_date = fetch_official()

    token = os.environ.get("MONIERATE_TOKEN", "").strip()
    if token:
        parallel, parallel_updated = fetch_parallel_monierate(token)
        parallel_source = "monierate"
    else:
        parallel, parallel_updated = fetch_parallel_aboki()
        parallel_source = "abokiforex.app"

    if official is None and parallel is None:
        print("both sources failed; nothing written", file=sys.stderr)
        sys.exit(1)

    latest = {
        "official": round(official, 2) if official else None,
        "official_date": official_date,
        "parallel": round(parallel, 2) if parallel else None,
        "parallel_updated_at": parallel_updated,
        "parallel_source": parallel_source,
        "pulled_at": now_iso,
    }
    kv_put("fx:latest", json.dumps(latest), ttl=172800)

    # accumulate one point per day
    hist = []
    raw = kv_get("fx:hist")
    if raw:
        try:
            hist = json.loads(raw)
        except json.JSONDecodeError:
            hist = []
    point = {"date": today,
             "official": round(official, 2) if official else None,
             "parallel": round(parallel, 2) if parallel else None}
    if hist and hist[-1].get("date") == today:
        # refresh today's point, preferring non-null legs
        prev = hist[-1]
        for leg in ("official", "parallel"):
            if point[leg] is None:
                point[leg] = prev.get(leg)
        hist[-1] = point
    else:
        hist.append(point)
    hist = hist[-120:]
    kv_put("fx:hist", json.dumps(hist), ttl=10368000)

    print(json.dumps(latest))


def cmd_latest():
    raw = kv_get("fx:latest")
    hist_raw = kv_get("fx:hist")
    print(json.dumps({
        "latest": json.loads(raw) if raw else None,
        "history_points": len(json.loads(hist_raw)) if hist_raw else 0,
    }, indent=2))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "pull"
    if cmd == "pull":
        cmd_pull()
    elif cmd == "latest":
        cmd_latest()
    else:
        print(f"unknown command: {cmd}", file=sys.stderr)
        sys.exit(2)
