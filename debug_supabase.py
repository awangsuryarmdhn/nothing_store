import sys
import os

print("Python Executable:", sys.executable)
print("Python Version:", sys.version)
print("Current Working Directory:", os.getcwd())
print("\nSys Path:")
for p in sys.path:
    print(p)

print("\nAttempting to import supabase...")
try:
    import supabase
    print("SUCCESS: supabase module found.")
    print("supabase file:", supabase.__file__)
except ImportError as e:
    print("FAILURE: Could not import supabase.")
    print(e)

print("\nAttempting to import supabase.client...")
try:
    from supabase import create_client, Client
    print("SUCCESS: imported create_client and Client.")
except ImportError as e:
    print("FAILURE: Could not import create_client/Client from supabase.")
    print(e)
