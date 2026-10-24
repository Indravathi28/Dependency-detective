"""Reusable UI pieces: theme CSS, hero, metric cards, badges."""
import streamlit as st

STATUS = {"vulnerable": ("Confirmed match", "#B42318"), "no_match": ("No matching record", "#2F7D4F"),
          "unresolved": ("Unresolved version", "#B7791F"), "lookup_unavailable": ("Lookup unavailable", "#667085"),
          "malformed": ("Malformed line", "#7A3E9D"), "skipped": ("Skipped option", "#475467")}
SEV = {"CRITICAL": "#7A1212", "HIGH": "#B42318", "MODERATE": "#C77700", "MEDIUM": "#C77700", "LOW": "#2563A8"}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
  --dd-ink: #17324D;
  --dd-muted: #587087;
  --dd-teal: #087F8C;
  --dd-line: #DCE8EC;
  --dd-surface: #FFFFFF;
  --dd-canvas: #F2F8FA;
}

html, body, .stMarkdown, label, input, textarea { font-family: 'IBM Plex Sans', sans-serif; }
.material-icons, [data-testid="stIconMaterial"] { font-family: 'Material Symbols Rounded' !important; }
div[data-testid="stFileUploader"] [data-testid="stIconMaterial"] { display: none; }
h1, h2, h3 { font-family: 'Fraunces', Georgia, serif !important; letter-spacing: -0.02em; color: var(--dd-ink); }
.stApp { background: linear-gradient(145deg, #F2F8FA 0%, #F8FAFC 54%, #F2F7F5 100%); }
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1200px; }

.dd-hero {
  position: relative;
  overflow: hidden;
  background: linear-gradient(115deg, #12314A 0%, #15566A 58%, #087F8C 100%);
  color: #F7FCFD;
  border: 1px solid rgba(255,255,255,.16);
  border-radius: 20px;
  padding: 34px 38px;
  margin-bottom: 26px;
  box-shadow: 0 16px 38px rgba(18,49,74,.15);
}
.dd-hero:after {
  content: "";
  position: absolute;
  width: 250px;
  height: 250px;
  top: -145px;
  right: 6%;
  border: 1px solid rgba(255,255,255,.2);
  border-radius: 50%;
  box-shadow: 0 0 0 28px rgba(255,255,255,.035), 0 0 0 58px rgba(255,255,255,.025);
}
.dd-hero .dd-kicker {
  color: #A9E2DE;
  font-size: .76rem;
  font-weight: 700;
  letter-spacing: .14em;
  text-transform: uppercase;
}
.dd-hero h1 { color: #F7FCFD; margin: 8px 0 7px; font-size: clamp(2rem, 4vw, 2.7rem); }
.dd-hero p { margin: 0; color: #D9E9EE; max-width: 68ch; line-height: 1.65; }
.dd-hero code {
  background: rgba(255,255,255,.13);
  color: #FFE09A;
  padding: 3px 7px;
  border: 1px solid rgba(255,255,255,.12);
  border-radius: 6px;
  font-family: 'IBM Plex Mono', monospace;
}

.dd-stat {
  min-height: 92px;
  background: var(--dd-surface);
  border: 1px solid var(--dd-line);
  border-top: 4px solid var(--c);
  border-radius: 14px;
  padding: 14px 16px;
  box-shadow: 0 5px 16px rgba(23,50,77,.045);
  transition: transform .18s ease, box-shadow .18s ease;
}
.dd-stat:hover { transform: translateY(-2px); box-shadow: 0 9px 22px rgba(23,50,77,.09); }
.dd-stat .n { font-family: 'Fraunces', Georgia, serif; font-size: 2rem; line-height: 1.1; color: var(--c); }
.dd-stat .l { margin-top: 5px; font-size: .82rem; font-weight: 600; color: var(--dd-muted); }
.dd-badge { display: inline-block; padding: 3px 9px; border-radius: 999px; font-size: .76rem; font-weight: 700; color: #fff; background: var(--c); }
.dd-adv { background: #fff; border: 1px solid var(--dd-line); border-left: 5px solid var(--c); border-radius: 12px; padding: 14px 16px; margin: 10px 0; box-shadow: 0 4px 12px rgba(23,50,77,.04); line-height: 1.7; }
.dd-adv .t { font-family: 'IBM Plex Mono', monospace; font-weight: 500; color: var(--dd-ink); }
.dd-fix { background: #E9F7F1; border: 1px solid #B7E3D0; border-radius: 12px; padding: 12px 15px; margin-top: 10px; color: #176747; }
.dd-warn { background: #FFF6E4; border: 1px solid #F0D391; border-radius: 12px; padding: 12px 15px; margin: 10px 0; color: #78520C; }

section[data-testid="stSidebar"] > div { background: linear-gradient(180deg, #EAF5F6 0%, #F4F8FB 100%); border-right: 1px solid var(--dd-line); }
section[data-testid="stSidebar"] h2 { color: var(--dd-ink); }
div[data-testid="stFileUploader"], div[data-testid="stTextArea"] textarea,
div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] > div,
div[data-testid="stMultiSelect"] > div { border-radius: 10px; }
div[data-testid="stTextArea"] textarea { border-color: #C9DCE2; background: rgba(255,255,255,.9); }
div[data-testid="stTextArea"] textarea:focus { border-color: var(--dd-teal); box-shadow: 0 0 0 2px rgba(8,127,140,.14); }

.stButton > button, .stDownloadButton > button {
  border-radius: 10px;
  min-height: 2.65rem;
  font-weight: 600;
  transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover { transform: translateY(-1px); box-shadow: 0 5px 14px rgba(23,50,77,.12); }
.stButton > button[kind="primary"] { border: 0; background: linear-gradient(110deg, #087F8C, #0A687A); color: #fff; }
.stButton > button[kind="primary"]:hover { background: linear-gradient(110deg, #066C78, #075A6A); }

.stTabs [data-baseweb="tab-list"] { gap: 8px; border-bottom: 1px solid var(--dd-line); }
.stTabs [data-baseweb="tab"] { border-radius: 9px 9px 0 0; padding: 10px 16px; font-weight: 600; }
.stTabs [aria-selected="true"] { color: var(--dd-teal); }
div[data-testid="stExpander"] { background: rgba(255,255,255,.82); border: 1px solid var(--dd-line); border-radius: 12px; }
div[data-testid="stDataFrame"] { border: 1px solid var(--dd-line); border-radius: 12px; overflow: hidden; }

@media (max-width: 640px) {
  .block-container { padding-top: 1rem; }
  .dd-hero { padding: 25px 22px; border-radius: 15px; }
}
@media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
</style>"""


def setup(title="Dependency Detective"):
    st.set_page_config(page_title=title, page_icon="🔎", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)


def hero():
    st.markdown("""<div class="dd-hero"><div class="dd-kicker">Python supply-chain check</div><h1>Dependency Detective</h1>
    <p>Check a Python <code>requirements.txt</code> against public vulnerability records. Findings come with their
    source; anything we could not check is listed separately instead of being called safe.</p></div>""", unsafe_allow_html=True)


def stat(col, value, label, color):
    col.markdown(f'<div class="dd-stat" style="--c:{color}"><div class="n">{value}</div><div class="l">{label}</div></div>',
                 unsafe_allow_html=True)


def badge(text, color):
    return f'<span class="dd-badge" style="--c:{color}">{text}</span>'


def sev_color(sev: str) -> str:
    return SEV.get(sev.split()[0], "#667085")
