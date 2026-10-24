"""Dependency Detective: Streamlit frontend. All logic lives in backend/."""
from urllib.parse import quote

import pandas as pd
import plotly.express as px
import streamlit as st

from backend import config
from backend.core.scanner import scan
from backend.utils import db
from backend.utils.report import LABEL, to_csv, to_json, to_markdown, to_upgraded_requirements
from backend.utils.validators import validate_text, validate_upload
from components import ui

ui.setup()
ui.hero()

# ---------- sidebar ----------
with st.sidebar:
    st.header("Scan settings")
    mode_label = st.radio("Advisory source", ["Offline (bundled + cached data)", "Online (OSV.dev)"],
                          help="Online needs internet. Offline uses the bundled sample snapshot and any records cached earlier.")
    mode = "online" if mode_label.startswith("Online") else "offline"
    st.caption("Online results are cached, so they also work offline afterwards.")
    st.divider()
    st.caption("Privacy: your file is processed in memory and only the scan report is stored locally. "
               "Do not upload private data.")

# ---------- input ----------
if "text" not in st.session_state:
    st.session_state.text = ""
left, right = st.columns([3, 2])
with right:
    up = st.file_uploader("Upload requirements.txt", type=["txt"])
    if st.button("Load demo file"):
        st.session_state.text = config.SAMPLE_REQUIREMENTS.read_text(encoding="utf-8")
with left:
    pasted = st.text_area("Or paste requirements", key="text", height=210, placeholder="flask==2.2.0\nrequests==2.28.0")

if st.button("Scan dependencies", type="primary"):
    try:
        text = validate_upload(up.name, up.getvalue()) if up else validate_text(pasted)
        with st.spinner("Scanning..."):
            report = scan(text, mode)
            db.save_scan(report)
        st.session_state.report = report
        st.session_state.requirements_text = text
    except ValueError as err:
        st.warning(str(err))
    except Exception:
        st.error("Something went wrong during the scan. Please try again.")

# ---------- results ----------
r = st.session_state.get("report")
if not r:
    st.info("Paste a requirements file or load the demo, then choose **Scan dependencies**.")
    st.stop()

for w in r["warnings"]:
    st.markdown(f'<div class="dd-warn">⚠️ {w}</div>', unsafe_allow_html=True)
s = r["summary"]
st.caption(f"Source: {r['source']} · scanned {r['scanned_at']} UTC")
cols = st.columns(5)
for c, (k, v) in zip(cols, [("vulnerable", "#B42318"), ("no_match", "#2F7D4F"), ("unresolved", "#B7791F"),
                            ("lookup_unavailable", "#667085"), ("malformed", "#7A3E9D")]):
    ui.stat(c, s[k], LABEL[k], v)
st.write("")

t1, t2, t3, t4 = st.tabs(["Findings", "All packages", "Charts", "Export"])

with t1:
    original_requirements = st.session_state.get("requirements_text", "")
    upgraded_requirements = to_upgraded_requirements(original_requirements, r["packages"])
    if upgraded_requirements != original_requirements:
        st.download_button(
            "Download upgraded requirements.txt",
            upgraded_requirements,
            "requirements-updated.txt",
            help="Updates only exact pins with a verified suggested version. Review compatibility and run your tests.",
        )
        st.caption("Review the suggested changes, then install with `pip install -r requirements-updated.txt` and run your tests.")
    if not r["findings"]:
        st.success("No advisories matched in the source used. This does not prove the packages are safe.")
    pk = {}
    for f in r["findings"]:
        pk.setdefault((f["package"], f["version"]), []).append(f)
    recs = {p["package"]: p for p in r["packages"] if p["recommended"] or p["note"]}
    for (name, ver), fs in pk.items():
        with st.expander(f"{name}=={ver}: {len(fs)} advisor{'y' if len(fs) == 1 else 'ies'}", expanded=len(pk) <= 3):
            for f in fs:
                col = ui.sev_color(f["severity"])
                al = f" · {', '.join(f['aliases'])}" if f["aliases"] else ""
                st.markdown(f'<div class="dd-adv" style="--c:{col}"><span class="t">{f["id"]}</span>{al} '
                            f'{ui.badge(f["severity"], col)}<br>{f["summary"]}<br>'
                            f'<small>Fixed in: {", ".join(f["fixed_in"]) or "not stated"} · '
                            f'<a href="{f["source_url"]}" target="_blank">OSV record</a></small></div>', unsafe_allow_html=True)
                if f["references"]:
                    st.caption("References: " + " · ".join(f"[{i + 1}]({u})" for i, u in enumerate(f["references"])))
            p = recs.get(name)
            if p and p["recommended"]:
                st.markdown(f'<div class="dd-fix"><b>Suggested upgrade:</b> {name} {ver} → <b>{p["recommended"]}</b><br>'
                            f'<small>{p["note"]}</small></div>', unsafe_allow_html=True)
                pypi_url = (
                    f"https://pypi.org/project/{quote(name, safe='')}/"
                    f"{quote(p['recommended'], safe='')}/"
                )
                st.link_button("View / download release files on PyPI", pypi_url)
            elif p:
                st.markdown(f'<div class="dd-warn"><b>No verified upgrade.</b> {p["note"]}</div>', unsafe_allow_html=True)
    incomplete = [p for p in r["packages"] if p["status"] in ("unresolved", "lookup_unavailable", "malformed", "skipped")]
    if incomplete:
        st.subheader("Incomplete checks")
        st.caption("These lines were not checked against advisories.")
        st.dataframe(pd.DataFrame(incomplete).assign(status=lambda d: d["status"].map(LABEL))
                     [["line", "package", "specifier", "status", "note"]], hide_index=True, width="stretch")

with t2:
    df = pd.DataFrame(r["packages"]).assign(status=lambda d: d["status"].map(LABEL))
    pick = st.multiselect("Filter by status", sorted(df["status"].unique()))
    st.dataframe(df[df["status"].isin(pick)] if pick else df, hide_index=True, width="stretch",
                 column_config={"advisories": st.column_config.NumberColumn("Advisories"),
                                "recommended": "Suggested version"})

with t3:
    a, b = st.columns(2)
    sc = pd.DataFrame([(LABEL[k], s[k]) for k in LABEL if s[k]], columns=["Status", "Count"])
    cmap = {LABEL[k]: v[1] for k, v in ui.STATUS.items()}
    a.plotly_chart(px.pie(sc, names="Status", values="Count", hole=.55, color="Status", color_discrete_map=cmap,
                          title="Packages by check result"), width="stretch")
    if s["severity"]:
        sv = pd.DataFrame(list(s["severity"].items()), columns=["Severity", "Advisories"])
        b.plotly_chart(px.bar(sv, x="Severity", y="Advisories", title="Advisories by source-provided severity",
                              color_discrete_sequence=["#14212B"]), width="stretch")
    else:
        b.info("No advisories to chart.")

with t4:
    st.caption("Reports separate confirmed findings from incomplete checks.")
    c1, c2, c3 = st.columns(3)
    c1.download_button("Markdown report", to_markdown(r), "dependency-report.md", width="stretch")
    c2.download_button("CSV (packages)", to_csv(r), "dependency-report.csv", width="stretch")
    c3.download_button("JSON (full)", to_json(r), "dependency-report.json", width="stretch")
    st.warning(r["disclaimer"])
