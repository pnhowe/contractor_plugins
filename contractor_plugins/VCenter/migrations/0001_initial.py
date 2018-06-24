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
            name='VcenterComplex',
            fields=[
                ('complex_ptr', models.OneToOneField(to='Building.Complex', auto_created=True, primary_key=True, parent_link=True, serialize=False)),
                ('vcenter_username', models.CharField(max_length=50)),
                ('vcenter_password', models.CharField(max_length=50)),
                ('vcenter_datacenter', models.CharField(help_text='set to "ha-datacenter" for ESX hosts', max_length=50)),
                ('vcenter_cluster', models.CharField(null=True, max_length=50, blank=True)),
                ('vcenter_host', models.ForeignKey(help_text='set to VCenter or the ESX host, if ESX host, leave members empty', to='Building.Structure')),
            ],
            bases=('Building.complex',),
        ),
        migrations.CreateModel(
            name='VcenterFoundation',
            fields=[
                ('foundation_ptr', models.OneToOneField(to='Building.Foundation', auto_created=True, primary_key=True, parent_link=True, serialize=False)),
                ('vcenter_uuid', models.CharField(null=True, max_length=36, blank=True)),
                ('vcenter_host', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='Vcenter.VcenterComplex')),
            ],
            bases=('Building.foundation',),
        ),
    ]
