from django.db import models


class Harddrive( models.Model ):
  serial = models.CharField( max_length=30, primary_key=True )
  model = models.CharField( max_length=30 )
  updated = models.DateTimeField( editable=False, auto_now=True )
  created = models.DateTimeField( editable=False, auto_now_add=True )

  def __str__( self ):
    return 'Harddrive {0}'.format( self.serial, self.model )
