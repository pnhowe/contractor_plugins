import re

from django.core.exceptions import ObjectDoesNotExist, ValidationError

from contractor.tscript.runner import ExternalFunction, ParamaterError, Pause

NAME_REGEX = re.compile( '^[a-zA-Z][a-zA-Z0-9\.\-_]*$' )
MAX_POWER_SET_ATTEMPTS = 5

INTERFACE_NAME_LIST = [ 'eth0' ]


# exported functions
class create( ExternalFunction ):
  def __init__( self, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.uuid = None
    self.in_rollback = False
    self.connection_paramaters = {}

  @property
  def ready( self ):
    if self.uuid is not None:
      return True
    else:
      if self.in_rollback:
        return 'Waiting for VM Rollback'
      else:
        return 'Waiting for VM Creation'

  @property
  def value( self ):
    return self.uuid

  def setup( self, parms ):
    try:
      vcenter_host = self.getScriptValue( 'foundation', 'vcenter_host' )
    except ValueError as e:
      raise ParamaterError( '<internal>', 'Unable to get Foundation vcenter_host: {0}'.format( e ) )

    self.connection_paramaters = vcenter_host.connection_paramaters

    self.vm_paramaters = {}

    self.vm_paramaters[ 'datacenter' ] = vcenter_host.vcenter_datacenter
    self.vm_paramaters[ 'cluster' ] = vcenter_host.vcenter_cluster

    try:
      self.vm_paramaters[ 'name' ] = self.getScriptValue( 'foundation', 'locator' )
    except KeyError as e:
      raise ParamaterError( '<internal>', 'Unable to get Foundation Locator: {0}'.format( e ) )

    for key in ( 'host', 'datastore' ):
      try:
        self.vm_paramaters[ key ] = parms[ key ]
      except KeyError:
        raise ParamaterError( key, 'required' )

    try:
      vm_spec = parms[ 'vm_spec' ]
    except KeyError:
      raise ParamaterError( 'vm_spec', 'required' )

    if not isinstance( vm_spec, dict ):
      raise ParamaterError( 'vm_spec', 'must be a dict' )

    # for now we will cary on CPU, Memeory, for OVAs evntually something will pull this info from the OVA
    for key in ( 'cpu_count', 'memory_size' ):
      try:
        self.vm_paramaters[ key ] = int( vm_spec[ key ] )
      except KeyError:
        raise ParamaterError( 'vm_spec.{0}'.format( key ), 'required' )
      except ( ValueError, TypeError ):
        raise ParamaterError( 'vm_spec.{0}'.format( key ), 'must be an integer' )

    if self.vm_paramaters[ 'cpu_count' ] > 64 or self.vm_paramaters[ 'cpu_count' ] < 1:
      raise ParamaterError( 'cpu_count', 'must be from 1 to 64')
    if self.vm_paramaters[ 'memory_size' ] > 1048510 or self.vm_paramaters[ 'memory_size' ] < 512:  # in MB
      raise ParamaterError( 'memory_size', 'must be from 512 to 1048510' )

    # is this an OVA, if so, short cut, just deploy it
    ova = vm_spec.get( 'ova', None )
    if ova is not None:
      self.vm_paramaters[ 'ova' ] = ova

      interface_list = []
      for name in INTERFACE_NAME_LIST:
        interface_list.append( { 'name': name, 'network': 'VM Network' } )

      self.vm_paramaters[ 'interface_list' ] = interface_list
      return

    # not OVA specify all the things
    try:
      interface_type = vm_spec[ 'vcenter_network_interface_class' ]
    except KeyError:
      interface_type = 'E1000'

    interface_list = []
    counter = 0
    for name in INTERFACE_NAME_LIST:
      interface_list.append( { 'name': name, 'network': 'VM Network', 'type': interface_type } )
      counter += 1

    self.vm_paramaters[ 'disk_list' ] = [ { 'size': 10, 'name': 'sda' } ]  # disk size in G, see _createDisk in subcontractor_plugsin/vcenter/lib.py
    self.vm_paramaters[ 'interface_list' ] = interface_list
    self.vm_paramaters[ 'boot_order' ] = [ 'net', 'hdd' ]  # list of 'net', 'hdd', 'cd', 'usb'

    if False:  # boot from iso instead
      self.vm_paramaters[ 'disk_list' ].append( { 'name': 'cd', 'file': '/home/peter/Downloads/ubuntu-16.04.2-server-amd64.iso' } )
      self.vm_paramaters[ 'boot_order' ] = [ 'cd', 'net', 'hdd' ]

    for key in ( 'vcenter_guest_id', 'vcenter_virtual_exec_usage', 'vcenter_virtual_mmu_usage' ):
      try:
        self.vm_paramaters[ key[ 8: ] ] = vm_spec[ key ]
      except KeyError:
        pass

    if not NAME_REGEX.match( self.vm_paramaters[ 'name' ] ):
      raise ParamaterError( 'invalid name' )

  def toSubcontractor( self ):
    if self.in_rollback:
      return ( 'create_rollback', { 'connection': self.connection_paramaters, 'vm': self.vm_paramaters } )
    else:
      return ( 'create', { 'connection': self.connection_paramaters, 'vm': self.vm_paramaters } )

  def fromSubcontractor( self, data ):  # TODO: really if these are missing or false, there is a problem
    if self.in_rollback:
      self.in_rollback = not data.get( 'rollback_done', False )
    else:
      self.uuid = data.get( 'uuid', None )

  def rollback( self ):
    if self.uuid is not None:
      raise ValueError( 'Unable to Rollback after vm has been created' )

    self.in_rollback = True

  def __getstate__( self ):
    return ( self.connection_paramaters, self.vm_paramaters, self.in_rollback, self.uuid )

  def __setstate__( self, state ):
    self.connection_paramaters = state[0]
    self.vm_paramaters = state[1]
    self.in_rollback = state[2]
    self.uuid = state[3]


class host_list( ExternalFunction ):
  def __init__( self, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.result = None
    self.connection_paramaters = {}
    self.datacenter = None
    self.cluster = None
    self.min_memory = None
    self.cpu_scaler = None
    self.memory_scaler = None

  @property
  def ready( self ):
    if self.result is not None:
      return True
    else:
      return 'Waiting for Host List'

  @property
  def value( self ):
    return self.result

  def setup( self, parms ):
    try:
      vcenter_host = self.getScriptValue( 'foundation', 'vcenter_host' )
    except ValueError as e:
      raise ParamaterError( '<internal>', 'Unable to get Foundation vcenter_host: {0}'.format( e ) )

    self.connection_paramaters = vcenter_host.connection_paramaters
    self.datacenter = vcenter_host.vcenter_datacenter
    self.cluster = vcenter_host.vcenter_cluster

    for key in ( 'min_memory', 'min_cpu' ):  # memory in MB
      try:
        setattr( self, key, int( parms[ key ] ) )
      except KeyError:
        raise ParamaterError( key, 'required' )
      except ( ValueError, TypeError ):
        raise ParamaterError( key, 'must be an integer' )

    for key in ( 'cpu_scaler', 'memory_scaler' ):
      try:
        setattr( self, key, int( parms.get( key, 1 ) ) )
      except ( ValueError, TypeError ):
        raise ParamaterError( key, 'must be an integer' )

  def toSubcontractor( self ):
    return ( 'host_list', { 'connection': self.connection_paramaters, 'datacenter': self.datacenter, 'cluster': self.cluster, 'min_memory': self.min_memory, 'min_cpu': self.min_cpu, 'cpu_scaler': self.cpu_scaler, 'memory_scaler': self.memory_scaler } )

  def fromSubcontractor( self, data ):
    self.result = data[ 'host_list' ]

  def __getstate__( self ):
    return ( self.connection_paramaters, self.datacenter, self.cluster, self.min_memory, self.min_cpu, self.cpu_scaler, self.memory_scaler, self.result )

  def __setstate__( self, state ):
    self.connection_paramaters = state[0]
    self.datacenter = state[1]
    self.cluster = state[2]
    self.min_memory = state[3]
    self.min_cpu = state[4]
    self.cpu_scaler = state[5]
    self.memory_scaler = state[6]
    self.result = state[7]


class create_datastore( ExternalFunction ):
  def __init__( self, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.done = False
    self.connection_paramaters = {}
    self.datacenter = None
    self.datastore_list = None

  @property
  def ready( self ):
    if self.done is True:
      return True
    else:
      return 'Waiting for Datastore Creation'

  def setup( self, parms ):
    try:
      vcenter_host = self.getScriptValue( 'foundation', 'vcenter_host' )
    except ValueError as e:
      raise ParamaterError( '<internal>', 'Unable to get Foundation vcenter_host: {0}'.format( e ) )

    self.connection_paramaters = vcenter_host.connection_paramaters
    self.datacenter = vcenter_host.vcenter_datacenter

    try:
      self.host = self.getScriptValue( 'config', 'vcenter_hostname' )
    except ValueError as e:
      raise ParamaterError( '<internal>', 'Unable to get Foundation vcenter_hostname: {0}'.format( e ) )

    try:
      self.name = parms[ 'name' ]
    except AttributeError as e:
      raise ParamaterError( 'name', 'required' )

    try:
      self.model = parms[ 'model' ]
    except AttributeError as e:
      raise ParamaterError( 'model', 'required' )

  def toSubcontractor( self ):
    return ( 'create_datastore', { 'connection': self.connection_paramaters, 'datacenter': self.datacenter, 'host': self.host, 'name': self.name, 'model': self.model } )

  def fromSubcontractor( self, data ):
    self.done = data.get( 'done', False )

  def __getstate__( self ):
    return ( self.connection_paramaters, self.datacenter, self.host, self.name, self.model, self.done )

  def __setstate__( self, state ):
    self.connection_paramaters = state[0]
    self.datacenter = state[1]
    self.host = state[2]
    self.name = state[3]
    self.model = state[4]
    self.done = state[5]


class datastore_list( ExternalFunction ):
  def __init__( self, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.result = None
    self.connection_paramaters = {}
    self.datacenter = None
    self.cluster = None
    self.host = None
    self.min_free_space = None
    self.name_regex = None

  @property
  def ready( self ):
    if self.result is not None:
      return True
    else:
      return 'Waiting for Datastore List'

  @property
  def value( self ):
    return self.result

  def setup( self, parms ):
    try:
      vcenter_host = self.getScriptValue( 'foundation', 'vcenter_host' )
    except ValueError as e:
      raise ParamaterError( '<internal>', 'Unable to get Foundation vcenter_host: {0}'.format( e ) )

    self.connection_paramaters = vcenter_host.connection_paramaters
    self.datacenter = vcenter_host.vcenter_datacenter
    self.cluster = vcenter_host.vcenter_cluster

    try:
      self.host = parms.get( 'host' )
    except AttributeError as e:
      raise ParamaterError( 'host', 'Required' )

    try:
      self.min_free_space = int( parms.get( 'min_free_space' ) )  # in GB
    except KeyError:
      raise ParamaterError( 'min_free_space', 'required' )
    except ( ValueError, TypeError ):
      raise ParamaterError( 'min_free_space', 'must be an integer' )

    self.name_regex = parms.get( 'name_regex', None )

  def toSubcontractor( self ):
    return ( 'datastore_list', { 'connection': self.connection_paramaters, 'datacenter': self.datacenter, 'cluster': self.cluster, 'host': self.host, 'min_free_space': self.min_free_space, 'name_regex': self.name_regex } )

  def fromSubcontractor( self, data ):
    self.result = data[ 'datastore_list' ]

  def __getstate__( self ):
    return ( self.connection_paramaters, self.datacenter, self.cluster, self.host, self.name_regex, self.min_free_space, self.result )

  def __setstate__( self, state ):
    self.connection_paramaters = state[0]
    self.datacenter = state[1]
    self.cluster = state[2]
    self.host = state[3]
    self.name_regex = state[4]
    self.min_free_space = state[5]
    self.result = state[6]


# other functions used by the virtualbox foundation
class destroy( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.uuid = foundation.vcenter_uuid
    self.name = foundation.locator
    self.connection_paramaters = foundation.vcenter_host.connection_paramaters
    self.done = None

  @property
  def ready( self ):
    if self.done is True:
      return True
    else:
      return 'Waiting for VM Destruction'

  def toSubcontractor( self ):
    return ( 'destroy', { 'connection': self.connection_paramaters, 'uuid': self.uuid, 'name': self.name } )

  def fromSubcontractor( self, data ):
    self.done = True

  def __getstate__( self ):
    return ( self.connection_paramaters, self.uuid, self.name, self.done )

  def __setstate__( self, state ):
    self.connection_paramaters = state[0]
    self.uuid = state[1]
    self.name = state[2]
    self.done = state[3]


class set_power( ExternalFunction ):  # TODO: need a delay after each power command, at least 5 seconds, last ones could possibly be longer
  def __init__( self, foundation, state, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.uuid = foundation.vcenter_uuid
    self.name = foundation.locator
    self.connection_paramaters = foundation.vcenter_host.connection_paramaters
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
      return ( 'set_power', { 'state': 'soft_off', 'connection': self.connection_paramaters, 'uuid': self.uuid, 'name': self.name } )
    else:
      return ( 'set_power', { 'state': self.desired_state, 'connection': self.connection_paramaters, 'uuid': self.uuid, 'name': self.name } )

  def fromSubcontractor( self, data ):
    self.curent_state = data[ 'state' ]

  def __getstate__( self ):
    return ( self.connection_paramaters, self.uuid, self.name, self.desired_state, self.curent_state, self.counter )

  def __setstate__( self, state ):
    self.connection_paramaters = state[0]
    self.uuid = state[1]
    self.name = state[2]
    self.desired_state = state[3]
    self.curent_state = state[4]
    self.counter = state[5]


class power_state( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.uuid = foundation.vcenter_uuid
    self.name = foundation.locator
    self.connection_paramaters = foundation.vcenter_host.connection_paramaters
    self.state = None

  @property
  def ready( self ):
    if self.state is not None:
      return True
    else:
      return 'Waiting for Power State'

  @property
  def value( self ):
    return self.state

  def toSubcontractor( self ):
    return ( 'power_state', { 'connection': self.connection_paramaters, 'uuid': self.uuid, 'name': self.name } )

  def fromSubcontractor( self, data ):
    self.state = data[ 'state' ]

  def __getstate__( self ):
    return ( self.connection_paramaters, self.uuid, self.name, self.state )

  def __setstate__( self, state ):
    self.connection_paramaters = state[0]
    self.uuid = state[1]
    self.name = state[3]
    self.state = state[2]


class wait_for_poweroff( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.uuid = foundation.vcenter_uuid
    self.name = foundation.locator
    self.connection_paramaters = foundation.vcenter_host.connection_paramaters
    self.current_state = None

  @property
  def ready( self ):
    if self.current_state == 'off':
      return True
    else:
      return 'Waiting for Power off, curently "{0}"'.format( self.current_state )

  def toSubcontractor( self ):
    return ( 'power_state', { 'connection': self.connection_paramaters, 'uuid': self.uuid, 'name': self.name } )

  def fromSubcontractor( self, data ):
    self.current_state = data[ 'state' ]

  def __getstate__( self ):
    return ( self.connection_paramaters, self.uuid, self.name, self.current_state )

  def __setstate__( self, state ):
    self.connection_paramaters = state[0]
    self.uuid = state[1]
    self.name = state[2]
    self.current_state = state[3]


class get_interface_map( ExternalFunction ):
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.uuid = foundation.vcenter_uuid
    self.name = foundation.locator
    self.connection_paramaters = foundation.vcenter_host.connection_paramaters
    self.interface_list = None

  @property
  def ready( self ):
    if self.interface_list is not None:
      return True
    else:
      return 'Waiting for Interface Map'

  def setup( self, parms ):
    pass

  @property
  def value( self ):
    result = {}
    for i in range( 0, min( len( INTERFACE_NAME_LIST ), len( self.interface_list ) ) ):
      result[ INTERFACE_NAME_LIST[ i ] ] = self.interface_list[ i ]

    return result

  def toSubcontractor( self ):
    return ( 'get_interface_map', { 'connection': self.connection_paramaters, 'uuid': self.uuid, 'name': self.name } )

  def fromSubcontractor( self, data ):
    self.interface_list = data[ 'interface_list' ]

  def __getstate__( self ):
    return ( self.connection_paramaters, self.uuid, self.name, self.interface_list )

  def __setstate__( self, state ):
    self.connection_paramaters = state[0]
    self.uuid = state[1]
    self.name = state[2]
    self.interface_list = state[3]


class set_interface_macs():
  def __init__( self, foundation, *args, **kwargs ):
    super().__init__( *args, **kwargs )
    self.foundation = foundation

  def __call__( self, interface_map ):
    for name in interface_map:
      mac = interface_map[ name ]
      try:
        iface = self.foundation.networkinterface_set.get( name=name )
      except ObjectDoesNotExist:
        raise ParamaterError( 'interface_map', 'interface named "{0}" not found'.format( name ) )

      iface.mac = mac

      try:
        iface.full_clean()
      except ValidationError as e:
        raise ParamaterError( 'interface_map', 'Error saving interface "{0}": {1}'.format( name, e ) )

      iface.save()


# plugin exports

TSCRIPT_NAME = 'vcenter'

TSCRIPT_FUNCTIONS = {
                      'create': create,
                      'host_list': host_list,
                      'create_datastore': create_datastore,
                      'datastore_list': datastore_list,
                    }

TSCRIPT_VALUES = {
                 }
