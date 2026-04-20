import os
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent / ".env"
print(".env path:", ENV_PATH)
print(".env exists:", ENV_PATH.exists())

load_dotenv(dotenv_path=ENV_PATH, override=True)

key = os.getenv("JUSTTCG_API_KEY")
print("Key is None?:", key is None)
print("Key preview:", key[:6] if key else None)
print("Key length:", len(key) if key else None)