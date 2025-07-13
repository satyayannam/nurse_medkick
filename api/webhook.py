import streamlit as st
from datetime import datetime, timedelta
import pytz
import pandas as pd
from api.calls import get_user_calls
from api.users import get_users

def serve_data_for_webhook(user_name, start, end):
    users = get_users()
    user_key = None
    for u in users:
        if user_name.lower() in str(u).lower():
            user_key = u["userKey"]
            break

    if not user_key:
        return {"error": "User not found"}

    shift_start = datetime.strptime(start, "%Y-%m-%d")
    shift_end = datetime.strptime(end, "%Y-%m-%d")
    shift_start_str = shift_start.strftime("%Y-%m-%dT00:00:00Z")
    shift_end_str = shift_end.strftime("%Y-%m-%dT23:59:59Z")

    calls = get_user_calls(user_key, shift_start_str, shift_end_str)
    df = pd.DataFrame(calls)
    df["duration"] = pd.to_numeric(df.get("duration", 0), errors="coerce") / 60000
    df["duration"] = df["duration"].fillna(0)

    answered = df[df["duration"] > 0]
    missed = df[df["duration"] == 0]

    return {
        "user": user_name,
        "total_calls": len(df),
        "answered_calls": len(answered),
        "missed_calls": len(missed),
        "avg_duration": round(answered["duration"].mean() or 0, 2),
        "total_duration": round(answered["duration"].sum(), 2)
    }
