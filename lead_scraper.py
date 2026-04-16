#!/usr/bin/env python3
"""
RSWebWorks Lead Scraper
Finds local service businesses with bad/no websites via Google Places API.
Appends qualified leads to ~/rswebworks/leads.csv and notifies Rev via Cortex.
"""

import csv
import json
import os
import re
import time
import datetime
import requests
from bs4 import BeautifulSoup
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────────────

PLACES_API_KEY    = "AIzaSyBddx_Fgtg06wzUuSXnXTiG1ymHhDCF5PQ"
PLACES_API_BASE   = "https://places.googleapis.com/v1/places:searchText"
PLACES_FIELD_MASK = "places.id,places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.websiteUri,places.rating,places.userRatingCount,nextPageToken"
BASE_DIR       = Path.home() / "rswebworks"
LEADS_CSV      = BASE_DIR / "leads.csv"
STATE_FILE     = BASE_DIR / "scraper_state.json"
SUMMARY_FILE   = BASE_DIR / "last_run_summary.txt"
CORTEX_URL     = "http://localhost:3002/api/internal/agent-pulse"
CORTEX_TOKEN   = "cortex-internal-2026"

NICHES = [
    "pressure washing", "lawn care", "landscaping", "junk removal",
    "pest control", "plumber", "electrician", "HVAC", "roofing",
    "painting", "handyman", "cleaning service", "window cleaning",
    "gutter cleaning", "pool service", "tree service", "carpet cleaning",
    "concrete driveway", "fencing", "garage door",
]

CITIES = [
    # Texas
    "Houston TX", "San Antonio TX", "Dallas TX", "Austin TX", "Fort Worth TX",
    "El Paso TX", "Arlington TX", "Corpus Christi TX", "Plano TX", "Laredo TX",
    "Lubbock TX", "Garland TX", "Irving TX", "Amarillo TX", "Grand Prairie TX",
    "McKinney TX", "Frisco TX", "Killeen TX", "Pasadena TX", "Mesquite TX",
    # Florida
    "Jacksonville FL", "Miami FL", "Tampa FL", "Orlando FL", "St Petersburg FL",
    "Hialeah FL", "Tallahassee FL", "Fort Lauderdale FL", "Port St Lucie FL",
    "Cape Coral FL", "Pembroke Pines FL", "Hollywood FL", "Gainesville FL",
    "Miramar FL", "Coral Springs FL", "Clearwater FL", "Palm Bay FL", "Lakeland FL",
    # California
    "Los Angeles CA", "San Diego CA", "San Jose CA", "San Francisco CA",
    "Fresno CA", "Sacramento CA", "Long Beach CA", "Oakland CA", "Bakersfield CA",
    "Anaheim CA", "Santa Ana CA", "Riverside CA", "Stockton CA", "Chula Vista CA",
    "Irvine CA", "Fremont CA", "San Bernardino CA", "Modesto CA", "Fontana CA",
    # New York
    "New York NY", "Buffalo NY", "Rochester NY", "Yonkers NY", "Syracuse NY",
    "Albany NY", "New Rochelle NY", "Mount Vernon NY",
    # Pennsylvania
    "Philadelphia PA", "Pittsburgh PA", "Allentown PA", "Erie PA", "Reading PA",
    "Scranton PA", "Bethlehem PA", "Lancaster PA",
    # Illinois
    "Chicago IL", "Aurora IL", "Joliet IL", "Naperville IL", "Rockford IL",
    "Springfield IL", "Peoria IL", "Elgin IL",
    # Ohio
    "Columbus OH", "Cleveland OH", "Cincinnati OH", "Toledo OH", "Akron OH",
    "Dayton OH", "Parma OH", "Canton OH",
    # Georgia
    "Atlanta GA", "Augusta GA", "Columbus GA", "Macon GA", "Savannah GA",
    "Athens GA", "Sandy Springs GA", "Roswell GA",
    # North Carolina
    "Charlotte NC", "Raleigh NC", "Greensboro NC", "Durham NC", "Winston-Salem NC",
    "Fayetteville NC", "Cary NC", "Wilmington NC",
    # Michigan
    "Detroit MI", "Grand Rapids MI", "Warren MI", "Sterling Heights MI",
    "Lansing MI", "Ann Arbor MI", "Flint MI", "Dearborn MI",
    # Arizona
    "Phoenix AZ", "Tucson AZ", "Mesa AZ", "Chandler AZ", "Scottsdale AZ",
    "Glendale AZ", "Gilbert AZ", "Tempe AZ", "Peoria AZ", "Surprise AZ",
    # Tennessee
    "Nashville TN", "Memphis TN", "Knoxville TN", "Chattanooga TN",
    "Clarksville TN", "Murfreesboro TN",
    # Washington
    "Seattle WA", "Spokane WA", "Tacoma WA", "Vancouver WA", "Bellevue WA",
    "Kirkland WA", "Renton WA", "Redmond WA",
    # Colorado
    "Denver CO", "Colorado Springs CO", "Aurora CO", "Fort Collins CO",
    "Lakewood CO", "Thornton CO", "Arvada CO", "Pueblo CO",
    # Nevada
    "Las Vegas NV", "Henderson NV", "Reno NV", "North Las Vegas NV",
    # Indiana
    "Indianapolis IN", "Fort Wayne IN", "Evansville IN", "South Bend IN",
    "Carmel IN", "Fishers IN", "Bloomington IN",
    # Missouri
    "Kansas City MO", "St Louis MO", "Springfield MO", "Columbia MO",
    # Wisconsin
    "Milwaukee WI", "Madison WI", "Green Bay WI", "Kenosha WI", "Racine WI",
    # Minnesota
    "Minneapolis MN", "St Paul MN", "Rochester MN", "Duluth MN",
    # Maryland
    "Baltimore MD", "Frederick MD", "Rockville MD", "Gaithersburg MD",
    # Virginia
    "Virginia Beach VA", "Norfolk VA", "Chesapeake VA", "Richmond VA",
    "Newport News VA", "Alexandria VA", "Hampton VA", "Roanoke VA",
    # New Jersey
    "Newark NJ", "Jersey City NJ", "Paterson NJ", "Elizabeth NJ", "Trenton NJ",
    # South Carolina
    "Columbia SC", "Charleston SC", "North Charleston SC", "Greenville SC",
    # Alabama
    "Birmingham AL", "Montgomery AL", "Huntsville AL", "Mobile AL",
    # Louisiana
    "New Orleans LA", "Baton Rouge LA", "Shreveport LA", "Metairie LA",
    # Kentucky
    "Louisville KY", "Lexington KY", "Bowling Green KY",
    # Oregon
    "Portland OR", "Salem OR", "Eugene OR", "Gresham OR", "Hillsboro OR",
    # Oklahoma
    "Oklahoma City OK", "Tulsa OK", "Norman OK", "Broken Arrow OK",
    # Connecticut
    "Bridgeport CT", "New Haven CT", "Hartford CT", "Stamford CT",
    # Iowa
    "Des Moines IA", "Cedar Rapids IA", "Davenport IA",
    # Mississippi
    "Jackson MS", "Gulfport MS", "Southaven MS",
    # Arkansas
    "Little Rock AR", "Fort Smith AR", "Fayetteville AR",
    # Nebraska
    "Omaha NE", "Lincoln NE",
    # Kansas
    "Wichita KS", "Overland Park KS", "Kansas City KS",
    # New Mexico
    "Albuquerque NM", "Las Cruces NM", "Rio Rancho NM",
    # Utah
    "Salt Lake City UT", "West Valley City UT", "Provo UT", "West Jordan UT",
    # Idaho
    "Boise ID", "Nampa ID", "Meridian ID",
    # Montana
    "Billings MT", "Missoula MT", "Great Falls MT",
    # Wyoming
    "Cheyenne WY", "Casper WY",
    # North Dakota
    "Fargo ND", "Bismarck ND",
    # South Dakota
    "Sioux Falls SD", "Rapid City SD",
    # West Virginia
    "Charleston WV", "Huntington WV",
    # Maine
    "Portland ME", "Lewiston ME",
    # New Hampshire
    "Manchester NH", "Nashua NH",
    # Vermont
    "Burlington VT",
    # Rhode Island
    "Providence RI", "Cranston RI",
    # Delaware
    "Wilmington DE", "Dover DE",
    # Hawaii
    "Honolulu HI", "Pearl City HI",
    # Alaska
    "Anchorage AK", "Fairbanks AK",
]

NICHES_PER_RUN = 3
CITIES_PER_RUN = 5

SOCIAL_DOMAINS = {
    "facebook.com", "fb.com", "instagram.com", "yelp.com",
    "twitter.com", "linkedin.com", "tiktok.com", "linktree.ee",
    "linktr.ee", "squarespace.com", "wix.com",
}

CSV_FIELDS = [
    "place_id", "business_name", "first_name", "email", "phone",
    "address", "city", "state", "rating", "review_count", "website",
    "track", "flaw", "niche", "quality_score", "slug", "status", "date_found",
]

# ─── State ────────────────────────────────────────────────────────────────────

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"niche_offset": 0, "city_offset": 0}

def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def get_rotation(items: list, offset: int, count: int) -> tuple[list, int]:
    """Return `count` items starting at `offset`, wrap around. Returns (items, new_offset)."""
    n = len(items)
    selected = [items[(offset + i) % n] for i in range(count)]
    new_offset = (offset + count) % n
    return selected, new_offset

# ─── CSV ──────────────────────────────────────────────────────────────────────

def load_existing_place_ids() -> set:
    ids = set()
    if LEADS_CSV.exists():
        with open(LEADS_CSV, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row.get("place_id", "").strip()
                if pid:
                    ids.add(pid)
    return ids

def append_leads(leads: list[dict]):
    write_header = not LEADS_CSV.exists()
    with open(LEADS_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if write_header:
            writer.writeheader()
        for lead in leads:
            writer.writerow({k: lead.get(k, "") for k in CSV_FIELDS})

# ─── Google Places (New API v1) ───────────────────────────────────────────────

def places_text_search(query: str) -> list[dict]:
    """
    Uses Places API (New) — POST /v1/places:searchText.
    Returns normalized dicts with keys: place_id, name, phone, website,
    address, rating, review_count.
    Pulls up to 60 results across 3 pages.
    """
    results = []
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": PLACES_API_KEY,
        "X-Goog-FieldMask": PLACES_FIELD_MASK,
    }
    body: dict = {"textQuery": query, "maxResultCount": 20}

    for _page in range(3):
        try:
            resp = requests.post(PLACES_API_BASE, headers=headers, json=body, timeout=10)
            data = resp.json()
        except Exception as e:
            print(f"  [places] search error: {e}")
            break

        for p in data.get("places", []):
            results.append({
                "place_id":     p.get("id", ""),
                "name":         p.get("displayName", {}).get("text", ""),
                "phone":        p.get("nationalPhoneNumber", ""),
                "website":      p.get("websiteUri", ""),
                "address":      p.get("formattedAddress", ""),
                "rating":       p.get("rating", 0) or 0,
                "review_count": p.get("userRatingCount", 0) or 0,
            })

        token = data.get("nextPageToken")
        if not token:
            break
        time.sleep(1)
        body = {"textQuery": query, "maxResultCount": 20, "pageToken": token}

    return results

# ─── Website qualification ────────────────────────────────────────────────────

def is_social_url(url: str) -> bool:
    """Return True if the URL is a social/directory site, not a real business site."""
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower().lstrip("www.")
        return any(s in domain for s in SOCIAL_DOMAINS)
    except Exception:
        return True

def fetch_site(url: str) -> str | None:
    """Fetch page HTML. Returns None on error."""
    if not url.startswith("http"):
        url = "https://" + url
    headers = {"User-Agent": "Mozilla/5.0 (compatible; RSWebWorks/1.0)"}
    try:
        resp = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
        if resp.status_code >= 400:
            return None
        return resp.text
    except Exception:
        return None

def detect_flaws(url: str, html: str) -> list[str]:
    """Return list of detected flaws. Empty = site passes / is good."""
    flaws = []

    # 1. No SSL
    if url.startswith("http://"):
        flaws.append("no_ssl")

    soup = BeautifulSoup(html, "html.parser")

    # 2. No mobile viewport
    viewport = soup.find("meta", attrs={"name": re.compile(r"viewport", re.I)})
    if not viewport:
        flaws.append("no_viewport")

    # 3. Copyright year < 2020
    text = soup.get_text(" ", strip=True)
    year_matches = re.findall(r"(?:copyright|©|&copy;)\s*(?:\d{4}\s*[-–]\s*)?(\d{4})", text, re.I)
    for yr in year_matches:
        try:
            if int(yr) < 2020:
                flaws.append("outdated_copyright")
                break
        except ValueError:
            pass

    # 4. No click-to-call (tel: link)
    tel_links = soup.find_all("a", href=re.compile(r"^tel:", re.I))
    if not tel_links:
        flaws.append("no_click_to_call")

    return flaws

PLACEHOLDER_EMAILS = {
    "filler@godaddy.com", "info@mydomain.com", "info@example.com",
    "email@example.com", "yourname@yourdomain.com", "noreply@squarespace.com",
    "webmaster@domain.com",
}
PLACEHOLDER_EMAIL_PATTERNS = re.compile(
    r"^(filler|placeholder|noreply|webmaster|admin@(godaddy|example|mydomain|yourdomain|domain)|www@)",
    re.I
)

def clean_email(raw: str) -> str:
    """URL-decode and strip junk from a mailto: href value."""
    from urllib.parse import unquote
    email = unquote(raw.replace("mailto:", "").strip().split("?")[0]).strip()
    # Strip leading garbage (spaces, %20, punctuation)
    email = re.sub(r"^[^a-zA-Z0-9]+", "", email)
    return email.lower()

def is_placeholder_email(email: str) -> bool:
    if not email or "@" not in email:
        return True
    if email in PLACEHOLDER_EMAILS:
        return True
    local = email.split("@")[0]
    # www@anydomain.com style
    if local == "www":
        return True
    if PLACEHOLDER_EMAIL_PATTERNS.search(email):
        return True
    return False

def scrape_email(html: str) -> str:
    """Find first real email address in HTML."""
    soup = BeautifulSoup(html, "html.parser")
    # mailto: links first (most reliable)
    for a in soup.find_all("a", href=re.compile(r"^mailto:", re.I)):
        email = clean_email(a["href"])
        if "@" in email and "." in email and not is_placeholder_email(email):
            return email
    # Plain text regex fallback
    text = soup.get_text(" ")
    matches = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
    for m in matches:
        email = m.lower()
        if not is_placeholder_email(email):
            return email
    return ""

# ─── Slug ─────────────────────────────────────────────────────────────────────

def make_slug(business_name: str, city_name: str, state: str) -> str:
    """Unique slug: 'business-name-city-state', e.g. 'cw-powerwashing-fort-worth-tx'"""
    raw = f"{business_name} {city_name} {state}"
    slug = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")
    return slug[:60]

# ─── Parse city/state from full city string ───────────────────────────────────

def parse_city_state(city_str: str) -> tuple[str, str]:
    """'Fort Worth TX' → ('Fort Worth', 'TX')"""
    parts = city_str.rsplit(" ", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return city_str, ""

# ─── Notify Cortex ────────────────────────────────────────────────────────────

def notify_cortex():
    try:
        resp = requests.post(
            CORTEX_URL,
            headers={
                "x-internal-token": CORTEX_TOKEN,
                "Content-Type": "application/json",
            },
            json={"sessionKey": "agent:main:main", "activity": "idle"},
            timeout=5,
        )
        print(f"  [cortex] notified: {resp.status_code}")
    except Exception as e:
        print(f"  [cortex] notify failed: {e}")

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    today = datetime.date.today().isoformat()
    print(f"\n{'='*60}")
    print(f"RSWebWorks Lead Scraper — {today}")
    print(f"{'='*60}")

    BASE_DIR.mkdir(parents=True, exist_ok=True)

    state = load_state()
    existing_ids = load_existing_place_ids()
    print(f"Existing leads in CSV: {len(existing_ids)}")

    # Pick rotation
    niches_this_run, new_niche_offset = get_rotation(NICHES, state["niche_offset"], NICHES_PER_RUN)
    cities_this_run, new_city_offset  = get_rotation(CITIES, state["city_offset"],  CITIES_PER_RUN)
    print(f"Niches: {niches_this_run}")
    print(f"Cities: {cities_this_run}")

    new_leads: list[dict] = []
    scanned = 0

    for niche in niches_this_run:
        for city in cities_this_run:
            city_name, city_state = parse_city_state(city)
            query = f"{niche} near {city}"
            print(f"\n  → {query}")

            results = places_text_search(query)
            print(f"     {len(results)} results from Places API")

            for r in results:
                place_id = r.get("place_id", "")
                if not place_id or place_id in existing_ids:
                    continue

                scanned += 1
                name     = r.get("name", "").strip()
                phone    = r.get("phone", "").strip()
                website  = r.get("website", "").strip()
                address  = r.get("address", "").strip()
                rating   = r.get("rating", 0) or 0
                reviews  = r.get("review_count", 0) or 0

                time.sleep(0.5)  # rate limit between website fetches

                # ── Track B: No website ──
                if not website:
                    if rating >= 4.0 and reviews >= 10 and phone:
                        lead = {
                            "place_id":     place_id,
                            "business_name": name,
                            "first_name":   "Owner",
                            "email":        "",
                            "phone":        phone,
                            "address":      address,
                            "city":         city_name,
                            "state":        city_state,
                            "rating":       rating,
                            "review_count": reviews,
                            "website":      "none",
                            "track":        "B",
                            "flaw":         "no website",
                            "niche":        niche,
                            "quality_score": 1,
                            "slug":         make_slug(name, city_name, city_state),
                            "status":       "",
                            "date_found":   today,
                        }
                        new_leads.append(lead)
                        existing_ids.add(place_id)
                        print(f"     ✓ Track B: {name} ({city_name}) — {reviews} reviews")
                    continue

                # ── Track A: Has website — check if it's social ──
                if is_social_url(website):
                    continue

                # Fetch site
                time.sleep(1)
                html = fetch_site(website)
                if html is None:
                    continue

                flaws = detect_flaws(website, html)
                if not flaws:
                    continue  # Site is fine — skip

                email = scrape_email(html)
                # Don't skip if no email — mockup can still be generated and Instantly
                # will attempt push; leads without email just won't get outreach email

                # Quality score: more/worse flaws = lower score (1 = worst/most broken)
                flaw_score = min(len(flaws), 4)
                quality_score = max(1, 5 - flaw_score)

                lead = {
                    "place_id":      place_id,
                    "business_name": name,
                    "first_name":    "Owner",
                    "email":         email,
                    "phone":         phone,
                    "address":       address,
                    "city":          city_name,
                    "state":         city_state,
                    "rating":        rating,
                    "review_count":  reviews,
                    "website":       website,
                    "track":         "A",
                    "flaw":          ", ".join(flaws),
                    "niche":         niche,
                    "quality_score": quality_score,
                    "slug":          make_slug(name, city_name, city_state),
                    "status":        "",
                    "date_found":    today,
                }
                new_leads.append(lead)
                existing_ids.add(place_id)
                print(f"     ✓ Track A: {name} ({city_name}) — flaws: {flaws} — {email}")

    # ── Sort: Track B first, then Track A by quality_score asc ──
    new_leads.sort(key=lambda l: (0 if l["track"] == "B" else 1, l["quality_score"]))

    # ── Append to CSV ──
    if new_leads:
        append_leads(new_leads)
        print(f"\nAppended {len(new_leads)} new leads to {LEADS_CSV}")
    else:
        print("\nNo new leads this run.")

    # ── Counts ──
    track_a = [l for l in new_leads if l["track"] == "A"]
    track_b = [l for l in new_leads if l["track"] == "B"]
    emails_found = sum(1 for l in new_leads if l.get("email"))

    # ── Summary file ──
    top5 = new_leads[:5]
    top5_lines = "\n".join(
        f"  {l['business_name']} | {l['city']}, {l['state']} | Track {l['track']} | {l['flaw']} | {l.get('email') or 'no email'}"
        for l in top5
    ) or "  (none)"

    summary = f"""RSWebWorks Scraper Run — {today}
Niches:    {', '.join(niches_this_run)}
Cities:    {', '.join(cities_this_run)}
Scanned:   {scanned} businesses
New leads: {len(new_leads)} (Track A: {len(track_a)}, Track B: {len(track_b)})
Emails:    {emails_found}

Top {len(top5)} leads:
{top5_lines}
"""
    SUMMARY_FILE.write_text(summary)
    print(f"\n{summary}")

    # ── Save state ──
    state["niche_offset"] = new_niche_offset
    state["city_offset"]  = new_city_offset
    save_state(state)

    # ── Notify Cortex / Rev ──
    print("Notifying Cortex...")
    notify_cortex()

    print("Done.\n")

if __name__ == "__main__":
    main()
