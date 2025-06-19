# api/calls.py
import requests
from config import ACCESS_TOKEN, ACCOUNT_KEY, BASE_URL

def get_user_calls(user_key, start_time, end_time):
    url = f"{BASE_URL}/call-history/v1/calls"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    params = {
        "userKey": user_key,
        "accountKey": ACCOUNT_KEY,
        "startTime": start_time,
        "endTime": end_time,
        "pageSize": 100
    }

    print("📞 Fetching calls with:", params)
    res = requests.get(url, headers=headers, params=params)
    print("🔍 Status:", res.status_code)
    print("📦 Raw:", res.text)

    res.raise_for_status()
    data = res.json()
    return data.get("items", [])

