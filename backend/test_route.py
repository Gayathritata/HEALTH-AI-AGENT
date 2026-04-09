import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
client = create_client(url, key)

import app.services.supabase_client as sc
print("Module imported")

# We don't have a valid jwt, wait, can we get one?
