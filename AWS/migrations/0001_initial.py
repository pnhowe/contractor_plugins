# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def load_foundation_blueprints( app, schema_editor ):
  FoundationBluePrint = app.get_model( 'BluePrint', 'FoundationBluePrint' )
  StructureBluePrint = app.get_model( 'BluePrint', 'StructureBluePrint' )
  Script = app.get_model( 'BluePrint', 'Script' )
  BluePrintScript = app.get_model( 'BluePrint', 'BluePrintScript' )

  fbp = FoundationBluePrint( name='generic-awsec2', description='Generic VirtualBox VM' )
  fbp.config_values = {}
  fbp.template = {}
  fbp.foundation_type_list = [ 'AWSEC2' ]
  fbp.physical_interface_names = [ 'eth0' ]
  fbp.full_clean()
  fbp.save()

  s = Script( name='create-generic-awsec2', description='Create AWS EC2 Instance' )
  s.script = """# Create Generic AWS EC2 Instance
begin( description="Instance Creation" )
  instance = aws.create()
  foundation.awsec2_uuid = instance[ 'uuid' ]
  foundation.set_interface_macs( interface_list=instance[ 'interface_list' ] )
end
  """
  s.full_clean()
  s.save()
  BluePrintScript( blueprint=fbp, script=s, name='create' ).save()

  s = Script( name='destroy-generic-awsec2', description='Destroy AWS EC2 Instance' )
  s.script = """# Destory Generic AWS EC2 Instance
begin( description="Instance Destruction" )
  foundation.power_off()
  foundation.destroy()
  foundation.awsec2_uuid = None
end
  """
  s.full_clean()
  s.save()
  BluePrintScript( blueprint=fbp, script=s, name='destroy' ).save()

  sbpl = StructureBluePrint.objects.get( name='generic-linux' )
  sbpl.foundation_blueprint_list.add( fbp )
  sbpl.save()


class Migration(migrations.Migration):

    dependencies = [
        ('Building', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AWSEC2Foundation',
            fields=[
                ('foundation_ptr', models.OneToOneField(auto_created=True, primary_key=True, parent_link=True, serialize=False, to='Building.Foundation')),
                ('awsec2_uuid', models.CharField(max_length=36, blank=True, null=True)),
            ],
            bases=('Building.foundation',),
        ),
        migrations.RunPython( load_foundation_blueprints ),
    ]
