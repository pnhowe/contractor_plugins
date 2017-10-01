# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def load_foundation_blueprints( app, schema_editor ):
  FoundationBluePrint = app.get_model( 'BluePrint', 'FoundationBluePrint' )
  StructureBluePrint = app.get_model( 'BluePrint', 'StructureBluePrint' )
  Script = app.get_model( 'BluePrint', 'Script' )
  BluePrintScript = app.get_model( 'BluePrint', 'BluePrintScript' )

  fbp = FoundationBluePrint( name='generic-amt', description='Generic AMT Server' )
  fbp.config_values = {}
  fbp.template = {}
  fbp.foundation_type_list = [ 'AMT' ]
  fbp.physical_interface_names = [ 'eth0' ]
  fbp.full_clean()
  fbp.save()

  sbpl = StructureBluePrint.objects.get( name='generic-linux' )
  sbpl.foundation_blueprint_list.add( fbp )
  sbpl.save()

  s = Script( name='create-generic-amt', description='Create AMT Server' )
  s.script = """# Test and Configure Generic AMT Server
foundation.wait_for_poweroff()
  """
  s.full_clean()
  s.save()
  BluePrintScript( blueprint=fbp, script=s, name='create' ).save()

  s = Script( name='destroy-generic-amt', description='Destroy AMT Server' )
  s.script = """# Decommission Generic Manual Server
foundation.power_off()
  """
  s.full_clean()
  s.save()
  BluePrintScript( blueprint=fbp, script=s, name='destroy' ).save()


class Migration(migrations.Migration):

    dependencies = [
        ('Building', '0001_initial'),
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
        migrations.RunPython( load_foundation_blueprints ),
    ]
