import streamlit as st
from datetime import datetime, timedelta
import pytz

from logic.overall import render_overall_view
from logic.userwise import render_userwise_view
from api.users import get_users

# --- Streamlit Config ---
st.set_page_config("GoTo Call Dashboard", layout="wide")
st.title("Satya's GoTo Call Dashboard")

# --- Footer ---
st.markdown("""
<hr style="margin-top: 3rem;">
<div style='text-align: center; padding: 10px; color: gray; font-size: 0.9em;'>
    <b>Satya's Nurse dashboard</b>
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

# --- User Dropdown (includes All Nurses)
users = get_users()
user_options = ["All Nurses"] + [
    u.get("lines", [{}])[0].get("name") or u.get("name") or f"User {u['userKey'][:6]}"
    for u in users if u.get("lines") and len(u["lines"]) > 0
]
selected_user = st.sidebar.selectbox("Select Nurse", user_options)

# --- Routing Logic ---
if selected_user == "All Nurses":
    render_overall_view(start, end)
else:
    # Find user_key for selected user
    user_map = {
        (u.get("lines", [{}])[0].get("name") or u.get("name") or f"User {u['userKey'][:6]}"): u["userKey"]
        for u in users if u.get("lines") and len(u["lines"]) > 0
    }
    user_key = user_map.get(selected_user)
    render_userwise_view(user_key, start, end)
