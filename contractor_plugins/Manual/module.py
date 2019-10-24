from contractor.tscript.runner import ExternalFunction, Pause


class set_power( ExternalFunction ):
  def __init__( self, foundation, state, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.locator = foundation.locator
    self.state = state
    self.complete = False

  def run( self ):
    self.compete = True
    raise Pause( 'Set Power of "{0}" to "{1}" then resume'.format( self.locator, self.state ) )

  @property
  def done( self ):
    return self.complete is True

  def __getstate__( self ):
    return ( self.locator, self.state, self.complete )

  def __setstate__( self, state ):
    self.locator = state[0]
    self.state = state[1]
    self.complete = state[2]


class power_state( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )

  @property
  def done( self ):
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
    self.compete = False

  def run( self ):
    self.compete = True
    raise Pause( 'Wait for "{0}" to Power Off, then Resume'.format( self.locator ) )

  @property
  def done( self ):
    return self.compete is True

  def __getstate__( self ):
    return ( self.locator, self.compete )

  def __setstate__( self, state ):
    self.locator = state[0]
    self.compete = state[1]
