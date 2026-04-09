import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
client = create_client(url, key)

print("Testing profiles table...")
try:
    res = client.table("profiles").select("*").limit(2).execute()
    print("Profiles data:", res.data)
except Exception as e:
    print("Error:", e)
