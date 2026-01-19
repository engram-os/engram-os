import streamlit as st
import requests
import os
import sys
from datetime import datetime
from PIL import Image

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
    
    .stApp { background-color: #F3F4F6; }
    #MainMenu, header, footer {visibility: hidden;}
    
    h1, h2, h3 { font-family: 'Inter', sans-serif; font-weight: 600; color: #111827; letter-spacing: -0.5px; }
    p, div { font-family: 'Inter', sans-serif; color: #374151; }
    
    .stTextInput > div > div > input {
        border: 1px solid #E5E7EB; border-radius: 12px; padding: 16px; font-size: 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .stTextInput > div > div > input:focus { border-color: #000000; box-shadow: 0 0 0 1px #000000; }
    
    .log-item { padding: 10px 0; border-bottom: 1px solid #F3F4F6; font-size: 13px; }
    .log-time { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #9CA3AF; margin-bottom: 2px; }
    
    .badge { padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; text-transform: uppercase; display: inline-block; margin-right: 6px; }
    .badge-green { background: #DCFCE7; color: #166534; }
    .badge-blue { background: #DBEAFE; color: #1E40AF; }
    .badge-red { background: #FEE2E2; color: #991B1B; }
    .badge-gray { background: #F3F4F6; color: #4B5563; }
</style>
""", unsafe_allow_html=True)

main_col, feed_col = st.columns([1.5, 1], gap="large")

with main_col:
    c1, c2 = st.columns([5, 1])
    with c1: st.title("Engram OS")
    with c2:
        try:
            requests.get(f"{API_URL}/", timeout=0.1)
            st.markdown('<div style="color:#059669; font-weight:600; text-align:right; padding-top:20px;">● ONLINE</div>', unsafe_allow_html=True)
        except:
            st.markdown('<div style="color:#DC2626; font-weight:600; text-align:right; padding-top:20px;">● OFFLINE</div>', unsafe_allow_html=True)

    st.markdown("###") 
    user_input = st.text_input("Input", placeholder="What can I do for you?", label_visibility="collapsed")
    st.markdown("###") 

    b1, b2, b3 = st.columns([1, 1, 3])
    with b1: save_btn = st.button("📥 Save Memory", use_container_width=True)
    with b2: chat_btn = st.button("✨ Chat", type="primary", use_container_width=True)

    if save_btn and user_input:
        try:
            requests.post(f"{API_URL}/ingest", json={"text": user_input})
            st.toast("Memory saved successfully!", icon="✅")
        except: st.error("Could not connect to Brain.")

    if chat_btn and user_input:
        with st.spinner("Processing..."):
            try:
                res = requests.post(f"{API_URL}/chat", json={"text": user_input})
                if res.status_code == 200:
                    data = res.json()
                    st.success(data['reply'], icon="🤖")
                    with st.expander("View Context"): st.json(data['context_used'])
            except: st.error("Brain is offline.")

    st.markdown("---")
    with st.expander("🔧 System Controls"):
        c_a, c_b = st.columns(2)
        with c_a:
            if st.button("Trigger Calendar Agent", use_container_width=True):
                requests.post(f"{API_URL}/run-agents/calendar")
                st.toast("Calendar Agent Started")
        with c_b:
            if st.button("Trigger Email Agent", use_container_width=True):
                requests.post(f"{API_URL}/run-agents/email")
                st.toast("Email Agent Started")

with feed_col:
    f_head, f_btn = st.columns([3, 1])
    with f_head: st.subheader("Activity Feed")
    with f_btn: 
        if st.button("↻", key="refresh"): st.rerun()

    with st.container(height=600):
        logs = get_recent_logs(20)
        if not logs: st.caption("No recent activity found.")
        
        for timestamp, agent, action, details in logs:
            badge_class = "badge-gray"
            if action == "TOOL_USE": badge_class = "badge-green"
            elif action == "ERROR": badge_class = "badge-red"
            elif action == "WAKE_UP": badge_class = "badge-blue"
            
            try:
                dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                nice_time = dt.strftime("%H:%M")
            except: nice_time = timestamp

            st.markdown(f"""
            <div class="log-item">
                <div class="log-time">{nice_time} • {agent}</div>
                <div><span class="badge {badge_class}">{action}</span> <span style="color: #1F2937;">{details}</span></div>
            </div>
            """, unsafe_allow_html=True)