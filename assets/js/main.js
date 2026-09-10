/* Vinstitution v2 — behaviour layer.
   Ports the design-canvas component logic to vanilla JS. No dependencies. */
(function () {
  'use strict';

  var $  = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function pad(n) { return n < 10 ? '0' + n : String(n); }
  function fmt(total) {
    return pad(Math.floor(total / 3600)) + ':' + pad(Math.floor((total % 3600) / 60)) + ':' + pad(total % 60);
  }

  /* ---------------------------------------------------------------- theme */
  var themeBtn = $('#theme-toggle');
  function themeLabel() {
    var dark = document.documentElement.getAttribute('data-theme') === 'dark';
    var label = dark ? 'Switch to day mode' : 'Switch to night mode';
    if (themeBtn) { themeBtn.setAttribute('aria-label', label); themeBtn.setAttribute('title', label); }
  }
  themeLabel();
  if (themeBtn) {
    themeBtn.addEventListener('click', function () {
      var next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      try { localStorage.setItem('vin-theme', next); } catch (e) {}
      themeLabel();
    });
  }

  /* ------------------------------------------------------------ mobile nav */
  var navBtn = $('#nav-toggle');
  var mnav   = $('#mnav');
  function setNav(open) {
    if (!mnav) return;
    mnav.hidden = !open;
    if (navBtn) navBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    document.body.style.overflow = open ? 'hidden' : '';
  }
  if (navBtn) navBtn.addEventListener('click', function () { setNav(mnav.hidden); });
  if (mnav) mnav.addEventListener('click', function (e) { if (e.target.closest('a')) setNav(false); });
  window.addEventListener('keydown', function (e) { if (e.key === 'Escape') setNav(false); });
  // a resize up to desktop must not leave the body scroll-locked
  var mq = window.matchMedia('(max-width: 900px)');
  var onMq = function () { if (!mq.matches) setNav(false); };
  if (mq.addEventListener) mq.addEventListener('change', onMq); else if (mq.addListener) mq.addListener(onMq);

  /* -------------------------------------------- scroll progress / back to top */
  var bar = $('#scroll-progress');
  var top = $('#to-top');
  function onScroll() {
    var h = document.documentElement.scrollHeight - window.innerHeight;
    var p = h > 0 ? Math.min(window.scrollY / h, 1) : 0;
    if (bar) bar.style.width = (p * 100).toFixed(2) + '%';
    if (top) top.style.display = window.scrollY > 700 ? 'grid' : 'none';
  }
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  /* ------------------------------------------------------------- reveals */
  (function () {
    var nodes = $$('[data-rv]');
    if (!nodes.length || reduced || !('IntersectionObserver' in window)) return;
    var vh = window.innerHeight;
    var pending = nodes.filter(function (el) {
      if (el.getBoundingClientRect().top < vh * 0.9) return false;
      el.style.opacity = '0';
      el.style.transform = 'translateY(24px)';
      el.style.transition = 'opacity .75s cubic-bezier(.2,.7,.3,1), transform .75s cubic-bezier(.2,.7,.3,1)';
      return true;
    });
    if (!pending.length) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        io.unobserve(e.target);
        e.target.style.opacity = '1';
        e.target.style.transform = 'none';
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.06 });
    pending.forEach(function (el) { io.observe(el); });
  })();

  /* ------------------------------------------------------------ counters */
  (function () {
    var nodes = $$('[data-count]');
    if (!nodes.length || reduced || !('IntersectionObserver' in window)) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var el = e.target; io.unobserve(el);
        var target = parseFloat(el.getAttribute('data-count'));
        var suffix = el.getAttribute('data-suffix') || '';
        var t0 = performance.now(), dur = 1200;
        (function tick(now) {
          var p = Math.min((now - t0) / dur, 1);
          el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3))) + suffix;
          if (p < 1) requestAnimationFrame(tick);
        })(performance.now());
      });
    }, { threshold: 0.5 });
    nodes.forEach(function (el) { io.observe(el); });
  })();

  /* ------------------------------------------- product mock-UI: tab groups */
  $$('.mock-tab').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var group = btn.getAttribute('data-tabset');
      var idx   = btn.getAttribute('data-tab');
      $$('.mock-tab[data-tabset="' + group + '"]').forEach(function (b) {
        b.classList.toggle('is-active', b === btn);
      });
      $$('[data-panel^="' + group + '-"]').forEach(function (p) {
        p.hidden = p.getAttribute('data-panel') !== group + '-' + idx;
      });
    });
  });

  /* ------------------------------------ Digi Classroom question chips (dg) */
  $$('.mock-q').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var idx = btn.getAttribute('data-q');
      $$('.mock-q').forEach(function (b) { b.classList.toggle('is-active', b === btn); });
      $$('[data-panel^="dg-"]').forEach(function (p) {
        p.hidden = p.getAttribute('data-panel') !== 'dg-' + idx;
      });
    });
  });

  /* --------------------------------------------- PDLMS audio player mockup */
  (function () {
    var play  = $('#pd-play');
    var panel = $('[data-panel="pd-2"]');
    var barEl = $('#pd-bar');
    var timeEl = $('#pd-time');
    if (!play || !panel) return;
    var pct = 34, playing = false, timer = null;

    function paint() {
      if (barEl) barEl.style.width = pct + '%';
      if (timeEl) timeEl.textContent = fmt(Math.round(pct * 1.9)).slice(3);
    }
    paint();

    play.addEventListener('click', function () {
      playing = !playing;
      panel.classList.toggle('is-playing', playing);
      play.setAttribute('aria-label', playing ? 'Pause' : 'Play');
      var showPlaying = play.querySelector('.ico-playing');
      var showPaused  = play.querySelector('.ico-paused');
      if (showPlaying) showPlaying.hidden = !playing;
      if (showPaused)  showPaused.hidden  = playing;
      clearInterval(timer);
      if (playing) {
        timer = setInterval(function () { pct = pct >= 100 ? 0 : pct + 1; paint(); }, 260);
      }
    });
    // the canvas renders only one icon at a time; start from the paused state
    var a = play.querySelector('.ico-playing'); if (a) a.hidden = true;
    var b = play.querySelector('.ico-paused');  if (b) b.hidden = false;
  })();

  /* ------------------------------------------ Practest timer + answer grid */
  (function () {
    var el = $('#exam-time');
    if (el) {
      var secs = 724;
      el.textContent = fmt(secs);
      setInterval(function () { secs = secs > 0 ? secs - 1 : 5400; el.textContent = fmt(secs); }, 1000);
    }
    var titles = ['Not visited', 'Answered', 'Not answered', 'Marked'];
    $$('.cell').forEach(function (cell) {
      cell.addEventListener('click', function () {
        var cur = 0;
        for (var i = 0; i < 4; i++) if (cell.classList.contains('is-' + i)) cur = i;
        var next = (cur + 1) % 4;
        cell.classList.remove('is-0', 'is-1', 'is-2', 'is-3');
        cell.classList.add('is-' + next);
        cell.setAttribute('title', titles[next]);
      });
    });
  })();

  /* ---------------------------------------------------------------- form */
  (function () {
    var form = $('#enquiry');
    var msg  = $('#form-msg');
    if (!form) return;

    function say(kind, text) {
      if (!msg) return;
      if (!text) { msg.style.display = 'none'; msg.textContent = ''; return; }
      var ok = kind === 'ok';
      msg.style.display  = 'block';
      msg.style.padding  = '14px 16px';
      msg.style.borderRadius = '13px';
      msg.style.background = ok ? 'var(--ok-t)' : 'var(--vv-t)';
      msg.style.color      = ok ? 'var(--ok)'   : 'var(--vv)';
      msg.style.border     = '1px solid ' + (ok ? 'var(--ok)' : 'var(--vv)');
      msg.textContent = text;
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var hp = form.querySelector('[name="website"]');
      if (hp && hp.value) return;                    // honeypot: stay silent
      var btn = form.querySelector('button[type="submit"]');
      var label = btn ? btn.textContent : '';
      if (btn) { btn.disabled = true; btn.textContent = 'Sending…'; btn.style.opacity = '.7'; }
      say('', '');
      fetch(form.action, { method: 'POST', body: new FormData(form) })
        .then(function (r) { return r.json().catch(function () { return { ok: r.ok }; }); })
        .then(function (data) {
          if (data && data.ok) {
            say('ok', 'Thank you — your enquiry has reached us. We reply within one working day.');
            form.reset();
          } else {
            say('err', (data && data.error) || 'Something went wrong. Please email tech@vinstitution.com instead.');
          }
        })
        .catch(function () {
          say('err', 'Network error. Please email tech@vinstitution.com instead.');
        })
        .then(function () {
          if (btn) { btn.disabled = false; btn.textContent = label; btn.style.opacity = ''; }
        });
    });
  })();

  /* ---------------------------------------------------------------- year */
  var year = document.getElementById('year');
  if (year) year.textContent = String(new Date().getFullYear());
  var yr = $('[data-year]');
  if (yr) yr.textContent = String(new Date().getFullYear());

  /* ------------------------------------------------------------------------
     Product pages (products/*.html) still use the earlier component markup.
     These hooks keep them working from this one bundle.
     --------------------------------------------------------------------- */

  var hdr = $('.hdr');
  if (hdr) {
    var stick = function () { hdr.classList.toggle('is-stuck', window.scrollY > 8); };
    stick();
    window.addEventListener('scroll', stick, { passive: true });
  }

  var burger = $('.burger');
  var legacyNav = $('.mnav');
  if (burger && legacyNav) {
    var setLegacyNav = function (open) {
      burger.setAttribute('aria-expanded', String(open));
      legacyNav.classList.toggle('is-open', open);
      document.body.style.overflow = open ? 'hidden' : '';
    };
    burger.addEventListener('click', function () {
      setLegacyNav(burger.getAttribute('aria-expanded') !== 'true');
    });
    legacyNav.addEventListener('click', function (e) { if (e.target.closest('a')) setLegacyNav(false); });
    window.addEventListener('keydown', function (e) { if (e.key === 'Escape') setLegacyNav(false); });
    window.addEventListener('resize', function () { if (window.innerWidth > 860) setLegacyNav(false); });
  }

  (function () {
    var reveals = $$('.rv');
    if (!reveals.length) return;
    if (reduced || !('IntersectionObserver' in window)) {
      reveals.forEach(function (el) { el.classList.add('in'); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        io.unobserve(el);
        setTimeout(function () { el.classList.add('in'); },
                   parseInt(el.getAttribute('data-rv-delay') || '0', 10));
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    reveals.forEach(function (el) { io.observe(el); });
  })();

  (function () {
    var bars = $$('.vbar');
    if (!bars.length || !('IntersectionObserver' in window)) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var fill = entry.target.querySelector('i');
        if (fill) fill.style.width = entry.target.getAttribute('data-w') || '60%';
        io.unobserve(entry.target);
      });
    }, { threshold: 0.4 });
    bars.forEach(function (el) {
      var fill = el.querySelector('i');
      if (fill) fill.style.width = '0%';
      io.observe(el);
    });
  })();
})();
