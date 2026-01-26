"""
Django settings for nothing_brain_project.

Updated for: Supabase, Midtrans, RajaOngkir, Whitenoise, & Security.
"""

from pathlib import Path
from decouple import config
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# ==============================================================================
# 1. SECURITY SETTINGS
# ==============================================================================

# SECRET_KEY diambil dari file .env
SECRET_KEY = config('SECRET_KEY', default='django-insecure-fallback-key-for-dev-only')

# DEBUG mode (True untuk Development, False untuk Production)
DEBUG = config('DEBUG', default=False, cast=bool)

# Host yang diizinkan mengakses website
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    '.vercel.app',
    'nothingbrain.store',
    '.nothingbrain.store',
    config('NGROK_HOSTNAME', default=''),
]

# Agar CSRF aman saat menggunakan Ngrok atau HTTPS
CSRF_TRUSTED_ORIGINS = [
    "https://*.ngrok-free.dev",
    "https://nothingbrain.store",
    "https://*.vercel.app",
]
if config('NGROK_HOSTNAME', default=''):
    CSRF_TRUSTED_ORIGINS.append(f"https://{config('NGROK_HOSTNAME')}")


# ==============================================================================
# 2. INSTALLED APPS
# ==============================================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Library Tambahan
    'storages', # <--- Untuk Supabase Storage / S3
    'imagekit', # <--- Untuk Image Optimization (resize, compress)
    'django.contrib.humanize', # Untuk format Rupiah (intcomma)

    # Apps Buatan Sendiri
    'store.apps.StoreConfig',
    'dashboard.apps.DashboardConfig',
]


# ==============================================================================
# 3. MIDDLEWARE
# ==============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    
    # WAJIB: Whitenoise untuk file statis di Production
    'whitenoise.middleware.WhiteNoiseMiddleware',
    
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'nothing_brain_project.urls'


# ==============================================================================
# 4. TEMPLATES
# ==============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Include project templates
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                
                # Context Processors Custom
                'store.context_processors.cart',
                'dashboard.context_processors.stock_notifications',
                'nothing_brain_project.context_processors.global_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'nothing_brain_project.wsgi.application'


# ==============================================================================
# 5. DATABASE (SUPABASE / POSTGRESQL)
# ==============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', cast=int),
        'OPTIONS': {
            'options': '-c search_path=public',
        },
    }
}


# ==============================================================================
# 6. PASSWORD VALIDATION
# ==============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ==============================================================================
# 7. INTERNATIONALIZATION
# ==============================================================================

LANGUAGE_CODE = 'id-id'
TIME_ZONE = 'Asia/Jakarta'
USE_I18N = True
USE_TZ = True


# ==============================================================================
# 8. STATIC FILES (Whitenoise Config)
# ==============================================================================

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise Configuration for Vercel (read-only filesystem)
# This allows WhiteNoise to serve files directly without requiring collectstatic
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True

# Tailwind Config
# Set True untuk menggunakan CDN (Aman untuk Vercel jika NPM gagal)
# Set False jika menggunakan local build 'static/css/output.css'
USE_TAILWIND_CDN = config('USE_TAILWIND_CDN', default=True, cast=bool)


# ==============================================================================
# 9. MEDIA FILES (SUPABASE STORAGE / S3)
# ==============================================================================

# Jika variabel Supabase diatur di .env, gunakan S3 Storage
if config('SUPABASE_ACCESS_KEY_ID', default=None):
    AWS_ACCESS_KEY_ID = config('SUPABASE_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = config('SUPABASE_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = config('SUPABASE_STORAGE_BUCKET_NAME')
    AWS_S3_ENDPOINT_URL = config('SUPABASE_S3_ENDPOINT_URL')
    AWS_S3_REGION_NAME = config('SUPABASE_S3_REGION_NAME', default='ap-southeast-1')

    AWS_S3_FILE_OVERWRITE = True
    AWS_DEFAULT_ACL = None
    AWS_S3_VERIFY = True

    AWS_S3_OBJECT_PARAMETERS = {
            'CacheControl': 'max-age=31536000',  # 1 year cache for images
        }

    # PERBAIKAN: Gunakan WhiteNoise untuk staticfiles agar admin CSS berfungsi
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
        },
    }
    
    # URL Media mengarah ke Supabase
    MEDIA_URL = f'{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/'

else:
    # Fallback ke penyimpanan lokal jika tidak ada config Supabase
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'
    
    # WhiteNoise untuk production tanpa Supabase
    if not DEBUG:
        STORAGES = {
            "default": {
                "BACKEND": "django.core.files.storage.FileSystemStorage",
            },
            "staticfiles": {
                "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
            },
        }


# ==============================================================================
# 13. CACHING (LocMemCache - Safer for Vercel)
# ==============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# ==============================================================================
# 10. DEFAULT SETTINGS
# ==============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login/Logout Redirect
LOGIN_URL = 'store:login'
LOGIN_REDIRECT_URL = 'store:landing_page'
LOGOUT_REDIRECT_URL = 'store:landing_page'

# Session ID untuk Keranjang
CART_SESSION_ID = 'cart'

# WhiteNoise Storage (Compression + Caching)
# Gunakan CompressedStaticFilesStorage agar tidak error 500 jika ada file yang hilang
if not DEBUG:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"


# ==============================================================================
# 12. EMAIL CONFIGURATION
# ==============================================================================
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@nothingbrain.store')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')


# ==============================================================================
# 11. THIRD PARTY INTEGRATION (KEYS)
# ==============================================================================

# Midtrans Payment Gateway
MIDTRANS_CLIENT_KEY = config('MIDTRANS_CLIENT_KEY', default='')
MIDTRANS_SERVER_KEY = config('MIDTRANS_SERVER_KEY', default='')
MIDTRANS_IS_PRODUCTION = config('MIDTRANS_IS_PRODUCTION', default=False, cast=bool)

# RajaOngkir API
RAJAONGKIR_API_KEY = config('RAJAONGKIR_API_KEY', default='')
RAJAONGKIR_ORIGIN_CITY_ID = config('RAJAONGKIR_ORIGIN_CITY_ID', default='152')