# One-off: rebuild the product-page component CSS on top of the v2 design tokens.
# The old stylesheet carried its own :root palette; we drop that and alias the old
# token names onto the v2 ones, so products/*.html inherit the new look AND dark mode.
import io, re, subprocess

ROOT = r"H:/vinstitution-site"
old = subprocess.run(["git", "show", "HEAD:assets/css/style.css"],
                     cwd=ROOT, capture_output=True, text=True, encoding="utf-8").stdout

# everything after the old :root{...} block
body = old[old.index("}", old.index(":root{")) + 1:].lstrip("\n")

shim = """/* Vinstitution — product-page components.
   The v2 design tokens live in style.css; this file only aliases the older
   variable names onto them, then carries the component classes that
   products/*.html still use. Load AFTER style.css. */

:root{
  /* ground + ink ------------------------------------------------------- */
  --bg:var(--surface);
  --bg-2:var(--surface-2);
  --bg-3:var(--paper-2);
  --bg-ink:var(--band);
  --muted-2:var(--faint);
  --line-dark:var(--band-line);

  /* brand: the old --brand was the bright tone, --brand-dk the deep one --- */
  --brand-dk:var(--brand);
  --brand-lt:var(--brand-tint);
  --gold-lt:var(--pd-t);
  --blue-lt:var(--pt-t);

  /* product accents ---------------------------------------------------- */
  --vv-lt:var(--vv-t);
  --pd-lt:var(--pd-t);
  --dg-lt:var(--dg-t);
  --pt-lt:var(--pt-t);
  --accent:var(--brand);
  --accent-lt:var(--brand-tint);

  /* type + metrics (no v2 equivalent, kept verbatim) -------------------- */
  --serif:'Fraunces',Georgia,'Times New Roman',serif;
  --sans:'Plus Jakarta Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  --deva:'Mukta','Nirmala UI',var(--sans);
  --mono:ui-monospace,SFMono-Regular,'SF Mono',Menlo,monospace;
  --wrap:1200px;
  --pad:clamp(16px,4vw,48px);
  --sec:clamp(64px,8vw,116px);
  --r:14px;
  --r-lg:22px;
  --ease:cubic-bezier(.2,.7,.3,1);
  --ease-io:cubic-bezier(.65,0,.35,1);

  /* elevation now follows the theme-aware v2 shadows -------------------- */
  --sh-1:var(--sh1);
  --sh-2:var(--sh2);
  --sh-3:var(--sh3);
}

"""

tail = """

/* --------------------------------------------------- v2 reconciliation --
   The component sheet above sets its own body ground; keep product pages on
   the same paper as the homepage, and let the shared theme toggle sit in the
   product header without inheriting nav link styling. */
body{background:var(--paper)}
.hdr__in .theme-btn{
  width:40px;height:40px;flex:none;border-radius:100px;display:grid;place-items:center;
  color:var(--ink);border:1px solid var(--line-2);background:var(--surface);cursor:pointer;
  transition:transform .35s var(--ease),box-shadow .3s,border-color .3s;
}
.hdr__in .theme-btn:hover{transform:rotate(18deg) scale(1.06);box-shadow:var(--sh2);border-color:var(--brand-hi)}
.hdr__in .theme-btn svg{width:18px;height:18px}

/* Colours the old sheet hard-coded for a light-only page. Re-pointed at the
   theme-aware tokens so they stay legible in night mode. */
.pillar:nth-child(3) .pillar__ic{color:var(--gold)}
.fmsg.ok{background:var(--ok-t);color:var(--ok);border-color:var(--ok)}
.fmsg.err{background:var(--vv-t);color:var(--vv);border-color:var(--vv)}
.ftr__iso{color:var(--band-body)}
"""

io.open(ROOT + "/assets/css/pages.css", "w", encoding="utf-8", newline="\n").write(shim + body + tail)
print("pages.css written:", len(shim + body + tail), "bytes")
