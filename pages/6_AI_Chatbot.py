import streamlit as st
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from frontend_utils.api_client import api_client
from frontend_utils.auth_state import (
    require_auth, get_token, get_current_user, render_sidebar_user_badge, render_theme_styles
)

st.set_page_config(page_title="AI Decision Advisor — CampusPredict", page_icon="🤖", layout="wide")
require_auth()
render_theme_styles()
render_sidebar_user_badge()

token = get_token()
user = get_current_user() or {}

st.markdown(
    """
    <div style="margin-bottom: 20px;">
        <h1 style="margin: 0; font-size: 1.9rem; font-weight: 800; color: #f8fafc;">
            🤖 CampusPredict AI Career & Institutional Advisor
        </h1>
        <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 0.9rem;">
            Real-time conversational intelligence for personalized placement strategies, DSA roadmaps, and campus resource insights
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Fetch user profile to display context banner
profile_res = api_client.get_student_profile(token)
profile = profile_res.get("data", {}) if profile_res.get("success") else {}

# Context Banner
cgpa_val = profile.get("cgpa", 7.8)
coding_val = profile.get("coding_score", 75.0)
backlogs_val = profile.get("backlogs", 0)
dept_val = profile.get("department_code", "CS")

st.markdown(
    f"""
    <div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.85)); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 12px; padding: 12px 18px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 1.2rem;">🧠</span>
            <span style="font-size: 0.85rem; color: #f8fafc; font-weight: 600;">Grounding Context Loaded:</span>
            <span style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; padding: 2px 8px; border-radius: 4px; font-size: 0.78rem; font-weight: 700;">{dept_val} Dept</span>
            <span style="background: rgba(16, 185, 129, 0.15); color: #34d399; padding: 2px 8px; border-radius: 4px; font-size: 0.78rem; font-weight: 700;">CGPA: {cgpa_val}</span>
            <span style="background: rgba(99, 102, 241, 0.15); color: #a5b4fc; padding: 2px 8px; border-radius: 4px; font-size: 0.78rem; font-weight: 700;">Coding: {coding_val}/100</span>
            <span style="background: {'rgba(239, 68, 68, 0.15)' if backlogs_val > 0 else 'rgba(16, 185, 129, 0.15)'}; color: {'#f87171' if backlogs_val > 0 else '#34d399'}; padding: 2px 8px; border-radius: 4px; font-size: 0.78rem; font-weight: 700;">Backlogs: {backlogs_val}</span>
        </div>
        <div style="font-size: 0.75rem; color: #64748b; font-weight: 600;">
            ● Active Advisor Mode
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Initialize Chat History in Session State
if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = [
        {
            "role": "assistant",
            "content": f"Hello **{user.get('full_name') or user.get('username')}**! I am your **CampusPredict AI Advisor**.\n\nI have loaded your academic profile and our university recruitment models. Ask me anything about improving your placement odds, preparing for technical interviews, or institutional resource forecasting!"
        }
    ]

# Suggested Query Chips
st.markdown("##### 💡 Suggested Questions")
c_chip1, c_chip2, c_chip3, c_chip4 = st.columns(4)

selected_prompt = None
with c_chip1:
    if st.button("🎯 How to raise placement odds to 90%?", use_container_width=True):
        selected_prompt = "How can I improve my placement probability above 90%?"
with c_chip2:
    if st.button("🗓️ 4-Week Coding & DSA Roadmap", use_container_width=True):
        selected_prompt = "Give me a 4-week coding and DSA study roadmap"
with c_chip3:
    if st.button("🏢 Tier-1 Tech Company Cutoffs", use_container_width=True):
        selected_prompt = "What are the cutoffs and criteria for Tier-1 technology companies?"
with c_chip4:
    if st.button("🏛️ Campus Enrollment Forecast", use_container_width=True):
        selected_prompt = "What is the projected departmental student enrollment for 2026-2027?"

# Display Conversation History
for msg in st.session_state["chat_messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Process User Input (either from chat_input or a clicked suggestion pill)
user_query = st.chat_input("Ask a question about placement preparation, cutoffs, or campus planning...")
query_to_send = selected_prompt or user_query

if query_to_send:
    # Append and display user message
    st.session_state["chat_messages"].append({"role": "user", "content": query_to_send})
    with st.chat_message("user"):
        st.markdown(query_to_send)

    # Generate assistant response from backend
    with st.chat_message("assistant"):
        with st.spinner("CampusPredict AI is formulating a data-grounded response..."):
            reply_res = api_client.chat_ai(token, message=query_to_send)
            
            if reply_res.get("success"):
                reply_payload = reply_res.get("data", {})
                reply_text = reply_payload.get("reply", "No response generated.")
                model_used = reply_payload.get("model_used", "Grounded Engine")
                
                st.markdown(reply_text)
                st.caption(f"⚡ Generated via: `{model_used}`")
                
                st.session_state["chat_messages"].append({
                    "role": "assistant",
                    "content": f"{reply_text}\n\n*Source: `{model_used}`*"
                })
            else:
                err_msg = f"❌ AI Advisor error: {reply_res.get('error')}"
                st.error(err_msg)
                st.session_state["chat_messages"].append({"role": "assistant", "content": err_msg})

st.markdown("---")
c_clear1, c_clear2 = st.columns([4, 1])
with c_clear2:
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state["chat_messages"] = [
            {
                "role": "assistant",
                "content": f"Chat history reset. How can I help you today, **{user.get('full_name') or user.get('username')}**?"
            }
        ]
        st.rerun()
