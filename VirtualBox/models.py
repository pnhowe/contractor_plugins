from django.db import models

from cinp.orm_django import DjangoCInP as CInP

from contractor.Building.models import Foundation, FOUNDATION_SUBCLASS_LIST
from contractor.Foreman.lib import RUNNER_MODULE_LIST

from contractor_plugins.VirtualBox.module import set_power, power_state, wait_for_poweroff, destroy, set_interface_macs

cinp = CInP( 'VirtualBox', '0.1' )

FOUNDATION_SUBCLASS_LIST.append( 'virtualboxfoundation' )
RUNNER_MODULE_LIST.append( 'contractor_plugins.VirtualBox.module' )


@cinp.model( property_list=( 'state', 'type', 'class_list' ) )
class VirtualBoxFoundation( Foundation ):
  virtualbox_uuid = models.CharField( max_length=36, blank=True, null=True )  # not going to do unique, there could be lots of virtualbox hosts

  @staticmethod
  def getTscriptValues( write_mode=False ):  # locator is handled seperatly
    result = super( VirtualBoxFoundation, VirtualBoxFoundation ).getTscriptValues( write_mode )

    result[ 'virtualbox_uuid' ] = ( lambda foundation: foundation.virtualbox_uuid, None )

    if write_mode is True:
      result[ 'virtualbox_uuid' ] = ( result[ 'virtualbox_uuid' ][0], lambda foundation, val: setattr( foundation, 'virtualbox_uuid', val ) )

    return result

  @staticmethod
  def getTscriptFunctions():
    result = super( VirtualBoxFoundation, VirtualBoxFoundation ).getTscriptFunctions()
    result[ 'power_on' ] = lambda foundation: ( 'virtualbox', set_power( foundation.virtualbox_uuid, 'on', foundation.locator ) )
    result[ 'power_off' ] = lambda foundation: ( 'virtualbox', set_power( foundation.virtualbox_uuid, 'off', foundation.locator ) )
    result[ 'power_state' ] = lambda foundation: ( 'virtualbox', power_state( foundation.virtualbox_uuid, foundation.locator ) )
    result[ 'wait_for_poweroff' ] = lambda foundation: ( 'virtualbox', wait_for_poweroff( foundation.virtualbox_uuid, foundation.locator ) )
    result[ 'destroy' ] = lambda foundation: ( 'virtualbox', destroy( foundation.virtualbox_uuid, foundation.locator ) )
    result[ 'set_interface_macs' ] = lambda foundation: set_interface_macs( foundation )

    return result

  def configValues( self ):
    result = super().configValues()
    result.update( { 'virtualbox_uuid': self.virtualbox_uuid } )

    return result

  @property
  def subclass( self ):
    return self

  @property
  def type( self ):
    return 'VirtualBox'

  @property
  def class_list( self ):
    return [ 'VM', 'VirtualBox' ]

  @property
  def can_auto_locate( self ):
    return self.structure.auto_build

  @cinp.list_filter( name='site', paramater_type_list=[ { 'type': 'Model', 'model': 'contractor.Site.models.Site' } ] )
  @staticmethod
  def filter_site( site ):
    return VirtualBoxFoundation.objects.filter( site=site )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, method, id_list, action=None ):
    return True

  def __str__( self ):
    return 'VirtualBoxFoundation {0}'.format( self.pk )
