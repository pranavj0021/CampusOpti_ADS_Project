import streamlit as st
import pandas as pd
import plotly.express as px
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from frontend_utils.api_client import api_client
from frontend_utils.auth_state import (
    require_auth, get_token, get_current_user, render_sidebar_user_badge, render_theme_styles
)

st.set_page_config(page_title="Prediction Audit Trail — CampusPredict", page_icon="📜", layout="wide")
require_auth()
render_theme_styles()
render_sidebar_user_badge()

token = get_token()
user = get_current_user() or {}

st.markdown(
    """
    <div style="margin-bottom: 22px;">
        <h1 style="margin: 0; font-size: 1.9rem; font-weight: 800; color: #f8fafc;">
            📜 Placement Prediction Audit History & Log Explorer
        </h1>
        <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 0.9rem;">
            Searchable, filterable repository of all past candidate evaluations, probability distributions, and career action plans
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Fetch history
with st.spinner("Fetching prediction logs from SQLite database..."):
    res = api_client.get_prediction_history(token)

if not res.get("success"):
    st.error(f"Failed to fetch history: {res.get('error')}")
    st.stop()

records = res.get("data", [])

if not records:
    st.info("No prediction history found. Run a placement evaluation in the Placement Prediction tab.")
    if st.button("🔮 Run a Placement Prediction Now", type="primary"):
        st.switch_page("pages/3_Placement_Prediction.py")
    st.stop()

df = pd.DataFrame(records)

# KPI Metrics
total_evals = len(df)
avg_prob = df["placement_probability"].mean() if "placement_probability" in df.columns else 0.0
high_chance_n = sum(df["predicted_status"] == "High Chance") if "predicted_status" in df.columns else 0
top_model = df["model_used"].mode()[0] if "model_used" in df.columns and not df["model_used"].empty else "XGBoost"

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Total Evaluations Logged", f"{total_evals}")
with m2:
    st.metric("Mean Placement Probability", f"{avg_prob*100:.1f}%")
with m3:
    st.metric("High Likelihood Outcomes", f"{high_chance_n} / {total_evals}")
with m4:
    st.metric("Primary ML Classifier", f"{top_model}")

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# Probability Distribution Histogram
if "placement_probability" in df.columns and len(df) >= 2:
    fig_hist = px.histogram(
        df,
        x="placement_probability",
        nbins=15,
        color="predicted_status",
        color_discrete_map={"High Chance": "#10b981", "Moderate Chance": "#f59e0b", "Needs Improvement": "#ef4444"},
        labels={"placement_probability": "Placement Probability (0.0 - 1.0)", "count": "Evaluation Count"},
        title="Historical Placement Probability Distribution"
    )
    fig_hist.update_layout(
        margin=dict(t=35, b=20, l=20, r=20),
        height=240,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8", family="Plus Jakarta Sans")
    )
    st.plotly_chart(fig_hist, use_container_width=True)

# Search & Filters
st.markdown("#### 🔍 Filter & Search Records")
c_search, c_f1, c_f2 = st.columns([2, 1, 1])

with c_search:
    search_q = st.text_input("🔎 Search by Candidate Name or Roll Number", placeholder="Type to filter...")

with c_f1:
    status_opts = ["All"] + sorted(list(df["predicted_status"].unique())) if "predicted_status" in df.columns else ["All"]
    filter_status = st.selectbox("Filter Outcome", status_opts)

with c_f2:
    model_opts = ["All"] + sorted(list(df["model_used"].unique())) if "model_used" in df.columns else ["All"]
    filter_model = st.selectbox("Filter Model", model_opts)

filtered = df.copy()
if search_q.strip():
    q = search_q.strip().lower()
    filtered = filtered[
        filtered["student_name"].astype(str).str.lower().str.contains(q) |
        filtered["roll_number"].astype(str).str.lower().str.contains(q)
    ]
if filter_status != "All":
    filtered = filtered[filtered["predicted_status"] == filter_status]
if filter_model != "All":
    filtered = filtered[filtered["model_used"] == filter_model]

st.markdown(f"**Displaying {len(filtered)} of {total_evals} audit records**")

# Display Table
show_cols = ["created_at", "roll_number", "department_code", "cgpa", "backlogs", "coding_score", "placement_probability", "predicted_status", "risk_level", "model_used"]
available_cols = [c for c in show_cols if c in filtered.columns]

table_df = filtered[available_cols].copy()
if "placement_probability" in table_df.columns:
    table_df["placement_probability"] = table_df["placement_probability"].apply(lambda x: f"{float(x)*100:.1f}%")

st.dataframe(table_df, use_container_width=True)

# Expandable Inspection Cards
st.markdown("#### 📑 Inspection & Strategic Recommendations")
for idx, row in filtered.head(15).iterrows():
    p_pct = f"{float(row.get('placement_probability', 0))*100:.1f}%"
    with st.expander(f"Record #{row.get('id', idx)} — {row.get('student_name', 'Student')} • {row.get('predicted_status')} ({p_pct}) • {row.get('model_used')}"):
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown(f"**Date:** `{row.get('created_at')}`")
            st.markdown(f"**Roll Number:** `{row.get('roll_number')}`")
            st.markdown(f"**Department:** `{row.get('department_code')}`")
            st.markdown(f"**CGPA:** `{row.get('cgpa')}` | **Backlogs:** `{row.get('backlogs')}`")
        with col_r2:
            st.markdown(f"**Coding Aptitude:** `{row.get('coding_score')}/100`")
            st.markdown(f"**Communication:** `{row.get('communication_score')}/100`")
            st.markdown(f"**Risk Level:** `{row.get('risk_level')}`")
            st.markdown(f"**Internships:** `{row.get('internships')}` | **Projects:** `{row.get('projects')}`")

        recs = row.get("recommendations_list", [])
        if recs:
            st.markdown("**Personalized Recommendation Plan:**")
            for r in recs:
                st.markdown(f"- 📌 {r}")

# Export button
csv_bytes = filtered.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Export Filtered History as CSV",
    data=csv_bytes,
    file_name="campuspredict_audit_trail.csv",
    mime="text/csv",
    use_container_width=True
)
