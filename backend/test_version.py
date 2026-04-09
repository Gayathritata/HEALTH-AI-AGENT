from supabase import create_client
import sys

print('Supabase client version:')
try:
    import pkg_resources
    print(pkg_resources.get_distribution('supabase').version)
except Exception:
    print('unknown')
