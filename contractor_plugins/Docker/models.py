from django.db import models
from django.core.exceptions import ValidationError

from cinp.orm_django import DjangoCInP as CInP

from contractor.Building.models import Foundation, Complex, FOUNDATION_SUBCLASS_LIST, COMPLEX_SUBCLASS_LIST
from contractor.Foreman.lib import RUNNER_MODULE_LIST

from contractor_plugins.Docker.module import start_stop, state, destroy

cinp = CInP( 'Docker', '0.1' )

FOUNDATION_SUBCLASS_LIST.append( 'dockerfoundation' )
COMPLEX_SUBCLASS_LIST.append( 'dockercomplex' )
RUNNER_MODULE_LIST.append( 'contractor_plugins.Docker.module' )


@cinp.model( property_list=( 'state', 'type' ) )
class DockerComplex( Complex ):
  @property
  def subclass( self ):
    return self

  @property
  def type( self ):
    return 'Docker'

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, method, id_list, action=None ):
    return True

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )
    errors = {}

    if self.pk and self.members.count() > 1:
      errors[ 'structure' ] = 'Docker Complex support only one structure'

    if errors:
      raise ValidationError( errors )

  def __str__( self ):
    return 'DockerComplex {0}'.format( self.pk )


@cinp.model( property_list=( 'state', 'type', 'class_list' ) )
class DockerFoundation( Foundation ):
  container_host = models.ForeignKey( DockerComplex, on_delete=models.PROTECT )
  container_id = models.CharField( max_length=64, blank=True, null=True )  # not going to do unique, there could be multiple docker hosts

  @staticmethod
  def getTscriptValues( write_mode=False ):  # locator is handled seperatly
    result = super( DockerFoundation, DockerFoundation ).getTscriptValues( write_mode )

    result[ 'container_id' ] = ( lambda foundation: foundation.docker_id, None )

    if write_mode is True:
      result[ 'container_id' ] = ( result[ 'container_id' ][0], lambda foundation, val: setattr( foundation, 'container_id', val ) )

    return result

  @staticmethod
  def getTscriptFunctions():
    result = super( DockerFoundation, DockerFoundation ).getTscriptFunctions()
    result[ 'start' ] = lambda foundation: ( 'docker', start_stop( foundation, 'start' ) )
    result[ 'stop' ] = lambda foundation: ( 'docker', start_stop( foundation, 'stop' ) )
    result[ 'state' ] = lambda foundation: ( 'docker', state( foundation ) )
    result[ 'destroy' ] = lambda foundation: ( 'docker', destroy( foundation ) )

    return result

  def configAttributes( self ):
    structure_config = self.structure.blueprint.getConfig()
    result = super().configAttributes()
    result.update( { 'container_id': self.container_id } )

    try:
      result.update( { 'docker_image': structure_config[ 'docker_image' ] } )
    except KeyError:
      pass

    return result

  @property
  def subclass( self ):
    return self

  @property
  def type( self ):
    return 'Docker'

  @property
  def class_list( self ):
    return [ 'Docker' ]

  @property
  def can_auto_locate( self ):
    return self.container_host.state == 'built' and self.structure.auto_build

  @property
  def complex( self ):
    return self.container_host

  @cinp.list_filter( name='site', paramater_type_list=[ { 'type': 'Model', 'model': 'contractor.Site.models.Site' } ] )
  @staticmethod
  def filter_site( site ):
    return DockerFoundation.objects.filter( site=site )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, method, id_list, action=None ):
    return True

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )
    errors = {}

    if self.site.pk != self.container_host.site.pk:
      errors[ 'site' ] = 'Site must match the container_host\'s site'

    if errors:
      raise ValidationError( errors )

  def __str__( self ):
    return 'DockerFoundation {0}'.format( self.pk )
