from django.db import models

from cinp.orm_django import DjangoCInP as CInP

from contractor.Building.models import Foundation, FOUNDATION_SUBCLASS_LIST
from contractor.Foreman.lib import RUNNER_MODULE_LIST

from contractor_plugins.AWS.module import set_power, power_state, destroy, set_interface_macs

cinp = CInP( 'AWS', '0.1' )

FOUNDATION_SUBCLASS_LIST.append( 'awsoundation' )
RUNNER_MODULE_LIST.append( 'contractor_plugins.AWS.module' )


@cinp.model( property_list=( 'state', 'type', 'class_list' ) )
class AWSEC2Foundation( Foundation ):
  awsec2_uuid = models.CharField( max_length=36, blank=True, null=True )  # not going to do unique, there could be multiple AWS accounts

  @staticmethod
  def getTscriptValues( write_mode=False ):  # locator is handled seperatly
    result = super( AWSEC2Foundation, AWSEC2Foundation ).getTscriptValues( write_mode )

    result[ 'awsec2_uuid' ] = ( lambda foundation: foundation.awsec2_uuid, None )

    if write_mode is True:
      result[ 'awsec2_uuid' ] = ( result[ 'awsec2_uuid' ][0], lambda foundation, val: setattr( foundation, 'awsec2_uuid', val ) )

    return result

  @staticmethod
  def getTscriptFunctions():
    result = super( AWSEC2Foundation, AWSEC2Foundation ).getTscriptFunctions()
    result[ 'power_on' ] = lambda foundation: ( 'virtualbox', set_power( foundation.virtualbox_uuid, 'on', foundation.locator ) )
    result[ 'power_off' ] = lambda foundation: ( 'virtualbox', set_power( foundation.virtualbox_uuid, 'off', foundation.locator ) )
    result[ 'power_state' ] = lambda foundation: ( 'virtualbox', power_state( foundation.virtualbox_uuid, foundation.locator ) )
    result[ 'destroy' ] = lambda foundation: ( 'virtualbox', destroy( foundation.virtualbox_uuid, foundation.locator ) )
    result[ 'set_interface_macs' ] = lambda foundation: set_interface_macs( foundation )

    return result

  def configValues( self ):
    result = super().configValues()
    result.update( { 'awsec2_uuid': self.awsec2_uuid } )

    return result

  @property
  def subclass( self ):
    return self

  @property
  def type( self ):
    return 'AWSEC2'

  @property
  def class_list( self ):
    return [ 'AWSEC2' ]

  @property
  def can_auto_locate( self ):
    return self.structure.auto_build

  @cinp.list_filter( name='site', paramater_type_list=[ { 'type': 'Model', 'model': 'contractor.Site.models.Site' } ] )
  @staticmethod
  def filter_site( site ):
    return AWSEC2Foundation.objects.filter( site=site )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, method, id_list, action=None ):
    return True

  def __str__( self ):
    return 'AWSEC2Foundation {0}'.format( self.pk )
