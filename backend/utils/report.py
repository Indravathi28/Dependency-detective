"""Export a scan report as JSON, CSV or Markdown."""
import json
import re
import pandas as pd
from packaging.utils import canonicalize_name

LABEL = {"vulnerable": "Confirmed match", "no_match": "No matching record", "unresolved": "Unresolved version",
         "lookup_unavailable": "Lookup unavailable", "malformed": "Malformed line", "skipped": "Skipped option"}

_PINNED_REQUIREMENT = re.compile(
    r"^(?P<indent>\s*)(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)"
    r"(?:\[[^\]\r\n]+\])?\s*(?:===|==)\s*(?P<version>[^\s;#\\]+)"
)


def to_json(r: dict) -> str:
    return json.dumps(r, indent=2)


def to_upgraded_requirements(text: str, packages: list[dict]) -> str:
    """Replace only verified, exact pins while preserving other input text."""
    upgrades = {
        package["line"]: (package["package"], package["version"], package["recommended"])
        for package in packages
        if package.get("recommended") and package.get("version")
    }
    output = []
    for line_number, line in enumerate(text.splitlines(keepends=True), 1):
        upgrade = upgrades.get(line_number)
        if not upgrade:
            output.append(line)
            continue

        package_name, old_version, new_version = upgrade
        content = line.rstrip("\r\n")
        ending = line[len(content):]
        match = _PINNED_REQUIREMENT.match(content)
        if (not match
                or canonicalize_name(match.group("name")) != canonicalize_name(package_name)
                or match.group("version") != old_version):
            output.append(line)
            continue

        start, end = match.span("version")
        output.append(content[:start] + new_version + content[end:] + ending)
    return "".join(output)


def to_csv(r: dict) -> str:
    return pd.DataFrame(r["packages"]).assign(status=lambda d: d["status"].map(LABEL)).to_csv(index=False)


def to_markdown(r: dict) -> str:
    s = r["summary"]
    md = [f"# Dependency Detective scan report", f"- Scanned (UTC): {r['scanned_at']}", f"- Mode: {r['mode']}",
          f"- Advisory source: {r['source']}", f"- Packages: {s['total']} | Confirmed matches: {s['vulnerable']} | "
          f"Unresolved: {s['unresolved']} | Lookup unavailable: {s['lookup_unavailable']}", "", "## Confirmed findings"]
    if not r["findings"]:
        md.append("None found in the source used.")
    for f in r["findings"]:
        md += [f"### {f['package']}=={f['version']}: {f['id']}", f"- Severity (source-provided): {f['severity']}",
               f"- Summary: {f['summary']}", f"- Fixed in: {', '.join(f['fixed_in']) or 'not stated'}",
               f"- Reference: {f['source_url']}"]
    md += ["", "## Suggested upgrades (evidence-based, not guaranteed compatible)"]
    md += [f"- {p['package']}: {p['version']} -> {p['recommended']}" for p in r["packages"] if p["recommended"]] or ["None."]
    md += ["", "## Incomplete checks"]
    md += [f"- line {p['line']} `{p['package']}`: {LABEL[p['status']]}. {p['note']}" for p in r["packages"]
           if p["status"] in ("unresolved", "lookup_unavailable", "malformed", "skipped")] or ["None."]
    md += ["", f"> {r['disclaimer']}"]
    return "\n".join(md)
