# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def load_foundation_blueprints( app, schema_editor ):
  FoundationBluePrint = app.get_model( 'BluePrint', 'FoundationBluePrint' )
  StructureBluePrint = app.get_model( 'BluePrint', 'StructureBluePrint' )
  Script = app.get_model( 'BluePrint', 'Script' )
  BluePrintScript = app.get_model( 'BluePrint', 'BluePrintScript' )

  fbp = FoundationBluePrint( name='generic-virtualbox', description='Generic VirtualBox VM' )
  fbp.config_values = {}
  fbp.template = {}
  fbp.foundation_type_list = [ 'VirtualBox' ]
  fbp.physical_interface_names = [ 'eth0' ]
  fbp.full_clean()
  fbp.save()

  sbpl = StructureBluePrint.objects.get( name='generic-linux' )
  sbpl.foundation_blueprint_list.add( fbp )
  sbpl.save()

  s = Script( name='create-generic-virtualbox', description='Create Manual Server' )
  s.script = """# Create Generic VirualBox VM
begin( description="VM Creation" )
  virtualbox.create()
end
  """
  s.full_clean()
  s.save()
  BluePrintScript( blueprint=fbp, script=s, name='create' ).save()

  s = Script( name='destroy-generic-virtualbox', description='Destroy Manual Server' )
  s.script = """# Destory Generic VirualBox VM
virtualbox.destroy()
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
            name='VirtualBoxFoundation',
            fields=[
                ('foundation_ptr', models.OneToOneField(auto_created=True, serialize=False, parent_link=True, to='Building.Foundation', primary_key=True)),
            ],
            bases=('Building.foundation',),
        ),
        migrations.RunPython( load_foundation_blueprints ),
    ]
