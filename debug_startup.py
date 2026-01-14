import os
import sys
import traceback

print("Starting debug script...", flush=True)

try:
    print("Setting environment...", flush=True)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nothing_brain_project.settings')
    
    print("Importing get_wsgi_application...", flush=True)
    from django.core.wsgi import get_wsgi_application
    
    print("Calling get_wsgi_application()...", flush=True)
    application = get_wsgi_application()
    
    print("Success! WSGI application loaded.", flush=True)

except Exception:
    print("Caught exception!", flush=True)
    traceback.print_exc()
