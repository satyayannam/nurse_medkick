import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import plotly.express as px
from api.calls import get_user_calls

def render_userwise_view(user_key, start_date, end_date):
    st.markdown("### Nurse Call Analytics")

    def format_minutes_to_hr_min(minutes):
        if pd.isna(minutes):
            return "0 hr 0 min"
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        return f"{hours} hr {mins} min"

    # --- Sidebar Clock-In/Out Time Inputs ---
    st.sidebar.markdown("Filter by Clocked-In Hours (Weekdays Only)")
    clock_in = st.sidebar.time_input("Clock-In Time", value=datetime.strptime("09:00", "%H:%M").time())
    clock_out = st.sidebar.time_input("Clock-Out Time", value=datetime.strptime("17:00", "%H:%M").time())

    # --- Time Range Setup ---
    eastern = pytz.timezone("US/Eastern")
    shift_start = eastern.localize(datetime.combine(start_date, datetime.min.time())).astimezone(pytz.UTC)
    shift_end = eastern.localize(datetime.combine(end_date, datetime.max.time())).astimezone(pytz.UTC)
    shift_start_str = shift_start.strftime("%Y-%m-%dT%H:%M:%SZ")
    shift_end_str = shift_end.strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        calls = get_user_calls(user_key, shift_start_str, shift_end_str)
    except Exception as e:
        st.error(f"Failed to fetch calls: {e}")
        return

    if not calls:
        st.warning("No call data found for this nurse in the selected range.")
        return

    df = pd.DataFrame(calls)
    df["startTime"] = pd.to_datetime(df["startTime"], errors="coerce", utc=True)
    df["duration"] = pd.to_numeric(df["duration"], errors="coerce") / 60000
    df["duration"] = df["duration"].fillna(0)
    df["endTime"] = df["startTime"] + pd.to_timedelta(df["duration"], unit="m")

    df["startTimeEastern"] = df["startTime"].dt.tz_convert("US/Eastern")
    df["endTimeEastern"] = df["endTime"].dt.tz_convert("US/Eastern")

    df["Caller"] = df["caller"].apply(lambda x: x.get("number") if isinstance(x, dict) else None)
    df["Callee"] = df["callee"].apply(lambda x: x.get("number") if isinstance(x, dict) else None)

    # --- Apply Mon–Fri Filter
    df["weekday"] = df["startTimeEastern"].dt.weekday
    df = df[df["weekday"] < 5]  # 0–4 = Monday–Friday

    # --- Apply Clocked-In Time Filter
    df["call_time_only"] = df["startTimeEastern"].dt.time
    df = df[(df["call_time_only"] >= clock_in) & (df["call_time_only"] <= clock_out)]

    if df.empty:
        st.warning("No calls found during the selected weekday and clock-in range.")
        return

    answered_df = df[df["duration"] > 0].copy()
    missed_df = df[(df["duration"] == 0) & (df["direction"] == "INBOUND")].copy()

    # --- Metrics
    total_calls = len(df)
    answered_calls = len(answered_df)
    missed_calls = len(missed_df)
    total_talk_time = answered_df["duration"].sum()
    avg_duration = answered_df["duration"].mean()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Calls", total_calls)
    col2.metric("Answered Calls", answered_calls)
    col3.metric("Missed INBOUND Calls", missed_calls)
    col4.metric("Talk Time", format_minutes_to_hr_min(total_talk_time))
    col5.metric("Avg Duration", format_minutes_to_hr_min(avg_duration))

    # --- Missed Call Table
    if not missed_df.empty:
        st.subheader("Missed INBOUND Call Times")
        missed_df["Missed Call Time"] = missed_df["startTimeEastern"].dt.strftime("%Y-%m-%d %H:%M:%S")
        st.dataframe(missed_df[["Missed Call Time", "Caller", "Callee"]], use_container_width=True)

    # --- Longest Call
    st.subheader("Longest Call")
    if not answered_df.empty:
        longest = answered_df.loc[answered_df["duration"].idxmax()]
        st.write(f"{longest['startTimeEastern'].strftime('%Y-%m-%d %H:%M:%S')} — {format_minutes_to_hr_min(longest['duration'])}")
    else:
        st.write("No answered calls found.")

    # --- Time Gaps > 30 Minutes
    st.subheader("Time Gaps > 30 Minutes")
    df = df.sort_values("startTime")
    df["prev_end"] = df["endTime"].shift()
    df["gap"] = (df["startTime"] - df["prev_end"]).dt.total_seconds() / 60
    gap_df = df[df["gap"] > 30][["prev_end", "startTime", "gap"]].dropna()

    if not gap_df.empty:
        gap_df["Previous Call End"] = gap_df["prev_end"].dt.tz_convert("US/Eastern").dt.strftime("%Y-%m-%d %H:%M:%S")
        gap_df["Current Call Start"] = gap_df["startTime"].dt.tz_convert("US/Eastern").dt.strftime("%Y-%m-%d %H:%M:%S")
        gap_df["Gap"] = gap_df["gap"].apply(format_minutes_to_hr_min)
        st.dataframe(gap_df[["Previous Call End", "Current Call Start", "Gap"]], use_container_width=True)
    else:
        st.write("No gaps greater than 30 minutes found.")

    # --- All Call Logs
    st.subheader("All Call Logs")
    full_logs = df[["startTimeEastern", "endTimeEastern", "duration", "direction", "Caller", "Callee"]].copy()
    full_logs["startTimeEastern"] = full_logs["startTimeEastern"].dt.strftime("%Y-%m-%d %H:%M:%S")
    full_logs["endTimeEastern"] = full_logs["endTimeEastern"].dt.strftime("%Y-%m-%d %H:%M:%S")
    full_logs["duration"] = full_logs["duration"].apply(format_minutes_to_hr_min)
    st.dataframe(full_logs.sort_values("startTimeEastern"), use_container_width=True)

    # --- Daily Answered vs Missed Chart
    st.subheader("Daily Answered vs Missed INBOUND Calls")
    df["date"] = df["startTimeEastern"].dt.date
    df["is_answered"] = df["duration"] > 0
    df["is_missed_inbound"] = (df["duration"] == 0) & (df["direction"] == "INBOUND")
    filtered = df[df["is_answered"] | df["is_missed_inbound"]].copy()
    filtered["Status"] = filtered["is_answered"].map({True: "Answered", False: "Missed"})
    call_status = filtered.groupby(["date", "Status"]).size().reset_index(name="Count")

    fig_daily_status = px.bar(
        call_status,
        x="date",
        y="Count",
        color="Status",
        title="Daily Call Outcomes (Inbound Missed Only)",
        barmode="stack",
        color_discrete_map={"Answered": "green", "Missed": "red"},
        labels={"date": "Date", "Count": "Number of Calls"}
    )
    fig_daily_status.update_layout(xaxis=dict(tickformat="%b %d", tickangle=0))
    st.plotly_chart(fig_daily_status, use_container_width=True)

    # --- Avg Duration Per Day
    st.subheader("Average Answered Call Duration Per Day")
    if not answered_df.empty:
        answered_df["date"] = answered_df["startTimeEastern"].dt.date
        avg_duration_daily = (
            answered_df.groupby("date")["duration"]
            .mean()
            .reset_index(name="Avg Duration")
        )
        avg_duration_daily["Avg Duration (hr:min)"] = avg_duration_daily["Avg Duration"].apply(format_minutes_to_hr_min)
        st.dataframe(avg_duration_daily[["date", "Avg Duration (hr:min)"]], use_container_width=True)
