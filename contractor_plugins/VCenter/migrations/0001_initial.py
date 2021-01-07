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
            name='VCenterComplex',
            fields=[
                ('complex_ptr', models.OneToOneField(auto_created=True, to='Building.Complex', primary_key=True, serialize=False, parent_link=True)),
                ('vcenter_username', models.CharField(max_length=50)),
                ('vcenter_password', models.CharField(max_length=50)),
                ('vcenter_datacenter', models.CharField(max_length=50, help_text='set to "ha-datacenter" for ESX hosts')),
                ('vcenter_cluster', models.CharField(max_length=50, help_text='set to the hostname (ie: "localhost.") for ESX hosts')),
                ('vcenter_host', models.ForeignKey(to='Building.Structure', help_text='set to VCenter or the ESX host, if ESX host, leave members empty',on_delete=models.CASCADE)),
            ],
            bases=('Building.complex',),
        ),
        migrations.CreateModel(
            name='VCenterFoundation',
            fields=[
                ('foundation_ptr', models.OneToOneField(auto_created=True, to='Building.Foundation', primary_key=True, serialize=False, parent_link=True)),
                ('vcenter_uuid', models.CharField(blank=True, null=True, max_length=36)),
                ('vcenter_complex', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='VCenter.VCenterComplex')),
            ],
            bases=('Building.foundation',),
        ),
    ]
