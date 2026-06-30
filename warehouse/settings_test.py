from .settings import *  # noqa

# Use SQLite for fast tests — no Postgres needed in CI
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Disable password hashing for faster tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable whitenoise manifest check in tests
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

DEBUG = True
SECRET_KEY = "test-secret-key"