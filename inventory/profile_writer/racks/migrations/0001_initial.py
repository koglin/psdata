# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=40)),
                ('height', models.IntegerField()),
                ('description', models.CharField(max_length=30)),
                ('orientation', models.CharField(max_length=20, choices=[(b'front', b'front of rack'), (b'back', b'back of rack')])),
            ],
        ),
        migrations.CreateModel(
            name='Hutch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=3, choices=[(b'XPP', b'XPP'), (b'XCS', b'XCS'), (b'AMO', b'AMO'), (b'SXR', b'SXR'), (b'CXI', b'CXI'), (b'MEC', b'MEC')])),
                ('building', models.CharField(max_length=4)),
            ],
        ),
        migrations.CreateModel(
            name='Rack',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=3)),
                ('height', models.IntegerField(default=48)),
                ('hutch', models.ForeignKey(to='racks.Hutch')),
            ],
        ),
        migrations.AddField(
            model_name='device',
            name='rack',
            field=models.ForeignKey(to='racks.Rack'),
        ),
    ]
