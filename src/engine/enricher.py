"""
src/engine/enricher.py
Automatically fetches and caches logos, flags, company icons, and general entity icons.
Provides local cache management and fallback to SportsDB, Flagpedia, Clearbit, and custom URLs.
"""

import os
import re
import urllib.request
import urllib.parse
import json
import hashlib
from typing import Dict, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE_DIR = os.path.join(ROOT, "assets", "cache")

# Create cache folders
os.makedirs(os.path.join(CACHE_DIR, "flags"), exist_ok=True)
os.makedirs(os.path.join(CACHE_DIR, "football"), exist_ok=True)
os.makedirs(os.path.join(CACHE_DIR, "companies"), exist_ok=True)
os.makedirs(os.path.join(CACHE_DIR, "general"), exist_ok=True)

# Standard mappings
COUNTRY_CODES = {
    "vietnam": "vn", "việt nam": "vn",
    "usa": "us", "united states": "us", "united states of america": "us", "mỹ": "us",
    "uk": "gb", "united kingdom": "gb", "england": "gb", "anh": "gb",
    "france": "fr", "pháp": "fr",
    "germany": "de", "đức": "de",
    "italy": "it", "ý": "it",
    "spain": "es", "tây ban nha": "es",
    "japan": "jp", "nhật bản": "jp",
    "korea": "kr", "south korea": "kr", "hàn quốc": "kr",
    "china": "cn", "trung quốc": "cn",
    "brazil": "br", "brazin": "br",
    "argentina": "ar",
    "portugal": "pt", "bồ đào nha": "pt",
    "netherlands": "nl", "hà lan": "nl",
    "belgium": "be", "bỉ": "be",
    "russia": "ru", "nga": "ru",
    "india": "in", "ấn độ": "in",
    "canada": "ca",
    "australia": "au", "úc": "au",
}

COMPANY_DOMAINS = {
    "google": "google.com", "alphabet": "google.com",
    "apple": "apple.com",
    "microsoft": "microsoft.com",
    "amazon": "amazon.com",
    "meta": "meta.com", "facebook": "meta. Meta.com",
    "netflix": "netflix.com",
    "tesla": "tesla.com",
    "nvidia": "nvidia.com",
    "samsung": "samsung.com",
    "toyota": "toyota.com",
    "intel": "intel.com",
    "amd": "amd.com",
    "coca cola": "cocacola.com", "pepsi": "pepsico.com",
}

def get_safe_filename(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_\-]', '', name.replace(" ", "_")).lower()

def download_url(url: str, dest_path: str) -> bool:
    """Download file from URL to dest_path with custom User-Agent to avoid HTTP 403."""
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=8) as response, open(dest_path, "wb") as out_file:
            out_file.write(response.read())
        return True
    except Exception as e:
        print(f"[Enricher] Error downloading {url}: {e}")
        return False

def enrich_entity_logo(entity_name: str) -> Optional[str]:
    """
    Search and download a logo for the given entity name.
    Checks flags, company domains, football APIs, and general logo servers.
    Returns the absolute path to the local cached file, or None if not found.
    """
    name_lower = entity_name.strip().lower()
    safe_name = get_safe_filename(entity_name)
    
    # 1. Check Country Flags (Flagpedia)
    for country, code in COUNTRY_CODES.items():
        if country in name_lower or name_lower == code:
            dest = os.path.join(CACHE_DIR, "flags", f"{code}.png")
            if os.path.exists(dest):
                return dest
            url = f"https://flagcdn.com/w320/{code}.png"
            if download_url(url, dest):
                return dest

    # 2. Check Corporate Brands (Clearbit via Logo.dev / logo.clearbit.com)
    for company, domain in COMPANY_DOMAINS.items():
        if company in name_lower:
            dest = os.path.join(CACHE_DIR, "companies", f"{safe_name}.png")
            if os.path.exists(dest):
                return dest
            url = f"https://logo.clearbit.com/{domain}"
            if download_url(url, dest):
                return dest

    # 3. Check Football / Sports Clubs (SportsDB API)
    # Common football clubs
    football_keywords = ["united", "city", "arsenal", "chelsea", "liverpool", "fc", "real madrid", "barcelona", "bayern", "juventus", "milan", "inter", "psg", "tottenham", "leicester", "newcastle", "blackburn"]
    if any(kw in name_lower for kw in football_keywords):
        dest = os.path.join(CACHE_DIR, "football", f"{safe_name}.png")
        if os.path.exists(dest):
            return dest
        try:
            # Query SportsDB API (using free test key 3)
            query = urllib.parse.quote(entity_name)
            url = f"https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t={query}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                if data and data.get("teams"):
                    badge_url = data["teams"][0].get("strTeamBadge") or data["teams"][0].get("strBadge")
                    if badge_url and download_url(badge_url, dest):
                        return dest
        except Exception as e:
            print(f"[Enricher] SportsDB query failed for {entity_name}: {e}")

    # 4. Fallback General Logo Search (Clearbit using direct domain guessing if name has domain suffix)
    if "." in name_lower and not name_lower.startswith("www"):
        dest = os.path.join(CACHE_DIR, "companies", f"{safe_name}.png")
        if os.path.exists(dest):
            return dest
        url = f"https://logo.clearbit.com/{name_lower}"
        if download_url(url, dest):
            return dest

    # If it's a popular brand, guess domain
    guessed_domain = f"{safe_name}.com"
    dest = os.path.join(CACHE_DIR, "companies", f"{safe_name}.png")
    if not os.path.exists(dest):
        url = f"https://logo.clearbit.com/{guessed_domain}"
        if download_url(url, dest):
            return dest

    return None
