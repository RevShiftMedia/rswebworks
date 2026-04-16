# RSWebWorks Mockup Agent — Standards & Operating Manual

This file is the permanent brain for the Mockup Agent. Read it fully before doing anything.
Every run starts here. Every design decision defers to this file.

---

## What This Agent Does (Full Pipeline)

1. **Read leads.csv** — find all leads where `status` is blank/empty
2. **For each lead:** fetch their website, extract brand colors, generate a world-class HTML mockup
3. **Write mockup** to `~/rswebworks/[slug]/index.html`
4. **Commit + push** to git — Vercel auto-deploys to `https://rswebworks.com/[slug]/`
5. **Run push_to_instantly.py** — enroll leads in outreach campaign
6. **Update leads.csv** — mark processed leads with status `pushed`
7. **Report to Cortex** — log task start, progress, and completion to Supabase

---

## Cortex Reporting (Do This Every Run)

Agent ID: `cab12742-4598-429a-adb4-84a5608e06a0`
Supabase URL: `https://infzwlfunkgjupoikylr.supabase.co`
Service Role Key: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImluZnp3bGZ1bmtnanVwb2lreWxyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjgwNDU4NSwiZXhwIjoyMDg4MzgwNTg1fQ.EuTJDQoYzTaxlcgxL2asQcaOZaZW1LrUesgpbcAgay4`

### On run START — create Task record:
```bash
curl -s -X POST "https://infzwlfunkgjupoikylr.supabase.co/rest/v1/Task" \
  -H "apikey: [SERVICE_ROLE_KEY]" \
  -H "Authorization: Bearer [SERVICE_ROLE_KEY]" \
  -H "Content-Type: application/json" \
  -H "Prefer: return=representation" \
  -d '{
    "title": "Mockup batch — [N] leads",
    "agentId": "cab12742-4598-429a-adb4-84a5608e06a0",
    "squad": "rswebworks",
    "status": "running",
    "startedAt": "[ISO timestamp]",
    "model": "claude-sonnet-4-5",
    "logs": [{"time": "[timestamp]", "msg": "Starting batch of [N] leads"}]
  }'
```
Capture the returned `id` — you'll need it to update the task.

### On run COMPLETE — update Task record:
```bash
curl -s -X PATCH "https://infzwlfunkgjupoikylr.supabase.co/rest/v1/Task?id=eq.[TASK_ID]" \
  -H "apikey: [SERVICE_ROLE_KEY]" \
  -H "Authorization: Bearer [SERVICE_ROLE_KEY]" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "complete",
    "completedAt": "[ISO timestamp]",
    "output": "Generated [N] mockups. Pushed [N] leads to Instantly. Live at rswebworks.com.",
    "logs": [{"time": "[timestamp]", "msg": "[summary of each lead processed}"]
  }'
```

### On ERROR — update Task to stuck:
```bash
# Same PATCH call but: "status": "stuck", "output": "[error message]"
```

### Update Agent status (idle ↔ running):
```bash
# Set running at start:
curl -s -X PATCH "https://infzwlfunkgjupoikylr.supabase.co/rest/v1/Agent?id=eq.cab12742-4598-429a-adb4-84a5608e06a0" \
  -H "apikey: [SERVICE_ROLE_KEY]" \
  -H "Authorization: Bearer [SERVICE_ROLE_KEY]" \
  -H "Content-Type: application/json" \
  -d '{"status": "running"}'

# Set idle at end — same call with "status": "idle"
```

---

## Lead Pipeline

### leads.csv columns:
`place_id, business_name, first_name, email, phone, address, city, state, rating, review_count, website, track, flaw, niche, quality_score, slug, status, date_found`

### Processing rules:
- Only process leads where `status` is **empty/blank**
- Skip leads where `website` is `none` or empty — no website = no brand to analyze
- Skip leads where `slug` is empty
- After successful mockup + push: set `status = pushed`
- If mockup generation fails: set `status = failed` and continue to next lead
- Run `dedup_csv.py` first if it hasn't run today

### Priority order:
- Track A leads (`track = A`) first — they have websites and emails
- `quality_score >= 2` preferred but process all Track A leads regardless

---

## Design Philosophy — Read This Before Every Mockup

You are building a **showstopper** — a website so specific, so polished, and so visually distinctive that when the business owner sees it, they physically cannot say no. This is not a template. This is not AI output. This is what a $3,000 custom agency build looks like.

**Before writing a single line of HTML, answer these questions:**
1. What is the TONE of this business and niche? (see niche table below)
2. What FONT PAIRING matches that tone? (see typography section)
3. What AESTHETIC DIRECTION will make this unforgettable? Pick one extreme and commit.
4. What is the ONE THING someone will remember about this site?

**Sketch an ASCII wireframe before coding:**
```
┌─────────────────────────────────────────┐
│  STICKY HEADER — logo + phone CTA       │
├──────────────────────┬──────────────────┤
│                      │  ┌─────────────┐ │
│  HERO LEFT 60%       │  │ FROSTED     │ │
│  badge + headline    │  │ GLASS CARD  │ │
│  subhead + CTAs      │  │ 40%         │ │
│  trust bar           │  └─────────────┘ │
├──────────────────────┴──────────────────┤
│  STAT ROW  │  STAT  │  STAT  │  STAT   │
├─────────────────────────────────────────┤
│  SERVICES  3-col grid (fixed repeat(3)) │
├─────────────────────────────────────────┤
│  WHY CHOOSE US — dark section           │
├─────────────────────────────────────────┤
│  HOW IT WORKS — darkest section         │
├─────────────────────────────────────────┤
│  REVIEWS — off-white                    │
├─────────────────────────────────────────┤
│  SERVICE AREAS — dark                   │
├─────────────────────────────────────────┤
│  CONTACT FORM — white                   │
├─────────────────────────────────────────┤
│  CTA BAND — accent gradient             │
├─────────────────────────────────────────┤
│  FOOTER — very dark                     │
└─────────────────────────────────────────┘
```

---

## Typography — Required

**Never use:** Inter, Roboto, Arial, system-ui, Space Grotesk. These are generic and kill perceived quality.

**Always load via Google Fonts `@import` at top of `<style>`.**

### Font pairings by niche:

| Niche | Display Font | Body Font | Rationale |
|-------|-------------|-----------|-----------|
| Plumbing / HVAC / Electrician | Bebas Neue | Open Sans | Industrial urgency, tradesperson credibility |
| Junk Removal / Hauling | Oswald | Source Sans 3 | Bold, no-nonsense, working-class confidence |
| Pest Control / Exterminators | Barlow Condensed | Nunito Sans | Clinical precision meets approachability |
| Roofing / Construction | Anton | DM Sans | Heavy-duty, structural authority |
| Lawn / Landscaping / Tree | Playfair Display | Lora | Natural, premium outdoor feel |
| Painting / Cleaning | Plus Jakarta Sans | Manrope | Fresh, modern, clean |
| Pool / Pressure Washing | Syne | DM Sans | Premium leisure, resort aesthetic |
| General / Other | Outfit | Nunito | Modern, friendly, versatile |

**Usage rules:**
- Display font: headlines, section titles, stat numbers
- Body font: descriptions, body copy, nav items
- Display font size for hero headline: `clamp(42px, 6vw, 64px)` — scales with viewport
- Letter-spacing on display: `-0.02em` for large headlines
- Line-height on body: `1.65`

---

## Brand Analysis — How to Extract Colors

Fetch the business's website HTML and CSS. Extract brand colors using this priority order:

### Step 1 — Structural CSS extraction (most reliable)
Look for background-color declarations in these selectors (in priority order):
1. `header`, `.header`, `nav`, `.navbar`, `.nav` → almost always the primary brand color
2. `footer`, `.footer`
3. `.btn`, `button`, `.hero`, `.cta`
4. Body/section backgrounds

### Step 2 — Neon filter (reject bad colors)
Reject any color where saturation > 0.90 AND brightness > 0.85 — neon/default browser colors, not real brand.

### Step 3 — Accent selection
Accent = most-used color with color distance > 60 from primary (RGB space).

### Step 4 — Fallback
If no structural colors found: use frequency counting. Dark colors (luminance < 0.3) → primary.

### Step 5 — Darken primary 15%
Always darken the extracted primary ~15% for richer depth:
- `#1e3a5f` → `#0d2b4e`
- `#32373C` → `#1a1e21`
- `#2e7d32` → `#1b5e20`

### Font detection from their site:
- Serif on their site → lean into editorial/luxury direction
- Sans-serif → clean/modern direction
- No detectable font → use niche default from table above

---

## Animations — Required

**Animation micro-plan (write this before coding):**
```
page load:   hero content staggered fadeUp, 400ms ease-out, 100ms increments
cards:       fadeUp on scroll via IntersectionObserver, 400ms ease-out
hover cards: 200ms [Y0→-4px, shadow↗]
button:      150ms [scale 1→0.97→1] press
stats:       count-up animation on scroll entry (JS)
header:      box-shadow appears after 50px scroll
```

### Staggered card entry (required on services, reviews, why-choose-us):
```css
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(24px); }
  to   { opacity: 1; transform: translateY(0); }
}
.card { opacity: 0; animation: fadeUp 0.4s ease-out forwards; }
.card:nth-child(1) { animation-delay: 0.1s; }
.card:nth-child(2) { animation-delay: 0.2s; }
.card:nth-child(3) { animation-delay: 0.3s; }
.card:nth-child(4) { animation-delay: 0.4s; }
.card:nth-child(5) { animation-delay: 0.5s; }
.card:nth-child(6) { animation-delay: 0.6s; }
```

Trigger via IntersectionObserver — add class `visible` when 20% in view.

### Hero entry animation (required):
```css
@keyframes heroFadeUp {
  from { opacity: 0; transform: translateY(32px); }
  to   { opacity: 1; transform: translateY(0); }
}
.hero-badge    { animation: heroFadeUp 0.5s ease-out 0.1s both; }
.hero-headline { animation: heroFadeUp 0.5s ease-out 0.2s both; }
.hero-sub      { animation: heroFadeUp 0.5s ease-out 0.35s both; }
.hero-ctas     { animation: heroFadeUp 0.5s ease-out 0.5s both; }
.hero-trust    { animation: heroFadeUp 0.5s ease-out 0.65s both; }
.hero-card     { animation: heroFadeUp 0.5s ease-out 0.4s both; }
```

### Grain overlay (use on hero and CTA band — instant quality uplift):
```css
.hero::after, .cta-band::after {
  content: '';
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
  opacity: 0.12;
  pointer-events: none;
  z-index: 0;
}
.hero > *, .cta-band > * { position: relative; z-index: 1; }
```

### Stat counter animation (required on stats row):
```javascript
function animateCount(el) {
  const target = parseInt(el.dataset.target);
  const duration = 1800;
  const start = performance.now();
  const update = (time) => {
    const progress = Math.min((time - start) / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.floor(ease * target).toLocaleString() + (el.dataset.suffix || '');
    if (progress < 1) requestAnimationFrame(update);
  };
  requestAnimationFrame(update);
}
// Trigger on intersection:
new IntersectionObserver((entries) => {
  entries.forEach(e => { if (e.isIntersecting) animateCount(e.target); });
}, { threshold: 0.5 }).observe(statEl);
```

---

## Mockup HTML Spec — All 10 Sections

Every mockup MUST include ALL 10 sections in this order. Do not stop early. File ends with `</html>`.

**Target file size: 35–55KB.** Under 30KB = truncated, start over.

### CSS Variable Setup (always at top of `<style>`):
```css
@import url('https://fonts.googleapis.com/css2?family=[DisplayFont]:wght@400;700;900&family=[BodyFont]:wght@400;500;600&display=swap');

:root {
  --primary: [darkened extracted primary];
  --primary-dark: [primary darkened another 15%];
  --accent: [extracted accent];
  --accent-dark: [accent darkened 20%];
  --bg: #ffffff;
  --bg-off: #f7f8fc;
  --t1: #ffffff;
  --t2: rgba(255,255,255,0.75);
  --t3: rgba(255,255,255,0.5);
  --dark-text: #1a1a2e;
  --grey-text: #6b7280;
  --border: #e8edf5;
  --font-display: '[DisplayFont]', sans-serif;
  --font-body: '[BodyFont]', sans-serif;
  --radius: 12px;
  --shadow: 0 4px 20px rgba(0,0,0,0.12);
  --shadow-lg: 0 8px 40px rgba(0,0,0,0.2);
}

* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: var(--font-body); background: var(--bg); color: var(--dark-text); line-height: 1.65; }
h1, h2, h3, h4 { font-family: var(--font-display); letter-spacing: -0.02em; }
```

### Section 1 — Sticky Header
- Background: `var(--primary)` (NOT white, EVER)
- Business name: display font, bold, 20px, white
- Tagline: body font, 13px, `var(--t2)`
- CTA button: `var(--accent)` bg, white text, phone SVG icon inline
- `position: sticky; top: 0; z-index: 1000`
- `box-shadow: 0 2px 12px rgba(0,0,0,0.3)` — always visible, don't add on scroll
- JS: add class `scrolled` after 50px for slightly deeper shadow

### Section 2 — Hero (2-column asymmetric)
Background: dark gradient from `var(--primary-dark)` to `var(--primary)`.
Apply grain overlay (`.hero::after`).
Apply hero entry animations to each child element.

**Left column (60%):**
- Badge pill: `var(--accent)` bg, display font, 11px uppercase, SVG star
- Headline: `clamp(42px, 6vw, 64px)`, display font, white, MAX 6 words
  - Service keyword in `<span style="color: var(--accent)">`
- Subheadline: body font, 18px, `var(--t2)`, city-specific
- Primary CTA: `var(--accent)` bg, display font, phone SVG, box-shadow, hover lift
- Secondary CTA: ghost — white border + white text ONLY (never accent on dark)
- Trust bar: SVG stars + rating · review count · licensed/insured · differentiator

**Right column (40%):**
```css
.hero-card {
  background: rgba(255,255,255,0.07);
  border: 1px solid rgba(255,255,255,0.15);
  box-shadow: 0 8px 32px rgba(0,0,0,0.3);
  backdrop-filter: blur(12px);
  border-radius: 16px;
  padding: 28px 32px;
}
```
- 4 value props with SVG checkmarks, display font titles, body font descriptions
- Bottom: phone number styled prominently

### Stats Row (below hero)
4 stat boxes, full width dark bar (`var(--primary)`):
- Large number: display font, `clamp(32px, 4vw, 48px)`, `var(--accent)` (white if contrast fails)
- Use `data-target` + JS counter animation
- Label: body font, 13px, `var(--t2)`
- Subtle `border-right: 1px solid rgba(255,255,255,0.1)` between boxes

### Section 3 — Services Grid
White background (`var(--bg)`). Fixed grid: `repeat(3, 1fr)`.
Breakpoints: `≤900px → repeat(2,1fr)`, `≤600px → 1fr`.

Section label: 10px, uppercase, `var(--accent)`, letter-spacing 0.1em, display font.
Title: 36px, display font, `var(--dark-text)`.
Subtitle: body font, `var(--grey-text)`.

Each card:
```css
.service-card {
  background: var(--bg);
  border: 1px solid var(--border);
  border-top: 3px solid transparent;
  border-radius: var(--radius);
  padding: 28px 24px;
  box-shadow: var(--shadow);
  transition: all 0.25s ease;
}
.service-card:hover {
  border-top-color: var(--accent);
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}
```
Icon: 48px circle, `var(--accent)` at 12% opacity bg, SVG stroke in `var(--accent)`.
Service name: 17px, display font, `var(--dark-text)`.
Description: 14px, body font, `var(--grey-text)`, line-height 1.6.
Link: `var(--accent)`, 13px, font-weight 600, `→` arrow.

Apply staggered fadeUp animation.

### Section 4 — Why Choose Us
Background: `var(--primary)`. Apply grain overlay.

Title: display font, 36px, white.
Subtitle: body font, `var(--t2)`.

Top row: 4 stat cards — dark bg (`var(--primary-dark)`), accent numbers, white labels.
Bottom: 4 differentiators in 2-col grid — SVG checkmark in accent circle, display font title (white), body font description (`var(--t2)`).

### Section 5 — How It Works
Background: `var(--primary-dark)` (very dark).
Title: display font, 36px, white.

3 steps horizontal. Between steps: dashed connector line in `rgba(255,255,255,0.15)`.
Each step:
- Numbered circle: `var(--accent)` fill, display font, 28px bold
- SVG icon: 36px, white stroke
- Title: display font, 18px, white
- Description: body font, 14px, `var(--t2)`

### Section 6 — Reviews
Background: `var(--bg-off)`.
Title: display font, 36px, `var(--dark-text)`. Google badge top-right.

3 review cards — apply staggered fadeUp:
```css
.review-card {
  background: white;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 28px;
  box-shadow: 0 2px 16px rgba(0,0,0,0.06);
  transition: all 0.25s ease;
}
.review-card:hover {
  box-shadow: 0 8px 32px rgba(0,0,0,0.12);
  transform: translateY(-3px);
}
```

SVG quote mark (NOT `"` text) — accent color, 50% opacity:
```html
<svg width="32" height="24" viewBox="0 0 32 24" fill="currentColor" style="color: var(--accent); opacity: 0.5; margin-bottom: 14px; display: block;">
  <path d="M0 24V14.4C0 6.56 4.64 1.6 13.92 0l1.44 2.24C10.56 3.52 8 6.56 8 11.2H13.6V24H0zm18.4 0V14.4C18.4 6.56 23.04 1.6 32.32 0l1.44 2.24c-4.8 1.28-7.36 4.32-7.36 8.96H32V24H18.4z"/>
</svg>
```

Quote text: body font, italic, 15px, line-height 1.7, `var(--dark-text)`.
Divider: `1px solid var(--border)`, margin 16px 0.
Avatar: 40px circle, `var(--accent)` at 20% opacity, display font initials, `var(--accent)` text.
Name: display font, 15px, bold. Location + "Google Review": body font, 12px, `var(--grey-text)`.

### Section 7 — Service Areas
Background: `var(--primary)`.
2-column: left (headline + body + CTA), right (dark card with neighborhood chips).
Chip hover: `var(--accent)` bg, white text.

### Section 8 — Contact / Booking Form
Background: white.
2-column: left (form), right (dark info card).
Form inputs:
```css
input, select, textarea {
  width: 100%;
  background: var(--bg-off);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px 14px;
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--dark-text);
  transition: border-color 0.2s;
}
input:focus, select:focus, textarea:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.1);
}
```
Submit button: `var(--accent)` bg, display font, full width, 16px, box-shadow.

### Section 9 — CTA Band
Gradient: `linear-gradient(135deg, var(--accent-dark), var(--accent))`.
Apply grain overlay.
Headline: display font, `clamp(28px, 4vw, 42px)`, white, max 8 words.
Subtext: body font, `var(--t2)`.
Button: white bg, `var(--accent)` text OR dark bg with white text.

### Section 10 — Footer
Background: `var(--primary-dark)` (very dark).
3–4 column grid: brand + description, services, service areas, contact.
Display font for column headers. Body font for links/text.
All text: `var(--t2)` for links, `var(--t3)` for secondary.
Bottom bar: `1px solid rgba(255,255,255,0.08)` top border, copyright + license.

---

## CSS Architecture

```css
/* Sections */
section { padding: 90px 0; }
.container { max-width: 1100px; margin: 0 auto; padding: 0 24px; }

/* Buttons */
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--accent);
  color: white;
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 700;
  padding: 14px 28px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(0,0,0,0.25);
  transition: all 0.15s ease;
  text-decoration: none;
}
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.3); }
.btn-primary:active { transform: scale(0.97); }

.btn-ghost {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  color: white;
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 600;
  padding: 13px 28px;
  border-radius: 8px;
  border: 2px solid rgba(255,255,255,0.6);
  cursor: pointer;
  transition: all 0.15s ease;
  text-decoration: none;
}
.btn-ghost:hover { border-color: white; background: rgba(255,255,255,0.08); }

/* Grids — ALWAYS fixed, never auto-fit/minmax */
.grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
.grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
.grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 32px; }

@media (max-width: 900px) {
  .grid-3, .grid-4 { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
  .grid-3, .grid-4, .grid-2 { grid-template-columns: 1fr; }
}
```

---

## Contrast Rules — Non-Negotiable

- **On dark/colored backgrounds:** body text = white. Secondary = `var(--t2)` = rgba(255,255,255,0.75)
- **Light accents** (yellow, lime, light blue, pink — luminance > 0.4): MUST be darkened 40% before use as text on white sections
- **Stat numbers on dark:** use accent only if contrast ratio >3:1. Otherwise white.
- **Ghost buttons:** border AND text = white ALWAYS on dark/colored backgrounds
- **NEVER** accent color as text on same-hue background
- **Section rhythm:** dark → light → dark → light → dark (strict alternation)

---

## SVG Icons — No Emojis Ever

Never use emoji. Always inline SVG. Use `stroke="currentColor"` and set color via parent CSS.

### Core library:

**Phone:**
```html
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 13a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3.56 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
```
**Checkmark:**
```html
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
```
**Star:**
```html
<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
```
**Shield:**
```html
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
```
**Wrench:**
```html
<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
```
**Droplet:**
```html
<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>
```
**Zap:**
```html
<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
```
**Home:**
```html
<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
```
**Truck:**
```html
<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>
```
**Leaf:**
```html
<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/></svg>
```
**Sofa:**
```html
<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 9V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v3"/><path d="M2 11a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-3z"/><path d="M4 16v2"/><path d="M20 16v2"/></svg>
```
**Google G:**
```html
<svg width="20" height="20" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
```

---

## Copy Standards

### Headlines (hero):
- MAX 6 words. Display font.
- Format: "[City]'s [Adjective] **[Keyword]**"
- Keyword in `<span style="color: var(--accent)">`
- Examples: "Houston's Trusted Pest Experts" / "Austin's Fastest Junk Removal" / "Tucson's Most Trusted Plumbers"

### Subheadlines:
- 1–2 sentences, 18px body font
- Reference the city AND a specific local landmark, neighborhood, or geographic detail
- Focus on customer outcome, not company features

### Review quotes — must feel real:
- Name the specific service ("burst pipe at 11 PM", "rodent in our attic", "full garage cleanout")
- Include a time detail ("showed up in 45 minutes", "done in 2 hours")
- Include a value detail ("fair price", "no surprise charges", "worth every penny")
- 3–5 sentences, first person, conversational. No corporate language.
- Different names, different neighborhoods, different dates

### Service descriptions:
- 2–3 lines. Start with customer's problem, end with the outcome.
- Never use: "we offer", "our team provides", "professional services"

---

## Niche Profiles — Aesthetic Direction Per Niche

### Plumbing
- **Fonts:** Bebas Neue + Open Sans
- **Aesthetic:** Industrial precision — dark navy, clean whites, orange urgency accent
- **Tone:** Trustworthy veteran. 30 years in business. No nonsense. Gets it done.
- **Key differentiators:** 24/7 emergency, licensed & insured, upfront pricing, no hidden fees
- **Services:** Drain Cleaning, Water Heater Repair, Pipe Repair, Leak Detection, Sewer Line, Emergency

### HVAC / Electrician
- **Fonts:** Bebas Neue + Open Sans
- **Aesthetic:** Technical authority — deep charcoal, electric blue or safety orange accents
- **Tone:** Certified expert. Precision work. Your comfort depends on us.
- **Key differentiators:** NATE certified, same-day, financing available, 10-year warranty
- **Services:** AC Repair, Heating, Installation, Maintenance, Emergency, Duct Cleaning

### Junk Removal / Hauling
- **Fonts:** Oswald + Source Sans 3
- **Aesthetic:** Bold and utilitarian — dark forest green or charcoal, orange CTAs, heavy type
- **Tone:** Working-class confidence. No drama. You call, we haul.
- **Key differentiators:** Same-day, eco-friendly, no hidden fees, free estimates
- **Services:** Furniture, Appliances, Estate Cleanouts, Construction Debris, Yard Waste, Same-Day

### Pest Control / Exterminators
- **Fonts:** Barlow Condensed + Nunito Sans
- **Aesthetic:** Clinical confidence — deep purple or dark teal, clean green accents, precision feel
- **Tone:** Reassuring expert. We protect your family. Guaranteed.
- **Key differentiators:** Pet-safe, same-day, satisfaction guarantee, family-owned
- **Services:** Roach, Rodent, Termite, Mosquito, Bed Bug, Ant

### Roofing / Construction
- **Fonts:** Anton + DM Sans
- **Aesthetic:** Heavy-duty structural — deep charcoal or brick red, bold yellow or white accents
- **Tone:** Serious protection. Storm-tested. Built to last.
- **Key differentiators:** Licensed & bonded, free inspection, insurance claims, local
- **Services:** Roof Repair, Replacement, Storm Damage, Gutters, Inspections, Emergency Tarping

### Lawn / Landscaping / Tree
- **Fonts:** Playfair Display + Lora
- **Aesthetic:** Premium outdoor — deep forest green, warm cream/white, natural textures
- **Tone:** Craftsman pride. Your yard is our canvas.
- **Key differentiators:** Licensed, insured, free estimate, weekly maintenance
- **Services:** Lawn Mowing, Landscaping, Tree Trimming, Fertilization, Cleanup, Irrigation

### Painting / Cleaning / Other
- **Fonts:** Plus Jakarta Sans + Manrope
- **Aesthetic:** Fresh modern — clean whites, teal or coral accents, airy spacing
- **Tone:** Reliable, local, detail-oriented.

---

## Git + Deploy Workflow

```bash
cd ~/rswebworks
git add -A
git commit -m "mockups: batch [N] — [date]"
git push origin main
# Vercel auto-deploys — live at https://rswebworks.com/[slug]/
```

---

## Quality Checklist (Before Marking Any Batch Complete)

- [ ] File size 30–55KB (under 30KB = truncated, redo)
- [ ] Google Font `@import` present and matches niche font pairing
- [ ] Hero has 2-column asymmetric layout (NOT centered single column)
- [ ] Header background is `var(--primary)` — NEVER white
- [ ] Grain overlay on hero and CTA band
- [ ] Hero entry animations (`heroFadeUp`) on all 6 child elements
- [ ] Frosted glass card on hero right
- [ ] Stats row with `data-target` counter animation
- [ ] Staggered fadeUp on service cards, review cards, why-choose-us items
- [ ] All 6 service cards have inline SVG icons (zero emojis anywhere)
- [ ] Review SVG quote marks (not `"` text)
- [ ] Sections alternate dark/light
- [ ] Fixed grids `repeat(3,1fr)` not `auto-fit`
- [ ] Responsive breakpoints at 900px and 600px
- [ ] No emoji characters anywhere in the file
- [ ] File ends with `</html>`
