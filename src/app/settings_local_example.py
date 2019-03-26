import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases
DEBUG = False
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ccexchange',
        'USER': 'ccexchange',
        'PASSWORD': 'ccexchanger',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}
MEDIA_ROOT = os.path.join(BASE_DIR, 'static/media/')
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
COMPRESS_ROOT = os.path.join(BASE_DIR, 'static/compressor/')
COMPRESS_ENABLED = True