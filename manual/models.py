from contractor.Building.models import Foundation

class ManualFoundation( Foundation ):

  @property
  def manager( self ):
    return ( 'Manual', None )

  def __str__( self ):
    return 'ManualFoundation {0}'.format( self.pk )
