# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


def load_foundation_blueprints( app, schema_editor ):
  FoundationBluePrint = app.get_model( 'BluePrint', 'FoundationBluePrint' )
  StructureBluePrint = app.get_model( 'BluePrint', 'StructureBluePrint' )
  Script = app.get_model( 'BluePrint', 'Script' )
  BluePrintScript = app.get_model( 'BluePrint', 'BluePrintScript' )

  fbp = FoundationBluePrint( name='generic-manual', description='Generic Manual(Non-IPMI/DRAC/Blade/etc) Server' )
  fbp.config_values = {}
  fbp.template = {}
  fbp.foundation_type_list = [ 'Manual', 'ManualComplex' ]
  fbp.physical_interface_names = [ 'eth0' ]
  fbp.full_clean()
  fbp.save()

  sbpl = StructureBluePrint.objects.get( name='generic-linux' )
  sbpl.foundation_blueprint_list.add( fbp )
  sbpl.save()

  sbpl = StructureBluePrint.objects.get( name='generic-manual-structure' )
  sbpl.foundation_blueprint_list.add( fbp )
  sbpl.save()

  s = Script( name='create-generic-manual', description='Create Manual Server' )
  s.script = """# Test and Configure Generic Manual Server
pause( msg='Resume when Server is Powered Off' )
pause( msg='Power On Server and Resume' )
  """
  s.full_clean()
  s.save()
  BluePrintScript( blueprint=fbp, script=s, name='create' ).save()

  s = Script( name='destroy-generic-manual', description='Destroy Manual Server' )
  s.script = """# Decommission Generic Manual Server
pause( msg='Resume script when Server is Off' )
  """
  s.full_clean()
  s.save()
  BluePrintScript( blueprint=fbp, script=s, name='destroy' ).save()

  s = Script( name='utility-generic-manual', description='Utility Script for Manual Server' )
  s.script = """# Utility Script for Generic Manual Server
pause( msg='Do the thing' )
  """
  s.full_clean()
  s.save()
  BluePrintScript( blueprint=fbp, script=s, name='utility' ).save()

class Migration(migrations.Migration):

    dependencies = [
        ('Building', '0001_initial'),
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
        migrations.RunPython( load_foundation_blueprints ),
    ]
