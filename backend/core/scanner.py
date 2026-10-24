"""Orchestrates: parse -> advisory lookup -> match -> remediation -> report dict."""
import json
from datetime import datetime, timezone
from backend import config
from backend.core.matcher import find_vulns, fixes_for
from backend.core.parser import parse_requirements
from backend.core.remediation import recommend
from backend.services import osv_service
from backend.utils import db

STATUS_OF = {"unresolved": "unresolved", "malformed": "malformed", "skipped": "skipped"}


def load_sample() -> dict:
    return json.loads(config.SAMPLE_ADVISORIES.read_text(encoding="utf-8"))


def _offline_advisories() -> tuple[list[dict], str]:
    sample = load_sample()
    merged = {v["id"]: v for v in sample["vulns"]}
    cached = db.cache_all()
    merged.update({v["id"]: v for v in cached})  # previously fetched OSV records win
    meta = sample["meta"]
    src = f"{meta['name']} (snapshot {meta['snapshot_date']}) + {len(cached)} cached OSV record(s)"
    return list(merged.values()), src


def _severity(v: dict) -> str:
    sev = (v.get("database_specific") or {}).get("severity")
    if sev:
        return str(sev).upper()
    cvss = [s.get("score") for s in v.get("severity", []) if s.get("score")]
    return f"CVSS vector: {cvss[0]}" if cvss else "Not provided"


def scan(text: str, mode: str = "offline") -> dict:
    entries = parse_requirements(text)
    pairs = sorted({(e["name"], e["version"]) for e in entries if e["status"] == "exact"})
    found, warnings = {}, []
    if mode == "online":
        source = "OSV.dev live API (api.osv.dev)"
        try:
            for pair, ids in zip(pairs, osv_service.query_batch(pairs)):
                found[pair] = [osv_service.get_vuln(i) for i in ids]
        except Exception as ex:
            found = None
            warnings.append(f"OSV lookup unavailable ({type(ex).__name__}). Switch to offline mode or retry.")
    else:
        advisories, source = _offline_advisories()
        found = {p: find_vulns(p[0], p[1], advisories) for p in pairs}

    packages, findings, sev_count = [], [], {}
    for e in entries:
        status = STATUS_OF.get(e["status"])
        vulns, rec = [], {"version": None, "note": ""}
        if e["status"] == "exact":
            if found is None:
                status = "lookup_unavailable"
            else:
                vulns = found[(e["name"], e["version"])]
                status = "vulnerable" if vulns else "no_match"
                rec = recommend(e["name"], e["version"], vulns)
        for v in vulns:
            sev = _severity(v)
            sev_count[sev] = sev_count.get(sev, 0) + 1
            fixes = sorted({str(f) for f in fixes_for(v, e["name"], e["version"])})
            findings.append({
                "package": e["name"], "version": e["version"], "id": v["id"],
                "aliases": v.get("aliases", []), "summary": v.get("summary") or "No summary provided",
                "severity": sev, "fixed_in": fixes, "modified": v.get("modified", ""),
                "references": [r["url"] for r in v.get("references", []) if r.get("url")][:5],
                "source_url": f"https://osv.dev/vulnerability/{v['id']}",
            })
        packages.append({"line": e["line"], "package": e["name"] or e["raw"], "specifier": e["specifier"],
                         "version": e["version"], "status": status, "advisories": len(vulns),
                         "recommended": rec["version"], "note": " ".join(filter(None, [e["note"] + ("." if e["note"] else ""), rec["note"]]))})
    count = lambda s: sum(p["status"] == s for p in packages)
    return {
        "scanned_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": mode, "source": source if found is not None else "OSV.dev (unreachable)",
        "summary": {"total": len(packages), "vulnerable": count("vulnerable"), "no_match": count("no_match"),
                    "unresolved": count("unresolved"), "lookup_unavailable": count("lookup_unavailable"),
                    "malformed": count("malformed"), "skipped": count("skipped"),
                    "advisories": len(findings), "severity": sev_count},
        "packages": packages, "findings": findings, "warnings": warnings,
        "disclaimer": "No matching record means none was found in the source used, not that a package is safe. "
                      "Upgrade suggestions are not guaranteed to be compatible.",
    }
