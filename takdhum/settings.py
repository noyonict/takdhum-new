import os
import configparser
from django.contrib.messages import constants as messages

# ---------------------------------------------------------------------------
# ENVIRONMENT SWITCH
# Set PRODUCTION = True for PythonAnywhere, False for local development.
# ---------------------------------------------------------------------------
PRODUCTION = True

# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = '=mr=m*i)*lhfxx63ddo9!w9aofbrt7$)_xp0#p1l_z4(xv$4++'

DEBUG = not PRODUCTION

ALLOWED_HOSTS = ['www.takdhum.com', 'takdhum.com', '127.0.0.1', 'localhost']

# ---------------------------------------------------------------------------
# DATABASE
# ---------------------------------------------------------------------------
if PRODUCTION:
    # Read MySQL password from PythonAnywhere's ~/.my.cnf
    _mysql_conf = configparser.ConfigParser()
    _mysql_conf.read(os.path.expanduser('~/.my.cnf'))
    _MYSQL_PASSWORD = (
        os.environ.get('TAKDHUM_DB_PASSWORD') or
        _mysql_conf.get('client', 'password', fallback=None) or
        _mysql_conf.get('mysqldump', 'password', fallback=None) or
        _mysql_conf.get('mysql', 'password', fallback='')
    ).strip('"\'')

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'romanahme$takdhum4',
            'USER': 'romanahme',
            'PASSWORD': _MYSQL_PASSWORD,
            'HOST': 'romanahme.mysql.pythonanywhere-services.com',
            'PORT': '',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }

# ---------------------------------------------------------------------------
# STATIC & MEDIA FILES
# ---------------------------------------------------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

if PRODUCTION:
    STATIC_ROOT = '/home/romanahme/takdhum4/static_cdn/'
    MEDIA_ROOT  = '/home/romanahme/media_cdn/'
else:
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media_cdn')

MEDIA_URL = '/media_cdn/'

# ---------------------------------------------------------------------------
# EMAIL
# ---------------------------------------------------------------------------
EMAIL_USE_TLS       = True
EMAIL_HOST          = 'smtp.gmail.com'
EMAIL_PORT          = 587
EMAIL_HOST_USER     = 'info.takdhum@gmail.com'
EMAIL_HOST_PASSWORD = 'Takdhum123'

# ---------------------------------------------------------------------------
# APPLICATION
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    'web',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap4',
    'django_filters',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'takdhum.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
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

WSGI_APPLICATION = 'takdhum.wsgi.application'

AUTH_PASSWORD_VALIDATORS = []

# ---------------------------------------------------------------------------
# INTERNATIONALISATION
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'Asia/Dhaka'
USE_I18N      = True
USE_L10N      = True
USE_TZ        = True

# ---------------------------------------------------------------------------
# MISC
# ---------------------------------------------------------------------------
MESSAGE_TAGS = {
    messages.INFO:    'alert alert-info',
    messages.SUCCESS: 'alert alert-success',
    messages.WARNING: 'alert alert-warning',
    messages.ERROR:   'alert alert-danger',
    messages.DEBUG:   'alert alert-info',
}

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap4'
CRISPY_TEMPLATE_PACK          = 'bootstrap4'

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

LOGIN_REDIRECT_URL  = 'profile'
LOGOUT_REDIRECT_URL = 'index'
