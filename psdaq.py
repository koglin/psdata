
# /reg/g/pcds/dist/pds/.../tools/procmgr/
import sys
import time
import psutils
import pydaq
#from ProcMgr import deduce_platform
import ProcMgr
#from ProcMgr import *
#import pycdb

class psdaq(object):
    """LCLS daq interface.
    """

    _pdsdir = '/reg/g/pcds/dist/pds'
    _control_properties = [
            'dbalias', 'dbkey', 'dbpath', 
            'detectors', 'devices', 'types',
            'eventnum', 'experiment', 'l3eventnum',
            'partition', 'record', 'runnumber',
            ]

    _control_functions = ['begin', 'configure', 'connect', 'disconnect', 'stop']

    _psdaq_functions = ['stop', 'begin', 'end', 'configure', 'connect', 'disconnect', 
        'stop_run', 'end_run', 'get_state', 'update_state']

    _pydaq = {
            'platform':  None,
            'host': None,
            'cnf': None,
            'instrument': None,
            'station': None,
            'control': None,
            'init': False,
            'connected': False,
            'ProcMgr': None,
            'state': None,
            'events': 120,
            'duration': None,
            'l1t_events': None,
            'l3t_events': None, 
            'controls': None,
            'monitors': None,
            }

    def __init__(self, initialize=False, **kwargs):

        if initialize or not self._pydaq['init']:
            self.init(**kwargs)

    def init(self, instrument=None, host=None, station=None,
                cnf_name=None, cnf_dir=None,
                procmgr_macro=None, **kwargs):
        if not instrument:
            instrument = psutils.instrument_guess()

        if not cnf_dir:
            cnf_dir = '{:}/{:}/scripts'.format(self._pdsdir, instrument)

        if not cnf_name:
            if station:
                cnf_name = '{:}_{:}.cnf'.format(instrument, station)
            else:
                cnf_name = '{:}.cnf'.format(instrument)
        
        if not host:
            if station == 1:
                host = instrument+'-monitor'
            else:
                host = instrument+'-daq'

        cnf_file = '/'.join([cnf_dir,cnf_name])

        print instrument, station, host, cnf_name

        platform = ProcMgr.deduce_platform(cnf_file)

#        proc_mgr = ProcMgr.ProcMgr(cnf_file, platform)

#        config = daq_config(cnf_file, platform, **kwargs)

        control = pydaq.Control(host, platform)

        self._pydaq.update({
                'control': control,
#                'ProcMgr': proc_mgr,
#                'config': config,
                'platform': platform,
                'instrument': instrument,
                'station': station,
                'host': host,
                'cnf': cnf_file,
                'cnf_dir': cnf_dir,
                'init': True,
                })

    def __getattr__(self, attr):
        if attr in self._pydaq:
            return self._pydaq[attr]

        if attr in self._psdaq_functions:
            return getattr(sys.modules[self.__module__], attr)

        if attr in self._control_functions:
            return getattr(self._pydaq['control'], attr)

        if attr in self._control_properties:
            return getattr(self._pydaq['control'], attr)()
    
    def __dir__(self):
        all_attrs = set(self._pydaq.keys() +
                        self._psdaq_functions +
                        self._control_functions +
                        self._control_properties +
                        self.__dict__.keys() + dir(psdaq))
        return list(sorted(all_attrs))

    def make_config(self, procmgr_macro=None, procmgr_config=None):
        """Build dictified Daq configuration built from daq cnf file.
        """
        _config_sub = {'id':'id', 'cmd':'cmd', 'flags':'flags', 
                  'port':'port', 'host':'host',
                  'rtprio':'rtprio', 'env':'env', 
                  'evr':'evr'}

        _config_def = {'platform': repr(self.platform), 
                  'procmgr_config': procmgr_config,
                  'procmgr_macro': procmgr_macro}

        _procmgr_attrs = ['procmgr_config_base', 'procmgr_config_dss', 'procmgr_config_mon']

        self._config_dict = dict(_config_sub.items() + _config_def.items())

        execfile(self.cnf, {}, self._config_dict)

        self._daq_hosts = {attr: val for attr,val in self._config_dict.items() \
                           if attr.startswith('daq_'+self.instrument.lower())}

        self._ffb_hosts = {attr: val for attr,val in self._config_dict.items() \
                           if attr.startswith('psana'+self.instrument)}

        for key, item in self._config_dict.items():
            setattr(self, key, item)

class daq_config(object):
    """Daq configuration built from daq cnf file.
    """

    def __init__(self, config, platform, **kwargs):
        """Initialize the configuration from daq cnf file.
        """

        self._hosts = {}
        
        for key, item in config.items():
            alias = ProcMgr.key2uniqueid(key)
            setattr(self, alias, item[2])

class ProcProcess(object):
    """ProcMgr Process object.
    """
    def __init__(self, daq, uniqid):

        self._ProcMgr = daq.ProcMgr
        self.uniqid = uniqid

#        _proc_funcs = ['spawnConsole', 'spawnLogfile']
#        for func in _proc_funcs:
#            setattr(self, func, getattr(daq.ProcMgr, func)(uniqid))

        _proc_properties = {'status': 'getStatus'} 
        for attr, func in _proc_properties.items():
            setattr(self, attr, getattr(daq.ProcMgr, func)(uniqid))

    def spawnConsole(self):
        self._ProcMgr.spawnConsole(self.uniqid)


class ProcHost(object):
    """ProcMgr host object.
    """

    def __init(self, daq, host, **kwargs):
       
        self.host
#        _proc_funcs = ['spawnXterm']
#        for func in _proc_funcs:
#            setattr(self, func, getattr(ProcMgr, func))

    def spawnXterm(self):
        self.ProcMgr.spawnXterm(self.uniqid)


def show_partition():
    """Returns a list of dictionary objects describing all nodes in the DAQ readout.
    """
    return psdaq._pydaq['control'].partition() 

def disconnect_daq(**kwargs):
    disconnect(**kwargs)

def disconnect(**kwargs):
    """Disconnect the python daq interface.
    """
    if psdaq._pydaq['connected']:
        psdaq._pydaq['control'].disconnect()
        psdaq._pydaq.update({'connected': False})
        psdaq._pydaq.update({'state': 'disconnected'})
        return 1
    
    else:
        print 'Connot disconnect daq:  daq is currently not connected'
        return 0

def connect(**kwargs):
    """Connect the python daq interface.
    """
    if not psdaq._pydaq['init']:
        daq = psdaq(**kwargs)    
    
    if not get_state('connected'):
        try:
            control().connect()
            psdaq._pydaq.update({'connected': True})
            update_state('connected')
            return 1
        except:
            print 'Cannot connect to daq -- check that Partition is selected in DAQ control GUI'

    else:
        print 'Daq is currently already connected'
        return 0

def configure(record=False, auto_config=True, **kwargs):
    """Configures control to use database key (default to current key) either:
         (1) collecting a fixed number of events on each cycle (when events=<Integer>
             or l1t_events=<Integer> is specified) or
         (2) collecting events until a fixed number of events have been accepted by
             the level3 filter (when l3t_events=<Integer>) or
         (3) collecting events for a fixed duration (when duration=[seconds,nanoseconds]
             is specified).  
           events=<Integer> or l1t_events=<Integer> or l3t_events=<Integer> or duration=[seconds,nanoseconds],
       
       The list of variables controlled (optional) in the scan:
           controls=[(name,value)]
       
       The list of variables to be monitored (optional) during acquisition are specified.
           monitors=[(name,lo_range,hi_range)]            

       The option to record can also be set.  
       If it is omitted, then the value from the local control is used.
       
       A modified list of objects from the Control.partition() call may be given for the partition argument to
       select only a subset of detectors for readout or recording by changing the values of the 'Readout' or 'Record'
       dictionary entries.  If this argument is omitted, the partition is readout and recorded as initially configured.
           partition=[()])
    """
    if auto_config and not connected():
        connect()

    if 'events' not in kwargs or 'l1t_events' not in kwargs \
            or 'l3t_events' not in kwargs or 'duration' not in kwargs:
        events = psdaq._pydaq['events']
        kwargs.update({'events': events})
    
    if get_state('connected'): 
        control().configure(record=record, **kwargs) 
        update_state('configured')
        return 1
    else:
        print 'Cannot configure daq:  daq must first be connected'
        return 0

def begin(auto_config=True, record=None, new_run=False, repeat=False, 
          disconnect=False, reconfigure=False,
          quiet=False, wait=False, **kwargs):
    """Begins acquisition for the specified settings of control variables (if specified).
       Actual control of these variables is the responsibility of the remote application.  
       Monitor variables (optional) are enforced during acquisition.  Omitted values
       default to those specified most recently (or in the 'configure' method).

          new_run:  starts new run
          wait:     wait until run is finished befure returning
          repeat:   number of times to repeat (default = 1)
          disconnect: disconnect daq when finished.
          reconfigure:  reconfigure daq (between runs/cycles if repeat is set True)

       Useful kwarg (automatically passed to configure method)
          events:  Number of events in cycle
    """
    if new_run and connected() and not get_state('configured'):
        stop_run()

    if auto_config or reconfigure:
        if not connected():
            connect()

        if get_state('connected'):
            configure(record=record, **kwargs)

    if get_state() in ['configured', 'stop', 'end', 'running']:
        if repeat:
            for irepeat in range(repeat):
                control().begin(**kwargs) 
                update_state('running')
                end(quiet=quiet, disconnect=disconnect)
                if irepeat < repeat:
                    if reconfigure:
                        connect()
                        configure(record=record, **kwargs)

        else:
            control().begin(**kwargs) 
            update_state('running')
            if wait:
                return end(quiet=quiet, disconnect=disconnect)
            elif disconnect:
                disconnect()

    else:
        print 'Cannot begin run:  daq must be configured'
        if get_state() is not 'connected':
            print '                   and daq must also be connected.' 
        return 0

def stop(disconnect=False, **kwargs):
    """Signals the local host control to terminate the current acquisition cycle.
       This method can be used to prematurely end a scan without closing the connection or reconfiguring. 
       The KeyboardInterrupt(SIGINT) signal handler can be reimplemented to call this method, which will
       result in the scan ending and a python ValueError exception being raised.
    """
    if get_state() in ['running', 'end', 'stop']:
        control().stop(**kwargs) 
        if disconnect:
            return disconnect_daq()
        else:
            update_state('stop')
            return 1
    
    else:
        print 'Cannot stop run:  daq is not running'
        return 0

def stop_run(**kwargs):
    """Stop acquisition and disconnect.
    """
    stop(disconnect=True)

def end_run(**kwargs):
    """End acquisition and disconnect.
    """
    end(disconnect=True, **kwargs)

def end(quiet=False, disconnect=False, **kwargs):
    """Waits for the end of acquisition cycle signalled from the local host control.
    """
    if get_state('running'):
        control().end()
        if not quiet:
            print 'Waiting for the end of acquisition cycle before stopping the daq.' 
        if disconnect:
            return disconnect_daq()
        else:
            update_state('end')
            return 1
    
    else:
        if disconnect:
            control().disconnect()
            update_state('disconnected')
            return 0

def get_state(*arg):
    """Get daq state.  
          disconnected
          connected
          configured
          running
          stop
          end

       If an arguement is supplied then the result will be a test if the state is
       the value of the argument.
    """
    if len(arg) > 0:
        if psdaq._pydaq['state'] is arg[0]:
            return True
        else:
            return False
    else:
        return psdaq._pydaq['state']

def update_state(state):
    psdaq._pydaq.update({'state': state})
    if state is 'connected':
        psdaq._pydaq.update({'connected': True})
    elif state is 'disconnected':
        psdaq._pydaq.update({'connected': False})

def connected():
    return psdaq._pydaq['connected']

def control(**kwargs):
    """Returns pydaq control object.
    """
    return psdaq._pydaq['control']

def eventnum():
    """Get event number -- WARNING starts new calib cycle!!!
    """
    if connected():
        return control().eventnum()
    else:
        return None

def experiment():
    if connected():
        control().experiment()
    else:
        return None

def runnumber():
    if connected():
        control().runnumber()
    else:
        return None

#    _control_functions = ['begin', 'configure', 'connect', 'disconnect', 'stop']

#for attr in _control_functions:
#    setattr(sys.modules['psdaq'], attr, getattr(psdaq._pydaq['control'], attr))

