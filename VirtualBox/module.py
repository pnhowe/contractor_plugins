from contractor.tscript.runner import Runner, ExternalFunction, ExecutionError, UnrecoverableError, ParamaterError

class create( ExternalFunction ):
  contractor_module = 'virtualbox'
  contractor_function = 'create'

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
      return 'VM Created'
    else:
      return 'Waiting for VM Creation'

  def from_contractor( self, data ):
    self.done = True
    return True

  def __getstate__( self ):
    return ( self.done, )

  def __setstate__( self, state ):
    self.done = state[0]


class destroy( ExternalFunction ):
  contractor_module = 'virtualbox'
  contractor_function = 'create'

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

  def from_contractor( self, data ):
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
