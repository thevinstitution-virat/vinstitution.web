<?php
/**
 * chat.php — Ishan AI, the Vinstitution website assistant.
 *
 * The page posts the conversation here; this script adds the API key (kept
 * OUTSIDE the web root) plus the Vinstitution knowledge base, calls an
 * OpenAI-compatible endpoint, and returns the reply. The key never reaches
 * the browser.
 *
 * Ishan can raise two signals, written as a bare token on their own line and
 * converted here into structured JSON for the widget:
 *   [[LEAD]]      -> show the inline "leave your details" card
 *   [[WHATSAPP]]  -> show a WhatsApp button, pre-filled with the conversation
 *
 * The endpoint is deliberately channel-aware (`channel: "whatsapp"`) and accepts
 * a shared secret instead of an Origin header, so a future WhatsApp channel can
 * reuse this same brain rather than growing a second persona that drifts.
 *
 * Config lives one level ABOVE the web root:  <home>/.vinstitution-chatbot.php
 *   <?php return [
 *     'api_key'          => '...',
 *     'model'            => 'google/gemini-2.5-flash-lite',
 *     'endpoint'         => 'https://openrouter.ai/api/v1/chat/completions',
 *     'daily_budget_usd' => 1.00,
 *     'shared_secret'    => '',   // optional, for a server-to-server channel
 *   ];
 */
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');
header('Cache-Control: no-store');

const WA_NUMBER  = '919310959596';
const TEAM_EMAIL = 'tech@vinstitution.com';

function fail(int $code, string $msg): void {
    http_response_code($code);
    echo json_encode(['error' => $msg], JSON_UNESCAPED_UNICODE);
    exit;
}

// ---- 1. Method ---------------------------------------------------------------
if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') fail(405, 'Method not allowed.');

// ---- 2. Config ---------------------------------------------------------------
$cfgFile  = dirname($_SERVER['DOCUMENT_ROOT']) . '/.vinstitution-chatbot.php';
$cfg      = is_readable($cfgFile) ? (require $cfgFile) : [];
$apiKey   = $cfg['api_key']  ?? (getenv('ISHAN_API_KEY') ?: '');
$model    = $cfg['model']    ?? 'google/gemini-2.5-flash-lite';
$endpoint = $cfg['endpoint'] ?? 'https://openrouter.ai/api/v1/chat/completions';
$secret   = (string) ($cfg['shared_secret'] ?? '');
$dailyCap = (float) ($cfg['daily_budget_usd'] ?? 1.00);
// NOTE: whether a key is present is deliberately NOT reported here. The caller
// is vetted first (section 2c) so a stranger cannot probe our configuration
// state; the missing-key failure is raised after that check.

// ---- 2b. Spend guard ---------------------------------------------------------
date_default_timezone_set('Asia/Kolkata');

function ishan_usage_dir(): string {
    $d = dirname($_SERVER['DOCUMENT_ROOT']) . '/.ishan-usage';
    if (!is_dir($d)) @mkdir($d, 0700, true);
    return $d;
}

function ishan_spend_today(): float {
    $f = ishan_usage_dir() . '/spend-' . date('Y-m-d') . '.txt';
    return is_readable($f) ? (float) file_get_contents($f) : 0.0;
}

/** Add to today's total under a lock — two visitors can be mid-reply at once. */
function ishan_add_spend(float $usd): void {
    if ($usd <= 0) return;
    $h = @fopen(ishan_usage_dir() . '/spend-' . date('Y-m-d') . '.txt', 'c+');
    if (!$h) return;
    if (flock($h, LOCK_EX)) {
        $cur = (float) stream_get_contents($h);
        rewind($h);
        ftruncate($h, 0);
        fwrite($h, sprintf('%.8f', $cur + $usd));
        fflush($h);
        flock($h, LOCK_UN);
    }
    fclose($h);
}

/** One JSON line per call, so a surprising bill can be explained afterwards. */
function ishan_log_call(array $row): void {
    @file_put_contents(
        ishan_usage_dir() . '/calls-' . date('Y-m') . '.jsonl',
        json_encode($row, JSON_UNESCAPED_UNICODE) . "\n",
        FILE_APPEND | LOCK_EX
    );
}

/**
 * USD for a call. The provider's own accounting wins when present; the table is
 * a fallback so a repriced model distorts the figure rather than reporting zero.
 * USD per million tokens: [prompt, completion].
 */
function ishan_cost(array $usage, string $model): float {
    if (isset($usage['cost']) && (float) $usage['cost'] > 0) return (float) $usage['cost'];
    $P = [
        'google/gemini-2.5-flash-lite'    => [0.100, 0.400],
        'google/gemini-2.5-flash'         => [0.300, 2.500],
        'deepseek/deepseek-v4-flash-0731' => [0.065, 0.180],
        'anthropic/claude-haiku-4.5'      => [1.000, 5.000],
    ];
    if (!isset($P[$model])) return 0.0;
    return ((int) ($usage['prompt_tokens'] ?? 0) / 1e6) * $P[$model][0]
         + ((int) ($usage['completion_tokens'] ?? 0) / 1e6) * $P[$model][1];
}

$spentToday = ishan_spend_today();

// ---- 2c. Caller trust --------------------------------------------------------
// A server-to-server channel has no Origin header, so it authenticates with the
// shared secret instead — and is then rate-limited per conversation, not per IP,
// so one gateway address cannot throttle everybody behind it.
$presented = (string) ($_SERVER['HTTP_X_ISHAN_SECRET'] ?? '');
$trusted = ($secret !== '' && $presented !== '' && hash_equals($secret, $presented));

if (!$trusted) {
    $allowedHost = 'vinstitution.com';
    $src = $_SERVER['HTTP_ORIGIN'] ?? ($_SERVER['HTTP_REFERER'] ?? '');
    $srcHost = $src !== '' ? (string) parse_url($src, PHP_URL_HOST) : '';
    if (!$srcHost || substr($srcHost, -strlen($allowedHost)) !== $allowedHost) {
        fail(403, 'Requests must come from the Vinstitution website.');
    }
}

// Only now that the caller is vetted is it safe to report configuration state.
// The wording is for a visitor, not an operator: this endpoint is publicly
// reachable the moment the site deploys, which may be before the key lands.
if ($apiKey === '') {
    error_log('ishan chat.php: no api_key in ' . $cfgFile);
    fail(503, 'I am still being set up here. In the meantime the team is on WhatsApp at +91 93109 59596, or ' . TEAM_EMAIL . ' — they reply within one working day.');
}

// Same reasoning for the budget: a stranger should not be able to read our
// spend state either.
if ($dailyCap > 0 && $spentToday >= $dailyCap) {
    error_log(sprintf('ishan chat.php: daily cap reached ($%.4f of $%.2f)', $spentToday, $dailyCap));
    fail(503, 'I have reached my limit for today. Please WhatsApp us on +91 93109 59596 or email ' . TEAM_EMAIL . ' — the team replies quickly.');
}

// ---- 3. Rate limit -----------------------------------------------------------
$LIMIT = 30; $WINDOW = 600;
if ($trusted) {
    $conv = (string) ($_SERVER['HTTP_X_ISHAN_CONVERSATION'] ?? 'server');
    $rlKey = 'conv:' . preg_replace('/[^A-Za-z0-9@._-]/', '', $conv);
} else {
    $ip = $_SERVER['HTTP_CF_CONNECTING_IP'] ?? $_SERVER['HTTP_X_FORWARDED_FOR'] ?? $_SERVER['REMOTE_ADDR'] ?? '0';
    $rlKey = 'ip:' . trim(explode(',', $ip)[0]);
}
$dir = sys_get_temp_dir() . '/vin_ishan_rl';
@mkdir($dir, 0700, true);
$bucket = $dir . '/' . hash('sha256', $rlKey);
$now = time(); $hits = [];
if (is_readable($bucket)) {
    $hits = array_filter(array_map('intval', explode(',', (string) file_get_contents($bucket))), fn($t) => $t > $now - $WINDOW);
}
if (count($hits) >= $LIMIT) {
    fail(429, 'That is a lot of questions in a short time. Give me a few minutes, or message us on WhatsApp: +91 93109 59596.');
}
$hits[] = $now;
@file_put_contents($bucket, implode(',', $hits), LOCK_EX);

// ---- 4. Parse request --------------------------------------------------------
$body = json_decode(file_get_contents('php://input') ?: '[]', true);
if (!is_array($body)) fail(400, 'Invalid request.');
$history = is_array($body['messages'] ?? null) ? $body['messages'] : [];

// The conversation reference ties this chat to the enquiry it may become.
$ref = strtoupper(preg_replace('/[^A-Za-z0-9-]/', '', (string) ($body['ref'] ?? '')));
if ($ref === '' || strlen($ref) > 24) $ref = 'VIN-' . strtoupper(bin2hex(random_bytes(3)));

$clean = [];
foreach ($history as $m) {
    $role = ($m['role'] ?? '') === 'assistant' ? 'assistant' : 'user';
    $content = trim((string) ($m['content'] ?? ''));
    if ($content === '') continue;
    if (mb_strlen($content) > 1200) $content = mb_substr($content, 0, 1200);
    $clean[] = ['role' => $role, 'content' => $content];
}
$clean = array_slice($clean, -8);
if (!$clean || end($clean)['role'] !== 'user') fail(400, 'No question provided.');

// ---- 5. Persona + knowledge base ---------------------------------------------
$kbFile = __DIR__ . '/chat-kb.txt';
$kb = is_readable($kbFile) ? file_get_contents($kbFile) : '';

$system = <<<SYS
You are Ishan — the assistant for Vinstitution, an education-technology company in New Delhi that builds four connected platforms for Indian institutions and learners. You refer to yourself as "I" and to the company as "we". You are calm, precise and helpful, never pushy.

LANGUAGE — THIS IS A HARD RULE
You speak ENGLISH and HINDI only. Judge the language by the WORDS, never by the script alone.
- English in -> reply in English.
- Hindi written in Devanagari -> reply in Devanagari Hindi. ALWAYS. Devanagari is Hindi's own script, so seeing Devanagari is NEVER by itself a reason to switch to English or to ask which language they want.
  Example — visitor: "पीडीएलएमएस प्रो क्या है?"  You reply in Devanagari Hindi, normally, with no preamble.
- Hindi written in Roman letters (Hinglish) -> reply in the same Hinglish.
- ONLY when the words are genuinely a third language — Marathi, Gujarati, Bengali, Tamil, Telugu, Kannada, Malayalam, Punjabi, Urdu or any other — do you decline that language: reply in English, opening with one short line "I can help in English or Hindi — which would you prefer?" and then answer their question in English.
  Marathi is also written in Devanagari, so tell it apart by the vocabulary and grammar, not by the alphabet. If you are unsure whether Devanagari text is Hindi or Marathi, treat it as HINDI and answer in Hindi.
Never mix three languages in one reply. Never translate the platform names.

HOW YOU TALK
- Short: 2-5 sentences. Plain text. Short bullet lists are fine. No headings, no markdown bold.
- Specific and concrete, never salesy filler. No "Certainly!", no "Great question!".
- At most one emoji, and only when it genuinely fits. Usually none.

WHAT YOU KNOW
Answer ONLY from the knowledge base below. Stay strictly on Vinstitution — the four platforms, how they connect, what we build, and how to reach us. Politely decline anything unrelated and steer back.
Never invent a price, a per-student rate, a discount, a timeline, a delivery date, an uptime figure or a customer count. There is no published price list: everything is scoped per institution. If you do not know, say so plainly and offer to put them in touch.
You are not a tutor. If a student asks you to solve homework or explain a syllabus topic, say that is exactly what Digi Classroom is built for and point them there.

TWO SIGNALS YOU CAN RAISE
Write these as a bare token on its very own last line. Never mention or explain the token itself.
- [[LEAD]]      Raise this the moment any of these is true: they ask what it would cost, or for a
                quote, pricing or a demo; they describe their own institution (a school, college,
                coaching centre, a student count) and a problem they want solved; they say they want
                to get started, to see a walkthrough, or to talk to the team. It opens a small card
                where they leave their name and email or phone. Say one short line inviting them to
                leave their details there, then the token.
                Do NOT ask for name, email or phone in your own sentences, and do NOT tell them to
                email us instead — the card is how they reach us.
                Raise it once; if they ignore it, carry on helping and do not raise it again.
                Example — visitor: "We're a CBSE school with 900 students, what would Vidyaverse cost?"
                You: "Scope decides it — how many students, which of the 47 modules you switch on, and
                whether you take the library and the tutor alongside. Leave your details and the team
                will walk you through it properly.
                [[LEAD]]"
- [[WHATSAPP]]  when they want to talk to a person now, want a callback, or when the conversation has
                gone as far as it usefully can here.
Use each only when it genuinely helps. Never put more than one on the same reply unless they truly asked for both. Write your normal sentences first, then the token on its own line.

=== KNOWLEDGE BASE ===
$kb
=== END KNOWLEDGE BASE ===
SYS;

// ---- 5b. Deterministic language routing --------------------------------------
// A small fast model reads "reply in English and ask which language they want"
// as the most quotable rule in the prompt and fires it at the sight of any
// non-Latin script — including Devanagari, which is Hindi's own. Marathi shares
// that script, so the model cannot settle it from the alphabet either.
// Decide it here instead and hand the model one flat instruction for this turn.
$lastUser = '';
for ($i = count($clean) - 1; $i >= 0; $i--) {
    if ($clean[$i]['role'] === 'user') { $lastUser = $clean[$i]['content']; break; }
}

$hasDevanagari = (bool) preg_match('/\p{Devanagari}/u', $lastUser);
// Words that are Marathi and not Hindi. Hindi says क्या / नहीं / आप, Marathi काय / नाही / तुम्ही.
$looksMarathi  = (bool) preg_match('/(आहे|आहेत|नाही|आणि|तुम्ही|मला|काय|कसे|कुठे|माझ|त्यांनी|पाहिजे)/u', $lastUser);
// Scripts that are never Hindi or English: Bengali, Gurmukhi, Gujarati, Oriya,
// Tamil, Telugu, Kannada, Malayalam, and Arabic (Urdu).
$otherScript = (bool) preg_match(
    '/[\x{0980}-\x{09FF}\x{0A00}-\x{0A7F}\x{0A80}-\x{0AFF}\x{0B00}-\x{0B7F}'
  . '\x{0B80}-\x{0BFF}\x{0C00}-\x{0C7F}\x{0C80}-\x{0CFF}\x{0D00}-\x{0D7F}\x{0600}-\x{06FF}]/u',
    $lastUser);

if ($otherScript || $looksMarathi) {
    $langRule = 'REPLY LANGUAGE FOR THIS TURN: English. The visitor wrote a language we do not support. '
              . 'Begin your reply with exactly this sentence and nothing before it: '
              . '"I can help in English or Hindi — which would you prefer?" '
              . 'Then answer their question in English.';
} elseif ($hasDevanagari) {
    $langRule = 'REPLY LANGUAGE FOR THIS TURN: Devanagari Hindi. The visitor wrote Hindi in Devanagari. '
              . 'Answer normally in Devanagari Hindi. Do NOT ask which language they prefer, and do NOT '
              . 'reply in English.';
} else {
    $langRule = 'REPLY LANGUAGE FOR THIS TURN: mirror the visitor exactly — English if they wrote English, '
              . 'the same Roman-letter Hinglish if they wrote Hindi in Roman letters. Do NOT ask which '
              . 'language they prefer.';
}

$messages = array_merge(
    [['role' => 'system', 'content' => $system]],
    $clean,
    [['role' => 'system', 'content' => $langRule]]
);

// ---- 6. Call the model -------------------------------------------------------
$reqBody = [
    'model' => $model,
    'messages' => $messages,
    'max_tokens' => 450,
    'temperature' => 0.3,
];
if (strpos($endpoint, 'openrouter.ai') !== false) {
    $reqBody['provider']  = ['sort' => 'throughput'];
    $reqBody['reasoning'] = ['enabled' => false];
    $reqBody['usage']     = ['include' => true];
}

$ch = curl_init($endpoint);
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => json_encode($reqBody, JSON_UNESCAPED_UNICODE),
    CURLOPT_TIMEOUT => 45,
    CURLOPT_HTTPHEADER => [
        'Content-Type: application/json',
        'Authorization: Bearer ' . $apiKey,
        'HTTP-Referer: https://vinstitution.com',
        'X-Title: Vinstitution - Ishan AI',
    ],
]);
$resp = curl_exec($ch);
$httpCode = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
$curlErr = curl_error($ch);
curl_close($ch);

if ($resp === false) fail(502, 'I could not reach my brain just then. Try again, or WhatsApp us on +91 93109 59596.');
if ($httpCode < 200 || $httpCode >= 300) {
    error_log("ishan chat.php upstream $httpCode: $resp $curlErr");
    fail(502, 'I had a hiccup there. Try once more, or reach us on WhatsApp: +91 93109 59596.');
}

$data = json_decode($resp, true);

// Record the spend before anything below can fail, so a billed call is never
// missing from the ledger.
$usage = is_array($data['usage'] ?? null) ? $data['usage'] : [];
$cost  = ishan_cost($usage, $model);
ishan_add_spend($cost);
ishan_log_call([
    'at'      => date('c'),
    'ref'     => $ref,
    'channel' => (($body['channel'] ?? 'web') === 'whatsapp') ? 'whatsapp' : 'web',
    'model'   => $model,
    'in'      => (int) ($usage['prompt_tokens'] ?? 0),
    'out'     => (int) ($usage['completion_tokens'] ?? 0),
    'usd'     => round($cost, 6),
    'day_usd' => round($spentToday + $cost, 6),
    'cap_usd' => $dailyCap,
]);

$reply = trim((string) ($data['choices'][0]['message']['content'] ?? ''));
if ($reply === '') fail(502, 'I did not manage a reply there — please try again.');

// ---- 7. Extract signals ------------------------------------------------------
$wantsWhatsApp = (bool) preg_match('/\[\[\s*WHATSAPP\s*\]\]/i', $reply);
$wantsLead     = (bool) preg_match('/\[\[\s*LEAD\s*\]\]/i', $reply);
$reply = trim(preg_replace('/\[\[\s*(WHATSAPP|LEAD)\s*\]\]/i', '', $reply));

// Safety net: a small fast model drops the token often enough that real buying
// intent would otherwise reach nobody. The browser tells us whether the card has
// already been shown, so a visitor is never asked twice.
$leadShown = !empty($body['lead_shown']);
if ($leadShown) $wantsLead = false;
if (!$wantsLead && !$leadShown) {
    $lastUser = '';
    for ($i = count($clean) - 1; $i >= 0; $i--) {
        if ($clean[$i]['role'] === 'user') { $lastUser = $clean[$i]['content']; break; }
    }
    $intent = '/\b(cost|costs|price|pricing|quote|quotation|estimate|charge|charges|rate|budget|'
            . 'how much|kitna|kitne|daam|keemat|kimat|'
            . 'demo|walkthrough|trial|onboard|onboarding|implement|'
            . 'my school|our school|my college|our college|my institute|our institute|'
            . 'coaching|students do|get started|want to start|sign up|talk to|'
            . 'call me|callback|call back|contact me|reach me)\b/iu';
    if ($lastUser !== '' && preg_match($intent, $lastUser)) $wantsLead = true;
}

// A model that emits nothing but a token would otherwise leave an empty bubble.
if ($reply === '') {
    $reply = $wantsLead
        ? 'Leave your details and the team will come back to you.'
        : 'Here you go.';
}

// A future WhatsApp channel has no widget to render cards, so the signals have
// to become part of the message itself. Ishan stays one persona across both.
$channel = (($body['channel'] ?? 'web') === 'whatsapp') ? 'whatsapp' : 'web';
if ($channel === 'whatsapp') {
    if ($wantsLead) {
        $reply = trim($reply . "\n\nIf you send me your name and email, I will put this in front of the team today.");
    }
    echo json_encode([
        'reply'       => $reply,
        'ref'         => $ref,
        'wants_lead'  => $wantsLead,
        'wants_human' => $wantsWhatsApp,
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

$out = ['reply' => $reply, 'ref' => $ref];

if ($wantsLead) {
    $out['lead'] = [
        'title' => 'Let the team pick this up',
        'note'  => 'Name and one way to reach you is enough. We reply within one working day.',
        'cta'   => 'Send to the team',
    ];
}

if ($wantsWhatsApp) {
    // Carry the visitor's own words across so the WhatsApp thread starts with
    // context and nobody has to ask everything again.
    $said = [];
    foreach ($clean as $m) {
        if ($m['role'] === 'user') $said[] = $m['content'];
    }
    $said = array_slice($said, -3);
    $ctx = trim(implode(' / ', $said));
    if (mb_strlen($ctx) > 400) $ctx = mb_substr($ctx, 0, 400) . '...';

    $prefill = "Hi Vinstitution — I was chatting with Ishan on your website.\n\n"
             . ($ctx !== '' ? "What I'm after: " . $ctx . "\n\n" : '')
             . "Could you help me from here?\n\n"
             . "[ref " . $ref . "]";

    $out['whatsapp'] = [
        'label'  => 'Continue on WhatsApp',
        'number' => WA_NUMBER,
        'url'    => 'https://wa.me/' . WA_NUMBER . '?text=' . rawurlencode($prefill),
    ];
}

echo json_encode($out, JSON_UNESCAPED_UNICODE);
