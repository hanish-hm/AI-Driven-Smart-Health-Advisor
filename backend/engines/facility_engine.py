"""
Facility engine: finds nearby hospitals/doctors using Nominatim (OpenStreetMap).
Completely free, no API key required.
Only called when urgency is 'see_doctor' or 'emergency'.
"""

import logging
import requests
from datetime import datetime
from backend.models.response import NearbyFacility

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
MAX_RESULTS   = 5
HEADERS       = {"User-Agent": "SmartHealthAdvisor/1.0"}

AMENITY_TIERS = ["hospital", "clinic", "doctors", "pharmacy"]


def _search(amenity: str, city: str, country: str) -> list[dict]:
    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={
                "q": f"{amenity} near {city}, {country}",
                "format": "json",
                "limit": MAX_RESULTS,
                "addressdetails": 1,
                "extratags": 1,
            },
            headers=HEADERS,
            timeout=8,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error("Nominatim search error: %s", e)
        return []


def get_nearby_facilities(city: str | None, country: str | None) -> list[NearbyFacility]:
    if not city and not country:
        return []

    city    = city or ""
    country = country or ""
    location_label = ", ".join(filter(None, [city, country]))
    results = []

    for amenity in AMENITY_TIERS:
        results = _search(amenity, city, country)
        if results:
            logger.info("Nominatim found %d results for amenity=%s near %s", len(results), amenity, location_label)
            break
        logger.info("No results for amenity=%s near %s, trying next tier", amenity, location_label)

    if not results:
        logger.warning("No facilities found near %s", location_label)
        return []

    facilities = []
    for place in results[:MAX_RESULTS]:
        name    = place.get("display_name", "").split(",")[0].strip() or "Unnamed Facility"
        address = ", ".join(place.get("display_name", "").split(",")[1:4]).strip() or location_label
        lat     = place.get("lat", "")
        lon     = place.get("lon", "")

        extratags     = place.get("extratags") or {}
        phone         = extratags.get("phone") or extratags.get("contact:phone")
        opening_hours = extratags.get("opening_hours", "")

        open_now = None
        if opening_hours:
            try:
                hour = datetime.now().hour
                if opening_hours.strip() == "24/7":
                    open_now = True
                elif "-" in opening_hours and ":" in opening_hours:
                    parts = opening_hours.split(" ")
                    if len(parts) >= 2:
                        time_range = parts[-1]
                        open_h, close_h = time_range.split("-")
                        open_now = int(open_h.split(":")[0]) <= hour < int(close_h.split(":")[0])
            except Exception:
                open_now = None

        maps_url = f"https://www.google.com/maps/search/{requests.utils.quote(name + ' ' + location_label)}/@{lat},{lon},17z"

        facilities.append(NearbyFacility(
            name=name,
            address=address,
            phone=phone,
            maps_url=maps_url,
            open_now=open_now,
            rating=None,
        ))

    return facilities
