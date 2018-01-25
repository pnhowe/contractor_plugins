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
  container = docker.create()
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
                ('complex_ptr', models.OneToOneField(to='Building.Complex', parent_link=True, auto_created=True, primary_key=True, serialize=False)),
            ],
            bases=('Building.complex',),
        ),
        migrations.CreateModel(
            name='DockerFoundation',
            fields=[
                ('foundation_ptr', models.OneToOneField(to='Building.Foundation', parent_link=True, auto_created=True, primary_key=True, serialize=False)),
                ('docker_id', models.CharField(max_length=64, blank=True, null=True)),
            ],
            bases=('Building.foundation',),
        ),
        migrations.CreateModel(
            name='DockerPort',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('port', models.IntegerField()),
                ('address_offset', models.IntegerField()),
                ('foundation_index', models.IntegerField(default=0)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('complex', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='Docker.DockerComplex')),
                ('foundation', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.PROTECT, null=True, to='Docker.DockerFoundation')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='dockerport',
            unique_together=set([('foundation', 'foundation_index')]),
        ),
        migrations.RunPython( load_foundation_blueprints ),
    ]
