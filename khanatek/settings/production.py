from __future__ import absolute_import, unicode_literals

import os

from .base import *

from decouple import config



DEBUG = False
TEMPLATES[0]['OPTIONS']['debug'] = False

# SECRET_KEY = config('SECRET_KEY')
# DEBUG = config('DEBUG', default=False, cast=bool)

# Allow all host headers
# ALLOWED_HOSTS = ['khanatek.herokuapp.com']

ALLOWED_HOSTS = []

# STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'

COMPRESS_OFFLINE = True
COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.CSSMinFilter',
]
COMPRESS_CSS_HASHING_METHOD = 'content'

try:
    from .local import *
except ImportError:
    pass