
import imghdr

from django.conf import settings
from django.contrib.syndication.views import Feed

from khanatek.core.models import ArticlePage
from khanatek.core.utils import play_filter


# Main artcile feed

class ArticleFeed(Feed):
    title = "The Khanatek Article"
    link = "/article/"
    description = "The latest news and views from Khanatek on the work we do"

    def items(self):
        return play_filter(ArticlePage.objects.live().order_by('-date'), 6)

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.intro if item.intro else item.body

    def item_link(self, item):
        return item.full_url

    def item_author_name(self, item):
        pass

    def item_pubdate(self, item):
        return datetime.combine(item.date, time())
