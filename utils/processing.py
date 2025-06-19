import pandas as pd

def analyze_calls(calls):
    df = pd.DataFrame(calls)
    if df.empty:
        return None

    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df["duration"] = pd.to_numeric(df["duration"], errors="coerce")
    df["endTime"] = df["startTime"] + pd.to_timedelta(df["duration"], unit="s")
    df["duration_minutes"] = df["duration"] / 60

    df["direction"] = df["direction"].fillna("UNKNOWN")

    # Identify missed calls: assume duration = 0 is missed
    df["missed"] = df["duration"] == 0

    return {
        "df": df,
        "total_calls": len(df),
        "missed_calls": df["missed"].sum(),
        "incoming": len(df[df["direction"] == "INBOUND"]),
        "outgoing": len(df[df["direction"] == "OUTBOUND"]),
    }
