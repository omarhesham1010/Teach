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

# Explicitly disable MEDIA_URL in production so we don't get relative paths
# Cloudinary will provide absolute URLs
MEDIA_URL = '/media/' # Keeping it for now as some libs expect it, but storage backend overrides it.
# Actually, let's allow the storage to drive.

CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL')
if CLOUDINARY_URL:
    # Use the official library to parse the URL safely
    config = cloudinary.config(parse_conversion_features=False) 
    # config is already set globally by the library reading the env var!
    # But django-cloudinary-storage needs CLOUDINARY_STORAGE dict.
    
    # We can extract from the global config if the env var was read
    # OR we just populate the dict from the env var directly as better practice
    
    # Let's extract manually but safer than regex
    # cloudinary://API_KEY:API_SECRET@CLOUD_NAME
    
    try:
        prefix = "cloudinary://"
        if CLOUDINARY_URL.startswith(prefix):
            creds = CLOUDINARY_URL[len(prefix):]
            api_part, cloud_name = creds.split('@')
            api_key, api_secret = api_part.split(':')
            
            CLOUDINARY_STORAGE = {
                'CLOUD_NAME': cloud_name,
                'API_KEY': api_key,
                'API_SECRET': api_secret,
            }
    except Exception:
        # Fallback or pass (will error on upload if failed)
        pass

# Security
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True') == 'True'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
CSRF_TRUSTED_ORIGINS = ['https://*.onrender.com']

# Static Files (WhiteNoise)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
