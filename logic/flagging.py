# logic/flagging.py
import pandas as pd
from datetime import datetime
import plotly.express as px
import pytz

def process_call_data(calls, start_datetime: datetime, end_datetime: datetime, gap_threshold: int):
    df = pd.DataFrame(calls)
    if df.empty:
        return None

    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df["duration"] = pd.to_numeric(df["duration"], errors="coerce")
    df["endTime"] = df["startTime"] + pd.to_timedelta(df["duration"], unit="s")

    # ✅ Add this block to handle 'missed' calls
    if "outcome" in df.columns:
        df["missed"] = df["duration"] == 0

    else:
        df["missed"] = False

    df = df.dropna(subset=["startTime", "endTime"])
    df["duration_minutes"] = (df["endTime"] - df["startTime"]).dt.total_seconds() / 60
    df = df.sort_values("startTime")

    df["prev_end"] = df["endTime"].shift()
    df["gap_minutes"] = (df["startTime"] - df["prev_end"]).dt.total_seconds() / 60
    df["gap_minutes"] = df["gap_minutes"].fillna(0)

    flagged = df[df["gap_minutes"] > gap_threshold].copy()

    fig_gap_dist = px.histogram(df, x="gap_minutes", nbins=20, title="Gap Between Calls (Minutes)")
    fig_timeline = px.timeline(df, x_start="startTime", x_end="endTime", y=df.index.astype(str), title="Call Timeline")
    fig_timeline.update_yaxes(title="Call Index")

    return {
        "df": df,
        "total_call_time": df["duration_minutes"].sum(),
        "flagged_gaps": flagged,
        "flag_count": len(flagged),
        "fig_gap_dist": fig_gap_dist,
        "fig_timeline": fig_timeline
    }
