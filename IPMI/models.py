from django.db import models

from contractor.Building.models import Foundation
from contractor.Utilities.models import PhysicalNetworkInterface, Networked

class IPMIFoundation( Foundation, Networked ):
  ipmi_interface = models.ForeignKey( PhysicalNetworkInterface )

  def __str__( self ):
    return 'IPMIFoundation {0}'.format( self.pk )
