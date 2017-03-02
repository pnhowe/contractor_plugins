from contractor.tscript.runner import Runner, ExternalFunction, ExecutionError, UnrecoverableError, ParamaterError

class ping( ExternalFunction ):
  def __init__( self, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.done = None

  @property
  def ready( self ):
    if self.done is True:
      return True
    else:
      return 'Waiting for Ping'

  @property
  def value( self ):
    return None

  def toSubcontractor( self ):
    return ( 'ping', { 'ip': '127.0.0.1' } )

  def fromSubcontractor( self, data ):
    self.done = True

  def __getstate__( self ):
    return ( self.done, )

  def __setstate__( self, state ):
    self.done = state[0]

## plugin exports

TSCRIPT_NAME = 'iputils'

TSCRIPT_FUNCTIONS = {
                      'ping': ping,
                      #'port_check': portCheck
                    }

TSCRIPT_VALUES = {
                 }
