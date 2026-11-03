import streamlit as st
import plotly.graph_objects as go
import json
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from frontend_utils.api_client import api_client
from frontend_utils.auth_state import (
    require_auth, get_token, get_current_user, render_sidebar_user_badge, render_theme_styles
)

st.set_page_config(page_title="Placement Prediction Engine — CampusPredict", page_icon="🔮", layout="wide")
require_auth()
render_theme_styles()
render_sidebar_user_badge()

token = get_token()
user = get_current_user() or {}

st.markdown(
    """
    <div style="margin-bottom: 20px;">
        <h1 style="margin: 0; font-size: 1.9rem; font-weight: 800; color: #f8fafc;">
            🔮 Placement Probability & What-If Scenario Engine
        </h1>
        <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 0.9rem;">
            Interactive machine learning inference with real-time risk classification and strategic career recommendations
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Fetch student profile for default population
profile_res = api_client.get_student_profile(token)
profile = profile_res.get("data", {}) if profile_res.get("success") else {}

col_input, col_output = st.columns([1.1, 1], gap="large")

with col_input:
    st.markdown("#### ⚙️ Simulation Parameters & Architecture")

    tab_actual, tab_whatif = st.tabs(["📌 Standard Prediction", "🔄 What-If Scenario Simulator"])

    with tab_actual:
        st.markdown("##### Evaluate Candidate Readiness")
        with st.form("actual_predict_form"):
            model_sel = st.selectbox(
                "Machine Learning Classifier",
                ["XGBoost (Recommended - 98.3% F1)", "Random Forest (Ensemble - 97.9%)", "Logistic Regression (Linear - 98.1%)"],
                index=0
            )
            dept_opts = ["CS", "AI", "EC", "ME", "EE", "CE"]
            curr_dept = profile.get("department_code", "CS")
            dept_idx = dept_opts.index(curr_dept) if curr_dept in dept_opts else 0
            in_dept = st.selectbox("Department", dept_opts, index=dept_idx)

            p_cgpa = float(profile.get("cgpa", 7.8))
            p_backlogs = int(profile.get("backlogs", 0))
            p_interns = int(profile.get("internships_count", 1))
            p_projects = int(profile.get("projects_count", 2))
            p_coding = float(profile.get("coding_score", 75.0))
            p_comm = float(profile.get("communication_score", 80.0))

            c1, c2 = st.columns(2)
            with c1:
                in_cgpa = st.number_input("Cumulative CGPA", min_value=0.0, max_value=10.0, value=p_cgpa, step=0.1, format="%.2f")
                in_backlogs = st.number_input("Active Backlogs", min_value=0, max_value=15, value=p_backlogs, step=1)
                in_interns = st.number_input("Internships", min_value=0, max_value=10, value=p_interns, step=1)
            with c2:
                in_projects = st.number_input("Projects Completed", min_value=0, max_value=15, value=p_projects, step=1)
                in_coding = st.slider("Coding Score (0-100)", min_value=0.0, max_value=100.0, value=p_coding, step=1.0)
                in_comm = st.slider("Communication Score (0-100)", min_value=0.0, max_value=100.0, value=p_comm, step=1.0)

            btn_run = st.form_submit_button("🚀 Run Placement Prediction", use_container_width=True, type="primary")

    with tab_whatif:
        st.markdown("##### What-If Career Simulation")
        st.caption("Test how improving your skills or clearing backlogs impacts your probability.")
        with st.form("whatif_form"):
            wi_cgpa = st.slider("Simulated CGPA", min_value=5.0, max_value=10.0, value=min(10.0, p_cgpa + 0.5), step=0.1)
            wi_backlogs = st.selectbox("Simulated Backlogs", [0, 1, 2, 3], index=0)
            wi_interns = st.slider("Simulated Internships", min_value=0, max_value=4, value=max(1, p_interns + 1))
            wi_coding = st.slider("Target Coding Score", min_value=40.0, max_value=100.0, value=min(100.0, p_coding + 15.0), step=5.0)
            wi_comm = st.slider("Target Soft Skills Score", min_value=40.0, max_value=100.0, value=p_comm, step=5.0)
            btn_whatif = st.form_submit_button("⚡ Simulate What-If Outcome", use_container_width=True)

with col_output:
    st.markdown("#### 📊 Prediction Analytics & Intelligence")

    # Run execution logic
    if btn_run or btn_whatif:
        if btn_whatif:
            eval_cgpa = wi_cgpa
            eval_backlogs = wi_backlogs
            eval_interns = wi_interns
            eval_projects = p_projects + 1
            eval_coding = wi_coding
            eval_comm = wi_comm
            model_tag = "XGBoost"
            eval_dept = curr_dept
            is_sim = True
        else:
            eval_cgpa = in_cgpa
            eval_backlogs = in_backlogs
            eval_interns = in_interns
            eval_projects = in_projects
            eval_coding = in_coding
            eval_comm = in_comm
            model_tag = "XGBoost" if "XGBoost" in model_sel else ("RandomForest" if "Forest" in model_sel else "LogisticRegression")
            eval_dept = in_dept
            is_sim = False

        payload = {
            "cgpa": eval_cgpa,
            "backlogs": eval_backlogs,
            "internships": eval_interns,
            "projects": eval_projects,
            "coding_score": eval_coding,
            "communication_score": eval_comm,
            "department_code": eval_dept,
            "model_name": model_tag,
            "student_name": profile.get("full_name") or user.get("full_name") or user.get("username", "Student"),
            "roll_number": profile.get("roll_number", "STU0001")
        }

        with st.spinner(f"Evaluating placement probability using {model_tag}..."):
            pred_res = api_client.create_prediction(token, payload)

        if pred_res.get("success"):
            st.session_state["active_pred"] = pred_res.get("data", {})
            st.session_state["is_sim"] = is_sim
            st.success("✅ Prediction model executed and record stored in database audit trail!")
        else:
            st.error(f"❌ Prediction evaluation failed: {pred_res.get('error')}")

    # Display results
    if "active_pred" in st.session_state:
        pred_data = st.session_state["active_pred"]
        prob = float(pred_data.get("placement_probability", 0.0))
        prob_pct = round(prob * 100, 1)
        status = pred_data.get("predicted_status", "Moderate Chance")
        risk = pred_data.get("risk_level", "Moderate Risk")
        model_used = pred_data.get("model_used", "XGBoost")

        if prob >= 0.75:
            bar_color = "#10b981"
            status_bg = "rgba(16, 185, 129, 0.2)"
        elif prob >= 0.50:
            bar_color = "#f59e0b"
            status_bg = "rgba(245, 158, 11, 0.2)"
        else:
            bar_color = "#f43f5e"
            status_bg = "rgba(244, 63, 94, 0.2)"

        # Gauge Chart
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=prob_pct,
            number={"suffix": "%", "font": {"size": 48, "color": bar_color, "family": "Outfit"}},
            title={"text": "Estimated Placement Probability", "font": {"size": 13, "color": "#94a3b8"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#64748b"},
                "bar": {"color": bar_color, "thickness": 0.3},
                "bgcolor": "rgba(255, 255, 255, 0.04)",
                "borderwidth": 1,
                "bordercolor": "rgba(255, 255, 255, 0.08)",
                "steps": [
                    {"range": [0, 50], "color": "rgba(239, 68, 68, 0.12)"},
                    {"range": [50, 75], "color": "rgba(245, 158, 11, 0.12)"},
                    {"range": [75, 100], "color": "rgba(16, 185, 129, 0.12)"}
                ],
                "threshold": {
                    "line": {"color": "#38bdf8", "width": 4},
                    "thickness": 0.8,
                    "value": prob_pct
                }
            }
        ))
        fig_gauge.update_layout(
            height=250,
            margin=dict(t=30, b=10, l=30, r=30),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f8fafc")
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

        # Outcome summary badges
        st.markdown(
            f"""
            <div style="display: flex; gap: 12px; margin-bottom: 16px;">
                <div style="flex: 1; background: {status_bg}; border: 1px solid {bar_color}; border-radius: 10px; padding: 12px; text-align: center;">
                    <div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; font-weight: 700;">Classification</div>
                    <div style="font-size: 1.15rem; font-weight: 800; color: {bar_color};">{status}</div>
                </div>
                <div style="flex: 1; background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 12px; text-align: center;">
                    <div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; font-weight: 700;">Risk Category</div>
                    <div style="font-size: 1.15rem; font-weight: 800; color: #f8fafc;">{risk}</div>
                </div>
                <div style="flex: 1; background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 12px; text-align: center;">
                    <div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; font-weight: 700;">Engine</div>
                    <div style="font-size: 1.15rem; font-weight: 800; color: #38bdf8;">{model_used}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Driving Factors
        factors = pred_data.get("key_factors", [])
        if factors:
            st.markdown("##### 🔍 Influencing Driving Factors")
            for factor in factors:
                st.markdown(f"- {factor}")

        # Action Recommendations
        recs = pred_data.get("recommendations_list", [])
        if recs:
            st.markdown("##### 💡 Strategic Action Recommendations")
            for r in recs:
                st.markdown(f"- 📌 {r}")
    else:
        st.info("👈 Enter your parameters or select a scenario to run real-time machine learning prediction.")
