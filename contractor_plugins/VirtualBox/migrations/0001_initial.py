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
                ('complex_ptr', models.OneToOneField(serialize=False, auto_created=True, to='Building.Complex', primary_key=True, parent_link=True)),
                ('virtualbox_username', models.CharField(max_length=50)),
                ('virtualbox_password', models.CharField(max_length=50)),
            ],
            bases=('Building.complex',),
        ),
        migrations.CreateModel(
            name='VirtualBoxFoundation',
            fields=[
                ('foundation_ptr', models.OneToOneField(serialize=False, auto_created=True, to='Building.Foundation', primary_key=True, parent_link=True)),
                ('virtualbox_uuid', models.CharField(blank=True, null=True, max_length=36)),
                ('virtualbox_host', models.ForeignKey(to='VirtualBox.VirtualBoxComplex', on_delete=django.db.models.deletion.PROTECT)),
            ],
            bases=('Building.foundation',),
        ),
    ]
