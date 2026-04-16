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
    "squad": "revshift",
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

# Set idle at end:
# Same call but "status": "idle"
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

### Quality gate:
- `quality_score >= 2` preferred, but process all non-empty-website leads
- Track A leads (`track = A`) are highest priority — process these first

---

## Brand Analysis — How to Extract Colors

Fetch the business's website HTML and CSS. Extract brand colors using this priority order:

### Step 1 — Structural CSS extraction (most reliable)
Look for background-color declarations in these selectors (in priority order):
1. `header`, `.header`, `nav`, `.navbar`, `.nav` → this is almost always the primary brand color
2. `footer`, `.footer`
3. `.btn`, `button`, `.hero`, `.cta`
4. Body/section backgrounds

### Step 2 — Neon filter (reject bad colors)
Reject any color where saturation > 0.90 AND brightness > 0.85 — these are neon/default colors, not real brand colors.

### Step 3 — Accent selection
Accent = most-used color with color distance > 60 from primary (in RGB space).

### Step 4 — Fallback
If no structural colors found, use frequency counting across all CSS. Dark colors (luminance < 0.3) default to primary.

### Darken primary 15%
Always darken the extracted primary color ~15% for richer depth:
- `#1e3a5f` → `#0d2b4e`
- `#32373C` → `#1a1e21`
- `#2e7d32` → `#1b5e20`

### Font detection:
- Look for font-family declarations in body/h1/h2
- If serif → "traditional/trustworthy"
- If sans-serif → "modern/approachable"
- If no font found → default to clean sans-serif

---

## Mockup HTML Spec — All 10 Sections

Every mockup MUST include ALL 10 sections, in this order. Do not stop early. End with `</html>`.

Target file size: 55–70KB. If you are under 40KB you have truncated — start over.

### Section 1 — Sticky Header
- Background: darkened primary color (NOT white)
- Business name: bold, 20px, white
- Tagline: 13px, white at 70% opacity
- CTA button: accent color, "Call: [phone]"
- Box-shadow: `0 2px 12px rgba(0,0,0,0.3)`
- `position: sticky; top: 0; z-index: 1000`

### Section 2 — Hero (2-column asymmetric)
- Full-width background: dark gradient using primary color
- **Left column (60%):**
  - Badge: accent-colored pill, e.g. "⭐ #1 Rated in [City]" (use SVG star, not emoji)
  - Headline: 52px bold white, MAX 6 words, format: "[City]'s [Adjective] **[Keyword]**"
    - The keyword gets a `<span>` in accent color
  - Subheadline: 18px, rgba(255,255,255,0.8), 1–2 sentences specific to the business
  - Primary CTA button: accent color, bold, box-shadow
  - Secondary CTA: ghost button, white border + white text (NEVER accent color on dark bg)
  - Trust bar: star rating · review count · licensed/insured · key differentiator
- **Right column (40%):**
  - Frosted glass card:
    ```css
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.15);
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    backdrop-filter: blur(12px);
    border-radius: 16px;
    padding: 28px;
    ```
  - 4 value props with SVG checkmarks, white text
  - Bottom: phone number or "Get Free Quote" sub-CTA

### Stats Row (below hero, full-width dark)
4 stat boxes in a row:
- Dark card bg (slightly lighter than hero bg)
- Large number in accent color (white if accent doesn't contrast >3:1 on dark bg)
- Label in white at 70% opacity
- Border: 1px solid accent at 25% opacity
- Box-shadow

### Section 3 — Services Grid
- White background
- Section label (10px uppercase, accent color, letter-spacing)
- Title: 32px bold, dark navy/primary
- Subtitle: grey, max 2 lines
- 6 service cards in 3-column grid
- Each card:
  - White bg, border: 1px solid #e8edf5, border-radius: 12px
  - Box-shadow: `0 2px 12px rgba(0,0,0,0.06)`
  - Hover: `translateY(-4px)`, deeper shadow, accent top-border (3px)
  - Icon: SVG in accent-colored circle (no emojis — see SVG rules below)
  - Service name: 16px bold, dark
  - Description: 14px grey, 2–3 lines
  - "Learn More →" or "Get Quote →" in accent color

### Section 4 — Why Choose Us
- Dark section (primary color bg)
- Title: white, 32px
- Top row: 4 dark stat cards
  - Numbers in accent (white if contrast fails)
  - Labels in white at 70%
- Bottom: 4 differentiator items in 2-col grid
  - SVG checkmark circles in accent color
  - Bold white title + grey description

### Section 5 — How It Works
- Darkest section (#0a... very dark)
- Title: white, 32px
- 3 steps horizontal with connecting visual
- Each step: numbered circle (accent color fill), icon (SVG), bold white title, grey description

### Section 6 — Reviews
- Off-white background (#f8f9fc or similar)
- Title: dark, 32px. Google badge top-right: Google G SVG + "4.X stars · N reviews"
- 3 review cards:
  - White bg, border: 1px solid #e8edf5, border-radius: 12px, padding: 28px
  - Box-shadow: `0 2px 16px rgba(0,0,0,0.06)`
  - Hover: `0 8px 32px rgba(0,0,0,0.12)`, `translateY(-3px)`
  - SVG quote icon at top (accent color, 50% opacity) — NOT a text `"` character:
    ```html
    <svg width="32" height="24" viewBox="0 0 32 24" fill="currentColor">
      <path d="M0 24V14.4C0 6.56 4.64 1.6 13.92 0l1.44 2.24C10.56 3.52 8 6.56 8 11.2H13.6V24H0zm18.4 0V14.4C18.4 6.56 23.04 1.6 32.32 0l1.44 2.24c-4.8 1.28-7.36 4.32-7.36 8.96H32V24H18.4z"/>
    </svg>
    ```
  - Quote text: italic, 15px, line-height 1.7, dark color
  - Divider line before reviewer info
  - Avatar: colored circle with initials, name bold, location + "Google Review" in grey

### Section 7 — Service Areas
- Dark section (primary)
- 2-column:
  - Left: headline "Serving All of [Metro Area]", subtext, CTA button
  - Right: dark card with 10 neighborhood chips (hover turns accent color)

### Section 8 — Contact / Booking Form
- White background
- 2-column:
  - Left: form (name, phone, service type selector, optional message, accent submit button)
  - Right: dark card with hours/contact + "Why Book Online" checklist

### Section 9 — CTA Band
- Gradient using accent color (dark→light or left→right)
- Bold white headline (max 8 words)
- White subtext
- White button with dark text (or dark button with white text)

### Section 10 — Footer
- Very dark background
- 3–4 column grid: brand info, services list, service areas, contact
- All text: white/grey
- Bottom bar: copyright, license number if applicable

---

## CSS Rules — Apply to Every Mockup

```css
/* Always define these variables */
:root {
  --primary: [darkened extracted primary];
  --accent: [extracted accent];
  --bg: #ffffff;
  --dark: [primary or very dark variant];
  --t1: #ffffff;
  --t2: rgba(255,255,255,0.75);
  --t3: rgba(255,255,255,0.5);
}

/* Cards */
box-shadow: 0 4px 20px rgba(0,0,0,0.15);
/* Card hover */
box-shadow: 0 8px 32px rgba(0,0,0,0.25);
transform: translateY(-3px);
transition: all 0.3s ease;

/* Section padding */
padding: 80px 0;

/* Content max-width */
max-width: 1100px;
margin: 0 auto;
padding: 0 24px;
```

---

## Contrast Rules — Non-Negotiable

- **On dark/colored backgrounds:** body text = white. Secondary = rgba(255,255,255,0.75)
- **Light accent colors** (yellow, lime, light blue, pink — luminance > 0.4): when used as TEXT on white sections, MUST be darkened 40% minimum
- **Stat numbers on dark bg:** use accent color only if contrast ratio >3:1 vs background. Otherwise use white
- **Ghost buttons on colored hero:** border AND text must be white — NEVER use accent color for ghost button text on a similar-hue background
- **NEVER** use accent color as text on a background sharing similar hue (e.g. light orange text on orange bg)
- **Section backgrounds alternate:** dark → white → dark → white for visual rhythm

---

## SVG Icons — No Emojis Ever

Never use emoji characters in any mockup. Always use inline SVG icons.

### Core icon library (copy these exactly):

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

**Shield/badge:**
```html
<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
```

**Wrench:**
```html
<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
```

**Droplet/water:**
```html
<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>
```

**Zap/lightning:**
```html
<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
```

**Home:**
```html
<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
```

**Truck (junk removal):**
```html
<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>
```

**Leaf (yard/landscaping):**
```html
<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10z"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/></svg>
```

**Sofa/furniture:**
```html
<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 9V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v3"/><path d="M2 11a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-3z"/><path d="M4 16v2"/><path d="M20 16v2"/></svg>
```

**Google G (for review badges):**
```html
<svg width="20" height="20" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
```

For niche-specific services, create appropriate SVGs using the same stroke style. Never default to emoji.

---

## Copy Standards

### Headlines (52px hero):
- MAX 6 words total
- Format: "[City]'s [Adjective] **[Service Keyword]**"
- Examples:
  - "Houston's Trusted Pest Experts"
  - "Austin's Fastest Junk Removal"
  - "Tucson's Most Trusted Plumbers"
  - "San Antonio's Best HVAC Team"

### Subheadlines:
- 1–2 sentences max, 18px
- Reference the city AND a specific local landmark or neighborhood when possible
- Focus on the customer's outcome, not the company's features

### Review quotes (make these feel real and specific):
- Reference a specific service ("burst pipe", "rodent infestation", "junk cleanout")
- Include a time detail ("showed up in 45 minutes", "fixed it in 2 hours")
- Include a money/value detail ("fair price", "no surprise charges", "worth every penny")
- 3–5 sentences, first person, conversational

### Service descriptions:
- 2–3 lines
- Start with the customer's problem, end with the outcome
- Avoid generic phrasing like "we offer" or "our team provides"

---

## Niche-Specific Templates

### Pest Control
Services: Roach Control, Rodent Removal, Termite Treatment, Mosquito Control, Bed Bug Treatment, Ant Control
Key trust signals: "pet-safe treatments", "same-day service", "satisfaction guarantee"
Tone: reassuring, clean, professional

### Junk Removal
Services: Furniture Removal, Appliance Hauling, Estate Cleanouts, Construction Debris, Yard Waste, Same-Day Service
Key trust signals: "eco-friendly", "same-day available", "no hidden fees", "licensed & insured"
Tone: bold, efficient, no-nonsense

### Plumbing
Services: Drain Cleaning, Water Heater Repair, Pipe Repair, Leak Detection, Sewer Line Service, Emergency Plumbing
Key trust signals: "licensed & insured", "24/7 emergency", "no hidden fees", "upfront pricing"
Tone: trustworthy, professional, experienced

### HVAC
Services: AC Repair, Heating Repair, System Installation, Maintenance Plans, Emergency Service, Duct Cleaning
Key trust signals: "NATE certified", "same-day service", "10-year warranty", "financing available"
Tone: expert, reliable, local

### Roofing
Services: Roof Repair, Roof Replacement, Storm Damage, Gutters, Inspections, Emergency Tarping
Key trust signals: "licensed & bonded", "free inspection", "insurance claims", "local company"
Tone: serious, trustworthy, protector

---

## Git + Deploy Workflow

```bash
cd ~/rswebworks
git add [slug]/index.html
git commit -m "mockups: add [business-name] ([city])"
git push origin main
# Vercel auto-deploys — live at https://rswebworks.com/[slug]/
```

For batches, commit all at once:
```bash
git add -A
git commit -m "mockups: batch [N] — [date]"
git push origin main
```

---

## Quality Checklist (Before Marking Complete)

Before finalizing each mockup, verify:
- [ ] File size > 40KB (if under, sections are missing)
- [ ] Header background is dark (not white)
- [ ] Hero has 2-column layout (not centered single column)
- [ ] Frosted glass card present on hero right side
- [ ] Stats row present below hero
- [ ] All 6 services have SVG icons (no emojis)
- [ ] Reviews section has SVG quote marks (not `"` text)
- [ ] No light text on light backgrounds
- [ ] No emoji characters anywhere in the file
- [ ] File ends with `</html>`
