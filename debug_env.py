import os
import sys

print(f"Python Executable: {sys.executable}", flush=True)
print(f"Python Version: {sys.version}", flush=True)
print("Sys Path:", flush=True)
for p in sys.path:
    print(f"  {p}", flush=True)

try:
    import whitenoise
    print(f"Whitenoise found at: {whitenoise.__file__}", flush=True)
except ImportError:
    print("Whitenoise NOT found!", flush=True)
