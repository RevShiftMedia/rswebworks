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

# ─── Search queries ────────────────────────────────────────────────────────────
# Each entry is (canonical_niche, query_string).
# Multiple query variants per niche surface different businesses from Google —
# "plumber" and "plumbing company" return meaningfully different result sets.

SEARCHES = [
    # Pressure washing
    ("pressure washing", "pressure washing"),
    ("pressure washing", "power washing"),
    ("pressure washing", "soft wash service"),
    # Lawn care
    ("lawn care", "lawn care"),
    ("lawn care", "lawn mowing service"),
    ("lawn care", "grass cutting service"),
    # Landscaping
    ("landscaping", "landscaping company"),
    ("landscaping", "landscaper"),
    ("landscaping", "landscape contractor"),
    # Junk removal
    ("junk removal", "junk removal"),
    ("junk removal", "junk hauling"),
    ("junk removal", "debris removal"),
    # Pest control
    ("pest control", "pest control"),
    ("pest control", "exterminator"),
    ("pest control", "bug exterminator"),
    # Plumbing
    ("plumber", "plumber"),
    ("plumber", "plumbing company"),
    ("plumber", "plumbing service"),
    # Electrician
    ("electrician", "electrician"),
    ("electrician", "electrical contractor"),
    ("electrician", "electrical company"),
    # HVAC
    ("HVAC", "HVAC"),
    ("HVAC", "AC repair"),
    ("HVAC", "air conditioning repair"),
    ("HVAC", "heating and cooling"),
    # Roofing
    ("roofing", "roofing"),
    ("roofing", "roofer"),
    ("roofing", "roof repair"),
    ("roofing", "roof replacement"),
    # Painting
    ("painting", "house painter"),
    ("painting", "painting contractor"),
    ("painting", "interior painting"),
    ("painting", "exterior painting"),
    # Handyman
    ("handyman", "handyman"),
    ("handyman", "handyman service"),
    # Cleaning service
    ("cleaning service", "house cleaning"),
    ("cleaning service", "maid service"),
    ("cleaning service", "home cleaning service"),
    # Window cleaning
    ("window cleaning", "window cleaning"),
    ("window cleaning", "window washing"),
    # Gutter cleaning
    ("gutter cleaning", "gutter cleaning"),
    ("gutter cleaning", "gutter guard installation"),
    ("gutter cleaning", "gutter service"),
    # Pool service
    ("pool service", "pool service"),
    ("pool service", "pool cleaning"),
    ("pool service", "pool repair"),
    # Tree service
    ("tree service", "tree service"),
    ("tree service", "tree trimming"),
    ("tree service", "tree removal"),
    # Carpet cleaning
    ("carpet cleaning", "carpet cleaning"),
    ("carpet cleaning", "carpet cleaner"),
    ("carpet cleaning", "rug cleaning"),
    # Concrete
    ("concrete contractor", "concrete contractor"),
    ("concrete contractor", "concrete driveway"),
    ("concrete contractor", "concrete paving"),
    # Fencing
    ("fencing", "fence contractor"),
    ("fencing", "fencing company"),
    ("fencing", "fence installation"),
    # Garage door
    ("garage door", "garage door repair"),
    ("garage door", "garage door company"),
    ("garage door", "garage door installation"),
    # ── NEW NICHES ───────────────────────────────────────────────────────────
    # Water heater
    ("water heater", "water heater repair"),
    ("water heater", "water heater replacement"),
    ("water heater", "water heater installation"),
    # Drain cleaning
    ("drain cleaning", "drain cleaning"),
    ("drain cleaning", "clogged drain"),
    ("drain cleaning", "drain unclogging"),
    # Foundation repair
    ("foundation repair", "foundation repair"),
    ("foundation repair", "foundation contractor"),
    ("foundation repair", "basement waterproofing"),
    # Septic service
    ("septic service", "septic service"),
    ("septic service", "septic tank pumping"),
    ("septic service", "septic tank cleaning"),
    # Deck contractor
    ("deck contractor", "deck contractor"),
    ("deck contractor", "deck builder"),
    ("deck contractor", "deck installation"),
    # Chimney
    ("chimney sweep", "chimney sweep"),
    ("chimney sweep", "chimney cleaning"),
    ("chimney sweep", "chimney repair"),
    # Appliance repair
    ("appliance repair", "appliance repair"),
    ("appliance repair", "refrigerator repair"),
    ("appliance repair", "washer dryer repair"),
    # Flooring
    ("flooring contractor", "flooring contractor"),
    ("flooring contractor", "floor installation"),
    ("flooring contractor", "hardwood floor installation"),
    # Tile
    ("tile contractor", "tile contractor"),
    ("tile contractor", "tile installation"),
    ("tile contractor", "tile setter"),
    # Drywall
    ("drywall contractor", "drywall contractor"),
    ("drywall contractor", "drywall repair"),
    ("drywall contractor", "drywall installation"),
    # Locksmith
    ("locksmith", "locksmith"),
    ("locksmith", "locksmith service"),
    # Auto detailing
    ("auto detailing", "auto detailing"),
    ("auto detailing", "mobile auto detailing"),
    ("auto detailing", "car detailing"),
    # Sprinkler / irrigation
    ("sprinkler repair", "sprinkler repair"),
    ("sprinkler repair", "irrigation repair"),
    ("sprinkler repair", "irrigation system installation"),
    # Moving
    ("moving company", "moving company"),
    ("moving company", "local movers"),
    ("moving company", "residential movers"),
    # Remodeling
    ("remodeling contractor", "remodeling contractor"),
    ("remodeling contractor", "home remodeling"),
    ("remodeling contractor", "kitchen remodeling"),
    # Masonry
    ("masonry", "masonry contractor"),
    ("masonry", "brick repair"),
    ("masonry", "stone mason"),
    # Insulation
    ("insulation contractor", "insulation contractor"),
    ("insulation contractor", "insulation installation"),
    # Solar
    ("solar installer", "solar installer"),
    ("solar installer", "solar panel installation"),
    # Siding
    ("siding contractor", "siding contractor"),
    ("siding contractor", "siding installation"),
    ("siding contractor", "vinyl siding"),
    # Plumbing drain (separate from main plumber)
    ("sewer line", "sewer line repair"),
    ("sewer line", "sewer cleaning"),
    # HVAC duct
    ("duct cleaning", "duct cleaning"),
    ("duct cleaning", "air duct cleaning"),
]

# ─── Cities ───────────────────────────────────────────────────────────────────
# Expanded with suburbs/metros for top cities — each suburb is its own query
# which breaks Google's 20-result ceiling per city query.

CITIES = [
    # ── Texas ──────────────────────────────────────────────────────────────
    "Houston TX", "San Antonio TX", "Dallas TX", "Austin TX", "Fort Worth TX",
    "El Paso TX", "Arlington TX", "Corpus Christi TX", "Plano TX", "Laredo TX",
    "Lubbock TX", "Garland TX", "Irving TX", "Amarillo TX", "Grand Prairie TX",
    "McKinney TX", "Frisco TX", "Killeen TX", "Pasadena TX", "Mesquite TX",
    "Carrollton TX", "Lewisville TX", "Denton TX", "Allen TX", "Richardson TX",
    "Grapevine TX", "Euless TX", "Bedford TX", "Hurst TX", "Mansfield TX",
    "Rowlett TX", "Cedar Hill TX", "Flower Mound TX", "Wylie TX", "Burleson TX",
    # Houston suburbs
    "Katy TX", "Sugar Land TX", "Pearland TX", "Baytown TX", "League City TX",
    "Friendswood TX", "Missouri City TX", "Stafford TX", "Humble TX", "Conroe TX",
    "Spring TX", "Cypress TX", "Tomball TX", "The Woodlands TX",
    # San Antonio suburbs
    "New Braunfels TX", "Seguin TX", "Cibolo TX", "Schertz TX", "San Marcos TX",
    "Kyle TX", "Buda TX", "Boerne TX",
    # Austin suburbs
    "Round Rock TX", "Cedar Park TX", "Georgetown TX", "Pflugerville TX",
    "Leander TX", "Hutto TX", "Bastrop TX",
    # ── Florida ────────────────────────────────────────────────────────────
    "Jacksonville FL", "Miami FL", "Tampa FL", "Orlando FL", "St Petersburg FL",
    "Hialeah FL", "Tallahassee FL", "Fort Lauderdale FL", "Port St Lucie FL",
    "Cape Coral FL", "Pembroke Pines FL", "Hollywood FL", "Gainesville FL",
    "Miramar FL", "Coral Springs FL", "Clearwater FL", "Palm Bay FL", "Lakeland FL",
    # Miami suburbs
    "Doral FL", "Homestead FL", "North Miami FL", "Aventura FL", "Boca Raton FL",
    "Delray Beach FL", "Boynton Beach FL", "West Palm Beach FL", "Pompano Beach FL",
    "Davie FL", "Plantation FL", "Sunrise FL", "Tamarac FL", "Wellington FL",
    "Coconut Creek FL", "Margate FL",
    # Tampa suburbs
    "Brandon FL", "Riverview FL", "Largo FL", "Dunedin FL", "Palm Harbor FL",
    "New Port Richey FL", "Wesley Chapel FL", "Land O Lakes FL", "Lutz FL",
    "Sarasota FL", "Bradenton FL", "Spring Hill FL",
    # Orlando suburbs
    "Kissimmee FL", "Sanford FL", "Apopka FL", "Oviedo FL", "Winter Park FL",
    "Altamonte Springs FL", "Casselberry FL", "Lake Mary FL",
    # Jacksonville suburbs
    "St Augustine FL", "Orange Park FL", "Fleming Island FL", "Ponte Vedra FL",
    # ── California ─────────────────────────────────────────────────────────
    "Los Angeles CA", "San Diego CA", "San Jose CA", "San Francisco CA",
    "Fresno CA", "Sacramento CA", "Long Beach CA", "Oakland CA", "Bakersfield CA",
    "Anaheim CA", "Santa Ana CA", "Riverside CA", "Stockton CA", "Chula Vista CA",
    "Irvine CA", "Fremont CA", "San Bernardino CA", "Modesto CA", "Fontana CA",
    # LA suburbs
    "Pasadena CA", "Torrance CA", "Carson CA", "Downey CA", "Compton CA",
    "Inglewood CA", "El Monte CA", "Burbank CA", "Glendale CA", "Santa Clarita CA",
    "Thousand Oaks CA", "Oxnard CA", "Simi Valley CA", "Pomona CA", "Ontario CA",
    "Rancho Cucamonga CA", "Victorville CA", "Murrieta CA", "Temecula CA",
    "Lancaster CA", "Palmdale CA", "El Cajon CA",
    # San Diego suburbs
    "Santee CA", "La Mesa CA", "National City CA", "Escondido CA",
    "Vista CA", "Carlsbad CA", "Oceanside CA", "Encinitas CA",
    # Bay Area
    "Sunnyvale CA", "Santa Clara CA", "Mountain View CA", "Palo Alto CA",
    "Milpitas CA", "Santa Rosa CA", "Vallejo CA", "Concord CA", "Antioch CA",
    "Richmond CA", "Berkeley CA", "Hayward CA", "San Mateo CA", "Daly City CA",
    "Pleasanton CA", "Livermore CA",
    # Sacramento suburbs
    "Elk Grove CA", "Roseville CA", "Folsom CA", "Citrus Heights CA",
    # ── New York ────────────────────────────────────────────────────────────
    "New York NY", "Buffalo NY", "Rochester NY", "Yonkers NY", "Syracuse NY",
    "Albany NY", "New Rochelle NY", "Mount Vernon NY",
    "Brooklyn NY", "Queens NY", "Bronx NY", "Staten Island NY",
    # NY suburbs / Long Island
    "Hempstead NY", "Freeport NY", "Levittown NY", "Brentwood NY",
    "Babylon NY", "Huntington NY", "Islip NY",
    # ── New Jersey ──────────────────────────────────────────────────────────
    "Newark NJ", "Jersey City NJ", "Paterson NJ", "Elizabeth NJ", "Trenton NJ",
    "Edison NJ", "Woodbridge NJ", "Toms River NJ", "Lakewood NJ", "Brick NJ",
    "Old Bridge NJ", "Cherry Hill NJ", "Vineland NJ", "Union City NJ", "Clifton NJ",
    "Passaic NJ", "Bayonne NJ", "East Orange NJ", "Irvington NJ",
    # ── Pennsylvania ────────────────────────────────────────────────────────
    "Philadelphia PA", "Pittsburgh PA", "Allentown PA", "Erie PA", "Reading PA",
    "Scranton PA", "Bethlehem PA", "Lancaster PA",
    # Philly suburbs
    "Levittown PA", "Bensalem PA", "Upper Darby PA", "Chester PA",
    # ── Illinois ────────────────────────────────────────────────────────────
    "Chicago IL", "Aurora IL", "Joliet IL", "Naperville IL", "Rockford IL",
    "Springfield IL", "Peoria IL", "Elgin IL",
    # Chicago suburbs
    "Schaumburg IL", "Bolingbrook IL", "Orland Park IL", "Tinley Park IL",
    "Cicero IL", "Berwyn IL", "Evanston IL", "Waukegan IL", "Palatine IL",
    "Hoffman Estates IL", "Des Plaines IL", "Skokie IL", "Mount Prospect IL",
    "Arlington Heights IL", "Downers Grove IL", "Oak Lawn IL", "Oak Park IL",
    "Lombard IL", "Wheaton IL", "Calumet City IL",
    # ── Ohio ────────────────────────────────────────────────────────────────
    "Columbus OH", "Cleveland OH", "Cincinnati OH", "Toledo OH", "Akron OH",
    "Dayton OH", "Parma OH", "Canton OH",
    # Columbus suburbs
    "Dublin OH", "Westerville OH", "Grove City OH", "Gahanna OH", "Hilliard OH",
    # Cleveland suburbs
    "Euclid OH", "Lakewood OH", "Strongsville OH", "Mentor OH", "Lorain OH",
    # Cincinnati suburbs
    "Kettering OH", "Hamilton OH", "Middletown OH", "Fairfield OH",
    # ── Georgia ─────────────────────────────────────────────────────────────
    "Atlanta GA", "Augusta GA", "Columbus GA", "Macon GA", "Savannah GA",
    "Athens GA", "Sandy Springs GA", "Roswell GA",
    # Atlanta suburbs
    "Marietta GA", "Smyrna GA", "Decatur GA", "Kennesaw GA", "Canton GA",
    "Alpharetta GA", "Duluth GA", "Lawrenceville GA", "Norcross GA",
    "Peachtree City GA", "Fayetteville GA", "McDonough GA", "Woodstock GA",
    "Johns Creek GA", "Cumming GA", "Buford GA",
    # ── North Carolina ──────────────────────────────────────────────────────
    "Charlotte NC", "Raleigh NC", "Greensboro NC", "Durham NC", "Winston-Salem NC",
    "Fayetteville NC", "Cary NC", "Wilmington NC",
    # Charlotte suburbs
    "Concord NC", "Gastonia NC", "Matthews NC", "Huntersville NC",
    "Kannapolis NC", "Monroe NC", "Mooresville NC",
    # Raleigh suburbs
    "Apex NC", "Holly Springs NC", "Wake Forest NC", "Garner NC", "Clayton NC",
    # ── Michigan ────────────────────────────────────────────────────────────
    "Detroit MI", "Grand Rapids MI", "Warren MI", "Sterling Heights MI",
    "Lansing MI", "Ann Arbor MI", "Flint MI", "Dearborn MI",
    # Detroit suburbs
    "Clinton Township MI", "Livonia MI", "Westland MI", "Southfield MI",
    "Pontiac MI", "Rochester Hills MI", "Troy MI", "Farmington Hills MI",
    # ── Arizona ─────────────────────────────────────────────────────────────
    "Phoenix AZ", "Tucson AZ", "Mesa AZ", "Chandler AZ", "Scottsdale AZ",
    "Glendale AZ", "Gilbert AZ", "Tempe AZ", "Peoria AZ", "Surprise AZ",
    # Phoenix suburbs
    "Goodyear AZ", "Avondale AZ", "Buckeye AZ", "Queen Creek AZ", "Maricopa AZ",
    "Apache Junction AZ", "Fountain Hills AZ", "Sun City AZ", "El Mirage AZ",
    "Cave Creek AZ", "Litchfield Park AZ",
    # ── Tennessee ───────────────────────────────────────────────────────────
    "Nashville TN", "Memphis TN", "Knoxville TN", "Chattanooga TN",
    "Clarksville TN", "Murfreesboro TN",
    # Nashville suburbs
    "Franklin TN", "Brentwood TN", "Hendersonville TN", "Spring Hill TN",
    "Smyrna TN", "Nolensville TN",
    # ── Washington ──────────────────────────────────────────────────────────
    "Seattle WA", "Spokane WA", "Tacoma WA", "Vancouver WA", "Bellevue WA",
    "Kirkland WA", "Renton WA", "Redmond WA",
    # Seattle suburbs
    "Federal Way WA", "Kent WA", "Auburn WA", "Shoreline WA", "Bothell WA",
    "Sammamish WA", "Issaquah WA", "Burien WA", "Edmonds WA", "Lynnwood WA",
    "Everett WA", "Marysville WA",
    # ── Colorado ────────────────────────────────────────────────────────────
    "Denver CO", "Colorado Springs CO", "Aurora CO", "Fort Collins CO",
    "Lakewood CO", "Thornton CO", "Arvada CO", "Pueblo CO",
    # Denver suburbs
    "Westminster CO", "Centennial CO", "Englewood CO", "Highlands Ranch CO",
    "Broomfield CO", "Commerce City CO", "Parker CO", "Longmont CO",
    "Brighton CO", "Greeley CO", "Loveland CO", "Castle Rock CO",
    # ── Nevada ──────────────────────────────────────────────────────────────
    "Las Vegas NV", "Henderson NV", "Reno NV", "North Las Vegas NV",
    # Las Vegas metro
    "Summerlin NV", "Spring Valley NV", "Enterprise NV", "Paradise NV",
    "Sunrise Manor NV", "Whitney NV",
    # ── Indiana ─────────────────────────────────────────────────────────────
    "Indianapolis IN", "Fort Wayne IN", "Evansville IN", "South Bend IN",
    "Carmel IN", "Fishers IN", "Bloomington IN",
    # Indy suburbs
    "Noblesville IN", "Greenwood IN", "Anderson IN", "Lawrence IN",
    # ── Missouri ────────────────────────────────────────────────────────────
    "Kansas City MO", "St Louis MO", "Springfield MO", "Columbia MO",
    # KC suburbs
    "Lee's Summit MO", "Independence MO", "Blue Springs MO", "Overland Park KS",
    "Olathe KS", "Shawnee KS", "Lenexa KS",
    # STL suburbs
    "St Charles MO", "Florissant MO", "O Fallon MO", "Belleville IL",
    # ── Wisconsin ───────────────────────────────────────────────────────────
    "Milwaukee WI", "Madison WI", "Green Bay WI", "Kenosha WI", "Racine WI",
    # Milwaukee suburbs
    "Waukesha WI", "Wauwatosa WI", "West Allis WI", "Brookfield WI",
    # ── Minnesota ───────────────────────────────────────────────────────────
    "Minneapolis MN", "St Paul MN", "Rochester MN", "Duluth MN",
    # Twin Cities suburbs
    "Bloomington MN", "Brooklyn Park MN", "Plymouth MN", "Coon Rapids MN",
    "Burnsville MN", "Eagan MN", "Eden Prairie MN", "Minnetonka MN",
    "Maple Grove MN", "Woodbury MN",
    # ── Maryland / DC Metro ─────────────────────────────────────────────────
    "Baltimore MD", "Frederick MD", "Rockville MD", "Gaithersburg MD",
    "Bowie MD", "Silver Spring MD", "Columbia MD", "Annapolis MD",
    "Towson MD", "Glen Burnie MD",
    # ── Virginia ────────────────────────────────────────────────────────────
    "Virginia Beach VA", "Norfolk VA", "Chesapeake VA", "Richmond VA",
    "Newport News VA", "Alexandria VA", "Hampton VA", "Roanoke VA",
    # DC/NoVA suburbs
    "Fairfax VA", "Herndon VA", "Reston VA", "Manassas VA", "Woodbridge VA",
    "Centreville VA", "Burke VA", "Springfield VA", "Chantilly VA",
    "Sterling VA", "Leesburg VA", "Ashburn VA",
    # ── South Carolina ──────────────────────────────────────────────────────
    "Columbia SC", "Charleston SC", "North Charleston SC", "Greenville SC",
    "Rock Hill SC", "Summerville SC", "Goose Creek SC", "Mount Pleasant SC",
    # ── Alabama ─────────────────────────────────────────────────────────────
    "Birmingham AL", "Montgomery AL", "Huntsville AL", "Mobile AL",
    "Tuscaloosa AL", "Hoover AL", "Decatur AL",
    # ── Louisiana ───────────────────────────────────────────────────────────
    "New Orleans LA", "Baton Rouge LA", "Shreveport LA", "Metairie LA",
    "Kenner LA", "Bossier City LA", "Lafayette LA",
    # ── Kentucky ────────────────────────────────────────────────────────────
    "Louisville KY", "Lexington KY", "Bowling Green KY",
    "Owensboro KY", "Covington KY",
    # ── Oregon ──────────────────────────────────────────────────────────────
    "Portland OR", "Salem OR", "Eugene OR", "Gresham OR", "Hillsboro OR",
    "Beaverton OR", "Medford OR", "Springfield OR",
    # Portland suburbs
    "Tigard OR", "Lake Oswego OR", "Tualatin OR",
    # ── Oklahoma ────────────────────────────────────────────────────────────
    "Oklahoma City OK", "Tulsa OK", "Norman OK", "Broken Arrow OK",
    "Edmond OK", "Lawton OK", "Moore OK", "Midwest City OK",
    # ── Connecticut ─────────────────────────────────────────────────────────
    "Bridgeport CT", "New Haven CT", "Hartford CT", "Stamford CT",
    "Waterbury CT", "Norwalk CT", "Danbury CT",
    # ── Iowa ────────────────────────────────────────────────────────────────
    "Des Moines IA", "Cedar Rapids IA", "Davenport IA",
    "Sioux City IA", "Iowa City IA", "Ames IA",
    # ── Mississippi ─────────────────────────────────────────────────────────
    "Jackson MS", "Gulfport MS", "Southaven MS", "Biloxi MS", "Hattiesburg MS",
    # ── Arkansas ────────────────────────────────────────────────────────────
    "Little Rock AR", "Fort Smith AR", "Fayetteville AR",
    "Springdale AR", "Jonesboro AR", "Conway AR",
    # ── Nebraska ────────────────────────────────────────────────────────────
    "Omaha NE", "Lincoln NE", "Bellevue NE",
    # ── Kansas ──────────────────────────────────────────────────────────────
    "Wichita KS", "Overland Park KS", "Kansas City KS", "Topeka KS",
    # ── New Mexico ──────────────────────────────────────────────────────────
    "Albuquerque NM", "Las Cruces NM", "Rio Rancho NM", "Santa Fe NM",
    # ── Utah ────────────────────────────────────────────────────────────────
    "Salt Lake City UT", "West Valley City UT", "Provo UT", "West Jordan UT",
    "Orem UT", "Sandy UT", "Ogden UT", "St George UT",
    # ── Idaho ───────────────────────────────────────────────────────────────
    "Boise ID", "Nampa ID", "Meridian ID",
    "Caldwell ID", "Twin Falls ID", "Coeur d Alene ID",
    # ── Montana ─────────────────────────────────────────────────────────────
    "Billings MT", "Missoula MT", "Great Falls MT",
    # ── Wyoming ─────────────────────────────────────────────────────────────
    "Cheyenne WY", "Casper WY",
    # ── North/South Dakota ──────────────────────────────────────────────────
    "Fargo ND", "Bismarck ND",
    "Sioux Falls SD", "Rapid City SD",
    # ── West Virginia ───────────────────────────────────────────────────────
    "Charleston WV", "Huntington WV",
    # ── Maine ───────────────────────────────────────────────────────────────
    "Portland ME", "Lewiston ME", "Bangor ME",
    # ── New Hampshire ───────────────────────────────────────────────────────
    "Manchester NH", "Nashua NH", "Concord NH",
    # ── Vermont ─────────────────────────────────────────────────────────────
    "Burlington VT", "South Burlington VT",
    # ── Rhode Island ────────────────────────────────────────────────────────
    "Providence RI", "Cranston RI", "Pawtucket RI", "Woonsocket RI",
    # ── Delaware ────────────────────────────────────────────────────────────
    "Wilmington DE", "Dover DE", "Newark DE",
    # ── Hawaii ──────────────────────────────────────────────────────────────
    "Honolulu HI", "Pearl City HI", "Kailua HI",
    # ── Alaska ──────────────────────────────────────────────────────────────
    "Anchorage AK", "Fairbanks AK",
]

# Searches per run — 10 queries × 15 cities = 150 Places API calls per run
# Cost at $0.017/call ≈ $2.55/run. Previously was 15 calls/run.
SEARCHES_PER_RUN = 10
CITIES_PER_RUN   = 15

SOCIAL_DOMAINS = {
    "facebook.com", "fb.com", "instagram.com", "yelp.com",
    "twitter.com", "x.com", "linkedin.com", "tiktok.com", "linktree.ee",
    "linktr.ee", "squarespace.com", "wix.com", "godaddy.com", "google.com",
    "nextdoor.com", "thumbtack.com", "angi.com", "homeadvisor.com",
    "houzz.com", "bark.com", "porch.com",
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
            s = json.loads(STATE_FILE.read_text())
            # Migrate old niche_offset key to query_offset
            if "niche_offset" in s and "query_offset" not in s:
                s["query_offset"] = s.pop("niche_offset")
            return s
        except Exception:
            pass
    return {"query_offset": 0, "city_offset": 0}

def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def get_rotation(items: list, offset: int, count: int) -> tuple[list, int]:
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
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower().lstrip("www.")
        return any(s in domain for s in SOCIAL_DOMAINS)
    except Exception:
        return True

def fetch_site(url: str) -> str | None:
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
    flaws = []

    if url.startswith("http://"):
        flaws.append("no_ssl")

    soup = BeautifulSoup(html, "html.parser")

    viewport = soup.find("meta", attrs={"name": re.compile(r"viewport", re.I)})
    if not viewport:
        flaws.append("no_viewport")

    text = soup.get_text(" ", strip=True)
    year_matches = re.findall(r"(?:copyright|©|&copy;)\s*(?:\d{4}\s*[-–]\s*)?(\d{4})", text, re.I)
    for yr in year_matches:
        try:
            if int(yr) < 2020:
                flaws.append("outdated_copyright")
                break
        except ValueError:
            pass

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
    from urllib.parse import unquote
    email = unquote(raw.replace("mailto:", "").strip().split("?")[0]).strip()
    email = re.sub(r"^[^a-zA-Z0-9]+", "", email)
    return email.lower()

def is_placeholder_email(email: str) -> bool:
    if not email or "@" not in email:
        return True
    if email in PLACEHOLDER_EMAILS:
        return True
    local = email.split("@")[0]
    if local == "www":
        return True
    if PLACEHOLDER_EMAIL_PATTERNS.search(email):
        return True
    return False

def scrape_email(html: str) -> str:
    """Find first real email address in HTML."""
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a", href=re.compile(r"^mailto:", re.I)):
        email = clean_email(a["href"])
        if "@" in email and "." in email and not is_placeholder_email(email):
            return email
    text = soup.get_text(" ")
    matches = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
    for m in matches:
        email = m.lower()
        if not is_placeholder_email(email):
            return email
    return ""

def scrape_email_with_fallback(website: str, homepage_html: str) -> str:
    """
    Try homepage first, then /contact, /contact-us, /about, /about-us pages.
    Many businesses only put their email on the contact page, not the homepage.
    """
    email = scrape_email(homepage_html)
    if email:
        return email

    base = website.rstrip("/").split("?")[0]
    fallback_paths = ["/contact", "/contact-us", "/about", "/about-us",
                      "/contact.html", "/about.html", "/contact.php"]

    for path in fallback_paths:
        try:
            time.sleep(0.4)
            contact_html = fetch_site(base + path)
            if not contact_html:
                continue
            email = scrape_email(contact_html)
            if email:
                return email
        except Exception:
            continue

    return ""

# ─── Slug ─────────────────────────────────────────────────────────────────────

def make_slug(business_name: str, city_name: str, state: str) -> str:
    raw = f"{business_name} {city_name} {state}"
    slug = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")
    return slug[:60]

# ─── Parse city/state ─────────────────────────────────────────────────────────

def parse_city_state(city_str: str) -> tuple[str, str]:
    parts = city_str.rsplit(" ", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return city_str, ""

# ─── Notify Cortex ────────────────────────────────────────────────────────────

def notify_cortex():
    try:
        resp = requests.post(
            CORTEX_URL,
            headers={"x-internal-token": CORTEX_TOKEN, "Content-Type": "application/json"},
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
    print(f"Search pool: {len(SEARCHES)} query variants × {len(CITIES)} cities")

    BASE_DIR.mkdir(parents=True, exist_ok=True)

    state = load_state()
    existing_ids = load_existing_place_ids()
    print(f"Existing leads in CSV: {len(existing_ids)}")

    # Pick this run's rotation
    searches_this_run, new_query_offset = get_rotation(SEARCHES, state["query_offset"],  SEARCHES_PER_RUN)
    cities_this_run,   new_city_offset  = get_rotation(CITIES,   state["city_offset"],   CITIES_PER_RUN)

    print(f"Queries ({SEARCHES_PER_RUN}): {[q for _, q in searches_this_run]}")
    print(f"Cities  ({CITIES_PER_RUN}):  {cities_this_run}")
    print(f"Total API calls this run: {SEARCHES_PER_RUN * CITIES_PER_RUN}")

    new_leads: list[dict] = []
    scanned = 0

    for (niche, query_string) in searches_this_run:
        for city in cities_this_run:
            city_name, city_state = parse_city_state(city)
            query = f"{query_string} near {city}"
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

                time.sleep(0.5)

                # ── Track B: No website ──────────────────────────────────
                # Lowered threshold: reviews >= 3 (was 10), removed rating floor.
                # A business with 3 reviews and no website is a strong lead.
                if not website:
                    if reviews >= 3 and phone:
                        lead = {
                            "place_id":      place_id,
                            "business_name": name,
                            "first_name":    "",
                            "email":         "",
                            "phone":         phone,
                            "address":       address,
                            "city":          city_name,
                            "state":         city_state,
                            "rating":        rating,
                            "review_count":  reviews,
                            "website":       "none",
                            "track":         "B",
                            "flaw":          "no website",
                            "niche":         niche,
                            "quality_score": 1,
                            "slug":          make_slug(name, city_name, city_state),
                            "status":        "cold_call",
                            "date_found":    today,
                        }
                        new_leads.append(lead)
                        existing_ids.add(place_id)
                        print(f"     ✓ Track B: {name} ({city_name}) — {reviews} reviews, no site → cold_call")
                    continue

                # ── Track A: Has website — check if it's social ──────────
                if is_social_url(website):
                    continue

                # Fetch homepage
                time.sleep(1)
                html = fetch_site(website)
                if html is None:
                    continue

                flaws = detect_flaws(website, html)
                if not flaws:
                    continue  # Site is fine — skip

                # Email: try homepage → /contact → /about
                email = scrape_email_with_fallback(website, html)

                flaw_score    = min(len(flaws), 4)
                quality_score = max(1, 5 - flaw_score)

                lead = {
                    "place_id":      place_id,
                    "business_name": name,
                    "first_name":    "",          # Not hardcoding "Owner" — Instantly template handles this
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
                print(f"     ✓ Track A: {name} ({city_name}) — flaws: {flaws} — {email or 'no email'}")

    # Sort: Track A first (worst sites first for mockup priority), Track B (cold_call) last
    new_leads.sort(key=lambda l: (1 if l["track"] == "B" else 0, l["quality_score"]))

    if new_leads:
        append_leads(new_leads)
        print(f"\nAppended {len(new_leads)} new leads to {LEADS_CSV}")
    else:
        print("\nNo new leads this run.")

    track_a      = [l for l in new_leads if l["track"] == "A"]
    track_b      = [l for l in new_leads if l["track"] == "B"]
    emails_found = sum(1 for l in new_leads if l.get("email"))

    top5 = new_leads[:5]
    top5_lines = "\n".join(
        f"  {l['business_name']} | {l['city']}, {l['state']} | Track {l['track']} | {l['flaw']} | {l.get('email') or 'no email'}"
        for l in top5
    ) or "  (none)"

    summary = f"""RSWebWorks Scraper Run — {today}
Queries:   {', '.join(q for _, q in searches_this_run)}
Cities:    {', '.join(cities_this_run)}
API calls: {SEARCHES_PER_RUN * CITIES_PER_RUN}
Scanned:   {scanned} businesses (new, not yet in CSV)
New leads: {len(new_leads)} (Track A: {len(track_a)}, Track B: {len(track_b)})
Emails:    {emails_found}

Top {len(top5)} leads:
{top5_lines}
"""
    SUMMARY_FILE.write_text(summary)
    print(f"\n{summary}")

    state["query_offset"] = new_query_offset
    state["city_offset"]  = new_city_offset
    save_state(state)

    print("Notifying Cortex...")
    notify_cortex()
    print("Done.\n")

if __name__ == "__main__":
    main()
