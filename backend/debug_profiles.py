#!/usr/bin/env python3
"""Debug script to check profile data in Supabase"""

from dotenv import load_dotenv
load_dotenv()

from app.services.supabase_client import get_supabase_client

client = get_supabase_client()
if client:
    try:
        result = client.table('profiles').select('*').limit(5).execute()
        print('Profiles in database:')
        if result.data:
            for profile in result.data:
                user_id = profile.get('id', 'unknown')[:8] if profile.get('id') else 'unknown'
                name = profile.get('full_name', 'N/A')
                appt = profile.get('appointment_id', 'N/A')
                print(f'  - ID: {user_id}... | Name: {name} | Appt: {appt}')
        else:
            print('  ❌ No profiles found in database!')
    except Exception as e:
        print(f'❌ Error querying profiles: {e}')
else:
    print('❌ Supabase not connected')
