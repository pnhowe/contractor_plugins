# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Survey', '0001_initial'),
        ('Building', '0002_initial2'),
    ]

    operations = [
        migrations.CreateModel(
            name='AMTFoundation',
            fields=[
                ('foundation_ptr', models.OneToOneField(primary_key=True, to='Building.Foundation', serialize=False, auto_created=True, parent_link=True)),
                ('amt_username', models.CharField(default='admin', max_length=16)),
                ('amt_password', models.CharField(max_length=16)),
                ('amt_ip_address', models.CharField(max_length=30)),
                ('plot', models.ForeignKey(to='Survey.Plot',on_delete=models.CASCADE)),
            ],
            bases=('Building.foundation',),
        ),
    ]
