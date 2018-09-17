# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Building', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='VirtualBoxComplex',
            fields=[
                ('complex_ptr', models.OneToOneField(primary_key=True, auto_created=True, parent_link=True, serialize=False, to='Building.Complex')),
            ],
            bases=('Building.complex',),
        ),
        migrations.CreateModel(
            name='VirtualBoxFoundation',
            fields=[
                ('foundation_ptr', models.OneToOneField(primary_key=True, auto_created=True, parent_link=True, serialize=False, to='Building.Foundation')),
                ('virtualbox_uuid', models.CharField(null=True, blank=True, max_length=36)),
                ('virtualbox_host', models.ForeignKey(to='VirtualBox.VirtualBoxComplex', on_delete=django.db.models.deletion.PROTECT)),
            ],
            bases=('Building.foundation',),
        ),
    ]
