from contractor.tscript.runner import Runner, ExternalFunction, ExecutionError, UnrecoverableError, ParamaterError

class create( ExternalFunction ):
  def __init__( self, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.done = False
    self.created = None

  @property
  def ready( self ):
    if self.done is True:
      return True
    else:
      return 'Waiting for VM Creation'

  @property
  def value( self ):
    return self.created

  def toSubcontractor( self ):
    return ( 'create', { 'disk_list': [ 10 ], 'interface_list': [ 'eth0' ] } )

  def fromSubcontractor( self, data ):
    self.done = True
    self.created = data

  def __getstate__( self ):
    return ( self.done, self.created )

  def __setstate__( self, state ):
    self.done = state[0]
    self.created = state[1]


class destroy( ExternalFunction ):
  def __init__( self, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.done = None

  @property
  def ready( self ):
    if self.done is True:
      return True
    else:
      return 'Waiting for VM Destruction'

  @property
  def value( self ):
    return

  def toSubcontractor( self ):
    return ( 'destroy', None )

  def fromSubcontractor( self, data ):
    self.done = True

  def __getstate__( self ):
    return ( self.done, )

  def __setstate__( self, state ):
    self.done = state[0]

## plugin exports

TSCRIPT_NAME = 'virtualbox'

TSCRIPT_FUNCTIONS = {
                      'create': create,
                      'destroy': destroy
                    }

TSCRIPT_VALUES = {
                 }
