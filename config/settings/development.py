"""
Development settings for 'Góc Phụ Kiện'.
"""
from .base import *

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]", "testserver"]

# In development, print emails to console if needed
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
