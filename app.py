import streamlit as st
from datetime import datetime, timedelta
import pytz
from api.users import get_users
from api.calls import get_user_calls
from utils.processing import analyze_calls
from logic.flagging import process_call_data
import plotly.express as px

import streamlit as st



import streamlit.components.v1 as components


st.set_page_config("GoTo Call Dashboard", layout="wide")
st.title("GoTo Call Dashboard")

# Welcome animation
with st.container():
    st.markdown(
        """
        <div style="text-align: center; margin-top: 2rem;">
            <h1 style="font-size: 3em; animation: fadeIn 2s ease-in-out;">Welcome to <span style="color:#00c0ff;">Nurse360</span></h1>
        </div>
        <style>
        @keyframes fadeIn {
            0% {opacity: 0;}
            100% {opacity: 1;}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# Footer copyright
st.markdown(
    """
    <hr style="margin-top: 3rem;">
    <div style='text-align: center; padding: 10px; color: gray; font-size: 0.9em;'>
        <b>Nurse360</b>
    </div>
    """,
    unsafe_allow_html=True
)




# --- Login Security ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def login():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_button = st.button("Login")

        if login_button:
            if username == st.secrets["auth"]["username"] and password == st.secrets["auth"]["password"]:
                st.session_state["authenticated"] = True
                st.success("Login successful!")
                st.rerun()  # <- Use this instead of experimental_rerun
            else:
                st.error("Invalid credentials")
        st.stop()


if not st.session_state.authenticated:
    login()
    st.stop()




# Sidebar filters
st.sidebar.header("Filters")
start = st.sidebar.date_input("Start Date", datetime.today() - timedelta(days=7))
end = st.sidebar.date_input("End Date", datetime.today())

clock_in = st.sidebar.time_input("Clock-in Time", value=datetime.strptime("09:00", "%H:%M").time(), key="clockin")
clock_out = st.sidebar.time_input("Clock-out Time", value=datetime.strptime("17:00", "%H:%M").time(), key="clockout")
gap_threshold = st.sidebar.number_input("Gap Threshold (minutes)", min_value=1, value=30)

# Timezone conversion
eastern = pytz.timezone("US/Eastern")
shift_start = eastern.localize(datetime.combine(start, clock_in)).astimezone(pytz.UTC)
shift_end = eastern.localize(datetime.combine(end, clock_out)).astimezone(pytz.UTC)

# User selection
users = get_users()
user_map = {}

for u in users:
    lines = u.get("lines", [])
    if lines and isinstance(lines, list):
        name = lines[0].get("name", f"User {u['userKey'][:6]}")
    else:
        name = f"User {u['userKey'][:6]}"
    user_map[name] = u["userKey"]

selected_user = st.selectbox("Select User", user_map.keys())

if selected_user:
    calls = get_user_calls(user_map[selected_user], f"{start}T00:00:00Z", f"{end}T23:59:59Z")
    stats = analyze_calls(calls)
    flagged_stats = process_call_data(calls, shift_start, shift_end, gap_threshold)

    if not stats or not flagged_stats:
        st.warning("No calls found for this user.")
    else:
        tabs = st.tabs(["Summary", "Call Log Table", "Flagging Details", "Charts"])

        with tabs[0]:
            st.subheader("User Summary")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Calls", stats["total_calls"])
            col2.metric("Missed Calls", stats["missed_calls"])
            col3.metric("Incoming", stats["incoming"])
            col4.metric("Outgoing", stats["outgoing"])

            st.markdown("### Missed Calls by Direction")
            missed_df = stats["df"][stats["df"]["missed"] == True]

            if not missed_df.empty:
                missed_by_dir = missed_df["direction"].value_counts().reset_index()
                missed_by_dir.columns = ["direction", "count"]
                fig_missed = px.pie(missed_by_dir, values="count", names="direction", title="Missed Call Distribution")
                st.plotly_chart(fig_missed, use_container_width=True, key="missed_calls_chart")
            else:
                st.info("No missed calls found in the selected date range.")


            st.markdown("### Flag Severity")
            flagged = flagged_stats["flagged_gaps"]
            def assign_severity(gap):
                if gap > gap_threshold * 2:
                    return "Red Flag"
                elif gap > gap_threshold:
                    return "Yellow Flag"
                else:
                    return "Normal"

            flagged["severity"] = flagged["gap_minutes"].apply(assign_severity)
            severity_count = flagged["severity"].value_counts().reset_index()
            severity_count.columns = ["severity", "count"]

            fig_severity = px.pie(
                severity_count,
                values="count",
                names="severity",
                title="Flag Severity Distribution"
            )
            st.plotly_chart(fig_severity, use_container_width=True)

        with tabs[1]:
            st.subheader("Call Logs Table")
            st.dataframe(stats["df"][["startTime", "endTime", "direction", "duration_minutes", "missed"]])

            flagged_stats["df"]["date"] = flagged_stats["df"]["startTime"].dt.date
            daily_calls = flagged_stats["df"].groupby("date").size().reset_index(name="call_count")
            fig_daily_calls = px.bar(
                daily_calls,
                x="date",
                y="call_count",
                title="Daily Call Count",
                labels={"date": "Date", "call_count": "Number of Calls"},
                height=400
            )
            st.plotly_chart(fig_daily_calls, use_container_width=True)

        with tabs[2]:
            st.subheader("Flagged Time Gaps")
            st.dataframe(flagged_stats["flagged_gaps"][["startTime", "endTime", "gap_minutes", "severity"]])
            st.markdown(f"**Total Call Time:** {flagged_stats['total_call_time']:.2f} minutes")
            st.markdown(f"**Flags (Gaps > {gap_threshold} mins):** {flagged_stats['flag_count']}")

        with tabs[3]:
            st.plotly_chart(flagged_stats["fig_gap_dist"], use_container_width=True)
            st.plotly_chart(flagged_stats["fig_timeline"], use_container_width=True)
