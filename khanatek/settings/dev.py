from __future__ import absolute_import, unicode_literals

from .base import *

import os


# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = config('DEBUG', default=False, cast=bool)
DEBUG = True
TEMPLATES[0]['OPTIONS']['debug'] = True

SECRET_KEY='riv_tsm@)$i+&$plnqm1i5h4m4yhr2#z%#465o4i&_*d-9nlws'


# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = config('SECRET_KEY')



INTERNAL_IPS = ('127.0.0.1')

BASE_URL = 'http://localhost:8000'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


try:
    from .local import *
except ImportError:
    pass
