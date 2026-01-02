from .base import *
# WARNING: This file is for LOCAL DEVELOPMENT ONLY.
# NEVER use this in production. It contains hardcoded credentials and disables security features.
import os

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'teach_db',
        'USER': 'postgres',
        'PASSWORD': '123', # Change this if needed
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Email Backend for Development (Console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# --- CLOUDINARY CONFIGURATION FOR LOCAL TESTING ---
CLOUDINARY_STORAGE = {
    'CLOUDINARY_URL': os.environ.get('CLOUDINARY_URL'),
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
}

# Use Cloudinary for Media, but Local for Static (faster dev)
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
