# pyrefly: ignore [missing-import]
import streamlit as st
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from frontend_utils.api_client import api_client
from frontend_utils.auth_state import (
    require_auth, get_token, get_current_user, logout_user,
    render_sidebar_user_badge, render_theme_styles
)

st.set_page_config(page_title="Settings & Session — CampusPredict", page_icon="⚙️", layout="wide")
require_auth()
render_theme_styles()
render_sidebar_user_badge()

token = get_token()
user = get_current_user() or {}

st.markdown(
    """
    <div style="margin-bottom: 20px;">
        <h1 style="margin: 0; font-size: 1.8rem; font-weight: 700; color: #f8fafc;">
            ⚙️ Account Settings & System Diagnostics
        </h1>
        <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 0.88rem;">
            Inspect user credentials, verify API endpoints, and manage session state
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

c1, c2 = st.columns(2, gap="large")

with c1:
    st.markdown("#### 👤 User Account Details")
    st.markdown(
        f"""
        <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 20px;">
            <p><b>User ID:</b> <code>#{user.get('id', 'N/A')}</code></p>
            <p><b>Username:</b> <code>@{user.get('username', 'N/A')}</code></p>
            <p><b>Full Name:</b> {user.get('full_name', 'N/A')}</p>
            <p><b>Email:</b> {user.get('email', 'N/A')}</p>
            <p><b>Role:</b> <span style="background: #3b82f6; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 600;">{(user.get('role') or 'student').upper()}</span></p>
            <p><b>Status:</b> <span style="color: #10b981; font-weight: 600;">● Active</span></p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    st.markdown("#### 🚪 Session Management")
    if st.button("Logout / Terminate Session", type="primary", use_container_width=True):
        api_client.logout(token)
        logout_user()
        st.success("Session terminated successfully.")
        st.switch_page("streamlit_app.py")

with c2:
    st.markdown("#### 📡 System Health & Diagnostics")
    
    health = api_client.check_health()
    backend_status = health.get("status") == "healthy"

    if backend_status:
        st.success("✅ **Flask REST API Connected**")
    else:
        st.error("❌ **Backend Unreachable**")

    st.markdown(
        f"""
        <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 20px;">
            <p><b>API Base Endpoint:</b> <code>{api_client.base_url}</code></p>
            <p><b>Backend Service:</b> {health.get('service', 'Flask Backend')}</p>
            <p><b>Version:</b> <code>{health.get('version', '2.0.0')}</code></p>
            <p><b>Database Connectivity:</b> <code>{health.get('database', 'connected')}</code></p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Re-run Health Diagnostics", use_container_width=True):
        st.rerun()
