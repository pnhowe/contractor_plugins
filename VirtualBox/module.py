from contractor.tscript.runner import Runner, ExternalFunction, ExecutionError, UnrecoverableError, ParamaterError

class create( ExternalFunction ):
  def __init__( self, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.done = None

  @property
  def ready( self ):
    if self.done is True:
      return True
    else:
      return 'Waiting for VM Creation'

  @property
  def value( self ):
    return None

  def to_subcontractor( self ):
    return { 'disk_list': [ 10 ], 'interface_list': [ 'eth0' ] }

  def from_subcontractor( self, data ):
    self.done = True
    return True

  def __getstate__( self ):
    return ( self.done, )

  def __setstate__( self, state ):
    self.done = state[0]


class destroy( ExternalFunction ):
  def __init__( self, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.done = None

  @property
  def ready( self ):
    if self.done is None:
      return 'Not Initilized'

    return self.done

  @property
  def value( self ):
    if self.done is True:
      return 'VM Destroyed'
    else:
      return 'Waiting for VM Destruction'

  def to_subcontractor( self ):
    return True

  def from_subcontractor( self, data ):
    self.done = True
    return True

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
