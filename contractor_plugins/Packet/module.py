from django.core.exceptions import ObjectDoesNotExist

from contractor.tscript.runner import ExternalFunction, ParamaterError, Pause
from contractor.Utilities.models import Address

MAX_POWER_SET_ATTEMPTS = 5


# exported functions
class create( ExternalFunction ):
  def __init__( self, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.uuid = None
    self.connection_paramaters = {}
    self.device_paramaters = {}

  @property
  def done( self ):
    return self.uuid is not None

  @property
  def message( self ):
    if self.uuid is not None:
      return 'Device Created'
    else:
      return 'Waiting for Device Creation'

  @property
  def value( self ):
    return self.uuid

  def setup( self, parms ):
    try:
      foundation = self.getScriptValue( 'foundation', 'foundation' )
    except ValueError as e:
      raise ParamaterError( '<internal>', 'Unable to get Foundation: {0}'.format( e ) )

    try:
      packet_complex = self.getScriptValue( 'foundation', 'packet_complex' )
    except ValueError as e:
      raise ParamaterError( '<internal>', 'Unable to get Foundation packet_complex: {0}'.format( e ) )

    self.connection_paramaters = packet_complex.connection_paramaters

    self.device_paramaters = {}

    self.device_paramaters[ 'facility' ] = packet_complex.packet_facility
    self.device_paramaters[ 'project' ] = packet_complex.packet_project

    try:
      self.device_paramaters[ 'description' ] = self.getScriptValue( 'foundation', 'locator' )
    except KeyError as e:
      raise ParamaterError( '<internal>', 'Unable to get Foundation Locator: {0}'.format( e ) )

    try:
      device_spec = parms[ 'device_spec' ]
    except KeyError:
      raise ParamaterError( 'device_spec', 'required' )

    if not isinstance( device_spec, dict ):
      raise ParamaterError( 'device_spec', 'must be a dict' )

    self.device_paramaters[ 'hostname' ] = device_spec[ 'hostname' ]
    self.device_paramaters[ 'plan' ] = device_spec[ 'plan' ]
    self.device_paramaters[ 'operating_system' ] = device_spec[ 'os' ]
    self.device_paramaters[ 'interface_map' ] = device_spec[ 'interface_map' ]

  def toSubcontractor( self ):
    return ( 'create', { 'connection': self.connection_paramaters, 'device': self.device_paramaters } )

  def fromSubcontractor( self, data ):  # TODO: really if these are missing or false, there is a problem
    self.uuid = data.get( 'uuid', None )

  def __getstate__( self ):
    return ( self.connection_paramaters, self.device_paramaters, self.uuid )

  def __setstate__( self, state ):
    self.connection_paramaters = state[0]
    self.device_paramaters = state[1]
    self.uuid = state[2]


# other functions used by the packet foundation
class destroy( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.uuid = foundation.packet_uuid
    self.description = foundation.locator
    self.connection_paramaters = foundation.packet_complex.connection_paramaters
    self.complete = None

  @property
  def done( self ):
    return self.complete is True

  @property
  def message( self ):
    if self.complete is True:
      return 'Device Destroyed'
    else:
      return 'Waiting for Device Destruction'

  def toSubcontractor( self ):
    return ( 'destroy', { 'connection': self.connection_paramaters, 'uuid': self.uuid, 'description': self.description } )

  def fromSubcontractor( self, data ):
    self.complete = True

  def __getstate__( self ):
    return ( self.connection_paramaters, self.uuid, self.description, self.complete )

  def __setstate__( self, state ):
    self.connection_paramaters = state[0]
    self.uuid = state[1]
    self.description = state[2]
    self.complete = state[3]


class set_power( ExternalFunction ):  # TODO: need a delay after each power command, at least 5 seconds, last ones could possibly be longer
  def __init__( self, foundation, state, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.uuid = foundation.packet_uuid
    self.description = foundation.locator
    self.connection_paramaters = foundation.packet_complex.connection_paramaters
    self.desired_state = state
    self.curent_state = None
    self.counter = 0

  def run( self ):
    if self.desired_state != self.curent_state and self.counter > MAX_POWER_SET_ATTEMPTS:
      raise Pause( 'To Many Attempts to set power to "{0}", curently "{1}"'.format( self.desired_state, self.curent_state ) )

  @property
  def done( self ):
    return self.desired_state == self.curent_state

  @property
  def message( self ):
    return 'Power curently "{0}" waiting for "{1}", attempt {2} of {3}'.format( self.curent_state, self.desired_state, self.counter, MAX_POWER_SET_ATTEMPTS )

  def rollback( self ):
    self.counter = 0
    self.curent_state = None

  def toSubcontractor( self ):
    self.counter += 1
    if self.desired_state == 'off' and self.counter < 3:  # the first two times, do it nicely, after that, the hard way
      return ( 'set_power', { 'state': 'soft_off', 'connection': self.connection_paramaters, 'uuid': self.uuid, 'description': self.description } )
    else:
      return ( 'set_power', { 'state': self.desired_state, 'connection': self.connection_paramaters, 'uuid': self.uuid, 'description': self.description } )

  def fromSubcontractor( self, data ):
    self.curent_state = data[ 'state' ]

  def __getstate__( self ):
    return ( self.connection_paramaters, self.uuid, self.description, self.desired_state, self.curent_state, self.counter )

  def __setstate__( self, state ):
    self.connection_paramaters = state[0]
    self.uuid = state[1]
    self.description = state[2]
    self.desired_state = state[3]
    self.curent_state = state[4]
    self.counter = state[5]


class power_state( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.uuid = foundation.packet_uuid
    self.description = foundation.locator
    self.connection_paramaters = foundation.packet_complex.connection_paramaters
    self.state = None

  @property
  def done( self ):
    return self.state is not None

  @property
  def message( self ):
    if self.state is None:
        return 'Retrieving for Power State'

    return 'Power State at "{0}"'.format( self.state )

  @property
  def value( self ):
    return self.state

  def toSubcontractor( self ):
    return ( 'power_state', { 'connection': self.connection_paramaters, 'uuid': self.uuid, 'description': self.description } )

  def fromSubcontractor( self, data ):
    self.state = data[ 'state' ]

  def __getstate__( self ):
    return ( self.connection_paramaters, self.uuid, self.description, self.state )

  def __setstate__( self, state ):
    self.connection_paramaters = state[0]
    self.uuid = state[1]
    self.description = state[2]
    self.state = state[3]


class wait_for_poweroff( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.uuid = foundation.packet_uuid
    self.description = foundation.locator
    self.connection_paramaters = foundation.packet_complex.connection_paramaters
    self.current_state = None

  @property
  def done( self ):
    return self.current_state == 'off'

  @property
  def message( self ):
    return 'Waiting for Power off, curently "{0}"'.format( self.current_state )

  def toSubcontractor( self ):
    return ( 'power_state', { 'connection': self.connection_paramaters, 'uuid': self.uuid, 'description': self.description } )

  def fromSubcontractor( self, data ):
    self.current_state = data[ 'state' ]

  def __getstate__( self ):
    return ( self.connection_paramaters, self.uuid, self.description, self.current_state )

  def __setstate__( self, state ):
    self.connection_paramaters = state[0]
    self.uuid = state[1]
    self.description = state[2]
    self.current_state = state[3]


class device_state( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.uuid = foundation.packet_uuid
    self.description = foundation.locator
    self.connection_paramaters = foundation.packet_complex.connection_paramaters
    self.state = None

  @property
  def done( self ):
    return self.state is not None

  @property
  def message( self ):
    if self.state is None:
        return 'Retrieving for Device State'

    return 'Device State at "{0}"'.format( self.state )

  @property
  def value( self ):
    return self.state

  def toSubcontractor( self ):
    return ( 'device_state', { 'connection': self.connection_paramaters, 'uuid': self.uuid, 'description': self.description } )

  def fromSubcontractor( self, data ):
    self.state = data[ 'state' ]

  def __getstate__( self ):
    return ( self.connection_paramaters, self.uuid, self.description, self.state )

  def __setstate__( self, state ):
    self.connection_paramaters = state[0]
    self.uuid = state[1]
    self.description = state[2]
    self.state = state[3]


class sync_networking_info( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.foundation = foundation
    self.uuid = foundation.packet_uuid
    self.description = foundation.locator
    self.connection_paramaters = foundation.packet_complex.connection_paramaters
    self.interface_map = None
    self._done = False

  @property
  def done( self ):
    return self._done

  @property
  def message( self ):
    if self._done:
      return 'Values Applied'
    elif self.interface_map is not None:
      return 'Waiting to Apply'
    else:
      return 'Waiting for Interface Map'

  def run( self ):
    if self._done:
      return

    if self.interface_map is None:
      return

    structure = self.foundation.structure

    for uuid, detail in self.interface_map.items():
      iface = None
      try:
        iface = self.foundation.networkinterface_set.get( physical_location=detail[ 'name' ] )
      except ObjectDoesNotExist:
        continue

      iface = iface.subclass
      iface.link_name = uuid
      if detail[ 'mac' ]:
        iface.mac = detail[ 'mac' ]
      iface.full_clean()
      iface.save()

      if iface.network.name != 'public':  # we only care about the auto-assigned ips on the public network
        continue

      current_ip_lookup_map = dict( [ ( i.ip_address, i ) for i in structure.address_set.filter( interface_name=iface.name ) ] )
      current_ip_addresses = set( current_ip_lookup_map.keys() )
      target_ip_addresses = set( [ i[ 'address' ] for i in detail[ 'ip_addresses' ] ] )

      for ip_address in current_ip_addresses - target_ip_addresses:
        current_ip_lookup_map[ ip_address ].delete()

      for ip_address in target_ip_addresses - current_ip_addresses:
        address = Address.fromIPAddress( structure.site, ip_address )
        if address is None:
          raise Exception( 'Address block for address "{0}" not found in site "{1}"'.format( ip_address, structure.site ) )

        address.networked = structure
        address.interface_name = iface.name
        address.full_clean()
        address.save()

      self._done = True

  def toSubcontractor( self ):
    if self.interface_map is not None:
      return None

    return ( 'get_interface_map', { 'connection': self.connection_paramaters, 'uuid': self.uuid, 'description': self.description } )

  def fromSubcontractor( self, data ):
    self.interface_map = data[ 'interface_map' ]

  def __getstate__( self ):
    return ( self.foundation, self.connection_paramaters, self.uuid, self.description, self.interface_map, self._done )

  def __setstate__( self, state ):
    self.foundation = state[0]
    self.connection_paramaters = state[1]
    self.uuid = state[2]
    self.description = state[3]
    self.interface_map = state[4]
    self._done = state[5]


# plugin exports

TSCRIPT_NAME = 'packet'

TSCRIPT_FUNCTIONS = {
                      'create': create,
                    }

TSCRIPT_VALUES = {
                 }
