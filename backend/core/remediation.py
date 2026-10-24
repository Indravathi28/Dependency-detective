"""Recommend an upgrade ONLY when advisory data supports it."""
from packaging.version import Version
from backend.core.matcher import affected_entries, fixes_for, version_affected

CAVEAT = "Not checked against advisories outside this scan: re-scan after upgrading and run your tests."


def recommend(name: str, version: str, vulns: list[dict]) -> dict:
    if not vulns:
        return {"version": None, "note": ""}
    targets = []
    for v in vulns:
        fixes = fixes_for(v, name, version)
        if not fixes:
            return {"version": None, "note": "At least one advisory lists no fixed version: no verified upgrade."}
        targets.append(min(fixes))
    target = max(targets)
    still = [v["id"] for v in vulns
             if any(version_affected(str(target), a) for a in affected_entries(v, name))]
    if still:
        return {"version": None, "note": f"{target} is still listed as affected by {', '.join(still)}."}
    major = " Major version change: read the changelog." if target.major != Version(version).major else ""
    return {"version": str(target), "note": f"Fixes all advisories found for this version.{major} {CAVEAT}"}
