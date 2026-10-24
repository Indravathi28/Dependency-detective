"""OSV.dev client (free, no API key). Advisory details are cached in SQLite."""
import requests
from backend import config
from backend.utils import db

TIMEOUT = 15
BATCH = 500


def query_batch(pairs: list[tuple]) -> list[list[str]]:
    """Return advisory ids per (name, version) pair. Raises on network/API errors."""
    out = []
    for i in range(0, len(pairs), BATCH):
        chunk = pairs[i:i + BATCH]
        body = {"queries": [{"package": {"name": n, "ecosystem": "PyPI"}, "version": v} for n, v in chunk]}
        r = requests.post(f"{config.OSV_API_URL}/querybatch", json=body, timeout=TIMEOUT)
        r.raise_for_status()
        out += [[x["id"] for x in res.get("vulns", [])] for res in r.json()["results"]]
    return out


def get_vuln(vid: str) -> dict:
    cached = db.cache_get(vid)
    if cached:
        return cached
    r = requests.get(f"{config.OSV_API_URL}/vulns/{vid}", timeout=TIMEOUT)
    r.raise_for_status()
    rec = r.json()
    db.cache_put(vid, rec)
    return rec
