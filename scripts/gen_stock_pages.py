#!/usr/bin/env python3
"""Generate one SEO stock page per NGX feed ticker in stocks/{SYM}.html.

Figma redesign pattern (quote hero, stat cards, price chart, dark footer).
Uses only real feed data; every figure is labeled with its trade date.
Trade date is derived from the feed itself (never hardcoded).
No invented fundamentals. Alias stubs (ACCESS/FBNH/GUARANTY) are preserved.
Curated external related-links are carried over per page.
"""
import json, os, html, re, urllib.request
from datetime import datetime

ROOT = os.path.expanduser('~/workspace/nairaview')
ASSET_V = '20261001c'
API = 'https://nairaview-api.meetomidiora.workers.dev'
SKIP = {'ACCESS', 'FBNH', 'GUARANTY'}  # ticker-alias redirect stubs
ALIAS = {'GUARANTY': 'GTCO', 'ACCESS': 'ACCESSCORP', 'TOTALNG': 'TOTAL', 'CCNN': 'BUACEMENT'}
LOGOS = set(f[:-4] for f in os.listdir(os.path.join(ROOT, 'assets', 'logos')) if f.endswith('.png'))
PALETTE = ['#1d4ed8', '#0e7490', '#0f766e', '#15803d', '#4d7c0f', '#a16207',
           '#b45309', '#b91c1c', '#be123c', '#7c3aed', '#6d28d9', '#0c4a6e']

def get_json(path, timeout=25):
    """Fetch JSON via curl (urllib hits IncompleteRead on large responses here)."""
    import subprocess
    out = subprocess.run(
        ['curl', '-s', '--retry', '2', '--max-time', str(timeout),
         '-H', 'User-Agent: nairaview-gen/1.0', API + path],
        capture_output=True, text=True, timeout=timeout + 10)
    return json.loads(out.stdout)

def fetch_prices():
    """Fetch /api/prices with retries; fall back to a fresh local snapshot."""
    last = None
    for _ in range(3):
        try:
            return get_json('/api/prices', timeout=45)
        except Exception as e:
            last = e
    fb = '/tmp/prices_feed.json'
    if os.path.exists(fb):
        print('API unreachable, using local snapshot', fb)
        return json.load(open(fb))
    raise last

print('fetching /api/prices ...')
d = fetch_prices()
inner = d['stocks'] if isinstance(d.get('stocks'), dict) else {}
stocks = inner.get('stocks', []) if isinstance(inner, dict) else []
raw_td = ((inner.get('market') or {}).get('trade_date')
          or inner.get('trade_date') or d.get('trade_date') or '')
try:
    dt = datetime.fromisoformat(str(raw_td).replace('Z', '+00:00'))
    trade_date = dt.strftime('%d %b %Y').lstrip('0')
    trade_iso = dt.strftime('%Y-%m-%d')
except Exception:
    trade_date = str(raw_td) or 'latest close'
    trade_iso = ''
print('trade_date:', trade_date, '| stocks:', len(stocks))

# carry over curated external related links from the pre-redesign pages (backup)
CURATED = {}
_backup = '/tmp/stocks_backup'
for sym in [s['symbol'] for s in stocks]:
    p = os.path.join(_backup, sym + '.html')
    if not os.path.exists(p):
        continue
    s = open(p).read()
    links = re.findall(r'<li><a href="(https?://[^"]+)"[^>]*>([^<]+)</a></li>', s)
    if links:
        CURATED[sym] = [(h, t) for h, t in links
                        if 'nairaview.com' not in h and not h.startswith('../')]
print('pages with curated links:', len(CURATED))

def esc(t):
    return html.escape(str(t), quote=True)

def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0

def fmt_price(p):
    return '₦' + format(fnum(p), ',.2f')

def fmt_pct(p):
    v = fnum(p)
    return ('+' if v > 0 else '') + format(v, '.2f') + '%'

def fmt_int(n):
    try:
        return format(int(float(n)), ',d')
    except (TypeError, ValueError):
        return '—'

def fmt_mcap(n):
    n = fnum(n)
    if n <= 0:
        return '—'
    if n >= 1e12:
        return '₦' + format(n / 1e12, '.2f') + ' trillion'
    if n >= 1e9:
        return '₦' + format(n / 1e9, '.1f') + ' billion'
    if n >= 1e6:
        return '₦' + format(n / 1e6, '.1f') + ' million'
    return '₦' + format(n, ',.0f')

def fmt_vol(n):
    n = fnum(n)
    if n <= 0:
        return '—'
    if n >= 1e9:
        return format(n / 1e9, '.2f') + 'bn'
    if n >= 1e6:
        return format(n / 1e6, '.1f') + 'm'
    return format(n, ',.0f')

def badge(sym):
    key = ALIAS.get(sym, sym)
    if key in LOGOS:
        return ('<span class="stk-badge lg stk-logo" aria-hidden="true">'
                '<img class="stk-img" data-sym="' + esc(sym) + '" data-size="lg" '
                'src="../assets/logos/' + esc(key) + '.png" alt="" loading="lazy"></span>')
    h = 0
    for ch in sym:
        h = (h * 31 + ord(ch)) % 997
    init = re.sub(r'[^A-Z0-9]', '', sym)[:2]
    return ('<span class="stk-badge lg" style="background:' + PALETTE[h % len(PALETTE)] +
            '" aria-hidden="true">' + esc(init) + '</span>')

def arrow(p):
    v = fnum(p)
    return '▲' if v > 0 else ('▼' if v < 0 else '■')

def chart_svg(sym, closes):
    """Build a simple SVG price chart from session closes (oldest -> newest)."""
    if len(closes) < 2:
        return ''
    w, h = 720, 260
    lo, hi = min(closes), max(closes)
    rng = (hi - lo) or 1
    n = len(closes)
    pts = []
    for i, v in enumerate(closes):
        x = 20 + (w - 40) * i / (n - 1)
        y = h - 24 - (h - 56) * (v - lo) / rng
        pts.append((x, y))
    dd = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts)
    up = closes[-1] >= closes[0]
    col = '#087A4B' if up else '#B43B3B'
    area = f'{dd} L{pts[-1][0]:.1f},{h-24} L{pts[0][0]:.1f},{h-24} Z'
    lx, ly = pts[-1]
    ret = (closes[-1] / closes[0] - 1) * 100
    return (f'<div class="price-chart-card"><div class="pc-head">'
            f'<span class="pc-title">Price history &middot; last {n} sessions</span>'
            f'<span class="pc-ret {"up" if up else "down"}">{ret:+.2f}%</span></div>'
            f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{esc(sym)} price chart, last {n} sessions">'
            f'<path d="{area}" fill="{col}" opacity="0.10"/>'
            f'<path d="{dd}" fill="none" stroke="{col}" stroke-width="2.5" stroke-linecap="round"/>'
            f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="5" fill="{col}" stroke="#fff" stroke-width="2.5"/>'
            f'</svg><div class="pc-note">Daily closes to {esc(trade_date)} &middot; not intraday</div></div>')

def footer():
    return '''    <footer class="site-footer">
      <div class="footer-inner">
        <div class="footer-grid">
          <div class="footer-brand">
            <a class="brand" href="../" aria-label="Nairaview home"><img src="../assets/logo-dark.svg" alt="Nairaview" height="34"></a>
            <p>The Nigerian Exchange, decoded daily. Prices, movers, offers and plain-language guides &mdash; built for first-time investors.</p>
          </div>
          <div class="footer-col">
            <h4>Markets</h4>
            <a href="../stocks">All listed stocks</a>
            <a href="../screener">Stock screener</a>
            <a href="../offers">Public offers</a>
            <a href="../calendar">Market calendar</a>
          </div>
          <div class="footer-col">
            <h4>Nairaview</h4>
            <a href="../news">Market news</a>
            <a href="../learn">Learn</a>
            <a href="../portfolio">Portfolio tracker</a>
            <a href="../market-recap">Weekly recap</a>
          </div>
        </div>
        <div class="footer-legal">
          <span>&copy; 2026 Nairaview. Information, not investment advice.</span>
          <span><a href="../account">Account</a></span>
        </div>
      </div>
      <div class="footer-disclaimer">Market data is delayed daily-close information from the Nigerian Exchange, provided for education only. Prices may have changed &mdash; confirm before acting.</div>
    </footer>'''

TEMPLATE = '''<!doctype html>
<html lang="en">
<head>
<script>try{var t=localStorage.getItem("nv-theme");if(t==="light"||t==="dark")document.documentElement.setAttribute("data-theme",t);}catch(e){}</script>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <meta name="color-scheme" content="light dark" />
  <meta name="theme-color" content="#087a4b" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="Nairaview" />
<meta property="og:title" content="@@OG_TITLE@@" />
<meta property="og:description" content="@@OG_DESC@@" />
<meta property="og:url" content="https://nairaview.com/stocks/@@SYM@@" />
<meta property="og:image" content="https://nairaview.com/assets/og-default.png" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="@@OG_TITLE@@" />
<meta name="twitter:description" content="@@OG_DESC@@" />
<meta name="twitter:image" content="https://nairaview.com/assets/og-default.png" />
<link rel="canonical" href="https://nairaview.com/stocks/@@SYM@@" />
  <meta name="description" content="@@META_DESC@@" />
  <link rel="icon" href="../assets/logo-icon.svg" type="image/svg+xml">
  <link rel="icon" href="../assets/favicon-32.png" sizes="32x32" type="image/png">
  <link rel="apple-touch-icon" href="../assets/apple-touch-icon.png">
  <title>@@TITLE@@</title>
  <link rel="stylesheet" href="../assets/styles.css?v=@@V@@" />
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Newsreader:opsz,wght@6..72,500;6..72,650&family=Public+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX"
     crossorigin="anonymous"></script>
<script type="application/ld+json">
@@JSONLD@@
</script>
</head>
<body>
  <header class="site-header">
    <div class="header-inner">
      <a class="brand" href="../" aria-label="Nairaview home"><picture><source srcset="../assets/logo-dark.svg" media="(prefers-color-scheme: dark)"><img src="../assets/logo.svg" alt="Nairaview" height="34"></picture></a>
      <nav class="site-nav" aria-label="Primary">
          <a href="../">Home</a>
          <a href="../stocks" class="active">Stocks</a>
          <a href="../screener">Screener</a>
          <a href="../offers">Offers</a>
          <a href="../calendar">Calendar</a>
          <a href="../news">News</a>
          <a href="../learn">Learn</a>
      </nav>
    </div>
  </header>
  <div class="shell">
    <div class="topline">
      <span class="status"><i class="status-dot" aria-hidden="true"></i> MARKET CLOSED</span>
      <span>DAILY CLOSE &middot; @@TRADE_DATE_UC@@ &middot; WAT</span>
    </div>
    <main>
      <nav class="crumbs" aria-label="Breadcrumb"><a href="../">Home</a><span class="sep">/</span><a href="../stocks">Stocks</a><span class="sep">/</span><span>@@SYM@@</span></nav>
      <div class="quote-hero">
        <div class="section-heading">
          <p class="kicker">Stock page &middot; @@SECTOR@@ &middot; @@BOARD@@</p>
          <div class="quote-top">
            <div class="quote-id">@@BADGE@@<div><h1>@@H1@@</h1><p class="sector-line">@@SECTOR@@ &middot; @@BOARD@@</p></div></div>
            <div><span class="status-pill"><span class="dot"></span>Daily close</span></div>
          </div>
          <div class="quote-price">@@PRICE@@</div>
          <div class="quote-chg @@CHG_CLASS@@">@@DAY_CHG@@</div>
          <p class="asof">As of the @@TRADE_DATE@@ close &mdash; refreshed daily when the market feed updates. Confirm before acting.</p>
        </div>
      </div>
      <div class="hstat-grid">
        <div class="hstat"><div class="k">7-day change</div><div class="v @@W_CLASS@@">@@W_CHG@@</div><div class="s">vs 7 days ago</div></div>
        <div class="hstat"><div class="k">Volume</div><div class="v">@@VOLUME@@</div><div class="s">shares traded</div></div>
        <div class="hstat"><div class="k">Market cap</div><div class="v">@@MCAP@@</div><div class="s">at latest close</div></div>
        <div class="hstat"><div class="k">Shares outstanding</div><div class="v">@@SHARES@@</div><div class="s">as reported</div></div>
      </div>
@@CHART@@
      <div class="section" style="padding-top:34px">
        <div class="ad-slot ad-leaderboard" aria-hidden="true">
          <div class="ad-label">Advertisement</div>
          <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-XXXXXXXXXXXXXXXX" data-ad-slot="1111111111" data-ad-format="auto" data-full-width-responsive="true"></ins>
        </div>
        <h2 class="guide-h2">How to buy @@SYM@@ shares</h2>
        <ol class="guide-list">
          <li>Open an account with a stockbroker licensed by the NGX.</li>
          <li>Fund your account and place a buy order for <strong>@@SYM@@</strong> (@@NAME@@) at your chosen price.</li>
          <li>Your shares are held electronically under your CSCS account.</li>
          <li>Track the position on Nairaview&rsquo;s <a href="../portfolio">portfolio tracker</a>.</li>
        </ol>
        <h2 class="guide-h2">Frequently asked questions</h2>
        <h3 class="guide-h3">What is the current @@SYM@@ share price?</h3>
        <p class="guide-p">@@NAME@@ (@@SYM@@) last closed at <strong>@@PRICE@@</strong> (@@DAY_CHG@@ on the day) on @@TRADE_DATE@@. Prices update here after each NGX trading session.</p>
        <h3 class="guide-h3">What sector is @@SYM@@ in?</h3>
        <p class="guide-p">@@SYM@@ is listed on the NGX @@BOARD@@ under the @@SECTOR@@ sector.</p>
        <h3 class="guide-h3">Where can I see @@SYM@@&rsquo;s recent price trend?</h3>
        <p class="guide-p">@@TREND_ANSWER@@</p>
        <h3 class="guide-h3">Is @@SYM@@ a good investment?</h3>
        <p class="guide-p">Nairaview provides market data, not investment advice. Consider the company&rsquo;s financials, your goals and risk tolerance &mdash; and speak to a licensed adviser before deciding.</p>
        <h2 class="guide-h2">Related stocks</h2>
        <ul class="guide-list">
@@PEERS@@
@@CURATED@@
          <li><a href="../stocks">All listed stocks</a></li>
          <li><a href="../screener">Stock screener</a></li>
        </ul>
        <p class="guide-p"><em>Figures from Nairaview&rsquo;s NGX daily-close feed, trade date @@TRADE_DATE@@. Not investment advice.</em></p>
      </div>
    </main>
  </div>
@@FOOTER@@
  <script src="../assets/data.js?v=@@V@@"></script>
  <script src="../assets/logos.js"></script>
  <script src="../assets/site.js?v=@@V@@"></script>
  <script src="../assets/live.js?v=@@V@@"></script>
  <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
  <!-- Cloudflare Web Analytics --><script defer src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{{"token": "a9f4136dd40547a7b1acca41e62cc7a5"}}'></script><!-- End Cloudflare Web Analytics -->
</body>
</html>
'''

by_sector = {}
for s in stocks:
    by_sector.setdefault(s.get('sector') or 'Other', []).append(s)
for sec in by_sector:
    by_sector[sec].sort(key=lambda s: fnum(s.get('market_cap')), reverse=True)

made, skipped, nochart = [], [], []
for s in stocks:
    sym = s['symbol']
    if sym in SKIP:
        skipped.append(sym)
        continue
    out = os.path.join(ROOT, 'stocks', sym + '.html')
    name = s.get('name') or sym
    sector = s.get('sector') or 'Other'
    board = s.get('market') or 'Main Board'
    price = fnum(s.get('current_price'))
    cp = fnum(s.get('change_percent'))
    prev = fnum(s.get('previous_close')) or (price / (1 + cp / 100) if cp != -100 else price)
    pts = price - prev
    day_chg = '%s %s (%s₦%s)' % (fmt_pct(cp), arrow(cp),
                                 '+' if pts > 0 else ('−' if pts < 0 else ''),
                                 format(abs(pts), ',.2f'))
    w = fnum(s.get('pct_change_7d'))
    w_chg = '%s %s' % (fmt_pct(w), arrow(w))
    volume = fmt_vol(s.get('volume'))
    mcap = fmt_mcap(s.get('market_cap'))
    shares = fmt_int(s.get('shares_outstanding'))

    # price history for the chart
    chart, trend_answer = '', ''
    try:
        h = get_json('/api/history?symbol=' + sym, timeout=15)
        closes = [p['close'] for p in (h.get('prices') or []) if p.get('close')]
        if len(closes) >= 2:
            chart = chart_svg(sym, closes[-9:])
            trend_answer = ('The chart above shows the last %d trading sessions. Use the '
                            '<a href="../screener">stock screener</a> to compare %s against '
                            'its sector peers.' % (min(len(closes), 9), sym))
    except Exception as e:
        pass
    if not chart:
        nochart.append(sym)
        trend_answer = ('Nairaview updates %s after each NGX trading day. Use the '
                        '<a href="../screener">stock screener</a> to compare %s against '
                        'its sector peers.' % (sym, sym))

    peers = [p for p in by_sector.get(sector, []) if p['symbol'] != sym][:6]
    peer_lis = '\n'.join(
        '          <li><a href="%s.html">%s &mdash; %s</a></li>' % (
            p['symbol'], esc(p['symbol']), esc(p.get('name') or p['symbol']))
        for p in peers)
    curated_lis = '\n'.join(
        '          <li><a href="%s" target="_blank" rel="noopener noreferrer">%s</a></li>' % (h, t)
        for h, t in CURATED.get(sym, []))

    og_title = '%s — %s | Nairaview' % (sym, name)
    og_desc = ('%s (%s) share price %s (%s) at the %s close. 7-day change %s, market cap %s. '
               'Daily-close NGX data on Nairaview.' % (sym, name, fmt_price(price), day_chg, trade_date, w_chg, mcap))
    title = '%s Share Price Today (%s) | Nairaview' % (sym, name)
    meta_desc = ('%s (%s) share price is %s (%s) as of the %s NGX close. 7-day change %s, '
                 'market cap %s, %s sector. Updated daily on Nairaview.' % (
                     sym, name, fmt_price(price), day_chg, trade_date, w_chg, mcap, sector))

    faq = [
        ('What is the current %s share price?' % sym,
         '%s (%s) last closed at %s (%s on the day) on %s.' % (name, sym, fmt_price(price), day_chg, trade_date)),
        ('What sector is %s in?' % sym,
         '%s is listed on the NGX %s under the %s sector.' % (sym, board, sector)),
        ('Where can I see %s\u2019s recent price trend?' % sym, trend_answer),
        ('Is %s a good investment?' % sym,
         'Nairaview provides market data, not investment advice. Speak to a licensed adviser before deciding.'),
    ]
    jsonld = json.dumps({
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        'mainEntity': [{'question': {'@type': 'Question', 'name': q},
                        'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faq],
    }, ensure_ascii=False, indent=2)

    vals = {'SYM': esc(sym), 'V': ASSET_V,
            'TRADE_DATE': trade_date, 'TRADE_DATE_UC': trade_date.upper(),
            'SECTOR': esc(sector), 'BOARD': esc(board), 'BADGE': badge(sym),
            'H1': '%s &mdash; %s' % (esc(sym), esc(name)),
            'PRICE': fmt_price(price),
            'DAY_CHG': esc(day_chg), 'CHG_CLASS': 'up' if cp > 0 else ('down' if cp < 0 else ''),
            'W_CHG': esc(w_chg), 'W_CLASS': 'up' if w > 0 else ('down' if w < 0 else ''),
            'VOLUME': volume, 'MCAP': mcap, 'SHARES': shares,
            'NAME': esc(name), 'PEERS': peer_lis, 'CURATED': curated_lis,
            'CHART': chart, 'TREND_ANSWER': trend_answer,
            'OG_TITLE': esc(og_title), 'OG_DESC': esc(og_desc),
            'TITLE': esc(title), 'META_DESC': esc(meta_desc), 'JSONLD': jsonld,
            'FOOTER': footer()}
    page = TEMPLATE
    for kk, vv in vals.items():
        page = page.replace('@@' + kk + '@@', vv)
    assert '@@' not in page, 'unreplaced placeholder in ' + sym
    with open(out, 'w') as fh:
        fh.write(page)
    made.append(sym)

print('generated:', len(made))
print('skipped (alias stubs):', skipped)
print('no chart data:', nochart)
