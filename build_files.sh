
# Install dependencies
pip install -r requirements.txt

# Collect Static Files (Whitenoise)
python manage.py collectstatic --noinput
