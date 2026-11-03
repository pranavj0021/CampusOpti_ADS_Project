import streamlit as st
import time
import os
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from frontend_utils.api_client import api_client
from frontend_utils.auth_state import (
    init_auth_state, is_authenticated, get_current_user,
    login_user, render_sidebar_user_badge, render_theme_styles
)

st.set_page_config(
    page_title="CampusPredict — AI Student Placement & Resource Forecaster",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_auth_state()
render_theme_styles()
render_sidebar_user_badge()

# Check backend health & latency
start_ping = time.time()
health = api_client.check_health()
latency_ms = round((time.time() - start_ping) * 1000, 1)
backend_online = (health.get("status") == "healthy")

# Header & System Badge
col_brand, col_status = st.columns([3, 1])
with col_brand:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 4px;">
            <div style="background: linear-gradient(135deg, #2563eb, #06b6d4); width: 48px; height: 48px; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 26px; box-shadow: 0 6px 20px rgba(37,99,235,0.45);">
                🎓
            </div>
            <div>
                <h1 style="margin: 0; font-size: 2.1rem; font-weight: 800; color: #f8fafc; letter-spacing: -0.02em;">
                    Campus<span style="color: #38bdf8;">Predict</span>
                </h1>
                <p style="margin: 2px 0 0 0; font-size: 0.88rem; color: #94a3b8; font-weight: 500;">
                    AI-Driven Student Placement Forecasting & Smart Institutional Decision Support Platform
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
with col_status:
    if backend_online:
        st.markdown(
            f"""
            <div style="text-align: right; margin-top: 10px;">
                <span style="background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.35); color: #34d399; padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; display: inline-flex; align-items: center; gap: 6px;">
                    <span style="width: 7px; height: 7px; border-radius: 50%; background: #34d399; box-shadow: 0 0 8px #34d399;"></span>
                    API Online ({latency_ms}ms)
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div style="text-align: right; margin-top: 10px;">
                <span style="background: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.35); color: #f87171; padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 700;">
                    ○ Backend Offline
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

st.markdown("<hr style='margin: 12px 0 24px 0; border: none; border-top: 1px solid rgba(255, 255, 255, 0.08);'>", unsafe_allow_html=True)

# Main Authentication View / Dashboard Router
if not is_authenticated():
    if not backend_online:
        st.error(
            f"⚠️ **Backend Service Unreachable:** Cannot reach Flask REST API at `{api_client.base_url}`. "
            "Please ensure the backend server is running via `python backend/app.py` or `docker compose up`."
        )

    # Hero Banner with Platform Stats
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.85)); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 16px; padding: 26px 32px; margin-bottom: 28px; box-shadow: 0 8px 32px rgba(0,0,0,0.3);">
            <div style="text-align: center; max-width: 720px; margin: 0 auto;">
                <h2 style="font-size: 1.6rem; font-weight: 800; color: #ffffff; margin-bottom: 8px;">
                    Intelligent Campus Recruitment & Resource Forecasting
                </h2>
                <p style="font-size: 0.95rem; color: #94a3b8; line-height: 1.6; margin-bottom: 20px;">
                    Predict placement probabilities using trained gradient boosting models, analyze academic risk indicators, and explore university-wide resource posture.
                </p>
                <div style="display: flex; justify-content: center; gap: 24px; flex-wrap: wrap;">
                    <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 8px 18px; text-align: center;">
                        <span style="font-size: 1.25rem; font-weight: 800; color: #38bdf8;">98.3%</span>
                        <span style="display: block; font-size: 0.72rem; color: #64748b; font-weight: 600;">MODEL ACCURACY</span>
                    </div>
                    <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 8px 18px; text-align: center;">
                        <span style="font-size: 1.25rem; font-weight: 800; color: #34d399;">3 Models</span>
                        <span style="display: block; font-size: 0.72rem; color: #64748b; font-weight: 600;">XGBOOST / RF / LR</span>
                    </div>
                    <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 8px 18px; text-align: center;">
                        <span style="font-size: 1.25rem; font-weight: 800; color: #a78bfa;">Instant</span>
                        <span style="display: block; font-size: 0.72rem; color: #64748b; font-weight: 600;">REAL-TIME INFERENCE</span>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    auth_col_left, auth_col_main, auth_col_right = st.columns([1, 2.2, 1])

    with auth_col_main:
        tab_login, tab_register = st.tabs(["🔑 Sign In to Portal", "📝 Create New Student Account"])

        with tab_login:
            # Interactive Quick Fill Pills
            st.markdown("##### Sign In with Registered Account")
            
            c_fill1, c_fill2 = st.columns(2)
            with c_fill1:
                if st.button("👉 Quick-Fill Admin Account", use_container_width=True):
                    st.session_state["login_user_fill"] = "admin"
                    st.session_state["login_pwd_fill"] = "admin123"
            with c_fill2:
                if st.button("👉 Quick-Fill Student Account", use_container_width=True):
                    st.session_state["login_user_fill"] = "student_9156"
                    st.session_state["login_pwd_fill"] = "Password123!"

            fill_user = st.session_state.get("login_user_fill", "admin")
            fill_pwd = st.session_state.get("login_pwd_fill", "admin123")

            with st.form("login_form", clear_on_submit=False):
                username_input = st.text_input("Username or Email", placeholder="e.g. admin or student1", value=fill_user)
                password_input = st.text_input("Password", type="password", placeholder="Enter your password", value=fill_pwd)
                submit_login = st.form_submit_button("🚀 Sign In to Portal", use_container_width=True, type="primary")

                if submit_login:
                    if not username_input or not password_input:
                        st.error("Please enter both username and password.")
                    else:
                        with st.spinner("Authenticating credentials with CampusPredict API..."):
                            result = api_client.login(username_input.strip(), password_input)
                            if result.get("success"):
                                token = result["data"]["access_token"]
                                user_info = result["data"]["user"]
                                login_user(token, user_info)
                                st.success(f"Welcome back, **{user_info.get('full_name') or user_info.get('username')}**!")
                                st.rerun()
                            else:
                                st.error(f"Authentication Failed: {result.get('error')}")

        with tab_register:
            st.markdown("##### Register New Student or Faculty Account")
            with st.form("register_form", clear_on_submit=False):
                r1, r2 = st.columns(2)
                with r1:
                    reg_name = st.text_input("Full Name", placeholder="e.g. Priya Sharma")
                    reg_username = st.text_input("Choose Username", placeholder="e.g. priya_s")
                    reg_email = st.text_input("Email Address", placeholder="e.g. priya@campus.edu")
                with r2:
                    reg_dept = st.selectbox("Department", ["CS", "AI", "EC", "ME", "EE", "CE"])
                    reg_pwd = st.text_input("Password (min 6 chars)", type="password")
                    reg_pwd_confirm = st.text_input("Confirm Password", type="password")

                submit_register = st.form_submit_button("✨ Register & Log In", use_container_width=True, type="primary")

                if submit_register:
                    if not reg_username or not reg_email or not reg_pwd:
                        st.error("All required fields must be filled.")
                    elif len(reg_pwd) < 6:
                        st.error("Password must be at least 6 characters long.")
                    elif reg_pwd != reg_pwd_confirm:
                        st.error("Passwords do not match. Please verify.")
                    else:
                        with st.spinner("Creating verified account in CampusPredict database..."):
                            reg_result = api_client.register(
                                username=reg_username.strip(),
                                email=reg_email.strip(),
                                password=reg_pwd,
                                full_name=reg_name.strip() or reg_username.strip(),
                                role="student"
                            )
                            if reg_result.get("success"):
                                token = reg_result["data"]["access_token"]
                                user_info = reg_result["data"]["user"]
                                login_user(token, user_info)
                                st.success("Account created successfully! Logging you in...")
                                st.rerun()
                            else:
                                st.error(f"Registration Failed: {reg_result.get('error')}")

else:
    # Authenticated Command Center
    user = get_current_user() or {}
    full_name = user.get("full_name") or user.get("username", "Student")
    role = (user.get("role") or "student").capitalize()

    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.85), rgba(15, 23, 42, 0.95)); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 16px; padding: 24px 30px; margin-bottom: 28px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;">
                <div>
                    <div style="font-size: 0.78rem; font-weight: 700; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">
                        ● AUTHORIZED SESSION ACTIVE
                    </div>
                    <h2 style="margin: 0; font-size: 1.65rem; font-weight: 800; color: #f8fafc;">
                        Welcome back, {full_name}! 👋
                    </h2>
                    <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 0.92rem;">
                        Logged in as <span style="color: #f8fafc; font-weight: 600;">{role}</span> (@{user.get('username')}) • CampusPredict Intelligence Suite Ready
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("#### 🚀 Interactive Modules & Navigation")
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            """
            <div class="glass-card" style="min-height: 190px; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="font-size: 2rem; margin-bottom: 8px;">📊</div>
                    <h3 style="margin: 0; font-size: 1.15rem; color: #f8fafc; font-weight: 700;">Executive Dashboard</h3>
                    <p style="margin: 6px 0 0 0; font-size: 0.84rem; color: #94a3b8; line-height: 1.45;">
                        Live institutional metrics, campus-wide placement stats, and resource capacity posture.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Open Dashboard ➜", use_container_width=True, key="btn_nav_dashboard", type="primary"):
            st.switch_page("pages/1_Dashboard.py")

    with c2:
        st.markdown(
            """
            <div class="glass-card" style="min-height: 190px; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="font-size: 2rem; margin-bottom: 8px;">👤</div>
                    <h3 style="margin: 0; font-size: 1.15rem; color: #f8fafc; font-weight: 700;">Student Academic Profile</h3>
                    <p style="margin: 6px 0 0 0; font-size: 0.84rem; color: #94a3b8; line-height: 1.45;">
                        Interactive skill competency radar, verified CGPA, backlogs, and project tracking.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Manage Profile ➜", use_container_width=True, key="btn_nav_profile"):
            st.switch_page("pages/2_Student_Profile.py")

    with c3:
        st.markdown(
            """
            <div class="glass-card" style="min-height: 190px; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="font-size: 2rem; margin-bottom: 8px;">🔮</div>
                    <h3 style="margin: 0; font-size: 1.15rem; color: #f8fafc; font-weight: 700;">Placement Prediction</h3>
                    <p style="margin: 6px 0 0 0; font-size: 0.84rem; color: #94a3b8; line-height: 1.45;">
                        What-if scenario simulator, real-time probability meter, and action recommendations.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Run Prediction ➜", use_container_width=True, key="btn_nav_prediction", type="primary"):
            st.switch_page("pages/3_Placement_Prediction.py")

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    c4, c5, c6 = st.columns(3)

    with c4:
        st.markdown(
            """
            <div class="glass-card" style="min-height: 190px; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="font-size: 2rem; margin-bottom: 8px;">📜</div>
                    <h3 style="margin: 0; font-size: 1.15rem; color: #f8fafc; font-weight: 700;">Prediction History</h3>
                    <p style="margin: 6px 0 0 0; font-size: 0.84rem; color: #94a3b8; line-height: 1.45;">
                        Searchable database audit trail of past placement runs, probability shifts, and CSV exports.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("View History ➜", use_container_width=True, key="btn_nav_history"):
            st.switch_page("pages/4_Prediction_History.py")

    with c5:
        st.markdown(
            """
            <div class="glass-card" style="min-height: 190px; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="font-size: 2rem; margin-bottom: 8px;">📈</div>
                    <h3 style="margin: 0; font-size: 1.15rem; color: #f8fafc; font-weight: 700;">Advanced Analytics</h3>
                    <p style="margin: 6px 0 0 0; font-size: 0.84rem; color: #94a3b8; line-height: 1.45;">
                        Interactive 3D scatters, CGPA vs DSA score correlation, and department benchmarks.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Explore Analytics ➜", use_container_width=True, key="btn_nav_analytics"):
            st.switch_page("pages/5_Analytics.py")

    with c6:
        st.markdown(
            """
            <div class="glass-card" style="min-height: 190px; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="font-size: 2rem; margin-bottom: 8px;">🤖</div>
                    <h3 style="margin: 0; font-size: 1.15rem; color: #f8fafc; font-weight: 700;">AI Decision Advisor</h3>
                    <p style="margin: 6px 0 0 0; font-size: 0.84rem; color: #94a3b8; line-height: 1.45;">
                        Personalized placement strategies, DSA preparation roadmaps, and grounded campus advice.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Consult AI Advisor ➜", use_container_width=True, key="btn_nav_chatbot", type="primary"):
            st.switch_page("pages/6_AI_Chatbot.py")

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    c7, _ = st.columns([1, 2])

    with c7:
        st.markdown(
            """
            <div class="glass-card" style="min-height: 190px; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="font-size: 2rem; margin-bottom: 8px;">⚙️</div>
                    <h3 style="margin: 0; font-size: 1.15rem; color: #f8fafc; font-weight: 700;">Settings & Diagnostics</h3>
                    <p style="margin: 6px 0 0 0; font-size: 0.84rem; color: #94a3b8; line-height: 1.45;">
                        Interactive REST API tester, latency probe, database verification, and session logout.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Open Settings ➜", use_container_width=True, key="btn_nav_settings"):
            st.switch_page("pages/7_Settings_and_Logout.py")
