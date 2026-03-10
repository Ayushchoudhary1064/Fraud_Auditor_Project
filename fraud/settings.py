# fraud/settings.py

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'iA2LVbrcPpH5NeFw5jdTHf8TWA17FuDkTb4O2t6clLpHSMvK8WE-BDeW-0WMsI_vT1g' # CHANGE THIS IN PRODUCTION!

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True # Set to False in production

ALLOWED_HOSTS = [] # Add your domain names here in production, e.g., ['yourdomain.com', 'www.yourdomain.com']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'auditor', # Your application
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

ROOT_URLCONF = 'fraud.urls' # Corrected to 'fraud.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')], # Add a project-level templates directory
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media', # Essential for media URL
            ],
        },
    },
]

WSGI_APPLICATION = 'fraud.wsgi.application' # Corrected to 'fraud.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata' # Set to your local timezone if desired, otherwise 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') # For collectstatic in production

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'), # Project-wide static files
]


# Media files (user-uploaded/dynamically generated)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'auditor.CustomUser' # This is correct, as 'auditor' is your app name

# Login Redirect URL
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

# Fraud Detection Thresholds (Add these, adjust values as needed)
FRAUD_COMMUNITY_SIZE_THRESHOLD = 5 # Example: Flag if patient is in a community of 5 or more
FRAUD_PROVIDER_CLAIM_COUNT_THRESHOLD = 10 # Example: Flag if a provider has more than 50 claims
FRAUD_PROCEDURE_CODE_PREFIXES = ['P9', 'X7'] # Example: Flag if procedure code starts with these
FRAUD_DIAGNOSIS_CODE_PREFIXES = ['D9', 'Z1'] # Example: Flag if diagnosis code starts with these
FRAUD_TOTAL_SCORE_THRESHOLD = 1 # Example: Flag as rejected if overall score is 2 or more
FRAUD_COMMUNITY_SIZE_THRESHOLD = 3