import random
from django.db import models
from django.core.exceptions import ValidationError

from cinp.orm_django import DjangoCInP as CInP

from contractor.Site.models import Site
from contractor.Building.models import Foundation, Complex, FOUNDATION_SUBCLASS_LIST, COMPLEX_SUBCLASS_LIST
from contractor.Foreman.lib import RUNNER_MODULE_LIST
from contractor.BluePrint.models import FoundationBluePrint
from contractor.lib.config import getConfig, mergeValues

from contractor_plugins.Proxmox.module import set_power, power_state, wait_for_poweroff, destroy, get_interface_map, set_interface_macs

cinp = CInP( 'Proxmox', '0.1' )

FOUNDATION_SUBCLASS_LIST.append( 'proxmoxfoundation' )
COMPLEX_SUBCLASS_LIST.append( 'proxmoxcomplex' )
RUNNER_MODULE_LIST.append( 'contractor_plugins.Proxmox.module' )


@cinp.model( property_list=( 'state', 'type' ) )
class ProxmoxComplex( Complex ):  # NOTE: will use the first member as the Host to send API requests to
  proxmox_username = models.CharField( max_length=50 )
  proxmox_password = models.CharField( max_length=50 )

  @property
  def subclass( self ):
    return self

  @property
  def type( self ):
    return 'Proxmox'

  @property
  def connection_paramaters( self ):
    if self.proxmox_password == '_VAULT_':
      creds = self.proxmox_username

    else:
      creds = {
                'username': self.proxmox_username,
                'password': self.proxmox_password
              }

    return {
              'host': self.members.all()[0].primary_address.ip_address,
              'credentials': creds
            }

  def newFoundation( self, hostname, site ):
    foundation = ProxmoxFoundation( site=site, blueprint=FoundationBluePrint.objects.get( pk='proxmox-qemu-base' ), locator=hostname )
    foundation.proxmox_complex = self
    foundation.full_clean()
    foundation.save()

    return foundation

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, method, id_list, action=None ):
    return super().checkAuth( user, method, id_list, action )

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )
    errors = {}

    if errors:
      raise ValidationError( errors )

  class Meta:
    default_permissions = ()

  def __str__( self ):
    return 'ProxmoxComplex {0}'.format( self.pk )


def _vmSpec( foundation ):
  result = {}

  structure_config = getConfig( foundation.structure )
  structure_config = mergeValues( structure_config )

  result[ 'vmid' ] = foundation.proxmox_vmid
  result[ 'core_count' ] = structure_config.get( 'cpu_count', 1 )
  result[ 'memory_size' ] = structure_config.get( 'memory_size', 1024 )  # in MiB
  # result[ 'swap_size' ] = structure_config.get( 'swap_size', 1024 ) # for lxc
  result[ 'disk_size' ] = structure_config.get( 'disk_size', 10 )  # in GiB
  result[ 'type' ] = 'qemu'  # only support quemu right now

  return result


@cinp.model( property_list=( 'state', 'type', 'class_list' ), read_only_list=( 'proxmox_vmid', ) )
class ProxmoxFoundation( Foundation ):
  proxmox_complex = models.ForeignKey( ProxmoxComplex, on_delete=models.PROTECT )
  proxmox_vmid = models.IntegerField( blank=True, null=True )  # not going to do unique, there could be lots of proxmox instances

  @staticmethod
  def getTscriptValues( write_mode=False ):  # locator is handled seperatly
    result = super( ProxmoxFoundation, ProxmoxFoundation ).getTscriptValues( write_mode )

    result[ 'proxmox_complex' ] = ( lambda foundation: foundation.proxmox_complex, None )
    result[ 'proxmox_vmid' ] = ( lambda foundation: foundation.proxmox_vmid, None )
    result[ 'proxmox_vmspec'] = ( lambda foundation: _vmSpec( foundation ), None )

    return result

  @staticmethod
  def getTscriptFunctions():
    result = super( ProxmoxFoundation, ProxmoxFoundation ).getTscriptFunctions()
    result[ 'power_on' ] = lambda foundation: ( 'proxmox', set_power( foundation, 'on' ) )
    result[ 'power_off' ] = lambda foundation: ( 'proxmox', set_power( foundation, 'off' ) )
    result[ 'power_state' ] = lambda foundation: ( 'proxmox', power_state( foundation ) )
    result[ 'wait_for_poweroff' ] = lambda foundation: ( 'proxmox', wait_for_poweroff( foundation ) )
    result[ 'destroy' ] = lambda foundation: ( 'proxmox', destroy( foundation ) )
    result[ 'get_interface_map' ] = lambda foundation: ( 'proxmox', get_interface_map( foundation ) )
    result[ 'set_interface_macs' ] = lambda foundation: set_interface_macs( foundation )

    return result

  def configAttributes( self ):
    result = super().configAttributes()
    result.update( { '_proxmox_vmid': self.proxmox_vmid } )
    result.update( { '_proxmox_complex': self.proxmox_complex.name } )

    return result

  @property
  def subclass( self ):
    return self

  @property
  def type( self ):
    return 'Proxmox'

  @property
  def class_list( self ):
    return [ 'VM', 'Proxmox' ]

  @property
  def complex( self ):
    return self.proxmox_complex

  @cinp.list_filter( name='site', paramater_type_list=[ { 'type': 'Model', 'model': Site } ] )
  @staticmethod
  def filter_site( site ):
    return ProxmoxFoundation.objects.filter( site=site )

  @cinp.check_auth()
  @staticmethod
  def checkAuth( user, method, id_list, action=None ):
    return super().checkAuth( user, method, id_list, action )

  def clean( self, *args, **kwargs ):
    super().clean( *args, **kwargs )
    errors = {}

    if not self.proxmox_vmid:
      self.proxmox_vmid = random.randint( 100, 999999999 )  # found this by trial and error, thanks Mark
      # TODO: make sure this randomally generated number isn't in use for this complex

    if self.proxmox_vmid < 100:
      errors[ 'proxmox_vmid' ] = 'Min value is 100'

    if errors:
      raise ValidationError( errors )

  class Meta:
    default_permissions = ()
    unique_together = ( ( 'proxmox_complex', 'proxmox_vmid' ), )

  def __str__( self ):
    return 'ProxmoxFoundation {0}'.format( self.pk )
