from django.db import models

from contractor.Building.models import Foundation
from contractor.Utilities.models import RealNetworkInterface, Networked


class IPMIFoundation( Foundation, Networked ):
  ipmi_interface = models.ForeignKey( RealNetworkInterface )

  def __str__( self ):
    return 'IPMIFoundation {0}'.format( self.pk )
