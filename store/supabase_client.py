from supabase import create_client, Client
from django.conf import settings
from decouple import config

# Dapatkan URL dan Key dari env
url: str = config('SUPABASE_URL', default='')
key: str = config('SUPABASE_KEY', default='')

def get_supabase_client() -> Client:
    if not url or not key:
        return None
    return create_client(url, key)
