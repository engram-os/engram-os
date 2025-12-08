import streamlit as st
import requests
import os
import sys
from datetime import datetime


from agents.logger import get_recent_logs


API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Engram",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed"
)


custom_css = """
<style>
    
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #1F1F1F;
    }
    
    
    .stApp { 
        background-color: #FAFAF9; /* Very subtle stone/white */
        margin-top: -40px; 
    }

    #MainMenu, header, footer {visibility: hidden;}

    
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlock"] {
        background-color: #FFFFFF;
        border: 1px solid #F0F0F0;
        border-radius: 16px;
        padding: 32px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.01), 0 2px 4px -1px rgba(0, 0, 0, 0.01);
        min-height: 70vh; /* Force it to look substantial */
    }

    
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 1px solid #E5E5E5;
        padding: 12px 16px;
        font-size: 16px;
        background-color: #FFFFFF;
        transition: all 0.2s;
    }
    .stTextInput > div > div > input:focus {
        border-color: #333333; 
        box-shadow: 0 0 0 1px #333333;
    }

    
    button[kind="primary"] {
        border-radius: 8px;
        font-weight: 500;
        background-color: #18181B; 
        color: #FFFFFF;
        border: 1px solid #18181B;
        transition: all 0.2s;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    button[kind="primary"]:hover {
        background-color: #27272A;
        border-color: #27272A;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    
    button[kind="secondary"] {
        border-radius: 8px;
        border: 1px solid #E4E4E7;
        background-color: #FFFFFF;
        color: #52525B;
        font-weight: 500;
    }
    button[kind="secondary"]:hover {
        border-color: #D4D4D8;
        background-color: #FAFAFA;
        color: #18181B;
    }

    
    .badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-right: 8px;
    }
    .badge-green { background-color: #ECFDF5; color: #047857; }
    .badge-blue  { background-color: #EFF6FF; color: #1D4ED8; }
    .badge-red   { background-color: #FEF2F2; color: #B91C1C; }
    .badge-gray  { background-color: #F4F4F5; color: #52525B; }
    .badge-orange{ background-color: #FFF7ED; color: #C2410C; }

    .log-entry {
        padding: 14px 0;
        border-bottom: 1px solid #F4F4F5;
        font-size: 14px;
        line-height: 1.6;
    }
    .log-meta {
        font-size: 11px;
        color: #A1A1AA;
        margin-bottom: 6px;
        font-family: 'Monaco', monospace;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)


col_margin_l, col_main, col_feed, col_margin_r = st.columns([1, 6, 3, 1], gap="large")


with col_main:
    col_title, col_status = st.columns([10, 3])
    
    with col_title:
        st.markdown("### Engram OS")

        
    with col_status:
        if os.path.exists("token.json"):
            st.markdown('<div style="text-align: right; color: #10B981; font-size: 12px; font-weight: 600; padding-top: 10px;">● ONLINE</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align: right; color: #EF4444; font-size: 12px; font-weight: 600; padding-top: 10px;">● OFFLINE</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    

    st.markdown("#### Command Center")
    user_input = st.text_input("Input", placeholder="Type a memory, task, or question...", label_visibility="collapsed")
    
    st.markdown("###") 


    b_col1, b_col2 = st.columns([1, 3])
    with b_col1:
        save_btn = st.button("Save Memory", use_container_width=True)
    with b_col2:
        ask_btn = st.button("Generate Response", type="primary", use_container_width=True)
    

    if save_btn and user_input:
        try:
            res = requests.post(f"{API_URL}/ingest", json={"text": user_input})
            if res.status_code == 200:
                st.toast("Memory saved to Second Brain.")
        except:
            st.error("System Offline")
    
    if ask_btn and user_input:
        try:
            with st.spinner("Processing..."):
                res = requests.post(f"{API_URL}/chat", json={"text": user_input})
                if res.status_code == 200:
                    data = res.json()
                    
                   
                    st.markdown("---")
                    st.markdown("#### Result")
                    st.success(data['reply'], icon="🤖")
                    
                    with st.expander("View Context Sources"):
                        st.json(data['context_used'])
        except:
            st.error("System Offline")

    
    st.markdown("---")
    with st.expander("Advanced Controls"):
        st.caption("Manual Agent Triggers")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Trigger Calendar Agent", use_container_width=True):
                requests.post(f"{API_URL}/run-agents/calendar")
                st.toast("Calendar Agent started")
        with c2:
            if st.button("Trigger Email Agent", use_container_width=True):
                requests.post(f"{API_URL}/run-agents/email")
                st.toast("Email Agent started")


with col_feed:
    st.markdown("#### Activity Feed")
    

    if st.button("Refresh", key="refresh_feed", use_container_width=True):
        st.rerun()
    
    st.markdown("---")
    
    logs = get_recent_logs(15)
    
    if not logs:
        st.markdown("""
            <div style="text-align: center; color: #9CA3AF; padding: 40px;">
                No recent activity.
            </div>
        """, unsafe_allow_html=True)
    else:
        for timestamp, agent, action, details in logs:

            badge_class = "badge-gray"
            if action == "TOOL_USE": badge_class = "badge-green"
            elif action == "DECISION": badge_class = "badge-orange"
            elif action == "ERROR": badge_class = "badge-red"
            elif action == "WAKE_UP": badge_class = "badge-blue"


            time_obj = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            time_str = time_obj.strftime("%H:%M")


            st.markdown(
                f"""
                <div class="log-entry">
                    <div class="log-meta">{time_str} • {agent}</div>
                    <div><span class="badge {badge_class}">{action}</span> <span style="color: #374151;">{details}</span></div>
                </div>
                """, 
                unsafe_allow_html=True
            )