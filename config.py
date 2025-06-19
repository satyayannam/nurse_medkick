import os
from dotenv import load_dotenv
load_dotenv()

ACCESS_TOKEN = os.getenv("GOTO_ACCESS_TOKEN")
ACCOUNT_KEY = os.getenv("GOTO_ACCOUNT_KEY")
BASE_URL = os.getenv("GOTO_BASE_URL", "https://api.goto.com")
