import streamlit as st
import plotly.graph_objects as go
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from frontend_utils.api_client import api_client
from frontend_utils.auth_state import (
    require_auth, get_token, get_current_user, render_sidebar_user_badge, render_theme_styles
)

st.set_page_config(page_title="Student Academic Profile — CampusPredict", page_icon="👤", layout="wide")
require_auth()
render_theme_styles()
render_sidebar_user_badge()

token = get_token()
user = get_current_user() or {}

st.markdown(
    """
    <div style="margin-bottom: 22px;">
        <h1 style="margin: 0; font-size: 1.9rem; font-weight: 800; color: #f8fafc;">
            👤 Student Academic & Competencies Profile
        </h1>
        <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 0.9rem;">
            Maintain verified academic metrics, evaluate multi-dimensional skill radar, and simulate profile strength
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Load profile from API
with st.spinner("Fetching verified student records..."):
    res = api_client.get_student_profile(token)

if not res.get("success"):
    st.error(f"Error retrieving profile: {res.get('error')}")
    st.stop()

profile = res.get("data", {})

# Profile Strength & Radar Computation
cgpa_current = float(profile.get("cgpa", 7.8))
backlogs_current = int(profile.get("backlogs", 0))
coding_current = float(profile.get("coding_score", 75.0))
comm_current = float(profile.get("communication_score", 80.0))
interns_current = int(profile.get("internships_count", 1))
projects_current = int(profile.get("projects_count", 2))

# Quick preset selector pills
st.markdown("##### ⚡ Quick Scenario Presets")
p1, p2, p3 = st.columns(3)
with p1:
    if st.button("🏆 Load Tier-1 SDE Profile Preset", use_container_width=True):
        st.session_state["preset_cgpa"] = 9.15
        st.session_state["preset_backlogs"] = 0
        st.session_state["preset_internships"] = 2
        st.session_state["preset_projects"] = 4
        st.session_state["preset_coding"] = 92.0
        st.session_state["preset_comm"] = 88.0
        st.success("Loaded Tier-1 SDE preset values below!")
with p2:
    if st.button("🚀 Load Standard Eligible Preset", use_container_width=True):
        st.session_state["preset_cgpa"] = 7.80
        st.session_state["preset_backlogs"] = 0
        st.session_state["preset_internships"] = 1
        st.session_state["preset_projects"] = 2
        st.session_state["preset_coding"] = 75.0
        st.session_state["preset_comm"] = 80.0
        st.success("Loaded Standard Eligible preset values below!")
with p3:
    if st.button("⚠️ Load At-Risk Candidate Preset", use_container_width=True):
        st.session_state["preset_cgpa"] = 6.20
        st.session_state["preset_backlogs"] = 2
        st.session_state["preset_internships"] = 0
        st.session_state["preset_projects"] = 1
        st.session_state["preset_coding"] = 45.0
        st.session_state["preset_comm"] = 55.0
        st.warning("Loaded At-Risk Candidate preset values below!")

# Determine active form values
v_cgpa = st.session_state.get("preset_cgpa", cgpa_current)
v_backlogs = st.session_state.get("preset_backlogs", backlogs_current)
v_interns = st.session_state.get("preset_internships", interns_current)
v_projects = st.session_state.get("preset_projects", projects_current)
v_coding = st.session_state.get("preset_coding", coding_current)
v_comm = st.session_state.get("preset_comm", comm_current)

col_editor, col_visual = st.columns([1.2, 1], gap="large")

with col_editor:
    st.markdown("#### 📝 Edit Academic & Placement Attributes")
    with st.form("profile_update_form"):
        f1, f2 = st.columns(2)
        with f1:
            in_name = st.text_input("Full Name", value=profile.get("full_name") or user.get("full_name") or user.get("username", ""))
            in_roll = st.text_input("Roll / Registration No.", value=profile.get("roll_number", f"STU{user.get('id', 1):04d}"))
            dept_options = ["CS", "AI", "EC", "ME", "EE", "CE"]
            curr_dept = profile.get("department_code", "CS")
            dept_idx = dept_options.index(curr_dept) if curr_dept in dept_options else 0
            in_dept = st.selectbox("Academic Department", dept_options, index=dept_idx)
            in_cgpa = st.number_input("Cumulative CGPA (0.0 - 10.0)", min_value=0.0, max_value=10.0, value=float(v_cgpa), step=0.05, format="%.2f")

        with f2:
            in_backlogs = st.number_input("Active Backlogs / Arrears", min_value=0, max_value=20, value=int(v_backlogs), step=1)
            in_internships = st.number_input("Industry Internships", min_value=0, max_value=10, value=int(v_interns), step=1)
            in_projects = st.number_input("Major Technical Projects", min_value=0, max_value=15, value=int(v_projects), step=1)
            in_certs = st.number_input("Professional Certifications", min_value=0, max_value=15, value=int(profile.get("certifications_count", 1)), step=1)

        st.markdown("##### Technical & Interpersonal Evaluations")
        in_coding = st.slider("Coding Assessment Score (0 - 100)", min_value=0.0, max_value=100.0, value=float(v_coding), step=1.0)
        in_comm = st.slider("Communication & Soft Skills Score (0 - 100)", min_value=0.0, max_value=100.0, value=float(v_comm), step=1.0)

        submit_save = st.form_submit_button("💾 Save Profile Changes to Database", use_container_width=True, type="primary")

        if submit_save:
            payload = {
                "full_name": in_name.strip(),
                "roll_number": in_roll.strip(),
                "department_code": in_dept,
                "cgpa": in_cgpa,
                "backlogs": in_backlogs,
                "internships_count": in_internships,
                "projects_count": in_projects,
                "certifications_count": in_certs,
                "coding_score": in_coding,
                "communication_score": in_comm
            }
            with st.spinner("Persisting updates to CampusPredict SQLite database..."):
                save_res = api_client.update_student_profile(token, payload)
                if save_res.get("success"):
                    st.success("✅ Profile successfully updated and persisted in database!")
                    # Clear presets
                    for k in ["preset_cgpa", "preset_backlogs", "preset_internships", "preset_projects", "preset_coding", "preset_comm"]:
                        st.session_state.pop(k, None)
                    st.rerun()
                else:
                    st.error(f"❌ Failed to update profile: {save_res.get('error')}")

with col_visual:
    st.markdown("#### 🎯 Competency Radar & Readiness")

    # Radar Chart
    categories = ["Academic (CGPA)", "Coding Proficiency", "Communication", "Practical Projects", "Internship Exp", "Backlog Safety"]
    
    # Normalize values out of 100 for radar
    cgpa_norm = min(100.0, (in_cgpa / 10.0) * 100.0)
    coding_norm = in_coding
    comm_norm = in_comm
    proj_norm = min(100.0, in_projects * 25.0)
    intern_norm = min(100.0, in_internships * 50.0)
    backlog_safety = max(0.0, 100.0 - (in_backlogs * 35.0))

    radar_values = [cgpa_norm, coding_norm, comm_norm, proj_norm, intern_norm, backlog_safety]
    # Close the polygon
    radar_values.append(radar_values[0])
    radar_categories = categories + [categories[0]]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=radar_values,
        theta=radar_categories,
        fill="toself",
        fillcolor="rgba(56, 189, 248, 0.25)",
        line=dict(color="#38bdf8", width=2),
        name="Candidate Profile"
    ))
    # Benchmark overlay
    fig_radar.add_trace(go.Scatterpolar(
        r=[75, 70, 75, 50, 50, 100, 75],
        theta=radar_categories,
        line=dict(color="rgba(255, 255, 255, 0.3)", width=1, dash="dot"),
        name="Campus Average"
    ))

    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(color="#64748b", size=9), gridcolor="rgba(255,255,255,0.08)"),
            angularaxis=dict(tickfont=dict(color="#94a3b8", size=10), gridcolor="rgba(255,255,255,0.08)")
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f8fafc"),
        margin=dict(t=20, b=20, l=30, r=30),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    # Calculated Profile Strength Meter
    overall_strength = round(sum(radar_values[:-1]) / len(radar_values[:-1]), 1)
    st.markdown(
        f"""
        <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 16px; margin-top: 14px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 0.82rem; font-weight: 700; color: #94a3b8; text-transform: uppercase;">Overall Profile Strength Score</span>
                <span style="font-size: 1.15rem; font-weight: 800; color: {'#10b981' if overall_strength >= 75 else ('#f59e0b' if overall_strength >= 50 else '#f43f5e')};">{overall_strength}%</span>
            </div>
            <div style="background: rgba(15, 23, 42, 0.8); border-radius: 6px; height: 10px; overflow: hidden;">
                <div style="width: {overall_strength}%; background: linear-gradient(90deg, #38bdf8, {'#10b981' if overall_strength >= 75 else ('#f59e0b' if overall_strength >= 50 else '#f43f5e')}); height: 100%;"></div>
            </div>
            <div style="font-size: 0.78rem; color: #64748b; margin-top: 8px;">
                {'🌟 Outstanding: Top percentile qualification for Fortune 500 campus drives' if overall_strength >= 75 else ('⚠️ Solid: Eligible for core mass recruiters, consider boosting coding score' if overall_strength >= 50 else '🚨 High Risk: Action required on backlogs and foundational coding assessments')}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
