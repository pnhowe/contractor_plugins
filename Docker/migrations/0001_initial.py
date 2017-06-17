# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def load_foundation_blueprints( app, schema_editor ):
  FoundationBluePrint = app.get_model( 'BluePrint', 'FoundationBluePrint' )
  StructureBluePrint = app.get_model( 'BluePrint', 'StructureBluePrint' )
  Script = app.get_model( 'BluePrint', 'Script' )
  BluePrintScript = app.get_model( 'BluePrint', 'BluePrintScript' )

  fbp = FoundationBluePrint( name='generic-docker', description='Generic Docker Container' )
  fbp.config_values = {}
  fbp.template = {}
  fbp.foundation_type_list = [ 'Docker' ]
  fbp.physical_interface_names = []
  fbp.full_clean()
  fbp.save()

  s = Script( name='create-generic-docker', description='Create Docker Container' )
  s.script = """# Create Generic Docker Container
begin( description="Container Creation" )
  container = docker.create()
  foundation.container_id = container[ 'container_id' ]
end
  """
  s.full_clean()
  s.save()
  BluePrintScript( blueprint=fbp, script=s, name='create' ).save()

  s = Script( name='destroy-generic-docker', description='Destroy Docker Container' )
  s.script = """# Destory Generic Docker Container
begin( description="Instance Destruction" )
  foundation.stop()
  foundation.destroy()
  foundation.container_id = None
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
            name='DockerFoundation',
            fields=[
                ('foundation_ptr', models.OneToOneField(to='Building.Foundation', serialize=False, parent_link=True, auto_created=True, primary_key=True)),
                ('container_id', models.CharField(blank=True, null=True, max_length=64)),
            ],
            bases=('Building.foundation',),
        ),
        migrations.RunPython( load_foundation_blueprints ),
    ]
