
from contractor.tscript.runner import ExternalFunction, Pause

MAX_POWER_SET_ATTEMPTS = 5


class set_power( ExternalFunction ):  # TODO: need a delay after each power command, at least 5 seconds, last ones could possibly be longer
  def __init__( self, foundation, state, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.ip_address = foundation.amt_ip_address
    self.password = foundation.amt_password
    self.desired_state = state
    self.curent_state = None
    self.counter = 0

  def run( self ):
    if self.desired_state != self.curent_state and self.counter > MAX_POWER_SET_ATTEMPTS:
      raise Pause( 'To Many Attempts to set power to "{0}", curently "{1}"'.format( self.desired_state, self.curent_state ) )

  @property
  def ready( self ):
    if self.desired_state == self.curent_state:
      return True
    else:
      return 'Power curently "{0}" waiting for "{1}", attempt {2} of {3}'.format( self.curent_state, self.desired_state, self.counter, MAX_POWER_SET_ATTEMPTS )

  def rollback( self ):
    self.counter = 0
    self.curent_state = None

  def toSubcontractor( self ):
    self.counter += 1
    if self.desired_state == 'off' and self.counter < 3:  # the first two times, do it nicely, after that, the hard way
      return ( 'set_power', { 'state': 'soft_off', 'ip_address': self.ip_address, 'password': self.password } )
    else:
      return ( 'set_power', { 'state': self.desired_state, 'ip_address': self.ip_address, 'password': self.password } )

  def fromSubcontractor( self, data ):
    self.curent_state = data[ 'state' ]

  def __getstate__( self ):
    return ( self.ip_address, self.password, self.desired_state, self.curent_state, self.counter )

  def __setstate__( self, state ):
    self.ip_address = state[0]
    self.password = state[1]
    self.desired_state = state[2]
    self.curent_state = state[3]
    self.counter = state[4]


class power_state( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.ip_address = foundation.amt_ip_address
    self.password = foundation.amt_password
    self.state = None

  @property
  def ready( self ):
    if self.state is not None:
      return True
    else:
      return 'Retrieving for Power State'

  @property
  def value( self ):
    return self.state

  def toSubcontractor( self ):
    return ( 'power_state', { 'ip_address': self.ip_address, 'password': self.password } )

  def fromSubcontractor( self, data ):
    self.state = data[ 'state' ]

  def __getstate__( self ):
    return ( self.ip_address, self.password, self.state )

  def __setstate__( self, state ):
    self.ip_address = state[0]
    self.password = state[1]
    self.state = state[2]


class wait_for_poweroff( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.ip_address = foundation.amt_ip_address
    self.password = foundation.amt_password
    self.curent_state = None

  @property
  def ready( self ):
    if self.curent_state == 'off':
      return True
    else:
      return 'Waiting for Power off, curently "{0}"'.format( self.curent_state )

  def toSubcontractor( self ):
    return ( 'power_state', { 'ip_address': self.ip_address, 'password': self.password } )

  def fromSubcontractor( self, data ):
    self.curent_state = data[ 'state' ]

  def __getstate__( self ):
    return ( self.ip_address, self.password, self.curent_state )

  def __setstate__( self, state ):
    self.ip_address = state[0]
    self.password = state[1]
    self.curent_state = state[2]


# plugin exports

TSCRIPT_NAME = 'amt'

TSCRIPT_FUNCTIONS = {
                    }

TSCRIPT_VALUES = {
                 }
