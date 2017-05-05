import re
from contractor.tscript.runner import ExternalFunction, ParamaterError, Pause

NAME_REGEX = re.compile( '^[a-zA-Z][a-zA-Z0-9\.\-_]*$' )
MAX_POWER_SET_ATTEMPTS = 5


# exported functions
class create( ExternalFunction ):
  def __init__( self, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.done = False
    self.uuid = None
    self.in_rollback = False

    subcontractor_id = 1
    self.vm_paramaters = {
                           'name': None,
                           'cpu_count': 1,
                           'memory_size': 512,  # in Meg
                           'disk_list': [ { 'name': 'sda', 'size': 5 } ],  # disk size in G
                           'interface_list': [ { 'type': 'host', 'name': 'vboxnet0', 'mac': '08:00:27:' + '00:00:{0:02x}'.format( ( 4 * subcontractor_id ) + 1 ) } ],  # type one of 'host', 'bridge', 'nat', 'internal',  name is name of network to attach to max 4 interfaces
                           'boot_order': [ 'net', 'hdd' ]  # list of 'net', 'hdd', 'cd', 'usb'
                         }


  @property
  def ready( self ):
    if self.done is True:
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
      self.vm_paramaters[ 'name' ] = parms[ 'name' ]
    except KeyError:
      raise ParamaterError( 'name', 'required' )

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
    if self.vm_paramaters[ 'memory_size' ] > 1048510 or self.vm_paramaters[ 'memory_size' ] < 512:
      raise ParamaterError( 'memory_size', 'must be from 512 to 1048510' )

  def toSubcontractor( self ):
    if self.in_rollback:
      return ( 'create_rollback', self.vm_paramaters )
    else:
      return ( 'create', self.vm_paramaters )

  def fromSubcontractor( self, data ):  # TODO: really if these are missing or false, there is a problem
    if self.in_rollback:
      self.in_rollback = not data.get( 'rollback_done', False )
    else:
      self.done = data.get( 'done', False )
      self.uuid = data.get( 'uuid', None )

  def rollback( self ):
    self.in_rollback = True

  def __getstate__( self ):
    return ( self.done, self.in_rollback, self.uuid, self.vm_paramaters )

  def __setstate__( self, state ):
    self.done = state[0]
    self.in_rollback = state[1]
    self.uuid = state[2]
    self.vm_paramaters = state[3]


# other functions used by the virtualbox foundation
class destroy( ExternalFunction ):
  def __init__( self, uuid, name, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.uuid = uuid
    self.name = name
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
    return ( self.done, self.uuid, self.name )

  def __setstate__( self, state ):
    self.done = state[0]
    self.uuid = state[1]
    self.name = state[2]


class set_power( ExternalFunction ):  # TODO: need a delay after each power command, at least 5 seconds, last ones could possibly be longer
  def __init__( self, uuid, state, name, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.uuid = uuid
    self.name = name
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
    return ( self.uuid, self.desired_state, self.curent_state, self.counter, self.name )

  def __setstate__( self, state ):
    self.uuid = state[0]
    self.desired_state = state[1]
    self.curent_state = state[2]
    self.counter = state[3]
    self.name = state[4]


class power_state( ExternalFunction ):
  def __init__( self, uuid, name, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.uuid = uuid
    self.name = name
    self.state = None

  @property
  def ready( self ):
    if self.state is not None:
      return True
    else:
      return 'Waiting for Power State'

  @property
  def value( self ):
    self.state

  def toSubcontractor( self ):
    return ( 'power_state', { 'uuid': self.uuid, 'name': self.name } )

  def fromSubcontractor( self, data ):
    self.state = data[ 'state' ]

  def __getstate__( self ):
    return ( self.uuid, self.state, self.name )

  def __setstate__( self, state ):
    self.uuid = state[0]
    self.state = state[1]
    self.name = state[2]


class wait_for_poweroff( ExternalFunction ):
  def __init__( self, uuid, name, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.uuid = uuid
    self.name = name
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
    self.current_State = data[ 'state' ]

  def __getstate__( self ):
    return ( self.uuid, self.current_state, self.name )

  def __setstate__( self, state ):
    self.uuid = state[0]
    self.current_state = state[1]
    self.name = state[2]


# plugin exports

TSCRIPT_NAME = 'vcenter'

TSCRIPT_FUNCTIONS = {
                      'create': create,
                    }

TSCRIPT_VALUES = {
                 }
