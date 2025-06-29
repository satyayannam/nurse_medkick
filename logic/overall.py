import pandas as pd
import streamlit as st
from datetime import datetime
import pytz
from api.users import get_users
from api.calls import get_user_calls
import plotly.express as px

def render_overall_view(start_date, end_date):
    # Time conversion
    eastern = pytz.timezone("US/Eastern")
    shift_start = eastern.localize(datetime.combine(start_date, datetime.min.time())).astimezone(pytz.UTC)
    shift_end = eastern.localize(datetime.combine(end_date, datetime.max.time())).astimezone(pytz.UTC)

    shift_start_str = shift_start.strftime("%Y-%m-%dT%H:%M:%SZ")
    shift_end_str = shift_end.strftime("%Y-%m-%dT%H:%M:%SZ")

    users = get_users()
    all_calls = []

    for user in users:
        calls = get_user_calls(user["userKey"], shift_start_str, shift_end_str)
        for call in calls:
            call["nurse"] = user.get("name") or user.get("email") or "Unknown"
        all_calls.extend(calls)

    df = pd.DataFrame(all_calls)

    if df.empty:
        st.warning("No call data found for this period.")
        return

    # Convert startTime to UTC and then to Eastern Time
# Convert startTime and endTime to UTC tz-aware datetimes
    df["startTime"] = pd.to_datetime(df["startTime"], errors="coerce", utc=True)

    if "endTime" in df.columns and df["endTime"].notnull().any():
        df["endTime"] = pd.to_datetime(df["endTime"], errors="coerce", utc=True)
        df["duration"] = (df["endTime"] - df["startTime"]).dt.total_seconds() / 60
    else:
        df["duration"] = df["duration"] / 60000  # ms to min if no endTime

    df["duration"] = df["duration"].fillna(0)

    # Convert startTime to Eastern for display and hourly bucketing
    df["startTimeEastern"] = df["startTime"].dt.tz_convert("US/Eastern")
    df["date"] = df["startTimeEastern"].dt.date
    df["hour"] = df["startTimeEastern"].dt.floor("h")


    # Final cleanup
    df["duration"] = df["duration"].fillna(0)


    # --- Metrics ---
    missed_df = df[df["duration"] == 0]
    total_calls = len(df)
    answered_calls = len(df[df["duration"] > 0])
    missed_calls = len(missed_df)
    total_talk_time = df[df["duration"] > 0]["duration"].sum()
    avg_duration = df[df["duration"] > 0]["duration"].mean()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Calls", total_calls)
    col2.metric("Answered Calls", answered_calls)
    col3.metric("Missed Calls", missed_calls)
    col4.metric("Talk Time (Hrs)", round(total_talk_time / 60, 2))
    col5.metric("Avg Call Duration (Min)", round(avg_duration or 0, 2))

    # --- Chart 1: Call Volume Zone ---
    daily_volume = df.groupby("date").size().reset_index(name="Total Calls")
    daily_volume["Zone"] = pd.cut(
        daily_volume["Total Calls"],
        bins=[-1, 30, 70, float("inf")],
        labels=["Low", "Moderate", "High"]
    )
    fig1 = px.line(
        daily_volume,
        x="date", y="Total Calls", color="Zone",
        title="📈 Daily Call Volume Classification",
        markers=True,
        color_discrete_map={"Low": "red", "Moderate": "orange", "High": "green"},
    )
    st.plotly_chart(fig1, use_container_width=True)

    # --- Chart 2: Total Talk Time per Day ---
    daily_talk = df[df["duration"] > 0].groupby("date")["duration"].sum().reset_index()
    daily_talk["Talk Hours"] = daily_talk["duration"] / 60
    fig2 = px.bar(
        daily_talk,
        x="date", y="Talk Hours",
        title="🕐 Total Talk Time per Day",
        labels={"Talk Hours": "Hours"}
    )
    st.plotly_chart(fig2, use_container_width=True)

# --- Chart 3: Call Outcomes Breakdown per Nurse ---
    outcomes = df.copy()
    outcomes["Answered"] = outcomes["duration"] > 0
    outcome_summary = outcomes.groupby(["nurse", "Answered"]).size().reset_index(name="Count")
    outcome_summary["Status"] = outcome_summary["Answered"].map({True: "Answered", False: "Missed"})

    if outcome_summary.empty:
        st.info("No call data to display in Call Outcomes Breakdown chart.")
    else:
        fig3 = px.bar(
            outcome_summary,
            x="nurse", y="Count", color="Status",
            title="📊 Call Outcomes Breakdown per Nurse",
            text="Count",
            labels={"Count": "Calls", "nurse": "Nurse"},
            barmode="stack",
            color_discrete_map={"Answered": "green", "Missed": "red"}
        )
        fig3.update_traces(textposition='inside')
        st.plotly_chart(fig3, use_container_width=True)




    # --- Missed Calls Table ---
    if not missed_df.empty:
        missed_df["Missed Time (Eastern)"] = missed_df["startTime"].dt.tz_convert("US/Eastern")
        missed_df["Caller"] = missed_df["caller"].apply(lambda x: x.get("number") if isinstance(x, dict) else None)
        missed_df["Callee"] = missed_df["callee"].apply(lambda x: x.get("number") if isinstance(x, dict) else None)
        table = missed_df[["Missed Time (Eastern)", "direction", "nurse", "Caller", "Callee"]]
        st.subheader("📋 Missed Calls Log")
        st.dataframe(table.sort_values("Missed Time (Eastern)"), use_container_width=True)
