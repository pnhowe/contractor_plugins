import random
import datetime

from contractor.tscript.runner import ExecutionError, UnrecoverableError, ExternalFunction, Pause


def delay_amount( amount, variance ):
  if variance == 0:
    return amount
  
  return int( random.triangular( amount - variance, amount + variance, amount ) )



class PowerOperation( ExternalFunction ):
  def __init__( self, foundation, operation,*args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.test_delay_variance = foundation.test_delay_variance
    self.test_fail_likelihood = foundation.test_fail_likelihood
    self.operation = operation
    self.end_at = None

  def run( self ):
    if random.randrange( 0, 1000 ) <= self.test_fail_likelihood:
      if random.randrange( 1, 100 ) <= self.test_fail_likelihood / 10:  # make sure we don't UncrevoerableError if the likelihood is less than 10
        raise UnrecoverableError( 'Testing really broke' )
      else:
        raise ExecutionError( 'Just Testing' )

  @property
  def done( self ):
    return datetime.datetime.utcnow() >= self.end_at

  @property
  def value( self ):
    return 'unknown'

  @property
  def message( self ):
    return 'Running "{0}" for {1} more seconds'.format( self.operation, ( self.end_at - datetime.datetime.utcnow() ) )

  def setup( self, parms ):
    base_delay = 5  # for 'power_off' and 'power_state'
    if self.operation == 'wait_for_poweroff':
      base_delay = 30
    elif self.operation == 'power_on':
      base_delay = 15

    self.end_at = datetime.datetime.utcnow() + datetime.timedelta( seconds=delay_amount( base_delay, self.test_delay_variance ) )

  def __getstate__( self ):
    return ( self.test_delay_variance, self.test_fail_likelihood, self.operation, self.end_at )

  def __setstate__( self, state ):
    self.test_delay_variance = state[0]
    self.test_fail_likelihood = state[1]
    self.operation = state[2]
    self.end_at = state[3]



