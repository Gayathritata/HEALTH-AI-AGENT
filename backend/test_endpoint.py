import os
import requests
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
client = create_client(url, key)

# Login
try:
    auth_res = client.auth.sign_in_with_password({
        "email": "1231775575929698@test.com", 
        "password": "defaultpassword123"
    })
    token = auth_res.session.access_token
    print("Logged in, token:", token[:10] + "...")

    # Access endpoint
    res = requests.get("http://127.0.0.1:8000/api/profile", headers={"Authorization": f"Bearer {token}"})
    print("Endpoint result:", res.status_code, res.text)
except Exception as e:
    print("Exception:", e)
