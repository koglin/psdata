# import standard python system tools
import argparse
from glob import glob
import re
import operator
import sys
import os
import imp
import subprocess
import inspect
import pprint
import time


# import standard python scientific data analysis packages from ana-release
from pylab import *
import pandas as pd

# ROOT currently messes with tab completion -- do not use until fixed 
# idea was to use ROOT in add_histogram, but Justin may have beter ideas.
#import ROOT

# import specialized python packages from ana-release 
import epics

# import PCDS specific python packages from ana-release
from RegDB import experiment_info
import psana
from psmon import publish
from psmon.plots import Image, XYPlot, MultiPlot
from LogBook import message_poster


from PsanaDictify import * 
import lcls_devices

_lcls_instruments = ['amo','sxr','xpp','xcs','cxi','mec','xrt']
_default_exp = {'exp': 'cxitut13', 'run': 22}
_instrument_good_guess = None 
_exp_good_guess = None

def interactive_mode():
    try:
        __IPYTHON__
    except NameError:
        if hasattr(sys,'ps1'):
            return 'interactive'
        else:
            return None
    else:
        return 'ipython'

def import_module(module_name,module_path):
    """Import a module from a given path.
    """
    try:
        if not isinstance(module_path,list):
            module_path = [module_path]
        file,filename,desc = imp.find_module(module_name,module_path)
        globals()[module_name] = imp.load_module(module_name, file, filename, desc)
#        setattr(sys.modules[__name__],module_name,
#                imp.load_module(module_name, file, filename, desc)) 
    except ImportError, err:
        print 'ImportError:', err
    except:
        print 'import_module error'

def get_groups(*args, **kwargs):
    """Return dictionary of groups for list of usernames.  
    If username(s) are not input get groups for current login user.
    """
    try:
        if len(args) == 1:
            if type(args[0]) is list:
                usernames = args[0]
            else:
                usernames = args
        elif len(args) > 1:
            usernames = args
        else:
            usernames = [os.getlogin()]

        groups = {}
        for user in usernames:
            try:
                groupinfo = subprocess.Popen(["groups",user],
                                stdout=subprocess.PIPE).communicate()[0]
                groupstr = groupinfo.split(':')[1]
                groups[user] = groupstr.split()
            except:
                groups[user] = [] 
        return groups
    except:
        print 'No groups found'
        return None

def get_experiments(*args, **kwargs):
    """Return dictionary of experiments for list of users.
    If username(s) are not input get experiments for current login user.
    """
    groups = get_groups(*args)
    experiments = {}
    for user in groups:
        try:
            experiments[user] = [exp for exp in groups[user] 
                             if len(exp) == 8 and len(exp.split('-')) == 1]
        except:
            experiments[user] = []
    return experiments

def parse_instrument(**kwargs):
    """Return (instrument, station) tuple from instrument and station keywords.
       Guess instrument and station if keywords not supplied.
    """
    if len(kwargs) > 0 and 'instrument' in kwargs.keys():
        instrument = kwargs['instrument']
    else:
        instrument = instrument_guess()
    if len(kwargs) > 0 and 'station' in kwargs.keys():
        station = kwargs['station']
    else:
        station = 0

    if len(instrument) > 3:
        try:
            station = int(instrument[4])
            if station > 1:
                station = 0
        except:
            station = 0
        instrument = instrument[0:3]

    return (instrument,station)

def active_experiment(*args, **kwargs):
    """Returns active experiment. 
    Will parse input as instrument:station where station is optional.
    Or instrument and station can be input as keywords with station=0 as default.

    PARAMETERS:

      @param instrument: the name of the instrument
      @param station: the optional station number 
            (default is 0, for cxi station 1 is the parasitic daq experiment)
      @return: the list of run descriptors as explained above
    
    """
    if len(args) > 0:
        kwargs['instrument'] = args[0]
    instrument, station = parse_instrument(**kwargs)

    try: 
        active_experiment = \
            experiment_info.active_experiment(instrument.upper(),station)[1]
    except:
        raise NameError('instrument:',instrument,'station:',station)
        print 'Cannot determint active experiment!'
        active_experiment = None

    return active_experiment

def live_source(*args, **kwargs):
    """Returns psana source string for live data from shared memory on the current node.
    """
    if 'monshmserver' in kwargs:
        monshmserver = kwargs['monshmserver']
    else:
        monshmserver = None

    if not monshmserver:
        monshmserver='psana'

    shm_srvs = glob('/dev/shm/PdsMonitorSharedMemory_'+monshmserver)
    if shm_srvs == []:
        instrument = instrument_guess()
        monshmserver = instrument.upper()
        shm_srvs = glob('/dev/shm/PdsMonitorSharedMemory_'+monshmserver)
    
    if shm_srvs != []:
        try:
            MPI_RANK = 0
            source_str = 'shmem={:}.0:stop=no'.format(monshmserver)
        except:
            print 'Exception in finding shared memory server: ',shm_srvs
            source_str = None
    else:
        source_str = None

    return source_str

def experiment_guess(*args, **kwargs):
    """Returns best guess as to what your experiment is based on
    most recent experiment for which you have been added.
    Use get_experiments to get a list of all of your experiments.
    instrument is an optional keyword to narrow the search
    """
    if len(args) == 0:
        global _exp_good_guess
        global _instrument_good_guess
    else:
        _exp_good_guess = None
        _instrument_good_guess = None

    try:
        instrument = kwargs['instrument']
    except:
        if _instrument_good_guess is None:
            instrument = instrument_guess() 
        else:
            instrument = None

    if instrument and is_in_group('ps-'+instrument) or is_in_psdata():
        exp_best = active_experiment(instrument)
    else:
        experiments = get_experiments(*args).values()[0]
        if len(experiments) > 0:
            nruns = 0
            iexp = 0
            while nruns == 0 and iexp < len(experiments):
                exp = experiments[-1-iexp]
                inst = exp[0:3]
                runs = experiment_info.experiment_runs(inst.upper(),exp)
                nruns = len(runs)
    #            print 'tryiing: ',exp,inst,nruns
                if nruns > 0:
                    exp_best = exp
                    nruns_best = nruns
                    if _instrument_good_guess is True and inst != instrument:
                        nruns = 0
                        _exp_good_guess = False 
                    else:
                        _exp_good_guess = True
                iexp += 1
            if nruns_best == 0:
                exp_best =  _default_exp['exp']
                _exp_good_guess = False 
        else:
            exp_best = _default_exp['exp'] 
            _exp_good_guess = False 

    return exp_best

def instrument_guess(*args):
    """Return the instrument on which you are working based. 
    """
    if len(args) > 0:
        global _instrument_good_guess
    else:
        _instrument_good_guess = None
    
    hostsplit = os.uname()[1].split('-')
    cwdsplit = os.getcwd().split('/')
    if len(hostsplit) == 2 and hostsplit[0] in _lcls_instruments:
        instrument = hostsplit[0]
        _instrument_good_guess = True
    elif len(hostsplit) > 2 and hostsplit[1] in _lcls_instruments:
        instrument = hostsplit[1]
        _instrument_good_guess = True
    elif len(cwdsplit) > 4 and cwdsplit[4] in _lcls_instruments:
        instrument = cwdsplit[4]
        _instrument_good_guess = True 
    elif len(get_ps_instruments(*args)) > 0:
        _instrument_good_guess = False
        instrument = get_ps_instruments(*args)[0]
    else:
        instrument = experiment_guess(*args)[0:3]
        _instrument_good_guess = False

    return instrument

def get_ps_instruments(*args):
    """Return list of instruments for which user is an instrument member.
       e.g., in the group 'ps-cxi'
    """
    # should add all instrument accounts if in ps-data?
    groupdict = {'ps-'+inst: inst for inst in _lcls_instruments}
    groups = get_groups(*args).values()[0]
    return [groupdict[key] for key 
            in list(set(groups) & set(groupdict.keys()))]

def get_opr_accounts(*args):
    """Return list of instruments for which user is an operator.
       e.g., in the group 'cxiopr'
    """
    groupdict = {inst+'opr': inst for inst in _lcls_instruments}
    groups = get_groups(*args).values()[0]
    return [groupdict[key] for key in list(set(groups) & set(groupdict.keys()))]

def is_in_group(group,*args):
    """Return True if user is in specified group.  
       If no username is supplied assume current user.
       Usage:
           is_in_group(group,[username])
    """
    groups = get_groups(*args).values()[0]
    return group in groups

def is_in_psdata(*args):
    """Return True if user is in 'ps-data' group.
    """
    return is_in_group('ps-data',*args)

def is_in_pcds(*args):
    """Return True if user is in 'ps-pcds' group.
    """
    return is_in_group('ps-pcds',*args)

def is_in_psusers(*args):
    """Return True if user is in 'ps-users' group.
    """
    return is_in_group('ps-users',*args)

def read_dictionary(file_name):
    """Read and return a python dictionary from file.
    """
    try: 
        with open(file_name,'r') as f:
            read_dict = eval(f.read())
    except:
        print "Failed reading ", file_name
        read_dict = None

    return read_dict

def write_dictionary(out_dict, file_name, **kwargs):
    """Write out a dictionary to file (using pprint for easy to read formatting).
    """
    print out_dict,filename
    try:
        with open(file_name,'w') as f:
            f.write(pprint.pformat(out_dict))
    except:
        print "Failed writing to ", file_name

def read_device_config(config_file=None, instrument=None, **kwargs):
    """Read device configuration file.  
       By default config_file is assumbed to be named 'device_config.dict' 
       and located in the instrument opr home directory. 
    """
#    if not config_file:
#        if not instrument:
#            instrument = instrument_guess()
#        config_file = '/reg/neh/home1/koglin/device_config.dict'
#        config_file = '/reg/neh/operator/'+instrument+'opr/device_config.dict'

    _device_types_default = {'MMS':     {'module': 'ims',
                                         'class':  'IMS'},
                             'PIC':     {'module': 'epics.motor',
                                         'class':  'Motor'}}
    
    device_config = {'device_sets': {}, 'device_types': _device_types_default}

    if config_file:
        try:
            print 'Loading configuation file from ', config_file
            device_config = read_dictionary(config_file)
            device_sets = device_config['device_sets']
            if 'device_types' not in device_config:
                device_config['device_types'] = _device_types_default
            print 'Setting device configuration detector aliases:'
            for det in device_sets:
                name_key = None
                if 'det' in device_sets[det]:
                    try:
                        src = device_sets[det]['det']
                        if 'detName' in src:
                            name_key = '_'.join([src['detName'],str(src['detId']),
                                            src['devName'],str(src['devId'])])
                        elif 'typeName' in src:
                            name_key = '_'.join([src['typeName'],str(src['type'])])
                        if name_key:
                            device_sets[det]['det']['det_key'] = name_key
                        print name_key, ' is defined as ', det
        
                    except:
                        pass

        except:
            print 'Warning!!! ',config_file, ' is not a valid detector configuration file: ' 

    else:
        print 'No config_file specified.  Organizing data according to daq aliases.' 

    return device_config

def write_epicsArch(device_sets, file_name='epicsArch_psana.txt'):
    """Write out an epicsArch file with aliases from a device_sets dictionary.
    """
    print "Writing to ",file_name
    with open(file_name,'w') as f:
        for det in device_sets:
            if 'pvs' in device_sets[det]:
                if 'desc' in device_sets[det]:
                    desc = device_sets[det]['desc']
                else:
                    desc = det
                f.write('\n')
                f.write('# {:} \n'.format(det))
                for alias,pv_dict in device_sets[det]['pvs'].items():
                    try:
                        if 'base' in pv_dict and pv_dict['base'].split(':')[2] in ['MMS','CLZ','CLF','MMN','MZM','PIC']:
                            f.write('*{:}_{:} \n'.format(det, alias))
                            f.write('{:}.RBV \n'.format(pv_dict['base']))
                    except:
                        pass

def doc_parse(attr):
    desc = None
    if attr.__doc__:
        try:
            data_type = attr.__doc__.split(' -> ')[1].split('\n')[0]
            desc = attr.__doc__.split(' -> ')[1].split('\n')[1:]
        except:
            data_type = None
    else:
        data_type = None
    return data_type

def true_args(arg_list, any=False, **kwargs):
    """Check if all arguments are in kwargs. 
       If any is set to True, then return True if any of the args in the list
       is set to True in kwargs. 
    """
    is_true = None
    for arg in arg_list:
        if arg in kwargs:
            if not kwargs[arg]:
                is_true = False
            elif any or is_true is None:
                is_true = True
        else:
            if not any:
                is_true = False
    return is_true

def args_list_flatten(*args):
    try:
        return [item for sublist in args for item in sublist]
    except:
        print 'Cannot flatten list of args: ', args

def get_unit_from_doc(doc):
    try:
        unit = '{:}'.format(doc.rsplit(' in ')[-1])
        unit = unit.rstrip('.').rstrip(',').rsplit(' ')[0].rstrip('.').rstrip(',')
    except:
        unit = None
    return unit

def get_psana_attr_dict(psana_class):
    """Return dictionary of the attributes for a psana data class.
    """
    try:
        if isinstance(psana_class,str):
            cls = eval(psana_class)
        else:
            cls = psana_class 

        attr_dict = {'class':    cls,
                     'name':      cls.__name__,
                     'module':   cls.__module__}

        for attr in ['TypeId','Version']:
            if hasattr(cls,attr):
                if attr is 'mro':
                    val = getattr(cls,attr)()
                else:
                    val = getattr(cls,attr)
            else:
                val = None
            attr_dict[attr] = val

        try:        
            attrs = {attr: doc_parse(getattr(cls,attr)) for attr in dir(cls)
                     if not attr.startswith(('_','TypeId','Version'))}
        except:
            attrs = None 

        attr_dict['attrs'] = attrs
    except:
        attr_dict = None
        print 'WARNING: ', psana_class, 'is not a valid psana class'

    return attr_dict

def psana_modules():
    psana_modules = {mod[0]: {cls[0]: get_psana_attr_dict(cls[1]) 
                     for cls in inspect.getmembers(mod[1], predicate=inspect.isclass)}
                     for mod in inspect.getmembers(psana, predicate=inspect.ismodule) 
                     if mod[1].__name__.startswith('psana')}

    return psana_modules

_psana_modules = psana_modules()

def psana_class_attrs():
    lookup = {}
    for id in range(0, 999):
        for mod in _psana_modules:
            for cls in _psana_modules[mod]:
                info = _psana_modules[mod][cls]
                if info['TypeId'] == id:
                    lookup[(id, info['Version'])] = info

    return lookup

class psdata(object):
    """Class to organize psana data according to detector sets and make it conveniently
       accessible in ipython.

       _psana_modules is a dictionary of all the psana modules and the data
           types expected from the psana docstring.
    """

    _default_modules = {'device': {
                            'EvrData': 'evr', 
                            'Imp': 'imp',
#                            'Acqiris': 'acqiris',
                            'Epix': 'epix100',
                            'CsPad': 'cspad',
                            },
                        'det_key': {
                            'XrayTransportDiagnostic_0_Opal1000_0': 'xtcav_det',
                                   },
                       }

    _default_functions = {'Acqiris': 'acqiris'}
    _instruments = _lcls_instruments
    _exp_defaults = {'instrument':None, 
                     'live':None, 
                     'exp':None, 
                     'h5':None,
                     'run':0, 
                     'station':0,
                     'ffb':None,
                     'cfg':None}
    _epics_devices = {}
    _epics_aliases = {}
    _det_src_list = ['detName','detId','detector','devName','devId','device','processId']
    _bld_src_list = ['typeName','type','processId']
    _psana_modules = psana_modules()
    _psana_class_attrs = psana_class_attrs()
    _no_data = False 
    _epics_live = False
    _publish = None

    def __init__(self, epics_only=False, *args, **kwargs):
        """Initialize psdata device configuration sets (_device_sets).
           From this generate a detector list (_det_list).
           Automatically loads data if the  instrument or exp keywords are set 
           to define the instrument and/or experiment, respectively.

          @param exp: optional name of the experiment 
                (default is the current experiment of the instrument)
          @param run: optional run number
                (default is last run, if run is negative then count backwards from last run)
          @param live: if true then use shared memory
          @param config_file: full path of device config file
                (default is 'device_config.dict' in instrument opr home direcectory)

        """
        self._kwargs = {}
        self.set_kwargs(**kwargs)
        self._detectors = {}
        self._det_list = [] 
        self._det_aliases = {}
        self._psplots = {}
        self._event_functions = {}
        self._source_attrs = []
        self._evt_time_last = (0,0)
        self.ievent = 0

#        self._user_attrs = {}
#        self._histograms = {}
        
        for key in kwargs:
            if key in self._exp_defaults:
                setattr(self,key,kwargs[key])
                print 'setting ',key, kwargs[key]

        self._device_config = read_device_config(**kwargs)
        self._device_sets = self._device_config['device_sets'] 
        self._device_types = self._device_config['device_types'] 

        for det in self._device_sets:
            if 'det' in self._device_sets[det]:
                if ('detName' in self._device_sets[det]['det'] or
                        'typeName' in self._device_sets[det]['det']):
                    self._det_list.append(det)
                    if 'det_key' in  self._device_sets[det]['det']:
                        self._det_aliases[self._device_sets[det]['det']['det_key']] = det 
            else:
                pass
            
            if 'pvs' in self._device_sets[det]:
                for attr in self._device_sets[det]['pvs']:
                    pvbase = self._device_sets[det]['pvs'][attr]['base']
                    alias = '_'.join([det,attr])
                    self.add_pv(pvbase, alias)

        self.set_exp_defaults(**kwargs)
        if self.get_kwarg('noload') or not live_source():
            if self._kwargs.get('epics_live'):
                if not self.get_kwarg('epics_file'):
                    self.set_kwargs(epics_file='epicsArch.txt')
        
        print 'Instrument = ',self.instrument 
        if self._kwargs.get('epics_file'):
            print 'Adding epics aliases according to',self._kwargs.get('epics_file')
            self.load_epics_dict(**kwargs)

        if not self.get_kwarg('noload'):
            self.load_run(*args, **kwargs)
            self._no_epicsStore = False

        if self.ds and self.live:
            self.next_event()
        
        if self.ds and not self._kwargs.get('epics_file') \
                and not self._kwargs.get('no_epics_aliases'):
            self.add_aliases_to_device_sets()
            print 'Adding epics aliases to device sets'

        if not self.ds:
            self._no_epicsStore = True
            self._no_data = True
            for det in self._device_sets:
                if 'pvs' in self._device_sets[det]:
                    print 'Adding epics ',det
                    self.add_detector(det)

#    def add_epics_modules(device_types):
#        """Add Epics modules from config dictionary.
#        """
#        for dev in device_types:
#            module_name = device_types[dev]['module']
#                    import_module(module_name, module_path)
#                    new_class =  getattr(globals()[module_name],module_name)
#                    print 'Loading {det} as {new_class} from {module_path}'.format(
#                           det=det,new_class=new_class,module_path=module_path)
#                    setattr(self, det, new_class(det,self))

    def add_pv(self, pv, alias):
        """Add pv to _device_sets dictionary and _epics_aliases dictionary.
           pv's will be loaded on demand when necessary.
        """
        pvbase = pv.split('.')[0]
        det = alias.split('_')[0]
        attr = '_'.join(alias.split('_')[1:])
        self._epics_aliases[alias] = pvbase 
        if det not in self._device_sets:
            self._device_sets[det] = {'pvs': {}}

        if attr not in self._device_sets[det]['pvs']:
            self._device_sets[det]['pvs'][attr] = {'base': pvbase}
        
        self._epics_aliases[alias] = pvbase

    def remove_pv(self, alias):
        """Remove a pv from _device_sets and _epics_aliases dictionaries.
        """
        if alias in self._epics_aliases:
            self._epics_aliases.pop(alias)
        try:
            det = alias.split('_')[0]
            attr = '_'.join(alias.split('_')[1:])
            self._device_sets[det]['pvs'].pop(attr)
        except:
            print 'No attribute {:} in {:} to remove'.format(attr, det)

    def get_kwarg(self, arg):
        """Get argument from keyword arguments set during loading of psdata.
        """
        return self._kwargs.get(arg)

    def set_kwargs(self, reset=False, **kwargs):
        """Store keywarg arguments set during loading.
           These arguments can be retrieved with get_kwarg(arg).
        """
        if reset:
            self._kwargs = {}
        for arg in kwargs:
            self._kwargs[arg] = kwargs[arg] 

    def reset(self, reset_user=False, **kwargs):
        """Resets defaults for psdata object from _default_attrs dictionary.
        Any additional keywords will also be set and added to the _user_attrs dictionary.
        """
        for attr in self._exp_defaults:
            setattr(self, attr, self._exp_defaults[attr])
        for attr in self._source_attrs:
            delattr(self, attr)
        self._source_attrs = []

    def set_exp_defaults(self, **kwargs):
        default_exp = False
        for key in kwargs:
            if key in self._exp_defaults:
                setattr(self,key,kwargs[key])
        if self.exp is not None:
            self.instrument = self.exp[0:3]
        if self.instrument is None:
             self.instrument = instrument_guess()

        if self.exp is None or self.live is True:
            if live_source(monshmserver=self.monshmserver) is not None:
                self.live = True
                self.exp = active_experiment(self.instrument)
                self.run = 0
                self.h5 = False
                self.indexed = False
            else:
                self.live = False
#                self.indexed = True
                if self.exp is None:
                    self.exp = experiment_guess(instrument=self.instrument)

        if self.exp.startswith('dia'):
            self.instrument = self.exp[3:6]
        else:
            self.instrument = self.exp[0:3]

        self.instrument_elog = message_poster.message_poster_self( \
                'NEH', self.instrument.upper()+' Instrument')
        self.exp_elog = message_poster.message_poster_self( \
                self.instrument.upper(), experiment=self.exp )

    def get_data_source(self, *args, **kwargs):
        """Data source used in loading psana. 
        When loading new data_source use existing keywords in self as defaults.

        PARAMETERS:

          @param exp: optional name of the experiment 
                (default is the current experiment of the instrument)
          @param run: optional run number
                (default is last run, if run is negative then count backwards from last run)
          @param live: if true then use shared memory

        TODO:

          Need to check if exp and run number are valid and if h5 data is available.

        """
        if kwargs.get('exp',None) is not self.exp:
            self.xtc_dir = None

        self.set_exp_defaults(**kwargs)
#        if self.get_kwarg('camrecord'):
#            host = os.uname()[1]
#            xtc_dir = "/reg/d/camera/{:}/"

        if self.get_kwarg('iocrc'):
            if self.get_kwarg('iocrc') in 'local':
                host = os.uname()[1]
            else:
                host = self.get_kwarg('iocrc')
            
            self.xtc_dir = "/reg/d/cameras/{:}/daq/xtc".format(host)
            print self.xtc_dir

        if self.xtc_dir:
            default_dir = True
        else:
            self.xtc_dir = "/reg/d/psdm/{instrument}/{exp}/xtc".format(
                                instrument=self.instrument,exp=self.exp)
            default_dir = True
        
        if not self.h5_dir:
            self.h5_dir = "/reg/d/psdm/{instrument}/{exp}/hdf5".format(
                                instrument=self.instrument,exp=self.exp)

        if self.live:
            data_source = live_source(monshmserver=self.monshmserver)
        
        else:
#            if len(self.runs) == 0:
#                self.exp = _default_exp['exp']
#                self.run = _default_exp['run']
#                self.instrument = self.exp[0:3]
##                self.runs = experiment_info.experiment_runs(self.instrument.upper(),self.exp)
#                print 'No runs taken yet for ',self.exp
#                print 'Using default experiment {exp} and run {run}'.format(
#                        exp=self.exp,run=self.run)

            if len(self.runs) > 0 and self.run <= 0:
                while self.run < 0 and 'xtc_files' not in self.runs[-1+self.run]:
                    self.run += 1
                self.run = self.runs[self.run]['num']

            if self.run <= 0:
                data_source = None
            else:
                try:
                    self.exper_id = self.runs[self.run-1]['exper_id']
                    data_source = "exp={exp}:run={run}".format(exp=self.exp,run=self.run)
                    if self.ffb:
                        data_source += ":one-stream"
        #                data_source += ":live"
                        self.xtc_dir = "/reg/d/ffb/{instrument}/{exp}/xtc".format(
                                        instrument=self.instrument,exp=self.exp)
                    elif self.h5:
                        data_source += ":h5"
                    elif self.indexed:
                        data_source += ":idx"
                    
                    if self.xtc_dir and not default_dir and not self.h5:
                        data_source += ":dir={:}".format(self.xtc_dir)
                except:
                    data_source = None
                    print 'No data source'

        return data_source

    def load_epics_dict(self, epics_dir=None,epics_file=None, **kwargs):
        """Load dictionary of epics pvs into _epics_dict based on
           an epicsArch.txt file used by the daq to archive epics
           data in the xtc data files.
        """
        if not epics_file:
            epics_file = 'epicsArch.txt'

        if not epics_dir and self.instrument:
            epics_dir = '/reg/g/pcds/dist/pds/'+self.instrument+'/misc/'

        if epics_dir:
            print self.instrument
            print epics_file
            print epics_dir
            self._epics_dict = lcls_devices.epicsArch_dict(epics_file,epics_dir)
            if self._epics_dict:
                for key,item in self._epics_dict.items():
                    if 'alias' in item:
                        alias = item['alias']
                        alias_comp = item['alias'].split('_')
                        if len(alias_comp) > 1:
                            det = alias_comp[0]
                            attr = '_'.join(alias_comp[1:])
                            self._epics_aliases[alias] = item['base']
                            if det not in self._device_sets:
                                self._device_sets[det] = {'pvs': {}}
                            self._device_sets[det]['pvs'][attr] = item
        else:
            print 'load_epics_dict exception:  ' \
                 +'epics_dir specified to load epics_file = ',epics_file

    @property
    def runs(self):
        """Experiment run information from MySQL database and xtc directory.
        """
        if experiment_info.name2id(self.exp):
            runs_list =  experiment_info.experiment_runs(self.instrument.upper(),self.exp)
            for item in runs_list:
                runnum = item['num']
                item['xtc_files'] = glob('{:}/*-r{:04d}*.xtc'.format(
                                        self.xtc_dir,runnum))                        
                item['h5_files'] = glob('{:}/*-r{:04d}*.h5'.format(
                                        self.h5_dir,runnum))                        
        else:
            runs_list = []

        return runs_list

    def show_runs(self,start=0,end=99999999,csv=False):
        """Show run summary for current experiment.
        """
        if csv:
            print '{:>7}, {:>10}, {:>8}, {:>10}, {:3}, {:2}'.format('Run', 
                                'Day', 'Time', 'Length', 'xtc', 'h5') 
           
        else:
            print '='*72
            print 'Experiment {:}'.format(self.exp)
            print '  xtc dir {:}'.format(self.xtc_dir)
            print '  hdf5 dir {:}'.format(self.h5_dir)
            print '-'*72
            print '{:>7} {:>10} {:>8} {:>10} {:3} {:2}'.format('Run', 'Day', 'Time', 
                                                  'Length', 'xtc', 'h5') 
            print '-'*72
        
        for item in self.runs:
            run = item['num']
            if run >= start and run <= end:
                datestr = time.strftime('%Y-%m-%d',
                                        time.localtime(item['begin_time_unix']))
                timestr = time.strftime('%H:%M:%S',
                                        time.localtime(item['begin_time_unix']))
                if len(item['xtc_files']) > 0:
                    xtc = 'xtc'
                else:
                    xtc = ''
                
                if len(item['h5_files']) > 0:
                    h5 = 'h5'
                else:
                    h5 = ''
                
                begin_time = item['begin_time_unix']
                end_time = item['end_time_unix'] 
                if end_time:
                    dtime = end_time - begin_time
                    flag = ' '
                else:
                    dtime = time.time() - begin_time
                    flag = '*'

                dmin = int(dtime/60)
                dsec = int(dtime % 60)
                if dmin > 0:
                    dtstr = '{:4}m {:02}s'.format(dmin,dsec)
                else:
                    dtstr = '{:02}s'.format(dsec)

                if csv:
                    print '{:7}, {:10}, {:8}, {:>10}, {:3}, {:2}'.format(run,
                                        datestr, timestr, dtstr, xtc, h5)
                else:
                    print '{:7} {:10} {:8} {:>10} {:3} {:2}'.format(run,
                                        datestr, timestr, dtstr, xtc, h5)

                if flag in '*':
                    print '* Currently Acquiring Data for Run {:}'.format(run)

#    @property
#    def open_files(self, run=None):
#        """Return a list of files created (by the DAQ system).  
#           Current run if no run is specified.
#        """
#        return experiment_info.get_open_files(self.exper_id,run)

    def load_run_summary(self):
        """Load MySQL database experiment run summary information into a dictionary.
        """
        vrun_attrs = {}
        print 'Loading summary of {:} runs for {:} from SQL database'.format( \
                len(self.runs),self.exp)
        print 'Estimate loading time ~{:} sec'.format(len(self.runs)/4)
        for run in range(1,self.runs[-1]['num']+1):
            run_attr = experiment_info.run_attributes(self.instrument,self.exp,run)
            for a in run_attr:
                if a['name'] not in vrun_attrs:
                    vrun_attrs[a['name']] = {'class': a['class'], 'desc': a['descr'], 
                                             'type': a['type'], 'val': 
                                             [None for i in range(1,run)]} 
                vrun_attrs[a['name']]['val'].append(a['val'])
        self.run_summary = vrun_attrs

#    Need to put in pandas and make conveniently available, e.g.,
#        temp = {key: pd.Series(dat['val']) for key,dat in data.run_summary.items()}
#        pd.DataFrame(temp,columns=['CXI:SC1:MMS:02.RBV'])

    def load_run(self, *args, **kwargs):
        """Load run for experiment.
           Optionally pass 
        """
        if 'data_source' in kwargs:
            data_source = kwargs['data_source']
        else:
            data_source = self.get_data_source(*args, **kwargs)
        
        self.data_source = data_source

        if data_source:
            try:
                if self.cfg:
                    psana.SetConfigFile(self.cfg)
                self.ds = psana.DataSource(data_source)
                _source_attrs = ['ds','events','evt']
                self.events = self.ds.events()
                self.configStore = PsanaDictify(self.ds.env().configStore())
                if 'no_epics_aliases' not in kwargs or kwargs['no_epics_aliases'] is False:
                    print 'Adding epics aliases to device sets'
                    self.add_aliases_to_device_sets()
                self.ievent = 0
                if self.get_kwarg('nstart'):
                    for i in range(self.get_kwarg('nstart')-1),:
                        self.next_event()
            except:
                print 'Failed to load data source "{:}"'.format(data_source)
        else:
            if len(self.runs) > 0:
                print 'WARNING:  No xtc files for {:} available in {:}'.format(
                            self.exp,self.xtc_dir)
                print 'Either set xtc_dir to a valid directory or restore files' 
                print '  through the Data Manager:'
                pswww_portal = 'https://pswww.slac.stanford.edu/apps/portal/index'
                print pswww_portal+'.php?exper_id={:}'.format(self.exper_id)
            else:
                print 'No runs taken for this experiment'

    def add_aliases_to_device_sets(self):
        """add epicsStore aliases to _device_sets. 
        """
        for det in self.pv_alias_dict:
            if not any([char in det for char in ('.',':','"',' ',',',';')]):
                print 'Adding epicsStore aliases for ',det
                if det not in self._device_sets:
                    self._device_sets[det] = {}
                if 'pvs' not in self._device_sets[det]:
                    self._device_sets[det]['pvs'] = {}
                self._device_sets[det]['epicsStore'] = {attr: pv for
                        attr, pv in self.pv_alias_dict[det].items()}
                #add to pvs for live
                for attr, pv in self.pv_alias_dict[det].items():
                    pvbase = pv.split('.')[0]
                    self._device_sets[det]['pvs'][attr] = {'base': pvbase}

    @property
    def pv_alias_dict(self):
        """Dictionary of aliases split according to first _ in name.
        """
        alias_dict = {}
        for alias in self.ds.env().epicsStore().aliases():
            base = alias.split('_')[0]
            attr = alias.lstrip(base).lstrip('_')
            if base not in alias_dict:
                alias_dict[base] = {}
            alias_dict[base][attr] = self.ds.env().epicsStore().pvName(alias)

        return alias_dict

    def add_detector(self, det, module=None, path=None, empty=False, 
                     device=None, pvs=None, desc=None, **kwargs):
        """Add a detector module and update _device_sets configuration.
           Overwrites any existing detector module.
           Optionally add a dictionary of pvs with aliases.
        """
        initialized = False

        if empty or pvs:
            print 'Creating a Detector class ', det
            if not desc:
                desc = 'Empty Detector Class'
            self._device_sets[det] = {'desc': desc}
            if pvs:
                self._device_sets[det]['pvs'] = {}
                for alias, pv in pvs.items():
                    pvbase = pv.rsplit('.')[0] 
                    attr = '_'.join([det, alias.lstrip(det).lstrip('_')])
                    self.add_pv(pvbase, attr)
                    if self._kwargs.get('epics_live'):
                        self.add_live_pv(pvbase)

        if det in self._device_sets:
            det_dict = self._device_sets[det]
            # First check for device configuration
            if 'module' in self._device_sets[det]:
                module_name = self._device_sets[det]['module']['name']
                if 'path' in self._device_sets[det]['module']:
                    module_path = self._device_sets[det]['module']['path']
                else:
                    module_path = ''
            else:
                module_name = None 
                module_path = ''

            # Then use module and path keywords if applicable
            if module:
                if module_name:
                    print 'Changing {det} detector module from \
                          {module_name} to {module}'.format(
                           det=det,module=module,module_name=module_name)
                else:
                    self._device_sets[det]['module'] = {}
                
                module_name = module
                self._device_sets[det]['module']['name'] = module

            if device:
                self._device_sets[det]['device'] = device
            else:
                if 'device' in self._device_sets[det]:
                    device = self._device_sets[det]['device']

            # Use defaults if not set by keyword or in device config
            if 'det' in det_dict and 'det_key' in det_dict['det']:
                det_key = det_dict['det']['det_key']
            else:
                det_key = None

            if not module_name: 
                if det_key and det_key in self._default_modules['det_key']:
                    module_name = self._default_modules['det_key'][det_key]
                    module_path = ''
                elif device and device in self._default_modules['device']:
                    module_name = self._default_modules['device'][device]
                    module_path = ''

            if module_name:
                is_default_class = False
            else:
                is_default_class = True

            if not is_default_class:
                if path:
                    module_path = path
                    self._device_sets[det]['module']['path'] = path
        
                if module_path:
                    print 'Using the path {module_path} for {module_name}'.format( \
                           module_path=module_path, module_name=module_name)
                        
                try:
                    import_module(module_name, module_path)
                    new_class =  getattr(globals()[module_name],module_name)
                    print 'Loading {det} as {new_class} from {module_path}'.format(
                           det=det,new_class=new_class,module_path=module_path)
                    nomodule = False
                    self._detectors[det] = new_class(det,self, **kwargs)
                    initialized = True
                except:
                    is_default_class = True
                    print 'ERROR:  Cannot load {module_name} from \
                           {module_path}'.format(module_name=module_name,
                           module_path=module_path)
#                    if self.get_kwargs('show_errors'):
#                        import_module(module_name, module_path)
#                        new_class =  getattr(globals()[module_name],module_name)
#                        self._detectors[det] = new_class(det,self, **kwargs)

            if is_default_class:
                print 'Loading {det} as standard Detector class'.format(det=det)
                self._detectors[det] = Detector(det,self)
                initialized = True

            path = [os.getcwd()]
            function_files = []
            if device in self._default_functions:
                function_files.append(self._default_functions[device])

            if 'functions' in self._device_sets[det]:
                function_files.append(self._device_sets[det]['functions']['file'])
                if 'path' in self._device_sets[det]['functions']:
                    path.append(self._device_sets[det]['functions']['path'])

#            for file in function_files:
##                try:
#                print 'Loading functions for ',det
#                load_func = getattr(self._detectors[det],'load_functions')
#                load_func(file,path=path)
##                except:
##                    print 'FAILED Loading functions for ',det, 'from', file, 'in', path
#
            if initialized and self.get_kwarg('quick_alias'):
                print 'Making quick alias for ',det
                setattr(sys.modules['__main__'], det, self._detectors[det])

        else:
            print 'ERROR:  Need to add ',det,' information to _device_sets.'

#    def get_evt_data(self,det_list=None):
#        """Returns dictionary of data results.
#           If evt_keys dictionary provided only load data from thoses
#           event keys.
#           Name mangle and return as pandas series.
#        """
#        data = {} 
#        if not det_list:
#            det_list = list(set([self._det_aliases[evt_key['det_key']] 
#                                 for evt_key in self._evt_keys]))
#        for evt_key in self._evt_keys:
#            det_key = evt_key['det_key']
#            det_name = self._det_aliases[det_key]
#            if det_name in det_list:
##                if det_name not in data:
##                    data[det_name] = {}
#                for attr in evt_key['data']:
#                    value = evt_key['data'][attr]
#                    try:
#                        value = value()
#                    except:
#                        pass
#                    if hasattr(value,'__func__'):
#                        try:
#                            value = value()
#                        except:
#                            pass
#                    data['__'.join([det_name,attr])] = value
##                    data[det_name][attr] = value
#
##        return data 
#        return pd.Series(data) 

#    def get_events(self,nevents,**kwargs):
#        """Get Number of specified events and return as Pandas DataFrame.
#        """
#        vdata = []
#        for i in range(0,nevents):
#            if i % 100 == 99:
#                print 'Getting Event',i+1
#            vdata.append(self.get_evt_data(**kwargs))
#            self.next_event()
#
#        return pd.DataFrame(vdata) 

    def next_run(self):
        """Shortcut to load next run for same experiment.
        """
        self.load_run(run=self.run+1)

    def next_event(self):
        """Load next event and update _evt_keys for all detectors.
           Add any detectors that were not already defined.
        """
        if not self._no_data and self.ds:
            if hasattr(self, 'EventId'): 
                if hasattr(self.EventId,'time'):
                    self._evt_time_last = self.EventId.time
            
            self.evt = PsanaDictify(self.events.next())
            for det, key_dict in self.evt._keys_dict.items():
                if det not in self._det_aliases.values():
                    det_key = key_dict['det']['det_key']
                    if det not in self._device_sets:
                        self._device_sets[det] = {}
                    self._device_sets[det].update({'det': key_dict['det']})
                    self._det_aliases[det_key] = det
                    self._det_list.append(det)
                    print 'adding', det
                    self.add_detector(det)

            if hasattr(self, 'EventId'): 
                if hasattr(self.EventId,'run'):
                    self.run = self.EventId.run

        self.exec_event_functions
        
        if self._publish:
            self.psmon_publish()
        
        self.ievent += 1

    def exec_event_functions(self):
        """Execute event functions added at the detector level with
           Detector.add_event_function() 
        """
        for name, fdict in self._event_functions.items():
            try:
                if self.ievent % fdict['nevents'] == 0:
                    det_class = getattr(self,fdict['det'])
                    func = getattr(det_class,fdict['attr']) 
                    func(det_class, **fdict['kwargs'])
            except:
                print 'Error -- not able to execture event function: ', name
                print 'see _event_functions[func] for details on function'

#    def draw_histograms(self, attrs):

    def psmon_publish(self):
        for name, psmon_args in self._psplots.items():
            try:
                det_class = getattr(self,psmon_args['det'])
                if getattr(det_class,'is_in_keys'):
                    psmon_fnc = psmon_args['plot_function'](psmon_args['ts'],
                                    psmon_args['title'],
                                    getattr(det_class,psmon_args['attr']),
                                    **psmon_args['kwargs'])
                    publish.send(name,psmon_fnc)
            except:
                pass

    def add_live_pv(self, pv):
        """Add live pv to _epics_devices.
           Generally will be accessed through the Detector class
           where aliases are used to represent epics pvs.
        """
        if self.get_kwarg('epics_live'):
            self._epics_devices[pv] = lcls_devices.get_live_pv(pv)
        else:
            print 'WARNING:  Not possible to add live epics pv unless epics_live is set'

    def get_live_pv(self, pv):
        """Get live epics pv device.
        """
        if self.get_kwarg('epics_live'):
            if pv not in self._epics_devices:
                pv = pv.split('.')[0]
                if pv in self._epics_aliases:
                    pv =  self._epics_aliases[pv]

                if pv not in self._epics_devices:
                    self.add_live_pv(pv)
                
            if pv in self._epics_devices:
                return self._epics_devices[pv]
            else:
                return None

        else:
            print 'WARNING:  Not possible to get live epics pv unless epics_live keyword is set'

    def show_epics_live_info(self, attrs, aliases=None):
        """Show info for a list of epics live pvs.
           If motor pv then show RBV otherwise show VAL.
        """
        if not isinstance(attrs,list):
            attrs = [attrs]
        if not aliases or len(aliases) != len(attrs):
            aliases = attrs
        if self.get_kwarg('epics_live'):
            for i,attr in enumerate(attrs):
                pv = self.get_live_pv(attr)
                alias = aliases[i]
                if pv: 
                    if hasattr(pv,'RBV'):
                        value = pv.RBV
                    elif hasattr(pv,'VAL'):
                        value = pv.VAL
                    else:
                        value = 'NA'
                    if hasattr(pv,'precision'):
                        precision = pv.precision
                    else:
                        precision = 4
                    if hasattr(pv, 'EGU'):
                        unit = pv.EGU
                        if len(unit) > 10 or unit.rfind('\n') > 0:
                            unit = ''
                    else:
                        unit = ''
                        precision = 0
                    doc = pv.DESC
                    name = pv.NAME
                    if precision > 5:
                        formatstr = '{:18s} {:10.5g} {:6} {:>14} - {:}'
                    elif precision == 0:
                        formatstr = '{:18s} {:10} {:6} {:>14} - {:}'
                    else:
                        formatstr = '{:18s} {:10.3f} {:6} {:>14} - {:}'
                    print formatstr.format(alias, value, unit, name, doc)
    
    def get_epicsStore(self, attr):
        """Retrieve attribute from epics store.
        """
        try:
            pvdata = self.ds.env().epicsStore().getPV(attr)
            if pvdata.isCtrl():
                val = None
                print 'Warning: {attr} pv is ctrl'.format(attr=attr)
            else:
                val = pvdata.value(0)
        except:
            val = None
            print 'no pv attribute: ',attr
        return val

    def show_epicsStore_info(self, attrs):
        """Show epicsStore info for a list of attributes.
        """
        if not isinstance(attrs,list):
            attrs = [attrs]
        for attr in attrs:
            value = self.get_epicsStore(attr)
            name = '' 
            unit = ''
            alias = attr
            try:
                if True:
                    print '{:18s} {:10.5g} {:6} {:>14}'.format(alias, value, unit, name)
            except:
                try:
                    print '{:18s} {:>10} {:6} {:>14}'.format(alias, value, unit, name)
                except:
                    print '{:18s} {:10} {:6} {:>14}'.format(alias, 'NA', unit, name)

    @property
    def _pv_dict(self):
        """Dictionary of epicsStore PV's used in PVdictify class,  
           which is accesible from psdata.epics.
        """
        pv_dict = {}
        for pv in  self.ds.env().epicsStore().names():
            name = re.sub(':|\.','_',pv)
            #check if valid -- some old data had aliases generated from comments in epicsArch files.
            if re.match("[_A-Za-z][_a-zA-Z0-9]*$", name):
                func = self.ds.env().epicsStore().getPV(pv)
                pvname = self.ds.env().epicsStore().pvName(pv)
                if pvname:
                    pvalias = pv
                else:
                    pvalias = self.ds.env().epicsStore().alias(pv)
                    pvname = pv

                components = re.split(':|\.|_',pv)
                for i,item in enumerate(components):
                    if item[0].isdigit():
                         components[i] = 'n'+components[i]
                
                pv_dict[name] =  { 'pv': pvname, 
                                   'alias': pvalias,
                                   'components': components,
                                   'func': func}

        return pv_dict

    @property
    def epics(self):
        """Show epics PVs with tabs.
        """
        return PVdictify(self._pv_dict)

    def pvName(self, *args):
        """Get PV name for specified alias name. 
           If specified alias is not found an empty string is returned.
           Wrapper for psana.ds.env().epicsStore().pvName
        """
        pvAliases = args_list_flatten(args) 
        name_func = self.ds.env().epicsStore().pvName
        return [name_func(pvAlias) for pvAlias in pvAliases]

    def pvAlias(self, *args):
        """Get alias name for specified PV name. 
           If specified PV is not found or does not have an alias 
           an empty string is returned.
           Wrapper for psana.ds.env().epicsStore().alias
        """
        pvNames = args_list_flatten(args) 
        alias_func = self.ds.env().epicsStore().alias
        return [alias_func(pvName) for pvName in pvNames]

    def __repr__(self):
        if self.live:
            repr_str = '{:}: {:} -- live'.format(self.__class__.__name__, 
                        self.exp) 
        else:
            repr_str = '{:}: {:}, Run {:}'.format(self.__class__.__name__,
                        self.exp, self.run) 

        return '< '+repr_str+' >'

    def __getattr__(self, attr):
        """Allow data to be accessed by det_key instead of the detector alias,
           but do not make det_key names tab accessible in ipython.
        """
        if attr in self._det_aliases:
            attr = self._det_aliases[attr]
        if attr in self._detector_dir:
            return self._detectors[self._detector_dir[attr]]
        if attr in self._device_sets:
            self.add_detector(attr)
            return self._detectors[self._detector_dir[attr]]

    @property
    def _detector_dir(self):
        """Detector directory used in __dir__ and __getattr__ as a lookup to
           the Detector classes.  Detectors that have data in the current event
           are shown and accessible in upper case as well as the Detector name, 
           which is typically defined as lower case or as Capitalized. 
        """
        detector_dir = {}
        for name in self._detectors:
#            if name in self._evt_dets:
#                detector_dir[name.upper()] = name
            detector_dir[name] = name
        return detector_dir

    def __dir__(self):
        all_attrs = set(self._detector_dir.keys() + 
                        self._device_sets.keys() +
                        self.__dict__.keys() + dir(psdata))
        return list(sorted(all_attrs))


class Detector(object):
    """Build detector from _device_sets configuration dictionary.
       Makes event data and epics data accessible for a detector set.
    """

#    _data_funcs = {'data': 'self.get_data()'}
    _data_funcs = {}
    _pv_funcs = {}
    _user_aliases = {}
    _det_key = None
    _name = None
    _module_attrs = []

    def __init__(self,det,data, **kwargs):
        """Initializes detector set, which may be comprised of 
           epics pv's (e.g., motors) and/or a DAQ detector (e.g., camera).
        """
        self._data = data
        self._name = det
        if det in data._device_sets:
            if 'det' in self._det:
                self._det_key = self._det['det']['det_key']
            if 'desc' in self._det:
                self.desc = self._det['desc']
            else:
                self.desc = self._name
            if 'pvs' not in self._det:
                self._det['pvs'] = {}
            if data._no_epicsStore:
                self._pvs = {attr: EpicsStore(data,val['base']) 
                             for attr, val in self._det['pvs'].items()}
            else:
                self._pvs = {}
            if 'epicsStore' in self._det:
                for attr,pv in self._det['epicsStore'].items():
                    self._pvs[attr] = EpicsStore(data,pv)
                    print 'adding epicsStore', attr

#            device = None
#            if 'device' in data._device_sets[det]:
#                device = data._device_sets[det]['device']
#            if device in data._default_functions:
#                print 'loading default functions', data._default_functions[device]
#                self.load_functions(data._default_functions[device])

        else:
            self.desc = det
                
        self._user_funcs = {}

    @property
    def _det(self):
        return self._data._device_sets[self._name]

    @property
    def config(self):
        """ConfigStore data for detector.
        """
        if hasattr(self._data.configStore, self._name):
            return getattr(self._data.configStore, self._name)
        else:
            return None

    def add_module(self, *args, **kwargs): 
        """Add a detector module.
           For Example:
            > data.gasdet.add_module('gasdet',path='/reg/neh/home1/koglin/src/ana')
            > data.Dg4CsPad.add_module('cspad',geom_file='0-end.data',geom_path='/reg/neh/home1/koglin/')
        """
#        if 'path' in kwargs:
#            path = kwargs['path']
#        else:
#            path = os.getcwd()
#
#        if len(args) > 0:
#            module = args[0]
#        elif 'module' in kwargs:
#            module = kwargs['module']
#
#        if 'path' not in kwargs:
#            path = os.getcwd()
#            kwargs['path'] = path

        if 'module' not in kwargs:
            if len(args) > 0:
                module = args[0]
            kwargs['module'] = module

        if 'module' in kwargs:
            self._data.add_detector(self._name, **kwargs)
#            self._data.add_detector(self._name, module=module, path=path, **kwargs)

    def load_functions(self, module_name, path=None):
        """Load functions from file that operate on the detector class attributes. 
           These functions will be held in self._user_funcs and printed out in self.show_info()
        """
        print self._det, module_name, path
#        try:
        if True:
            if not path:
                path = os.getcwd()
            if not isinstance(path,list):
                path = [path]
            file,filename,desc = imp.find_module(module_name,path)
            funcs = imp.load_module(module_name, file, filename, desc)
            if hasattr(funcs,'_init'):
                getattr(funcs,'_init')(self)
            attrs = [attr for attr in funcs.__dict__ 
                     if not attr.startswith('__')
                     and attr is not '_init'
                     and not hasattr(getattr(funcs,attr),'__base__')]
            for attr in attrs:
                try:
                    print 'Adding', attr, 'to', self._name
                    self.add_function(getattr(funcs,attr))
                except:
                    print 'Error adding', attr, 'to', self._name
        
#        except:
#            print 'ERROR loading ',module_name, ' from ', path, ' for ',self._name

#    def add_hist(self, attr, nbinsx, xlow, xup, name=None, title=None, **kwargs):
#        if not name:
#            name = self._name+'__'+attr
#        if not title:
#            title = 'Histogram of X for {:}'.format(attr, self.desc)
#        hist_dict = {}
#        hist_dict['det'] = self._name
#        hist_dict['attr'] = attr
#        self._data._histograms[name] = ROOT.TH1F(name,title,nbinsx,xlow,xup)

    def add_function(self, func_name, *args, **kwargs):
        """Add a function that operates on this detector object.
                add_function(func_name [, attr])
           The result will be added as an attribute to the detecor with the
           name of the function unless attr is provided.
           For example:
            > def myfunc(self):       
                  return self.ebeamL3Energy
            > data.ebeam.add_function(myfunc, 'energy')

           Or alternatively using lambda:
            > data.ebeam.add_function(lambda self: self.ebeamL3Energy, 'energy')
        """
        if len(args) > 0:
            attr = args[0]
        else:
            attr = func_name.func_name
        self._user_funcs[attr] = func_name 

    def get_function(self,attr):
        """Return a user defined function from self._user_funcs.
        """
        func_name = self._user_funcs[attr] 
        if hasattr(func_name,'__call__'):
            func_name = func_name(self)
        return func_name 

    def del_functions(self, *args):
        """Delete all user defined functions stored in _user_function.
        """
        if len(args) > 0:
            attrs = args
        else:
            self._user_function.clear()

    def add_event_function(self, attr, name=None, nevents=1, *args, **kwargs):
        """Add function that will be performed for every nevents.
        """
        if not name:
            name = self._name+'_'+attr
        
        if hasattr(self, attr):
            self._data._event_functions[name] = {'det': self._name, 
                                                 'attr': attr, 
                                                 'nevents': nevents,
                                                 'kwargs': kwargs} 
        else:
            print 'Error adding event function:  {:} has no function ' \
                  'named {:}'.format(self._name, attr)

    def add_psplot(self, attr, local=True, **kwargs):
        """Update psplot 
        """
        plot_error = '' 

        if 'name' in kwargs:
            name = kwargs['name']
        else:
            name = self._name+'_'+attr
        if 'title' in kwargs:
            title = kwargs['title']
        else:
            if self._desc:
                title = self._desc
            else:
                title = self._name+' '+attr
        if 'ts' in kwargs:
            ts = kwargs['ts']
        else:
            ts = self._data.ievent

        if 'plot_type' in kwargs:
            plot_type = kwargs['plot_type']
        else:
            plot_type = None

        if not plot_error and plot_type not in ['Image','XYPlot']:
            try:
                ndim = getattr(self,attr).ndim
                if ndim == 2:
                    plot_type = 'Image'
                elif ndim == 1:
                    plot_type = 'XYPlot'
                else:
                    plot_error = 'Data with ndim = {:} not valid'.format(ndim)
            except:
                plot_error = 'Data must be numpy array of one or two dimensions.\n'               
        if not plot_error:
            if plot_type is 'Image':
                plt_opts = ['xlabel', 'ylabel', 'aspect_ratio', 'aspect_lock']
                plt_kwargs = {key: item for key, item in kwargs.items() \
                              if key in plt_opts}
                plt_args = {'det': self._name,
                            'attr': attr,  
                            'name': name,
                            'plot_function': Image,
                            'ts': ts,
                            'title': title,
                            'kwargs': plt_kwargs}
#                for key, item in kwargs.items():
#                    if key in plt_opts:
#                        plt_args[key] = item
            
            elif plot_type is 'XYPlot':
                plt_opts = ['xlabel','ylabel','formats']
                plt_kwargs = {key: item for key, item in kwargs.items() if key in plt_opts}
                if 'xdata' in kwargs:
                    xdata = kwargs['xdata']
                else:
                    xdata = range(len(ydata))
                plt_args = {'det': self._name,
                            'attr': attr,
                            'xdata': xdata,
                            'name': name,
                            'plot_function': XYPlot,
                            'ts': ts,
                            'title': title,
                            'kwargs': plt_kwargs}
            else: 
                plot_error = 'Unknown plot type {:} \n'.format(plot_type)

        if plot_error:
            print 'Error adding psplot:' 
            print plot_error
            return None
        else:
#            if name in self._data._psplots[name]:
            print 'psmon plot added -- use the following to view: '
            print '--> psplot -s {:} -p 12301 {:}'.format(os.uname()[1], name)
            print 'WARNING -- see notice when adding for -p PORT specification'
            print '           if default PORT=12301 not available'
            self._data._psplots[name] = plt_args
            if not self._data._publish:
                publish.init()
                self._data._publish = True

            if local:
                subprocess.call('psplot {:} &'.format(name),shell=True)

    def del_psplot(self, name):
        """Remove psplot.
        """
        if name in self._data._psplots:
            self._data._psplots.pop(name)

    def monitor(self, **kwargs):
        """Monitor detector attributes continuously 
           with show_info function.
        """
        self.show_info(monitor=True, **kwargs)

    def show_info(self, attrs=None,
                        next_event=False, 
                        nevents=1, monitor=False, sleep=0.2,
                        is_in_keys=False,
                        no_epics_live=False,
                        no_epicsStore=False,
                        no_data=False,
                        config=False,
                        *args, **kwargs):
        """Show Detector attributes.
        """
        ievent = 0
        try:
            while ievent < nevents or monitor:
                if ievent > 0:
                    time.sleep(sleep)
                    self._data.next_event()

                elif next_event or monitor:
                    self._data.next_event()
                
                while is_in_keys and not self.is_in_keys:
                    self._data.next_event()
                    ievent += 1
                
                ievent += 1
                print ''
                if 'det' in self._det and not no_data and not self._data._no_data:
                    print '='*80
                    print '{:}, Run {:}, Event {:}'.format(self._data.exp, \
                           self._data.run, ievent) 
                    try:
                        EventTime = time.strftime('%H:%M:%S',
                                time.localtime(self._data.EventId.time[0]))
                        EventTime += '.{:04}'.format(int(self._data.EventId.time[1]/1e5))
                        DeltaTime = (self._data.EventId.time[0] \
                                     -self._data._evt_time_last[0]) \
                                   +(self._data.EventId.time[1] \
                                     -self._data._evt_time_last[1])/1.e9
                        if DeltaTime > 0:
                            Rate = '{:8.1f} Hz'.format(1./DeltaTime)
                            DeltaTime = '{:8.4f}'.format(DeltaTime)
                        else:
                            Rate = 'NA'
                            DeltaTime = 'NA'
                    except:
                        EventTime = 'NA'
                        DeltaTime = 'NA'
                        Rate = 'NA'

                    try:
                        eventCodes = self._data.Evr.eventCodes
                    except:
                        eventCodes = ''

                    print '-'*80
                    print '{:} {:} {:} '.format(self.desc, EventTime, Rate), eventCodes
                    if config:
                        self.config.show_info()
                        print '-'*80
                    if self._detector:
                        self._detector.show_info(attrs=attrs)

                if not no_epics_live and self._data._kwargs.get('epics_live') \
                        and 'pvs' in self._det:
                    live_pv_attrs = list(sorted(self._det['pvs'].keys()))
                    if attrs:
                        live_pv_attrs = [attr for attr in live_pv_attrs if attr in attrs] 
                    if live_pv_attrs:
                        print '-'*72
                        print self.desc+': Live Epics PVs'
                        print '-'*72
                        pvs = [self._det['pvs'][attr]['base'] for attr in live_pv_attrs]
                        self._data.show_epics_live_info(pvs,aliases=live_pv_attrs)

                if not no_epicsStore and not self._data._no_epicsStore \
                        and 'epicsStore' in self._det:
                    epics_store_pvs = list(sorted(self._det['epicsStore'].keys())) 
                    if attrs:
                        epics_store_pvs = [attr for attr in epics_store_pvs \
                                           if attr in attrs] 
                    if epics_store_pvs:
                        print '-'*72
                        print self.desc+': Epics Store PVs'
                        print '-'*72
                        pvs = [re.sub(':|\.','_',self._det['epicsStore'][attr]) 
                               for attr in epics_store_pvs]
                        for attr in epics_store_pvs:
                            try:
                                if True:
                                    value = self._pvs[attr].value
                                    print '{:18s} {:10.5g}'.format(attr, value)
                            except:
                                try:
                                    value = self._pvs[attr].value
                                    print '{:18s} {:>10}'.format(attr, value)
                                except:
                                    print '{:18s} NA'.format(attr)
                
        except KeyboardInterrupt:
            pass
    
    @property 
    def is_in_keys(self):
        """Return True if detector is in evt.keys().
        """
        if self._detector:
            return True
        else:
            return False

    def __repr__(self):
        repr_str = '< {:} {:}: {:}>'.format(self._name, self.__class__.__name__,self.desc) 
        print repr_str
        self.show_info()
        return repr_str

    def add_live_pv(self, attr, pv=None):
        """Add a live epics pv. 
           pv keyward only needs to be set if the specified attr 
           is not in the _det['pvs'] dictionary.
        """
        if self._data.get_kwarg('epics_live'):
            if attr in self._det['pvs']:
                pvbase = self._det['pvs'][attr]['base']
            else:
                if not pv:
                    pvbase = attr.split('.')[0]
                    attr = pvbase.replace(':','_')
                else:
                    pvbase = pv.split('.')[0]
            alias = '_'.join([self._name, attr])
            self._data.add_pv(pvbase, alias)
            self._data.add_live_pv(pvbase)
        else:
            print 'WARNING: Epics is not live.' 
            print '         Must be on appropriate machine and epics_live set to True.'

    def show_epics(self, show_all=False):
        """Show epics table.
        """
        pv_dict = {}
        pv_types = {}
        if self._data.get_kwarg('epics_live'):
            for pv in self._det['pvs']:
                pvbase = self._det['pvs'][pv]['base']
                epics_device = self.get_epics_pv(pv)
                rtyp = getattr(epics_device,'RTYP')
                if rtyp not in pv_types:
                    pv_types[rtyp] = []
                pv_types[rtyp].append(pv)

                if show_all:
                    if hasattr(epics_device, '_all_attrs'):
                        attrs = epics_device._all_attrs
                    else:
                        attrs = epics_device._alias.values()
                else:
                    attrs = epics_device._info_attrs
                
                pv_dict[pv] = {attr: epics_device.get(attr, as_string=True) \
                               for attr in attrs}

            for pvtype, pvs in pv_types.items():
                attrs = list(sorted(set(pv_dict[pvs[0]].keys())))
                if 'DESC' in attrs:
                    attrs.remove('DESC')
                    attrs.insert(0, 'DESC')
                
                pline = '{:10}'.format('Attrs')
                wmax = 1
                for pv in pvs:
                    for attr in attrs:
                        wmax = max(wmax, len(pv_dict[pv][attr]))

                column_format = '{:>'+str(min(max(12,140/len(pvs)),wmax+1))+'}'
                for pv in pvs:
                    pline += column_format.format(pv)
                
                print '-'*len(pline)
                print pline
                print '-'*len(pline)
                for attr in attrs:
                    pline = '{:10}'.format(attr)
                    for pv in pvs:
                        pline += column_format.format(pv_dict[pv][attr])
                    
                    print pline
        else:
            print 'No live epics data to show'

    def get_epics_pv(self, attr):
        """Get epics live pv for detector pv alias attribute.
        """
        if attr in self._det['pvs']:
            pvbase = self._det['pvs'][attr]['base']
            if self._data.get_kwarg('epics_live'):
                if pvbase not in self._data._epics_devices:
                    self.add_live_pv(attr)
                
                if pvbase in self._data._epics_devices:
                    return self._data._epics_devices[pvbase]
                
                else:
                    return None
            
            else: 
                return self._pvs[attr]

    @property
    def _det_attrs(self):
        """Detector attributes.  
           Plan to switch to getting them from config instead of evt data.
        """
        if 'det' in self._det and self._detector:
            return self._detector._attr_type
        else:
            return {}

    @property
    def _detector(self):
        """Get Detector data from PsanaDictify Class.
        """
        return self._data.evt._get_det_dict(self._name)

    def _get_det_attr(self, attr):
        """Get Detector attribute from PsanaDictify Class.
        """
        if attr in self._det_attrs:
            return getattr(self._detector, attr)
        else:
            return None

    def __getattr__(self, attr):
        """Return detector attribues from detector functions and  pv aliases.
           Detector functions will be automatically defined for each data type.
        """
        if attr == '_evt_keys':
            print 'Restricted attribute!!!  Returning:  None'
            return None
      
        if self._det.get('det'):
            if attr in self._det_attrs:
                return self._get_det_attr(attr)

            if attr in self._data_funcs:
                return eval(self._data_funcs[attr]) 
            
        if attr in self._det['pvs']:
            return self.get_epics_pv(attr)
            pvbase = self._det['pvs'][attr]['base']
        
        if 'epicsStore' in self._det and attr in self._det['epicsStore']:
            return self._pvs[attr]
        
        if attr in self._pv_funcs:
            return eval(self._pv_funcs[attr]) 
        
        if attr in self._user_funcs:
            return self.get_function(attr)

    def __dir__(self):
        # As noted in epics.device -- there's no cleaner method to do this until Python 3.3
        all_attrs = set(self._det_attrs.keys() +
                        self._det['pvs'].keys() +
                        self._pvs.keys() +
                        self._data_funcs.keys() +
                        self._pv_funcs.keys() +
                        self._user_funcs.keys() +
                        self.__dict__.keys() + dir(Detector))
        return list(sorted(all_attrs))

# read in and write out updated config dict
#for det in device_sets:
#    if 'pvs' in device_sets[det]:
#        device_sets[det]['pvs'] = {alias: {'base': pvbase} for alias, pvbase in device_sets[det]['pvs'].items()}

class EpicsStore(object):
    """Class to retrieve attributes of base pv's from the psana epicsStore.
    """
    _attrs = {}
    _aliases = {'RBV': 'value'}

    def __init__(self, data, base):
        self._data = data
        self._base = base
        if not data._no_epicsStore:
            try:
                self._attrs = {n.strip(base).replace('.','_').replace(':','_').lstrip('_'): n
                               for n in data.ds.env().epicsStore().names() 
                               if n.startswith(base)}
                if base in data.ds.env().epicsStore().names():
                    self._attrs = {'value': base}
                for attr in self._aliases:
                    if attr in self._attrs:
                        self._attrs[self._aliases[attr]] =  self._attrs[attr]
            except:
                print 'EpicsStore not available to load', base

    def _get_pv_attr(self, attr):
        """Retrieve PV from epics store.
           Currently only retrieves the readback value (RBV) of motors.
        """
        try:
            pvdata = self._data.ds.env().epicsStore().getPV(self._attrs[attr])
            if pvdata.isCtrl():
                val = None
                print 'Warning: {attr} pv is ctrl'.format(attr=attr)
            else:
                val = pvdata.value(0)
        except:
            val = None
            print 'no pv attribute: ',attr
        return val

    def __getattr__(self,attr):
        if attr in self._attrs:
            return self._get_pv_attr(attr)
        
#    def __repr__(self):
#        '{:}'.format(self._get_pv_attr('value'))

    def __dir__(self):
        all_attrs = set(self._attrs.keys() + 
                        self.__dict__.keys() + dir(EpicsStore))
           
        return list(sorted(all_attrs))

class PVdictify(object):
    """Dot.dictifies a dictionary of {PVnames: values}.
    """
#    _levels = ['location','region','component','number','field']

    def __init__(self,attr_dict,level=0):
        self._attr_dict = attr_dict
        self._level = int(level)
        self._attrs = list(set([pdict['components'][level] 
                                for key,pdict in attr_dict.items()]))

    def show_info(self):
        """Show information from PVdictionary for all PV's starting with 
           the specified dictified base.
           (i.e. ':' replaced by '.' to make them tab accessible in python)
        """
        print self.get_info()

    def get_info(self):
        """Return string representation of all PV's starting with 
           the specified dictified base.
           (i.e. ':' replaced by '.' to make them tab accessible in python)
        """
        info = ''
#        for key,pdict in self._attr_dict.items():
        items = sorted(self._attr_dict.items(), key=operator.itemgetter(0))
        for key,pdict in items:
            alias = pdict['alias']
            if alias:
                name = alias
                pv = pdict['pv']
            else:
                name = pdict['pv']
                pv = ''

            value = pdict['func'].value(0)
            try:
                info += '{:30s} {:10.4g} -- {:30s}\n'.format(name,value,pv)
            except:
                info += '{:30s} {:>10} -- {:30s}\n'.format(name,value,pv)
        return info

    def __getattr__(self,attr):
        if attr in self._attrs:
            attr_dict = {key: pdict for key,pdict in self._attr_dict.items()
                         if pdict['components'][self._level] in attr}
            if len(attr_dict) == 1:
                key = attr_dict.keys()[0]
                if len(self._attr_dict[key]['components']) == (self._level+1):
                    pvdata = self._attr_dict[key]['func']
                    if pvdata.isCtrl():
                        val = None
                        print 'Warning: {pv} pv is ctrl'.format(pv=pv)
                    else:
                        val = pvdata.value(0)
                    return val
            if len(attr_dict) > 0:
                return PVdictify(attr_dict,level=self._level+1)

    def __repr__(self):
        return self.get_info()

    def __dir__(self):
        all_attrs = set(self._attrs +
                        self.__dict__.keys() + dir(PVdictify))
        return list(sorted(all_attrs))

def initArgs():
    """Initialize argparse arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--exp", type=str, 
                        help='Experiment number')
    parser.add_argument("-r", "--run", type=int, default=-1, 
                        help='Run number')
    parser.add_argument("-i", "--instrument", type=str, 
                        help='Instrument')
    parser.add_argument("-s", "--station", type=int, 
                        help='Station')
    parser.add_argument("--cfg", type=str, 
                        help='psana cfg config file')
    parser.add_argument("--h5", action="store_true", 
                        help='Use hdf5 data instead of xtc')
    parser.add_argument("--xtc_dir", type=str, 
                        help='xtc file directory')
    parser.add_argument("-l", "--live", action="store_true", 
                        help='Use live data stream')
    parser.add_argument("-f", "--ffb", action="store_true", 
                        help='Use FFB data')
    parser.add_argument("-z", "--epics_live", action="store_true", 
                        help='Use live epics')
    parser.add_argument("--quick_alias", action="store_true", 
                        help='Use quick alias in interactive python')
    parser.add_argument("--epics_file", type=str, 
                        help='epics alias file with epicsArch style file')
    parser.add_argument("--epics_dir", type=str, 
                        help='dir for epics_file used for epics aliases')
    parser.add_argument("--no_epics_aliases", action="store_true", 
                        help='Do not make epics aliases available')
    parser.add_argument("--show_errors", action="store_true", default=False,
            help='Show Errors in cases that might not be explicit due to try/except statements')
    parser.add_argument("--indexed", action="store_true", default=False, 
            help='Use indexing, see: https://confluence.slac.stanford.edu/display/PSDM/psana+-+Python+Script+Analysis+Manual#psana-PythonScriptAnalysisManual-RandomAccesstoXTCFiles("Indexing")')
    parser.add_argument("-b", "--base", type=str, 
                        help='Base into which psdata is loaded.')
    parser.add_argument("-c", "--config_file", type=str, 
                        help='File with configuration dictionary.')
    parser.add_argument("--noload", action="store_true", 
                        help='Do not load psana data')
    parser.add_argument("--iocrc", type=str, 
                        help='Use local file of controls camera, xtc_dir="/reg/d/camera/{iocrc}/daq/xtc/')
    parser.add_argument("-P", "--monshmserver", type=str, default='psana', 
                        help='-P monshmserver flag used in cnf file for live data')
    parser.add_argument("-n", "--nstart", type=int, default=2, help='Number of Events to load on start')
#    parser.add_argument("-d", "--det_list", type=str, help='List of detectors if nevents set')
    return parser.parse_args()

if __name__ == "__main__":
    args = initArgs()
    print "*"*80
    print 'Loading psdata with the following arguments:'
    for attr,val in vars(args).items():
        print "   {:} = {:}".format(attr, val)
    print "*"*80
    base_default = 'data'
    if True:
#    try:
        if args.exp and not args.instrument:
            args.instrument = args.exp[0:3]
        
        if not args.base:
            if args.instrument:
                args.base = args.instrument
            else:
                args.base = instrument_guess()
#                args.base = base_default

        setattr(sys.modules['__main__'], args.base, psdata(**vars(args)))

#        if base is base_default and args.instrument:
#            setattr(sys.modules['__main__'], args.base, 
#                    getattr(sys.modules['__main__'], base))
        
        run_info = getattr(sys.modules['__main__'], args.base)
#        if getattr(getattr(sys.modules['__main__'], args.base),'live'):
#            run_info += ' -- Live Data from Shared Memory'
        print ""
        print "*"*80
        print run_info
        print "*"*80
#    except:
#        print "*"*80
#        print "*"*80
#        print 'ERROR loading psdata'
#        print "*"*80
#        print "*"*80
#    if args.nevents:
#        data.get_events(args.nevents,det_list=args.det_list)



