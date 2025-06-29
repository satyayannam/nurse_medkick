import streamlit as st
from datetime import datetime, timedelta
import pytz

from logic.overall import render_overall_view
from logic.userwise import render_userwise_view

# --- Streamlit Config ---
st.set_page_config("GoTo Call Dashboard", layout="wide")
st.title("GoTo Call Dashboard")

# --- Welcome Animation ---
st.markdown("""
<div style="text-align: center; margin-top: 2rem;">
    <h1 style="font-size: 3em; animation: fadeIn 2s ease-in-out;">Welcome to <span style="color:#00c0ff;">Nurse360</span></h1>
</div>
<style>
@keyframes fadeIn {
    0% {opacity: 0;}
    100% {opacity: 1;}
}
</style>
""", unsafe_allow_html=True)

# --- Footer ---
st.markdown("""
<hr style="margin-top: 3rem;">
<div style='text-align: center; padding: 10px; color: gray; font-size: 0.9em;'>
    <b>Nurse360</b>
</div>
""", unsafe_allow_html=True)

# --- Auth ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def login():
    if not st.session_state["authenticated"]:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_button = st.button("Login")

        if login_button:
            if username == st.secrets["auth"]["username"] and password == st.secrets["auth"]["password"]:
                st.session_state["authenticated"] = True
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials")
        st.stop()

if not st.session_state.authenticated:
    login()
    st.stop()

# --- Sidebar Filters ---
st.sidebar.header("Filters")
view_mode = st.sidebar.radio("Dashboard Mode", ["Overall View", "User View"], key="view_mode")

today = datetime.today().date()
range_option = st.sidebar.selectbox("Date Range", ["Day", "Week", "Month", "Custom"])

if range_option == "Day":
    start = end = today
elif range_option == "Week":
    start = today - timedelta(days=7)
    end = today
elif range_option == "Month":
    start = today.replace(day=1)
    end = today
else:
    start = st.sidebar.date_input("Start Date", today - timedelta(days=7))
    end = st.sidebar.date_input("End Date", today)

# --- Routing Logic ---
if view_mode == "Overall View":
    render_overall_view(start, end)
else:
    render_userwise_view(start, end)
