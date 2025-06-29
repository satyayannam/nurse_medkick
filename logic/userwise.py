import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import plotly.express as px
from api.calls import get_user_calls
from api.users import get_users

def render_userwise_view(start_date, end_date):
    st.header("📞 User-wise Call Analysis")

    # --- Time Conversion
    eastern = pytz.timezone("US/Eastern")
    shift_start = eastern.localize(datetime.combine(start_date, datetime.min.time())).astimezone(pytz.UTC)
    shift_end = eastern.localize(datetime.combine(end_date, datetime.max.time())).astimezone(pytz.UTC)
    shift_start_str = shift_start.strftime("%Y-%m-%dT%H:%M:%SZ")
    shift_end_str = shift_end.strftime("%Y-%m-%dT%H:%M:%SZ")

    # --- Select User
    users = get_users()
    user_map = {
        (u.get("lines", [{}])[0].get("name") or u.get("name") or f"User {u['userKey'][:6]}"): u["userKey"]
        for u in users if u.get("lines") and len(u["lines"]) > 0
    }
    selected_user = st.selectbox("Select User", list(user_map.keys()))
    user_key = user_map[selected_user]

    # --- Get Calls
    try:
        calls = get_user_calls(user_key, shift_start_str, shift_end_str)
    except Exception as e:
        st.error(f"❌ Failed to fetch calls for {selected_user}: {e}")
        return

    if not calls:
        st.warning("No call data found for this user in the selected range.")
        return

    for call in calls:
        call["nurse"] = selected_user

    df = pd.DataFrame(calls)
    df["startTime"] = pd.to_datetime(df.get("startTime"), errors="coerce", utc=True)
    df["duration"] = pd.to_numeric(df.get("duration", 0), errors="coerce") / 60000
    df["duration"] = df["duration"].fillna(0)
    df["endTime"] = df["startTime"] + pd.to_timedelta(df["duration"], unit="m")

    df["startTimeEastern"] = df["startTime"].dt.tz_convert("US/Eastern")
    df["endTimeEastern"] = df["endTime"].dt.tz_convert("US/Eastern")

    # --- Filtered Answered and Missed
    answered_df = df[(df["duration"] > 0) & (df["startTimeEastern"].notnull())].copy()
    missed_df = df[(df["duration"] == 0) & (df["startTimeEastern"].notnull())].copy()

    # --- Metrics
    total_calls = len(df)
    answered_calls = len(answered_df)
    missed_calls = len(missed_df)
    total_talk_time = answered_df["duration"].sum()
    avg_duration = answered_df["duration"].mean()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("📞 Total Calls", total_calls)
    col2.metric("✅ Answered Calls", answered_calls)
    col3.metric("❌ Missed Calls", missed_calls)
    col4.metric("🕐 Talk Time (min)", round(total_talk_time, 2))
    col5.metric("⏱️ Avg Duration (min)", round(avg_duration or 0, 2))

    # --- Missed Calls Table
    if not missed_df.empty:
        st.subheader("📅 Missed Call Times (Inbound/Outbound)")
        missed_df["Direction"] = missed_df["direction"].str.capitalize()
        missed_df_sorted = missed_df.sort_values("startTimeEastern")
        st.dataframe(missed_df_sorted[["startTimeEastern", "Direction"]].rename(
            columns={"startTimeEastern": "Missed Call Time"}
        ))

    # --- Longest Call
    st.subheader("📞 Longest Call")
    if not answered_df.empty:
        longest = answered_df.loc[answered_df["duration"].idxmax()]
        st.write(f"🔸 {longest['startTimeEastern']} — {round(longest['duration'], 2)} minutes")
    else:
        st.write("No answered calls found.")

    # --- Gaps > 30 Minutes
    st.subheader("🚨 Time Gaps > 30 Minutes")
    df = df.sort_values("startTime")
    df["prev_end"] = df["endTime"].shift()
    df["gap"] = (df["startTime"] - df["prev_end"]).dt.total_seconds() / 60
    gap_df = df[df["gap"] > 30][["prev_end", "startTime", "gap"]].dropna()

    if not gap_df.empty:
        gap_df["prev_end"] = gap_df["prev_end"].dt.tz_convert("US/Eastern")
        gap_df["startTime"] = gap_df["startTime"].dt.tz_convert("US/Eastern")
        st.dataframe(gap_df.rename(columns={
            "prev_end": "Previous Call End",
            "startTime": "Current Call Start",
            "gap": "Gap (min)"
        }))
    else:
        st.write("✅ No gaps greater than 30 minutes found.")

    # === VISUALIZATIONS ===

    # 1. 📅 Total Calls Per Day
    st.subheader("📅 Total Calls Per Day")
    df = df[df["startTimeEastern"].notnull()]
    df["date"] = df["startTimeEastern"].dt.date
    daily_counts = df.groupby("date").size().reset_index(name="Total Calls")
    fig_calls = px.bar(
        daily_counts,
        x="date",
        y="Total Calls",
        title="Daily Call Volume",
        labels={"date": "Date", "Total Calls": "Number of Calls"}
    )
    st.plotly_chart(fig_calls, use_container_width=True)

    # 2. 📎 Answered vs Missed Pie Chart
    st.subheader("📎 Answered vs Missed Calls")
    pie_data = pd.Series({
        "Answered": answered_calls,
        "Missed": missed_calls
    }).reset_index()
    pie_data.columns = ["Status", "Count"]
    fig_pie = px.pie(
        pie_data,
        names="Status",
        values="Count",
        title="Call Outcome Breakdown",
        color_discrete_map={"Answered": "green", "Missed": "red"}
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    # 3. ⏱️ Average Call Duration Per Day (Answered Only)
    st.subheader("⏱️ Avg Answered Call Duration Per Day")
    if not answered_df.empty:
        answered_df["date"] = answered_df["startTimeEastern"].dt.date
        avg_duration_daily = (
            answered_df.groupby("date")["duration"]
            .mean()
            .reset_index(name="Avg Duration")
        )
        avg_duration_daily["Avg Duration"] = avg_duration_daily["Avg Duration"].round(2)
        fig_avg = px.bar(
            avg_duration_daily,
            x="date",
            y="Avg Duration",
            title="Average Answered Call Duration Per Day (Minutes)",
            labels={"date": "Date", "Avg Duration": "Minutes"}
        )
        st.plotly_chart(fig_avg, use_container_width=True)
