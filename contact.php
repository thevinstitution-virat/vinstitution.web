<?php
/**
 * Vinstitution — enquiry handler
 * Receives the site enquiry form and mails it to the team inbox.
 * Returns JSON {"ok":true} / {"ok":false,"error":"..."} — the shape main.js expects.
 */
declare(strict_types=1);
header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');

// Mailboxes that actually exist on this cPanel account for vinstitution.com.
const MAIL_TO   = 'tech@vinstitution.com';
const MAIL_FROM = 'no-reply@vinstitution.com';

function fail(int $code, string $msg): void {
    http_response_code($code);
    echo json_encode(['ok' => false, 'error' => $msg], JSON_UNESCAPED_UNICODE);
    exit;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    fail(405, 'Method not allowed.');
}

// Honeypot: a filled hidden field means a bot. Answer 200 so it learns nothing.
if (trim((string)($_POST['website'] ?? '')) !== '') {
    echo json_encode(['ok' => true], JSON_UNESCAPED_UNICODE);
    exit;
}

/** Strip CR/LF so nothing can be smuggled into a mail header. */
function clean(string $v, int $max = 300): string {
    $v = str_replace(["\r", "\n", "\0"], ' ', trim($v));
    return mb_substr($v, 0, $max);
}

$name     = clean($_POST['name']     ?? '', 120);
$org      = clean($_POST['org']      ?? '', 160);
$email    = clean($_POST['email']    ?? '', 190);
$phone    = clean($_POST['phone']    ?? '', 40);
$interest = clean($_POST['interest'] ?? '', 80);
$message  = mb_substr(trim((string)($_POST['message'] ?? '')), 0, 5000);

$errors = [];
if ($name === '')    { $errors[] = 'Name is required.'; }
if ($email === '')   { $errors[] = 'Email is required.'; }
elseif (!filter_var($email, FILTER_VALIDATE_EMAIL)) { $errors[] = 'Please provide a valid email address.'; }
if ($message === '') { $errors[] = 'Message is required.'; }
if ($errors) {
    fail(400, implode(' ', $errors));
}

$lines = [
    'New enquiry from vinstitution.com',
    str_repeat('=', 36),
    '',
    'Name:        ' . $name,
    'Email:       ' . $email,
];
if ($org !== '')      { $lines[] = 'Institution: ' . $org; }
if ($phone !== '')    { $lines[] = 'Phone:       ' . $phone; }
if ($interest !== '') { $lines[] = 'Interest:    ' . $interest; }
$lines[] = '';
$lines[] = 'Message:';
$lines[] = $message;
$lines[] = '';
$lines[] = str_repeat('-', 36);
$lines[] = 'Sent ' . date('d M Y, H:i') . ' IST from ' . ($_SERVER['REMOTE_ADDR'] ?? 'unknown');

$body    = implode("\n", $lines);
$subject = '=?UTF-8?B?' . base64_encode('Enquiry — ' . ($interest !== '' ? $interest : 'vinstitution.com')) . '?=';

$headers = implode("\r\n", [
    'From: Vinstitution Website <' . MAIL_FROM . '>',
    'Reply-To: ' . $email,
    'MIME-Version: 1.0',
    'Content-Type: text/plain; charset=UTF-8',
    'Content-Transfer-Encoding: 8bit',
    'X-Mailer: Vinstitution-Site/1.0',
]);

// Warnings are suppressed so a transport failure cannot corrupt the JSON body.
if (@mail(MAIL_TO, $subject, $body, $headers, '-f' . MAIL_FROM)) {
    echo json_encode(['ok' => true], JSON_UNESCAPED_UNICODE);
} else {
    fail(500, 'Mail could not be sent. Please email tech@vinstitution.com directly.');
}
