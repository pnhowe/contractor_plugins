# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Building', '0002_initial2'),
    ]

    operations = [
        migrations.CreateModel(
            name='IPMIFoundation',
            fields=[
                ('foundation_ptr', models.OneToOneField(auto_created=True, serialize=False, to='Building.Foundation', parent_link=True, primary_key=True)),
                ('ipmi_username', models.CharField(max_length=16)),
                ('ipmi_password', models.CharField(max_length=16)),
                ('ipmi_ip_address', models.CharField(max_length=30)),
            ],
            bases=('Building.foundation',),
        ),
    ]
