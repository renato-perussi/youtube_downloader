"""Configuracao base do projeto."""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / '.env')

ENVIRONMENT = os.getenv('ENVIRONMENT', 'dev')

SECRET_KEY = os.getenv('SECRET_KEY', '')

_WEAK_MARKERS = ('insecure', 'django-insecure', 'change-me', 'troque-por', 'placeholder')

if ENVIRONMENT == 'prd':
    lowered = SECRET_KEY.lower()
    if len(SECRET_KEY) < 32 or any(marker in lowered for marker in _WEAK_MARKERS):
        raise ImproperlyConfigured(
            'Defina SECRET_KEY forte (>=32 chars, sem marcadores inseguros) quando ENVIRONMENT=prd.'
        )
    if SECRET_KEY.startswith('dev-'):
        raise ImproperlyConfigured('Defina SECRET_KEY forte quando ENVIRONMENT=prd.')

if not SECRET_KEY:
    SECRET_KEY = 'dev-insecure-key-change-me'

DEBUG = os.getenv('DEBUG', 'False') == 'True'

if ENVIRONMENT == 'prd' and DEBUG:
    raise ImproperlyConfigured('DEBUG deve ser False quando ENVIRONMENT=prd.')

ALLOWED_HOSTS = [
    h.strip() for h in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'ytdownloader',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'ytdownloader.context_processors.tenant',
            ],
        },
    },
]

WSGI_APPLICATION = 'app.wsgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'login_redirect'
LOGOUT_REDIRECT_URL = 'login'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

YTDLP_DOWNLOAD_DIR_NAME = 'downloads'

SESSION_KEY_VIDEO_INFO = 'download_video_info'
