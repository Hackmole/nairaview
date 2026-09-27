#!/usr/bin/env python3
"""Generate one SEO stock page per NGX feed ticker in stocks/{SYM}.html.
Skips pages that already exist (hand-built). Uses only real feed data;
every figure is labeled with its trade date. No invented fundamentals."""
import json, os, html, re
from datetime import datetime

ROOT = os.path.expanduser('~/workspace/nairaview')
ASSET_V = '20260927s'
ALIAS = {'GUARANTY': 'GTCO', 'ACCESS': 'ACCESSCORP', 'TOTALNG': 'TOTAL', 'CCNN': 'BUACEMENT'}
LOGOS = set(f[:-4] for f in os.listdir(os.path.join(ROOT, 'assets', 'logos')) if f.endswith('.png'))
PALETTE = ['#1d4ed8', '#0e7490', '#0f766e', '#15803d', '#4d7c0f', '#a16207',
           '#b45309', '#b91c1c', '#be123c', '#7c3aed', '#6d28d9', '#0c4a6e']

d = json.load(open('/tmp/prices.json'))
stocks = d['stocks']['stocks']
trade_date = '25 Sep 2026'

def esc(t):
    return html.escape(str(t), quote=True)

def fmt_price(p):
    return '₦' + format(float(p), ',.2f')

def fmt_pct(p):
    v = float(p or 0)
    return ('+' if v > 0 else '') + format(v, '.2f') + '%'

def fmt_int(n):
    try:
        return format(int(n), ',d')
    except (TypeError, ValueError):
        return '—'

def fmt_mcap(n):
    try:
        n = float(n)
    except (TypeError, ValueError):
        return '—'
    if n >= 1e12:
        return '₦' + format(n / 1e12, '.2f') + ' trillion'
    if n >= 1e9:
        return '₦' + format(n / 1e9, '.1f') + ' billion'
    if n >= 1e6:
        return '₦' + format(n / 1e6, '.1f') + ' million'
    return '₦' + format(n, ',.0f')

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
    v = float(p or 0)
    return '▲' if v > 0 else ('▼' if v < 0 else '■')

by_sector = {}
for s in stocks:
    by_sector.setdefault(s.get('sector') or 'Other', []).append(s)
for sec in by_sector:
    by_sector[sec].sort(key=lambda s: float(s.get('market_cap') or 0), reverse=True)

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
      <span>SNAPSHOT &middot; FRI 25 SEP 2026 &middot; WAT</span>
    </div>
    <main>
      <section class="section">
        <div class="section-heading">
          <p class="kicker">STOCK PAGE &middot; @@SECTOR@@ &middot; @@BOARD@@</p>
          <h1 class="stock-head-badged">@@BADGE@@@@H1@@</h1>
          <div class="stock-price">@@PRICE@@</div>
          <p class="asof">As of the @@TRADE_DATE@@ close &mdash; refreshed daily when the market feed updates. Confirm before acting.</p>
        </div>
        <h2 class="guide-h2">Key facts</h2>
        <div class="facts">
          <div class="fact"><span>Latest close</span><strong>@@PRICE@@</strong></div>
          <div class="fact"><span>Day change</span><strong>@@DAY_CHG@@</strong></div>
          <div class="fact"><span>7-day change</span><strong>@@W_CHG@@</strong></div>
          <div class="fact"><span>Volume</span><strong>@@VOLUME@@ shares</strong></div>
          <div class="fact"><span>Market cap</span><strong>@@MCAP@@</strong></div>
          <div class="fact"><span>Shares outstanding</span><strong>@@SHARES@@</strong></div>
        </div>
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
        <p class="guide-p">The chart above shows the last seven trading sessions. Use the <a href="../screener">stock screener</a> to compare @@SYM@@ against its sector peers.</p>
        <h3 class="guide-h3">Is @@SYM@@ a good investment?</h3>
        <p class="guide-p">Nairaview provides market data, not investment advice. Consider the company&rsquo;s financials, your goals and risk tolerance &mdash; and speak to a licensed adviser before deciding.</p>
        <h2 class="guide-h2">Related stocks</h2>
        <ul class="guide-list">
@@PEERS@@
          <li><a href="../stocks">All listed stocks</a></li>
          <li><a href="../screener">Stock screener</a></li>
        </ul>
        <p class="guide-p"><em>Figures from Nairaview&rsquo;s NGX daily-close feed, trade date @@TRADE_DATE@@. Not investment advice.</em></p>
      </section>
    </main>
    <footer class="footer"><strong>Nairaview</strong><span>Information, not investment advice.</span></footer>
  </div>
  <script src="../assets/data.js?v=@@V@@"></script>
  <script src="../assets/logos.js"></script>
  <script src="../assets/site.js?v=@@V@@"></script>
  <script src="../assets/live.js?v=@@V@@"></script>
  <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
  <!-- Cloudflare Web Analytics --><script defer src='https://static.cloudflareinsights.com/beacon.min.js' data-cf-beacon='{{"token": "a9f4136dd40547a7b1acca41e62cc7a5"}}'></script><!-- End Cloudflare Web Analytics -->
</body>
</html>
'''

made = []
for s in stocks:
    sym = s['symbol']
    out = os.path.join(ROOT, 'stocks', sym + '.html')
    if os.path.exists(out):
        continue
    name = s.get('name') or sym
    sector = s.get('sector') or 'Other'
    board = s.get('market') or 'Main Board'
    price = fmt_price(s.get('current_price'))
    day_chg = fmt_pct(s.get('change_percent')) + ' ' + arrow(s.get('change_percent'))
    w_chg = fmt_pct(s.get('pct_change_7d')) + ' ' + arrow(s.get('pct_change_7d'))
    volume = fmt_int(s.get('volume'))
    mcap = fmt_mcap(s.get('market_cap'))
    shares = fmt_int(s.get('shares_outstanding'))

    peers = [p for p in by_sector.get(sector, []) if p['symbol'] != sym][:6]
    peer_lis = '\n'.join(
        '          <li><a href="{p}.html">{ps} &mdash; {pn}</a></li>'.format(
            p=p['symbol'], ps=esc(p['symbol']), pn=esc(p.get('name') or p['symbol']))
        for p in peers)

    og_title = '%s — %s | Nairaview' % (sym, name)
    og_desc = ('%s (%s) share price %s (%s) at the %s close. 7-day change %s, market cap %s. '
               'Daily-close NGX data on Nairaview.' % (sym, name, price, day_chg, trade_date, w_chg, mcap))
    title = '%s Share Price Today (%s) | Nairaview' % (sym, name)
    meta_desc = ('%s (%s) share price is %s (%s) as of the %s NGX close. 7-day change %s, '
                 'market cap %s, %s sector. Updated daily on Nairaview.' % (
                     sym, name, price, day_chg, trade_date, w_chg, mcap, sector))
    h1 = '%s &mdash; %s' % (esc(sym), esc(name))

    faq = [
        ('What is the current %s share price?' % sym,
         '%s (%s) last closed at %s (%s on the day) on %s.' % (name, sym, price, day_chg, trade_date)),
        ('What sector is %s in?' % sym,
         '%s is listed on the NGX %s under the %s sector.' % (sym, board, sector)),
        ('Where can I see %s\u2019s recent price trend?' % sym,
         'Nairaview shows the last seven trading sessions for %s, updated after each NGX trading day.' % sym),
        ('Is %s a good investment?' % sym,
         'Nairaview provides market data, not investment advice. Speak to a licensed adviser before deciding.'),
    ]
    jsonld = json.dumps({
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        'mainEntity': [{'question': {'@type': 'Question', 'name': q},
                        'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faq],
    }, ensure_ascii=False, indent=2)

    vals = {'SYM': esc(sym), 'V': ASSET_V, 'TRADE_DATE': trade_date,
            'SECTOR': esc(sector), 'BOARD': esc(board), 'BADGE': badge(sym), 'H1': h1,
            'PRICE': price, 'DAY_CHG': esc(day_chg), 'W_CHG': esc(w_chg),
            'VOLUME': volume, 'MCAP': mcap, 'SHARES': shares,
            'NAME': esc(name), 'PEERS': peer_lis,
            'OG_TITLE': esc(og_title), 'OG_DESC': esc(og_desc),
            'TITLE': esc(title), 'META_DESC': esc(meta_desc), 'JSONLD': jsonld}
    page = TEMPLATE
    for kk, vv in vals.items():
        page = page.replace('@@' + kk + '@@', vv)
    with open(out, 'w') as f:
        f.write(page)
    made.append(sym)

# sitemap: add every generated page
sm = os.path.join(ROOT, 'sitemap.xml')
xml = open(sm).read()
new_urls = []
for sym in sorted(made):
    tag = '<url><loc>https://nairaview.com/stocks/%s</loc><priority>0.7</priority></url>' % sym
    if tag not in xml:
        new_urls.append('  ' + tag)
if new_urls:
    xml = xml.replace('</urlset>', '\n'.join(new_urls) + '\n</urlset>')
    open(sm, 'w').write(xml)

print('generated:', len(made))
print('sitemap urls added:', len(new_urls))
