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
    interface_list = []
    counter = 0
    for name in INTERFACE_NAME_LIST:
      interface_list.append( { 'name': name, 'network': 'vboxnet0', 'type': 'host' } )  # type one of 'host', 'bridge', 'nat', 'internal',  max 4 interfaces
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
      self.vm_paramaters[ 'name' ] = self.getScriptValue( 'foundation', 'locator' )
    except KeyError as e:
      raise ParamaterError( '<internal>', 'Unable to get Foundation Locator: {0}'.format( e ) )

    try:
      self.vm_paramaters[ 'cpu_count' ] = int( parms.get( 'cpu_count', 1 ) )
    except ( ValueError, TypeError ):
      raise ParamaterError( 'cpu_count', 'must be an integer' )

    try:
      self.vm_paramaters[ 'memory_size' ] = int( parms.get( 'memory_size', 1024 ) )
    except ( ValueError, TypeError ):
      raise ParamaterError( 'memory_size', 'must be an integer' )

    if not NAME_REGEX.match( self.vm_paramaters[ 'name' ] ):
      raise ParamaterError( 'invalid name' )
    if self.vm_paramaters[ 'cpu_count' ] > 64 or self.vm_paramaters[ 'cpu_count' ] < 1:
      raise ParamaterError( 'cpu_count', 'must be from 1 to 64')
    if self.vm_paramaters[ 'memory_size' ] > 1048510 or self.vm_paramaters[ 'memory_size' ] < 512:  # in MB
      raise ParamaterError( 'memory_size', 'must be from 512 to 1048510' )

  def toSubcontractor( self ):
    if self.in_rollback:
      return ( 'create_rollback', { 'vm': self.vm_paramaters } )
    else:
      return ( 'create', { 'vm': self.vm_paramaters } )

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
    return ( self.vm_paramaters, self.in_rollback, self.uuid )

  def __setstate__( self, state ):
    self.vm_paramaters = state[0]
    self.in_rollback = state[1]
    self.uuid = state[2]


# other functions used by the virtualbox foundation
class destroy( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.uuid = foundation.virtualbox_uuid
    self.name = foundation.locator
    self.done = None

  @property
  def ready( self ):
    if self.done is True:
      return True
    else:
      return 'Waiting for VM Destruction'

  def toSubcontractor( self ):
    return ( 'destroy', { 'uuid': self.uuid, 'name': self.name } )

  def fromSubcontractor( self, data ):
    self.done = True

  def __getstate__( self ):
    return ( self.done, self.name, self.uuid )

  def __setstate__( self, state ):
    self.done = state[0]
    self.name = state[1]
    self.uuid = state[2]


class set_power( ExternalFunction ):  # TODO: need a delay after each power command, at least 5 seconds, last ones could possibly be longer
  def __init__( self, foundation, state, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.uuid = foundation.virtualbox_uuid
    self.name = foundation.locator
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
      return ( 'set_power', { 'state': 'soft_off', 'uuid': self.uuid, 'name': self.name } )
    else:
      return ( 'set_power', { 'state': self.desired_state, 'uuid': self.uuid, 'name': self.name } )

  def fromSubcontractor( self, data ):
    self.curent_state = data[ 'state' ]

  def __getstate__( self ):
    return ( self.uuid, self.name, self.desired_state, self.curent_state, self.counter )

  def __setstate__( self, state ):
    self.uuid = state[0]
    self.name = state[1]
    self.desired_state = state[2]
    self.curent_state = state[3]
    self.counter = state[4]


class power_state( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.uuid = foundation.virtualbox_uuid
    self.name = foundation.locator
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
    return ( 'power_state', { 'uuid': self.uuid, 'name': self.name } )

  def fromSubcontractor( self, data ):
    self.state = data[ 'state' ]

  def __getstate__( self ):
    return ( self.uuid, self.name, self.state )

  def __setstate__( self, state ):
    self.uuid = state[0]
    self.name = state[1]
    self.state = state[2]


class wait_for_poweroff( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.uuid = foundation.virtualbox_uuid
    self.name = foundation.locator
    self.current_state = None

  @property
  def ready( self ):
    if self.current_state == 'off':
      return True
    else:
      return 'Waiting for Power off, curently "{0}"'.format( self.current_state )

  def toSubcontractor( self ):
    return ( 'power_state', { 'uuid': self.uuid, 'name': self.name } )

  def fromSubcontractor( self, data ):
    self.current_state = data[ 'state' ]

  def __getstate__( self ):
    return ( self.uuid, self.name, self.current_state )

  def __setstate__( self, state ):
    self.uuid = state[0]
    self.name = state[1]
    self.current_state = state[2]


class get_interface_map( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.uuid = foundation.virtualbox_uuid
    self.name = foundation.locator
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
    return ( 'get_interface_map', { 'uuid': self.uuid, 'name': self.name } )

  def fromSubcontractor( self, data ):
    self.interface_list = data[ 'interface_list' ]

  def __getstate__( self ):
    return ( self.uuid, self.name, self.interface_list )

  def __setstate__( self, state ):
    self.uuid = state[0]
    self.name = state[1]
    self.interface_list = state[2]


class set_interface_macs():
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.foundation = foundation

  def __call__( self, interface_list ):
    for interface in interface_list:
      try:
        iface = self.foundation.networkinterface_set.get( name=interface[ 'name' ] )
      except ObjectDoesNotExist:
        raise ParamaterError( 'interface_list', 'interface named "{0}" not found'.format( interface[ 'name' ] ) )

      iface.mac = interface[ 'mac' ]

      try:
        iface.full_clean()
      except ValidationError as e:
        raise ParamaterError( 'interface_list', 'Error saving interface "{0}": {1}'.format( interface[ 'name' ], e ) )

      iface.save()

# plugin exports

TSCRIPT_NAME = 'virtualbox'

TSCRIPT_FUNCTIONS = {
                      'create': create,
                    }

TSCRIPT_VALUES = {
                 }
