from cinp.orm_django import DjangoCInP as CInP

from contractor.Building.models import Foundation, FOUNDATION_SUBCLASS_LIST
from contractor.Foreman.lib import RUNNER_MODULE_LIST

cinp = CInP( 'VirtualBox', '0.1' )

FOUNDATION_SUBCLASS_LIST.append( 'virtualboxfoundation' )
RUNNER_MODULE_LIST.append( 'contractor_plugins.VirtualBox.module' )

@cinp.model( property_list=( 'state', 'type', 'class_list' ) )
class VirtualBoxFoundation( Foundation ):
  @property
  def subclass( self ):
    return self

  @property
  def manager( self ):
    return ( 'virtualbox', self.locator )

  @property
  def type( self ):
    return 'VirtualBox'

  @property
  def class_list( self ):
    return [ 'VM', 'VirtualBox' ]

  @property
  def can_auto_locate( self ):
    return True

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
