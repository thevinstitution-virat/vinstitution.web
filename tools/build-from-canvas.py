# Convert the Claude Design Canvas spec (.dc.html) into the static Vinstitution site.
# Mechanical transform: DSL -> plain HTML + CSS classes + vanilla JS hooks.
import io, os, re

SRC  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "design", "vinstitution-v2.dc.html")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
VER  = "3"

src = io.open(SRC, encoding="utf-8").read()

# ---------------------------------------------------------------- 1. helmet CSS
base_css = re.search(r"<style>(.*?)</style>", src, re.S).group(1).strip("\n")

# ---------------------------------------------------------------- 2. body slice
start = src.index('<div style="background:var(--paper)">')
body  = src[start:src.index("</x-dc>")].rstrip()

# ---------------------------------------------------------------- 3. sc-for
SEED   = [1,1,0,2,1,3,0,1,1,2,0,0,1,1,3,0,1,0,2,1]
TITLES = ["Not visited", "Answered", "Not answered", "Marked"]
m = re.search(r'<sc-for\b.*?</sc-for>', body, re.S)
cells = "\n".join(
    '                <button type="button" class="cell is-%d" data-cell="%d" title="%s">%d</button>'
    % (v, i, TITLES[v], i + 1)
    for i, v in enumerate(SEED)
)
body = body[:m.start()] + cells.lstrip() + body[m.end():]

# ---------------------------------------------------------------- 4. sc-if
PANEL = {
    "vvIsOverview": ("vv", 0), "vvIsFees": ("vv", 1), "vvIsMsgs": ("vv", 2),
    "pdIsEpub": ("pd", 0), "pdIsPdf": ("pd", 1), "pdIsAudio": ("pd", 2), "pdIsVarta": ("pd", 3),
    "dgIsPhoto": ("dg", 0), "dgIsHeat": ("dg", 1),
}
TAGGED = {
    "isDesktop": "js-desktop", "isMobile": "js-mobile",
    "isDark": "ico-dark", "isLight": "ico-light",
    "playing": "ico-playing", "paused": "ico-paused",
    "navOpen": "js-mobile-nav",
}
PLAIN = {"showHeroVisual", "showStats"}

def add_attrs(chunk, cls=None, extra=""):
    """Add a class (merging) and extra attributes to the first element in chunk."""
    tm = re.search(r"<([a-zA-Z][\w-]*)((?:\s[^>]*?)?)(/?)>", chunk, re.S)
    if not tm:
        return chunk
    name, attrs, slash = tm.group(1), tm.group(2), tm.group(3)
    if cls:
        cm = re.search(r'\sclass="([^"]*)"', attrs)
        if cm:
            attrs = attrs[:cm.start()] + ' class="%s %s"' % (cm.group(1), cls) + attrs[cm.end():]
        else:
            attrs = ' class="%s"' % cls + attrs
    if extra:
        attrs = " " + extra.strip() + attrs
    return chunk[:tm.start()] + "<%s%s%s>" % (name, attrs, slash) + chunk[tm.end():]

def resolve(value, inner):
    if value in PANEL:
        group, idx = PANEL[value]
        hid = "" if idx == 0 else " hidden"
        return ('<div class="mock-panel" data-panel="%s-%d"%s>%s</div>' % (group, idx, hid, inner))
    if value in TAGGED:
        # the nav starts closed, and the player starts paused - so both begin hidden
        extra = 'hidden' if value in ("navOpen", "playing") else ""
        return add_attrs(inner, TAGGED[value], extra)
    if value in PLAIN:
        return inner
    raise SystemExit("unmapped sc-if: " + value)

while "<sc-if" in body:
    ci = body.index("</sc-if>")
    oi = body.rindex("<sc-if", 0, ci)
    oe = body.index(">", oi) + 1
    value = re.search(r'value="\{\{\s*(\w+)\s*\}\}"', body[oi:oe]).group(1)
    body = body[:oi] + resolve(value, body[oe:ci]) + body[ci + len("</sc-if>"):]

# ---------------------------------------------------------------- 5. bindings
def tab(group, idx):
    return 'class="mock-tab%s" data-tabset="%s" data-tab="%d"' % (
        " is-active" if idx == 0 else "", group, idx)

repl = {}
for i in range(3):
    repl['style="{{ vvTab%d }}"' % i] = tab("vv", i)
for i in range(4):
    repl['style="{{ pdTab%d }}"' % i] = tab("pd", i)
for i in range(2):
    repl['style="{{ dgQ%d }}"' % i] = 'class="mock-q%s" data-q="%d"' % (
        " is-active" if i == 0 else "", i)
for i in range(1, 13):
    # mirrors waveStyle(i) in the canvas: height 10+((i*7)%20)px, duration .7+(i%5)*.12s
    repl['style="{{ wave%d }}"' % i] = 'class="wv" style="--h:%dpx;--d:%.2fs"' % (
        10 + ((i * 7) % 20), 0.7 + (i % 5) * 0.12)
repl.update({
    'style="{{ audioBar }}"'        : 'class="pd-bar" id="pd-bar"',
    '>{{ audioTime }}<'             : '><span id="pd-time">01:05</span><',
    '>{{ examTime }}<'              : '><span id="exam-time">00:12:04</span><',
    'ref="{{ progressRef }}"'       : 'id="scroll-progress"',
    'ref="{{ msgRef }}"'            : 'id="form-msg"',
    'ref="{{ yearRef }}"'           : 'id="year"',
    'ref="{{ topRef }}"'            : 'id="to-top"',
    'onClick="{{ toggleTheme }}"'   : 'id="theme-toggle"',
    'onClick="{{ toggleNav }}"'     : 'id="nav-toggle"',
    'onClick="{{ togglePlay }}"'    : 'id="pd-play"',
    'onClick="{{ closeNav }}"'      : '',
    'onClick="{{ vvOverview }}"'    : '', 'onClick="{{ vvFees }}"' : '',
    'onClick="{{ vvMsgs }}"'        : '',
    'onClick="{{ pdEpub }}"'        : '', 'onClick="{{ pdPdf }}"'  : '',
    'onClick="{{ pdAudio }}"'       : '', 'onClick="{{ pdVarta }}"': '',
    'onClick="{{ askPhoto }}"'      : '', 'onClick="{{ askHeat }}"': '',
    'onSubmit="{{ onSubmit }}"'     : '',
    'aria-label="{{ themeLabel }}"' : 'aria-label="Switch to night mode"',
    'title="{{ themeLabel }}"'      : 'title="Switch to night mode"',
    'aria-label="{{ playLabel }}"'  : 'aria-label="Play"',
    'aria-expanded="{{ expanded }}"': 'aria-expanded="false"',
})
for k, v in repl.items():
    body = body.replace(k, v)

leftover = re.findall(r"\{\{[^}]*\}\}", body)
if leftover:
    raise SystemExit("unresolved bindings: " + repr(sorted(set(leftover))[:10]))

# ---------------------------------------------------------------- 6. hover/focus
# Inline styles beat selectors, so every generated declaration needs !important.
def bang(decls):
    out = []
    for d in decls.split(";"):
        d = d.strip()
        if d:
            out.append(d + " !important")
    return ";".join(out)

state_css, seen = [], {}
def hook(match, attr, pseudo, prefix):
    decls = match.group(1)
    if decls not in seen:
        n = len(seen) + 1
        seen[decls] = n
        state_css.append("[%s=\"%d\"]:%s{%s}" % (attr, n, pseudo, bang(decls)))
    return '%s="%d"' % (attr, seen[decls])

seen_h = {}
def sub_hover(m):
    decls = m.group(1)
    if decls not in seen_h:
        n = len(seen_h) + 1
        seen_h[decls] = n
        state_css.append('[data-hv="%d"]:hover{%s}' % (n, bang(decls)))
    return 'data-hv="%d"' % seen_h[decls]

seen_f = {}
def sub_focus(m):
    decls = m.group(1)
    if decls not in seen_f:
        n = len(seen_f) + 1
        seen_f[decls] = n
        state_css.append('[data-fc="%d"]:focus{%s}' % (n, bang(decls)))
    return 'data-fc="%d"' % seen_f[decls]

body = re.sub(r'style-hover="([^"]*)"', sub_hover, body)
body = re.sub(r'style-focus="([^"]*)"', sub_focus, body)

body = re.sub(r'\s+hint-placeholder-(val|count)="[^"]*"', "", body)

# each of the four product cards exposes its own accent to the tab / chip CSS
_acc = {"i": 0}
def _tag_card(m):
    a = ["vv", "pd", "dg", "pt"][_acc["i"]]
    _acc["i"] += 1
    return '<article data-acc="%s" data-rv' % a
body = re.sub(
    r'<article data-rv(?= style="position:relative;display:grid;'
    r'grid-template-columns:repeat\(auto-fit,minmax\(min\(320px)', _tag_card, body, count=4)
if _acc["i"] != 4:
    raise SystemExit("expected 4 product cards, tagged %d" % _acc["i"])

body = re.sub(r'[ ]{2,}(?=[a-zA-Z-]+=")', " ", body)   # tidy gaps left by stripped handlers
body = re.sub(r"[ \t]+\n", "\n", body)

# ---------------------------------------------------------------- 7. CSS file
extra_css = """
/* ---------- v2 component layer (added by the design-canvas conversion) ---------- */
.js-desktop{display:flex}
@media (max-width:900px){.js-desktop{display:none !important}}
@media (min-width:901px){.js-mobile{display:none !important}}
[hidden]{display:none !important}

/* theme icons: the correct one is chosen by the document theme, no JS needed */
html:not([data-theme="dark"]) .ico-dark{display:none}
html[data-theme="dark"] .ico-light{display:none}

/* mock-UI panels inside the product cards */
.mock-panel{display:flex;flex-direction:column;gap:10px;flex:1;min-width:0}

.mock-tab{font-size:10.5px;font-weight:800;letter-spacing:.1em;padding:7px 12px;border-radius:100px;
  cursor:pointer;border:1px solid var(--line);background:var(--surface);color:var(--muted);
  transition:background .25s,color .25s,border-color .25s,transform .25s}
.mock-tab:hover{transform:translateY(-1px);color:var(--ink)}
.mock-tab.is-active{border-color:transparent;background:var(--acc-btn);color:#fff}

.mock-q{font-size:11.5px;font-weight:700;text-align:left;padding:9px 13px;border-radius:100px;
  cursor:pointer;border:1px solid var(--line);background:var(--surface);color:var(--muted);
  transition:background .25s,color .25s,border-color .25s}
.mock-q:hover{color:var(--ink)}
.mock-q.is-active{border-color:var(--acc);background:var(--acc-t);color:var(--acc)}

/* practest question palette */
.cell{aspect-ratio:1;display:grid;place-items:center;border-radius:8px;font-size:10.5px;font-weight:800;
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;cursor:pointer;padding:0;
  transition:transform .2s,background .2s;background:var(--surface);color:var(--muted);border:1px solid var(--line)}
.cell:hover{transform:scale(1.08)}
.cell.is-1{background:var(--ok-t);color:var(--ok);border-color:var(--ok)}
.cell.is-2{background:var(--vv-t);color:var(--vv);border-color:var(--vv)}
.cell.is-3{background:var(--pt-t);color:var(--pt);border-color:var(--pt)}

/* pdlms audio waveform */
.wv{display:block;flex:1;min-width:0;border-radius:100px;background:var(--pd);opacity:.75;
  transform-origin:bottom;transform:scaleY(.45);height:var(--h,14px)}
.is-playing .wv{transform:none;animation:wave var(--d,.8s) ease-in-out infinite}
.pd-bar{display:block;height:100%;width:34%;border-radius:100px;background:var(--pd-btn);transition:width .26s linear}

/* product-card accents drive the tab/chip colours */
[data-acc="vv"]{--acc:var(--vv);--acc-t:var(--vv-t);--acc-btn:var(--vv-btn)}
[data-acc="pd"]{--acc:var(--pd);--acc-t:var(--pd-t);--acc-btn:var(--pd-btn)}
[data-acc="dg"]{--acc:var(--dg);--acc-t:var(--dg-t);--acc-btn:var(--dg-btn)}
[data-acc="pt"]{--acc:var(--pt);--acc-t:var(--pt-t);--acc-btn:var(--pt-btn)}

button{font:inherit}
"""

hover_css = "\n/* ---------- generated hover / focus states ---------- */\n" + "\n".join(state_css) + "\n"
io.open(os.path.join(ROOT, "assets/css/style.css"), "w", encoding="utf-8", newline="\n").write(
    "/* Vinstitution v2 - generated from the design canvas. Edit the canvas, re-run the build. */\n"
    + base_css + "\n" + extra_css + hover_css)

# ---------------------------------------------------------------- 8. index.html
old = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
head = old[old.index("<head>") + len("<head>"):old.index("</head>")]
head = re.sub(r'\n<link rel="stylesheet" href="assets/css/style\.css[^"]*">', "", head)
# strip a theme-boot block from a previous run so repeated builds stay idempotent
head = re.sub(r"\n<script>\s*\(function\(\)\{\s*try\{\s*var s = localStorage\.getItem\('vin-theme'\).*?</script>",
              "", head, flags=re.S)
head = re.sub(r"\n{3,}", "\n\n", head)
head = head.replace('<meta name="theme-color" content="#E8452A">',
                    '<meta name="theme-color" content="#FFFCF9" media="(prefers-color-scheme: light)">\n'
                    '<meta name="theme-color" content="#090D15" media="(prefers-color-scheme: dark)">')

theme_boot = """
<script>
  (function(){
    try{
      var s = localStorage.getItem('vin-theme');
      var d = window.matchMedia('(prefers-color-scheme: dark)').matches;
      document.documentElement.setAttribute('data-theme', s || (d ? 'dark' : 'light'));
    }catch(e){ document.documentElement.setAttribute('data-theme','light'); }
  })();
</script>
<link rel="stylesheet" href="assets/css/style.css?v=%s">
""" % VER

html = ("<!DOCTYPE html>\n<html lang=\"en\">\n<head>" + head + theme_boot + "</head>\n<body>\n"
        + body + "\n\n<script src=\"assets/js/main.js?v=%s\"></script>\n</body>\n</html>\n" % VER)
io.open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8", newline="\n").write(html)

print("style.css   :", len(base_css) + len(extra_css) + len(hover_css), "bytes")
print("hover rules :", len(seen_h), "  focus rules:", len(seen_f))
print("index.html  :", len(html), "bytes")
