# In match.py, can't access dev_settings via "from django.conf import settings"  since this and that are in no ways connected
import redis
import os
from django.views.decorators.cache import cache_page
print("Running in DEV mode")
# ***DEV vs PROD
SECRET_KEY = os.environ['secret_key']
ADMIN_USERNAME = os.environ['admin_username']
ADMIN_USER_ID = os.environ['admin_user_id']
DEBUG = True
ALLOWED_HOSTS = ["*"]

SESSION_COOKIE_SECURE = False # True
SECURE_SSL_REDIRECT = False # Truee

# For HTTPS connections, https://stackoverflow.com/a/49168623
SECURE_HSTS_SECONDS = 0 # Read above answer for correct value

CACHE_EXPIRE_SECONDS = 1 # decimal value wont work.High value in prod

# In Prod,store credentials in environment variables
DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.postgresql_psycopg2',
		'NAME': 'chat',
		'USER': os.environ['postgres_username'],
		'PASSWORD': os.environ['postgres_password'],
		'HOST': 'localhost',
		'PORT': os.environ['postgres_port'],
	}
}
# ---DEV vs PROD

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_LOCATION=BASE_DIR + '/front_end'
LOGIN_URL = '/login/'
INSTALLED_APPS = [
	'channels',
	'chat',
	'rest_framework',
	# this is required for importing Token in consumers.weird
	'rest_framework.authtoken',
	'django.contrib.auth',
	'django.contrib.contenttypes',
	'django.contrib.sessions',
	'django.contrib.messages',
	'corsheaders',
]

CORS_ORIGIN_WHITELIST = (
    'http://localhost:8001',
)

#Allowing token authentication
REST_FRAMEWORK = {
	'DEFAULT_AUTHENTICATION_CLASSES': (
		'rest_framework.authentication.TokenAuthentication',
	),
}

MIDDLEWARE = [
	'corsheaders.middleware.CorsMiddleware',
	'django.middleware.security.SecurityMiddleware',
	'django.middleware.clickjacking.XFrameOptionsMiddleware' ,
	'django.middleware.csrf.CsrfViewMiddleware',
]

ROOT_URLCONF = 'mysite.urls'

TEMPLATES = [
	{
		'BACKEND': 'django.template.backends.django.DjangoTemplates',
		'DIRS': [TEMPLATE_LOCATION],
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

STATIC_URL = '/static/'
STATIC_ROOT = TEMPLATE_LOCATION

ASGI_APPLICATION = 'mysite.asgi.application'

# algo.py
CHANNEL_LAYERS = {
	'default': {
		'BACKEND': 'channels_redis.core.RedisChannelLayer',
		'CONFIG': {
			"hosts": [('127.0.0.1', 6379)],
		},
	},
}

REDIS_CACHE_DB = 5
redis_client = redis.Redis(host='localhost', port=6379, db=REDIS_CACHE_DB)
print(f"@settings.py: flushing redis_db no:{REDIS_CACHE_DB} which is used for caching views")
redis_client.flushdb()

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/"+str(REDIS_CACHE_DB),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        },
        "KEY_PREFIX": "c42_cache"
    }
}