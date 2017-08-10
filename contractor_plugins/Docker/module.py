import re
from contractor.tscript.runner import ExternalFunction, ParamaterError

NAME_REGEX = re.compile( '^[a-zA-Z][a-zA-Z0-9\.\-_]*$' )


# exported functions
class create( ExternalFunction ):
  def __init__( self, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.done = False
    self.container_id = None
    self.in_rollback = False
    self.container_paramaters = {}

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
    return { 'container_id': self.container_id }

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

    self.container_paramaters = {
                                 'name': name,
                                 'docker_image': docker_image
                               }

  def toSubcontractor( self ):
    if self.in_rollback:
      return ( 'create_rollback', self.container_paramaters )
    else:
      return ( 'create', self.container_paramaters )

  def fromSubcontractor( self, data ):  # TODO: really if these are missing or false, there is a problem
    if self.in_rollback:
      self.in_rollback = not data.get( 'rollback_done', False )
    else:
      self.done = data.get( 'done', False )
      self.container_id = data.get( 'id', None )

  def rollback( self ):
    self.in_rollback = True

  def __getstate__( self ):
    return ( self.done, self.in_rollback, self.container_id, self.container_paramaters )

  def __setstate__( self, state ):
    self.done = state[0]
    self.in_rollback = state[1]
    self.container_id = state[2]
    self.container_paramaters = state[3]


# other functions used by the virtualbox foundation
class destroy( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.container_id = foundation.container_id
    self.name = foundation.locator
    self.done = None

  @property
  def ready( self ):
    if self.done is True:
      return True
    else:
      return 'Waiting for Container Destruction'

  def toSubcontractor( self ):
    return ( 'destroy', { 'container_id': self.container_id, 'name': self.name } )

  def fromSubcontractor( self, data ):
    self.done = True

  def __getstate__( self ):
    return ( self.done, self.container_id, self.name )

  def __setstate__( self, state ):
    self.done = state[0]
    self.container_id = state[1]
    self.name = state[2]


class start_stop( ExternalFunction ):  # TODO: need a delay after each power command, at least 5 seconds, last ones could possibly be longer
  def __init__( self, foundation, state, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.container_id = foundation.container_id
    self.name = foundation.locator
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
    return ( 'start_stop', { 'state': self.desired_state, 'container_id': self.container_id, 'name': self.name, 'sent': self.sent } )

  def fromSubcontractor( self, data ):
    self.curent_state = data[ 'state' ]
    self.sent = True

  def __getstate__( self ):
    return ( self.container_id, self.desired_state, self.curent_state, self.sent, self.name )

  def __setstate__( self, state ):
    self.container_id = state[0]
    self.desired_state = state[1]
    self.curent_state = state[2]
    self.sent = state[3]
    self.name = state[4]


class state( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.container_id = foundation.container_id
    self.name = foundation.locator
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
    return ( 'state', { 'instance_id': self.instance_id, 'name': self.name } )

  def fromSubcontractor( self, data ):
    self.state = data[ 'state' ]

  def __getstate__( self ):
    return ( self.instance_id, self.state, self.name )

  def __setstate__( self, state ):
    self.instance_id = state[0]
    self.state = state[1]
    self.name = state[2]


# plugin exports

TSCRIPT_NAME = 'docker'

TSCRIPT_FUNCTIONS = {
                      'create': create,
                    }

TSCRIPT_VALUES = {
                 }
