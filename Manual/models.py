from django.db import models
from django.core.exceptions import ValidationError

from cinp.orm_django import DjangoCInP as CInP

from contractor.Building.models import Foundation, Complex, FOUNDATION_SUBCLASS_LIST, COMPLEX_SUBCLASS_LIST

cinp = CInP( 'Manual', '0.1' )

FOUNDATION_SUBCLASS_LIST.append( 'manualfoundation' )
COMPLEX_SUBCLASS_LIST.append( 'manualcomplex' )


@cinp.model( property_list=( 'state', 'type' ) )
class ManualComplex( Complex ):
  @property
  def subclass( self ):
    return self

  @property
  def type( self ):
    return 'Manual'

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, method, id_list, action=None ):
    return True

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )
    errors = {}

    if errors:
      raise ValidationError( errors )

  def __str__( self ):
    return 'ManualComplex {0}'.format( self.pk )


@cinp.model( property_list=( 'state', 'type', 'class_list' ) )
class ManualFoundation( Foundation ):
  @property
  def subclass( self ):
    return self

  @property
  def type( self ):
    return 'Manual'

  @property
  def class_list( self ):
    return [ 'Metal', 'Manual' ]

  @property
  def can_auto_locate( self ):
    return self.structure.auto_build

  @cinp.list_filter( name='site', paramater_type_list=[ { 'type': 'Model', 'model': 'contractor.Site.models.Site' } ] )
  @staticmethod
  def filter_site( site ):
    return ManualFoundation.objects.filter( site=site )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, method, id_list, action=None ):
    return True

  def __str__( self ):
    return 'ManualFoundation {0}'.format( self.pk )


@cinp.model( property_list=( 'state', 'type', 'class_list' ) )
class ManualComplexedFoundation( Foundation ):
  complex_host = models.ForeignKey( ManualComplex, on_delete=models.PROTECT )

  @property
  def subclass( self ):
    return self

  @property
  def type( self ):
    return 'ManualComplex'

  @property
  def class_list( self ):
    return [ 'ManualComplex' ]

  @property
  def can_auto_locate( self ):
    return self.complex_host.state == 'built' and self.structure.auto_build

  @cinp.list_filter( name='site', paramater_type_list=[ { 'type': 'Model', 'model': 'contractor.Site.models.Site' } ] )
  @staticmethod
  def filter_site( site ):
    return ManualComplexedFoundation.objects.filter( site=site )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, method, id_list, action=None ):
    return True

  def __str__( self ):
    return 'ManualComplexedFoundation {0}'.format( self.pk )
