# api/users.py
import requests
from config import ACCESS_TOKEN, ACCOUNT_KEY, BASE_URL

# api/users.py
def get_users():
    url = f"{BASE_URL}/users/v1/users?accountKey={ACCOUNT_KEY}"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json().get("items", [])  # <-- this line is critical


