from contractor.tscript.runner import Runner, ExternalFunction, ExecutionError, UnrecoverableError, ParamaterError

class create( ExternalFunction ):
  def __init__( self, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.done = False
    self.uuid = None
    self.in_rollback = False

    self.disk_list = [ { 'name': 'sda', 'size': 5 }, { 'name': 'cd', 'file': '/home/peter/Downloads/ubuntu-16.04.2-server-amd64.iso' } ] # disk size in G
    self.interface_list = [ 'eth0' ]
    self.memory_size = 1024 # in Meg

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

  def toSubcontractor( self ):
    if self.in_rollback:
      return ( 'create_rollback', { 'name': 'thetesting', 'disk_list': self.disk_list } )
    else:
      return ( 'create', { 'name': 'thetesting', 'memory_size': self.memory_size, 'disk_list': self.disk_list, 'interface_list': self.interface_list } )

  def fromSubcontractor( self, data ): # TODO: really if these are missing or false, there is a problem
    if self.in_rollback:
      self.in_rollback = not data.get( 'rollback_done', False )
    else:
      self.done = data.get( 'done', False )
      self.uuid = data.get( 'uuid', None )

  def rollback( self ):
    self.in_rollback =  True

  def __getstate__( self ):
    return ( self.done, self.in_rollback, self.uuid, self.memory_size, self.disk_list, self.interface_list )

  def __setstate__( self, state ):
    self.done = state[0]
    self.in_rollback = state[1]
    self.uuid = state[2]
    self.memory_size = state[3]
    self.disk_list = state[4]
    self.interface_list = state[5]


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
