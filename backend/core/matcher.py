"""Match a package version against OSV-format advisory records."""
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version

_ORDER = {"introduced": 0, "fixed": 1, "last_affected": 1}


def _v(s):
    try:
        return Version(str(s))
    except InvalidVersion:
        return None


def affected_entries(vuln: dict, name: str):
    """Yield the 'affected' blocks of a record that belong to this PyPI package."""
    for a in vuln.get("affected", []):
        p = a.get("package", {})
        if p.get("ecosystem") == "PyPI" and canonicalize_name(p.get("name", "")) == name:
            yield a


def _in_range(v: Version, events: list) -> bool:
    evs = [(pv, k) for e in events for k, val in e.items()
           if k in _ORDER and (pv := _v(val)) is not None]
    hit = False
    for pv, k in sorted(evs, key=lambda t: (t[0], _ORDER[t[1]])):
        if k == "introduced" and v >= pv:
            hit = True
        elif k == "fixed" and v >= pv:
            hit = False
        elif k == "last_affected" and v > pv:
            hit = False
    return hit


def version_affected(version: str, entry: dict) -> bool:
    v = _v(version)
    if v is None:
        return False
    if any(_v(x) == v for x in entry.get("versions", [])):  # explicitly listed
        return True
    return any(_in_range(v, r.get("events", [])) for r in entry.get("ranges", [])
               if r.get("type") in ("ECOSYSTEM", "SEMVER"))


def is_affected(vuln: dict, name: str, version: str) -> bool:
    return any(version_affected(version, a) for a in affected_entries(vuln, name))


def find_vulns(name: str, version: str, advisories: list[dict]) -> list[dict]:
    return [a for a in advisories if is_affected(a, name, version)]


def fixes_for(vuln: dict, name: str, version: str) -> list[Version]:
    """Fixed versions above the current one, from ranges that contain the current version."""
    cur, out = Version(version), []
    for a in affected_entries(vuln, name):
        if version_affected(version, a):
            for r in a.get("ranges", []):
                for e in r.get("events", []):
                    fv = _v(e["fixed"]) if "fixed" in e else None
                    if fv and fv > cur:
                        out.append(fv)
    return out
