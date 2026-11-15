(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };

  /* ---------- nav ---------- */
  var nav = $('#nav'), toggle = $('#navToggle'), drawer = $('#navDrawer');
  addEventListener('scroll', function () { nav.classList.toggle('stuck', scrollY > 8); }, { passive: true });
  toggle.addEventListener('click', function () {
    var open = drawer.classList.toggle('open');
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
  });
  drawer.addEventListener('click', function (e) {
    if (e.target.tagName === 'A') { drawer.classList.remove('open'); toggle.setAttribute('aria-expanded', 'false'); }
  });

  /* ---------- hero form: hand over to the full form ---------- */
  var heroForm = $('#heroForm'), heroEmail = $('#heroEmail'), heroErr = $('#heroErr');
  heroForm.addEventListener('submit', function (e) {
    e.preventDefault();
    var v = heroEmail.value.trim();
    if (!/^[^@\s]{1,64}@[^@\s]+\.[A-Za-z]{2,}$/.test(v)) {
      heroErr.textContent = 'Please enter a valid work e-mail.';
      heroErr.classList.add('on');
      heroEmail.focus();
      return;
    }
    heroErr.classList.remove('on');
    var full = $('#f-email');
    if (full) full.value = v;
    document.getElementById('waitlist').scrollIntoView({ behavior: 'smooth', block: 'start' });
    setTimeout(function () { if (full) full.focus({ preventScroll: true }); }, 500);
  });
  heroEmail.addEventListener('input', function () { heroErr.classList.remove('on'); });

  /* ---------- hero wireframe ---------- */
  var NS = 'http://www.w3.org/2000/svg';
  function el(name, attrs) {
    var n = document.createElementNS(NS, name);
    for (var k in attrs) if (Object.prototype.hasOwnProperty.call(attrs, k)) n.setAttribute(k, attrs[k]);
    return n;
  }
  function gearPath(cx, cy, rO, rR, teeth, rot) {
    var step = Math.PI * 2 / teeth, d = '';
    for (var i = 0; i < teeth; i++) {
      var a = i * step + rot;
      var pts = [
        [a, rR], [a + step * 0.26, rR], [a + step * 0.34, rO],
        [a + step * 0.64, rO], [a + step * 0.72, rR], [a + step, rR]
      ];
      for (var j = 0; j < pts.length; j++) {
        var ang = pts[j][0], r = pts[j][1];
        d += (d ? 'L' : 'M') + (cx + Math.cos(ang) * r).toFixed(1) + ' ' + (cy + Math.sin(ang) * r).toFixed(1);
      }
    }
    return d + 'Z';
  }
  function drawMesh() {
    var svg = $('#mesh');
    if (!svg) return;
    var defs = el('defs');

    var hot = el('radialGradient', { id: 'hot', cx: '50%', cy: '50%', r: '50%' });
    hot.appendChild(el('stop', { offset: '0%', 'stop-color': '#FFE45E', 'stop-opacity': '.85' }));
    hot.appendChild(el('stop', { offset: '38%', 'stop-color': '#7CFFB2', 'stop-opacity': '.45' }));
    hot.appendChild(el('stop', { offset: '72%', 'stop-color': '#00E5FF', 'stop-opacity': '.22' }));
    hot.appendChild(el('stop', { offset: '100%', 'stop-color': '#00E5FF', 'stop-opacity': '0' }));
    defs.appendChild(hot);

    var clip = el('clipPath', { id: 'housingClip' });
    clip.appendChild(el('rect', { x: '128', y: '138', width: '280', height: '230', rx: '10' }));
    defs.appendChild(clip);
    svg.appendChild(defs);

    var g = el('g', {});
    /* housing: front face + depth */
    var front = { x: 128, y: 138, w: 280, h: 230 };
    var depth = { x: 96, y: -46 };
    g.appendChild(el('rect', { x: front.x + depth.x, y: front.y + depth.y, width: front.w, height: front.h, rx: 10, fill: '#0C1013', stroke: 'rgba(0,229,255,.26)', 'stroke-width': '1.1' }));
    ['lt', 'rt', 'rb', 'lb'].forEach(function (c) {
      var x1 = front.x + (c[0] === 'l' ? 0 : front.w), y1 = front.y + (c[1] === 't' ? 0 : front.h);
      g.appendChild(el('line', { x1: x1, y1: y1, x2: x1 + depth.x, y2: y1 + depth.y, stroke: 'rgba(0,229,255,.26)', 'stroke-width': '1.1' }));
    });
    g.appendChild(el('rect', { x: front.x, y: front.y, width: front.w, height: front.h, rx: 10, fill: 'rgba(10,16,20,.72)', stroke: 'rgba(0,229,255,.5)', 'stroke-width': '1.4' }));

    /* mesh grid inside the housing */
    var grid = el('g', { 'clip-path': 'url(#housingClip)', opacity: '.5' });
    for (var x = front.x; x <= front.x + front.w; x += 17)
      grid.appendChild(el('line', { x1: x, y1: front.y, x2: x, y2: front.y + front.h, stroke: 'rgba(0,229,255,.10)' }));
    for (var y = front.y; y <= front.y + front.h; y += 17)
      grid.appendChild(el('line', { x1: front.x, y1: y, x2: front.x + front.w, y2: y, stroke: 'rgba(0,229,255,.10)' }));
    g.appendChild(grid);

    /* shafts */
    g.appendChild(el('path', { d: 'M60 214h96M60 206h96M60 222h96', stroke: 'rgba(0,229,255,.42)', 'stroke-width': '1.2', fill: 'none' }));
    g.appendChild(el('path', { d: 'M330 300h120M330 292h120M330 308h120', stroke: 'rgba(0,229,255,.32)', 'stroke-width': '1.2', fill: 'none' }));

    /* gears */
    var g1 = el('path', { d: gearPath(226, 246, 74, 60, 26, .2), fill: 'none', stroke: 'rgba(0,229,255,.62)', 'stroke-width': '1.3' });
    var g2 = el('path', { d: gearPath(330, 306, 46, 36, 17, .5), fill: 'none', stroke: 'rgba(0,229,255,.55)', 'stroke-width': '1.25' });
    g.appendChild(g1); g.appendChild(g2);
    g.appendChild(el('circle', { cx: 226, cy: 246, r: 20, fill: 'none', stroke: 'rgba(0,229,255,.3)' }));
    g.appendChild(el('circle', { cx: 330, cy: 306, r: 12, fill: 'none', stroke: 'rgba(0,229,255,.3)' }));
    g.appendChild(el('circle', { cx: 226, cy: 246, r: 6, fill: 'rgba(0,229,255,.5)' }));

    /* bearing seats */
    [ [168, 246, 16], [286, 246, 13], [330, 306, 9] ].forEach(function (b) {
      g.appendChild(el('circle', { cx: b[0], cy: b[1], r: b[2], fill: 'none', stroke: 'rgba(0,229,255,.32)', 'stroke-width': '1.1', 'stroke-dasharray': '3 3' }));
    });

    /* stress field */
    var stress = el('g', { style: 'mix-blend-mode:screen' });
    stress.appendChild(el('ellipse', { cx: 286, cy: 214, rx: 74, ry: 52, fill: 'url(#hot)' }));
    stress.appendChild(el('ellipse', { cx: 330, cy: 306, rx: 48, ry: 34, fill: 'url(#hot)', opacity: '.65' }));
    stress.appendChild(el('ellipse', { cx: 168, cy: 300, rx: 40, ry: 30, fill: 'url(#hot)', opacity: '.4' }));
    g.appendChild(stress);

    /* leader line to the badge */
    g.appendChild(el('path', { d: 'M286 214 L 340 150 L 430 120', stroke: 'rgba(0,229,255,.4)', 'stroke-width': '1', fill: 'none', 'stroke-dasharray': '4 4' }));
    g.appendChild(el('circle', { cx: 286, cy: 214, r: 3.2, fill: '#FFE45E', opacity: '.9' }));

    /* dimension line */
    g.appendChild(el('path', { d: 'M128 392h-14M114 382v20M386 392h14M400 382v20M128 392h258', stroke: 'rgba(0,229,255,.22)', 'stroke-width': '.9', fill: 'none' }));
    svg.appendChild(g);
  }
  drawMesh();

  /* ---------- reveal ---------- */
  var rvs = [].slice.call(document.querySelectorAll('.rv'));
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.06 });
    rvs.forEach(function (n) { io.observe(n); });
  } else rvs.forEach(function (n) { n.classList.add('in'); });

  /* ---------- waitlist ---------- */
  var API = '';                       /* same origin: server.py serves this page and the API */
  var form = $('#wl'), state = $('#wlState'), btn = $('#wlBtn'), ok = $('#wlOk');
  var started = Date.now();

  try {
    fetch(API + '/visit', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ref: new URLSearchParams(location.search).get('ref') || 'direct' })
    }).catch(function () {});
  } catch (e) { /* ignore */ }

  function setErr(key, msg) {
    var n = form.querySelector('[data-err="' + key + '"]');
    if (n) n.textContent = msg || '';
  }
  function clearAll() { ['name', 'email', 'industry', 'company_size', 'design_partner', 'consent'].forEach(function (k) { setErr(k, ''); }); }

  function busy(on) {
    btn.disabled = on;
    btn.textContent = on ? 'Sending…' : 'Request Early Access →';
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    clearAll();
    var fd = new FormData(form);
    var d = {};
    ['name', 'email', 'company', 'role', 'industry', 'company_size', 'components', 'country', 'design_partner', 'website'].forEach(function (k) {
      d[k] = (fd.get(k) || '').toString().trim();
    });
    d.consent = fd.get('consent') === 'on';
    d.fill_ms = Date.now() - started;

    var bad = false;
    if (!d.name) { setErr('name', 'Please enter your name.'); bad = true; }
    if (!/^[^@\s]{1,64}@[^@\s]+\.[A-Za-z]{2,}$/.test(d.email)) { setErr('email', 'Please enter a valid work e-mail.'); bad = true; }
    if (!d.industry) { setErr('industry', 'Please choose an industry.'); bad = true; }
    if (!d.company_size) { setErr('company_size', 'Please choose a company size.'); bad = true; }
    if (!d.design_partner) { setErr('design_partner', 'Please answer the design partner question.'); bad = true; }
    if (!d.consent) { setErr('consent', 'Please tick the consent box so we may store your details.'); bad = true; }
    if (bad) {
      state.textContent = 'Please check the highlighted fields.';
      state.className = 'form-state bad';
      var first = form.querySelector('.msg:not(:empty)');
      if (first) { var f = form.querySelector('#' + ({ name: 'f-name', email: 'f-email', industry: 'f-industry', company_size: 'f-size', design_partner: 'f-partner', consent: 'f-consent' }[first.dataset.err])); if (f) f.focus(); }
      return;
    }

    busy(true);
    state.textContent = '';
    state.className = 'form-state';

    var ctl = window.AbortController ? new AbortController() : null;
    var timer = ctl ? setTimeout(function () { ctl.abort(); }, 15000) : null;

    fetch(API + '/waitlist', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(d), signal: ctl ? ctl.signal : undefined
    }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (b) { return { status: r.status, body: b }; });
    }).then(function (res) {
      if (timer) clearTimeout(timer);
      busy(false);
      if (res.status === 200 && res.body.success) {
        form.style.display = 'none';
        ok.classList.add('on');
        $('#wlOkMsg').textContent = d.design_partner === 'no'
          ? "We'll email you when new features open."
          : "We'll email you when new features open. You also asked about the Design Partner program — we'll contact you personally.";
        ok.scrollIntoView({ behavior: 'smooth', block: 'center' });
        return;
      }
      if (res.status === 429) { state.textContent = res.body.error || 'Too many sign-ups from this connection. Please try again later.'; state.className = 'form-state bad'; return; }
      if (res.body && res.body.fields) {
        Object.keys(res.body.fields).forEach(function (k) { setErr(k === 'company_size' ? 'company_size' : k, res.body.fields[k]); });
        state.textContent = res.body.error || 'Please check the highlighted fields.';
        state.className = 'form-state bad';
        return;
      }
      state.textContent = (res.body && res.body.error) ? res.body.error : 'Sign-up failed. Please try again.';
      state.className = 'form-state bad';
    }).catch(function () {
      if (timer) clearTimeout(timer);
      busy(false);
      state.textContent = 'Network error. Please try again.';
      state.className = 'form-state bad';
    });
  });
})();
