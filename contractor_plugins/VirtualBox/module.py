import re

from django.core.exceptions import ObjectDoesNotExist, ValidationError

from contractor.tscript.runner import ExternalFunction, ParamaterError, Pause

NAME_REGEX = re.compile( '^[a-zA-Z][a-zA-Z0-9\.\-_]*$' )
MAX_POWER_SET_ATTEMPTS = 5

INTERFACE_NAME_LIST = [ 'eth0', 'eth1', 'eth2', 'eth3' ]  # virtualbox does only 4 interfaces


# exported functions
class create( ExternalFunction ):
  def __init__( self, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.uuid = None
    self.in_rollback = False
    self.connection_paramaters = {}
    self.vm_paramaters = {}

  @property
  def ready( self ):
    if self.uuid is not None:
      return True
    else:
      if self.in_rollback:
        return 'Waiting for VM Rollback'
      else:
        return 'Waiting for VM Creation'

  @property
  def value( self ):
    return self.uuid

  def setup( self, parms ):
    try:
      foundation = self.getScriptValue( 'foundation', 'foundation' )
    except ValueError as e:
      raise ParamaterError( '<internal>', 'Unable to get Foundation: {0}'.format( e ) )

    try:
      virtualbox_host = self.getScriptValue( 'foundation', 'virtualbox_host' )
    except ValueError as e:
      raise ParamaterError( '<internal>', 'Unable to get Foundation vcenter_host: {0}'.format( e ) )

    self.connection_paramaters = virtualbox_host.connection_paramaters

    interface_list = []
    counter = 0
    for interface in foundation.networkinterface_set.all().order_by( 'physical_location' )[ :4 ]:  # max 4 interfaces
      name_map = interface.addressblock_name_map
      if not name_map:
        raise ParamaterError( '<internal>', 'addressblock name maping is empty for interface "{0}"'.format( interface.name ) )

      interface_list.append( { 'name': interface.name, 'index': counter, 'network': name_map[ None ], 'type': 'host' } )  # type one of 'host', 'bridge', 'nat', 'internal'
      counter += 1

    self.vm_paramaters = {  # the defaults
                           'disk_list': [ { 'name': 'sda', 'size': 5 } ],  # disk size in G
                           'interface_list': interface_list,
                           'boot_order': [ 'net', 'hdd' ]  # list of 'net', 'hdd', 'cd', 'usb'
                         }

    if False:  # boot from iso instead
      self.vm_paramaters[ 'disk_list' ].append( { 'name': 'cd', 'file': '/home/peter/Downloads/ubuntu-16.04.2-server-amd64.iso' } )
      self.vm_paramaters[ 'boot_order' ][0] = 'cd'

    try:
      vm_spec = parms[ 'vm_spec' ]
    except KeyError:
      raise ParamaterError( 'vm_spec', 'required' )

    if not isinstance( vm_spec, dict ):
      raise ParamaterError( 'vm_spec', 'must be a dict' )

    for key in ( 'cpu_count', 'memory_size' ):
      try:
        self.vm_paramaters[ key ] = int( vm_spec[ key ] )
      except KeyError:
        raise ParamaterError( 'vm_spec.{0}'.format( key ), 'required' )
      except ( ValueError, TypeError ):
        raise ParamaterError( 'vm_spec.{0}'.format( key ), 'must be an integer' )

    if self.vm_paramaters[ 'cpu_count' ] > 64 or self.vm_paramaters[ 'cpu_count' ] < 1:
      raise ParamaterError( 'cpu_count', 'must be from 1 to 64')
    if self.vm_paramaters[ 'memory_size' ] > 1048510 or self.vm_paramaters[ 'memory_size' ] < 512:  # in MB
      raise ParamaterError( 'memory_size', 'must be from 512 to 1048510' )

    try:
      self.vm_paramaters[ 'name' ] = self.getScriptValue( 'foundation', 'locator' )
    except KeyError as e:
      raise ParamaterError( '<internal>', 'Unable to get Foundation Locator: {0}'.format( e ) )

    if not NAME_REGEX.match( self.vm_paramaters[ 'name' ] ):
      raise ParamaterError( 'invalid name' )

    for key in ( 'virtualbox_guest_type', ):
      try:
        self.vm_paramaters[ key[ 11: ] ] = vm_spec[ key ]
      except KeyError:
        pass

  def toSubcontractor( self ):
    if self.in_rollback:
      return ( 'create_rollback', { 'connection': self.connection_paramaters, 'vm': self.vm_paramaters } )
    else:
      return ( 'create', { 'connection': self.connection_paramaters, 'vm': self.vm_paramaters } )

  def fromSubcontractor( self, data ):  # TODO: really if these are missing or false, there is a problem
    if self.in_rollback:
      self.in_rollback = not data.get( 'rollback_done', False )
    else:
      self.uuid = data.get( 'uuid', None )

  def rollback( self ):
    if self.uuid is not None:
      raise ValueError( 'Unable to Rollback after vm has been created' )

    self.in_rollback = True

  def __getstate__( self ):
    return ( self.connection_paramaters, self.vm_paramaters, self.in_rollback, self.uuid )

  def __setstate__( self, state ):
    self.connection_paramaters = state[0]
    self.vm_paramaters = state[1]
    self.in_rollback = state[2]
    self.uuid = state[3]


# other functions used by the virtualbox foundation
class destroy( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.uuid = foundation.virtualbox_uuid
    self.name = foundation.locator
    self.connection_paramaters = foundation.virtualbox_host.connection_paramaters
    self.done = None

  @property
  def ready( self ):
    if self.done is True:
      return True
    else:
      return 'Waiting for VM Destruction'

  def toSubcontractor( self ):
    return ( 'destroy', { 'connection': self.connection_paramaters, 'uuid': self.uuid, 'name': self.name } )

  def fromSubcontractor( self, data ):
    self.done = True

  def __getstate__( self ):
    return ( self.connection_paramaters, self.done, self.name, self.uuid )

  def __setstate__( self, state ):
    self.connection_paramaters = state[0]
    self.done = state[1]
    self.name = state[2]
    self.uuid = state[3]


class set_power( ExternalFunction ):  # TODO: need a delay after each power command, at least 5 seconds, last ones could possibly be longer
  def __init__( self, foundation, state, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.uuid = foundation.virtualbox_uuid
    self.name = foundation.locator
    self.connection_paramaters = foundation.virtualbox_host.connection_paramaters
    self.desired_state = state
    self.curent_state = None
    self.counter = 0

  def run( self ):
    if self.desired_state != self.curent_state and self.counter > MAX_POWER_SET_ATTEMPTS:
      raise Pause( 'To Many Attempts to set power to "{0}", curently "{1}"'.format( self.desired_state, self.curent_state ) )

  @property
  def ready( self ):
    if self.desired_state == self.curent_state:
      return True
    else:
      return 'Power curently "{0}" waiting for "{1}", attempt {2} of {3}'.format( self.curent_state, self.desired_state, self.counter, MAX_POWER_SET_ATTEMPTS )

  def rollback( self ):
    self.counter = 0
    self.curent_state = None

  def toSubcontractor( self ):
    self.counter += 1
    if self.desired_state == 'off' and self.counter < 3:  # the first two times, do it nicely, after that, the hard way
      return ( 'set_power', { 'connection': self.connection_paramaters, 'state': 'soft_off', 'uuid': self.uuid, 'name': self.name } )
    else:
      return ( 'set_power', { 'connection': self.connection_paramaters, 'state': self.desired_state, 'uuid': self.uuid, 'name': self.name } )

  def fromSubcontractor( self, data ):
    self.curent_state = data[ 'state' ]

  def __getstate__( self ):
    return ( self.connection_paramaters, self.uuid, self.name, self.desired_state, self.curent_state, self.counter )

  def __setstate__( self, state ):
    self.connection_paramaters = state[0]
    self.uuid = state[1]
    self.name = state[2]
    self.desired_state = state[3]
    self.curent_state = state[4]
    self.counter = state[5]


class power_state( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.uuid = foundation.virtualbox_uuid
    self.name = foundation.locator
    self.connection_paramaters = foundation.virtualbox_host.connection_paramaters
    self.state = None

  @property
  def ready( self ):
    if self.state is not None:
      return True
    else:
      return 'Retrieving for Power State'

  @property
  def value( self ):
    return self.state

  def toSubcontractor( self ):
    return ( 'power_state', { 'connection': self.connection_paramaters, 'uuid': self.uuid, 'name': self.name } )

  def fromSubcontractor( self, data ):
    self.state = data[ 'state' ]

  def __getstate__( self ):
    return ( self.connection_paramaters, self.uuid, self.name, self.state )

  def __setstate__( self, state ):
    self.connection_paramaters = state[0]
    self.uuid = state[1]
    self.name = state[2]
    self.state = state[3]


class wait_for_poweroff( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.uuid = foundation.virtualbox_uuid
    self.name = foundation.locator
    self.connection_paramaters = foundation.virtualbox_host.connection_paramaters
    self.current_state = None

  @property
  def ready( self ):
    if self.current_state == 'off':
      return True
    else:
      return 'Waiting for Power off, curently "{0}"'.format( self.current_state )

  def toSubcontractor( self ):
    return ( 'power_state', { 'connection': self.connection_paramaters, 'uuid': self.uuid, 'name': self.name } )

  def fromSubcontractor( self, data ):
    self.current_state = data[ 'state' ]

  def __getstate__( self ):
    return ( self.connection_paramaters, self.uuid, self.name, self.current_state )

  def __setstate__( self, state ):
    self.connection_paramaters = state[0]
    self.uuid = state[1]
    self.name = state[2]
    self.current_state = state[3]


class get_interface_map( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.uuid = foundation.virtualbox_uuid
    self.name = foundation.locator
    self.connection_paramaters = foundation.virtualbox_host.connection_paramaters
    self.interface_list = None

  @property
  def ready( self ):
    if self.interface_list is not None:
      return True
    else:
      return 'Waiting for Interface Map'

  def setup( self, parms ):
    pass

  @property
  def value( self ):
    result = {}
    for i in range( 0, min( len( INTERFACE_NAME_LIST ), len( self.interface_list ) ) ):
      result[ INTERFACE_NAME_LIST[ i ] ] = self.interface_list[ i ]

    return result

  def toSubcontractor( self ):
    return ( 'get_interface_map', { 'connection': self.connection_paramaters, 'uuid': self.uuid, 'name': self.name } )

  def fromSubcontractor( self, data ):
    self.interface_list = data[ 'interface_list' ]

  def __getstate__( self ):
    return ( self.connection_paramaters, self.uuid, self.name, self.interface_list )

  def __setstate__( self, state ):
    self.connection_paramaters = state[0]
    self.uuid = state[1]
    self.name = state[2]
    self.interface_list = state[3]


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

TSCRIPT_NAME = 'virtualbox'

TSCRIPT_FUNCTIONS = {
                      'create': create,
                    }

TSCRIPT_VALUES = {
                 }
