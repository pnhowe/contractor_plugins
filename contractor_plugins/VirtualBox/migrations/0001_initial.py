# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


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

  s = Script( name='create-generic-virtualbox', description='Create Virtual Box VM' )
  s.script = """# Create Generic VirualBox VM
begin( description="VM Creation" )
  vm = virtualbox.create()
  foundation.virtualbox_uuid = vm[ 'uuid' ]
  foundation.set_interface_macs( interface_list=vm[ 'interface_list' ] )
end
  """
  s.full_clean()
  s.save()
  BluePrintScript( blueprint=fbp, script=s, name='create' ).save()

  s = Script( name='destroy-generic-virtualbox', description='Destroy Virtual Box VM' )
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

  sbpl = StructureBluePrint.objects.get( name='generic-linux' )
  sbpl.foundation_blueprint_list.add( fbp )
  sbpl.save()

  sbpe = StructureBluePrint.objects.get( name='generic-esx' )
  sbpe.foundation_blueprint_list.add( fbp )
  sbpe.save()


class Migration(migrations.Migration):

    dependencies = [
        ('Building', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='VirtualBoxComplex',
            fields=[
                ('complex_ptr', models.OneToOneField(primary_key=True, auto_created=True, parent_link=True, serialize=False, to='Building.Complex')),
            ],
            bases=('Building.complex',),
        ),
        migrations.CreateModel(
            name='VirtualBoxFoundation',
            fields=[
                ('foundation_ptr', models.OneToOneField(primary_key=True, auto_created=True, parent_link=True, serialize=False, to='Building.Foundation')),
                ('virtualbox_uuid', models.CharField(null=True, blank=True, max_length=36)),
                ('virtualbox_host', models.ForeignKey(to='VirtualBox.VirtualBoxComplex', on_delete=django.db.models.deletion.PROTECT)),
            ],
            bases=('Building.foundation',),
        ),
        migrations.RunPython( load_foundation_blueprints ),
    ]
