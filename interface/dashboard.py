"""interface/dashboard.py — Engram OS Dashboard"""
import streamlit as st
import requests
import os
import sys
import html as _esc
from datetime import datetime
from PIL import Image

try:
    from streamlit_javascript import st_javascript
    JS_AVAILABLE = True
except ImportError:
    JS_AVAILABLE = False

try:
    from zoneinfo import ZoneInfo
    def _local(dt, tz): return dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo(tz))
except ImportError:
    import pytz
    def _local(dt, tz): return pytz.utc.localize(dt).astimezone(pytz.timezone(tz))

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from agents.logger import get_recent_logs
from core.schemas import ChatResponse

# ─── Constants ────────────────────────────────────────────────────────────────

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir    = os.path.dirname(current_dir)

try:
    icon_image = Image.open(os.path.join(root_dir, "screenshots", "E-Icon.png"))
except Exception:
    icon_image = "🧠"

API_URL     = "http://ai_os_api:8000"
_api_key    = os.getenv("ENGRAM_API_KEY", "")
API_HEADERS = {"X-API-Key": _api_key} if _api_key else {}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get(path: str, timeout: int = 5) -> dict:
    try:
        r = requests.get(f"{API_URL}{path}", headers=API_HEADERS, timeout=(3, timeout))
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}


def _matter_payload() -> dict:
    mid = st.session_state.get("active_matter_id")
    return {"matter_id": mid} if mid else {}


def _fmt_time(ts: str) -> str:
    try:
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        tz = st.session_state.get("user_tz")
        return _local(dt, tz).strftime("%H:%M") if tz else dt.strftime("%H:%M")
    except Exception:
        return ts


# ─── Theme ────────────────────────────────────────────────────────────────────
# Sidebar colors are part of each theme dict (sb_*) so the toggle controls both
# the main area and the sidebar in one pass.

LIGHT = dict(
    bg       = "#FAFAF9",
    card     = "#FFFFFF",
    text     = "#0D0D0D",
    muted    = "#6E6E73",
    border   = "#E8E8E8",
    user_bg  = "#F4F4F4",
    ai_bg    = "transparent",
    inp_bg   = "#FFFFFF",
    send_bg  = "#0D0D0D",
    send_fg  = "#FFFFFF",
    primary  = "#0D0D0D",
    # sidebar
    sb_bg    = "#F0F0EF",
    sb_txt   = "#111111",
    sb_mute  = "#666666",
    sb_bdr   = "#DEDEDE",
    sb_sel   = "#E8E8E8",
    # feed badges
    b_tool   = ("#D4EDDA", "#1A5C36"),
    b_err    = ("#F8D7DA", "#842029"),
    b_wake   = ("#D0E8FF", "#0051A2"),
    b_skip   = ("#FFF3CD", "#856404"),
    b_def    = ("#EBEBEB", "#555555"),
    toggle   = "Dark",
)

DARK = dict(
    bg       = "#212121",
    card     = "#2A2A2A",
    text     = "#ECECEC",
    muted    = "#AAAAAA",
    border   = "#383838",
    user_bg  = "#2F2F2F",
    ai_bg    = "transparent",
    inp_bg   = "#2C2C2C",
    send_bg  = "#D0D0D0",
    send_fg  = "#0D0D0D",
    primary  = "#ECECEC",
    # sidebar
    sb_bg    = "#1C1C1E",
    sb_txt   = "#F5F5F5",
    sb_mute  = "#8E8EA0",
    sb_bdr   = "#3A3A3C",
    sb_sel   = "#2C2C2E",
    # feed badges
    b_tool   = ("#1A3B26", "#6EE7A0"),
    b_err    = ("#3B1010", "#F28B8B"),
    b_wake   = ("#0D2A4A", "#7EC8F5"),
    b_skip   = ("#3B2800", "#F5C842"),
    b_def    = ("#333333", "#AAAAAA"),
    toggle   = "Light",
)


def T() -> dict:
    return DARK if st.session_state.get("dark_mode") else LIGHT


# ─── CSS ──────────────────────────────────────────────────────────────────────

def _css(t: dict) -> None:
    # Inject all theme tokens (main area + sidebar) as CSS variables.
    st.markdown(f"""
<style>
:root {{
    --bg:      {t['bg']};
    --card:    {t['card']};
    --txt:     {t['text']};
    --muted:   {t['muted']};
    --border:  {t['border']};
    --userbg:  {t['user_bg']};
    --aibg:    {t['ai_bg']};
    --inpbg:   {t['inp_bg']};
    --sendbg:  {t['send_bg']};
    --sendfg:  {t['send_fg']};
    --primary: {t['primary']};

    --sb-bg:   {t['sb_bg']};
    --sb-txt:  {t['sb_txt']};
    --sb-mute: {t['sb_mute']};
    --sb-bdr:  {t['sb_bdr']};
    --sb-sel:  {t['sb_sel']};
}}
</style>
""", unsafe_allow_html=True)

    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

/* ── Reset ── */
html, body, .stApp {
    background: var(--bg) !important;
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    color: var(--txt) !important;
}
* { box-sizing: border-box; }

/* ── Hide Streamlit chrome but keep sidebar toggle ── */
#MainMenu, footer { visibility: hidden; }
header { background: transparent !important; border-bottom: none !important; box-shadow: none !important; }
header [data-testid="stToolbar"],
header [data-testid="stDecoration"],
header [data-testid="stStatusWidget"],
header [data-testid="stToolbarActions"] { visibility: hidden !important; }

/* ── Main container ── */
.main .block-container {
    padding: 1.5rem 2rem 1rem !important;
    max-width: 1600px !important;
}

/* ── Sidebar — always dark ── */
section[data-testid="stSidebar"] {
    background: var(--sb-bg) !important;
    border-right: 1px solid var(--sb-bdr) !important;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] .stCaption {
    color: var(--sb-txt) !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── All buttons: default ── */
.stButton > button {
    background: transparent !important;
    color: var(--muted) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    font-family: 'Inter', sans-serif !important;
    padding: 0.4rem 0.9rem !important;
    transition: all 0.12s ease !important;
    box-shadow: none !important;
}
.stButton > button:hover {
    border-color: var(--txt) !important;
    color: var(--txt) !important;
}

/* ── Primary button ── */
.stButton > button[kind="primary"] {
    background: var(--sendbg) !important;
    color: var(--sendfg) !important;
    border: none !important;
}
.stButton > button[kind="primary"]:hover {
    opacity: 0.85 !important;
}

/* ── Sidebar buttons — light on dark background ── */
section[data-testid="stSidebar"] .stButton > button {
    color: var(--sb-mute) !important;
    border-color: var(--sb-bdr) !important;
    background: transparent !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    color: var(--sb-txt) !important;
    border-color: var(--sb-txt) !important;
    background: var(--sb-bdr) !important;
}

/* ── Text input ── */
.stTextInput > div > div > input {
    background: var(--inpbg) !important;
    color: var(--txt) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    font-size: 0.9rem !important;
    font-family: 'Inter', sans-serif !important;
    padding: 0.6rem 0.9rem !important;
    box-shadow: none !important;
    outline: none !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--txt) !important;
    box-shadow: none !important;
}
.stTextInput > div > div > input::placeholder {
    color: var(--muted) !important;
    opacity: 1 !important;
}
.stTextInput > label { display: none !important; }

/* ── Sidebar text inputs — explicit dark/light override ── */
section[data-testid="stSidebar"] .stTextInput > div > div > input {
    background: var(--sb-sel) !important;
    color: var(--sb-txt) !important;
    border-color: var(--sb-bdr) !important;
}
section[data-testid="stSidebar"] .stTextInput > div > div > input::placeholder {
    color: var(--sb-mute) !important;
    opacity: 1 !important;
}

/* ── Sidebar expander header text ── */
section[data-testid="stSidebar"] .streamlit-expanderHeader,
section[data-testid="stSidebar"] .streamlit-expanderHeader p,
section[data-testid="stSidebar"] details summary p,
section[data-testid="stSidebar"] [data-testid="stExpanderToggleIcon"] {
    color: var(--sb-txt) !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Sidebar caption / label elements (covers st.caption, st.markdown inside expanders) ── */
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] .stCaption p,
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
    color: var(--sb-mute) !important;
}

/* ── Sidebar selectbox selected value text ── */
section[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] span,
section[data-testid="stSidebar"] .stSelectbox > div > div > div {
    color: var(--sb-txt) !important;
}

/* ── Selectbox ── */
.stSelectbox > div > div {
    background: var(--inpbg) !important;
    color: var(--txt) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
}
section[data-testid="stSidebar"] .stSelectbox > div > div {
    background: var(--sb-sel) !important;
    border-color: var(--sb-bdr) !important;
    color: var(--sb-txt) !important;
}
.stSelectbox > label { display: none !important; }

/* ── Expander ── */
.streamlit-expanderHeader {
    background: transparent !important;
    color: var(--sb-mute) !important;
    border: 1px solid var(--sb-bdr) !important;
    border-radius: 8px !important;
    font-size: 0.82rem !important;
}
.streamlit-expanderContent {
    background: transparent !important;
    border: 1px solid var(--sb-bdr) !important;
    border-top: none !important;
    border-radius: 0 0 8px 8px !important;
}

/* ── Dividers ── */
hr { border-color: var(--border) !important; }
section[data-testid="stSidebar"] hr { border-color: var(--sb-bdr) !important; }

/* ── Caption text ── */
.stCaption { color: var(--muted) !important; font-size: 0.75rem !important; }
section[data-testid="stSidebar"] .stCaption { color: var(--sb-mute) !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

/* ── Success / error alerts ── */
.stAlert { border-radius: 8px !important; font-size: 0.82rem !important; }

/* ── Code blocks ── */
.stCode { font-size: 0.78rem !important; border-radius: 6px !important; }

/* ── Dataframe ── */
.stDataFrame { border-radius: 8px !important; overflow: hidden; }
</style>
""", unsafe_allow_html=True)


# ─── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Engram OS",
    page_icon=icon_image,
    layout="wide",
    initial_sidebar_state="expanded",
)

for k, v in [("dark_mode", False), ("messages", []), ("active_matter_id", None), ("user_tz", None)]:
    st.session_state.setdefault(k, v)

t = T()
_css(t)

# ─── Passphrase ───────────────────────────────────────────────────────────────

_PP = os.getenv("DASHBOARD_PASSPHRASE", "")
if _PP and not st.session_state.get("authenticated"):
    st.text_input("Passphrase", type="password", key="pp")
    if st.button("Unlock", type="primary") and st.session_state.get("pp") == _PP:
        st.session_state["authenticated"] = True
        st.rerun()
    elif st.session_state.get("pp") and st.session_state.get("pp") != _PP:
        st.error("Incorrect passphrase.")
    st.stop()

# ─── Timezone ─────────────────────────────────────────────────────────────────

if JS_AVAILABLE:
    tz = st_javascript("Intl.DateTimeFormat().resolvedOptions().timeZone")
    if isinstance(tz, str) and tz:
        st.session_state["user_tz"] = tz

# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    # Wordmark
    st.markdown(
        f'<div style="padding: 0.75rem 0 1rem;">'
        f'<div style="font-size:1rem; font-weight:600; color:{t["sb_txt"]}; letter-spacing:-0.2px;">Engram</div>'
        f'<div style="font-size:0.7rem; color:{t["sb_mute"]}; margin-top:1px;">AI Operating System</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Theme toggle — always visible: light text on dark sidebar
    if st.button(f"{t['toggle']} mode", key="theme_toggle", use_container_width=True):
        st.session_state["dark_mode"] = not st.session_state["dark_mode"]
        st.rerun()

    st.divider()

    # Matter selector
    st.caption("ACTIVE MATTER")

    matters_resp  = _get("/api/matters")
    matters       = matters_resp.get("matters", [])
    matter_labels = {"All memories": None, **{m["name"]: m["id"] for m in matters}}

    sel = st.selectbox("matter", list(matter_labels.keys()), key="matter_selector", label_visibility="collapsed")
    st.session_state["active_matter_id"] = matter_labels[sel]

    st.divider()

    # Matter management
    with st.expander("Manage matters"):
        nm = st.text_input("Name", key="new_matter", placeholder="e.g. Prior Auth — Alice J.")
        if st.button("Create", key="create_matter", type="primary"):
            if nm.strip():
                try:
                    r = requests.post(f"{API_URL}/api/matters", params={"name": nm.strip()}, headers=API_HEADERS, timeout=(5, 10))
                    (st.success(f"Created '{nm}'") or st.rerun()) if r.status_code == 200 else st.error(r.text)
                except Exception:
                    st.error("Cannot reach API.")
        if matters:
            st.markdown("---")
            st.caption("Close a matter")
            co = {m["name"]: m["id"] for m in matters}
            cl = st.selectbox("Close", list(co.keys()), key="close_sel")
            cf = st.text_input("Type name to confirm", key="close_confirm")
            if st.button("Close", key="close_matter"):
                if cf == cl:
                    try:
                        r = requests.post(f"{API_URL}/api/matters/{co[cl]}/close", headers=API_HEADERS, timeout=(5, 30))
                        if r.status_code == 200:
                            st.success(f"Closed. {r.json().get('deleted_points', 0)} records removed.")
                            st.rerun()
                        else:
                            st.error(r.text)
                    except Exception:
                        st.error("Cannot reach API.")
                else:
                    st.warning("Name doesn't match.")

    # Memory deletion
    with st.expander("Delete memories"):
        # ── Single delete ──────────────────────────────────────────────────
        st.caption("SINGLE MEMORY")
        del_id = st.text_input(
            "Point ID", key="del_point_id",
            placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        )
        del_ok = st.checkbox("Confirm — this cannot be undone", key="del_confirm_single")
        if st.button("Delete", key="del_single_btn"):
            if not del_id.strip():
                st.warning("Enter a point ID.")
            elif not del_ok:
                st.warning("Check the confirmation box.")
            else:
                try:
                    r = requests.delete(
                        f"{API_URL}/api/memory/{del_id.strip()}",
                        headers=API_HEADERS, timeout=(5, 10),
                    )
                    if r.status_code == 200:
                        st.toast("Memory deleted.")
                        st.rerun()
                    elif r.status_code == 404:
                        st.error("Memory not found.")
                    elif r.status_code == 403:
                        st.error("Access denied.")
                    else:
                        st.error(r.text)
                except Exception:
                    st.error("Cannot reach API.")

        # ── Batch delete ───────────────────────────────────────────────────
        if matters:
            st.markdown("---")
            st.caption("BATCH DELETE BY MATTER")
            dm = {m["name"]: m["id"] for m in matters}
            dl = st.selectbox("Matter", list(dm.keys()), key="del_matter_sel")
            dt = st.selectbox(
                "Type",
                ["all", "file_ingest", "raw_ingestion", "browsing_event", "explicit_memory"],
                key="del_type_sel",
            )
            dc = st.text_input(
                "Type matter name to confirm", key="del_batch_confirm",
                placeholder=dl,
            )
            if st.button("Delete all", key="del_batch_btn"):
                if dc != dl:
                    st.warning("Name doesn't match.")
                else:
                    try:
                        params = {"matter_id": dm[dl]}
                        if dt != "all":
                            params["type"] = dt
                        r = requests.delete(
                            f"{API_URL}/api/memories",
                            params=params, headers=API_HEADERS, timeout=(5, 30),
                        )
                        if r.status_code == 200:
                            st.toast("Batch deleted.")
                            st.rerun()
                        else:
                            st.error(r.text)
                    except Exception:
                        st.error("Cannot reach API.")

    # Admin users
    me = _get("/api/me")
    if me.get("role") == "admin":
        with st.expander("Users"):
            un = st.text_input("Display name", key="new_user_name")
            ur = st.selectbox("Role", ["user", "admin"], key="new_user_role")
            if st.button("Create user", key="create_user", type="primary"):
                if un.strip():
                    try:
                        r = requests.post(f"{API_URL}/api/users", params={"display_name": un.strip(), "role": ur}, headers=API_HEADERS, timeout=(5, 10))
                        if r.status_code == 200:
                            d = r.json()
                            st.success(f"Created '{d['display_name']}'")
                            st.code(d["api_key"])
                            st.caption("Key shown once only.")
                        else:
                            st.error(r.text)
                    except Exception:
                        st.error("Cannot reach API.")
            users = _get("/api/users").get("users", [])
            if users:
                st.markdown("---")
                st.dataframe([{"name": u["display_name"], "role": u["role"]} for u in users], use_container_width=True, hide_index=True)

# ─── Main layout ──────────────────────────────────────────────────────────────

col_chat, col_feed = st.columns([13, 9], gap="large")

# ══ CHAT ══════════════════════════════════════════════════════════════════════

with col_chat:
    # Active matter indicator
    if st.session_state["active_matter_id"]:
        st.markdown(
            f'<div style="font-size:0.72rem; color:{t["muted"]}; margin-bottom:0.6rem; '
            f'font-weight:500; letter-spacing:0.01em;">'
            f'<span style="display:inline-block; width:6px; height:6px; background:{t["send_bg"]}; '
            f'border-radius:50%; margin-right:6px; vertical-align:middle;"></span>'
            f'{_esc.escape(sel)}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Message window
    chat_box = st.container(height=500)
    with chat_box:
        if not st.session_state["messages"]:
            st.markdown(
                f'<div style="height:280px; display:flex; flex-direction:column; '
                f'align-items:center; justify-content:center; gap:0.5rem; text-align:center;">'
                f'<div style="font-size:1.5rem; font-weight:300; color:{t["text"]}; letter-spacing:-0.5px;">Engram</div>'
                f'<div style="font-size:0.85rem; color:{t["muted"]}; max-width:300px; line-height:1.6;">'
                f'Ask a question or save a memory. Responses draw on encrypted, matter-isolated context.</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            for msg in st.session_state["messages"]:
                safe = _esc.escape(msg["text"])
                ts   = msg.get("time", "")

                if msg["role"] == "user":
                    st.markdown(
                        f'<div style="display:flex; justify-content:flex-end; margin:0.35rem 0 0.1rem;">'
                        f'<div style="background:{t["user_bg"]}; color:{t["text"]}; '
                        f'border-radius:14px 14px 3px 14px; padding:0.6rem 0.95rem; '
                        f'max-width:68%; font-size:0.88rem; line-height:1.6;">'
                        f'{safe}</div></div>'
                        f'<div style="text-align:right; padding-right:2px; margin-bottom:0.5rem;">'
                        f'<span style="font-size:0.65rem; color:{t["muted"]};">{ts}</span></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    clf = msg.get("classification", "")
                    clf_html = ""
                    if clf in ("PHI", "PII", "RESTRICTED"):
                        clf_html = f'<span style="background:#FEE2E2;color:#B91C1C;padding:1px 6px;border-radius:3px;font-size:0.6rem;font-weight:700;letter-spacing:0.05em;text-transform:uppercase;margin-left:8px;">{_esc.escape(clf)}</span>'
                    elif clf == "CONFIDENTIAL":
                        clf_html = f'<span style="background:#FEF9C3;color:#A16207;padding:1px 6px;border-radius:3px;font-size:0.6rem;font-weight:700;letter-spacing:0.05em;text-transform:uppercase;margin-left:8px;">{_esc.escape(clf)}</span>'

                    st.markdown(
                        f'<div style="display:flex; align-items:flex-start; gap:0.7rem; margin:0.35rem 0 0.1rem;">'
                        f'<div style="width:24px; height:24px; background:{t["text"]}; border-radius:50%; '
                        f'display:flex; align-items:center; justify-content:center; flex-shrink:0; margin-top:3px;">'
                        f'<span style="font-size:10px; font-weight:700; color:{t["bg"]};">E</span></div>'
                        f'<div style="font-size:0.88rem; line-height:1.7; color:{t["text"]}; max-width:84%;">{safe}</div>'
                        f'</div>'
                        f'<div style="padding-left:2.4rem; margin-bottom:0.5rem;">'
                        f'<span style="font-size:0.65rem; color:{t["muted"]};">{ts}</span>{clf_html}</div>',
                        unsafe_allow_html=True,
                    )

    # ── Input ──
    st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)
    user_input = st.text_input("msg", placeholder="Message Engram...", label_visibility="collapsed", key="chat_input")

    c1, c2, c3 = st.columns([6, 4, 1])
    with c1:
        chat_btn = st.button("Send", type="primary", use_container_width=True, key="chat_btn")
    with c2:
        save_btn = st.button("Save as memory", use_container_width=True, key="save_btn")
    with c3:
        clear_btn = st.button("✕", use_container_width=True, key="clear_btn", help="Clear conversation")

    if clear_btn:
        st.session_state["messages"] = []
        st.rerun()

    if save_btn and user_input:
        try:
            r = requests.post(f"{API_URL}/ingest", json={"text": user_input, **_matter_payload()}, headers=API_HEADERS, timeout=(5, 10))
            if r.status_code == 200:
                st.session_state["messages"].append({"role": "user",   "text": user_input,        "time": datetime.now().strftime("%H:%M")})
                st.session_state["messages"].append({"role": "engram", "text": "Memory saved.",   "time": datetime.now().strftime("%H:%M"), "classification": ""})
                st.rerun()
            else:
                st.error(f"Save failed ({r.status_code})")
        except Exception:
            st.error("Cannot reach API.")

    if chat_btn and user_input:
        st.session_state["messages"].append({"role": "user", "text": user_input, "time": datetime.now().strftime("%H:%M")})
        with st.spinner(""):
            try:
                res = requests.post(f"{API_URL}/chat", json={"text": user_input, **_matter_payload()}, headers=API_HEADERS, timeout=(5, 60))
                if res.status_code == 200:
                    d = ChatResponse.model_validate(res.json())
                    st.session_state["messages"].append({"role": "engram", "text": d.reply, "time": datetime.now().strftime("%H:%M"), "classification": "", "context": d.context_used})
                else:
                    st.session_state["messages"].append({"role": "engram", "text": f"Error {res.status_code}.", "time": datetime.now().strftime("%H:%M"), "classification": ""})
            except Exception:
                st.session_state["messages"].append({"role": "engram", "text": "Engram is offline.", "time": datetime.now().strftime("%H:%M"), "classification": ""})
        st.rerun()

# ══ FEED ══════════════════════════════════════════════════════════════════════

with col_feed:
    # Section label
    st.markdown(
        f'<div style="font-size:0.72rem; font-weight:600; text-transform:uppercase; '
        f'letter-spacing:0.1em; color:{t["muted"]}; margin-bottom:0.75rem;">Agents</div>',
        unsafe_allow_html=True,
    )

    a1, a2 = st.columns(2)
    with a1:
        if st.button("Calendar", use_container_width=True, key="cal_btn"):
            try:
                requests.post(f"{API_URL}/run-agents/calendar", headers=API_HEADERS, timeout=(5, 10))
                st.toast("Calendar agent triggered")
            except Exception:
                st.toast("Cannot reach API")
    with a2:
        if st.button("Email", use_container_width=True, key="email_btn"):
            try:
                requests.post(f"{API_URL}/run-agents/email", headers=API_HEADERS, timeout=(5, 10))
                st.toast("Email agent triggered")
            except Exception:
                st.toast("Cannot reach API")

    st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)

    # Feed header
    fl, fr = st.columns([5, 1])
    with fl:
        st.markdown(
            f'<div style="font-size:0.72rem; font-weight:600; text-transform:uppercase; '
            f'letter-spacing:0.1em; color:{t["muted"]};">Activity</div>',
            unsafe_allow_html=True,
        )
    with fr:
        if st.button("↻", use_container_width=True, key="refresh_btn", help="Refresh"):
            st.rerun()

    feed_box = st.container(height=470)
    with feed_box:
        logs = get_recent_logs(40)
        if not logs:
            st.markdown(
                f'<div style="padding:3rem 0; text-align:center; color:{t["muted"]}; font-size:0.82rem; line-height:1.9;">'
                f'No activity yet.<br>Trigger an agent above.</div>',
                unsafe_allow_html=True,
            )
        else:
            def _badge(action: str) -> tuple[str, str]:
                a = str(action)
                if a == "TOOL_USE":                    return t["b_tool"]
                if a == "ERROR":                       return t["b_err"]
                if a == "WAKE_UP":                     return t["b_wake"]
                if a in ("SKIP", "WARNING"):           return t["b_skip"]
                if a in ("DELETE", "DELETE_BATCH"):    return t["b_err"]
                if a in ("WRITE", "READ"):             return t["b_tool"]
                return t["b_def"]

            for ts, agent, action, details in logs:
                bg, fg = _badge(action)
                st.markdown(
                    f'<div style="padding:0.55rem 0; border-bottom:1px solid {t["border"]};">'
                    f'<div style="font-size:0.65rem; color:{t["muted"]}; font-variant-numeric:tabular-nums; margin-bottom:3px;">'
                    f'{_esc.escape(_fmt_time(str(ts)))} &nbsp;·&nbsp; {_esc.escape(str(agent))}</div>'
                    f'<div style="display:flex; align-items:baseline; gap:0.5rem; flex-wrap:wrap;">'
                    f'<span style="background:{bg}; color:{fg}; padding:0 6px; border-radius:3px; '
                    f'font-size:0.6rem; font-weight:700; text-transform:uppercase; letter-spacing:0.05em; flex-shrink:0; line-height:1.8;">'
                    f'{_esc.escape(str(action))}</span>'
                    f'<span style="font-size:0.8rem; color:{t["text"]}; line-height:1.5;">{_esc.escape(str(details))}</span>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
