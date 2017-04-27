from django.conf.urls import url

from khanatek.core.feeds import ArticleFeed
from khanatek.core import views

urlpatterns = [
    url(r'^article/feed/$', ArticleFeed(), name='article_feed'),
]