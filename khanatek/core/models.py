from __future__ import absolute_import, unicode_literals

from django import forms
from django.core.mail import EmailMessage
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.shortcuts import render
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.views.decorators.vary import vary_on_headers

from modelcluster.fields import ParentalKey, ForeignKey
from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.wagtailadmin.edit_handlers import (FieldPanel, InlinePanel,
                                                MultiFieldPanel,
                                                PageChooserPanel,
                                                StreamFieldPanel)
from wagtail.wagtailadmin.utils import send_mail

from wagtail.wagtailcore.blocks import (CharBlock, FieldBlock, ListBlock,
                                        PageChooserBlock, RawHTMLBlock,
                                        RichTextBlock, StreamBlock,
                                        StructBlock, TextBlock, URLBlock)
from wagtail.wagtailcore.fields import RichTextField, StreamField
from wagtail.wagtailcore.models import Orderable, Page
from wagtail.wagtaildocs.edit_handlers import DocumentChooserPanel
from wagtail.wagtaildocs.blocks import DocumentChooserBlock
from wagtail.wagtailembeds.blocks import EmbedBlock
from wagtail.wagtailforms.models import AbstractEmailForm, AbstractFormField
from wagtail.wagtailimages.blocks import ImageChooserBlock
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailimages.models import (AbstractImage, AbstractRendition,
                                          Image)
from wagtail.wagtailsearch import index
from wagtail.wagtailsnippets.models import register_snippet
from wagtailmarkdown.fields import MarkdownBlock
from .fields import ColorField





# Streamfield blocks and config

class ImageFormatChoiceBlock(FieldBlock):
    field = forms.ChoiceField(choices=(
        ('left', 'Wrap left'),
        ('right', 'Wrap right'),
        ('half', 'Half width'),
        ('full', 'Full width'),
    ))


class ImageBlock(StructBlock):
    image = ImageChooserBlock()
    alignment = ImageFormatChoiceBlock()
    caption = CharBlock()
    attribution = CharBlock(required=False)

    class Meta:
        icon = "image"


class PhotoGridBlock(StructBlock):
    images = ListBlock(ImageChooserBlock())

    class Meta:
        icon = "grip"


class PullQuoteBlock(StructBlock):
    quote = CharBlock(classname="quote title")
    attribution = CharBlock()

    class Meta:
        icon = "openquote"


class PullQuoteImageBlock(StructBlock):
    quote = CharBlock()
    attribution = CharBlock()
    image = ImageChooserBlock(required=False)


class BustoutBlock(StructBlock):
    image = ImageChooserBlock()
    text = RichTextBlock()

    class Meta:
        icon = "pick"


class WideImage(StructBlock):
    image = ImageChooserBlock()

    class Meta:
        icon = "image"


class StatsBlock(StructBlock):
    pass

    class Meta:
        icon = "order"


class StoryBlock(StreamBlock):
    h2 = CharBlock(icon="title", classname="title")
    h3 = CharBlock(icon="title", classname="title")
    h4 = CharBlock(icon="title", classname="title")
    intro = RichTextBlock(icon="pilcrow")
    paragraph = RichTextBlock(icon="pilcrow")
    aligned_image = ImageBlock(label="Aligned image")
    wide_image = WideImage(label="Wide image")
    bustout = BustoutBlock()
    pullquote = PullQuoteBlock()
    raw_html = RawHTMLBlock(label='Raw HTML', icon="code")
    embed = EmbedBlock(icon="code")
    markdown = MarkdownBlock(icon="code")


# A couple of abstract classes that contain commonly used fields
class ContentBlock(models.Model):
    content = RichTextField()

    panels = [
        FieldPanel('content'),
    ]

    class Meta:
        abstract = True


class LinkFields(models.Model):
    link_external = models.URLField("External link", blank=True)
    link_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        related_name='+'
    )
    link_document = models.ForeignKey(
        'wagtaildocs.Document',
        null=True,
        blank=True,
        related_name='+'
    )

    @property
    def link(self):
        if self.link_page:
            return self.link_page.url
        elif self.link_document:
            return self.link_document.url
        else:
            return self.link_external

    panels = [
        FieldPanel('link_external'),
        PageChooserPanel('link_page'),
        DocumentChooserPanel('link_document'),
    ]

    class Meta:
        abstract = True


class ContactFields(models.Model):
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address_1 = models.CharField(max_length=255, blank=True)
    address_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=255, blank=True)
    post_code = models.CharField(max_length=10, blank=True)

    panels = [
        FieldPanel('telephone'),
        FieldPanel('email'),
        FieldPanel('address_1'),
        FieldPanel('address_2'),
        FieldPanel('city'),
        FieldPanel('country'),
        FieldPanel('post_code'),
    ]

    class Meta:
        abstract = True

# Related links
class RelatedLink(LinkFields):
    title = models.CharField(max_length=255, help_text="Link title")

    panels = [
        FieldPanel('title'),
        MultiFieldPanel(LinkFields.panels, "Link"),
    ]

    class Meta:
        abstract = True


				##################
    			##################
				### Home page  ###
				##################
				##################

class HomePageHero(Orderable, RelatedLink):
    page = ParentalKey('core.HomePage', related_name='hero')
    colour = models.CharField(max_length=255)
    background = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    logo = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    text = models.CharField(
        max_length=255
    )

    panels = RelatedLink.panels + [
        ImageChooserPanel('background'),
        ImageChooserPanel('logo'),
        FieldPanel('colour'),
        FieldPanel('text'),
    ]


class HomePageClient(Orderable, RelatedLink):
    page = ParentalKey('core.HomePage', related_name='clients')
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    panels = RelatedLink.panels + [
        ImageChooserPanel('image')
    ]


class HomePage(Page):
    intro_body = RichTextField(blank=True)
    article_title = models.TextField(blank=True)
    project_title = models.TextField(blank=True)
    clients_title = models.TextField(blank=True)
    search_fields = Page.search_fields + [
    	index.SearchField('intro_body'),
    ]

    class Meta:
        verbose_name = "Homepage"

# HomePage.content_panels
    content_panels = [
        FieldPanel('title', classname="full title"),
        InlinePanel('hero', label="Hero"),
        FieldPanel('intro_body'),
        FieldPanel('article_title'),
        FieldPanel('project_title'),
        FieldPanel('clients_title'),
        InlinePanel('clients', label="Clients"),
    ]

    @property
    def article_posts(self):
        # Get list of article pages.
        article_posts = ArticlePage.objects.live().public()

        # Order by most recent date first
        article_posts = article_posts.order_by('-date')

        return article_posts

    

    			#####################
    			#####################
				### Standard page ###
				#####################
				#####################

class StandardPageContentBlock(Orderable, ContentBlock):
    page = ParentalKey('core.StandardPage', related_name='content_block')


class StandardPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('core.StandardPage', related_name='related_links')


class StandardPageClient(Orderable, RelatedLink):
    page = ParentalKey('core.StandardPage', related_name='clients')
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    panels = RelatedLink.panels + [
        ImageChooserPanel('image')
    ]


class StandardPage(Page):
    main_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    credit = models.CharField(max_length=255, blank=True)
    heading = RichTextField(blank=True)
    quote = models.CharField(max_length=255, blank=True)
    intro = RichTextField(blank=True)
    middle_break = RichTextField(blank=True)
    body = StreamField([
        ('h2', CharBlock(icon="title", classname="title")),
        ('h3', CharBlock(icon="title", classname="title")),
        ('h4', CharBlock(icon="title", classname="title")),
        ('intro', RichTextBlock(icon="pilcrow")),
        ('paragraph', RichTextBlock(icon="pilcrow")),
        ('aligned_image', ImageBlock(label="Aligned image")),
        ('wide_image', WideImage(label="Wide image")),
        ('bustout', BustoutBlock()),
        ('pullquote', PullQuoteBlock()),
        ('raw_html', RawHTMLBlock(label='Raw HTML', icon="code")),
        ('embed', EmbedBlock(icon="code")),
        ('markdown', MarkdownBlock(icon="code")),
    ])
    # streamfield = StreamField(StoryBlock())
    email = models.EmailField(blank=True)

    feed_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    show_in_play_menu = models.BooleanField(default=False)

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

    content_panels = Page.content_panels + [
        FieldPanel('title', classname="full title"),
        ImageChooserPanel('main_image'),
        ImageChooserPanel('feed_image'),
        FieldPanel('credit', classname="full"),
        FieldPanel('heading', classname="full"),
        FieldPanel('quote', classname="full"),
        FieldPanel('intro'),
        FieldPanel('middle_break', classname="full"),
        StreamFieldPanel('body'),
        FieldPanel('email', classname="full"),
        InlinePanel('content_block', label="Content block"),
        InlinePanel('related_links', label="Related links"),
        InlinePanel('clients', label="Clients"),
    ]

    promote_panels = [
        MultiFieldPanel(Page.promote_panels, "Common page configuration"),
        FieldPanel('show_in_play_menu'),
    ]

    			##################
    			##################
				### About page ###
				##################
				##################

class AboutPageRelatedLinkButton(Orderable, RelatedLink):
    page = ParentalKey('core.AboutPage', related_name='related_link_buttons')


class AboutPageOffice(Orderable):
    page = ParentalKey('core.AboutPage', related_name='offices')
    title = models.TextField()
    svg = models.TextField(null=True)
    description = models.TextField()

    panels = [
        FieldPanel('title'),
        FieldPanel('description'),
        FieldPanel('svg')
    ]


class AboutPageContentBlock(Orderable):
    page = ParentalKey('core.AboutPage', related_name='content_blocks')
    year = models.IntegerField()
    title = models.TextField()
    description = models.TextField()
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    panels = [
        FieldPanel('year'),
        FieldPanel('title'),
        FieldPanel('description'),
        ImageChooserPanel('image')
    ]


class AboutPage(Page):
    main_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    heading = models.TextField(blank=True)
    intro = models.TextField(blank=True)
    involvement_title = models.TextField(blank=True)

    content_panels = [
        FieldPanel('title', classname='full title'),
        ImageChooserPanel('main_image'),
        FieldPanel('heading', classname='full'),
        FieldPanel('intro', classname='full'),
        InlinePanel('related_link_buttons', label='Header buttons'),
        InlinePanel('content_blocks', label='Content blocks'),
        InlinePanel('offices', label='Offices'),
        FieldPanel('involvement_title'),
    ]

    			#####################
    			#####################
				### Services page ###
				#####################
				#####################

class ServicesPageService(Orderable):
    page = ParentalKey('core.ServicesPage', related_name='services')
    title = models.TextField()
    svg = models.TextField(null=True)
    description = models.TextField()
    link = models.ForeignKey(
        'core.ServicePage',
        related_name='+',
        blank=True,
        null=True,
    )

    panels = [
        FieldPanel('title'),
        FieldPanel('description'),
        PageChooserPanel('link'),
        FieldPanel('svg')
    ]


class ServicesPage(Page):
    main_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    heading = models.TextField(blank=True)
    intro = models.TextField(blank=True)

    search_fields = Page.search_fields + [
        index.SearchField('title'),
        index.SearchField('intro'),
        index.SearchField('heading'),
    ]

    content_panels = [
        FieldPanel('title', classname='full title'),
        ImageChooserPanel('main_image'),
        FieldPanel('heading'),
        FieldPanel('intro', classname='full'),
        InlinePanel('services', label='Services'),
    ]

    			##############################
    			##############################
				### Services/Projects page ###
				##############################
				##############################


class CaseStudyBlock(StructBlock):
    title = CharBlock(required=True)
    intro = TextBlock(required=True)
    case_studies = ListBlock(StructBlock([
        ('page', PageChooserBlock('core.ProjectPage')),
        ('title', CharBlock(required=False)),
        ('descriptive_title', CharBlock(required=False)),
        ('image', ImageChooserBlock(required=False)),
    ]))

    class Meta:
        template = 'blocks/case_study_block.html'


class HighlightBlock(StructBlock):
    title = CharBlock(required=True)
    intro = TextBlock(required=False)
    highlights = ListBlock(TextBlock())

    class Meta:
        template = 'blocks/highlight_block.html'


class StepByStepBlock(StructBlock):
    title = CharBlock(required=True)
    intro = TextBlock(required=False)
    steps = ListBlock(StructBlock([
        ('subtitle', CharBlock(required=False)),
        ('title', CharBlock(required=True)),
        ('icon', CharBlock(max_length=9000, required=True, help_text='Paste SVG code here')),
        ('description', TextBlock(required=True))
    ]))

    class Meta:
        template = 'blocks/step_by_step_block.html'


class PeopleBlock(StructBlock):
    title = CharBlock(required=True)
    intro = TextBlock(required=True)
    people = ListBlock(PageChooserBlock())

    class Meta:
        template = 'blocks/people_block.html'


class FeaturedPagesBlock(StructBlock):
    title = CharBlock()
    pages = ListBlock(StructBlock([
        ('page', PageChooserBlock()),
        ('image', ImageChooserBlock()),
        ('text', TextBlock()),
        ('sub_text', CharBlock(max_length=100)),
    ]))

    class Meta:
        template = 'blocks/featured_pages_block.html'


class SignUpFormPageBlock(StructBlock):
    page = PageChooserBlock('core.SignUpFormPage')

    def get_context(self, value, parent_context=None):
        context = super(SignUpFormPageBlock, self).get_context(value, parent_context)
        context['form'] = value['page'].sign_up_form_class()

        return context

    class Meta:
        icon = 'doc-full'
        template = 'blocks/sign_up_form_page_block.html'


class LogosBlock(StructBlock):
    title = CharBlock()
    intro = CharBlock()
    logos = ListBlock(StructBlock((
        ('image', ImageChooserBlock()),
        ('link_page', PageChooserBlock(required=False)),
        ('link_external', URLBlock(required=False)),
    )))

    class Meta:
        icon = 'site'
        template = 'blocks/logos_block.html'

class ServicePageBlock(StreamBlock):
    case_studies = CaseStudyBlock()
    highlights = HighlightBlock()
    pull_quote = PullQuoteBlock(template='blocks/pull_quote_block.html')
    process = StepByStepBlock()
    people = PeopleBlock()
    featured_pages = FeaturedPagesBlock()
    sign_up_form_page = SignUpFormPageBlock()
    logos = LogosBlock()


class ServicePage(Page):
    description = models.TextField()
    streamfield = StreamField(ServicePageBlock())
    particle = models.ForeignKey(
        'ParticleSnippet',
        blank=True,
        null=True,
        on_delete=models.SET_NULL)

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('description', classname="full"),
        StreamFieldPanel('streamfield'),
        FieldPanel('particle'),
    ]

@register_snippet
class ParticleSnippet(models.Model):
    """
    Snippet for configuring particlejs options
    """
    # particle type choices
    CIRCLE = 1
    EDGE = 2
    TRIANGLE = 3
    POLYGON = 4
    STAR = 5
    IMAGE = 6
    PARTICLES_TYPE_CHOICES = (
        (CIRCLE, 'circle'),
        (EDGE, 'edge'),
        (TRIANGLE, 'triangle'),
        (POLYGON, 'polygon'),
        (STAR, 'star'),
        (IMAGE, 'image'),
    )
    # particle movement direction choices
    NONE = 1
    TOP = 2
    TOP_RIGHT = 3
    RIGHT = 4
    BOTTOM_RIGHT = 5
    BOTTOM = 6
    BOTTOM_LEFT = 7
    LEFT = 8
    PARTICLES_MOVE_DIRECTION_CHOICES = (
        (NONE, 'none'),
        (TOP, 'top'),
        (TOP_RIGHT, 'top-right'),
        (RIGHT, 'right'),
        (BOTTOM_RIGHT, 'bottom-right'),
        (BOTTOM, 'bottom'),
        (BOTTOM_LEFT, 'bottom-left'),
        (LEFT, 'left'),
    )
    title = models.CharField(max_length=50)
    number = models.PositiveSmallIntegerField(default=50)
    shape_type = models.PositiveSmallIntegerField(
        choices=PARTICLES_TYPE_CHOICES, default=CIRCLE)
    polygon_sides = models.PositiveSmallIntegerField(default=5)
    size = models.DecimalField(default=2.5, max_digits=4, decimal_places=1)
    size_random = models.BooleanField(default=False)
    colour = ColorField(default='ffffff', help_text="Don't include # symbol.")
    opacity = models.DecimalField(default=0.9, max_digits=2, decimal_places=1)
    opacity_random = models.BooleanField(default=False)
    move_speed = models.DecimalField(
        default=2.5, max_digits=2, decimal_places=1)
    move_direction = models.PositiveSmallIntegerField(
        choices=PARTICLES_MOVE_DIRECTION_CHOICES,
        default=NONE)
    line_linked = models.BooleanField(default=True)
    css_background_colour = ColorField(
        blank=True,
        help_text="Don't include # symbol. Will be overridden by linear gradient")
    css_background_linear_gradient = models.CharField(
        blank=True,
        max_length=255,
        help_text="Enter in the format 'to right, #2b2b2b 0%, #243e3f 28%, #2b2b2b 100%'")
    css_background_url = models.URLField(blank=True, max_length=255)

    def __str__(self):
        return self.title




				##############################
    			##############################
				#### Article index page   ####
				##############################
				##############################

class ArticleIndexPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('core.ArticleIndexPage', related_name='related_links')


class ArticleIndexPage(Page):
    intro = models.TextField(blank=True)

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('title'),
    ]

    show_in_play_menu = models.BooleanField(default=False)

    def get_popular_tags(self):
        # the same as Drupal and only needed for the rss feed)
        popular_tags = ArticlePageTagSelect.objects.all().exclude(tag__name='planet-drupal').values('tag').annotate(item_count=models.Count('tag')).order_by('-item_count')

        # Getting them individually to preserve the order
        return [ArticlePageTagList.objects.get(id=tag['tag']) for tag in popular_tags[:6]]

    @property
    def article_posts(self):
        # Get list of article pages that are descendants of this page
        # and are not marketing_only
        article_posts = ArticlePage.objects.filter(
            live=True,
            path__startswith=self.path
        ).exclude(marketing_only=True)

        # Order by most recent date first
        article_posts = article_posts.order_by('-date', 'pk')

        return article_posts

    def serve(self, request):
        # Get article_posts
        article_posts = self.article_posts

        # Filter by tag
        tag = request.GET.get('tag')
        if tag:
            article_posts = article_posts.filter(tags__tag__slug=tag)

        # Pagination
        per_page = 9
        page = request.GET.get('page')
        paginator = Paginator(article_posts, per_page)  # Show 9 article_posts per page
        try:
            article_posts = paginator.page(page)
        except PageNotAnInteger:
            article_posts = paginator.page(1)
        except EmptyPage:
            article_posts = paginator.page(paginator.num_pages)

        if request.is_ajax():
            return render(request, "core/includes/article_listing.html", {
                'self': self,
                'article_posts': article_posts,
                'per_page': per_page,
            })
        else:
            return render(request, self.template, {
                'self': self,
                'article_posts': article_posts,
                'per_page': per_page,
            })

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('intro', classname="full"),
        InlinePanel('related_links', label="Related links"),
    ]

    promote_panels = [
        MultiFieldPanel(Page.promote_panels, "Common page configuration"),
        FieldPanel('show_in_play_menu'),
    ]


# Article page
class ArticlePageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('core.ArticlePage', related_name='related_links')


@python_2_unicode_compatible
class ArticlePageTagList(models.Model):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)

    def __str__(self):
        return self.name

register_snippet(ArticlePageTagList)


class ArticlePageTagSelect(Orderable):
    page = ParentalKey('core.ArticlePage', related_name='tags')
    tag = models.ForeignKey(
        'core.ArticlePageTagList',
        related_name='article_page_tag_select'
    )


class ArticlePageAuthor(Orderable):
    page = ParentalKey('core.ArticlePage', related_name='related_author')
    author = models.ForeignKey(
        'core.PersonPage',
        null=True,
        blank=True,
        related_name='+'
    )

    panels = [
        PageChooserPanel('author'),
    ]

class ArticlePage(Page):
    main_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    intro = RichTextField("Intro", blank=True)
    body = StreamField([ 
                ('h2', CharBlock(icon="title", classname="title")),
                ('h3', CharBlock(icon="title", classname="title")),
                ('h4', CharBlock(icon="title", classname="title")),
                ('intro', RichTextBlock(icon="pilcrow")),
                ('paragraph', RichTextBlock(icon="pilcrow")),
                ('aligned_image', ImageBlock(label="Aligned image")),
                ('wide_image', WideImage(label="Wide image")),
                ('bustout', BustoutBlock()),
                ('pullquote', PullQuoteBlock()),
                ('raw_html', RawHTMLBlock(label='Raw HTML', icon="code")),
                ('embed', EmbedBlock(icon="code")),
                ('markdown', MarkdownBlock(icon="code")),
            ])
    colour = models.CharField(
        "Listing card colour if left blank will display image",
        choices=(
            ('orange', "Orange"),
            ('blue', "Blue"),
            ('white', "White")
        ),
        max_length=255,
        blank=True
    )
    # streamfield = StreamField(StoryBlock(), blank=True)
    date = models.DateField("Post date")
    feed_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    marketing_only = models.BooleanField(default=False, help_text='Display this article post only on marketing landing page')

    canonical_url = models.URLField(blank=True, max_length=255)

    search_fields = Page.search_fields + [
        index.SearchField('body'),
        index.SearchField('intro'),
    ]

    @property
    def article_index(self):
        # Find article index in ancestors
        for ancestor in reversed(self.get_ancestors()):
            if isinstance(ancestor.specific, ArticleIndexPage):
                return ancestor

        # No ancestors are article indexes,
        # just return first blog index in database
        return ArticleIndexPage.objects.first()

    @property
    def has_authors(self):
        for author in self.related_author.all():
            if author.author:
                return True

    content_panels = [
        FieldPanel('title', classname="full title"),
        ImageChooserPanel('main_image'),
        ImageChooserPanel('feed_image'),
        FieldPanel('colour'),
        InlinePanel('related_author', label="Author"),
        FieldPanel('date'),
        FieldPanel('intro', classname="full"),
        StreamFieldPanel('body'),
        # StreamFieldPanel('streamfield'),
        InlinePanel('related_links', label="Related links"),
        InlinePanel('tags', label="Tags")
    ]

    promote_panels = [
        MultiFieldPanel(Page.promote_panels, "Common page configuration"),
        FieldPanel('canonical_url'),
        FieldPanel('marketing_only'),
    ]


    			#################################
    			#################################
				####  Career/Job index page  ####
				#################################
				#################################


class ReasonToJoin(Orderable):
    page = ParentalKey('core.JobIndexPage', related_name='reasons_to_join')
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    title = models.CharField(max_length=255)
    body = models.CharField(max_length=511)

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('title'),
        FieldPanel('body')
    ]


class JobIndexPageJob(Orderable):
    page = ParentalKey('core.JobIndexPage', related_name='job')
    job_title = models.CharField(max_length=255)
    job_intro = models.CharField(max_length=255)
    url = models.URLField(null=True)
    location = models.CharField(max_length=255, blank=True)

    panels = [
        FieldPanel('job_title'),
        FieldPanel('job_intro'),
        FieldPanel("url"),
        FieldPanel("location"),
    ]


class JobIndexPage(Page):
    intro = models.TextField(blank=True)
    listing_intro = models.TextField(
        blank=True,
        help_text="Will be shown instead of the intro when job listings are included "
        "on other pages")
    no_jobs_that_fit = RichTextField(blank=True)
    # main_image = models.ForeignKey(
    #     'wagtailimages.Image',
    #     null=True,
    #     blank=True,
    #     on_delete=models.SET_NULL,
    #     related_name='+'
    # )
    # terms_and_conditions = models.URLField(null=True, blank=True)
    # refer_a_friend = models.URLField(null=True, blank=True)
    reasons_intro = models.TextField(blank=True)

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super(
            JobIndexPage, self
        ).get_context(request, *args, **kwargs)
        context['jobs'] = self.job.all()
        context['articles'] = ArticlePage.objects.live().order_by('-date')[:4]
        return context

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('intro', classname="full"),
        # ImageChooserPanel('main_image'),
        FieldPanel('listing_intro', classname="full"),
        FieldPanel('no_jobs_that_fit', classname="full"),
        # FieldPanel('terms_and_conditions', classname="full"),
        # FieldPanel('refer_a_friend', classname="full"),
        InlinePanel('job', label="Job"),
        FieldPanel('reasons_intro', classname="full"),
        InlinePanel('reasons_to_join', label="Reasons To Join"),
    ]

    promote_panels = [
        MultiFieldPanel(Page.promote_panels, "Common page configuration"),
    ]



				##############################
    			##############################
				####   Project page  	  ####
				##############################
				##############################



class ProjectPageTagSelect(Orderable):
    page = ParentalKey('core.ProjectPage', related_name='tags')
    tag = models.ForeignKey(
        'core.ArticlePageTagList',
        related_name='project_page_tag_select'
    )


class ProjectPageScreenshot(Orderable):
    page = ParentalKey('core.ProjectPage', related_name='screenshots')
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    panels = [
        ImageChooserPanel('image'),
    ]


class ProjectPageAuthor(Orderable):
    page = ParentalKey('core.ProjectPage', related_name='related_author')
    author = models.ForeignKey(
        'core.PersonPage',
        null=True,
        blank=True,
        related_name='+'
    )

    panels = [
        PageChooserPanel('author'),
    ]


class ProjectPage(Page):
    summary = models.CharField(max_length=255)
    descriptive_title = models.CharField(max_length=255)
    intro = RichTextField("Intro", blank=True)
    body = StreamField([
        ('h2', CharBlock(icon="title", classname="title")),
        ('h3', CharBlock(icon="title", classname="title")),
        ('h4', CharBlock(icon="title", classname="title")),
        ('intro', RichTextBlock(icon="pilcrow")),
        ('paragraph', RichTextBlock(icon="pilcrow")),
        ('aligned_image', ImageBlock(label="Aligned image")),
        ('wide_image', WideImage(label="Wide image")),
        ('bustout', BustoutBlock()),
        ('pullquote', PullQuoteBlock()),
        ('embed', EmbedBlock(icon="code")),
        ('markdown', MarkdownBlock(icon="code")),
    ])
    homepage_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    marketing_only = models.BooleanField(default=False, help_text='Display this work item only on marketing landing page')
    visit_the_site = models.URLField(blank=True)

    show_in_play_menu = models.BooleanField(default=False)

    @property
    def project_index(self):
        # Find work index in ancestors
        for ancestor in reversed(self.get_ancestors()):
            if isinstance(ancestor.specific, ProjectIndexPage):
                return ancestor

        # No ancestors are work indexes,
        # just return first work index in database
        return ProjectIndexPage.objects.first()

    @property
    def has_authors(self):
        for author in self.related_author.all():
            if author.author:
                return True

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('descriptive_title'),
        InlinePanel('related_author', label="Author"),
        # FieldPanel('author_left'),
        FieldPanel('summary'),
        FieldPanel('intro', classname="full"),
        StreamFieldPanel('body'),
        # StreamFieldPanel('streamfield'),
        ImageChooserPanel('homepage_image'),
        InlinePanel('screenshots', label="Screenshots"),
        InlinePanel('tags', label="Tags"),
        FieldPanel('visit_the_site'),
    ]

    promote_panels = [
	    MultiFieldPanel(Page.promote_panels, "Common page configuration"),
	    FieldPanel('show_in_play_menu'),
	    FieldPanel('marketing_only'),
    ]


# Project index page
class ProjectIndexPage(Page):
    intro = RichTextField(blank=True)

    show_in_play_menu = models.BooleanField(default=False)
    hide_popular_tags = models.BooleanField(default=False)

    def get_popular_tags(self):
        # Get a ValuesQuerySet of tags ordered by most popular
        popular_tags = ProjectPageTagSelect.objects.all().values('tag').annotate(item_count=models.Count('tag')).order_by('-item_count')

        # Return first 10 popular tags as tag objects
        # Getting them individually to preserve the order
        return [ArticlePageTagList.objects.get(id=tag['tag']) for tag in popular_tags[:10]]

    @property
    def projects(self):
        # Get list of work pages that are descendants of this page
        # and are not marketing only
        projects = ProjectPage.objects.filter(
            live=True,
            path__startswith=self.path
        ).exclude(marketing_only=True)

        return projects

    def serve(self, request):
        # Get project pages
        projects = self.projects

        # Filter by tag
        tag = request.GET.get('tag')
        if tag:
            projects = projects.filter(tags__tag__slug=tag)

        # Pagination
        page = request.GET.get('page')
        paginator = Paginator(projects, 10)  # Show 10 works per page
        try:
            projects = paginator.page(page)
        except PageNotAnInteger:
            projects = paginator.page(1)
        except EmptyPage:
            projects = paginator.page(paginator.num_pages)

        return render(request, self.template, {
            'self': self,
            'projects': projects,
        })

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('intro', classname="full"),
        FieldPanel('hide_popular_tags'),
    ]

    promote_panels = [
        MultiFieldPanel(Page.promote_panels, "Common page configuration"),
        FieldPanel('show_in_play_menu'),
    ]



				##############################
    			##############################
				####   Person page  	  ####
				##############################
				##############################


class PersonPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('core.PersonPage', related_name='related_links')


class PersonPage(Page, ContactFields):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    role = models.CharField(max_length=255, blank=True)
    is_senior = models.BooleanField(default=False)
    intro = RichTextField(blank=True)
    biography = RichTextField(blank=True)
    short_biography = models.CharField(
        max_length=255, blank=True,
        help_text='A shorter summary biography for including in other pages'
    )
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    feed_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    search_fields = Page.search_fields + [
        index.SearchField('first_name'),
        index.SearchField('last_name'),
        index.SearchField('intro'),
        index.SearchField('biography'),
    ]

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('first_name'),
        FieldPanel('last_name'),
        FieldPanel('role'),
        FieldPanel('is_senior'),
        FieldPanel('intro', classname="full"),
        FieldPanel('biography', classname="full"),
        FieldPanel('short_biography', classname="full"),
        ImageChooserPanel('image'),
        ImageChooserPanel('feed_image'),
        MultiFieldPanel(ContactFields.panels, "Contact"),
        InlinePanel('related_links', label="Related links"),
    ]

    promote_panels = [
        MultiFieldPanel(Page.promote_panels, "Common page configuration"),
    ]


# Person index
class PersonIndexPage(Page):
    intro = models.TextField()
    senior_management_intro = models.TextField()
    team_intro = models.TextField()

    @cached_property
    def people(self):
        return PersonPage.objects.exclude(is_senior=True).live().public()

    @cached_property
    def senior_management(self):
        return PersonPage.objects.exclude(is_senior=False).live().public()

    content_panels = Page.content_panels + [
        FieldPanel('intro', classname="full"),
        FieldPanel('senior_management_intro', classname="full"),
        FieldPanel('team_intro', classname="full"),
    ]




    			########################################
    			########################################
				####   Sign-up for something page  	####
				########################################
				########################################


class SignUpFormPageBullet(Orderable):
    page = ParentalKey('core.SignUpFormPage', related_name='bullet_points')
    icon = models.CharField(max_length=100, choices=(
        ('core/includes/svg/bulb-svg.html', 'Light bulb'),
        ('core/includes/svg/pro-svg.html', 'Chart'),
        ('core/includes/svg/tick-svg.html', 'Tick'),
    ))
    title = models.CharField(max_length=100)
    body = models.TextField()

    panels = [
        FieldPanel('icon'),
        FieldPanel('title'),
        FieldPanel('body'),
    ]


class SignUpFormPageLogo(Orderable):
    page = ParentalKey('core.SignUpFormPage', related_name='logos')
    logo = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    panels = [
        ImageChooserPanel('logo'),
    ]


class SignUpFormPageQuote(Orderable):
    page = ParentalKey('core.SignUpFormPage', related_name='quotes')
    quote = models.TextField()
    author = models.CharField(max_length=100)
    organisation = models.CharField(max_length=100)

    panels = [
        FieldPanel('quote'),
        FieldPanel('author'),
        FieldPanel('organisation'),
    ]


class SignUpFormPageResponse(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    email = models.EmailField()

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return self.email


class SignUpFormPageForm(forms.ModelForm):
    class Meta:
        model = SignUpFormPageResponse
        fields = [
            'email',
        ]
        widgets = {
            'email': forms.TextInput(attrs={'placeholder': "Enter your email address"}),
        }


class SignUpFormPage(Page):
    formatted_title = models.CharField(
        max_length=255, blank=True,
        help_text="This is the title displayed on the page, not the document "
        "title tag. HTML is permitted (Remember Ibraheem)."
    )
    intro = RichTextField()
    call_to_action_text = models.CharField(
        max_length=255, help_text="Displayed above the email submission form."
    )
    call_to_action_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    form_button_text = models.CharField(max_length=255)
    thank_you_text = models.CharField(max_length=255,
                                      help_text="Displayed on successful form submission.")
    email_subject = models.CharField(max_length=100, verbose_name='subject')
    email_body = models.TextField(verbose_name='body')
    email_attachment = models.ForeignKey(
        'wagtaildocs.Document',
        null=True,
        related_name='+',
        on_delete=models.SET_NULL,
        verbose_name='attachment',
    )
    email_from_address = models.EmailField(
        verbose_name='from address',
        help_text="Anything ending in @khanatek.com is good.")

    sign_up_form_class = SignUpFormPageForm

    content_panels = [
        MultiFieldPanel([
            FieldPanel('title', classname="title"),
            FieldPanel('formatted_title'),
        ], 'Title'),
        FieldPanel('intro', classname="full"),
        InlinePanel('bullet_points', label="Bullet points"),
        InlinePanel('logos', label="Logos"),
        InlinePanel('quotes', label="Quotes"),
        MultiFieldPanel([
            FieldPanel('call_to_action_text'),
            ImageChooserPanel('call_to_action_image'),
            FieldPanel('form_button_text'),
            FieldPanel('thank_you_text'),
        ], 'Form'),
        MultiFieldPanel([
            FieldPanel('email_subject'),
            FieldPanel('email_body'),
            DocumentChooserPanel('email_attachment'),
            FieldPanel('email_from_address'),
        ], 'Email'),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super(SignUpFormPage, self).get_context(request, *args, **kwargs)
        context['form'] = self.sign_up_form_class()
        return context

    @vary_on_headers('X-Requested-With')
    def serve(self, request, *args, **kwargs):
        if request.is_ajax() and request.method == "POST":
            form = self.sign_up_form_class(request.POST)

            if form.is_valid():
                form.save()
                self.send_email_response(form.cleaned_data['email'])
                return render(
                    request,
                    'core/includes/sign_up_form_page_landing.html',
                    {
                        'page': self,
                        'form': form,
                        'legend': self.call_to_action_text
                     }
                )
            else:
                return render(
                    request,
                    'core/includes/sign_up_form_page_form.html',
                    {
                        'page': self,
                        'form': form,
                        'legend': self.call_to_action_text
                    }
                )
        else:
            return super(SignUpFormPage, self).serve(request)

    def send_email_response(self, to_address):
        email_message = EmailMessage(
            subject=self.email_subject,
            body=self.email_body,
            from_email=self.email_from_address,
            to=[to_address],
        )
        email_message.attach_file(self.email_attachment.file.path)
        email_message.send()


        		########################################
    			########################################
				####   		Contact page  			####
				########################################
				########################################


class ContactFormField(AbstractFormField):
    page = ParentalKey('Contact', related_name='form_fields')


class ContactLandingPageRelatedLinkButton(Orderable, RelatedLink):
    page = ParentalKey('core.Contact', related_name='related_link_buttons')


class Contact(AbstractEmailForm):
    intro = RichTextField(blank=True)
    main_image = models.ForeignKey('wagtailimages.Image', null=True,
                                   blank=True, on_delete=models.SET_NULL,
                                   related_name='+')
    landing_image = models.ForeignKey('wagtailimages.Image', null=True,
                                      blank=True, on_delete=models.SET_NULL,
                                      related_name='+')
    thank_you_text = models.CharField(max_length=255, help_text='e.g. Thanks!')
    thank_you_follow_up = models.CharField(max_length=255, help_text='e.g. We\'ll be in touch')
    landing_page_button_title = models.CharField(max_length=255, blank=True)
    landing_page_button_link = models.ForeignKey(
        'wagtailcore.Page', null=True, blank=True, related_name='+',
        on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = "Contact Page"

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('intro', classname="full"),
        ImageChooserPanel('main_image'),
        InlinePanel('form_fields', label="Form fields"),
        MultiFieldPanel([
            FieldPanel('to_address', classname="full"),
            FieldPanel('from_address', classname="full"),
            FieldPanel('subject', classname="full"),
        ], "Email"),
        MultiFieldPanel([
            ImageChooserPanel('landing_image'),
            FieldPanel('thank_you_text'),
            FieldPanel('thank_you_follow_up'),
            PageChooserPanel('landing_page_button_link'),
            FieldPanel('landing_page_button_title'),
        ], "Landing page"),
    ]


@register_setting
class GlobalSettings(BaseSetting):

    contact_telephone = models.CharField(max_length=255, help_text='Telephone', null=True)
    contact_email = models.EmailField(max_length=255, help_text='Email address', null=True)
    edmonton_address_title = models.CharField(max_length=255, help_text='Full address', null=True)
    edmonton_address = models.CharField(max_length=255, help_text='Full address', null=True)
    edmonton_address_link = models.URLField(max_length=255, help_text='Link to google maps', null=True)
    edmonton_address_svg = models.CharField(max_length=9000, help_text='Paste SVG code here', null=True)


	# Contact widget
    contact_person = models.ForeignKey(
        'core.PersonPage', related_name='+', null=True,
        on_delete=models.SET_NULL,
        help_text="Ensure this person has telephone and email fields set")
    contact_widget_intro = models.TextField()
    contact_widget_call_to_action = models.TextField()
    contact_widget_button_text = models.TextField()

    class Meta:
        verbose_name = 'Global Settings'

    panels = [
    		FieldPanel('contact_telephone'),
    		FieldPanel('contact_email'),
            FieldPanel('edmonton_address_title'),
            FieldPanel('edmonton_address'),
            FieldPanel('edmonton_address_link'),
            FieldPanel('edmonton_address_svg'),
    		MultiFieldPanel([
                PageChooserPanel('contact_person'),
                FieldPanel('contact_widget_intro'),
                FieldPanel('contact_widget_call_to_action'),
                FieldPanel('contact_widget_button_text'),
            ], 'Contact widget')
    ]

class SubMenuItemBlock(StreamBlock):
    subitem = PageChooserBlock()


class MenuItemBlock(StructBlock):
    page = PageChooserBlock()
    subitems = SubMenuItemBlock()

    class Meta:
        template = "core/includes/menu_item.html"


class MenuBlock(StreamBlock):
    items = MenuItemBlock()


@register_setting
class MainMenu(BaseSetting):
    menu = StreamField(MenuBlock(), blank=True)

    panels = [
        StreamFieldPanel('menu'),
    ]