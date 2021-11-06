from django.db import models
from django.core.exceptions import ValidationError

from cinp.orm_django import DjangoCInP as CInP

from contractor.Site.models import Site
from contractor.Building.models import Foundation, Complex, FOUNDATION_SUBCLASS_LIST, COMPLEX_SUBCLASS_LIST
from contractor.Foreman.lib import RUNNER_MODULE_LIST
from contractor.BluePrint.models import FoundationBluePrint
from contractor.lib.config import getConfig, mergeValues

from contractor_plugins.Packet.module import set_power, power_state, wait_for_poweroff, destroy, sync_networking_info

cinp = CInP( 'Packet', '0.1' )

FOUNDATION_SUBCLASS_LIST.append( 'packetfoundation' )
COMPLEX_SUBCLASS_LIST.append( 'packetcomplex' )
RUNNER_MODULE_LIST.append( 'contractor_plugins.Packet.module' )


@cinp.model( property_list=( 'state', 'type' ) )
class PacketComplex( Complex ):
  packet_auth_token = models.CharField( max_length=32 )
  packet_facility = models.CharField( max_length=36 )
  packet_project = models.CharField( max_length=36 )

  @property
  def subclass( self ):
    return self

  @property
  def state( self ):
    return 'built'

  @property
  def type( self ):
    return 'Packet'

  @property
  def connection_paramaters( self ):
    if self.packet_auth_token.startswith( '_VAULT_' ):
      creds = self.packet_auth_token[ :7 ]

    else:
      creds = {
                'token': self.packet_auth_token
              }

    return {
              'credentials': creds
            }

  def newFoundation( self, hostname, site ):
    foundation = PacketFoundation( site=site, blueprint=FoundationBluePrint.objects.get( pk='packet-device-base' ), locator=hostname )
    foundation.packet_complex = self
    foundation.full_clean()
    foundation.save()

    return foundation

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, method, id_list, action=None ):
    return super( __class__, __class__ ).checkAuth( user, method, id_list, action )

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )
    errors = {}

    if errors:
      raise ValidationError( errors )

  class Meta:
    default_permissions = ()

  def __str__( self ):
    return 'PacketComplex {0}'.format( self.pk )


def _deviceSpec( foundation ):
  result = {}

  structure_config = getConfig( foundation.structure )
  structure_config = mergeValues( structure_config )

  result[ 'hostname' ] = foundation.structure.hostname
  result[ 'plan' ] = structure_config.get( 'packet_plan', '18e285e0-1872-11ea-8d71-362b9e155667' )  # 'c3.small.x86'
  result[ 'os' ] = structure_config.get( 'packet_os', 'ubuntu_20_04' )

  return result


@cinp.model( property_list=( 'state', 'type', 'class_list' ), read_only_list=( 'packet_uuid', ) )
class PacketFoundation( Foundation ):
  packet_complex = models.ForeignKey( PacketComplex, on_delete=models.PROTECT )
  packet_uuid = models.CharField( max_length=36, blank=True, null=True )

  @staticmethod
  def getTscriptValues( write_mode=False ):  # locator is handled seperatly
    result = super( PacketFoundation, PacketFoundation ).getTscriptValues( write_mode )

    result[ 'packet_complex' ] = ( lambda foundation: foundation.packet_complex, None )
    result[ 'packet_uuid' ] = ( lambda foundation: foundation.packet_uuid, None )
    result[ 'packet_devicespec'] = ( lambda foundation: _deviceSpec( foundation ), None )

    if write_mode is True:
      result[ 'packet_uuid' ] = ( result[ 'packet_uuid' ][0], lambda foundation, val: setattr( foundation, 'packet_uuid', val ) )

    return result

  @staticmethod
  def getTscriptFunctions():
    result = super( PacketFoundation, PacketFoundation ).getTscriptFunctions()
    result[ 'power_on' ] = lambda foundation: ( 'packet', set_power( foundation, 'on' ) )
    result[ 'power_off' ] = lambda foundation: ( 'packet', set_power( foundation, 'off' ) )
    result[ 'power_state' ] = lambda foundation: ( 'packet', power_state( foundation ) )
    result[ 'wait_for_poweroff' ] = lambda foundation: ( 'packet', wait_for_poweroff( foundation ) )
    result[ 'destroy' ] = lambda foundation: ( 'packet', destroy( foundation ) )
    result[ 'sync_networking_info' ] = lambda foundation: ( 'packet', sync_networking_info( foundation ) )

    return result

  def configAttributes( self ):
    result = super().configAttributes()
    result.update( { '_packet_uuid': self.packet_uuid } )
    result.update( { '_packet_complex': self.packet_complex.name } )
    result.update( { '_packet_project': self.packet_complex.packet_project } )
    result.update( { '_packet_facility': self.packet_complex.packet_facility } )

    return result

  @property
  def subclass( self ):
    return self

  @property
  def type( self ):
    return 'Packet'

  @property
  def class_list( self ):
    return [ 'Packet' ]

  @property
  def complex( self ):
    return self.packet_complex

  @cinp.list_filter( name='site', paramater_type_list=[ { 'type': 'Model', 'model': Site } ] )
  @staticmethod
  def filter_site( site ):
    return PacketFoundation.objects.filter( site=site )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, method, id_list, action=None ):
    return super( __class__, __class__ ).checkAuth( user, method, id_list, action )

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )
    errors = {}

    if self.pk is not None:
      current = PacketFoundation.objects.get( pk=self.pk )
      if ( self.packet_uuid is not None or current.packet_uuid is not None ) and current.packet_complex != self.packet_complex:
        errors[ 'packet_complex' ] = 'can not move complexes without first destroying'

    if errors:
      raise ValidationError( errors )

  class Meta:
    default_permissions = ()

  def __str__( self ):
    return 'PacketFoundation {0}'.format( self.pk )
