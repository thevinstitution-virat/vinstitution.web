# Bring products/*.html onto the v2 design system: shared tokens, dark mode,
# theme toggle, and the refreshed asset stamps.
import io, glob, re, os

ROOT = r"H:/vinstitution-site"
VER = "3"

THEME_BOOT = """<script>
  (function(){
    try{
      var s = localStorage.getItem('vin-theme');
      var d = window.matchMedia('(prefers-color-scheme: dark)').matches;
      document.documentElement.setAttribute('data-theme', s || (d ? 'dark' : 'light'));
    }catch(e){ document.documentElement.setAttribute('data-theme','light'); }
  })();
</script>
<link rel="stylesheet" href="../assets/css/style.css?v=%s">
<link rel="stylesheet" href="../assets/css/pages.css?v=%s">""" % (VER, VER)

TOGGLE = """      <button type="button" id="theme-toggle" class="theme-btn" aria-label="Switch to night mode" title="Switch to night mode">
        <svg class="ico-dark" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2"></circle><path d="M12 2v2.4M12 19.6V22M2 12h2.4M19.6 12H22M4.9 4.9l1.7 1.7M17.4 17.4l1.7 1.7M19.1 4.9l-1.7 1.7M6.6 17.4l-1.7 1.7"></path></svg>
        <svg class="ico-light" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 13.2A8.6 8.6 0 1 1 10.8 3a6.8 6.8 0 0 0 10.2 10.2Z"></path></svg>
      </button>
"""

for path in sorted(glob.glob(os.path.join(ROOT, "products", "*.html"))):
    s = io.open(path, encoding="utf-8").read()
    orig = s

    # 1. stylesheet link -> theme boot + both sheets
    s = re.sub(r'<link rel="stylesheet" href="\.\./assets/css/style\.css\?v=\d+">', THEME_BOOT, s, count=1)

    # 2. theme-color: one per scheme instead of the product accent
    s = re.sub(r'<meta name="theme-color" content="#[0-9A-Fa-f]{6}">',
               '<meta name="theme-color" content="#FFFCF9" media="(prefers-color-scheme: light)">\n'
               '<meta name="theme-color" content="#090D15" media="(prefers-color-scheme: dark)">', s, count=1)

    # 3. theme toggle, immediately before the header CTA
    s = re.sub(r'(?m)^([ \t]*)<a class="btn btn--sm" href="\.\./#contact">', TOGGLE + r'\1<a class="btn btn--sm" href="../#contact">', s, count=1)

    # 4. script stamp
    s = s.replace('../assets/js/main.js?v=2', '../assets/js/main.js?v=%s' % VER)

    io.open(path, "w", encoding="utf-8", newline="\n").write(s)
    name = os.path.basename(path)
    print("%-24s css:%s  theme-color:%s  toggle:%s  js:%s" % (
        name,
        "ok" if "pages.css?v=" + VER in s else "MISS",
        "ok" if "prefers-color-scheme: dark" in s else "MISS",
        "ok" if 'id="theme-toggle"' in s else "MISS",
        "ok" if "main.js?v=" + VER in s else "MISS"))
