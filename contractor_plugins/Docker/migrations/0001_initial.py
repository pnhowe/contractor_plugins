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
            name='DockerComplex',
            fields=[
                ('complex_ptr', models.OneToOneField(to='Building.Complex', serialize=False, auto_created=True, parent_link=True, primary_key=True)),
            ],
            bases=('Building.complex',),
        ),
        migrations.CreateModel(
            name='DockerFoundation',
            fields=[
                ('foundation_ptr', models.OneToOneField(to='Building.Foundation', serialize=False, auto_created=True, parent_link=True, primary_key=True)),
                ('docker_id', models.CharField(null=True, max_length=64, blank=True)),
                ('docker_host', models.ForeignKey(to='Docker.DockerComplex', on_delete=django.db.models.deletion.PROTECT)),
            ],
            bases=('Building.foundation',),
        ),
        migrations.CreateModel(
            name='DockerPort',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('port', models.IntegerField()),
                ('address_offset', models.IntegerField()),
                ('foundation_index', models.IntegerField(default=0)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('complex', models.ForeignKey(to='Docker.DockerComplex', on_delete=django.db.models.deletion.CASCADE)),
                ('foundation', models.ForeignKey(to='Docker.DockerFoundation', on_delete=django.db.models.deletion.SET_NULL, blank=True, null=True)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='dockerport',
            unique_together=set([('foundation', 'foundation_index')]),
        ),
    ]
