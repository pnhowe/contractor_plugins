from django.db import models

from cinp.orm_django import DjangoCInP as CInP

from contractor.Building.models import Foundation, FOUNDATION_SUBCLASS_LIST
from contractor.Foreman.lib import RUNNER_MODULE_LIST

from contractor_plugins.Docker.module import start_stop, state, destroy

cinp = CInP( 'Docker', '0.1' )

FOUNDATION_SUBCLASS_LIST.append( 'dockerfoundation' )
RUNNER_MODULE_LIST.append( 'contractor_plugins.Docker.module' )


@cinp.model( property_list=( 'state', 'type', 'class_list' ) )
class DockerFoundation( Foundation ):
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
    result[ 'start' ] = lambda foundation: ( 'docker', start_stop( foundation.container_id, 'start', foundation.locator ) )
    result[ 'stop' ] = lambda foundation: ( 'docker', start_stop( foundation.container_id, 'stop', foundation.locator ) )
    result[ 'state' ] = lambda foundation: ( 'docker', state( foundation.container_id, foundation.locator ) )
    result[ 'destroy' ] = lambda foundation: ( 'docker', destroy( foundation.container_id, foundation.locator ) )

    return result

  def configValues( self ):
    structure_config = self.structure.blueprint.getConfig()
    result = super().configValues()
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
    return self.structure.auto_build

  @cinp.list_filter( name='site', paramater_type_list=[ { 'type': 'Model', 'model': 'contractor.Site.models.Site' } ] )
  @staticmethod
  def filter_site( site ):
    return DockerFoundation.objects.filter( site=site )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, method, id_list, action=None ):
    return True

  def __str__( self ):
    return 'DockerFoundation {0}'.format( self.pk )
