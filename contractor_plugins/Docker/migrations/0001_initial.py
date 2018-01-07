# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


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
  container = docker.create( host=foundation.docker_host )
  foundation.docker_id = container[ 'docker_id' ]
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
  foundation.docker_id = None
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
            name='DockerComplex',
            fields=[
                ('complex_ptr', models.OneToOneField(parent_link=True, to='Building.Complex', serialize=False, primary_key=True, auto_created=True)),
            ],
            bases=('Building.complex',),
        ),
        migrations.CreateModel(
            name='DockerFoundation',
            fields=[
                ('foundation_ptr', models.OneToOneField(parent_link=True, to='Building.Foundation', serialize=False, primary_key=True, auto_created=True)),
                ('docker_id', models.CharField(null=True, max_length=64, blank=True)),
                ('docker_host', models.ForeignKey(to='Docker.DockerComplex', on_delete=django.db.models.deletion.PROTECT)),
            ],
            bases=('Building.foundation',),
        ),
        migrations.RunPython( load_foundation_blueprints ),
    ]
