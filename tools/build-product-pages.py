# Build products/*.html in the v2 design language.
#
# Content comes from design/product-content.json (extracted from the v1 pages,
# so every word is carried across verbatim). Layout is extrapolated from
# design/vinstitution-v2.dc.html and expressed with the classes in
# assets/css/product.css. The interactive hero panels deliberately reuse the
# .mock-tab / .mock-panel / .cell hooks that main.js already drives.
#
#   python tools/build-product-pages.py
import io, json, os, re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VER = "3"
content = json.load(io.open(os.path.join(ROOT, "design", "product-content.json"), encoding="utf-8"))

def fix_href(h):
    """the v1 pages wrote sibling links as ../products/x.html; from products/ that is just x.html"""
    return re.sub(r"^\.\./products/", "", h)

def clean_links(html):
    html = re.sub(r'href="\.\./products/', 'href="', html)
    return re.sub(r'\s*style="color:var\(--gold\)"', '', html)


# --------------------------------------------------------------- per product
PRODUCTS = {
    "vidyaverse": dict(
        acc="vv", name="Vidyaverse", app="https://vidyaverse.vinstitution.com",
        app_label="Open Vidyaverse", url_hint="vidyaverse.vinstitution.com / dashboard",
        em="operating system",
        facts=[("47", "Modules"), ("6", "Module categories"),
               ("1", "Institutional login"), ("ISO 9001", "2015 certified")],
        panel="tabs_vv"),
    "pdlms": dict(
        acc="pd", name="PDLMS Pro", app="https://pdlms.vinstitution.com",
        app_label="Open PDLMS Pro", url_hint="pdlms.vinstitution.com / reader",
        em="digital library",
        facts=[("4", "Ways to read a book"), ("Varta", "Cites the paragraph"),
               ("Multi-tenant", "Per-institution libraries"), ("SSO", "From Vidyaverse")],
        panel="tabs_pd"),
    "digi-classroom": dict(
        acc="dg", name="Digi Classroom", app="https://dgcl.vinstitution.com",
        app_label="Open Digi Classroom", url_hint="dgcl.vinstitution.com / ask",
        em="shows its sources",
        facts=[("6–12", "Classes covered"), ("NCERT", "Grounded answers"),
               ("Sarvagya", "Agentic RAG engine"), ("CBSE &amp; ICSE", "Boards")],
        panel="ask_dg"),
    "practest": dict(
        acc="pt", name="e-Learning Practest", app="https://practest.live",
        app_label="Open Practest", url_hint="practest.live / mock-test",
        em="the real exam hall",
        facts=[("5", "Exam families"), ("Server-timed", "Real exam clock"),
               ("Negative marking", "Exact paper rules"), ("Video", "Course library")],
        panel="exam_pt"),
}
ORDER = ["vidyaverse", "pdlms", "digi-classroom", "practest"]
NAV = [("vidyaverse", "Vidyaverse"), ("pdlms", "PDLMS Pro"),
       ("digi-classroom", "Digi Classroom"), ("practest", "Practest")]

ICON = {
 "arrow_out": '<path d="M7 17 17 7M9 7h8v8"></path>',
 "arrow_down": '<path d="M12 5v14M19 12l-7 7-7-7"></path>',
 "up": '<path d="M12 19V5M5 12l7-7 7 7"></path>',
 "sun": '<circle cx="12" cy="12" r="4.2"></circle><path d="M12 2v2.4M12 19.6V22M2 12h2.4M19.6 12H22M4.9 4.9l1.7 1.7M17.4 17.4l1.7 1.7M19.1 4.9l-1.7 1.7M6.6 17.4l-1.7 1.7"></path>',
 "moon": '<path d="M21 13.2A8.6 8.6 0 1 1 10.8 3a6.8 6.8 0 0 0 10.2 10.2Z"></path>',
 "menu": '<path d="M4 7h16M4 12h16M4 17h16"></path>',
 "users": '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8"></path>',
 "check": '<path d="m9 11 3 3L22 4M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>',
 "rupee": '<path d="M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>',
 "book": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z"></path>',
 "play": '<path d="M7 4v16l13-8z"></path>',
 "pause": '<path d="M8 4h3v16H8zM13 4h3v16h-3z"></path>',
 "spark": '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M18.4 5.6l-2.8 2.8M8.4 15.6l-2.8 2.8"></path>',
 "clock": '<circle cx="12" cy="12" r="9"></circle><path d="M12 7v5l3.2 2"></path>',
}

def svg(name, size=16, sw="2"):
    return ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="%s" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" '
            'style="width:%dpx;height:%dpx">%s</svg>' % (sw, size, size, ICON[name]))

def em_wrap(text, phrase):
    """wrap the key phrase of an h1 in <em> so it takes the accent + underline"""
    if phrase and phrase in text:
        return text.replace(phrase, "<em>%s</em>" % phrase, 1)
    return text

# ------------------------------------------------------------- hero panels
def row(icon, title, sub, value):
    return ('<div class="row"><span class="row__ic">%s</span><span class="row__t"><b>%s</b>'
            '<span>%s</span></span><span class="row__v">%s</span></div>'
            % (svg(icon, 14), title, sub, value))

def panel_tabs_vv():
    p0 = ("".join([row("users", "Students on roll", "+18 this week", "1,248"),
                   row("check", "Present today", "1,201 / 1,248", "96.2%"),
                   '<div class="meter"><i style="width:96%"></i></div>',
                   row("rupee", "Fees collected", "82% of term target", "₹18.4L"),
                   '<div class="meter"><i style="width:82%"></i></div>']))
    p1 = ("".join([row("rupee", "Term-2 fee · Aarav Sharma", "Due 15 Jun", "₹12,500"),
                   '<div class="meter"><i style="width:82%"></i></div>',
                   row("check", "Receipts issued today", "Auto-numbered, DPDP-logged", "37")]))
    p2 = ('<div class="note"><b>WhatsApp · to parent</b>Aarav was marked present today at '
          '8:42&nbsp;AM ✅ &nbsp;· Term-2 fee ₹12,500 due 15 Jun.</div>'
          + row("users", "Parents reached today", "Delivered 1,204 / 1,248", "96%"))
    tabs = ["Overview", "Fees", "Messages"]
    return tab_panel("vv", tabs, [p0, p1, p2])

def panel_tabs_pd():
    p0 = "".join([row("book", "Reflowable EPUB", "Font size, theme, bookmarks", "EPUB"),
                  row("check", "Reading position synced", "Across every signed-in device", "✓")])
    p1 = "".join([row("book", "Page-accurate PDF", "Exactly as the publisher set it", "PDF"),
                  '<div class="meter"><i style="width:46%"></i></div>',
                  row("check", "Page 118 of 256", "Annotations kept per student", "46%")])
    p2 = ('<div class="row" style="gap:12px"><button type="button" id="pd-play" class="playbtn" aria-label="Play">'
          '<span class="ico-playing" hidden>%s</span><span class="ico-paused">%s</span></button>'
          '<span class="row__t"><b>Natural text-to-speech</b><span>Chapter 4 · The Living World</span></span>'
          '<span class="row__v" id="pd-time">01:05</span></div>'
          '<div class="wavewrap">%s</div>'
          '<div class="meter"><i id="pd-bar" style="width:34%%"></i></div>'
          % (svg("pause", 15), svg("play", 15),
             "".join('<i class="wv" style="--h:%dpx;--d:%.2fs"></i>'
                     % (10 + ((i * 7) % 20), 0.7 + (i % 5) * 0.12) for i in range(1, 13))))
    p3 = ('<div class="note"><b>Varta · study assistant</b>“Why is the mitochondrion called the '
          'powerhouse?”</div>'
          + row("spark", "Answered from your own library", "Cited to page 118, paragraph 3", "CITED")
          + row("book", "Saved to Sanchika", "Your notebook, searchable later", "✓"))
    return tab_panel("pd", ["EPUB", "PDF", "AUDIO", "VARTA"], [p0, p1, p2, p3])

def tab_panel(group, labels, panels):
    tabs = "".join('<button type="button" class="mock-tab%s" data-tabset="%s" data-tab="%d">%s</button>'
                   % (" is-active" if i == 0 else "", group, i, l) for i, l in enumerate(labels))
    bodies = "".join('<div class="mock-panel" data-panel="%s-%d"%s>%s</div>'
                     % (group, i, "" if i == 0 else " hidden", p) for i, p in enumerate(panels))
    return '<div class="app__tabs">%s</div><div class="app__body">%s</div>' % (tabs, bodies)

def panel_ask_dg():
    qs = ('<div class="app__tabs">'
          '<button type="button" class="mock-q is-active" data-q="0">Explain photosynthesis</button>'
          '<button type="button" class="mock-q" data-q="1">Why is my room warmer?</button></div>')
    a0 = ('<div class="mock-panel" data-panel="dg-0">'
          + '<div class="note"><b>Sarvagya · grounded answer</b>Photosynthesis converts light energy '
            'into chemical energy stored as glucose.</div>'
          + row("book", "NCERT Class 10 · Ch. 6", "Life Processes, page 95", "SOURCE")
          + row("spark", "Bloom level", "Understand → Apply", "L2")
          + '</div>')
    a1 = ('<div class="mock-panel" data-panel="dg-1" hidden>'
          + '<div class="note"><b>Sarvagya · grounded answer</b>Conduction, convection and radiation '
            'all move heat into the room — here is which dominates.</div>'
          + row("book", "NCERT Class 7 · Ch. 4", "Heat, page 43", "SOURCE")
          + row("spark", "Bloom level", "Analyse", "L4")
          + '</div>')
    return qs + '<div class="app__body">%s%s</div>' % (a0, a1)

def panel_exam_pt():
    seed = [1, 1, 0, 2, 1, 3, 0, 1, 1, 2, 0, 0, 1, 1, 3, 0, 1, 0, 2, 1]
    titles = ["Not visited", "Answered", "Not answered", "Marked"]
    cells = "".join('<button type="button" class="cell is-%d" data-cell="%d" title="%s">%d</button>'
                    % (v, i, titles[v], i + 1) for i, v in enumerate(seed))
    legend = ('<div class="legend">'
              '<span><i style="background:var(--ok-t);border-color:var(--ok)"></i>Answered</span>'
              '<span><i style="background:var(--vv-t);border-color:var(--vv)"></i>Not answered</span>'
              '<span><i style="background:var(--pt-t);border-color:var(--pt)"></i>Marked</span>'
              '<span><i></i>Not visited</span></div>')
    return ('<div class="app__body">'
            '<div class="clock"><span>Quantitative Aptitude · Section 2 of 4</span>'
            '<time id="exam-time">00:12:04</time></div>'
            '<div class="palette">%s</div>%s'
            '<p style="font-size:11.5px;color:var(--muted);margin:0">Click any number — the palette '
            'cycles exactly as it does in the real paper.</p></div>' % (cells, legend))

PANELS = {"tabs_vv": panel_tabs_vv, "tabs_pd": panel_tabs_pd,
          "ask_dg": panel_ask_dg, "exam_pt": panel_exam_pt}

# ------------------------------------------------------------------ sections
def render_cards(cards, kind, links=None):
    links = links or {}
    out = []
    for i, c in enumerate(cards):
        d = min(i * 60, 180)
        if kind == "module":
            chips = "".join("<li>%s</li>" % x for x in c["li"])
            out.append('<article class="card card--mod" data-rv data-rv-delay="%d">'
                       '<span class="card__rule"></span>'
                       '<div class="card__head"><h3>%s</h3><span class="card__meta">%s</span></div>'
                       '<ul class="chips">%s</ul></article>' % (d, c["h3"], c["meta"], chips))
        elif kind == "eco":
            # the v1 markup carried the cross-link as a list item; make it a real link
            link = ""
            for label in c["li"]:
                href = links.get(label)
                if href:
                    link = ('<a class="linkarrow" href="%s" style="color:var(--gold-hi)">%s %s</a>'
                            % (href, label.replace("→", "").strip(), svg("arrow_out", 15)))
            out.append('<article class="ecocard2" data-rv data-rv-delay="%d">%s<h3>%s</h3>%s%s</article>'
                       % (d, '<span class="card__tag">%s</span>' % c["tag"] if c["tag"] else "",
                          c["h3"], "".join("<p>%s</p>" % p for p in c["p"]), link))
        else:
            chips = ('<ul class="chips">%s</ul>' % "".join("<li>%s</li>" % x for x in c["li"])) if c["li"] else ""
            meta = ('<span class="card__meta">%s</span>' % c["meta"]) if c["meta"] else ""
            out.append('<article class="card" data-rv data-rv-delay="%d">'
                       '<span class="card__rule"></span>%s%s<h3>%s</h3>%s%s</article>'
                       % (d, '<span class="card__tag">%s</span>' % c["tag"] if c["tag"] else "",
                          meta, c["h3"], "".join("<p>%s</p>" % p for p in c["p"]), chips))
    return "".join(out)

def render_steps(cards):
    return "".join('<article class="step" data-rv data-rv-delay="%d"><h3>%s</h3>%s</article>'
                   % (i * 70, c["h3"], "".join("<p>%s</p>" % p for p in c["p"]))
                   for i, c in enumerate(cards))

def kind_of(sec, idx, total):
    if "eco" in sec["cls"]:
        return "eco"
    if any(c["li"] and c["meta"] for c in sec["cards"]):
        return "module"
    # a walkthrough is three plain cards - no tag, no meta, no chips. Everything
    # else with three cards (reading modes, tiers, ecosystem) is tagged.
    if len(sec["cards"]) == 3 and all(
            not c["tag"] and not c["meta"] and not c["li"] for c in sec["cards"]):
        return "step"
    return "card"

def render_section(sec, idx, alt, cfg):
    kind = kind_of(sec, idx, 0)
    if not sec["cards"] and kind != "eco":
        return ""   # the closing CTA is rendered separately
    keep = sec["intro"] if kind == "eco" else sec["intro"][:1]
    intro = "".join('<p class="lede">%s</p>' % clean_links(p) for p in keep)
    head = ('<div class="sechead" data-rv>%s<h2 class="h2">%s</h2>%s</div>'
            % ('<span class="eyeb">%s</span>' % sec["eyebrow"] if sec["eyebrow"] else "",
               sec["h2"], intro))
    if kind == "eco":
        linkmap = {label: fix_href(href) for href, label in sec["links"]}
        body = ('<div class="ecogrid2">%s</div>' % render_cards(sec["cards"], "eco", linkmap)) if sec["cards"] else ""
        return '<section class="sec sec--band"><div class="wrap">%s%s</div></section>' % (head, body)
    if kind == "step":
        body = '<div class="steps">%s</div>' % render_steps(sec["cards"])
    else:
        body = '<div class="grid">%s</div>' % render_cards(sec["cards"], kind)
    return ('<section class="sec%s"><div class="wrap">%s%s</div></section>'
            % (" sec--alt" if alt else "", head, body))

def render_close(sec, cfg):
    links = sec["links"] or []
    btns = []
    for href, label in links[:2]:
        if href.startswith("http"):
            btns.append('<a class="b b--acc" href="%s" target="_blank" rel="noopener">%s %s</a>'
                        % (href, label, svg("arrow_out", 16)))
        else:
            btns.append('<a class="b b--ghost" href="%s">%s</a>' % (href, label))
    if not btns:
        btns = ['<a class="b b--acc" href="../#contact">Book a walkthrough</a>']
    return ('<section class="sec"><div class="wrap"><div class="close" data-rv>'
            '<span class="close__glow"></span>'
            '<h2 class="h2">%s</h2>%s<div class="pcta">%s</div></div></div></section>'
            % (sec["h2"], "".join('<p class="lede" style="margin-inline:auto">%s</p>' % p
                                  for p in sec["intro"][:1]), "".join(btns)))

# ------------------------------------------------------------------- page
def build(key):
    cfg = PRODUCTS[key]
    data = content[key]
    hero, meta = data["hero"], data["meta"]

    nav = "".join('<a href="%s.html"%s>%s</a>' % (k, ' aria-current="page"' if k == key else "", label)
                  for k, label in NAV)
    mnav = "".join('<a href="%s.html">%s</a>' % (k, label) for k, label in NAV)

    facts = "".join('<div class="fact"%s><b>%s</b><span>%s</span><i></i></div>'
                    % (' data-rv' if i else "", v, l) for i, (v, l) in enumerate(cfg["facts"]))

    secs = data["sections"]
    body_secs, alt = [], True
    for i, sec in enumerate(secs):
        if not sec["cards"] and sec is secs[-1] and "eco" not in sec["cls"]:
            body_secs.append(render_close(sec, cfg)); continue
        html = render_section(sec, i, alt, cfg)
        if html:
            body_secs.append(html)
            if "sec--band" not in html:
                alt = not alt

    jsonld = "".join('<script type="application/ld+json">%s</script>' % j for j in data["jsonld"])

    return """<!DOCTYPE html>
<html lang="en" data-acc="{acc}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{canonical}">

<meta property="og:type" content="website">
<meta property="og:site_name" content="Vinstitution">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{og_desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_image}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{og_title}">
<meta name="twitter:description" content="{og_desc}">
<meta name="twitter:image" content="{og_image}">
<meta name="theme-color" content="#FFFCF9" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#090D15" media="(prefers-color-scheme: dark)">

<link rel="icon" href="../favicon-32.png" type="image/png" sizes="32x32">
<link rel="icon" href="../assets/img/icon-192.png" type="image/png" sizes="192x192">
<link rel="apple-touch-icon" href="../assets/img/apple-touch-icon.png">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Mukta:wght@400;500;600&display=swap" rel="stylesheet">
<script>
  (function(){{
    try{{
      var s = localStorage.getItem('vin-theme');
      var d = window.matchMedia('(prefers-color-scheme: dark)').matches;
      document.documentElement.setAttribute('data-theme', s || (d ? 'dark' : 'light'));
    }}catch(e){{ document.documentElement.setAttribute('data-theme','light'); }}
  }})();
</script>
<link rel="stylesheet" href="../assets/css/style.css?v={ver}">
<link rel="stylesheet" href="../assets/css/product.css?v={ver}">
{jsonld}
</head>
<body>

<div id="scroll-progress" class="progress" aria-hidden="true"></div>

<header class="top">
  <div class="wrap">
    <div class="top__in">
      <a class="top__logo" href="../index.html" aria-label="Vinstitution — home">
        <img src="../assets/logos/vinstitution-lockup.png" alt="Vinstitution" width="520" height="168" fetchpriority="high">
      </a>
      <nav class="top__nav" aria-label="Primary">{nav}<a href="../#contact">Contact</a></nav>
      <button type="button" id="theme-toggle" class="iconbtn" aria-label="Switch to night mode" title="Switch to night mode">
        <span class="ico-dark">{sun}</span><span class="ico-light">{moon}</span>
      </button>
      <a class="b b--acc b--sm top__cta" href="../#contact">Book a demo</a>
      <button type="button" id="nav-toggle" class="burger2" aria-label="Menu" aria-controls="mnav" aria-expanded="false">{menu}</button>
    </div>
  </div>
</header>

<nav id="mnav" class="mnav2" aria-label="Mobile" hidden>{mnav}<a href="../#contact">Contact</a>
  <a class="b b--acc" href="../#contact" style="align-self:flex-start;margin-top:22px">Book a demo</a>
</nav>

<section class="phero2" id="top">
  <span class="phero2__glow" aria-hidden="true"></span>
  <span class="phero2__grid" aria-hidden="true"></span>
  <div class="wrap">
    <nav class="crumb2" aria-label="Breadcrumb"><a href="../index.html">Vinstitution</a><span>/</span>{name}</nav>
    <div class="phero2__in">
      <div style="min-width:0">
        <span class="eyeb">{eyebrow}</span>
        <h1 class="h1">{h1}</h1>
        {deva}
        <p class="plede">{lede}</p>
        <div class="pcta">
          <a class="b b--acc" href="{app}" target="_blank" rel="noopener">{app_label} {out}</a>
          <a class="b b--ghost" href="../#contact">Book a walkthrough</a>
        </div>
      </div>
      <div style="min-width:0">
        <div class="app">
          <div class="app__bar"><i></i><i></i><i></i><span class="app__url">{url_hint}</span>
            <span class="app__live"><i></i>LIVE</span></div>
          {panel}
        </div>
      </div>
    </div>
  </div>
</section>

<div class="wrap"><div class="facts">{facts}</div></div>

{sections}

<footer class="foot">
  <div class="wrap">
    <div class="foot__top">
      <div class="foot__brand">
        <a href="../index.html" aria-label="Vinstitution — home">
          <img src="../assets/logos/vinstitution-full.png" alt="Vinstitution — Uttiṣṭhata, Jāgrata, Prāpya · ISO 9001:2015 Certified" width="760" height="338" loading="lazy">
        </a>
        <p>Education technology for Indian institutions and learners — a campus operating system, an AI digital library, an NCERT-grounded tutor and a CBT exam engine, connected by one institutional login.</p>
      </div>
      <div>
        <h4>Platforms</h4>
        <ul>{footnav}</ul>
      </div>
      <div>
        <h4>Company</h4>
        <ul>
          <li><a href="../index.html#why">Why Vinstitution</a></li>
          <li><a href="../index.html#services">Services</a></li>
          <li><a href="../index.html#ecosystem">Ecosystem</a></li>
          <li><a href="../#contact">Contact</a></li>
        </ul>
      </div>
      <div>
        <h4>Reach us</h4>
        <ul>
          <li><a href="mailto:tech@vinstitution.com">tech@vinstitution.com</a></li>
          <li>New Delhi, India</li>
        </ul>
      </div>
    </div>
    <div class="foot__btm">
      <span>&copy; <span data-year>2026</span> Vinstitution. All rights reserved.</span>
      <span class="foot__iso">ISO 9001:2015 Certified</span>
    </div>
  </div>
</footer>

<a href="#top" id="to-top" class="totop" aria-label="Back to top">{up}</a>

<script src="../assets/js/main.js?v={ver}"></script>
</body>
</html>
""".format(
        acc=cfg["acc"], ver=VER,
        title=meta["title"], desc=meta["description"], canonical=meta["canonical"],
        og_title=meta["og_title"] or meta["title"], og_desc=meta["og_desc"] or meta["description"],
        og_image=meta["og_image"], jsonld=jsonld,
        nav=nav, mnav=mnav,
        footnav="".join('<li><a href="%s.html">%s</a></li>' % (k, l) for k, l in NAV),
        name=cfg["name"], eyebrow=hero["eyebrow"],
        h1=em_wrap(hero["h1"], cfg["em"]),
        deva=('<p class="deva2">%s</p>' % hero["deva"]) if hero["deva"] else "",
        lede=hero["lede"], app=cfg["app"], app_label=cfg["app_label"],
        url_hint=cfg["url_hint"], panel=PANELS[cfg["panel"]](),
        facts=facts, sections="\n\n".join(body_secs),
        sun=svg("sun", 19, "1.9"), moon=svg("moon", 19, "1.9"), menu=svg("menu", 20),
        out=svg("arrow_out", 16), up=svg("up", 18, "2.2"))

for key in ORDER:
    html = build(key)
    path = os.path.join(ROOT, "products", key + ".html")
    io.open(path, "w", encoding="utf-8", newline="\n").write(html)
    print("%-22s %6d bytes" % (key + ".html", len(html)))
