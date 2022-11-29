import redis
import os
# import sentry_sdk
# from sentry_sdk.integrations.django import DjangoIntegration
from django.views.decorators.cache import cache_page

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = 'd(0_a+($7*dbbgchr-s(@+#!9q408ja20b+b70(uote0fliff9'
DEBUG = True
ALLOWED_HOSTS = ["*"]
template_loc=BASE_DIR+'/front_end'
# for serving ws_tester.html
template_loc2=BASE_DIR+'/chat'
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
# bug
CORS_ORIGIN_ALLOW_ALL = True 


# MUST:Allowing token authentication
REST_FRAMEWORK = {
	'DEFAULT_AUTHENTICATION_CLASSES': (
		'rest_framework.authentication.TokenAuthentication',
	),
}

MIDDLEWARE = [
	'corsheaders.middleware.CorsMiddleware',
	#'django.middleware.security.SecurityMiddleware',
	#'django.contrib.sessions.middleware.SessionMiddleware',
	#'django.middleware.common.CommonMiddleware',
	#'django.middleware.csrf.CsrfViewMiddleware',
	#'django.contrib.auth.middleware.AuthenticationMiddleware',
	#'django.contrib.messages.middleware.MessageMiddleware',
	#'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mysite.urls'

TEMPLATES = [
	{
		'BACKEND': 'django.template.backends.django.DjangoTemplates',
		'DIRS': [template_loc,template_loc2],
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

# 
STATIC_URL = '/static/'
STATIC_ROOT = template_loc
# If we specify ASGI_APPLICATION,WSGI_APPLICATION doesn't matter (irrespective of it's position)
# WSGI_APPLICATION = 'mysite.wsgi.application'
ASGI_APPLICATION = 'mysite.asgi.application'

#change redis url
# hey when changing  this,change at external matcher module too.
CHANNEL_LAYERS = {
	'default': {
		'BACKEND': 'channels_redis.core.RedisChannelLayer',
		'CONFIG': {
			"hosts": [('127.0.0.1', 6379)],
		},
	},
}

redis_cache_db = 5
redis_client = redis.Redis(host='localhost', port=6379, db=redis_cache_db)
print(f"@settings.py: flushing redis_db no:{redis_cache_db} which is used for caching views")
redis_client.flushdb()
#here also change redis url
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
		#using db 5 for caching
        "LOCATION": "redis://127.0.0.1:6379/"+str(redis_cache_db),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        },
        "KEY_PREFIX": "c42_cache"
    }
}

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.postgresql_psycopg2',
		'NAME': 'chat',
		'USER': 'postgres',
		'PASSWORD': '',
		'HOST': 'localhost',
		'PORT': '5432',
	}
}