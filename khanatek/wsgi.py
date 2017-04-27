from __future__ import absolute_import, unicode_literals

import os
from dj_static import Cling

# from whitenoise.django import DjangoWhiteNoise
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "khanatek.settings.production")

application = Cling(get_wsgi_application())
# application = DjangoWhiteNoise(application)