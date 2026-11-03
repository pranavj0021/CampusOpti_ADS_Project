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

st.set_page_config(page_title="Executive Dashboard — CampusPredict", page_icon="📊", layout="wide")
require_auth()
render_theme_styles()
render_sidebar_user_badge()

token = get_token()
user = get_current_user() or {}

# Header & Controls
top_c1, top_c2 = st.columns([3, 1])
with top_c1:
    st.markdown(
        """
        <div style="margin-bottom: 12px;">
            <h1 style="margin: 0; font-size: 1.9rem; font-weight: 800; color: #f8fafc;">
                📊 Executive Analytics Dashboard
            </h1>
            <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 0.9rem;">
                Real-time institutional placement indicators, candidate readiness distribution, and resource capacity
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
with top_c2:
    selected_year = st.selectbox("Planning Academic Horizon", ["2026-2027", "2027-2028", "2025-2026"], index=0)

# Fetch live analytics & dashboard overview
with st.spinner("Synchronizing live metrics from CampusPredict API..."):
    analytics_res = api_client.get_analytics(token)
    dash_res = api_client.get_dashboard_overview(token, academic_year=selected_year)

if not analytics_res.get("success"):
    st.error(f"Failed to fetch analytics from backend: {analytics_res.get('error')}")
    st.stop()

data = analytics_res.get("data", {})
overview = data.get("overview", {})
placement_data = data.get("placement_analytics", {})
infra = data.get("campus_infrastructure", {})
dash_data = dash_res.get("data", {}) if dash_res.get("success") else {}
dash_kpis = dash_data.get("kpis", {})

# Top KPI Metric Cards
k1, k2, k3, k4 = st.columns(4)

avg_placement = overview.get('average_placement_rate_pct', 0.0)
with k1:
    st.metric(
        label="Placement Readiness Rate",
        value=f"{avg_placement}%",
        delta="Target >= 80%" if avg_placement >= 80 else "Attention Required"
    )

with k2:
    st.metric(
        label="Total Predictions Logged",
        value=f"{overview.get('total_predictions', 0):,}",
        delta=f"{overview.get('total_profiles', 0)} Active Profiles"
    )

with k3:
    st.metric(
        label="Benchmark Candidate CGPA",
        value=f"{overview.get('benchmark_cgpa', 7.5):.2f} / 10",
        delta="Tier-1 Cutoff: 7.50"
    )

with k4:
    st.metric(
        label="Coding Aptitude Benchmark",
        value=f"{overview.get('benchmark_coding_score', 75.0):.1f} / 100",
        delta="DSA Cutoff: 70.0"
    )

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

# Main Dashboard Tabs
tab_placement_view, tab_infra_view, tab_ai_view = st.tabs([
    "🎯 Placement Readiness & Risk Distributions",
    "🏢 Campus Resource & Infrastructure Posture",
    "🤖 CampusPredict AI Decision Advisor"
])

with tab_placement_view:
    c_left, c_right = st.columns(2, gap="large")

    with c_left:
        st.markdown("##### 🎯 Candidate Placement Readiness Breakdown")
        status_dist = placement_data.get("status_distribution", {})
        if any(status_dist.values()):
            df_status = pd.DataFrame([
                {"Status": k, "Count": v} for k, v in status_dist.items()
            ])
            fig_donut = px.pie(
                df_status,
                names="Status",
                values="Count",
                hole=0.58,
                color="Status",
                color_discrete_map={
                    "High Chance": "#10b981",
                    "Moderate Chance": "#f59e0b",
                    "Needs Improvement": "#ef4444"
                }
            )
            fig_donut.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8", family="Plus Jakarta Sans"),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("No placement predictions recorded yet. Run your first prediction in the Placement Prediction tab!")

    with c_right:
        st.markdown("##### 🛡️ Candidate Risk Profile Distribution")
        risk_dist = placement_data.get("risk_distribution", {})
        if any(risk_dist.values()):
            df_risk = pd.DataFrame([
                {"Risk Level": k, "Candidates": v} for k, v in risk_dist.items()
            ])
            fig_bar = px.bar(
                df_risk,
                x="Risk Level",
                y="Candidates",
                color="Risk Level",
                color_discrete_map={
                    "Low Risk": "#10b981",
                    "Moderate Risk": "#f59e0b",
                    "High Risk": "#f43f5e"
                },
                text="Candidates"
            )
            fig_bar.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8", family="Plus Jakarta Sans"),
                showlegend=False,
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)")
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Risk assessment metrics will populate automatically after generating student predictions.")

    # Recent Audit Log Table
    st.markdown("##### 🕒 Recent Placement Audit Logs (Live Database)")
    hist_res = api_client.get_prediction_history(token)
    if hist_res.get("success"):
        hist_items = hist_res.get("data", [])
        if hist_items:
            df_hist = pd.DataFrame(hist_items)
            display_cols = ["created_at", "student_name", "department_code", "cgpa", "backlogs", "coding_score", "predicted_status", "placement_probability", "model_used"]
            available_cols = [c for c in display_cols if c in df_hist.columns]
            
            df_show = df_hist[available_cols].copy()
            if "placement_probability" in df_show.columns:
                df_show["placement_probability"] = df_show["placement_probability"].apply(lambda p: f"{float(p)*100:.1f}%")
            
            st.dataframe(df_show.head(10), use_container_width=True)
        else:
            st.info("No prediction history recorded yet.")

with tab_infra_view:
    st.markdown(f"##### 🏛️ Institutional Resource Posture for Academic Horizon: **{selected_year}**")
    
    i1, i2, i3, i4 = st.columns(4)
    with i1:
        st.metric("Projected Enrollment", f"{dash_kpis.get('total_predicted_students', 1850):,} Students", "Forecasted Growth")
    with i2:
        st.metric("Available Classrooms", f"{dash_kpis.get('available_classrooms', 34)} Rooms", "Optimal Allocation")
    with i3:
        st.metric("Faculty Headcount", f"{dash_kpis.get('available_faculty', 48)} Faculty", "14.0h Avg Teaching Load")
    with i4:
        st.metric("Computing Laboratories", f"{dash_kpis.get('laboratories_count', 18)} Labs", f"{dash_kpis.get('avg_lab_utilization', 75.0)}% Utilized")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Department Forecasts Bar Chart
    dept_forecasts = dash_data.get("department_forecasts", [])
    if dept_forecasts:
        df_forecast = pd.DataFrame(dept_forecasts)
        fig_f = px.bar(
            df_forecast,
            x="department_code",
            y="predicted_students",
            text="predicted_students",
            color="growth_rate_pct",
            color_continuous_scale="Tealgrn",
            labels={"department_code": "Department", "predicted_students": "Forecasted Enrollment", "growth_rate_pct": "Growth Rate (%)"}
        )
        fig_f.update_layout(
            margin=dict(t=20, b=20, l=20, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8", family="Plus Jakarta Sans"),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)")
        )
        st.plotly_chart(fig_f, use_container_width=True)

with tab_ai_view:
    st.markdown("##### 🤖 CampusPredict AI Interactive Decision Assistant")
    st.caption("Ask questions about your placement forecast, preparation strategies, or university resource bottlenecks.")

    dash_prompt = st.text_input("💬 Ask AI Advisor:", placeholder="e.g. How can I boost my placement likelihood above 90%?", key="dash_ai_input")
    c_btn1, c_btn2, c_btn3 = st.columns(3)
    quick_q = None
    with c_btn1:
        if st.button("💡 Tier-1 Company Screening Cutoffs", use_container_width=True, key="d_q1"):
            quick_q = "What are the screening cutoffs and criteria for Tier-1 technology companies?"
    with c_btn2:
        if st.button("🗓️ 4-Week Coding & DSA Roadmap", use_container_width=True, key="d_q2"):
            quick_q = "Give me a 4-week coding and DSA study roadmap"
    with c_btn3:
        if st.button("🏛️ Explain Enrollment Trends", use_container_width=True, key="d_q3"):
            quick_q = f"Explain projected departmental student enrollment trends for {selected_year}"

    q_to_run = quick_q or (dash_prompt.strip() if dash_prompt else None)
    if q_to_run:
        with st.spinner("CampusPredict AI is analyzing system context..."):
            ai_res = api_client.chat_ai(token, message=q_to_run, academic_year=selected_year)
            if ai_res.get("success"):
                reply_info = ai_res.get("data", {})
                st.markdown(
                    f"""
                    <div class="glass-card" style="margin-top: 14px; border-left: 4px solid #38bdf8;">
                        <div style="font-size: 0.8rem; color: #38bdf8; font-weight: 700; text-transform: uppercase; margin-bottom: 6px;">
                            Response from {reply_info.get('model_used', 'CampusPredict AI')}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                st.markdown(reply_info.get("reply", "No reply generated."))
            else:
                st.error(f"AI Advisor request failed: {ai_res.get('error')}")
