"""Parse requirements.txt into structured entries (never executes anything)."""
import re
from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version

# status: exact | unresolved | malformed | skipped


def parse_requirements(text: str) -> list[dict]:
    items, seen = [], {}
    text = re.sub(r"\\\r?\n", " ", text)  # join "\" line continuations
    for no, raw in enumerate(text.splitlines(), 1):
        line = re.sub(r"(^|\s)#.*$", "", raw).strip()  # drop comments
        if not line:
            continue
        item = {"line": no, "raw": raw.strip(), "name": None, "specifier": "",
                "version": None, "status": "", "note": "", "duplicate_of": None}
        items.append(item)
        # -r, -e, --index-url, URLs and local paths are not scanned
        if line.startswith("-") or "://" in line or line.startswith((".", "/")):
            item.update(status="skipped", note="Option, URL or path: not scanned")
            continue
        line = re.sub(r"\s--hash=\S+", "", line)  # hashes are irrelevant here
        try:
            req = Requirement(line)
        except InvalidRequirement:
            item.update(status="malformed", note="Line could not be parsed")
            continue
        name = canonicalize_name(req.name)
        item.update(name=name, specifier=str(req.specifier))
        specs = list(req.specifier)
        if len(specs) == 1 and specs[0].operator in ("==", "===") and "*" not in specs[0].version:
            try:
                Version(specs[0].version)
                item.update(status="exact", version=specs[0].version)
            except InvalidVersion:
                item.update(status="unresolved", note="Version is not PEP 440 valid")
        elif specs:
            item.update(status="unresolved", note="Version range: exact version unknown")
        else:
            item.update(status="unresolved", note="No version specified")
        if req.marker:
            item["note"] = (item["note"] + "; " if item["note"] else "") + "Has environment marker"
        if name in seen:
            item["duplicate_of"] = seen[name]
            item["note"] = (item["note"] + "; " if item["note"] else "") + f"Duplicate of line {seen[name]}"
        else:
            seen[name] = no
    return items
