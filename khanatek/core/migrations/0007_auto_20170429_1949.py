# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-04-30 01:49
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailforms', '0003_capitalizeverbose'),
        ('wagtailcore', '0032_add_bulk_delete_page_permission'),
        ('wagtailredirects', '0005_capitalizeverbose'),
        ('core', '0006_auto_20170429_1944'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='servicepage',
            name='page_ptr',
        ),
        migrations.DeleteModel(
            name='ServicePage',
        ),
    ]
