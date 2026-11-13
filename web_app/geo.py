# Vibe coded: this web interface was written with an AI assistant in 2026.
"""
Where an address is, for the staff delivery map.

The database stores an address as one line of text. To put an order on a street map the address
is looked up once at OpenStreetMap's Nominatim service and the answer is kept in geocache.json,
so every address is sent at most one time. Lookups run in the background, one per second at most
(the service's limit). Until an answer is there, or when lookups are switched off with
MAP_GEOCODING=0, the order sits at the rough middle of its postal area.
"""
import json
import os
import queue
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path

ENABLED = os.getenv("MAP_GEOCODING", "1") != "0"
COUNTRY = os.getenv("MAP_COUNTRY", "nl")
SHOP = {"lat": float(os.getenv("SHOP_LAT", "50.8514")), "lng": float(os.getenv("SHOP_LNG", "5.6910"))}  # Markt, Maastricht
CACHE_FILE = Path(__file__).parent / "geocache.json"

# rough centres of the Maastricht postal areas, only used while an address has no exact position
AREA_CENTRES = {
    "6211": (50.8492, 5.6885), "6212": (50.8400, 5.6890), "6213": (50.8370, 5.6690), "6214": (50.8470, 5.6660),
    "6215": (50.8560, 5.6600), "6216": (50.8600, 5.6790), "6217": (50.8660, 5.6650), "6218": (50.8700, 5.6500),
    "6219": (50.8720, 5.6850), "6221": (50.8490, 5.7010), "6222": (50.8660, 5.7050), "6223": (50.8850, 5.6950),
    "6224": (50.8520, 5.7130), "6225": (50.8600, 5.7300), "6226": (50.8440, 5.7170), "6227": (50.8370, 5.7250),
    "6228": (50.8280, 5.7250), "6229": (50.8320, 5.7080),
}

_lock = threading.Lock()
_todo: "queue.Queue[str]" = queue.Queue()
_queued: set[str] = set()
try:
    _cache: dict = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
except Exception:
    _cache = {}


def _key(address: str) -> str:
    return " ".join((address or "").lower().split())


def _lookup(address: str):
    query = urllib.parse.urlencode({"format": "jsonv2", "limit": 1, "countrycodes": COUNTRY, "q": address})
    request = urllib.request.Request("https://nominatim.openstreetmap.org/search?" + query,
                                     headers={"User-Agent": "pizza-ordering-system-demo/1.0"})
    with urllib.request.urlopen(request, timeout=10) as response:
        found = json.loads(response.read().decode("utf-8"))
    return [float(found[0]["lat"]), float(found[0]["lon"])] if found else None


def _worker():
    while True:
        address = _todo.get()
        try:
            position = _lookup(address)
            with _lock:
                _cache[_key(address)] = position  # None is kept too: the address is unknown, don't ask again
                CACHE_FILE.write_text(json.dumps(_cache, indent=1), encoding="utf-8")
        except Exception:
            with _lock:
                _queued.discard(_key(address))  # network trouble: try again on a later request
        time.sleep(1.1)


if ENABLED:
    threading.Thread(target=_worker, daemon=True).start()


def locate(address: str, postal_code: str):
    """Return {'lat', 'lng', 'exact'} for an address, or None when even the postal area is unknown."""
    key = _key(address)
    with _lock:
        position = _cache.get(key)
        if ENABLED and key and key not in _cache and key not in _queued:
            _queued.add(key)
            _todo.put(address)
    if position:
        return {"lat": position[0], "lng": position[1], "exact": True}
    centre = AREA_CENTRES.get(postal_code)
    if centre:
        return {"lat": centre[0], "lng": centre[1], "exact": False}
    return None
