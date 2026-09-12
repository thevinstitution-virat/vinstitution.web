#!/bin/bash
# =============================================================================
#  vinstitution.com — deploy the repository into the cPanel document root
#
#  Invoked by .cpanel.yml when cPanel's Git Version Control deploys HEAD, and
#  safe to run by hand over SSH:
#
#      ~/repositories/vinstitution.web/deploy.sh
#
#  Two things in the docroot are NOT ours and must survive every deploy:
#    1. .well-known/  — Let's Encrypt validation. Losing it breaks HTTPS renewal.
#    2. The cPanel-generated PHP handler block inside .htaccess. Without it
#       contact.php is served as plain text instead of being executed.
# =============================================================================
set -euo pipefail

DOCROOT="${1:-$HOME/public_html}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Everything the live site is made of. Anything not listed here is not deployed.
PAYLOAD=(index.html about.html contact.php favicon.ico favicon.png favicon-32.png apple-touch-icon.png robots.txt sitemap.xml products assets ishan)

say() { printf '  %s\n' "$*"; }

echo "==> Deploying $SRC -> $DOCROOT"

[ -d "$DOCROOT" ] || { echo "!! docroot $DOCROOT does not exist"; exit 1; }
[ -f "$SRC/index.html" ] || { echo "!! source looks wrong: no index.html in $SRC"; exit 1; }

# --- 1. capture the cPanel PHP handler block before touching anything --------
HANDLER=""
if [ -f "$DOCROOT/.htaccess" ]; then
  HANDLER="$(sed -n '/BEGIN cPanel-generated handler/,/END cPanel-generated handler/p' "$DOCROOT/.htaccess" || true)"
fi
if [ -z "$HANDLER" ] && [ -f "$SRC/php-handler.fallback" ]; then
  say "live .htaccess had no handler block — using php-handler.fallback"
  HANDLER="$(cat "$SRC/php-handler.fallback")"
fi
[ -n "$HANDLER" ] || { echo "!! refusing to deploy: no PHP handler block found"; exit 1; }

# --- 2. replace the payload -------------------------------------------------
for item in "${PAYLOAD[@]}"; do
  [ -n "$item" ] || continue                       # never rm -rf an empty name
  [ -e "$SRC/$item" ] || { echo "!! missing from repo: $item"; exit 1; }
  rm -rf "${DOCROOT:?}/$item"
  cp -a "$SRC/$item" "$DOCROOT/"
  say "synced $item"
done

# --- 3. rebuild .htaccess = our config + the untouched cPanel block ----------
# The key installer is an operator tool, not site content. Put it in the home
# directory where the operator can actually reach it (matching ~/set-riva-key.sh),
# and make sure the copy under the docroot is never served.
if [ -f "$SRC/ishan/set-ishan-key.sh" ]; then
  install -m 700 "$SRC/ishan/set-ishan-key.sh" "$HOME/set-ishan-key.sh"
  say "installed ~/set-ishan-key.sh (0700)"
fi
rm -f "$DOCROOT/ishan/set-ishan-key.sh"
say "kept set-ishan-key.sh out of the docroot"

cat "$SRC/htaccess-head" > "$DOCROOT/.htaccess"
printf '%s\n' "$HANDLER" >> "$DOCROOT/.htaccess"
say "rebuilt .htaccess (handler block preserved)"

# --- 4. permissions ---------------------------------------------------------
find "$DOCROOT" -type d -exec chmod 755 {} \;
find "$DOCROOT" -type f -exec chmod 644 {} \;

echo "==> Done. $(date '+%d %b %Y %H:%M') — $(cd "$SRC" && git rev-parse --short HEAD 2>/dev/null || echo 'no git') deployed."
