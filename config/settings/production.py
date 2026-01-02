from .base import *
import dj_database_url
import os

DEBUG = False

# Render sets ALLOWED_HOSTS for us or we set it manually
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',') + ['.onrender.com']

# Database
# https://github.com/jazzband/dj-database-url
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=True
    )
}

# Cloudinary Storage Configuration
# Parse CLOUDINARY_URL if present (Render often provides this single var)
CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL')
if CLOUDINARY_URL:
    # Format: cloudinary://<api_key>:<api_secret>@<cloud_name>
    import re
    match = re.match(r'cloudinary://(.*):(.*)@(.*)', CLOUDINARY_URL)
    if match:
        CLOUDINARY_STORAGE = {
            'CLOUD_NAME': match.group(3),
            'API_KEY': match.group(1),
            'API_SECRET': match.group(2),
        }

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Security
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True') == 'True'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
CSRF_TRUSTED_ORIGINS = ['https://*.onrender.com']

# Static Files (WhiteNoise)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
