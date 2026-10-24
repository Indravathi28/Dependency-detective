# Dependency Detective

Software supply-chain risk analyzer: scans a Python `requirements.txt` against OSV advisory data and reports confirmed findings, evidence-based upgrades and incomplete checks.

## 1. Problem Statement
Projects depend on external packages that may have known vulnerabilities. Developers need to know which pinned versions are affected, why, and what fixes exist.

## 2. Objectives
- Parse requirements files (pins, ranges, comments, duplicates, malformed lines)
- Match exact versions against advisory data (OSV online, or cached/offline)
- Suggest upgrades only when advisory data supports them; export reports and keep history

## 3. Features
Exact-version matching, source-provided severity only, five result states (confirmed / unresolved / no matching record / lookup unavailable / malformed), Markdown/CSV/JSON export, scan history and before/after comparison. Limits: `.txt` only, 200 KB, direct dependencies only (no lockfile).

## 4. Technology Stack
Python 3.12, Streamlit, `packaging`, requests, pandas, Plotly, SQLite, pytest. No LLM and no API key needed.

## 5. Architecture
upload/paste -> validators -> parser -> advisory lookup (OSV API or cached dataset) -> version matcher -> remediation -> report -> UI/export/history

## 6. Project Structure
`app.py` UI · `pages/` history page · `components/` UI helpers · `backend/core` parser, matcher, remediation, scanner, compare · `backend/services` OSV client · `backend/utils` validators, db, report · `data/sample` demo files · `tests/`

## 7. Prerequisites
Python 3.11/3.12, Git. Internet only for online mode.

## 8. Installation
```
git clone <repo-url> && cd dependency-detective
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

## 9. Run
```
streamlit run app.py
```

## 10. How to Use
Click **Load demo file**, choose a source, click **Scan dependencies**. Expect confirmed matches for flask, requests, PyYAML, Jinja2, urllib3 and pillow; `numpy`/`pandas` unresolved; one malformed line; `rich` with no matching record. For evidence-backed upgrades, open a PyPI release link or download the updated requirements file from the Findings tab. Review compatibility and run your tests before installing upgrades.

## 11. Configuration
`OSV_API_URL` (optional, default `https://api.osv.dev/v1`) in `.env` or Streamlit secrets.

## 12. Testing
`python -m pytest -q` (26 tests: parsing, version boundaries, remediation, online failure, exports, validation).

## 13. Screenshots / Demo
Add screenshots to `assets/` and the live Streamlit Cloud URL here.

## 14. Known Limitations
Bundled dataset is a small demo subset: refresh via online scans. Range/unpinned versions are not resolved. OSV pagination for very large result sets is not handled. SQLite history is temporary on Streamlit Cloud. Upgrades are not guaranteed compatible.

## 15. Privacy and Responsible Use
Files are processed in memory; only the report is stored locally. "No matching record" never means "safe". Do not upload private data.

## 16. Future Enhancements
Lockfile/transitive analysis with NetworkX, test run after upgrade, local-LLM explanations from retrieved records.

## 17. Credits and License
Advisory data: OSV.dev and GitHub Advisory Database. Add a license of your choice.
