from cinp.orm_django import DjangoCInP as CInP

from contractor.Building.models import Foundation, FOUNDATION_SUBCLASS_LIST

cinp = CInP( 'Manual', '0.1' )

FOUNDATION_SUBCLASS_LIST.append( 'manualfoundation' )

@cinp.model( property_list=( 'state', 'type' ) )
class ManualFoundation( Foundation ):
  @property
  def manager( self ):
    return ( None, None )

  @property
  def type( self ):
    return 'Manual'

  @property
  def class_list( self ):
    return [ 'Metal', 'Manual' ]

  @property
  def can_auto_locate( self ):
    return False

  @cinp.list_filter( name='site', paramater_type_list=[ { 'type': 'Model', 'model': 'contractor.Site.models.Site' } ] )
  @staticmethod
  def filter_site( site ):
    return VirtualBoxFoundation.objects.filter( site=site )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, method, id_list, action=None ):
    return True


  def __str__( self ):
    return 'ManualFoundation {0}'.format( self.pk )
