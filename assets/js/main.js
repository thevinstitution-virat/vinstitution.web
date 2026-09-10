/* ==========================================================================
   Vinstitution — site behaviour
   No framework. Progressive enhancement only: everything below is optional
   polish, the page reads and works with JS disabled.
   ========================================================================== */
(function () {
  'use strict';

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ------------------------------------------------ sticky header state -- */
  var hdr = document.querySelector('.hdr');
  if (hdr) {
    var onScroll = function () {
      hdr.classList.toggle('is-stuck', window.scrollY > 8);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* -------------------------------------------------------- mobile nav -- */
  var burger = document.querySelector('.burger');
  var mnav = document.querySelector('.mnav');
  if (burger && mnav) {
    var setNav = function (open) {
      burger.setAttribute('aria-expanded', String(open));
      mnav.classList.toggle('is-open', open);
      document.body.style.overflow = open ? 'hidden' : '';
    };
    burger.addEventListener('click', function () {
      setNav(burger.getAttribute('aria-expanded') !== 'true');
    });
    mnav.addEventListener('click', function (e) {
      if (e.target.closest('a')) setNav(false);
    });
    window.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') setNav(false);
    });
    window.addEventListener('resize', function () {
      if (window.innerWidth > 860) setNav(false);
    });
  }

  /* ----------------------------------------------------- reveal on scroll -- */
  var reveals = document.querySelectorAll('.rv');
  if (reveals.length) {
    if (reduced || !('IntersectionObserver' in window)) {
      reveals.forEach(function (el) { el.classList.add('in'); });
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var el = entry.target;
          var delay = parseInt(el.getAttribute('data-rv-delay') || '0', 10);
          setTimeout(function () { el.classList.add('in'); }, delay);
          io.unobserve(el);
        });
      }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
      reveals.forEach(function (el) { io.observe(el); });
    }
  }

  /* ---------------------------------------------------- count-up stats -- */
  var counters = document.querySelectorAll('[data-count]');
  if (counters.length && !reduced && 'IntersectionObserver' in window) {
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        cio.unobserve(el);
        var target = parseFloat(el.getAttribute('data-count'));
        var suffix = el.getAttribute('data-suffix') || '';
        var dur = 1100;
        var t0 = performance.now();
        var tick = function (now) {
          var p = Math.min((now - t0) / dur, 1);
          var eased = 1 - Math.pow(1 - p, 3);
          el.textContent = Math.round(target * eased) + suffix;
          if (p < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
      });
    }, { threshold: 0.5 });
    counters.forEach(function (el) { cio.observe(el); });
  }

  /* -------------------------------------------------------- bar fillers -- */
  var bars = document.querySelectorAll('.vbar');
  if (bars.length && 'IntersectionObserver' in window) {
    var bio = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var fill = entry.target.querySelector('i');
        if (fill) fill.style.width = entry.target.getAttribute('data-w') || '60%';
        bio.unobserve(entry.target);
      });
    }, { threshold: 0.4 });
    bars.forEach(function (el) {
      var fill = el.querySelector('i');
      if (fill) fill.style.width = '0%';
      bio.observe(el);
    });
  }

  /* ------------------------------------------------------- contact form -- */
  var form = document.querySelector('#enquiry');
  if (form) {
    var msg = form.querySelector('.fmsg');
    var btn = form.querySelector('button[type="submit"]');
    var say = function (kind, text) {
      if (!msg) return;
      msg.className = 'fmsg ' + kind;
      msg.textContent = text;
    };

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      // Honeypot: bots fill hidden fields, humans never see them.
      if (form.querySelector('[name="website"]').value) return;

      var label = btn ? btn.textContent : '';
      if (btn) { btn.disabled = true; btn.textContent = 'Sending…'; }
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
          say('err', 'Network problem. Please email tech@vinstitution.com or call +91 93109 59596.');
        })
        .finally(function () {
          if (btn) { btn.disabled = false; btn.textContent = label; }
        });
    });
  }

  /* --------------------------------------------------------- year stamp -- */
  var yr = document.querySelector('[data-year]');
  if (yr) yr.textContent = String(new Date().getFullYear());
})();
