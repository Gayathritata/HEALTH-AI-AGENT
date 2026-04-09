import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
client = create_client(url, key)

try:
    res = client.table("profiles").select("*").execute()
    print("PROFILES DATA:")
    print(res.data)
except Exception as e:
    print("ERROR:", e)
