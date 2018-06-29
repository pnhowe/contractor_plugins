import re
from django.db import models
from django.core.exceptions import ValidationError

from cinp.orm_django import DjangoCInP as CInP

from contractor.Building.models import Foundation, Complex, Structure, FOUNDATION_SUBCLASS_LIST, COMPLEX_SUBCLASS_LIST
from contractor.Foreman.lib import RUNNER_MODULE_LIST
from contractor.Utilities.models import RealNetworkInterface
from contractor.BluePrint.models import FoundationBluePrint

from contractor_plugins.VCenter.module import set_power, power_state, wait_for_poweroff, destroy, get_interface_map, set_interface_macs

cinp = CInP( 'VCenter', '0.1' )

FOUNDATION_SUBCLASS_LIST.append( 'vcenterfoundation' )
COMPLEX_SUBCLASS_LIST.append( 'vcentercomplex' )
RUNNER_MODULE_LIST.append( 'contractor_plugins.VCenter.module' )

datacenter_name_regex = re.compile( '^[a-zA-Z0-9][a-zA-Z0-9_\-]*$' )
cluster_name_regex = re.compile( '^[a-zA-Z0-9][a-zA-Z0-9_\-\.]*$' )


@cinp.model( property_list=( 'state', 'type' ) )
class VCenterComplex( Complex ):
  vcenter_host = models.ForeignKey( Structure, help_text='set to VCenter or the ESX host, if ESX host, leave members empty' )  # no need for unique, the same vcenter_host can be used for multiple clusters
  vcenter_username = models.CharField( max_length=50 )
  vcenter_password = models.CharField( max_length=50 )
  vcenter_datacenter = models.CharField( max_length=50, help_text='set to "ha-datacenter" for ESX hosts' )
  vcenter_cluster = models.CharField( max_length=50, blank=True, null=True )

  @property
  def subclass( self ):
    return self

  @property
  def state( self ):
    if self.vcenter_host.state != 'built':
      return 'planned'

    state = super().state
    if state == 'built' and self.vcenter_host.state == 'built':
      return 'built'

    return 'planned'

  @property
  def type( self ):
    return 'VCenter'

  def newFoundation( self, hostname ):
    foundation = VCenterFoundation( site=self.site, blueprint=FoundationBluePrint.objects.get( pk='generic-vcenter' ), locator=hostname )
    foundation.vcenter_host = self
    foundation.full_clean()
    foundation.save()

    iface = RealNetworkInterface( name='eth0', is_provisioning=True )
    iface.foundation = foundation
    iface.physical_location = 'eth0'
    iface.full_clean()
    iface.save()

    return foundation

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, method, id_list, action=None ):
    return True

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )
    errors = {}

    if not datacenter_name_regex.match( self.vcenter_datacenter ):
      errors[ 'vcenter_datacenter' ] = '"{0}" is invalid'.format( self.vcenter_datacenter )

    if not cluster_name_regex.match( self.vcenter_cluster ):
      errors[ 'vcenter_cluster' ] = '"{0}" is invalid'.format( self.vcenter_cluster )

    if errors:
      raise ValidationError( errors )

  def __str__( self ):
    return 'VCenterComplex {0}'.format( self.pk )


@cinp.model( property_list=( 'state', 'type', 'class_list' ) )
class VCenterFoundation( Foundation ):
  vcenter_host = models.ForeignKey( VCenterComplex, on_delete=models.PROTECT )
  vcenter_uuid = models.CharField( max_length=36, blank=True, null=True )  # not going to do unique, there could be lots of vcenter clusters

  @staticmethod
  def getTscriptValues( write_mode=False ):  # locator is handled seperatly
    result = super( VCenterFoundation, VCenterFoundation ).getTscriptValues( write_mode )

    result[ 'vcenter_host' ] = ( lambda foundation: foundation.host_ip, None )
    result[ 'vcenter_username' ] = ( lambda foundation: foundation.vcenter_host.vcenter_username, None )
    result[ 'vcenter_password' ] = ( lambda foundation: foundation.vcenter_host.vcenter_password, None )
    result[ 'vcenter_datacenter' ] = ( lambda foundation: foundation.vcenter_host.vcenter_datacenter, None )
    result[ 'vcenter_cluster' ] = ( lambda foundation: foundation.vcenter_host.vcenter_cluster, None )

    result[ 'vcenter_uuid' ] = ( lambda foundation: foundation.vcenter_uuid, None )

    if write_mode is True:
      result[ 'vcenter_uuid' ] = ( result[ 'vcenter_uuid' ][0], lambda foundation, val: setattr( foundation, 'vcenter_uuid', val ) )

    return result

  @staticmethod
  def getTscriptFunctions():
    result = super( VCenterFoundation, VCenterFoundation ).getTscriptFunctions()
    result[ 'power_on' ] = lambda foundation: ( 'vcenter', set_power( foundation, 'on' ) )
    result[ 'power_off' ] = lambda foundation: ( 'vcenter', set_power( foundation, 'off' ) )
    result[ 'power_state' ] = lambda foundation: ( 'vcenter', power_state( foundation ) )
    result[ 'wait_for_poweroff' ] = lambda foundation: ( 'vcenter', wait_for_poweroff( foundation ) )
    result[ 'destroy' ] = lambda foundation: ( 'vcenter', destroy( foundation ) )
    result[ 'get_interface_map' ] = lambda foundation: ( 'vcenter', get_interface_map( foundation ) )
    result[ 'set_interface_macs' ] = lambda foundation: set_interface_macs( foundation )

    return result

  def configAttributes( self ):
    result = super().configAttributes()
    result.update( { 'vcenter_uuid': self.vcenter_uuid } )

    return result

  @property
  def subclass( self ):
    return self

  @property
  def type( self ):
    return 'VCenter'

  @property
  def class_list( self ):
    return [ 'VM', 'VCenter' ]

  @property
  def can_auto_locate( self ):
    try:
      return self.vcenter_host.state == 'built' and self.structure.auto_build
    except AttributeError:
      return False

  @property
  def complex( self ):
    return self.vcenter_host

  @property
  def host_ip( self ):
    return self.vcenter_host.vcenter_host.primary_ip

  @cinp.list_filter( name='site', paramater_type_list=[ { 'type': 'Model', 'model': 'contractor.Site.models.Site' } ] )
  @staticmethod
  def filter_site( site ):
    return VCenterFoundation.objects.filter( site=site )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, method, id_list, action=None ):
    return True

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )
    errors = {}

    if errors:
      raise ValidationError( errors )

  def __str__( self ):
    return 'VCenterFoundation {0}'.format( self.pk )
