import re
from contractor.tscript.runner import ExternalFunction, ParamaterError

NAME_REGEX = re.compile( '^[a-zA-Z][a-zA-Z0-9\.\-_]*$' )


# exported functions
class create( ExternalFunction ):
  def __init__( self, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.host = None
    self.done = False
    self.docker_id = None
    self.in_rollback = False
    self.docker_paramaters = {}

  @property
  def ready( self ):
    if self.done is True:
      return True
    else:
      if self.in_rollback:
        return 'Waiting for Container Rollback'
      else:
        return 'Waiting for Container Creation'

  @property
  def value( self ):
    return { 'docker_id': self.docker_id }

  def setup( self, parms ):
    try:
      docker_image = self.getScriptValue( 'config', 'docker_image' )
    except ValueError as e:
      raise ParamaterError( '<internal>', 'Unable to get docker_image: {0}'.format( e ) )

    try:
      name = self.getScriptValue( 'foundation', 'locator' )
    except ValueError as e:
      raise ParamaterError( '<internal>', 'Unable to get Foundation Locator: {0}'.format( e ) )

    if not NAME_REGEX.match( name ):
      raise ParamaterError( '<internal>', 'invalid name (ie: Foundation Locator)' )

    port_map = {}
    try:
      port_map = self.getScriptValue( 'config', 'docker_port_map' )
    except ValueError as e:
      pass

    try:
      self.host = self.getScriptValue( 'foundation', 'docker_host' )
    except ValueError as e:
      raise ParamaterError( '<internal>', 'Unable to get Foundation docker_host: {0}'.format( e ) )

    self.docker_paramaters = {
                               'name': name,
                               'docker_image': docker_image,
                               'port_map': port_map
                              }

  def toSubcontractor( self ):
    paramaters = self.docker_paramaters.copy()
    paramaters.update( { 'host': self.host } )

    if self.in_rollback:
      return ( 'create_rollback', paramaters )
    else:
      return ( 'create', paramaters )

  def fromSubcontractor( self, data ):  # TODO: really if these are missing or false, there is a problem
    if self.in_rollback:
      self.in_rollback = not data.get( 'rollback_done', False )
    else:
      self.done = data.get( 'done', False )
      self.docker_id = data.get( 'id', None )

  def rollback( self ):
    self.in_rollback = True

  def __getstate__( self ):
    return ( self.host, self.done, self.in_rollback, self.docker_id, self.docker_paramaters )

  def __setstate__( self, state ):
    self.host = state[0]
    self.done = state[1]
    self.in_rollback = state[2]
    self.docker_id = state[3]
    self.docker_paramaters = state[4]


# other functions used by the virtualbox foundation
class destroy( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.docker_id = foundation.docker_id
    self.name = foundation.locator
    self.host = foundation.host_ip
    self.done = None

  @property
  def ready( self ):
    if self.done is True:
      return True
    else:
      return 'Waiting for Container Destruction'

  def toSubcontractor( self ):
    return ( 'destroy', { 'docker_id': self.docker_id, 'name': self.name, 'host': self.host } )

  def fromSubcontractor( self, data ):
    self.done = True

  def __getstate__( self ):
    return ( self.done, self.docker_id, self.name, self.host )

  def __setstate__( self, state ):
    self.done = state[0]
    self.docker_id = state[1]
    self.name = state[2]
    self.host = state[3]


class start_stop( ExternalFunction ):  # TODO: need a delay after each power command, at least 5 seconds, last ones could possibly be longer
  def __init__( self, foundation, state, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.docker_id = foundation.docker_id
    self.name = foundation.locator
    self.host = foundation.host_ip
    self.desired_state = state
    self.curent_state = None
    self.sent = False

  def run( self ):
    pass

  @property
  def ready( self ):
    if self.desired_state == self.curent_state:
      return True
    else:
      return 'State curently "{0}" waiting for "{1}"'.format( self.curent_state, self.desired_state )

  def rollback( self ):
    self.curent_state = None

  def toSubcontractor( self ):
    return ( 'start_stop', { 'state': self.desired_state, 'docker_id': self.docker_id, 'name': self.name, 'host': self.host, 'sent': self.sent } )

  def fromSubcontractor( self, data ):
    self.curent_state = data[ 'state' ]
    self.sent = True

  def __getstate__( self ):
    return ( self.docker_id, self.name, self.host, self.desired_state, self.curent_state, self.sent )

  def __setstate__( self, state ):
    self.docker_id = state[0]
    self.name = state[1]
    self.host = state[2]
    self.desired_state = state[3]
    self.curent_state = state[4]
    self.sent = state[5]


class state( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.docker_id = foundation.docker_id
    self.name = foundation.locator
    self.host = foundation.host_ip
    self.state = None

  @property
  def ready( self ):
    if self.state is not None:
      return True
    else:
      return 'Retrieving State'

  @property
  def value( self ):
    return self.state

  def toSubcontractor( self ):
    return ( 'state', { 'docker_id': self.docker_id, 'name': self.name, 'host': self.host } )

  def fromSubcontractor( self, data ):
    self.state = data[ 'state' ]

  def __getstate__( self ):
    return ( self.docker_id, self.state, self.name, self.host )

  def __setstate__( self, state ):
    self.docker_id = state[0]
    self.state = state[1]
    self.name = state[2]
    self.host = state[3]


# plugin exports

TSCRIPT_NAME = 'docker'

TSCRIPT_FUNCTIONS = {
                      'create': create,
                    }

TSCRIPT_VALUES = {
                 }
