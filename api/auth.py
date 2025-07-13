# api/auth.py
import os
import requests
import time

CLIENT_ID = os.getenv("06435202-5497-4fd5-ad8b-d5d0e8717b0d")
CLIENT_SECRET = os.getenv("Dio1p74JoaDukguN991rojAq")
REFRESH_TOKEN = os.getenv("eyJraWQiOiI2MjAiLCJhbGciOiJSUzUxMiJ9.eyJzYyI6ImNhbGxzLnYyLmluaXRpYXRlIGZheC52MS5yZWFkIHdlYnJ0Yy52MS53cml0ZSBjci52MS5yZWFkIHZvaWNlLWFkbWluLnYxLndyaXRlIHZvaWNlbWFpbC52MS52b2ljZW1haWxzLnJlYWQgdXNlcnMudjEucmVhZCB2b2ljZW1haWwudjEubm90aWZpY2F0aW9ucy5tYW5hZ2UgcHJlc2VuY2UudjEud3JpdGUgbWVzc2FnaW5nLnYxLndyaXRlIGZheC52MS53cml0ZSByZWNvcmRpbmcudjEubm90aWZpY2F0aW9ucy5tYW5hZ2UgY2FsbC1oaXN0b3J5LnYxLm5vdGlmaWNhdGlvbnMubWFuYWdlIG1lc3NhZ2luZy52MS5ub3RpZmljYXRpb25zLm1hbmFnZSB1c2Vycy52MS5saW5lcy5yZWFkIHdlYnJ0Yy52MS5yZWFkIHZvaWNlLWFkbWluLnYxLnJlYWQgY2FsbC1ldmVudHMudjEuZXZlbnRzLnJlYWQgZmF4LnYxLm5vdGlmaWNhdGlvbnMubWFuYWdlIHJlY29yZGluZy52MS5yZWFkIHByZXNlbmNlLnYxLm5vdGlmaWNhdGlvbnMubWFuYWdlIG1lc3NhZ2luZy52MS5zZW5kIHByZXNlbmNlLnYxLnJlYWQgdm9pY2VtYWlsLnYxLnZvaWNlbWFpbHMud3JpdGUgY2FsbC1jb250cm9sLnYxLmNhbGxzLmNvbnRyb2wgY2FsbC1ldmVudHMudjEubm90aWZpY2F0aW9ucy5tYW5hZ2UgbWVzc2FnaW5nLnYxLnJlYWQgaWRlbnRpdHk6c2NpbS5tZSIsInN1YiI6IjgzNDY1OTU0ODkxNTU2MDY4ODkiLCJhdWQiOiIwNjQzNTIwMi01NDk3LTRmZDUtYWQ4Yi1kNWQwZTg3MTdiMGQiLCJvZ24iOiJwd2QiLCJscyI6IjEzNmQyNmI2LTk2MTEtNGZjOS05NTVkLWJmZDQwMzM5OTc1OCIsInR5cCI6ImMiLCJleHAiOjE3NTI0MzY3NTUsImlhdCI6MTc1MjQzNjE1NSwidXJpIjoiaHR0cHM6Ly9vYXV0aC5wc3Rtbi5pby92MS9jYWxsYmFjayIsImp0aSI6IjkyOThhZGI3LTdmYTktNDc5Yi1hMmYzLTQwYzJiYWRjZmMxMCIsImxvYSI6M30.SwWN7MuSOSKpIbn-TkGMYzgIS4IVytWeJL4OdED3GgehIABm1UHAMTbfz7QhPrPyDrv7UtcdhnwSXpLXthvKjefnJC8BfXy5rXIH73r2a2LeFPr5DF01supk_7Q0W6v7XbtB-lBVhEvqKOGb4n7so6A-j8W2C94Ym6cTDtWS7WlI5xM79fqg6QOnJC183XcucnTD7qm-EQF6YHlPUK4-qWLgJHqk5dhwzO1zZTIXNF68Iu63aILbYkzeyqRvPswiLR_tblWog1ljI5rZYy_oTxwLA0UdAp9RCLzmStBDRRP3iwUSUlgbvOZV_hKG5-xPOOq_XN9Ho6TySM9wMqhI7g")

TOKEN_CACHE = {
    "access_token": None,
    "expires_at": 0
}

def get_access_token():
    now = time.time()
    if TOKEN_CACHE["access_token"] and TOKEN_CACHE["expires_at"] > now + 60:
        return TOKEN_CACHE["access_token"]

    url = "https://api.getgo.com/oauth/v2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }

    res = requests.post(url, data=data)
    res.raise_for_status()
    tokens = res.json()

    TOKEN_CACHE["access_token"] = tokens["access_token"]
    TOKEN_CACHE["expires_at"] = now + tokens.get("expires_in", 3600)

    return TOKEN_CACHE["access_token"]
