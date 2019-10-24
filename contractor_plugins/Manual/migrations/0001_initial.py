# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Building', '0002_initial2'),
    ]

    operations = [
        migrations.CreateModel(
            name='ManualComplex',
            fields=[
                ('complex_ptr', models.OneToOneField(serialize=False, auto_created=True, to='Building.Complex', primary_key=True, parent_link=True)),
            ],
            bases=('Building.complex',),
        ),
        migrations.CreateModel(
            name='ManualComplexedFoundation',
            fields=[
                ('foundation_ptr', models.OneToOneField(serialize=False, auto_created=True, to='Building.Foundation', primary_key=True, parent_link=True)),
                ('complex_host', models.ForeignKey(to='Manual.ManualComplex', on_delete=django.db.models.deletion.PROTECT)),
            ],
            bases=('Building.foundation',),
        ),
        migrations.CreateModel(
            name='ManualFoundation',
            fields=[
                ('foundation_ptr', models.OneToOneField(serialize=False, auto_created=True, to='Building.Foundation', primary_key=True, parent_link=True)),
            ],
            bases=('Building.foundation',),
        ),
    ]
