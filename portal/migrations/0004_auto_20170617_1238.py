# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-17 12:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0003_auto_20170617_1222'),
    ]

    operations = [
        migrations.AddField(
            model_name='newsandupdate',
            name='slug',
            field=models.SlugField(default=1, unique=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='newsandupdate',
            name='body',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='newsandupdate',
            name='category',
            field=models.CharField(choices=[('realese', 'New release'), ('bug', 'Bug fix'), ('announcement', 'Announcement'), ('other', 'Other')], max_length=150),
        ),
    ]