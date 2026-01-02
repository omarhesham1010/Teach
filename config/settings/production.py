from .base import *
import dj_database_url
import os
import cloudinary

DEBUG = False

# Render sets ALLOWED_HOSTS for us or we set it manually
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',') + ['.onrender.com']

# Database
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=True
    )
}

# Cloudinary Storage Configuration
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Using cloudinary library to parse CLOUDINARY_URL safely
CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL')
if CLOUDINARY_URL:
    # This automatically reads the env var and sets global config
    config = cloudinary.config()
    
    # Populate the dict that django-cloudinary-storage expects
    if config.cloud_name:
        CLOUDINARY_STORAGE = {
            'CLOUD_NAME': config.cloud_name,
            'API_KEY': config.api_key,
            'API_SECRET': config.api_secret,
        }

# Security
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True') == 'True'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
CSRF_TRUSTED_ORIGINS = ['https://*.onrender.com']

# Static Files (WhiteNoise)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
