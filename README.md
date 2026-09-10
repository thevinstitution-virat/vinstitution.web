# vinstitution.com

Marketing and ecosystem site for **Vinstitution** — the parent site for four connected
education platforms. Hand-built static HTML with one PHP endpoint. No build step, no
framework, no dependencies to install.

Live at **https://vinstitution.com**

---

## The four platforms

| Product | Live at | What it is |
|---|---|---|
| **Vidyaverse** | [vidyaverse.vinstitution.com](https://vidyaverse.vinstitution.com) | Campus operating system — 47 modules, one login. Also the OIDC identity provider the others sign in against. |
| **PDLMS Pro** | [pdlms.vinstitution.com](https://pdlms.vinstitution.com) | Multi-tenant AI digital library. Four reading modes plus *Varta*, which answers only from the book with paragraph-level citations. |
| **Digi Classroom** | [dgcl.vinstitution.com](https://dgcl.vinstitution.com) | NCERT-grounded AI tutor on the *Sarvagya* agentic-RAG engine. Citation-backed, Bloom-tagged, CBSE & ICSE Classes 6–12. |
| **e-Learning Practest** | [practest.live](https://practest.live) | Exam-pattern CBT mocks for SSC, Banking, Railways, UPSC and State PCS. |

> **`practest.in` is not in use** — it is registered but has no DNS record. Always link
> `practest.live`.

---

## Layout

```
index.html              hub page
products/
  vidyaverse.html       one deep-dive page per platform, each in its own accent colour
  pdlms.html
  digi-classroom.html
  practest.html
contact.php             enquiry handler -> tech@vinstitution.com, returns JSON
assets/
  css/style.css         the whole design system, one file
  js/main.js            progressive enhancement only; the site works without it
  img/                  OG share cards, app icons
  logos/                the three logo crops (see below)
htaccess-head           .htaccess minus the cPanel PHP block (assembled at deploy)
php-handler.fallback    safety copy of that cPanel block
deploy.sh               repo -> document root
.cpanel.yml             tells cPanel Git Version Control to run deploy.sh
```

### Design system

Light ground, brand palette taken from the logo: vermilion `#E8452A`, gold `#F5B31E`,
blue `#2E75BC`. Each product owns an accent that the whole page inherits through a single
`--accent` custom property, set per page in one line:

```html
<style>:root{--accent:var(--pd);--accent-lt:var(--pd-lt)}</style>
```

Type is Fraunces (display) + Plus Jakarta Sans (UI) + Mukta (Devanagari).

### Logo

The source logo is a stacked lockup in four tiers. **Do not squash the whole thing into a
header** — below roughly 90px tall the Sanskrit tagline and the ISO line turn to mush.
Three crops are committed instead:

| File | Contains | Used for |
|---|---|---|
| `vinstitution-lockup.png` | symbol + wordmark + ™ | header, 48px tall |
| `vinstitution-full.png` | everything, incl. *Uttiṣṭhata · Jāgrata · Prāpya* and ISO 9001:2015 | footer, schema.org logo |
| `vinstitution-mark.png` | symbol only | favicons, OG cards |

---

## How local, GitHub and cPanel are linked

```
  H:\vinstitution-site  --push-->  github.com/thevinstitution-virat/vinstitution.web
                                                    |
                                                    | cPanel Git Version Control pulls
                                                    v
                                    ~/repositories/vinstitution.web  (on the server)
                                                    |
                                                    | .cpanel.yml runs deploy.sh
                                                    v
                                            ~/public_html   (live site)
```

GitHub is the source of truth. The server holds a clone, never edits in place.

### Deploy

```bash
git add -A && git commit -m "..." && git push
ssh cpanel '~/repositories/vinstitution.web/deploy.sh'
```

The second line can also be done from cPanel → **Git™ Version Control** → *Manage* →
**Deploy HEAD Commit**, which runs the exact same `.cpanel.yml` task.

### Preview locally

```bash
php -S 127.0.0.1:8123 -t .
```

PHP is only needed so `contact.php` runs; every page is static.

---

## Things that will bite you

**Bump the cache stamp.** `.htaccess` caches CSS and JS for a month. After changing
`assets/css/style.css` or `assets/js/main.js`, bump `?v=` on the `<link>`/`<script>` tags
in all five pages or nobody sees the change. Currently `v=2`.

**Never remove the cPanel PHP handler block** from `.htaccess`. Without it `contact.php`
is served as text instead of executed. `deploy.sh` carries it across automatically and
refuses to deploy if it cannot find one.

**`.well-known/` stays.** Let's Encrypt validates there. `deploy.sh` replaces only the
paths it owns and never touches it.

**Mail.** Only `tech@` and `vidyaverse@` mailboxes exist on the domain. `contact.php`
delivers to `tech@vinstitution.com`.

**Cloudflare sits in front.** Static assets are cached hard at the edge, so purge the
cache after changing a file that keeps its name.

---

## Hosting

cPanel shared hosting, `sgp.centreserver.com` (OVH, Singapore), account `thevins1`.
vinstitution.com is the account's primary domain, so `~/public_html` is its document root.
DNS and CDN are on Cloudflare, proxied.
