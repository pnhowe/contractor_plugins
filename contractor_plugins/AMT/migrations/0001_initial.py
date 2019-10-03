# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Building', '0002_initial2'),
    ]

    operations = [
        migrations.CreateModel(
            name='AMTFoundation',
            fields=[
                ('foundation_ptr', models.OneToOneField(to='Building.Foundation', serialize=False, primary_key=True, parent_link=True, auto_created=True)),
                ('amt_password', models.CharField(max_length=16)),
                ('amt_ip_address', models.CharField(max_length=30)),
            ],
            bases=('Building.foundation',),
        ),
    ]
