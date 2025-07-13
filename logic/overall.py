import pandas as pd
import streamlit as st
from datetime import datetime
import pytz
from api.users import get_users
from api.calls import get_user_calls
import plotly.express as px

def format_minutes_to_hr_min(minutes):
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    return f"{hours} hr {mins} min"

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

    df["startTime"] = pd.to_datetime(df["startTime"], errors="coerce", utc=True)

    if "endTime" in df.columns and df["endTime"].notnull().any():
        df["endTime"] = pd.to_datetime(df["endTime"], errors="coerce", utc=True)
        df["duration"] = (df["endTime"] - df["startTime"]).dt.total_seconds() / 60
    else:
        df["duration"] = df["duration"] / 60000  # fallback in ms

    df["duration"] = df["duration"].fillna(0)
    df["startTimeEastern"] = df["startTime"].dt.tz_convert("US/Eastern")
    df["date"] = df["startTimeEastern"].dt.date
    df["hour"] = df["startTimeEastern"].dt.floor("h")

    # --- Metrics
    missed_df = df[(df["duration"] == 0) & (df["direction"] == "INBOUND")]
    total_calls = len(df)
    answered_calls = len(df[df["duration"] > 0])
    missed_calls = len(missed_df)
    total_talk_time = df[df["duration"] > 0]["duration"].sum()
    avg_duration = df[df["duration"] > 0]["duration"].mean()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Calls", total_calls)
    col2.metric("Answered Calls", answered_calls)
    col3.metric("Missed INBOUND Calls", missed_calls)
    col4.metric("Talk Time", format_minutes_to_hr_min(total_talk_time))
    col5.metric("Avg Call Duration", format_minutes_to_hr_min(avg_duration or 0))

    # --- Chart 1: Daily Call Volume Classification
    daily_volume = df.groupby("date").size().reset_index(name="Total Calls")
    daily_volume["Zone"] = pd.cut(
        daily_volume["Total Calls"],
        bins=[-1, 30, 70, float("inf")],
        labels=["Low", "Moderate", "High"]
    )
    fig1 = px.bar(
        daily_volume,
        x="date", y="Total Calls", color="Zone",
        title="📊 Daily Call Volume Classification",
        color_discrete_map={"Low": "red", "Moderate": "orange", "High": "green"},
        labels={"date": "Date", "Total Calls": "Number of Calls"}
    )
    fig1.update_layout(xaxis=dict(tickformat="%b %d"))
    st.plotly_chart(fig1, use_container_width=True)

    # --- Chart 2: Total Talk Time per Day
    daily_talk = df[df["duration"] > 0].groupby("date")["duration"].sum().reset_index()
    daily_talk["Talk Time"] = daily_talk["duration"].apply(format_minutes_to_hr_min)
    st.subheader("🕐 Total Talk Time per Day")
    st.dataframe(daily_talk[["date", "Talk Time"]], use_container_width=True)

    # --- Chart 3: Call Outcomes Breakdown per Nurse (Inbound Missed Only)
    outcomes = df.copy()
    outcomes["Answered"] = outcomes["duration"] > 0
    outcomes["MissedInbound"] = (outcomes["duration"] == 0) & (outcomes["direction"] == "INBOUND")
    filtered = outcomes[(outcomes["Answered"]) | (outcomes["MissedInbound"])].copy()
    filtered["Status"] = filtered.apply(lambda row: "Answered" if row["Answered"] else "Missed", axis=1)
    outcome_summary = filtered.groupby(["nurse", "Status"]).size().reset_index(name="Count")

    if outcome_summary.empty:
        st.info("No call data to display in Call Outcomes Breakdown chart.")
    else:
        fig3 = px.bar(
            outcome_summary,
            x="nurse", y="Count", color="Status",
            title="📊 Call Outcomes Breakdown per Nurse (Inbound Missed Only)",
            text="Count",
            labels={"Count": "Calls", "nurse": "Nurse"},
            barmode="stack",
            color_discrete_map={"Answered": "green", "Missed": "red"}
        )
        fig3.update_traces(textposition='inside')
        st.plotly_chart(fig3, use_container_width=True)

    # --- Missed Call Log
    if not missed_df.empty:
        missed_df["Missed Time (Eastern)"] = missed_df["startTime"].dt.tz_convert("US/Eastern")
        missed_df["Caller"] = missed_df["caller"].apply(lambda x: x.get("number") if isinstance(x, dict) else None)
        missed_df["Callee"] = missed_df["callee"].apply(lambda x: x.get("number") if isinstance(x, dict) else None)
        table = missed_df[["Missed Time (Eastern)", "direction", "nurse", "Caller", "Callee"]]
        st.subheader("📋 Missed Inbound Calls Log")
        st.dataframe(table.sort_values("Missed Time (Eastern)"), use_container_width=True)
