from django.db import models
from django.core.exceptions import ValidationError

from cinp.orm_django import DjangoCInP as CInP

from contractor.Building.models import Foundation, Complex, FOUNDATION_SUBCLASS_LIST, COMPLEX_SUBCLASS_LIST
from contractor.Foreman.lib import RUNNER_MODULE_LIST
from contractor.Utilities.models import RealNetworkInterface
from contractor.BluePrint.models import FoundationBluePrint
from contractor.lib.config import _structureConfig

from contractor_plugins.Docker.module import start_stop, state, destroy, map_ports, unmap_ports

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

  def newFoundation( self, hostname ):
    foundation = DockerFoundation( site=self.site, blueprint=FoundationBluePrint.objects.get( pk='generic-docker' ), locator=hostname )
    foundation.docker_host = self
    foundation.full_clean()
    foundation.save()

    iface = RealNetworkInterface( name='eth0', is_provisioning=True )
    iface.foundation = foundation
    iface.physical_location = 'eth0'
    iface.full_clean()
    iface.save()

    return foundation

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


@cinp.model( property_list=( 'state', 'type', 'class_list' ), read_only_list=[ 'docker_id' ] )
class DockerFoundation( Foundation ):
  docker_host = models.ForeignKey( DockerComplex, on_delete=models.PROTECT )
  docker_id = models.CharField( max_length=64, blank=True, null=True )  # not going to do unique, there could be multiple docker hosts

  @staticmethod
  def getTscriptValues( write_mode=False ):  # locator is handled seperatly
    result = super( DockerFoundation, DockerFoundation ).getTscriptValues( write_mode )

    result[ 'docker_id' ] = ( lambda foundation: foundation.docker_id, None )
    result[ 'docker_host' ] = ( lambda foundation: foundation.host_ip, None )

    if write_mode is True:
      result[ 'docker_id' ] = ( result[ 'docker_id' ][0], lambda foundation, val: setattr( foundation, 'docker_id', val ) )

    return result

  @staticmethod
  def getTscriptFunctions():
    result = super( DockerFoundation, DockerFoundation ).getTscriptFunctions()
    result[ 'start' ] = lambda foundation: ( 'docker', start_stop( foundation, 'start' ) )
    result[ 'stop' ] = lambda foundation: ( 'docker', start_stop( foundation, 'stop' ) )
    result[ 'state' ] = lambda foundation: ( 'docker', state( foundation ) )
    result[ 'destroy' ] = lambda foundation: ( 'docker', destroy( foundation ) )
    result[ 'map_ports' ] = lambda foundation: map_ports( foundation )
    result[ 'unmap_ports' ] = lambda foundation: unmap_ports( foundation )

    return result

  def configAttributes( self ):
    structure_blueprint_config = self.structure.blueprint.getConfig()
    result = super().configAttributes()
    result.update( { 'docker_id': self.docker_id } )

    _structureConfig( self.structure, [], structure_blueprint_config )  # TODO: need a getConfig (above) that only does the structure and it's blueprint

    try:
      result.update( { 'docker_image': structure_blueprint_config[ 'docker_image' ] } )
    except KeyError:
      pass

    try:
      result.update( { 'docker_port_map': structure_blueprint_config[ 'docker_port_map' ] } )
    except KeyError:
      pass

    try:
      result.update( { 'docker_port_list': structure_blueprint_config[ 'docker_port_list' ] } )
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
    try:
      return self.docker_host.state == 'built' and self.structure.auto_build
    except AttributeError:
      return False

  @property
  def complex( self ):
    return self.docker_host

  @property
  def host_ip( self ):
    return self.docker_host.members.get().primary_ip

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

    if self.site.pk != self.docker_host.site.pk:
      errors[ 'site' ] = 'Site must match the docker_host\'s site'

    if errors:
      raise ValidationError( errors )

  def __str__( self ):
    return 'DockerFoundation {0}'.format( self.pk )


@cinp.model()
class DockerPort( models.Model ):
  complex = models.ForeignKey( DockerComplex, on_delete=models.CASCADE )
  port = models.IntegerField()
  address_offset = models.IntegerField()
  foundation = models.ForeignKey( DockerFoundation, on_delete=models.SET_NULL, blank=True, null=True )
  foundation_index = models.IntegerField( default=0 )
  updated = models.DateTimeField( editable=False, auto_now=True )
  created = models.DateTimeField( editable=False, auto_now_add=True )

  @property
  def address( self ):
    addr_set = self.complex.members.get().networked_ptr.address_set.order_by( 'is_primary' )
    try:
      return addr_set[ self.address_offset ]
    except KeyError:
      return None

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, verb, id_list, action=None ):
    return True

  def clean( self, *args, **kwargs ):  # TODO: do not allow port or address_offset to change, or find a way to make changes propagate
    super().clean( *args, **kwargs )
    errors = {}

    if self.port > 65535 and self.port < 4096:
      errors[ 'port' ] = 'must be from 4096 to 65535'

    if self.address_offset > 100 and self.address_offset < 0:
      errors[ 'address_offset' ] = 'must be from 0 to 100'

    if self.foundation is not None and self.complex != self.foundation.docker_host:
      errors[ 'foundation' ] = 'Port\'s complex does not match the Foundation\'s complex'

    if errors:
      raise ValidationError( errors )

  class Meta:
    unique_together = ( ( 'foundation', 'foundation_index' ), )

  def __str__( self ):
    return 'DockerPort {0}'.format( self.pk )
