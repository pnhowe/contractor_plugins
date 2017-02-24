# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def load_foundation_blueprints( app, schema_editor ):
  FoundationBluePrint = app.get_model( 'BluePrint', 'FoundationBluePrint' )
  StructureBluePrint = app.get_model( 'BluePrint', 'StructureBluePrint' )
  Script = app.get_model( 'BluePrint', 'Script' )
  BluePrintScript = app.get_model( 'BluePrint', 'BluePrintScript' )

  fbp = FoundationBluePrint( name='generic-manual', description='Generic Manual(Non-IPMI/DRAC/Blade/etc) Server' )
  fbp.config_values = {}
  fbp.template = {}
  fbp.foundation_type_list = [ 'Manual' ]
  fbp.physical_interface_names = [ 'eth0' ]
  fbp.full_clean()
  fbp.save()

  sbpl = StructureBluePrint.objects.get( name='generic-linux' )
  sbpl.foundation_blueprint_list.add( fbp )
  sbpl.save()

  s = Script( name='create-generic-manual', description='Create Manual Server' )
  s.script = """# Test and Configure Generic Manual Server
waitfor poweroff()
  """
  s.full_clean()
  s.save()
  BluePrintScript( blueprint=fbp, script=s, name='create' ).save()

  s = Script( name='destroy-generic-manual', description='Destroy Manual Server' )
  s.script = """# Decommission Generic Manual Server
ipmi.poweroff()
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
            name='ManualFoundation',
            fields=[
                ('foundation_ptr', models.OneToOneField(serialize=False, to='Building.Foundation', primary_key=True, auto_created=True, parent_link=True)),
            ],
            bases=('Building.foundation',),
        ),
        migrations.RunPython( load_foundation_blueprints ),
    ]
