# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def load_foundation_blueprints( app, schema_editor ):
  FoundationBluePrint = app.get_model( 'BluePrint', 'FoundationBluePrint' )
  StructureBluePrint = app.get_model( 'BluePrint', 'StructureBluePrint' )
  Script = app.get_model( 'BluePrint', 'Script' )
  BluePrintScript = app.get_model( 'BluePrint', 'BluePrintScript' )

  fbp = FoundationBluePrint( name='generic-virtualbox', description='Generic VirtualBox VM' )
  fbp.config_values = { 'memory_size': 512, 'cpu_count': 1 }
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
  vm = virtualbox.create( name=foundation.locator, memory_size=config.memory_size, cpu_count=config.cpu_count )
  foundation.virtualbox_uuid = vm[ 'uuid' ]
  foundation.set_interface_macs( interface_list=vm[ 'interface_list' ] )
end
  """
  s.full_clean()
  s.save()
  BluePrintScript( blueprint=fbp, script=s, name='create' ).save()

  s = Script( name='destroy-generic-virtualbox', description='Destroy Manual Server' )
  s.script = """# Destory Generic VirualBox VM
begin( description="VM Destruction" )
  foundation.power_off()
  foundation.destroy()
  foundation.virtualbox_uuid = None
end
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
                ('foundation_ptr', models.OneToOneField(parent_link=True, to='Building.Foundation', serialize=False, primary_key=True, auto_created=True)),
                ('virtualbox_uuid', models.CharField(blank=True, max_length=36, null=True)),
            ],
            bases=('Building.foundation',),
        ),
        migrations.RunPython( load_foundation_blueprints ),
    ]
