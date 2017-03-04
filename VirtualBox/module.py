from contractor.tscript.runner import Runner, ExternalFunction, ExecutionError, UnrecoverableError, ParamaterError

class create( ExternalFunction ):
  def __init__( self, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.done = False
    self.in_rollback = False

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
    return None

  def toSubcontractor( self ):
    if self.in_rollback:
      return ( 'create_rollback', { 'name': 'thetesting', 'disk_list': [ { 'name': 'sda', 'size': 2 }, { 'name': 'cd', 'file': '/home/peter/Downloads/ubuntu-16.04.2-server-amd64.iso' } ] } )
    else:
      return ( 'create', { 'name': 'thetesting', 'disk_list': [ { 'name': 'sda', 'size': 2 }, { 'name': 'cd', 'file': '/home/peter/Downloads/ubuntu-16.04.2-server-amd64.iso' } ], 'interface_list': [ 'eth0' ] } )

  def fromSubcontractor( self, data ): # TODO: really if these are missing or false, there is a problem
    if self.in_rollback:
      self.in_rollback = not data.get( 'rollback_done', False )
    else:
      self.done = not data.get( 'done', False )

  def rollback( self ):
    self.in_rollback =  True

  def __getstate__( self ):
    return ( self.done, self.in_rollback )

  def __setstate__( self, state ):
    self.done = state[0]
    self.in_rollback = state[1]


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
    return ( 'destroy', { 'name': 'thetesting' } )

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
