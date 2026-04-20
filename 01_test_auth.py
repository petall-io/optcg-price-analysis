import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("JUSTTCG_API_KEY")

BASE_URL = "https://api.justtcg.com/v1"

headers = {"x-api-key": API_KEY}

# look at games and structure
resp = requests.get(f"{BASE_URL}/games", headers=headers, timeout=30)
print("Status:", resp.status_code)
print(resp.text[:1000])
resp.raise_for_status()

