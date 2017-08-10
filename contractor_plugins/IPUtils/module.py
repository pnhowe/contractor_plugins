from contractor.tscript.runner import ExternalFunction, ParamaterError


class ping( ExternalFunction ):
  def __init__( self, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.target = None
    self.count = None
    self.result = None

  @property
  def ready( self ):
    if self.result is not None:
      return True
    else:
      return 'Waiting for Ping Results'

  @property
  def value( self ):
    return self.result

  def setup( self, parms ):
    try:
      self.target = parms[ 'target' ]
    except KeyError:
      raise ParamaterError( 'target', 'required' )

    if self.target is None:
      raise ParamaterError( 'target', 'is None' )

    try:
      self.count = int( parms.get( 'count', 5 ) )
    except ( ValueError, TypeError ):
      raise ParamaterError( 'count', 'must be an integer' )

  def toSubcontractor( self ):
    return ( 'ping', { 'target': self.target, 'count': self.count } )

  def fromSubcontractor( self, data ):
    self.result = data[ 'result' ]

  def __getstate__( self ):
    return ( self.target, self.count, self.result  )

  def __setstate__( self, state ):
    self.target = state[0]
    self.count = state[1]
    self.result = state[2]


class waitForPort( ExternalFunction ):
  def __init__( self, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.curent_state = None

  @property
  def ready( self ):
    if self.curent_state == 'open':
      return True
    else:
      return 'Port State Curently "{0}"'.format( self.curent_state )

  def setup( self, parms ):
    try:
      self.target = parms[ 'target' ]
    except KeyError:
      raise ParamaterError( 'target', 'required' )

    if self.target is None:
      raise ParamaterError( 'target', 'is None' )

    try:
      self.port = int( parms[ 'port' ] )
    except ( ValueError, TypeError, KeyError ):
      raise ParamaterError( 'count', 'is required and must be an integer' )

  def toSubcontractor( self ):
    return ( 'port_state', { 'target': self.target, 'port': self.port } )

  def fromSubcontractor( self, data ):
    self.curent_state = data[ 'state' ]

  def __getstate__( self ):
    return ( self.target, self.port, self.curent_state  )

  def __setstate__( self, state ):
    self.target = state[0]
    self.port = state[1]
    self.curent_state = state[2]


# plugin exports

TSCRIPT_NAME = 'iputils'

TSCRIPT_FUNCTIONS = {
                      'ping': ping,
                      'wait_for_port': waitForPort
                    }

TSCRIPT_VALUES = {
                 }
