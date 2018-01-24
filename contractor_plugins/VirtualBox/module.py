import re

from django.core.exceptions import ObjectDoesNotExist, ValidationError

from contractor.tscript.runner import ExternalFunction, ParamaterError, Pause

NAME_REGEX = re.compile( '^[a-zA-Z][a-zA-Z0-9\.\-_]*$' )
MAX_POWER_SET_ATTEMPTS = 5


# exported functions
class create( ExternalFunction ):
  def __init__( self, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.uuid = None
    self.interface_list = []
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
    return { 'uuid': self.uuid, 'interface_list': self.interface_list }

  def setup( self, parms ):
    try:
      foundation_id = self.getScriptValue( 'foundation', 'id' )
    except ValueError as e:
      raise ParamaterError( '<internal>', 'Unable to get Foundation Id: {0}'.format( e ) )

    try:
      name = self.getScriptValue( 'foundation', 'locator' )
    except ValueError as e:
      raise ParamaterError( '<internal>', 'Unable to get Foundation Locator: {0}'.format( e ) )

    if not NAME_REGEX.match( name ):
      raise ParamaterError( '<internal>', 'invalid name (ie: Foundation Locator)' )

    try:
      cpu_count = self.getScriptValue( 'config', 'cpu_count' )
    except ValueError as e:  # TODO: would be nice to log a warning here
      cpu_count = 1

    try:
      cpu_count = int( cpu_count )
    except TypeError:
      raise ParamaterError( '<internal>', 'cpu count must be integer' )

    if cpu_count > 64 or cpu_count < 1:
      raise ParamaterError( 'cpu_count', 'cpu_count must be from 1 to 64')

    try:
      memory_size = self.getScriptValue( 'config', 'memory_size' )
    except ValueError as e:  # TODO: would be nice to log a warning here
      memory_size = 512

    try:
      memory_size = int( memory_size )
    except TypeError:
      raise ParamaterError( '<internal>', 'cpu count must be integer' )

    if memory_size > 1048510 or memory_size < 512:
      raise ParamaterError( 'memory_size', 'must be from 512 to 1048510' )

    mac = '080027{0:06x}'.format( ( 4 * foundation_id ) )  # leaving room for 4 interfaces per foundation
    self.vm_paramaters = {
                           'name': name,
                           'cpu_count': cpu_count,
                           'memory_size': memory_size,  # in Meg
                           'disk_list': [ { 'name': 'sda', 'size': 5 } ],  # disk size in G
                           'interface_list': [ { 'type': 'bridge', 'network': 'enx847beb5.1000', 'name': 'eth0', 'mac': mac } ],  # type one of 'host', 'bridge', 'nat', 'internal',  max 4 interfaces
                           #'interface_list': [ { 'type': 'host', 'network': 'vboxnet0', 'name': 'eth0', 'mac': mac } ],  # type one of 'host', 'bridge', 'nat', 'internal',  max 4 interfaces
                           'boot_order': [ 'net', 'hdd' ]  # list of 'net', 'hdd', 'cd', 'usb'
                         }

    if False:  # boot from iso instead
      self.vm_paramaters[ 'disk_list' ].append( { 'name': 'cd', 'file': '/home/peter/Downloads/ubuntu-16.04.2-server-amd64.iso' } )
      self.vm_paramaters[ 'boot_order' ][0] = 'cd'

  def toSubcontractor( self ):
    if self.in_rollback:
      return ( 'create_rollback', self.vm_paramaters )
    else:
      return ( 'create', self.vm_paramaters )

  def fromSubcontractor( self, data ):  # TODO: really if these are missing or false, there is a problem
    if self.in_rollback:
      self.in_rollback = not data.get( 'rollback_done', False )
    else:
      self.uuid = data.get( 'uuid', None )
      self.interface_list = data.get( 'interface_list', [] )  #TODO: seperate the interface_list out to seperate function like vcenter

  def rollback( self ):
    if self.uuid is not None:
      raise ValueError( 'Unable to Rollback after vm has been created' )

    self.in_rollback = True

  def __getstate__( self ):
    return ( self.in_rollback, self.uuid, self.interface_list, self.vm_paramaters )

  def __setstate__( self, state ):
    self.in_rollback = state[0]
    self.uuid = state[1]
    self.interface_list = state[2]
    self.vm_paramaters = state[3]


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


class set_interface_macs():
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.foundation = foundation

  def __call__( self, interface_list ):
    for interface in interface_list:
      try:
        iface = self.foundation.interfaces.get( name=interface[ 'name' ] )
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
