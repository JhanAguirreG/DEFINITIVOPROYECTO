from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url
# --------------------------------------------------
# BASE
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
SECRET_KEY = 'jhanprueba'

DEBUG = True

import os

ALLOWED_HOSTS = os.environ.get(
    "ALLOWED_HOSTS",
    "127.0.0.1,localhost"
).split(",")
# --------------------------------------------------
# APLICACIONES
# --------------------------------------------------

INSTALLED_APPS = [
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "django_extensions",

    # Apps del proyecto
    'apps.usuarios',
    'apps.instituciones',
    'apps.servicios',
    'apps.equipos',
    'apps.inspecciones',
    'apps.catalogo',
    'apps.hojas_vida',
    'apps.mantenimiento',
    "apps.calibraciones",
        
]

# --------------------------------------------------
# MIDDLEWARE
# --------------------------------------------------

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


# --------------------------------------------------
# URLS
# --------------------------------------------------

ROOT_URLCONF = 'sighi.urls'


# --------------------------------------------------
# TEMPLATES (IMPORTANTE)
# --------------------------------------------------

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        # Puedes dejarlo vacío porque usaremos templates dentro de la app
        'DIRS': [BASE_DIR / 'templates'],

        'APP_DIRS': True,  # 🔥 ESTO DEBE ESTAR EN TRUE

        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# --------------------------------------------------
# WSGI
# --------------------------------------------------

WSGI_APPLICATION = 'sighi.wsgi.application'


# --------------------------------------------------
# BASE DE DATOS
# --------------------------------------------------

DATABASES = {
    "default": dj_database_url.config(
        conn_max_age=600,
        ssl_require=True,
    )
}


# --------------------------------------------------
# VALIDACIÓN DE PASSWORD
# --------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# --------------------------------------------------
# INTERNACIONALIZACIÓN
# --------------------------------------------------

LANGUAGE_CODE = 'es-co'

TIME_ZONE = 'America/Bogota'

USE_I18N = True
USE_TZ = True


# --------------------------------------------------
# ARCHIVOS ESTÁTICOS
# --------------------------------------------------

STATIC_URL = "static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
# 2. Credenciales y parámetros del Object Storage de Neon
AWS_STORAGE_BUCKET_NAME = os.environ.get("NEON_STORAGE_BUCKET_NAME")
AWS_S3_ENDPOINT_URL = os.environ.get("NEON_STORAGE_ENDPOINT_URL")
AWS_ACCESS_KEY_ID = os.environ.get("NEON_STORAGE_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("NEON_STORAGE_SECRET_ACCESS_KEY")

# Evita que boto3 intente consultar metadatos de AWS EC2 de forma innecesaria
AWS_PRELOAD_METADATA = True
AWS_QUERYSTRING_AUTH = False  # Mantiene las URLs de los archivos limpias y públicas para lectura

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# --------------------------------------------------
# ARCHIVOS MEDIA (PDFS Y FIRMAS)
# --------------------------------------------------



# --------------------------------------------------
# LOGIN
# --------------------------------------------------
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"
#LOGIN_REDIRECT_URL = '/inspecciones/'


# --------------------------------------------------
# DEFAULT PRIMARY KEY
# --------------------------------------------------

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'usuarios.Usuario'