# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


def load_foundation_blueprints( app, schema_editor ):
  FoundationBluePrint = app.get_model( 'BluePrint', 'FoundationBluePrint' )
  StructureBluePrint = app.get_model( 'BluePrint', 'StructureBluePrint' )
  Script = app.get_model( 'BluePrint', 'Script' )
  BluePrintScript = app.get_model( 'BluePrint', 'BluePrintScript' )
  PXE = app.get_model( 'BluePrint', 'PXE' )

  sbpe = StructureBluePrint( name='generic-esx', description='Generic ESXi' )
  sbpe.config_values = { }
  sbpe.full_clean()
  sbpe.save()

  s = Script( name='create-esx', description='Install ESXi' )
  s.script = """# pxe boot and install
dhcp.set_pxe( interface=structure.provisioning_interface, pxe="esx" )
foundation.power_on()
delay( seconds=120 )
foundation.wait_for_poweroff()

dhcp.set_pxe( interface=structure.provisioning_interface, pxe="normal-boot" )
foundation.power_on()

iputils.wait_for_port( target=structure.provisioning_ip, port=80 )

datastore_list = config.datastore_list
while len( array=datastore_list ) do
begin()
  datastore = pop( array=datastore_list )
  vcenter.create_datastore( name=datastore[ 'name' ], model=datastore[ 'model' ] )
end
  """
  s.full_clean()
  s.save()
  BluePrintScript( blueprint=sbpe, script=s, name='create' ).save()

  s = Script( name='destroy-esx', description='Uninstall ESXi' )
  s.script = """# nothing to do, foundation cleanup should wipe/destroy the disks
foundation.power_off()
#eventually pxe boot to MBR wipper
  """
  s.full_clean()
  s.save()
  BluePrintScript( blueprint=sbpe, script=s, name='destroy' ).save()

  pxe = PXE( name='esx' )
  pxe.boot_script = """echo ESX Installer
kernel -n mboot.c32 http://192.168.200.51:8081/esxi/mboot.c32
imgargs mboot.c32 -c http://192.168.200.51:8081/esxi/boot.cfg ks=http://192.168.200.51:8888/config/pxe_template/
boot mboot.c32
"""
  pxe.template = """
accepteula

rootpw vmware

clearpart --alldrives --overwritevmfs

#install --firstdisk --overwritevmfs
install --firstdisk=usb --overwritevmfs

network --bootproto=static --ip={{ network.eth0.ip_address }} --netmask={{ network.eth0.netmask }}{% if network.eth0.gateway %} --gateway={{ network.eth0.gateway }}{% endif %} --nameserver={{ dns_servers.0 }} --hostname={{ hostname }}

%post --interpreter=busybox
/sbin/poweroff
"""
  pxe.full_clean()
  pxe.save()

  fbp = FoundationBluePrint( name='generic-vcenter', description='Generic VCenter VM' )
  fbp.config_values = {}
  fbp.template = {}
  fbp.foundation_type_list = [ 'vcenter' ]
  fbp.physical_interface_names = []
  fbp.full_clean()
  fbp.save()

  s = Script( name='create-generic-vcenter', description='Create VCenter VM' )
  s.script = """# Create Generic VCenter VM
begin( description="VM Creation" )
  host_list = vcenter.host_list( min_memory=1024 )
  datastore_list = vcenter.datastore_list( host=host_list[0], min_free_space=5, name_regex='.*fast.*' )
  vm_uuid = vcenter.create( host=host_list[0], datastore=datastore_list[0] )
  foundation.vcenter_uuid = vm_uuid
  interface_map = foundation.get_interface_map()
  foundation.set_interface_macs( interface_map=interface_map )
end
  """
  s.full_clean()
  s.save()
  BluePrintScript( blueprint=fbp, script=s, name='create' ).save()

  s = Script( name='destroy-generic-vcenter', description='Destroy VCenter VM' )
  s.script = """# Destory Generic VCenter VM
begin( description="VM Destruction" )
  foundation.power_off()
  foundation.destroy()
  foundation.vcenter_uuid = None
end
  """
  s.full_clean()
  s.save()
  BluePrintScript( blueprint=fbp, script=s, name='destroy' ).save()

  sbp = StructureBluePrint.objects.get( name='generic-linux' )
  sbp.foundation_blueprint_list.add( fbp )

  sbp = StructureBluePrint.objects.get( name='generic-esx' )
  sbp.foundation_blueprint_list.add( fbp )


class Migration(migrations.Migration):

    dependencies = [
        ('Building', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='VcenterComplex',
            fields=[
                ('complex_ptr', models.OneToOneField(to='Building.Complex', auto_created=True, primary_key=True, parent_link=True, serialize=False)),
                ('vcenter_username', models.CharField(max_length=50)),
                ('vcenter_password', models.CharField(max_length=50)),
                ('vcenter_datacenter', models.CharField(help_text='set to "ha-datacenter" for ESX hosts', max_length=50)),
                ('vcenter_cluster', models.CharField(null=True, max_length=50, blank=True)),
                ('vcenter_host', models.ForeignKey(help_text='set to VCenter or the ESX host, if ESX host, leave members empty', to='Building.Structure')),
            ],
            bases=('Building.complex',),
        ),
        migrations.CreateModel(
            name='VcenterFoundation',
            fields=[
                ('foundation_ptr', models.OneToOneField(to='Building.Foundation', auto_created=True, primary_key=True, parent_link=True, serialize=False)),
                ('vcenter_uuid', models.CharField(null=True, max_length=36, blank=True)),
                ('vcenter_host', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='Vcenter.VcenterComplex')),
            ],
            bases=('Building.foundation',),
        ),
        migrations.RunPython( load_foundation_blueprints ),
    ]
