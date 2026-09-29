    /* ---- Per-stock icons: real company logos where we have them
       (assets/logos/{TICKER}.png, see window.NV_LOGOS), falling back to a
       deterministic two-letter monogram badge so no stock renders icon-less. ---- */
    (function stockBadges() {
      var PALETTE = ['#1d4ed8', '#0e7490', '#0f766e', '#15803d', '#4d7c0f', '#a16207',
                     '#b45309', '#b91c1c', '#be123c', '#7c3aed', '#6d28d9', '#0c4a6e'];
      function initials(sym) {
        var s = String(sym || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
        if (!s) return '?';
        return s.length <= 2 ? s : s.charAt(0) + s.charAt(1);
      }
      function colorFor(sym) {
        var s = String(sym || '').toUpperCase();
        var h = 0, i;
        for (i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 997;
        return PALETTE[h % PALETTE.length];
      }
      function monoHTML(sym, size) {
        var cls = 'stk-badge' + (size ? ' ' + size : '');
        return '<span class="' + cls + '" style="background:' + colorFor(sym) +
               '" aria-hidden="true">' + initials(sym) + '</span>';
      }
      window.nvMonoHTML = monoHTML;
      /* Old directory tickers that were renamed on the NGX. */
      var LOGO_ALIAS = { GUARANTY: 'GTCO', ACCESS: 'ACCESSCORP', TOTALNG: 'TOTAL', CCNN: 'BUACEMENT' };
      function logoKey(sym) { return LOGO_ALIAS[sym] || sym; }
      function logoBase() {
        return window.location.pathname.indexOf('/stocks/') !== -1 ? '../assets/logos/' : 'assets/logos/';
      }
      window.nvBadgeHTML = function (sym, size) {
        var cls = 'stk-badge' + (size ? ' ' + size : '');
        var key = logoKey(sym);
        if (window.NV_LOGOS && window.NV_LOGOS[key]) {
          return '<span class="' + cls + ' stk-logo" aria-hidden="true">' +
            '<img class="stk-img" data-sym="' + sym + '" data-size="' + (size || '') + '"' +
            ' src="' + logoBase() + key + '.png" alt="" loading="lazy"></span>';
        }
        return monoHTML(sym, size);
      };
      window.nvBadge = function (sym, size) {
        var d = document.createElement('div');
        d.innerHTML = window.nvBadgeHTML(sym, size);
        return d.firstChild;
      };
      /* If a logo image fails to load, swap in the monogram badge. */
      document.addEventListener('error', function (ev) {
        var t = ev.target;
        if (t && t.tagName === 'IMG' && t.className.indexOf('stk-img') !== -1 && !t.getAttribute('data-fbk')) {
          t.setAttribute('data-fbk', '1');
          var d = document.createElement('div');
          d.innerHTML = monoHTML(t.getAttribute('data-sym'), t.getAttribute('data-size') || undefined);
          if (t.parentNode) t.parentNode.replaceWith(d.firstChild);
        }
      }, true);
    }());

    /* ---- Theme: manual light/dark override, runs before first paint where possible ---- */
    (function themeInit() {
      function saved() { try { return localStorage.getItem('nv-theme'); } catch (e) { return null; } }
      function apply(t) {
        if (t === 'light' || t === 'dark') document.documentElement.setAttribute('data-theme', t);
        else document.documentElement.removeAttribute('data-theme');
        paintLogo();
      }
      function isDark() {
        var t = document.documentElement.getAttribute('data-theme');
        if (t) return t === 'dark';
        return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
      }
      function paintLogo() {
        var img = document.querySelector('.brand img');
        if (!img) return;
        var src = img.getAttribute('src') || '';
        var base = src.replace(/logo(-dark)?\.svg$/, '');
        if (!base) return;
        img.setAttribute('src', base + (isDark() ? 'logo-dark.svg' : 'logo.svg'));
        var pic = img.closest('picture');
        if (pic) { var s = pic.querySelector('source'); if (s) s.remove(); }
      }
      apply(saved());
      if (window.matchMedia) {
        var mq = window.matchMedia('(prefers-color-scheme: dark)');
        if (mq.addEventListener) mq.addEventListener('change', function () { if (!saved()) paintLogo(); });
      }
      /* Toggle button: auto -> light -> dark -> auto. Injected into the header. */
      var header = document.querySelector('.header-inner');
      if (header && !header.querySelector('.theme-toggle')) {
        var btn = document.createElement('button');
        btn.type = 'button'; btn.className = 'theme-toggle';
        var icons = { auto: '\u25D0', light: '\u2600', dark: '\u263E' };
        var labels = { auto: 'Appearance: automatic', light: 'Appearance: light', dark: 'Appearance: dark' };
        function state() { return saved() || 'auto'; }
        function paint() {
          var st = state();
          btn.textContent = icons[st];
          btn.setAttribute('aria-label', labels[st] + ' — activate to change');
          btn.title = labels[st];
        }
        btn.addEventListener('click', function () {
          var next = state() === 'auto' ? 'light' : state() === 'light' ? 'dark' : 'auto';
          try {
            if (next === 'auto') localStorage.removeItem('nv-theme');
            else localStorage.setItem('nv-theme', next);
          } catch (e) {}
          apply(next === 'auto' ? null : next);
          paint();
        });
        paint();
        header.appendChild(btn);
      }
    }());
    /* ---- Market status: NGX trades Mon–Fri 9:30–14:30 WAT (UTC+1) ---- */
    (function marketStatus() {
      var statusEl = document.querySelector('.topline .status');
      if (!statusEl) return;
      var now = new Date();
      var wat = new Date(now.getTime() + (now.getTimezoneOffset() + 60) * 60000);
      var day = wat.getDay(), mins = wat.getHours() * 60 + wat.getMinutes();
      var open = day >= 1 && day <= 5 && mins >= 570 && mins < 870;
      statusEl.innerHTML = '<i class="status-dot" aria-hidden="true"></i> ' + (open ? 'MARKET OPEN' : 'MARKET CLOSED');
      statusEl.classList.toggle('closed', !open);
      var hh = String(wat.getHours()).padStart(2, '0'), mm = String(wat.getMinutes()).padStart(2, '0');
      statusEl.title = 'Nigerian Exchange trading hours: Mon–Fri 9:30–14:30 WAT. Now ' + hh + ':' + mm + ' WAT.';
    }());
    /* ---- Auth nav: runs FIRST so links appear even if a widget below throws ---- */
    (function authNav() {
      var nav = document.querySelector('.site-nav');
      if (!nav || nav.querySelector('[data-authnav]')) return;
      var prefix = window.location.pathname.indexOf('/stocks/') === 0 ? '../' : '';
      var here = window.location.pathname.replace(/\/$/, '');
      /* Single Portfolio entry: logged-out visitors are routed through sign-in
         by portfolio.html itself; logged-in users land on their holdings. */
      var a = document.createElement('a');
      a.href = prefix + 'portfolio'; a.textContent = 'Portfolio'; a.setAttribute('data-authnav', '1');
      if (/portfolio$/.test(here)) a.className = 'active';
      nav.appendChild(a);
    }());
    /* ---- Nav link icons: every header link gets a small inline SVG icon. ---- */
    (function navIcons() {
      var S = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">';
      var ICONS = {
        'home': S + '<path d="M3 9.5 12 3l9 6.5V20a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z"/></svg>',
        'stocks': S + '<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/></svg>',
        'screener': S + '<path d="M4 5h16l-6 7v5l-4 2v-7z"/></svg>',
        'offers': S + '<path d="M20.6 13.4 12 22 2 12V2h10l8.6 8.6a2 2 0 0 0 0 2.8z"/><circle cx="7.5" cy="7.5" r="1.5"/></svg>',
        'calendar': S + '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M8 3v4M16 3v4M3 10h18"/></svg>',
        'news': S + '<path d="M4 6h13v12H6a2 2 0 0 1-2-2z"/><path d="M17 8h2a1 1 0 0 1 1 1v9a2 2 0 0 1-2 2H4"/><path d="M7 10h7M7 14h5"/></svg>',
        'learn': S + '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V4H6.5A2.5 2.5 0 0 0 4 6.5z"/><path d="M4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5"/></svg>',
        'portfolio': S + '<path d="M21.2 15.9A10 10 0 1 1 8 2.8"/><path d="M22 12A10 10 0 0 0 12 2v10z"/></svg>'
      };
      function paint() {
        var nav = document.querySelector('.site-nav');
        if (!nav) return;
        Array.prototype.forEach.call(nav.querySelectorAll('a'), function (a) {
          if (a.querySelector('svg')) return;
          var key = a.textContent.trim().toLowerCase();
          if (ICONS[key]) a.insertAdjacentHTML('afterbegin', ICONS[key]);
        });
      }
      paint();
      /* Re-run after any late nav injection so new links get icons too. */
      if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', paint);
      else setTimeout(paint, 0);
    }());
    (function () {
      
      var rangeSessions = { '1W': 5, '1M': 22, '3M': 66, '6M': 132, 'YTD': 'ytd' };
      var currentRange = 'YTD';
      /* Points for a range: last N sessions, or every session since 1 Jan for YTD.
         Works on the snapshot asiHistory and on live data swapped in later. */
      function rangePoints(range) {
        if (range === 'YTD') {
          var yr = String(new Date().getFullYear());
          var pts = asiHistory.filter(function (p) { return p.d >= yr + '-01-01'; });
          return pts.length > 1 ? pts : asiHistory.slice(-22);
        }
        return asiHistory.slice(-Math.min(rangeSessions[range] || 22, asiHistory.length));
      }
      function fmtAsiLabel(iso) {
        var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        var parts = String(iso).split('-');
        return parts[2].replace(/^0/, '') + ' ' + months[Number(parts[1]) - 1] + ' ' + parts[0];
      }
      var svg = document.getElementById('asiChart');
      var tooltip = document.getElementById('tooltip');
      var periodLabel = document.getElementById('periodLabel');
      var chartChange = document.getElementById('chartChange');
      var NS = 'http://www.w3.org/2000/svg';

      function formatNumber(n) { return n.toLocaleString('en-NG', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
      function node(name, attrs) {
        var el = document.createElementNS(NS, name);
        Object.keys(attrs || {}).forEach(function (key) { el.setAttribute(key, attrs[key]); });
        return el;
      }
      function draw(range) {
        while (svg.firstChild) svg.removeChild(svg.firstChild);
        var points = rangePoints(range);
        if (!points.length) return;
        function plabel(p) { return p.label || fmtAsiLabel(p.d); }
        var title = node('title', { id: 'chartTitle' }); title.textContent = 'NGX All-Share Index closing values'; svg.appendChild(title);
        var desc = node('desc', { id: 'chartDesc' }); desc.textContent = 'Interactive chart for ' + range + ' ending ' + plabel(points[points.length - 1]) + '.'; svg.appendChild(desc);
        var defs = node('defs', {});
        var grad = node('linearGradient', { id: 'asiAreaGrad', x1: '0', y1: '0', x2: '0', y2: '1' });
        grad.appendChild(node('stop', { offset: '0%' }));
        grad.appendChild(node('stop', { offset: '100%' }));
        defs.appendChild(grad);
        svg.appendChild(defs);
        var W = 1000, H = 360, L = 72, R = 28, T = 34, B = 46;
        var vals = points.map(function (p) { return p.v; });
        var min = Math.min.apply(null, vals), max = Math.max.apply(null, vals);
        var pad = Math.max((max - min) * .16, 300);
        min -= pad; max += pad;
        function x(i) { return points.length === 1 ? (L + W - R) / 2 : L + i * (W - L - R) / (points.length - 1); }
        function y(v) { return T + (max - v) * (H - T - B) / (max - min); }
        for (var i = 0; i < 4; i++) {
          var gy = T + i * (H - T - B) / 3;
          svg.appendChild(node('line', { x1: L, x2: W - R, y1: gy, y2: gy, 'class': 'grid-line' }));
          var label = node('text', { x: L - 12, y: gy + 4, 'text-anchor': 'end', 'class': 'axis-label' });
          label.textContent = Math.round(max - i * (max - min) / 3).toLocaleString('en-NG'); svg.appendChild(label);
        }
        var coords = points.map(function (p, idx) { return [x(idx), y(p.v)]; });
        var lineD = coords.map(function (c, idx) { return (idx ? 'L' : 'M') + c[0].toFixed(1) + ',' + c[1].toFixed(1); }).join(' ');
        var areaD = lineD + ' L' + coords[coords.length - 1][0].toFixed(1) + ',' + (H-B) + ' L' + coords[0][0].toFixed(1) + ',' + (H-B) + ' Z';
        svg.appendChild(node('path', { d: areaD, 'class': 'area' }));
        svg.appendChild(node('path', { d: lineD, 'class': 'series' }));
        points.forEach(function (p, idx) {
          var dot = node('circle', { cx: coords[idx][0], cy: coords[idx][1], r: 5, 'class': 'chart-dot', tabindex: '0', role: 'button', 'aria-label': plabel(p) + ': ' + formatNumber(p.v) });
          function show() {
            var wrap = svg.parentElement.getBoundingClientRect();
            var box = svg.getBoundingClientRect();
            tooltip.textContent = plabel(p) + ' · ' + formatNumber(p.v);
            tooltip.style.left = ((coords[idx][0] / W) * box.width + box.left - wrap.left) + 'px';
            tooltip.style.top = ((coords[idx][1] / H) * box.height + box.top - wrap.top) + 'px';
            tooltip.classList.add('visible'); tooltip.setAttribute('aria-hidden', 'false');
          }
          function hide() { tooltip.classList.remove('visible'); tooltip.setAttribute('aria-hidden', 'true'); }
          dot.addEventListener('mouseenter', show); dot.addEventListener('focus', show); dot.addEventListener('click', show); dot.addEventListener('mouseleave', hide); dot.addEventListener('blur', hide);
          svg.appendChild(dot);
        });
        var first = node('text', { x: L, y: H - 17, 'text-anchor': 'start', 'class': 'axis-label' }); first.textContent = plabel(points[0]); svg.appendChild(first);
        var last = node('text', { x: W - R, y: H - 17, 'text-anchor': 'end', 'class': 'axis-label' }); last.textContent = plabel(points[points.length-1]); svg.appendChild(last);
        var chgPct = (points[points.length - 1].v - points[0].v) / points[0].v * 100;
        chartChange.textContent = (chgPct < 0 ? '−' : '+') + Math.abs(chgPct).toFixed(2) + '% since ' + plabel(points[0]);
        chartChange.className = 'chart-change ' + (chgPct < 0 ? 'down' : 'up');
        periodLabel.textContent = plabel(points[0]) + ' — ' + plabel(points[points.length-1]);
      }
      document.querySelectorAll('.range-button').forEach(function (button) {
        button.addEventListener('click', function () {
          document.querySelectorAll('.range-button').forEach(function (b) { b.setAttribute('aria-pressed', 'false'); });
          button.setAttribute('aria-pressed', 'true');
          currentRange = button.getAttribute('data-range');
          draw(currentRange);
        });
      });

      
      var dirState = { query: '', sector: 'All' };
      var dirSearch = document.getElementById('dirSearch');
      var dirList = document.getElementById('directoryList');
      var dirCount = document.getElementById('dirCount');
      var sectorChips = document.getElementById('sectorChips');
      function dirRows() {
        var q = dirState.query.toLowerCase();
        /* Map current NGX tickers back to the old directory symbols. */
        var REV_ALIAS = { GTCO: 'GUARANTY', ACCESSCORP: 'ACCESS', TOTAL: 'TOTALNG', BUACEMENT: 'CCNN' };
        return directory.filter(function (e) {
          if (dirState.sector !== 'All' && e.g !== dirState.sector) return false;
          if (!q) return true;
          if (e.s.toLowerCase().indexOf(q) !== -1 || e.c.toLowerCase().indexOf(q) !== -1 || e.g.toLowerCase().indexOf(q) !== -1) return true;
          return REV_ALIAS[q.toUpperCase()] === e.s;
        }).sort(function (a, b) { return a.s < b.s ? -1 : a.s > b.s ? 1 : 0; });
      }
      function renderDirectory() {
        if (!dirList) return;
        dirList.innerHTML = '';
        var rows = dirRows();
        dirCount.textContent = rows.length + (rows.length === 1 ? ' stock' : ' stocks');
        if (!rows.length) {
          var empty = document.createElement('div'); empty.className = 'empty-note';
          empty.textContent = 'No stocks match your search.';
          dirList.appendChild(empty); return;
        }
        rows.forEach(function (r) {
          var item = document.createElement('div'); item.className = 'market-row';
          var star = document.createElement('button'); star.type = 'button'; star.className = 'star';
          var starred = isStarred(r.s);
          star.setAttribute('aria-pressed', starred ? 'true' : 'false');
          star.setAttribute('aria-label', (starred ? 'Remove ' : 'Add ') + r.s + (starred ? ' from' : ' to') + ' watchlist');
          star.textContent = starred ? '★' : '☆';
          star.addEventListener('click', function (ev) { ev.stopPropagation(); toggleStar(r.s); });
          var main = document.createElement('button'); main.type = 'button'; main.className = 'row-main';
          main.setAttribute('aria-label', r.s + ', ' + r.c + ' — view details');
          var symbol = document.createElement('span'); symbol.className = 'symbol'; symbol.textContent = r.s;
          var tag = document.createElement('span'); tag.className = 'list-tag'; tag.textContent = r.g;
          symbol.appendChild(tag);
          var company = document.createElement('span'); company.className = 'company'; company.textContent = r.c;
          var rowText = document.createElement('span'); rowText.className = 'row-text'; rowText.appendChild(symbol); rowText.appendChild(company); main.appendChild(window.nvBadge(r.s)); main.appendChild(rowText);
          main.addEventListener('click', function () { openModal(r.s, main); });
          var price = document.createElement('div'); price.className = 'price'; price.textContent = r.p;
          var move = document.createElement('div'); move.className = 'move ' + (r.d || ''); move.textContent = r.m;
          item.appendChild(star); item.appendChild(main); item.appendChild(price); item.appendChild(move);
          dirList.appendChild(item);
        });
      }
      if (sectorChips) (function buildSectorChips() {
        var sectors = ['All'];
        directory.forEach(function (e) { if (sectors.indexOf(e.g) === -1) sectors.push(e.g); });
        sectors.forEach(function (name) {
          var b = document.createElement('button'); b.type = 'button'; b.className = 'sector-chip';
          b.textContent = name; b.setAttribute('aria-pressed', name === 'All' ? 'true' : 'false');
          b.addEventListener('click', function () {
            dirState.sector = name;
            sectorChips.querySelectorAll('.sector-chip').forEach(function (c) { c.setAttribute('aria-pressed', c === b ? 'true' : 'false'); });
            renderDirectory();
          });
          sectorChips.appendChild(b);
        });
      }());
      var dirTimer = null;
      if (dirSearch) dirSearch.addEventListener('input', function () {
        clearTimeout(dirTimer);
        dirTimer = setTimeout(function () { dirState.query = dirSearch.value.trim(); renderDirectory(); }, 160);
      });
      var marketList = document.getElementById('market-list');
      var searchInput = document.getElementById('stockSearch');
      var watchCount = document.getElementById('watchCount');
      var sortLabel = document.querySelector('.sort-move-label');
      var state = { table: 'gainers', query: '', sortKey: null, sortDir: 1 };
      var watchlist = [];
      try { watchlist = JSON.parse(localStorage.getItem('ngxWatchlist') || '[]'); } catch (e) { watchlist = []; }
      function saveWatchlist() { try { localStorage.setItem('ngxWatchlist', JSON.stringify(watchlist)); } catch (e) {} }
      function isStarred(s) { return watchlist.indexOf(s) !== -1; }
      function updateWatchCount() { if (!watchCount) return; watchCount.textContent = watchlist.length ? '(' + watchlist.length + ')' : ''; }
      function findStock(s) {
        for (var k in tables) {
          for (var i = 0; i < tables[k].length; i++) {
            if (tables[k][i].s === s) return { row: tables[k][i], list: k };
          }
        }
        for (var j = 0; j < directory.length; j++) {
          if (directory[j].s === s) return { row: directory[j], list: 'directory' };
        }
        return null;
      }
      function toggleStar(s) {
        var i = watchlist.indexOf(s);
        if (i === -1) watchlist.push(s); else watchlist.splice(i, 1);
        saveWatchlist(); updateWatchCount(); render(); renderDirectory();
        if (currentModal === s) paintModalStar(s);
      }
      function currentRows() {
        var rows;
        if (state.query) {
          var q = state.query.toLowerCase();
          rows = [];
          ['gainers', 'losers', 'volume'].forEach(function (k) {
            tables[k].forEach(function (r) {
              if (r.s.toLowerCase().indexOf(q) !== -1 || r.c.toLowerCase().indexOf(q) !== -1) {
                rows.push({ row: r, list: k });
              }
            });
          });
        } else if (state.table === 'watchlist') {
          rows = watchlist.map(findStock).filter(Boolean);
        } else {
          rows = tables[state.table].map(function (r) { return { row: r, list: state.table }; });
        }
        if (state.sortKey) {
          var key = state.sortKey, dir = state.sortDir;
          rows.sort(function (a, b) {
            var av, bv;
            if (key === 'symbol') { av = a.row.s; bv = b.row.s; return dir * (av < bv ? -1 : av > bv ? 1 : 0); }
            if (key === 'price') {
              av = a.row.pv; bv = b.row.pv;
              if (av === null && bv === null) return 0;
              if (av === null) return 1; if (bv === null) return -1;
              return dir * (av - bv);
            }
            return dir * (a.row.cv - b.row.cv);
          });
        }
        return rows;
      }
      function paintTabs() {
        document.querySelectorAll('.switcher button').forEach(function (b) {
          b.setAttribute('aria-selected', state.query ? 'false' : (b.getAttribute('data-table') === state.table ? 'true' : 'false'));
        });
      }
      function paintSortArrows() {
        document.querySelectorAll('.sort-bar button').forEach(function (b) {
          var arrow = b.querySelector('.arrow');
          arrow.textContent = b.getAttribute('data-sort') === state.sortKey ? (state.sortDir === 1 ? ' ▲' : ' ▼') : '';
        });
      }
      function render() {
        paintTabs();
        if (!marketList) return;
        marketList.innerHTML = '';
        var rows = currentRows();
        sortLabel.textContent = state.table === 'volume' && !state.query ? 'Volume' : 'Change';
        if (!rows.length) {
          var empty = document.createElement('div'); empty.className = 'empty-note';
          empty.textContent = (state.table === 'watchlist' && !state.query)
            ? 'Your watchlist is empty. Tap the ☆ on any stock to pin it here — it stays saved in this browser.'
            : 'No stocks match your search.';
          marketList.appendChild(empty);
          return;
        }
        rows.forEach(function (entry, i) {
          var r = entry.row;
          var item = document.createElement('div'); item.className = 'market-row';
          var star = document.createElement('button'); star.type = 'button'; star.className = 'star';
          var starred = isStarred(r.s);
          star.setAttribute('aria-pressed', starred ? 'true' : 'false');
          star.setAttribute('aria-label', (starred ? 'Remove ' : 'Add ') + r.s + (starred ? ' from' : ' to') + ' watchlist');
          star.textContent = starred ? '★' : '☆';
          star.addEventListener('click', function (ev) { ev.stopPropagation(); toggleStar(r.s); });
          var main = document.createElement('button'); main.type = 'button'; main.className = 'row-main';
          main.setAttribute('aria-label', r.s + ', ' + r.c + ' — view details');
          var symbol = document.createElement('span'); symbol.className = 'symbol'; symbol.textContent = (i + 1) + '. ' + r.s;
          if (state.query || state.table === 'watchlist') {
            var tag = document.createElement('span'); tag.className = 'list-tag'; tag.textContent = listNames[entry.list];
            symbol.appendChild(tag);
          }
          var company = document.createElement('span'); company.className = 'company'; company.textContent = r.c;
          var rowText = document.createElement('span'); rowText.className = 'row-text'; rowText.appendChild(symbol); rowText.appendChild(company); main.appendChild(window.nvBadge(r.s)); main.appendChild(rowText);
          main.addEventListener('click', function () { openModal(r.s, main); });
          var price = document.createElement('div'); price.className = 'price'; price.textContent = r.p;
          var move = document.createElement('div'); move.className = 'move ' + r.d; move.textContent = r.m;
          item.appendChild(star); item.appendChild(main); item.appendChild(price); item.appendChild(move);
          marketList.appendChild(item);
        });
      }
      document.querySelectorAll('.sort-bar button').forEach(function (b) {
        b.addEventListener('click', function () {
          var key = b.getAttribute('data-sort');
          if (state.sortKey === key) { state.sortDir *= -1; }
          else { state.sortKey = key; state.sortDir = key === 'symbol' ? 1 : -1; }
          paintSortArrows(); render();
        });
      });
      document.querySelectorAll('.switcher button').forEach(function (button) {
        button.addEventListener('click', function () {
          state.table = button.getAttribute('data-table');
          state.query = ''; searchInput.value = '';
          state.sortKey = null; paintSortArrows();
          marketList.setAttribute('aria-labelledby', button.id);
          render();
        });
      });
      var searchTimer = null;
      if (searchInput) searchInput.addEventListener('input', function () {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(function () { state.query = searchInput.value.trim(); render(); }, 160);
      });
      var backdrop = document.getElementById('modalBackdrop');
      var modalClose = document.getElementById('modalClose');
      var modalStar = document.getElementById('modalStar');
      var currentModal = null, lastFocused = null;
      function paintModalStar(s) {
        modalStar.textContent = isStarred(s) ? '★ Starred — tap to remove from watchlist' : '☆ Add to watchlist';
      }
      function openModal(s, opener) {
        var found = findStock(s); if (!found) return;
        var r = found.row;
        var isDir = found.list === 'directory';
        currentModal = s; lastFocused = opener || document.activeElement;
        var snapShort = window.NVTradeDate || '25 Sep 2026';
        var snapLong = window.NVTradeDateLong || '25 September 2026';
        document.getElementById('modalList').textContent = isDir ? 'Market directory' : (listNames[found.list] + ' \u00b7 Snapshot ' + snapShort);
        var msEl = document.getElementById('modalSymbol');
        msEl.innerHTML = '';
        msEl.appendChild(window.nvBadge(r.s, 'lg'));
        var msTx = document.createElement('span'); msTx.textContent = r.s; msEl.appendChild(msTx);
        document.getElementById('modalCompany').textContent = r.c + (isDir && r.g ? ' \u00b7 ' + r.g : '');
        document.getElementById('modalPrice').textContent = r.p;
        document.getElementById('modalMoveLabel').textContent = r.vol ? 'Volume' : (r.noSnap ? 'Sector' : 'Day change');
        var mm = document.getElementById('modalMove');
        mm.textContent = r.noSnap ? r.g : (r.m + (r.vol ? ' shares' : ''));
        mm.style.color = r.noSnap ? 'inherit' : (r.d === 'up' ? 'var(--green-strong)' : 'var(--red)');
        document.getElementById('modalNote').innerHTML = r.noSnap
          ? 'No snapshot price held for this stock. <a href="https://ngnmarket.com/stocks/' + s + '" target="_blank" rel="noopener noreferrer">See its live quote on NGN Market ↗</a>'
          : 'Figures are fixed at the ' + snapLong + ' close and are not live. <a href="https://ngxgroup.com/" target="_blank" rel="noopener noreferrer">Check official NGX data ↗</a>';
        document.getElementById('modalLive').href = 'https://ngnmarket.com/stocks/' + s;
        var mpEl = document.getElementById('modalPage');
        if (mpEl) {
          var hasPage = !!(window.NV_STOCK_PAGES && window.NV_STOCK_PAGES[s]);
          mpEl.hidden = !hasPage;
          if (hasPage) mpEl.href = 'stocks/' + s;
        }
        paintModalStar(s);
        backdrop.hidden = false;
        document.body.style.overflow = 'hidden';
        modalClose.focus();
      }
      function closeModal() {
        backdrop.hidden = true;
        document.body.style.overflow = '';
        currentModal = null;
        if (lastFocused && lastFocused.focus) lastFocused.focus();
      }
      if (modalClose) modalClose.addEventListener('click', closeModal);
      if (backdrop) backdrop.addEventListener('click', function (ev) { if (ev.target === backdrop) closeModal(); });
      document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape' && backdrop && !backdrop.hidden) closeModal(); });
      if (modalStar) modalStar.addEventListener('click', function () { if (currentModal) toggleStar(currentModal); });
      var newsState = { sector: 'All' };
      var newsChips = document.getElementById('newsChips');
      function getNewsCards() { return Array.prototype.slice.call(document.querySelectorAll('.news-card')); }
      var newsSectors = ['All', 'Market-wide', 'Banking', 'Insurance', 'Oil & Gas', 'Consumer Goods', 'Industrial Goods'];
      var newsKeys = { 'All': 'all', 'Market-wide': 'market', 'Banking': 'banking', 'Insurance': 'insurance', 'Oil & Gas': 'oilgas', 'Consumer Goods': 'consumer', 'Industrial Goods': 'industrial' };
      function renderNews() {
        var key = newsKeys[newsState.sector];
        var n = 0;
        getNewsCards().forEach(function (c) {
          var show = key === 'all' || c.getAttribute('data-sector') === key;
          c.style.display = show ? '' : 'none';
          if (show) n++;
        });
        var newsCountEl = document.getElementById('newsCount');
        if (newsCountEl) newsCountEl.textContent = n + (n === 1 ? ' story' : ' stories');
      }
      if (newsChips) newsSectors.forEach(function (name) {
        var b = document.createElement('button'); b.type = 'button'; b.className = 'sector-chip';
        b.textContent = name; b.setAttribute('aria-pressed', name === 'All' ? 'true' : 'false');
        b.addEventListener('click', function () {
          newsState.sector = name;
          newsChips.querySelectorAll('.sector-chip').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
          renderNews();
        });
        newsChips.appendChild(b);
      });
      renderNews();
      // Live headlines from the auto newsroom (worker refreshes the feed every few hours).
      (function loadLiveNews() {
        var grid = document.getElementById('liveNewsGrid');
        if (!grid) return;
        var section = document.getElementById('liveNewsSection');
        var updatedEl = document.getElementById('liveNewsUpdated');
        var sectorKey = { 'market-wide': 'market', 'banking': 'banking', 'insurance': 'insurance', 'oil & gas': 'oilgas', 'consumer goods': 'consumer', 'industrial goods': 'industrial' };
        var sectorLabel = { 'market-wide': 'Market-wide', 'banking': 'Banking', 'insurance': 'Insurance', 'oil & gas': 'Oil & Gas', 'consumer goods': 'Consumer Goods', 'industrial goods': 'Industrial Goods' };
        function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
        function fmtDate(ts) {
          var d = new Date(ts);
          var months = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];
          return d.getDate() + ' ' + months[d.getMonth()];
        }
        function ago(ts) {
          var m = Math.round((Date.now() - ts) / 60000);
          if (m < 1) return 'just now';
          if (m < 60) return m + 'm ago';
          var h = Math.round(m / 60);
          return h < 24 ? h + 'h ago' : Math.round(h / 24) + 'd ago';
        }
        fetch('https://nairaview-api.meetomidiora.workers.dev/api/news')
          .then(function (r) { if (!r.ok) throw new Error('news feed unavailable'); return r.json(); })
          .then(function (data) {
            var items = (data && data.items) || [];
            if (!items.length) { if (section) section.style.display = 'none'; return; }
            var html = '';
            items.slice(0, 24).forEach(function (it) {
              var key = sectorKey[it.sector] || 'market';
              html += '<a class="news-card" data-sector="' + key + '" href="' + esc(it.link) + '" target="_blank" rel="noopener noreferrer">'
                + '<div class="news-meta"><span>' + esc((it.source || '').toUpperCase()) + '</span><span>' + esc(fmtDate(it.published_at)) + '</span><span class="news-sector">' + esc(sectorLabel[it.sector] || 'Market-wide') + '</span></div>'
                + '<h3>' + esc(it.title) + '</h3>'
                + (it.description ? '<p>' + esc(it.description) + '</p>' : '')
                + '<span class="arrow" aria-hidden="true">\u2197</span></a>';
            });
            grid.innerHTML = html;
            if (updatedEl && data.updated_at) updatedEl.textContent = 'Updated ' + ago(data.updated_at) + ' \u00B7 headlines refresh automatically';
            renderNews();
          })
          .catch(function () { if (section) section.style.display = 'none'; });
      })();
      document.querySelectorAll('.news-card[data-tickers]').forEach(function (card) {
        var tickers = card.getAttribute('data-tickers').split(',');
        var wrap = document.createElement('div');
        wrap.className = 'ticker-chips';
        tickers.forEach(function (t) {
          var chip = document.createElement('span');
          chip.className = 'ticker-chip';
          chip.textContent = t;
          chip.setAttribute('role', 'link');
          chip.setAttribute('tabindex', '0');
          chip.setAttribute('aria-label', 'View ' + t + ' stock page');
          function go(ev) { ev.preventDefault(); ev.stopPropagation(); window.location.href = 'stocks/' + t; }
          chip.addEventListener('click', go);
          chip.addEventListener('keydown', function (ev) { if (ev.key === 'Enter' || ev.key === ' ') go(ev); });
          wrap.appendChild(chip);
        });
        card.appendChild(wrap);
      });
      var stickyClosed = false;
      function revealAds() {
        var anySticky = false;
        document.querySelectorAll('.ad-slot').forEach(function (slot) {
          if (slot.id === 'adSticky' && stickyClosed) return;
          if (slot.querySelector('iframe')) {
            slot.classList.add('ad-live');
            if (slot.id === 'adSticky') anySticky = true;
          }
        });
        document.body.classList.toggle('ad-sticky-on', anySticky);
      }
      var adTries = 0;
      function pollAds() {
        revealAds();
        if (++adTries < 15 && !document.querySelector('.ad-slot.ad-live')) setTimeout(pollAds, 1000);
      }
      window.addEventListener('load', function () { setTimeout(pollAds, 1500); });
      var adClose = document.getElementById('adStickyClose');
      if (adClose) adClose.addEventListener('click', function () {
        stickyClosed = true;
        document.getElementById('adSticky').classList.remove('ad-live');
        document.body.classList.remove('ad-sticky-on');
      });
      /* ---- Native market ticker (own snapshot data; replaces blocked ngnmarket iframe) ---- */
      function renderTape() {
        var track = document.getElementById('tickerTrack');
        if (!track) return;
        var rows = (typeof tables !== 'undefined') ? tables.gainers.concat(tables.losers) : [];
        if (!rows.length) { track.parentNode.style.display = 'none'; return; }
        var html = rows.map(function (r) {
          return '<span class="ticker-item">' + window.nvBadgeHTML(r.s, 'sm') + '<span class="tk-s">' + r.s + '</span>' +
            '<span class="tk-p">' + r.p + '</span>' +
            '<span class="tk-m ' + (r.d === 'up' ? 'up' : 'down') + '">' + r.m + '</span></span>';
        }).join('');
        track.innerHTML = html + html; /* duplicate for a seamless -50% loop */
      }
      renderTape();
      /* ---- Market heatmap ---- */
      function renderHeatmap() {
        var host = document.getElementById('heatTiles');
        if (!host) return;
        host.innerHTML = '';
        tables.gainers.concat(tables.losers).forEach(function (r) {
          var t = document.createElement('button');
          t.type = 'button'; t.className = 'heat-tile'; t.setAttribute('role', 'listitem');
          var mag = Math.abs(r.cv);
          t.style.flex = Math.max(1, Math.round(mag)) + ' 1 120px';
          /* Pastel tile, dark text; only the change figure carries color. */
          t.style.background = r.cv >= 0 ? 'var(--green-soft)' : 'var(--red-soft)';
          var s1 = document.createElement('span'); s1.className = 'ht-s'; s1.textContent = r.s;
          var s2 = document.createElement('span'); s2.className = 'ht-c ' + (r.cv >= 0 ? 'up' : 'down'); s2.textContent = r.m;
          var s3 = document.createElement('span'); s3.className = 'ht-p'; s3.textContent = r.p;
          t.insertBefore(window.nvBadge(r.s, 'sm'), t.firstChild);
          t.appendChild(s1); t.appendChild(s2); t.appendChild(s3);
          t.setAttribute('aria-label', r.s + ', ' + r.c + ', day change ' + r.m + ' — view details');
          t.addEventListener('click', function () { openModal(r.s, t); });
          host.appendChild(t);
        });
      }
      renderHeatmap();
      /* ---- Stock screener ---- */
      if (document.getElementById('screenList')) {
      var scrState = { mover: 'all', sector: 'All', minP: '', maxP: '', minC: '', maxC: '', sort: 'chg-desc' };
      var screenList = document.getElementById('screenList');
      var screenCount = document.getElementById('screenCount');
      function scrKey(e, what) {
        if (what === 'chg') return (!e.vol && e.pv !== null && !e.noSnap) ? e.cv : null;
        if (what === 'price') return e.pv;
        if (what === 'vol') return e.vol ? e.cv : null;
        return null;
      }
      function scrRows() {
        var minP = parseFloat(scrState.minP), maxP = parseFloat(scrState.maxP);
        var minC = parseFloat(scrState.minC), maxC = parseFloat(scrState.maxC);
        var priceOn = !isNaN(minP) || !isNaN(maxP);
        var chgOn = !isNaN(minC) || !isNaN(maxC);
        var rows = directory.filter(function (e) {
          if (scrState.mover === 'gainers' && !(!e.vol && e.d === 'up')) return false;
          if (scrState.mover === 'losers' && e.d !== 'down') return false;
          if (scrState.mover === 'volume' && !e.vol) return false;
          if (scrState.sector !== 'All' && e.g !== scrState.sector) return false;
          if (priceOn) {
            if (e.pv === null) return false;
            if (!isNaN(minP) && e.pv < minP) return false;
            if (!isNaN(maxP) && e.pv > maxP) return false;
          }
          if (chgOn) {
            var c = scrKey(e, 'chg');
            if (c === null) return false;
            if (!isNaN(minC) && c < minC) return false;
            if (!isNaN(maxC) && c > maxC) return false;
          }
          return true;
        });
        var key = scrState.sort;
        rows.sort(function (a, b) {
          if (key === 'name') return a.s < b.s ? -1 : a.s > b.s ? 1 : 0;
          var wk = key === 'vol-desc' ? 'vol' : (key.indexOf('chg') === 0 ? 'chg' : 'price');
          var ka = scrKey(a, wk), kb = scrKey(b, wk);
          if (ka === null && kb === null) return 0;
          if (ka === null) return 1;
          if (kb === null) return -1;
          return (key === 'chg-asc' || key === 'price-asc') ? ka - kb : kb - ka;
        });
        return rows;
      }
      function renderScreener() {
        screenList.innerHTML = '';
        var rows = scrRows();
        screenCount.textContent = rows.length + (rows.length === 1 ? ' stock' : ' stocks');
        if (!rows.length) {
          var empty = document.createElement('div'); empty.className = 'empty-note';
          empty.textContent = 'No stocks match these filters.';
          screenList.appendChild(empty); return;
        }
        rows.forEach(function (r) {
          var item = document.createElement('div'); item.className = 'market-row';
          var star = document.createElement('button'); star.type = 'button'; star.className = 'star';
          var starred = isStarred(r.s);
          star.setAttribute('aria-pressed', starred ? 'true' : 'false');
          star.setAttribute('aria-label', (starred ? 'Remove ' : 'Add ') + r.s + (starred ? ' from' : ' to') + ' watchlist');
          star.textContent = starred ? '★' : '☆';
          star.addEventListener('click', function (ev) { ev.stopPropagation(); toggleStar(r.s); renderScreener(); });
          var main = document.createElement('button'); main.type = 'button'; main.className = 'row-main';
          main.setAttribute('aria-label', r.s + ', ' + r.c + ' — view details');
          var symbol = document.createElement('span'); symbol.className = 'symbol'; symbol.textContent = r.s;
          var tag = document.createElement('span'); tag.className = 'list-tag'; tag.textContent = r.g;
          symbol.appendChild(tag);
          var company = document.createElement('span'); company.className = 'company'; company.textContent = r.c;
          var rowText = document.createElement('span'); rowText.className = 'row-text'; rowText.appendChild(symbol); rowText.appendChild(company); main.appendChild(window.nvBadge(r.s)); main.appendChild(rowText);
          main.addEventListener('click', function () { openModal(r.s, main); });
          var price = document.createElement('div'); price.className = 'price'; price.textContent = r.p;
          var move = document.createElement('div'); move.className = 'move ' + (r.d || ''); move.textContent = r.vol ? r.m + ' shares' : r.m;
          item.appendChild(star); item.appendChild(main); item.appendChild(price); item.appendChild(move);
          screenList.appendChild(item);
        });
      }
      (function buildScreenChips() {
        var host = document.getElementById('screenMover');
        [['all', 'All'], ['gainers', 'Gainers'], ['losers', 'Losers'], ['volume', 'Most traded']].forEach(function (opt) {
          var b = document.createElement('button'); b.type = 'button'; b.className = 'sector-chip';
          b.textContent = opt[1]; b.setAttribute('aria-pressed', opt[0] === 'all' ? 'true' : 'false');
          b.addEventListener('click', function () {
            scrState.mover = opt[0];
            host.querySelectorAll('.sector-chip').forEach(function (c) { c.setAttribute('aria-pressed', c === b ? 'true' : 'false'); });
            renderScreener();
          });
          host.appendChild(b);
        });
      }());
      (function buildScreenSectors() {
        var sel = document.getElementById('screenSector');
        var sectors = ['All'];
        directory.forEach(function (e) { if (sectors.indexOf(e.g) === -1) sectors.push(e.g); });
        sectors.forEach(function (name) {
          var o = document.createElement('option'); o.value = name;
          o.textContent = name === 'All' ? 'All sectors' : name;
          sel.appendChild(o);
        });
        sel.addEventListener('change', function () { scrState.sector = sel.value; renderScreener(); });
      }());
      [['screenMinP', 'minP'], ['screenMaxP', 'maxP'], ['screenMinC', 'minC'], ['screenMaxC', 'maxC']].forEach(function (pair) {
        document.getElementById(pair[0]).addEventListener('input', function (ev) { scrState[pair[1]] = ev.target.value; renderScreener(); });
      });
      document.getElementById('screenSort').addEventListener('change', function (ev) { scrState.sort = ev.target.value; renderScreener(); });
      document.getElementById('screenReset').addEventListener('click', function () {
        scrState = { mover: 'all', sector: 'All', minP: '', maxP: '', minC: '', maxC: '', sort: 'chg-desc' };
        document.getElementById('screenSector').value = 'All';
        document.getElementById('screenSort').value = 'chg-desc';
        ['screenMinP', 'screenMaxP', 'screenMinC', 'screenMaxC'].forEach(function (id) { document.getElementById(id).value = ''; });
        document.querySelectorAll('#screenMover .sector-chip').forEach(function (c, i) { c.setAttribute('aria-pressed', i === 0 ? 'true' : 'false'); });
        renderScreener();
      });
      renderScreener();
      }
      /* ---- Calendar type filters ---- */
      (function buildCalChips() {
        var host = document.getElementById('calChips');
        if (!host) return;
        ['All', 'Dividend', 'Offer', 'Earnings', 'Regulatory'].forEach(function (name, i) {
          var b = document.createElement('button'); b.type = 'button'; b.className = 'sector-chip';
          b.textContent = name; b.setAttribute('aria-pressed', i === 0 ? 'true' : 'false');
          b.addEventListener('click', function () {
            host.querySelectorAll('.sector-chip').forEach(function (c) { c.setAttribute('aria-pressed', c === b ? 'true' : 'false'); });
            document.querySelectorAll('.cal-event').forEach(function (ev) {
              ev.style.display = (name === 'All' || ev.getAttribute('data-type') === name) ? '' : 'none';
            });
          });
          host.appendChild(b);
        });
      }());
      updateWatchCount();
      if (document.getElementById('asiChart')) draw('YTD');
      render();
      renderDirectory();
      /* Live-data hooks: assets/live.js swaps in fresh market data after load
         and calls these to repaint without a page reload. */
      window.NV = window.NV || {};
      window.NV.redrawAsi = function (r) { if (document.getElementById('asiChart')) draw(r || currentRange); };
      window.NV.renderTape = function () { renderTape(); };
      window.NV.renderHeatmap = function () { renderHeatmap(); };
      window.NV.renderTables = function () { render(); };
      window.NV.renderDirectory = function () { renderDirectory(); };
      window.NV.renderScreener = function () { if (typeof renderScreener === 'function' && document.getElementById('screenList')) renderScreener(); };
    }());
