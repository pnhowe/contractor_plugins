import re

from django.core.exceptions import ObjectDoesNotExist, ValidationError

from contractor.tscript.runner import ExternalFunction, ParamaterError, Pause

NAME_REGEX = re.compile( r'^[a-zA-Z][a-zA-Z0-9\.\-_]*$' )
MAX_POWER_SET_ATTEMPTS = 5


# exported functions
class create( ExternalFunction ):
  def __init__( self, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.complete = None
    self.connection_paramaters = {}
    self.vm_paramaters = {}

  @property
  def done( self ):
    return self.complete is True

  @property
  def message( self ):
    if self.complete is True:
      return 'VM Created'
    else:
      return 'Waiting for VM Creation'

  def setup( self, parms ):
    try:
      foundation = self.getScriptValue( 'foundation', 'foundation' )
    except ValueError as e:
      raise ParamaterError( '<internal>', 'Unable to get Foundation: {0}'.format( e ) )

    try:
      proxmox_complex = self.getScriptValue( 'foundation', 'proxmox_complex' )
    except ValueError as e:
      raise ParamaterError( '<internal>', 'Unable to get Foundation proxmox_complex: {0}'.format( e ) )

    self.connection_paramaters = proxmox_complex.connection_paramaters

    self.vm_paramaters = { 'vmid': foundation.proxmox_vmid }

    try:
      self.vm_paramaters[ 'name' ] = self.getScriptValue( 'foundation', 'locator' )
    except KeyError as e:
      raise ParamaterError( '<internal>', 'Unable to get Foundation Locator: {0}'.format( e ) )

    if not NAME_REGEX.match( self.vm_paramaters[ 'name' ] ):
      raise ParamaterError( 'invalid name' )

    try:
      vm_spec = parms[ 'vm_spec' ]
    except KeyError:
      raise ParamaterError( 'vm_spec', 'required' )

    if not isinstance( vm_spec, dict ):
      raise ParamaterError( 'vm_spec', 'must be a dict' )

    for key in ( 'node', ):
      try:
        self.vm_paramaters[ key ] = parms[ key ]
      except KeyError:
        raise ParamaterError( key, 'required' )

    for key in ( 'core_count', 'memory_size' ):  # , 'swap_size' ): for lxc
      try:
        self.vm_paramaters[ key ] = int( vm_spec[ key ] )
      except KeyError:
        raise ParamaterError( 'vm_spec.{0}'.format( key ), 'required' )
      except ( ValueError, TypeError ):
        raise ParamaterError( 'vm_spec.{0}'.format( key ), 'must be an integer' )

    if self.vm_paramaters[ 'core_count' ] > 64 or self.vm_paramaters[ 'core_count' ] < 1:
      raise ParamaterError( 'core_count', 'must be from 1 to 64')
    if self.vm_paramaters[ 'memory_size' ] > 1048510 or self.vm_paramaters[ 'memory_size' ] < 512:  # in MiB
      raise ParamaterError( 'memory_size', 'must be from 512 to 1048510' )
    # if self.vm_paramaters[ 'swap_size' ] > 1048510 or self.vm_paramaters[ 'swap_size' ] < 512:  # in MiB  for lxc
    #   raise ParamaterError( 'swap_size', 'must be from 512 to 1048510' )

    for key in ( 'proxmox_ostype', ):
      try:
        self.vm_paramaters[ key[ 8: ] ] = vm_spec[ key ]
      except KeyError:
        pass

    interface_type = 'virtio'
    interface_list = []
    for interface in foundation.networkinterface_set.all().order_by( 'physical_location' ):
      interface_list.append( { 'name': interface.name, 'physical_location': interface.physical_location, 'network': interface.network.name, 'type': interface_type } )

    self.vm_paramaters[ 'disk_list' ] = [ { 'size': vm_spec.get( 'disk_size', 10 ), 'name': 'sda', 'type': vm_spec.get( 'disk_provisioning', 'thick' ) } ]  # disk size in GiB
    self.vm_paramaters[ 'interface_list' ] = interface_list
    self.vm_paramaters[ 'boot_order' ] = [ 'net', 'hdd' ]  # list of 'net', 'hdd', 'cd'

  def toSubcontractor( self ):
    return ( 'create', { 'connection': self.connection_paramaters, 'vm': self.vm_paramaters } )

  def fromSubcontractor( self, data ):
    self.complete = True

  def __getstate__( self ):
    return ( self.connection_paramaters, self.vm_paramaters, self.complete )

  def __setstate__( self, state ):
    self.connection_paramaters = state[0]
    self.vm_paramaters = state[1]
    self.complete = state[2]


class node_list( ExternalFunction ):
  def __init__( self, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.node_list = None
    self.connection_paramaters = {}
    self.min_memory = None
    self.min_cores = None
    self.scalers = { 'cpu': 4, 'memory': 4, 'io': 8, 'vm': 1 }  # must be integers

  @property
  def done( self ):
    return self.node_list is not None

  @property
  def message( self ):
    if self.node_list is not None:
      return 'Node List Length: "{0}"'.format( len( self.node_list ) )
    else:
      return 'Waiting for Node List'

  @property
  def value( self ):
    return self.node_list

  def setup( self, parms ):
    try:
      proxmox_complex = self.getScriptValue( 'foundation', 'proxmox_complex' )
    except ValueError as e:
      raise ParamaterError( '<internal>', 'Unable to get Foundation proxmox_complex: {0}'.format( e ) )

    self.connection_paramaters = proxmox_complex.connection_paramaters

    for key in ( 'min_memory', 'min_cores' ):  # memory in MB
      try:
        setattr( self, key, int( parms[ key ] ) )
      except KeyError:
        raise ParamaterError( key, 'required' )
      except ( ValueError, TypeError ):
        raise ParamaterError( key, 'must be an integer' )

    for name in ( 'cpu', 'memory', 'io', 'vm' ):  # each is turned into a value from 0 -> 1, 1 being most desireable, then * by the scaler and added up, and sorted
      try:
        self.scalers[ name ] = int( parms[ '{0}_scaler'.format( name ) ] )
      except KeyError:
        pass
      except ( ValueError, TypeError ):
        raise ParamaterError( '{0}_scaler'.format( name ), 'must be an integer' )

  def toSubcontractor( self ):
    return ( 'node_list', { 'connection': self.connection_paramaters, 'min_memory': self.min_memory, 'min_cores': self.min_cores, 'scalers': self.scalers } )

  def fromSubcontractor( self, data ):
    self.node_list = data[ 'node_list' ]

  def __getstate__( self ):
    return ( self.connection_paramaters, self.min_memory, self.min_cores, self.scalers, self.node_list )

  def __setstate__( self, state ):
    self.connection_paramaters = state[0]
    self.min_memory = state[1]
    self.min_cores = state[2]
    self.scalers = state[3]
    self.node_list = state[4]


# other functions used by the proxmox foundation
class destroy( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.vmid = foundation.proxmox_vmid
    self.name = foundation.locator
    self.connection_paramaters = foundation.proxmox_complex.connection_paramaters
    self.complete = None

  @property
  def done( self ):
    return self.complete is True

  @property
  def message( self ):
    if self.complete is True:
      return 'VM Destroyed'
    else:
      return 'Waiting for VM Destruction'

  def toSubcontractor( self ):
    return ( 'destroy', { 'connection': self.connection_paramaters, 'vmid': self.vmid, 'name': self.name } )

  def fromSubcontractor( self, data ):
    self.complete = True

  def __getstate__( self ):
    return ( self.connection_paramaters, self.vmid, self.name, self.complete )

  def __setstate__( self, state ):
    self.connection_paramaters = state[0]
    self.vmid = state[1]
    self.name = state[2]
    self.complete = state[3]


class set_power( ExternalFunction ):  # TODO: need a delay after each power command, at least 5 seconds, last ones could possibly be longer
  def __init__( self, foundation, state, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.vmid = foundation.proxmox_vmid
    self.name = foundation.locator
    self.connection_paramaters = foundation.proxmox_complex.connection_paramaters
    self.desired_state = state
    self.curent_state = None
    self.counter = 0

  def run( self ):
    if self.desired_state != self.curent_state and self.counter > MAX_POWER_SET_ATTEMPTS:
      raise Pause( 'To Many Attempts to set power to "{0}", curently "{1}"'.format( self.desired_state, self.curent_state ) )

  @property
  def done( self ):
    return self.desired_state == self.curent_state

  @property
  def message( self ):
    return 'Power curently "{0}" waiting for "{1}", attempt {2} of {3}'.format( self.curent_state, self.desired_state, self.counter, MAX_POWER_SET_ATTEMPTS )

  def rollback( self ):
    self.counter = 0
    self.curent_state = None

  def toSubcontractor( self ):
    self.counter += 1
    if self.desired_state == 'off' and self.counter < 3:  # the first two times, do it nicely, after that, the hard way
      return ( 'set_power', { 'state': 'soft_off', 'connection': self.connection_paramaters, 'vmid': self.vmid, 'name': self.name } )
    else:
      return ( 'set_power', { 'state': self.desired_state, 'connection': self.connection_paramaters, 'vmid': self.vmid, 'name': self.name } )

  def fromSubcontractor( self, data ):
    self.curent_state = data[ 'state' ]

  def __getstate__( self ):
    return ( self.connection_paramaters, self.vmid, self.name, self.desired_state, self.curent_state, self.counter )

  def __setstate__( self, state ):
    self.connection_paramaters = state[0]
    self.vmid = state[1]
    self.name = state[2]
    self.desired_state = state[3]
    self.curent_state = state[4]
    self.counter = state[5]


class power_state( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.vmid = foundation.proxmox_vmid
    self.name = foundation.locator
    self.connection_paramaters = foundation.proxmox_complex.connection_paramaters
    self.state = None

  @property
  def done( self ):
    return self.state is not None

  @property
  def message( self ):
    if self.state is None:
        return 'Retrieving for Power State'

    return 'Power State at "{0}"'.format( self.state )

  @property
  def value( self ):
    return self.state

  def toSubcontractor( self ):
    return ( 'power_state', { 'connection': self.connection_paramaters, 'vmid': self.vmid, 'name': self.name } )

  def fromSubcontractor( self, data ):
    self.state = data[ 'state' ]

  def __getstate__( self ):
    return ( self.connection_paramaters, self.vmid, self.name, self.state )

  def __setstate__( self, state ):
    self.connection_paramaters = state[0]
    self.vmid = state[1]
    self.name = state[2]
    self.state = state[3]


class wait_for_poweroff( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.vmid = foundation.proxmox_vmid
    self.name = foundation.locator
    self.connection_paramaters = foundation.proxmox_complex.connection_paramaters
    self.current_state = None

  @property
  def done( self ):
    return self.current_state == 'off'

  @property
  def message( self ):
    return 'Waiting for Power off, curently "{0}"'.format( self.current_state )

  def toSubcontractor( self ):
    return ( 'power_state', { 'connection': self.connection_paramaters, 'vmid': self.vmid, 'name': self.name } )

  def fromSubcontractor( self, data ):
    self.current_state = data[ 'state' ]

  def __getstate__( self ):
    return ( self.connection_paramaters, self.vmid, self.name, self.current_state )

  def __setstate__( self, state ):
    self.connection_paramaters = state[0]
    self.vmid = state[1]
    self.name = state[2]
    self.current_state = state[3]


class get_interface_map( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.foundation = foundation
    self.vmid = foundation.proxmox_vmid
    self.name = foundation.locator
    self.connection_paramaters = foundation.proxmox_complex.connection_paramaters
    self.interface_list = None

  @property
  def done( self ):
    return self.interface_list is not None

  @property
  def message( self ):
    if self.interface_list is not None:
      return 'Interface Map Length: "{0}"'.format( len( self.interface_list ) )
    else:
      return 'Waiting for Interface Map'

  def setup( self, parms ):
    pass

  @property
  def value( self ):
    pos = 0
    result = {}
    for interface in self.foundation.networkinterface_set.all().order_by( 'physical_location' ):
      result[ interface.physical_location ] = self.interface_list[ pos ]
      pos += 1

    return result

  def toSubcontractor( self ):
    return ( 'get_interface_map', { 'connection': self.connection_paramaters, 'vmid': self.vmid, 'name': self.name } )

  def fromSubcontractor( self, data ):
    self.interface_list = data[ 'interface_list' ]

  def __getstate__( self ):
    return ( self.foundation, self.connection_paramaters, self.vmid, self.name, self.interface_list )

  def __setstate__( self, state ):
    self.foundation = state[0]
    self.connection_paramaters = state[1]
    self.vmid = state[2]
    self.name = state[3]
    self.interface_list = state[4]


class set_interface_macs():
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.foundation = foundation

  def __call__( self, interface_map ):
    for physical_location in interface_map:
      try:
        iface = self.foundation.networkinterface_set.get( physical_location=physical_location )
      except ObjectDoesNotExist:
        raise ParamaterError( 'interface_map', 'interface at "{0}" not found'.format( physical_location ) )

      iface.mac = interface_map[ physical_location ]

      try:
        iface.full_clean()
      except ValidationError as e:
        raise ParamaterError( 'interface_map', 'Error saving interface "{0}": {1}'.format( physical_location, e ) )

      iface.save()


# plugin exports

TSCRIPT_NAME = 'proxmox'

TSCRIPT_FUNCTIONS = {
                      'create': create,
                      'node_list': node_list
                    }

TSCRIPT_VALUES = {
                 }
