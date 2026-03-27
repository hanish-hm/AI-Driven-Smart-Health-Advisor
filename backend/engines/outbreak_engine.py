"""
Real-time outbreak alert engine.
Fetches WHO Disease Outbreak News API, caches 1 hour.
Returns exactly 2 alerts:
  - Alert 1: most recent WHO alert matching user's country or region (nearest)
  - Alert 2: most recent global WHO alert
Falls back to 1 global alert if no location match found.
"""
import time
import re
from typing import List, Optional
import httpx

_WHO_DON_URL  = "https://www.who.int/api/news/diseaseoutbreaknews"
_WHO_BASE_URL = "https://www.who.int/emergencies/disease-outbreak-news/item/"
_CACHE_TTL    = 3600

_state = {"cache": [], "cache_time": 0.0}

_REGION_MAP = {
    "africa":   ["nigeria","ghana","kenya","ethiopia","tanzania","uganda","cameroon","senegal",
                 "mali","niger","chad","sudan","south sudan","somalia","mozambique","zambia",
                 "zimbabwe","malawi","rwanda","burundi","drc","congo","angola","namibia",
                 "botswana","south africa","egypt","libya","tunisia","morocco","algeria",
                 "guinea","sierra leone","liberia","ivory coast","burkina faso","togo","benin",
                 "gabon","central african republic","eritrea","djibouti","comoros","madagascar"],
    "asia":     ["china","india","pakistan","bangladesh","indonesia","philippines","vietnam",
                 "thailand","myanmar","cambodia","laos","malaysia","singapore","japan","korea",
                 "nepal","sri lanka","afghanistan","iran","iraq","saudi arabia","yemen","oman",
                 "jordan","lebanon","syria","turkey","azerbaijan","georgia","kazakhstan",
                 "uzbekistan","tajikistan","kyrgyzstan","mongolia","taiwan","hong kong"],
    "americas": ["united states","usa","canada","mexico","brazil","argentina","colombia",
                 "venezuela","peru","chile","ecuador","bolivia","paraguay","uruguay","cuba",
                 "haiti","dominican republic","jamaica","trinidad","guatemala","honduras",
                 "el salvador","nicaragua","costa rica","panama"],
    "europe":   ["uk","united kingdom","france","germany","italy","spain","portugal","netherlands",
                 "belgium","switzerland","austria","sweden","norway","denmark","finland","poland",
                 "ukraine","russia","greece","romania","bulgaria","hungary","czech","slovakia",
                 "croatia","serbia","albania","moldova","belarus","estonia","latvia","lithuania",
                 "ireland","iceland"],
    "oceania":  ["australia","new zealand","papua new guinea","fiji","solomon islands","vanuatu",
                 "samoa","tonga","kiribati","micronesia"],
}


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text or "").strip()


def _get_region(country: str) -> Optional[str]:
    loc = country.lower()
    for region, countries in _REGION_MAP.items():
        if any(c in loc for c in countries):
            return region
    return None


def _refresh() -> None:
    try:
        r = httpx.get(_WHO_DON_URL, timeout=8.0, follow_redirects=True)
        r.raise_for_status()
        items = sorted(
            r.json().get("value", []),
            key=lambda x: x.get("PublicationDate", ""),
            reverse=True,
        )
        parsed = []
        for item in items:
            title    = item.get("Title", "").strip()
            summary  = _strip_html(item.get("Summary") or item.get("Overview") or "")
            date     = (item.get("PublicationDate") or "")[:10]
            url_name = item.get("UrlName", "")
            link     = f"{_WHO_BASE_URL}{url_name}" if url_name else "https://www.who.int/emergencies/disease-outbreak-news"
            if title:
                parsed.append({
                    "title":          title,
                    "summary":        summary[:300] + ("..." if len(summary) > 300 else ""),
                    "link":           link,
                    "date":           date,
                    "source":         "WHO Disease Outbreak News",
                    "location_match": False,
                    "match_type":     "global_fallback",
                })
        _state["cache"]      = parsed
        _state["cache_time"] = time.time()
    except Exception:
        pass


def get_relevant_alerts(country: Optional[str], city: Optional[str]) -> List[dict]:
    """Return exactly 2 WHO alerts:
    - Alert 1: most recent WHO alert matching user's country or region
    - Alert 2: most recent global WHO alert (always the latest)
    """
    if not _state["cache"] or (time.time() - _state["cache_time"]) >= _CACHE_TTL:
        _refresh()

    cache = _state["cache"]
    if not cache:
        return []

    tokens_exact = [t.lower().strip() for t in [country, city] if t]
    region       = _get_region(country or "")

    local_alert = None

    # Try exact country/city match
    if tokens_exact:
        for a in cache:
            if any(t in a["title"].lower() for t in tokens_exact):
                local_alert = {**a, "location_match": True, "match_type": "exact"}
                break

    # Try regional match
    if local_alert is None and region and region in _REGION_MAP:
        for a in cache:
            if any(c in a["title"].lower() for c in _REGION_MAP[region]):
                local_alert = {**a, "location_match": True, "match_type": "region"}
                break

    # Alert 2: always the most recent global alert
    global_alert = {**cache[0], "location_match": False, "match_type": "global_fallback"}

    if local_alert is None:
        return [global_alert]

    # Avoid duplicate if local and global are the same article
    if local_alert["title"] == global_alert["title"]:
        return [local_alert]

    return [local_alert, global_alert]
