from django.db import models

from cinp.orm_django import DjangoCInP as CInP

from contractor.Building.models import Foundation, FOUNDATION_SUBCLASS_LIST
from contractor.Foreman.lib import RUNNER_MODULE_LIST

from contractor_plugins.Vcenter.module import set_power, power_state, wait_for_poweroff, destroy

cinp = CInP( 'Vcenter', '0.1' )

FOUNDATION_SUBCLASS_LIST.append( 'vcenterfoundation' )
RUNNER_MODULE_LIST.append( 'contractor_plugins.Vcenter.module' )


@cinp.model( property_list=( 'state', 'type', 'class_list' ) )
class VcenterFoundation( Foundation ):
  vcenter_uuid = models.CharField( max_length=36, blank=True, null=True )  # not going to do unique, there could be lots of vcenter clusters

  @staticmethod
  def getTscriptValues( write_mode=False ):  # locator is handled seperatly
    result = super( VcenterFoundation, VcenterFoundation ).getTscriptValues( write_mode )

    result[ 'vcenter_uuid' ] = ( lambda foundation: foundation.vcenter_uuid, None )

    if write_mode is True:
      result[ 'vcenter_uuid' ] = ( result[ 'vcenter_uuid' ][0], lambda foundation, val: setattr( foundation, 'vcenter_uuid', val ) )

    return result

  @staticmethod
  def getTscriptFunctions():
    result = super( VcenterFoundation, VcenterFoundation ).getTscriptFunctions()
    result[ 'power_on' ] = lambda foundation: ( 'vcenter', set_power( foundation.vcenter_uuid, 'on', foundation.locator ) )
    result[ 'power_off' ] = lambda foundation: ( 'vcenter', set_power( foundation.vcenter_uuid, 'off', foundation.locator ) )
    result[ 'power_state' ] = lambda foundation: ( 'vcenter', power_state( foundation.vcenter_uuid, foundation.locator ) )
    result[ 'wait_for_poweroff' ] = lambda foundation: ( 'vcenter', wait_for_poweroff( foundation.vcenter_uuid, foundation.locator ) )
    result[ 'destroy' ] = lambda foundation: ( 'vcenter', destroy( foundation.vcenter_uuid, foundation.locator ) )

    return result

  def configValues( self ):
    result = super().configValues()
    result.update( { 'vcenter_uuid': self.vcenter_uuid } )

    return result

  @property
  def subclass( self ):
    return self

  @property
  def type( self ):
    return 'vcenter'

  @property
  def class_list( self ):
    return [ 'VM', 'Vcenter' ]

  @property
  def can_auto_locate( self ):
    return self.structure.auto_build

  @cinp.list_filter( name='site', paramater_type_list=[ { 'type': 'Model', 'model': 'contractor.Site.models.Site' } ] )
  @staticmethod
  def filter_site( site ):
    return VcenterFoundation.objects.filter( site=site )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, method, id_list, action=None ):
    return True

  def __str__( self ):
    return 'VcenterFoundation {0}'.format( self.pk )
