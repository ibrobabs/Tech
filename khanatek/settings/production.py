from __future__ import absolute_import, unicode_literals

import os

from .base import *

# import khanatek.utils

from decouple import config



# DEBUG = False
TEMPLATES[0]['OPTIONS']['debug'] = False

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)

# Allow all host headers
ALLOWED_HOSTS = ['khanatek.herokuapp.com']

# ALLOWED_HOSTS = []

# STATICFILES_STORAGE = 'StaticRootS3BotoStorage'
# COMPRESS_STORAGE = STATICFILES_STORAGE

# COMPRESS_OFFLINE = True
# COMPRESS_CSS_FILTERS = [
#     'compressor.filters.css_default.CssAbsoluteFilter',
#     'compressor.filters.cssmin.CSSMinFilter',
# ]
# COMPRESS_CSS_HASHING_METHOD = 'content'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'



WAGTAILSEARCH_BACKENDS = {
    'default': {
        'BACKEND': 'wagtail.wagtailsearch.backends.elasticsearch',
        'URLS': ['http://localhost:9200'],
        'INDEX': 'khanatek',
        'TIMEOUT': 5,
    }
}


# CACHES = {
#     'default': {
#         'BACKEND': 'redis_cache.cache.RedisCache',
#         'LOCATION': '127.0.0.1:6379',
#         'KEY_PREFIX': 'khanatek',
#         'OPTIONS': {
#             'CLIENT_CLASS': 'redis_cache.client.DefaultClient',
#         }
#     }
# }

try:
    from .local import *
except ImportError:
    pass