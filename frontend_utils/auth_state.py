import streamlit as st
from typing import Optional, Dict, Any

def init_auth_state():
    """Initializes session state keys for authentication."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "token" not in st.session_state:
        st.session_state.token = None
    if "user" not in st.session_state:
        st.session_state.user = None
    if "profile" not in st.session_state:
        st.session_state.profile = None

def is_authenticated() -> bool:
    """Returns True if user has an active authenticated session."""
    init_auth_state()
    return bool(st.session_state.authenticated and st.session_state.token)

def get_token() -> Optional[str]:
    """Returns current JWT access token or None."""
    init_auth_state()
    return st.session_state.token

def get_current_user() -> Optional[Dict[str, Any]]:
    """Returns authenticated user dictionary."""
    init_auth_state()
    return st.session_state.user

def login_user(token: str, user_data: Dict[str, Any]):
    """Stores authentication token and user data in session state."""
    init_auth_state()
    st.session_state.authenticated = True
    st.session_state.token = token
    st.session_state.user = user_data

def logout_user():
    """Clears session state and logs user out."""
    init_auth_state()
    st.session_state.authenticated = False
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.profile = None

def require_auth():
    """
    Guards protected Streamlit pages.
    If unauthenticated, displays alert and stops script execution.
    """
    init_auth_state()
    if not is_authenticated():
        render_theme_styles()
        st.markdown(
            """
            <div style="background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(15, 23, 42, 0.8)); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 14px; padding: 24px; text-align: center; margin: 30px auto; max-width: 650px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
                <div style="font-size: 2.5rem; margin-bottom: 10px;">🔒</div>
                <h2 style="color: #f87171; margin: 0 0 8px 0; font-size: 1.4rem; font-weight: 700;">Authentication Required</h2>
                <p style="color: #94a3b8; font-size: 0.95rem; line-height: 1.5; margin-bottom: 20px;">
                    You must be logged in with a valid account to access this module. Please return to the Home portal to sign in or create a student profile.
                </p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("⬅️ Return to Sign In / Home Page", use_container_width=True, type="primary"):
                st.switch_page("streamlit_app.py")
        st.stop()

def render_sidebar_user_badge():
    """Renders active user identity and logout control in the sidebar with glassmorphic styling."""
    init_auth_state()
    with st.sidebar:
        # App Branding Header in Sidebar
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 16px; padding-bottom: 14px; border-bottom: 1px solid rgba(255,255,255,0.08);">
                <div style="background: linear-gradient(135deg, #2563eb, #06b6d4); width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 18px; box-shadow: 0 4px 12px rgba(37,99,235,0.4);">
                    🎓
                </div>
                <div>
                    <div style="font-size: 1.15rem; font-weight: 800; color: #f8fafc; letter-spacing: -0.02em;">
                        Campus<span style="color: #38bdf8;">Predict</span>
                    </div>
                    <div style="font-size: 0.72rem; color: #64748b; font-weight: 500;">
                        v2.0 • AI Decision System
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if is_authenticated():
            user = st.session_state.user or {}
            username = user.get("username", "User")
            role = (user.get("role") or "student").upper()
            full_name = user.get("full_name") or username

            st.markdown(
                f"""
                <div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8)); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 12px; padding: 14px; margin: 12px 0; box-shadow: 0 4px 16px rgba(0,0,0,0.2);">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                        <span style="font-size: 0.72rem; color: #38bdf8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; display: flex; align-items: center; gap: 4px;">
                            <span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #34d399; box-shadow: 0 0 8px #34d399;"></span>
                            ACTIVE SESSION
                        </span>
                        <span style="background: rgba(99, 102, 241, 0.2); border: 1px solid rgba(99, 102, 241, 0.4); color: #a5b4fc; font-size: 0.7rem; font-weight: 700; padding: 1px 6px; border-radius: 4px;">
                            {role}
                        </span>
                    </div>
                    <div style="font-size: 0.96rem; font-weight: 700; color: #f8fafc; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                        {full_name}
                    </div>
                    <div style="font-size: 0.78rem; color: #94a3b8; margin-top: 2px;">
                        @{username}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button("🚪 Sign Out", use_container_width=True, key="sidebar_logout_btn"):
                logout_user()
                st.success("Session closed.")
                st.switch_page("streamlit_app.py")
        else:
            st.markdown(
                """
                <div style="background: rgba(30, 41, 59, 0.4); border: 1px dashed rgba(255,255,255,0.1); border-radius: 10px; padding: 12px; text-align: center; margin: 12px 0;">
                    <div style="font-size: 0.8rem; color: #94a3b8;">Guest Mode</div>
                    <div style="font-size: 0.72rem; color: #64748b; margin-top: 2px;">Sign in from the home page</div>
                </div>
                """,
                unsafe_allow_html=True
            )

def render_theme_styles():
    """Injects state-of-the-art CSS styling, fonts, glassmorphism, micro-animations, and custom cards."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Outfit:wght@400;600;700;800&display=swap');

        /* Global Typography & Font Family */
        html, body, [class*="css"], [class*="st-"] {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }

        h1, h2, h3, h4, h5, h6 {
            font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif !important;
            letter-spacing: -0.02em;
        }

        /* Container margins */
        .main .block-container {
            padding-top: 2rem !important;
            padding-bottom: 3.5rem !important;
            max-width: 1240px !important;
        }

        /* Glassmorphic Cards & Containers */
        .glass-card {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.65), rgba(15, 23, 42, 0.85));
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            padding: 22px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
            transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
        }
        .glass-card:hover {
            border-color: rgba(56, 189, 248, 0.35);
            box-shadow: 0 15px 30px -5px rgba(56, 189, 248, 0.15);
            transform: translateY(-2px);
        }

        /* Metric cards */
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.85)) !important;
            border: 1px solid rgba(255, 255, 255, 0.09) !important;
            border-radius: 12px !important;
            padding: 16px 20px !important;
            box-shadow: 0 6px 18px rgba(0, 0, 0, 0.2) !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="stMetric"]:hover {
            border-color: rgba(56, 189, 248, 0.4) !important;
            transform: translateY(-2px);
        }
        div[data-testid="stMetricValue"] {
            font-size: 2rem !important;
            font-weight: 800 !important;
            background: linear-gradient(135deg, #38bdf8, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        div[data-testid="stMetricLabel"] {
            color: #94a3b8 !important;
            font-weight: 600 !important;
            font-size: 0.82rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.04em !important;
        }

        /* Streamlit Primary & Secondary Buttons */
        .stButton>button {
            border-radius: 10px !important;
            font-weight: 700 !important;
            font-size: 0.92rem !important;
            padding: 0.55rem 1.25rem !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
        }
        .stButton>button:hover {
            border-color: #38bdf8 !important;
            box-shadow: 0 0 16px rgba(56, 189, 248, 0.35) !important;
            transform: translateY(-1px);
        }
        button[kind="primary"] {
            background: linear-gradient(135deg, #2563eb, #0284c7) !important;
            color: #ffffff !important;
            border: none !important;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35) !important;
        }
        button[kind="primary"]:hover {
            background: linear-gradient(135deg, #1d4ed8, #0369a1) !important;
            box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5) !important;
        }

        /* Modern Tabs */
        button[data-baseweb="tab"] {
            font-weight: 700 !important;
            font-size: 0.95rem !important;
            padding: 10px 18px !important;
            border-radius: 8px !important;
            transition: all 0.2s ease !important;
        }

        /* Input Fields & Dropdowns */
        div[data-baseweb="input"] input, div[data-baseweb="select"] {
            border-radius: 8px !important;
        }

        /* Expanders */
        div[data-testid="stExpander"] {
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 12px !important;
            background: rgba(15, 23, 42, 0.5) !important;
            margin-bottom: 10px !important;
        }
        div[data-testid="stExpander"]:hover {
            border-color: rgba(56, 189, 248, 0.25) !important;
        }

        /* Tables & Dataframes */
        div[data-testid="stDataFrame"] {
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 12px !important;
            overflow: hidden !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
