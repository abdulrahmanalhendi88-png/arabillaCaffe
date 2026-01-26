from pathlib import Path
import os

# جذر المشروع الحقيقي
BASE_DIR = Path(__file__).resolve().parent.parent

# مسار الداتا الدائم على Render (Persistent Disk)
DATA_DIR = Path(os.getenv("DATA_DIR", "/var/data"))

DEBUG = os.getenv("DEBUG", "0") == "1"
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")

# hosts
if DEBUG:
    ALLOWED_HOSTS = ["*"]
else:
    # لمنع [''] إذا المتغير فاضي
    ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "menu",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "arabella.urls"
WSGI_APPLICATION = "arabella.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # هون لازم تضل على BASE_DIR تبع المشروع
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

# SQLite على الديسك الدائم
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(DATA_DIR / "db.sqlite3"),
    }
}

LANGUAGE_CODE = "ar"
TIME_ZONE = "Asia/Damascus"
USE_I18N = True
USE_TZ = True

# Static عبر collectstatic + WhiteNoise
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]  # لو عندك مجلد static داخل المشروع

# Media على الديسك الدائم
MEDIA_URL = "/media/"
MEDIA_ROOT = str(DATA_DIR / "media")

STORAGES = {
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# (مفيد على Render) إذا واجهت مشكلة CSRF عند تسجيل الدخول للـ admin عبر https
# CSRF_TRUSTED_ORIGINS = ["https://your-app.onrender.com"]
CSRF_TRUSTED_ORIGINS = ["https://arabillacaffe.onrender.com"]

