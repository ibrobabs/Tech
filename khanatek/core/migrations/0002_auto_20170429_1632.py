# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-04-29 22:32
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='articleindexpage',
            name='show_in_play_menu',
        ),
        migrations.RemoveField(
            model_name='projectindexpage',
            name='show_in_play_menu',
        ),
        migrations.RemoveField(
            model_name='projectpage',
            name='show_in_play_menu',
        ),
        migrations.RemoveField(
            model_name='projectpage',
            name='summary',
        ),
        migrations.RemoveField(
            model_name='standardpage',
            name='show_in_play_menu',
        ),
    ]
