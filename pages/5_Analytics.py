import streamlit as st
import pandas as pd
import plotly.express as px
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

st.set_page_config(page_title="Advanced Analytics — CampusPredict", page_icon="📈", layout="wide")
require_auth()
render_theme_styles()
render_sidebar_user_badge()

token = get_token()

st.markdown(
    """
    <div style="margin-bottom: 22px;">
        <h1 style="margin: 0; font-size: 1.9rem; font-weight: 800; color: #f8fafc;">
            📈 Advanced Institutional Analytics & Predictive Models
        </h1>
        <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 0.9rem;">
            Interactive multi-variable competency correlations, departmental cohort benchmarks, and ML model performance
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Fetch data
with st.spinner("Aggregating institutional data streams..."):
    analytics_res = api_client.get_analytics(token)
    models_res = api_client.get_models_info()
    hist_res = api_client.get_prediction_history(token)

if not analytics_res.get("success"):
    st.error(f"Error loading analytics: {analytics_res.get('error')}")
    st.stop()

data = analytics_res.get("data", {})
placement_data = data.get("placement_analytics", {})
infra = data.get("campus_infrastructure", {})
hist_records = hist_res.get("data", []) if hist_res.get("success") else []

tab_multi, tab_dept, tab_models, tab_matrix = st.tabs([
    "🔬 3D Competency Correlations",
    "🏛️ Department Cohort Benchmarks",
    "🤖 ML Models & Evaluation",
    "🏢 Physical Campus Assets"
])

# -------------------------------------------------------------------
# TAB 1: 3D Competency Correlations
# -------------------------------------------------------------------
with tab_multi:
    st.markdown("##### 🌐 Multi-Dimensional Competency Correlation")
    
    if len(hist_records) >= 3:
        df_p = pd.DataFrame(hist_records)
    else:
        # Realistic sample baseline for rich visualization
        df_p = pd.DataFrame({
            "cgpa": [6.2, 7.1, 7.8, 8.4, 9.1, 6.8, 8.9, 7.5, 9.4, 8.1, 7.3, 8.6, 6.5, 9.0, 7.9],
            "coding_score": [48, 62, 76, 88, 94, 55, 84, 70, 96, 82, 68, 87, 50, 91, 78],
            "communication_score": [60, 72, 78, 85, 90, 65, 82, 75, 92, 80, 74, 86, 58, 89, 81],
            "internships": [0, 1, 1, 2, 3, 0, 2, 1, 3, 2, 1, 2, 0, 2, 1],
            "placement_probability": [0.35, 0.62, 0.81, 0.94, 0.99, 0.48, 0.95, 0.74, 0.99, 0.88, 0.69, 0.93, 0.40, 0.97, 0.82],
            "predicted_status": ["Needs Improvement", "Moderate Chance", "High Chance", "High Chance", "High Chance", "Needs Improvement", "High Chance", "Moderate Chance", "High Chance", "High Chance", "Moderate Chance", "High Chance", "Needs Improvement", "High Chance", "High Chance"],
            "department_code": ["ME", "EC", "CS", "AI", "CS", "CE", "AI", "EC", "CS", "CS", "EE", "AI", "ME", "CS", "EC"]
        })

    c_3d, c_2d = st.columns([1.2, 1], gap="medium")

    with c_3d:
        st.markdown("###### 3D Skill Space (CGPA × Coding Score × Probability)")
        fig_3d = px.scatter_3d(
            df_p,
            x="cgpa",
            y="coding_score",
            z="placement_probability",
            color="predicted_status",
            size="internships",
            color_discrete_map={"High Chance": "#10b981", "Moderate Chance": "#f59e0b", "Needs Improvement": "#ef4444"},
            labels={"cgpa": "CGPA", "coding_score": "Coding Score", "placement_probability": "Placement Odds"}
        )
        fig_3d.update_layout(
            height=440,
            margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            scene=dict(
                xaxis=dict(gridcolor="rgba(255,255,255,0.08)", backgroundcolor="rgba(0,0,0,0)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.08)", backgroundcolor="rgba(0,0,0,0)"),
                zaxis=dict(gridcolor="rgba(255,255,255,0.08)", backgroundcolor="rgba(0,0,0,0)")
            ),
            font=dict(color="#94a3b8")
        )
        st.plotly_chart(fig_3d, use_container_width=True)

    with c_2d:
        st.markdown("###### CGPA vs Probability with Linear Fit")
        fig_2d = px.scatter(
            df_p,
            x="cgpa",
            y="placement_probability",
            color="predicted_status",
            color_discrete_map={"High Chance": "#10b981", "Moderate Chance": "#f59e0b", "Needs Improvement": "#ef4444"},
            labels={"cgpa": "Cumulative GPA", "placement_probability": "Placement Probability"}
        )
        # Compute smooth linear fit using numpy without requiring statsmodels
        try:
            import numpy as np
            x_vals = df_p["cgpa"].astype(float).values
            y_vals = df_p["placement_probability"].astype(float).values
            if len(x_vals) >= 2:
                idx_sort = np.argsort(x_vals)
                x_sorted = x_vals[idx_sort]
                poly = np.poly1d(np.polyfit(x_vals, y_vals, 1))
                y_fit = np.clip(poly(x_sorted), 0.0, 1.0)
                fig_2d.add_trace(go.Scatter(
                    x=x_sorted,
                    y=y_fit,
                    mode="lines",
                    line=dict(color="#38bdf8", width=2, dash="dash"),
                    name="Linear Trend Fit"
                ))
        except Exception:
            pass

        fig_2d.update_layout(
            height=440,
            margin=dict(t=20, b=20, l=20, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8"),
            xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.06)")
        )
        st.plotly_chart(fig_2d, use_container_width=True)

# -------------------------------------------------------------------
# TAB 2: Department Cohort Benchmarks
# -------------------------------------------------------------------
with tab_dept:
    st.markdown("##### 🏛️ Department Cohort Volumes & Placement Readiness")
    depts = infra.get("departments", [])
    if depts:
        df_d = pd.DataFrame(depts)
        fig_bar = px.bar(
            df_d,
            x="code",
            y="total_historical_students",
            text="total_historical_students",
            color="total_historical_students",
            color_continuous_scale="Purples",
            labels={"code": "Department Code", "total_historical_students": "Historical Student Cohort Volume"}
        )
        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8")
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        st.dataframe(df_d, use_container_width=True)

# -------------------------------------------------------------------
# TAB 3: ML Models & Evaluation
# -------------------------------------------------------------------
with tab_models:
    st.markdown("##### 🤖 Machine Learning Model Benchmarks & Metrics")

    m_info = models_res.get("data", {}) if models_res.get("success") else {}
    p_models = m_info.get("placement_models", {})
    metrics = placement_data.get("models_evaluation", {})

    if metrics:
        rows = []
        for m_name, vals in metrics.items():
            rows.append({
                "Model Architecture": m_name,
                "Accuracy Score": f"{vals.get('accuracy', 0)*100:.2f}%",
                "F1 Score": f"{vals.get('f1', 0):.4f}",
                "Status": "⭐ Active Best" if m_name == p_models.get("best_model") else "Candidate"
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

    st.markdown(
        f"""
        <div class="glass-card" style="margin-top: 14px;">
            <p style="margin: 0; font-size: 0.88rem; color: #f8fafc;">
                <b>Feature Vector (7 Features):</b> <code>{', '.join(p_models.get('features', []))}</code>
            </p>
            <p style="margin: 6px 0 0 0; font-size: 0.82rem; color: #94a3b8;">
                Trained using Stratified Hold-Out Cross-Validation. XGBoost provides optimized gradient boosting with logloss regularization.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

# -------------------------------------------------------------------
# TAB 4: Physical Campus Assets
# -------------------------------------------------------------------
with tab_matrix:
    st.markdown("##### 🏢 Campus Infrastructure & Asset Utilization")
    a1, a2, a3, a4 = st.columns(4)
    with a1:
        st.metric("Total Lecture Halls", f"{infra.get('total_classrooms', 34)}", f"{infra.get('avg_classroom_utilization', 75.0)}% Util")
    with a2:
        st.metric("Faculty Members", f"{infra.get('total_faculty', 48)}", f"{infra.get('avg_teaching_hours', 14.0)}h / 16h Workload")
    with a3:
        st.metric("Computing Laboratories", f"{infra.get('total_laboratories', 18)}", f"{infra.get('total_computers', 540)} Workstations")
    with a4:
        st.metric("Operational Equipment", f"{infra.get('operational_equipment_units', 110)} / {infra.get('total_equipment_units', 120)}", "Ready")
