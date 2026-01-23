"""
Script to collect static files for Vercel deployment.
Run this locally before pushing to generate admin static files.

Usage:
    python collect_for_vercel.py
"""
import os
import sys

# Set minimal environment for collectstatic
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nothing_brain_project.settings')
os.environ['SECRET_KEY'] = 'temporary-key-for-collectstatic-only'
os.environ['DEBUG'] = 'True'
os.environ['DATABASE_URL'] = 'sqlite:///temp.db'

import django
django.setup()

from django.core.management import call_command

print("=" * 50)
print("Collecting static files for Vercel...")
print("=" * 50)

call_command('collectstatic', '--noinput', '--clear')

print("\n" + "=" * 50)
print("Done! Now commit the 'staticfiles/' directory:")
print("  git add staticfiles/")
print("  git commit -m 'Add static files for Vercel'")
print("  git push")
print("=" * 50)
