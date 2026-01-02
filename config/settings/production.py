from .base import *
import dj_database_url
import os

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

CLOUDINARY_STORAGE = {
    'CLOUDINARY_URL': os.environ.get('CLOUDINARY_URL'),
    # Fallbacks if individual vars are used instead of the full URL
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'), 
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
}

# Security
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True') == 'True'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
CSRF_TRUSTED_ORIGINS = ['https://*.onrender.com']

# Static Files (WhiteNoise)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
