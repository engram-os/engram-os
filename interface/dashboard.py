import streamlit as st
import requests
import os
import sys
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

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
icon_path = os.path.join(root_dir, "screenshots", "E-Icon.png")

try:
    icon_image = Image.open(icon_path)
except Exception:
    icon_image = "🧠"

API_URL = "http://ai_os_api:8000"

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
            requests.post(f"{API_URL}/ingest", json={"text": user_input}, timeout=(5, 10))
            st.toast("Memory saved successfully!", icon="✅")
        except:
            st.error("Could not connect to Brain.")

    if chat_btn and user_input:
        with st.spinner("Processing..."):
            try:
                res = requests.post(f"{API_URL}/chat", json={"text": user_input}, timeout=(5, 60))
                if res.status_code == 200:
                    data = res.json()
                    st.markdown(f"""
                    <div style="background: white; padding: 20px; border-radius: 15px; margin-top: 20px; border: 1px solid #E9ECEF; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                        <b>Engram:</b> {data['reply']}
                    </div>
                    """, unsafe_allow_html=True)
                    with st.expander("View Context"):
                        st.json(data['context_used'])
            except:
                st.error("Engram is offline.")

    st.markdown("---") 

    with st.expander("System Controls"):
        c_a, c_b = st.columns(2)
        with c_a:
            if st.button("Trigger Calendar Agent", use_container_width=True, type="secondary"):
                requests.post(f"{API_URL}/run-agents/calendar", timeout=(5, 10))
                st.toast("Calendar Agent Started")
        with c_b:
            if st.button("Trigger Email Agent", use_container_width=True, type="secondary"):
                requests.post(f"{API_URL}/run-agents/email", timeout=(5, 10))
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

            st.markdown(f"""
            <div class="log-item">
                <div class="log-time">{nice_time} • {agent}</div>
                <div><span class="badge {badge_class}">{action}</span> <span style="color: #212529;">{details}</span></div>
            </div>
            """, unsafe_allow_html=True)
   