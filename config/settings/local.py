from .base import *
# WARNING: This file is for LOCAL DEVELOPMENT ONLY.
# NEVER use this in production. It contains hardcoded credentials and disables security features.
import os

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Database
# Use local PostgreSQL
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
