from contractor.tscript.runner import ExternalFunction, Pause


class set_power( ExternalFunction ):
  def __init__( self, foundation, state, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.locator = foundation.locator
    self.state = state
    self.done = False

  def run( self ):
    self.done = True
    raise Pause( 'Set Power of "{0}" to "{1}" then resume'.format( self.locator, self.state ) )

  @property
  def ready( self ):
    return self.done

  def __getstate__( self ):
    return ( self.locator, self.state, self.done )

  def __setstate__( self, state ):
    self.locator = state[0]
    self.state = state[1]
    self.done = state[2]


class power_state( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )

  @property
  def ready( self ):
    return True

  @property
  def value( self ):
    return 'unknown'

  def __getstate__( self ):
    return []

  def __setstate__( self, state ):
    pass


class wait_for_poweroff( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.locator = foundation.locator
    self.done = False

  def run( self ):
    self.done = True
    raise Pause( 'Wait for "{0}" to Power Off, then Resume'.format( self.locator ) )

  @property
  def ready( self ):
    return self.done

  def __getstate__( self ):
    return ( self.locator, self.done )

  def __setstate__( self, state ):
    self.locator = state[0]
    self.done = state[1]
