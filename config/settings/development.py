"""
Development settings for 'Góc Phụ Kiện'.
"""
from .base import *

DEBUG = True

# In development, print emails to console if needed
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
