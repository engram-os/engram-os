import streamlit as st
import requests
import os
import sys
import html as html_escape_lib
from datetime import datetime
from PIL import Image

try:
    from streamlit_javascript import st_javascript
    JS_AVAILABLE = True
except ImportError:
    JS_AVAILABLE = False

try:
    from zoneinfo import ZoneInfo          
    def make_aware(dt, tz_name):
        return dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo(tz_name))
except ImportError:
    import pytz                            
    def make_aware(dt, tz_name):
        utc_dt = pytz.utc.localize(dt)
        return utc_dt.astimezone(pytz.timezone(tz_name))

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.logger import get_recent_logs
from core.schemas import ChatResponse

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
icon_path = os.path.join(root_dir, "screenshots", "E-Icon.png")

try:
    icon_image = Image.open(icon_path)
except Exception:
    icon_image = "🧠"

API_URL = "http://ai_os_api:8000"

# Pass the API key on every brain request if one is configured.
_api_key = os.getenv("ENGRAM_API_KEY", "")
API_HEADERS = {"X-API-Key": _api_key} if _api_key else {}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _api_get(path: str) -> dict:
    try:
        r = requests.get(f"{API_URL}{path}", headers=API_HEADERS, timeout=(5, 10))
        return r.json() if r.status_code == 200 else {}
    except requests.RequestException:
        return {}


def _active_matter_payload() -> dict:
    """Return a dict with matter_id key if a matter is selected, else empty."""
    mid = st.session_state.get("active_matter_id")
    return {"matter_id": mid} if mid else {}

st.set_page_config(
    page_title="Engram OS",
    page_icon=icon_image,
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=JetBrains+Mono:wght@500&display=swap');
    
    .stApp { background-color: #F8F9FA; } /* Lighter background */
    #MainMenu, header, footer {visibility: hidden;}

    .google-title {
        font-family: 'Product Sans', 'Roboto', sans-serif;
        font-weight: 500;
        font-size: 4.5rem;
        color: #202124;
        text-align: center;
        letter-spacing: -2px;
        margin-bottom: 20px;
        margin-top: 40px;
    }

    .stTextInput > div > div > input {
        border-radius: 50px;
        padding: 12px 25px;
        font-size: 16px;
        border: 1px solid #dfe1e5;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        color: #202124; /* Google text color */
        background-color: white;
    }

    .stTextInput > div > div > input:focus {
        outline: none; /* Removes standard browser outline */
        border-color: #dfe1e5;
        box-shadow: 0 1px 6px rgba(32,33,36,.28); /* Google's focus shadow */
    }

    .stButton > button {
        border-radius: 50px;
        padding: 12px 24px;
        font-weight: 600;
        border: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.2s;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    button[kind="primary"] {
        background-color: #619cfa !important; 
        color: white !important;
    }
    button[kind="secondary"] {
        background-color: white !important;
        color: #212529 !important;
        border: 1px solid #CED4DA !important;
    }
    
    .log-item { padding: 10px 0; border-bottom: 1px solid #E9ECEF; font-size: 13px; }
    .log-time { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #ADB5BD; margin-bottom: 2px; }
    
    .badge { padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; text-transform: uppercase; display: inline-block; margin-right: 6px; }
    .badge-green { background: #D1E7DD; color: #0F5132; }
    .badge-blue { background: #CFE2FF; color: #084298; }
    .badge-red { background: #F8D7DA; color: #842029; }
    .badge-gray { background: #E9ECEF; color: #495057; }
</style>
""", unsafe_allow_html=True)

_PASSPHRASE = os.getenv("DASHBOARD_PASSPHRASE", "")
if _PASSPHRASE:
    if not st.session_state.get("authenticated"):
        st.markdown("## Engram OS — Authentication Required")
        entered = st.text_input("Passphrase", type="password", placeholder="Enter dashboard passphrase")
        if st.button("Unlock"):
            if entered == _PASSPHRASE:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect passphrase.")
        st.stop()

# ─── Sidebar — matter selector, management, admin panel ──────────────────────

with st.sidebar:
    st.markdown("### Engram OS")

    # Fetch current user identity.
    me = _api_get("/api/me")
    is_admin = me.get("role") == "admin"

    # Matter selector.
    matters_resp = _api_get("/api/matters")
    matters = matters_resp.get("matters", [])
    matter_options = {"All (no filter)": None}
    for m in matters:
        matter_options[m["name"]] = m["id"]

    selected_label = st.selectbox(
        "Active matter",
        options=list(matter_options.keys()),
        key="matter_selector_label",
    )
    st.session_state["active_matter_id"] = matter_options[selected_label]

    # Matter management.
    with st.expander("Manage Matters"):
        new_matter_name = st.text_input("New matter name", key="new_matter_name")
        if st.button("Create matter", key="create_matter_btn"):
            if new_matter_name.strip():
                try:
                    r = requests.post(
                        f"{API_URL}/api/matters",
                        params={"name": new_matter_name.strip()},
                        headers=API_HEADERS,
                        timeout=(5, 10),
                    )
                    if r.status_code == 200:
                        st.success(f"Matter '{new_matter_name}' created.")
                        st.rerun()
                    else:
                        st.error(f"Failed: {r.text}")
                except requests.RequestException:
                    st.error("Could not connect to Brain.")

        st.markdown("---")
        st.markdown("**Close a matter** (deletes all its data):")
        close_options = {m["name"]: m["id"] for m in matters}
        if close_options:
            close_label = st.selectbox("Select matter to close", list(close_options.keys()), key="close_matter_select")
            confirm_name = st.text_input("Type matter name to confirm", key="close_confirm")
            if st.button("Close matter", key="close_matter_btn", type="secondary"):
                if confirm_name == close_label:
                    try:
                        r = requests.post(
                            f"{API_URL}/api/matters/{close_options[close_label]}/close",
                            headers=API_HEADERS,
                            timeout=(5, 30),
                        )
                        if r.status_code == 200:
                            data = r.json()
                            st.success(f"Closed. {data.get('deleted_points', 0)} points removed.")
                            st.rerun()
                        else:
                            st.error(f"Failed: {r.text}")
                    except requests.RequestException:
                        st.error("Could not connect to Brain.")
                else:
                    st.warning("Name doesn't match. Type the exact matter name to confirm.")
        else:
            st.caption("No open matters.")

    # Admin-only: user management.
    if is_admin:
        with st.expander("User Management (Admin)"):
            st.markdown("**Create user**")
            new_user_name = st.text_input("Display name", key="new_user_name")
            new_user_role = st.selectbox("Role", ["user", "admin"], key="new_user_role")
            if st.button("Create user", key="create_user_btn"):
                if new_user_name.strip():
                    try:
                        r = requests.post(
                            f"{API_URL}/api/users",
                            params={"display_name": new_user_name.strip(), "role": new_user_role},
                            headers=API_HEADERS,
                            timeout=(5, 10),
                        )
                        if r.status_code == 200:
                            data = r.json()
                            st.success(f"User '{data['display_name']}' created.")
                            st.code(data["api_key"], language=None)
                            st.caption("This API key will not be shown again.")
                        else:
                            st.error(f"Failed: {r.text}")
                    except requests.RequestException:
                        st.error("Could not connect to Brain.")

            st.markdown("---")
            st.markdown("**All users**")
            users_resp = _api_get("/api/users")
            all_users = users_resp.get("users", [])
            if all_users:
                st.dataframe(
                    [{"id": u["id"], "name": u["display_name"], "role": u["role"], "created": u.get("created_at", "")} for u in all_users],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.caption("No users in registry.")


if JS_AVAILABLE:
    tz_name = st_javascript("Intl.DateTimeFormat().resolvedOptions().timeZone")
    if isinstance(tz_name, str) and tz_name:
        st.session_state["user_tz"] = tz_name   # real value — cache it
    elif "user_tz" not in st.session_state:
        st.session_state["user_tz"] = None       # still waiting for JS
else:
    st.session_state["user_tz"] = None

user_tz = st.session_state.get("user_tz")       # None until JS resolves


def format_log_time(timestamp_str: str) -> str:
    """
    Converts a UTC timestamp string to the user's local time.
    Falls back to raw HH:MM (UTC) if conversion is unavailable.
    """
    try:
        dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        if user_tz:
            local_dt = make_aware(dt, user_tz)
            return local_dt.strftime("%H:%M")
        return dt.strftime("%H:%M")   # JS not resolved yet — show UTC time
    except Exception:
        return timestamp_str

spacer_left, center_col, spacer_right = st.columns([1, 2, 1])

with center_col:
    st.markdown('<div class="google-title">Engram OS</div>', unsafe_allow_html=True)
    user_input = st.text_input("Input", placeholder="Type a command or search...", label_visibility="collapsed")
    st.markdown("###")

    b_spacer_l, b1, b2, b_spacer_r = st.columns([1, 2, 2, 1])
    with b1:
        save_btn = st.button("Save Memory", use_container_width=True, type="secondary")
    with b2:
        chat_btn = st.button("Chat with OS", type="primary", use_container_width=True)

    if save_btn and user_input:
        try:
            payload = {"text": user_input, **_active_matter_payload()}
            requests.post(f"{API_URL}/ingest", json=payload, headers=API_HEADERS, timeout=(5, 10))
            st.toast("Memory saved successfully!", icon="✅")
        except requests.RequestException:
            st.error("Could not connect to Brain.")

    if chat_btn and user_input:
        with st.spinner("Processing..."):
            try:
                payload = {"text": user_input, **_active_matter_payload()}
                res = requests.post(f"{API_URL}/chat", json=payload, headers=API_HEADERS, timeout=(5, 60))
                if res.status_code == 200:
                    chat = ChatResponse.model_validate(res.json())
                    safe_reply = html_escape_lib.escape(chat.reply)
                    st.markdown(f"""
                    <div style="background: white; padding: 20px; border-radius: 15px; margin-top: 20px; border: 1px solid #E9ECEF; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                        <b>Engram:</b> {safe_reply}
                    </div>
                    """, unsafe_allow_html=True)
                    with st.expander("View Context"):
                        st.json(chat.context_used)
            except requests.RequestException:
                st.error("Engram is offline.")

    st.markdown("---") 

    with st.expander("System Controls"):
        c_a, c_b = st.columns(2)
        with c_a:
            if st.button("Trigger Calendar Agent", use_container_width=True, type="secondary"):
                requests.post(f"{API_URL}/run-agents/calendar", headers=API_HEADERS, timeout=(5, 10))
                st.toast("Calendar Agent Started")
        with c_b:
            if st.button("Trigger Email Agent", use_container_width=True, type="secondary"):
                requests.post(f"{API_URL}/run-agents/email", headers=API_HEADERS, timeout=(5, 10))
                st.toast("Email Agent Started")

st.markdown("###") 
f_spacer_left, f_center_col, f_spacer_right = st.columns([1, 2, 1])

with f_center_col:
    f_head, f_tz, f_btn = st.columns([3, 1, 1])
    
    with f_btn:
        if st.button("Refresh Feed", key="refresh", type="secondary"):
            st.rerun()

    with st.container(height=400):
        logs = get_recent_logs(20)
        
        for timestamp, agent, action, details in logs:
            badge_class = "badge-gray"
            if action == "TOOL_USE": badge_class = "badge-green"
            elif action == "ERROR": badge_class = "badge-red"
            elif action == "WAKE_UP": badge_class = "badge-blue"
            
            nice_time = format_log_time(timestamp)
            safe_time = html_escape_lib.escape(nice_time)
            safe_agent = html_escape_lib.escape(str(agent))
            safe_action = html_escape_lib.escape(str(action))
            safe_details = html_escape_lib.escape(str(details))

            st.markdown(f"""
            <div class="log-item">
                <div class="log-time">{safe_time} • {safe_agent}</div>
                <div><span class="badge {badge_class}">{safe_action}</span> <span style="color: #212529;">{safe_details}</span></div>
            </div>
            """, unsafe_allow_html=True)
   