"""
Django settings for cms project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'tv_6=v%3e*eqb)k24aiypdzz8qds@2oioccje8py*q7tiqluxe'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'cms.urls'

WSGI_APPLICATION = 'cms.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

TEMPLATE_DIRS = (os.path.join(BASE_DIR, 'templates'),)


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

XML_ROOT = os.path.join(BASE_DIR, 'xml/')

DBZ_HOURLY_XML = XML_ROOT + 'dbz_hourly.xml'
DBZ_FULL_XML = XML_ROOT + 'dbz_full.xml'

PF_HOURLY_XML = XML_ROOT + 'pf_hourly.xml'
PF_FULL_XML = XML_ROOT + 'pf_full.xml'


PF_HOURLY_XML_V2 = XML_ROOT + 'pf_hourly_v2.xml'
PF_FULL_XML_V2 = XML_ROOT + 'pf_full_v2.xml'


DOMAIN_NAME = 'http://www.prop-pix.com/'


MEDIA_URL = 'media/'


## Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.webfaction.com'
EMAIL_HOST_USER = 'prop_pix'
EMAIL_HOST_PASSWORD = 'quakeroats'
DEFAULT_FROM_EMAIL = 'support@prop-pix.com'
SERVER_EMAIL = 'support@prop-pix.com'

WATERMARK = os.path.join(BASE_DIR, 'logo_final.png')
WATERMARK_OPACITY = 0.25
