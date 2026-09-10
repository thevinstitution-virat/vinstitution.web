#!/bin/bash
# Install or rotate Ishan AI's API key.
#
#   ~/set-ishan-key.sh <API_KEY> [MODEL] [ENDPOINT]
#
# Defaults to an OpenRouter endpoint, but any OpenAI-compatible /chat/completions
# URL works — pass it as the third argument.
#
# The key is tested against the endpoint BEFORE it is saved, so a bad key can
# never take the assistant offline. The config is written 0600, one level above
# the web root, and any existing config is backed up first.
set -u

CFG="$HOME/.vinstitution-chatbot.php"
KEY="${1:-}"
MODEL="${2:-google/gemini-2.5-flash-lite}"
ENDPOINT="${3:-https://openrouter.ai/api/v1/chat/completions}"
BUDGET="${ISHAN_BUDGET_USD:-1.00}"

if [ -z "$KEY" ]; then
  echo "Usage: ~/set-ishan-key.sh <API_KEY> [MODEL] [ENDPOINT]"
  if [ -f "$CFG" ]; then
    echo -n "Current: "
    php -r '$c=require getenv("HOME")."/.vinstitution-chatbot.php";
            printf("%s...(%d chars)  model=%s\n", substr($c["api_key"],0,10), strlen($c["api_key"]), $c["model"]);' 2>/dev/null \
      || echo "(config unreadable)"
  else
    echo "No config yet at $CFG"
  fi
  exit 1
fi

echo "Testing the key against $MODEL at $ENDPOINT ..."
TMP="/tmp/ishankey.$$"
CODE=$(curl -sS -o "$TMP" -w '%{http_code}' -m 45 "$ENDPOINT" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $KEY" \
  -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"say ok\"}],\"max_tokens\":5}")

if [ "$CODE" != "200" ]; then
  echo "REFUSED: the endpoint returned HTTP $CODE. Nothing was changed."
  echo "--- response ---"
  head -c 400 "$TMP"; echo
  rm -f "$TMP"
  exit 1
fi
rm -f "$TMP"
echo "Key works."

if [ -f "$CFG" ]; then
  cp -p "$CFG" "$CFG.bak-$(date +%Y%m%d-%H%M%S)"
  echo "Backed up the previous config."
fi

# Keep an existing shared secret if one is already set, so a configured
# server-to-server channel is not silently broken by a key rotation.
SECRET=""
if [ -f "$CFG" ]; then
  SECRET=$(php -r '$c=@require getenv("HOME")."/.vinstitution-chatbot.php"; echo $c["shared_secret"] ?? "";' 2>/dev/null)
fi

umask 077
cat > "$CFG" <<PHPEOF
<?php
// Ishan AI — Vinstitution website assistant. Read by ishan/chat.php.
// This file lives ABOVE the web root on purpose: the key must never be served.
return [
    'api_key'          => '$KEY',
    'model'            => '$MODEL',
    'endpoint'         => '$ENDPOINT',
    'daily_budget_usd' => $BUDGET,
    'shared_secret'    => '$SECRET',
];
PHPEOF
chmod 600 "$CFG"

echo "Saved $CFG (0600)."
echo "Daily budget: \$$BUDGET   Model: $MODEL"
echo
echo "Check it end to end:"
echo "  curl -sS -X POST https://vinstitution.com/ishan/chat.php \\"
echo "    -H 'Content-Type: application/json' -H 'Origin: https://vinstitution.com' \\"
echo "    --data '{\"messages\":[{\"role\":\"user\",\"content\":\"What is Vidyaverse?\"}]}'"
