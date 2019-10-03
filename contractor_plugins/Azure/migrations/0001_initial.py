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
            name='AzureComplex',
            fields=[
                ('complex_ptr', models.OneToOneField(parent_link=True, primary_key=True, to='Building.Complex', serialize=False, auto_created=True)),
                ('azure_subscription_id', models.CharField(max_length=36)),
                ('azure_location', models.CharField(max_length=20)),
                ('azure_resource_group', models.CharField(max_length=90)),
                ('azure_client_id', models.CharField(help_text='also called App Id', max_length=36)),
                ('azure_password', models.CharField(max_length=36)),
                ('azure_tenant_id', models.CharField(max_length=36)),
            ],
            bases=('Building.complex',),
        ),
        migrations.CreateModel(
            name='AzureFoundation',
            fields=[
                ('foundation_ptr', models.OneToOneField(parent_link=True, primary_key=True, to='Building.Foundation', serialize=False, auto_created=True)),
                ('azure_resource_name', models.CharField(blank=True, null=True, max_length=64)),
                ('azure_complex', models.ForeignKey(to='Azure.AzureComplex', on_delete=django.db.models.deletion.PROTECT)),
            ],
            bases=('Building.foundation',),
        ),
    ]
