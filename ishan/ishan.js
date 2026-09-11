/* ===========================================================================
   Ishan AI — floating action stack + chat widget for vinstitution.com
   No dependencies. Everything below is progressive enhancement: with JS off
   the page is unaffected, and the call / WhatsApp links still work because
   they are real anchors.
   =========================================================================== */
(function () {
  'use strict';

  var PHONE   = '+919310959596';
  var PHONE_H = '+91 93109 59596';
  var WA      = '919310959596';
  var WA_TEXT = 'Hi Vinstitution — I have a question about your platforms.';

  // Resolve paths from this script's own URL, so the widget behaves the same
  // on / and on /products/*.html without hard-coded relative paths.
  var here = (document.currentScript && document.currentScript.src) || '';
  var base = here ? here.replace(/[^/]*$/, '') : '/ishan/';
  var CHAT_URL = base + 'chat.php';
  var LEAD_URL = base.replace(/ishan\/$/, '') + 'contact.php';

  var el = {}, history = [], busy = false, leadShown = false, greeted = false;

  /* ------------------------------------------------------------- helpers */
  function store(k, v) { try { sessionStorage.setItem(k, v); } catch (e) {} }
  function load(k) { try { return sessionStorage.getItem(k); } catch (e) { return null; } }

  function ref() {
    var r = load('ishan-ref');
    if (!r) {
      r = 'VIN-' + Math.random().toString(16).slice(2, 8).toUpperCase();
      store('ishan-ref', r);
    }
    return r;
  }

  function saveHistory() {
    try { store('ishan-log', JSON.stringify(history.slice(-12))); } catch (e) {}
  }

  function svg(d, w) {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
           'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"' +
           (w ? ' class="' + w + '"' : '') + '>' + d + '</svg>';
  }

  var ICON = {
    phone: '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .3 1.9.7 2.8a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.3-1.2a2 2 0 0 1 2.1-.5c.9.4 1.8.6 2.8.7a2 2 0 0 1 1.7 2Z"></path>',
    wa: '<path d="M20.5 3.5A11.9 11.9 0 0 0 3.6 19.6L2 22l2.5-1.6A11.9 11.9 0 1 0 20.5 3.5Z"></path><path d="M8.5 8.5c.4-.2.9 0 1.1.4l.8 1.5c.2.4.1.8-.2 1.1l-.5.5a7 7 0 0 0 3.3 3.3l.5-.5c.3-.3.7-.4 1.1-.2l1.5.8c.4.2.6.7.4 1.1-.3.7-1 1.3-1.9 1.4-2.7.2-6.9-3.6-7.4-6.9-.1-.9.4-1.8 1.3-2.5Z"></path>',
    spark: '<path d="M12 3v3M12 18v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M3 12h3M18 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"></path><circle cx="12" cy="12" r="3.2"></circle>',
    close: '<path d="M18 6 6 18M6 6l12 12"></path>',
    send: '<path d="M22 2 11 13M22 2l-7 20-4-9-9-4Z"></path>',
    out: '<path d="M7 17 17 7M9 7h8v8"></path>'
  };

  /* ---------------------------------------------------------------- build */
  function fabs() {
    var stack = document.createElement('div');
    stack.className = 'vin-fab';

    var chat = document.createElement('button');
    chat.type = 'button';
    chat.className = 'vin-fab__btn vin-fab__btn--chat';
    chat.setAttribute('aria-label', 'Ask Ishan AI');
    chat.innerHTML = svg(ICON.spark, 'vin-fab__ico') + '<span class="vin-fab__label">Ask Ishan AI</span>';
    chat.addEventListener('click', open);

    var wa = document.createElement('a');
    wa.className = 'vin-fab__btn vin-fab__btn--wa';
    wa.href = 'https://wa.me/' + WA + '?text=' + encodeURIComponent(WA_TEXT);
    wa.target = '_blank';
    wa.rel = 'noopener';
    wa.setAttribute('aria-label', 'WhatsApp us on ' + PHONE_H);
    wa.innerHTML = svg(ICON.wa, 'vin-fab__ico') + '<span class="vin-fab__label">WhatsApp</span>';

    var call = document.createElement('a');
    call.className = 'vin-fab__btn vin-fab__btn--call';
    call.href = 'tel:' + PHONE;
    call.setAttribute('aria-label', 'Call us on ' + PHONE_H);
    call.innerHTML = svg(ICON.phone, 'vin-fab__ico') + '<span class="vin-fab__label">Call</span>';

    stack.appendChild(chat);
    stack.appendChild(wa);
    stack.appendChild(call);
    document.body.appendChild(stack);
    el.stack = stack;
  }

  function panel() {
    var p = document.createElement('div');
    p.className = 'ishan';
    p.setAttribute('role', 'dialog');
    p.setAttribute('aria-label', 'Chat with Ishan AI');
    p.setAttribute('aria-modal', 'false');
    p.innerHTML =
      '<div class="ishan__head">' +
        '<span class="ishan__avatar" aria-hidden="true">इ</span>' +
        '<span class="ishan__who">' +
          '<span class="ishan__name">Ishan AI</span>' +
          '<span class="ishan__sub"><span class="ishan__dot"></span>Vinstitution assistant · हिन्दी / English</span>' +
        '</span>' +
        '<button type="button" class="ishan__x" aria-label="Close chat">' + svg(ICON.close) + '</button>' +
      '</div>' +
      '<div class="ishan__log" role="log" aria-live="polite"></div>' +
      '<div class="ishan__chips"></div>' +
      '<div class="ishan__composer">' +
        '<textarea class="ishan__input" rows="1" placeholder="Ask about our platforms…" aria-label="Your message"></textarea>' +
        '<button type="button" class="ishan__send" aria-label="Send">' + svg(ICON.send) + '</button>' +
      '</div>' +
      '<p class="ishan__legal">Ishan is an AI assistant and can be wrong. For anything binding, email ' +
        '<a href="mailto:tech@vinstitution.com">tech@vinstitution.com</a>.</p>';
    document.body.appendChild(p);

    el.panel = p;
    el.log   = p.querySelector('.ishan__log');
    el.chips = p.querySelector('.ishan__chips');
    el.input = p.querySelector('.ishan__input');
    el.send  = p.querySelector('.ishan__send');
    el.close = p.querySelector('.ishan__x');
  }

  /* -------------------------------------------------------------- render */
  function scroll() { if (el.log) el.log.scrollTop = el.log.scrollHeight; }

  function bubble(text, who) {
    var d = document.createElement('div');
    d.className = 'ishan__msg ishan__msg--' + (who === 'me' ? 'me' : 'bot');
    d.textContent = text;
    el.log.appendChild(d);
    scroll();
    return d;
  }

  function typing(on) {
    var t = el.log.querySelector('.ishan__typing');
    if (on && !t) {
      t = document.createElement('div');
      t.className = 'ishan__typing';
      t.innerHTML = '<i></i><i></i><i></i>';
      el.log.appendChild(t);
      scroll();
    } else if (!on && t) {
      t.remove();
    }
  }

  function chips(list) {
    el.chips.innerHTML = '';
    list.forEach(function (c) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'ishan__chip';
      b.textContent = c;
      b.addEventListener('click', function () { send(c); });
      el.chips.appendChild(b);
    });
  }

  function waCard(spec) {
    var a = document.createElement('a');
    a.className = 'ishan__card ishan__card--wa';
    a.href = spec.url;
    a.target = '_blank';
    a.rel = 'noopener';
    a.innerHTML = svg(ICON.wa) + '<span>' + spec.label + '</span>' + svg(ICON.out);
    el.log.appendChild(a);
    scroll();
  }

  function leadCard(spec) {
    if (leadShown) return;
    leadShown = true;
    chips([]);

    var box = document.createElement('div');
    box.className = 'ishan__lead';
    box.innerHTML =
      '<h4></h4><p></p>' +
      '<input type="text" name="name" placeholder="Your name" autocomplete="name" required>' +
      '<input type="email" name="email" placeholder="Email (optional)" autocomplete="email">' +
      '<input type="tel" name="phone" placeholder="Phone" autocomplete="tel" required>' +
      '<button type="button"></button>' +
      '<p class="ishan__err" hidden></p>';
    box.querySelector('h4').textContent = spec.title || 'Let the team pick this up';
    box.querySelector('p').textContent = spec.note || '';
    var btn = box.querySelector('button');
    btn.textContent = spec.cta || 'Send to the team';
    var err = box.querySelector('.ishan__err');

    btn.addEventListener('click', function () {
      var name  = box.querySelector('[name=name]').value.trim();
      var email = box.querySelector('[name=email]').value.trim();
      var phone = box.querySelector('[name=phone]').value.trim();
      err.hidden = true;
      if (!name)  { err.textContent = 'Please add your name.'; err.hidden = false; return; }
      if (!phone) { err.textContent = 'Please add your phone number.'; err.hidden = false; return; }
      // A required field that accepts "x" is not really required. Count digits
      // rather than pattern-matching, so +91 / spaces / dashes all pass.
      if (phone.replace(/\D/g, '').length < 8) {
        err.textContent = 'Please add a valid phone number.'; err.hidden = false; return;
      }
      // The email is optional, but a typo in one that was offered is worth catching
      // now rather than discovering it when a reply bounces.
      if (email && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
        err.textContent = 'That email does not look right — check it, or leave it blank.';
        err.hidden = false; return;
      }

      btn.disabled = true;
      btn.textContent = 'Sending…';

      // Reuse the site's own enquiry handler rather than standing up a second
      // mail path: it already validates, rate-limits and reaches the team.
      var said = history.filter(function (m) { return m.role === 'user'; })
                        .slice(-6).map(function (m) { return '• ' + m.content; }).join('\n');
      var fd = new FormData();
      fd.append('name', name);
      fd.append('email', email);
      fd.append('phone', phone);
      fd.append('org', '');
      fd.append('interest', 'Ishan AI chat');
      fd.append('message', 'Enquiry raised from the Ishan AI chat [ref ' + ref() + ']\n\n' +
                           'What they asked:\n' + (said || '(no messages captured)'));
      fd.append('website', '');   // honeypot, must stay empty

      fetch(LEAD_URL, { method: 'POST', body: fd })
        .then(function (r) { return r.json().catch(function () { return { ok: r.ok }; }); })
        .then(function (d) {
          if (d && d.ok) {
            box.innerHTML = '';
            box.style.borderColor = 'var(--ok)';
            var ok = document.createElement('p');
            ok.style.cssText = 'margin:0;font-size:13.5px;font-weight:700;color:var(--ok)';
            ok.textContent = 'Thank you — the team has this and will reply within one working day.';
            box.appendChild(ok);
          } else {
            err.textContent = (d && d.error) || 'That did not go through. Please email tech@vinstitution.com.';
            err.hidden = false;
            btn.disabled = false;
            btn.textContent = spec.cta || 'Send to the team';
          }
        })
        .catch(function () {
          err.textContent = 'Network problem. Please email tech@vinstitution.com.';
          err.hidden = false;
          btn.disabled = false;
          btn.textContent = spec.cta || 'Send to the team';
        });
    });

    el.log.appendChild(box);
    scroll();
  }

  /* ------------------------------------------------------------- network */
  function send(text) {
    text = (text || '').trim();
    if (!text || busy) return;

    bubble(text, 'me');
    history.push({ role: 'user', content: text });
    saveHistory();
    el.input.value = '';
    el.input.style.height = 'auto';
    chips([]);
    busy = true;
    el.send.disabled = true;
    typing(true);

    fetch(CHAT_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: history.slice(-8),
        ref: ref(),
        lead_shown: leadShown,
        channel: 'web'
      })
    })
      .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
      .then(function (res) {
        typing(false);
        if (!res.ok) {
          bubble((res.d && res.d.error) || 'Something went wrong. Please try again.', 'bot');
          return;
        }
        var d = res.d || {};
        if (d.reply) {
          bubble(d.reply, 'bot');
          history.push({ role: 'assistant', content: d.reply });
          saveHistory();
        }
        if (d.lead) leadCard(d.lead);
        if (d.whatsapp) waCard(d.whatsapp);
      })
      .catch(function () {
        typing(false);
        bubble('I could not reach the server. Please try again, or WhatsApp us on ' + PHONE_H + '.', 'bot');
      })
      .then(function () {
        busy = false;
        el.send.disabled = false;
        el.input.focus();
      });
  }

  /* ------------------------------------------------- open / close / keys */
  function greet() {
    if (greeted) return;
    greeted = true;
    var saved = null;
    try { saved = JSON.parse(load('ishan-log') || 'null'); } catch (e) {}
    if (saved && saved.length) {
      history = saved;
      saved.forEach(function (m) { bubble(m.content, m.role === 'user' ? 'me' : 'bot'); });
      return;
    }
    bubble('Hi, I\'m Ishan — I look after questions about Vinstitution. ' +
           'We build four platforms: Vidyaverse, Book Buddy, Study Buddy and Practest. ' +
           'What would you like to know?\n\nआप हिन्दी में भी पूछ सकते हैं.', 'bot');
    chips(['What is Vidyaverse?', 'How does the single login work?',
           'हिन्दी में बात करें', 'Book a demo']);
  }

  function keyboard() {
    var vv = window.visualViewport;
    if (!vv) return;
    var kb = Math.max(0, window.innerHeight - vv.height - vv.offsetTop);
    var prev = document.documentElement.style.getPropertyValue('--ishan-kb');
    var next = kb + 'px';
    if (prev === next) return;                      // only re-pin on a real change
    document.documentElement.style.setProperty('--ishan-kb', next);
    if (el.panel && el.panel.classList.contains('open')) scroll();
  }

  function open() {
    el.panel.classList.add('open');
    document.body.classList.add('ishan-open');
    greet();
    setTimeout(function () { el.input.focus(); }, 60);
  }

  function close() {
    el.panel.classList.remove('open');
    document.body.classList.remove('ishan-open');
  }

  function wire() {
    el.close.addEventListener('click', close);
    el.send.addEventListener('click', function () { send(el.input.value); });
    el.input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(el.input.value); }
    });
    el.input.addEventListener('input', function () {
      el.input.style.height = 'auto';
      el.input.style.height = Math.min(el.input.scrollHeight, 110) + 'px';
    });
    window.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && el.panel.classList.contains('open')) close();
    });
    var vv = window.visualViewport;
    if (vv) { vv.addEventListener('resize', keyboard); vv.addEventListener('scroll', keyboard); }
  }

  function init() {
    if (document.querySelector('.vin-fab')) return;
    fabs();
    panel();
    wire();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
