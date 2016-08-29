#import standard python system tools
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
import atexit
import traceback

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
#import psami

from psmon import publish
publish.client_opts.daemon = True
from psmon.plots import Image, XYPlot, MultiPlot

from PsanaDictify import * 
from DetectorDictify import DetectorDictify
import psioc
import lcls_devices
import psutils

_lcls_instruments = ['amo','sxr','xpp','xcs','cxi','mec','xrt']
_default_exp = {'exp': 'cxitut13', 'run': 22}

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
        return
    except Exception as err:
        print 'import_module error', err
        traceback.print_exc()

    sys.exit()

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

class psdata(object):
    """Class to organize psana data according to detector sets and make it conveniently
       accessible in ipython.
    """

    _default_modules = {
            'device': {
                'Evr': 'evr', 
                'Imp': 'imp',
#                'Acqiris': 'acqiris',
                'Epix': 'epix100',
                'Cspad': 'cspad',
                'Cspad2x2': 'cspad2x2',
                'Tm6740': 'pim',
                'Opal1000': 'camera',
                'Opal2000': 'camera',
                'Opal4000': 'camera',
                'Opal8000': 'camera',
                },
             'det_key': {
                'XrayTransportDiagnostic_0_Opal1000_0': 'xtcav_det',
#                'CxiDsu_0_Opal1000_0': 'timetool',     
                },
            }

    _default_functions = {'Acqiris': 'acqiris'}
    _instruments = _lcls_instruments
    _exp_defaults = {'instrument':None, 
                     'live':None, 
                     'exp':None, 
                     'h5':None,
                     'run':0, 
                     'station':None,
                     'indexed':None,
                     'idx':None,
                     'smd':None,
                     'ffb':None,
                     'cfg':None}
    _no_evtData = False 
    _epics_live = False
    _publish = None
    _evr_alias = None

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
        self._detectors = {}
        self._det_list = [] 
        self._det_aliases = {}
        self._psplots = {}
        self._event_functions = {}
        self._source_attrs = []
        self._evt_time_last = (0,0)
        self.ievent = 0
        self._reloadOnLoadRun = False
        self._reloadOnNextEvent = False
        self.psana_cfg_dict = {}
        self._default_module_path = ''

#        self._user_attrs = {}
#        self._histograms = {}
        
        for key in kwargs:
            self._kwargs[key] = kwargs[key] 
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
                        det_key = self._device_sets[det]['det']['det_key']
                        self._det_aliases[det_key] = det 
            else:
                pass
            
#            if 'pvs' in self._device_sets[det]:
#                for attr in self._device_sets[det]['pvs']:
#                    pvbase = self._device_sets[det]['pvs'][attr]['base']
#                    alias = '_'.join([det,attr])
#                    self.add_pv(pvbase, alias)

        self.set_exp_defaults(**kwargs)
        if not self._kwargs.get('noload'):
            self.data_source = self.get_data_source(**kwargs)
            print 'Data Source = ', self.data_source
        else:
            self.data_source = None

        if not self.data_source:
            self._kwargs['noload'] = True
        else:
            kwargs['run'] = self.run

#        if self._kwargs.get('noload') or self.live:
#            if self._kwargs.get('epics_live'):
#                self.set_kwargs(ami=True)
        
        if self._kwargs.get('ami'):
            print 'loading ami'
            self.load_ami(**kwargs)

        if not self._kwargs.get('noload'):
            print 'loading run'
            self.load_run(*args, **kwargs)
            self._no_epicsStore = False
    
        print 'Instrument = ', self.instrument

        if self._kwargs.get('epics_live'): # and self._kwargs.get('epics_file'):
            print 'loading epics'
            self.load_epicsLive(**kwargs)

        if self.ds and self.live:
            self.next_event()
        
        if self.ds and self._reloadOnNextEvent:
            self.next_event()
                
        if not self.ds:
            self._no_epicsStore = True
            self._no_evtData = True
            for det in self._device_sets:
                if 'pvs' in self._device_sets[det]:
                    print 'Adding epics ',det
                    self.add_detector(det)

    def load_epicsLive(self, instrument=None, **kwargs):
        """Load live epics data from the EpicsSets class in 
           the lcls_devices module.
           This is based on pyepics3 devices:
              see:  http://cars9.uchicago.edu/software/python/pyepics3
        """
#        if 'instrument' in kwargs:
#            instrument = kwargs.get('instrument')
#            self.instrument = instrument
        if not instrument:
            instrument = self.instrument

        self.ioc = psioc.IOC(instrument=self.instrument)
        if self.instrument in ['cxi', 'mfx', 'xcs', 'mec']:
            self.ioc.load_cfg('xrt')
        
        print 'Loading EpicsSets for', instrument
        self.epicsLive = lcls_devices.EpicsSets(instrument=instrument, **kwargs)
        self.update_epicsLive()

    def update_epicsLive(self):
        for det in self.epicsLive._sets:
            if det not in self._detectors:
                self.add_detector(det)
            
            aliases = self.epicsLive._sets[det]._aliases
            if 'epicsLive' not in self._device_sets[det]:
                self._device_sets[det]['epicsLive'] = {}
            
            self._device_sets[det]['epicsLive'].update({'attrs': aliases})

    def load_daq(self, instrument=None, station=None, **kwargs):
        """Load daq.
        """
        import psdaq
        if not instrument:
            instrument = self.instrument
        
        if station is None:
            station = self.station

        self.daq = psdaq.psdaq(instrument=instrument, station=station, **kwargs)

    def load_ami(self, **kwargs):
        """Load ami from proxy host.
        """
        import psami
        proxy_nodes = ['daq-{:}-mon{:02}'.format(self.instrument,num+1) \
                       for num in range(6)]
        
        proxy_host = kwargs.get('proxy_host', None)
        if not proxy_host and hasattr(self, '_kwargs'):
            proxy_host = self._kwargs.get('proxy_host')

        if proxy_host:
            proxy_nodes.insert(0,proxy_host)

        for proxy_host in proxy_nodes:
            try:
                self.ami = psami.Ami(proxy_host)
                print 'Loading ami from:',proxy_host
                break
            except:
                print 'Cannot load ami from', proxy_host
                pass

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

#    def get_kwarg(self, arg):
#        """Get argument from keyword arguments set during loading of psdata.
#        """
#        return self._kwargs.get(arg)
#
#    def set_kwargs(self, reset=False, **kwargs):
#        """Store keywarg arguments set during loading.
#           These arguments can be retrieved with get_kwarg(arg).
#        """
#        if reset:
#            self._kwargs = {}
#        for arg in kwargs:
#            self._kwargs[arg] = kwargs[arg] 

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
        """Sets experiment defaults based on kwargs, guesses (using psutils) and defaults.
        """
        default_exp = False
        for key in kwargs:
            if key in self._exp_defaults:
                setattr(self,key,kwargs[key])
        
        if self.exp is not None:
            self.instrument = self.exp[0:3]
        if self.instrument is None:
             self.instrument = psutils.instrument_guess()

        if self.station is None:
            station = 0
        else:
            station = self.station

        inst_id = '{:}:{:}'.format(self.instrument.upper(),  station)

        if self.exp is None or self.live is True:
            if psutils.live_source(monshmserver=self.monshmserver) is not None:
                self.live = True
                self.exp = psutils.active_experiment(inst_id)
                self.run = 0
                self.h5 = False
                self.indexed = False
            else:
                self.live = False
                if self.ffb:
                    self.indexed = True
                else:
                    self.indexed = True
                if self.exp is None:
                    self.exp = psutils.experiment_guess(instrument=self.instrument)

        if self.exp.startswith('dia'):
            self.instrument = self.exp[3:6]
            self.indexed = False
        else:
            self.instrument = self.exp[0:3]

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

        if self._kwargs.get('iocrc'):
            if self._kwargs.get('iocrc') in 'local':
                host = os.uname()[1]
            else:
                host = self._kwargs.get('iocrc')
            
            self.xtc_dir = "/reg/d/cameras/{:}/daq/xtc".format(host)

        if self.exp.startswith('dia'):
            folder = 'dia'
        else:
            folder = self.instrument
        
        if self.xtc_dir:
            default_dir = True
        else:
            self.xtc_dir = "/reg/d/psdm/{:}/{:}/xtc".format(folder, self.exp)
            default_dir = True
        
        if not self.h5_dir:
            self.h5_dir = "/reg/d/psdm/{:}/{:}/hdf5".format(folder, self.exp)

        if self.live:
            data_source = psutils.live_source(monshmserver=self.monshmserver)
        
        else:
#            if len(self.runs) == 0:
#                self.exp = _default_exp['exp']
#                self.run = _default_exp['run']
#                self.instrument = self.exp[0:3]
##                self.runs = experiment_info.experiment_runs(self.instrument.upper(),self.exp)
#                print 'No runs taken yet for ',self.exp
#                print 'Using default experiment {exp} and run {run}'.format(
#                        exp=self.exp,run=self.run)

            if len(self.runs) > 0 and self.run > len(self.runs):
                print 'Run number {:} too large'.format(self.run)
                print 'Looking to load last run from experiment {:}'.format(self.exp)
                self.run = -1
            
            if len(self.runs) > 0 and self.run <= 0:
                while -self.run < len(self.runs)-1 and \
                        len(self.runs[-1+self.run].get('xtc_files',[])) == 0:
                    self.run -= 1
                
                if self.run:
                    self.run = self.runs[self.run]['num']
                else:
                    self.run = 0

                if len(self.runs[-1+self.run].get('xtc_files',[])) == 0:
                    data_source = None
                    self._kwargs['noload'] = True
            
            if self.run <= 0:
                data_source = None
                self._kwargs['noload'] = True
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
                        if self.idx:
                            data_source += ":idx"
                            self.smd = False
                        else:
                            data_source += ":smd"

                    if self.xtc_dir and not default_dir and not self.h5:
                        data_source += ":dir={:}".format(self.xtc_dir)
                except:
                    data_source = None
                    self._kwargs['noload'] = True
                    print 'No data source'

        return data_source

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

    def setOptions(self):
        """Set psana cfg options from psana_cfg_dict.
           these may be set by custom Detector classes added with add_module
           in this case set _reloadOnLoadRun flag
        """
        psana_modules = ' '.join(self.psana_cfg_dict.keys())
        self.cfg_setOptions = {'psana.modules': psana_modules}
        for module, params in self.psana_cfg_dict.items():
            for attr, val in params.items():
                self.cfg_setOptions[module+'.'+attr] = val

        psana.setOptions(self.cfg_setOptions)

    def load_run(self, reload=False, *args, **kwargs):
        """Load run for experiment.
           Optionally pass 
        """
        if 'data_source' in kwargs:
            data_source = kwargs['data_source']
        else:
            data_source = self.get_data_source(*args, **kwargs)
       
        if data_source:
#            try:
            if True:
                self.data_source = data_source
                if self.psana_cfg_dict:
                    self.setOptions()
                elif self.cfg:
                    # if a cfg file is specified it will be loaded
                    # however, the cfg_setOptions takes precidence
                    # in future may try combind the two.
                    psana.setConfigFile(self.cfg)

                calibDir = '/reg/d/psdm/cxi/{:}/calib'.format(self.exp)
                print 'setting calibDir', self.exp, calibDir
                psana.setOption('psana.calib-dir', calibDir)

                print 'Loading data from ',data_source
                if self.ds and self.live:
                    print 'WARNING:  Currently Cannot reload live shared memory'
                    print '          Need to exit python to reload'
                else:
                    self.ds = psana.DataSource(data_source)
                    self._no_evtData = False

                self._ds_run = self.ds.runs().next()

                _source_attrs = ['ds','events','evt']
                if self.indexed:
                    self.times = self._ds_run.times()

                self.events = self._ds_run.events()
                self.configStore = PsanaDictify(self._ds_run.env().configStore())
                self.evrConfig = EvrDictify(self.configStore)
                self.load_epicsStore()

#                self.daqEventCodes = [ec.code() for ec in self.configStore.evr0.eventcodes] 
                self.ievent = 0
                if not reload and self._kwargs.get('nstart'):
                    for i in range(self._kwargs.get('nstart')-1),:
                        self.next_event()
                
#            except:
#                print 'Failed to load data source "{:}"'.format(data_source)
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

        if self._reloadOnLoadRun:
            self._reloadOnLoadRun = False
            self.load_run(reload=True)

    def load_epicsStore(self, **kwargs):
        """Load epics store
        """
        self.epicsStore = EpicsDictify(self._ds_run)
        dets = set([a['alias'].split('_')[0] for a in self.epicsStore._pv_dict.values() \
                if a and a.get('alias')]) 
        for det in dets:
            if det and det not in self._device_sets:
                self.add_detector(det)
            det_class = getattr(self.epicsStore, det)
            if det_class:
                aliases = {item['components'][1]: item['pv'] \
                           for alias, item in det_class._attr_dict.items()}
                self._device_sets[det].update({'epicsStore': {'attrs': aliases}})

    def add_detector(self, det, module=None, path=None, empty=False, 
                     device=None, pvs=None, desc=None, parameters={}, **kwargs):
        """Add a detector module and update _device_sets configuration.
           Overwrites any existing detector module.
           Optionally add a dictionary of pvs with aliases.
           Optionally pass 'parameters' that are stored in _device_sets
             and tab accessible.
        """
        initialized = False

#        if empty or pvs or (self.epicsLive and hasattr(self.epicsLive, det)) \
#                        or (self.epicsStore and hasattr(self.epicsStore, det)):
        if det not in self._device_sets:
            self._device_sets[det] = {}
            if not desc:
                desc = det

        if pvs:
            if self._kwargs.get('epics_live'):
                if isinstance(pvs, dict):
                    pv_dict = {'_'.join([det,pvalias]): pvbase for pvalias,pvbase in pvs.items()}
                else:
                    if not isinstance(pvs, list):
                        pvs = [pvs]
                    
                    pv_dict = {det: pv for pv in pvs}

                self.epicsLive.add_device(**pv_dict)
            
            aliases = self.epicsLive._sets[det]._aliases
            if 'epicsLive' not in self._device_sets[det]:
                self._device_sets[det]['epicsLive'] = {}
            
            self._device_sets[det]['epicsLive'].update({'attrs': aliases})


#                self._device_sets[det]['pvs'] = {}
#                for alias, pv in pvs.items():
#                    pvbase = pv.rsplit('.')[0] 
#                    attr = '_'.join([det, alias.lstrip(det).lstrip('_')])
#                    print attr, pv, pvbase
#                    self.add_pv(pvbase, attr)
        
        if det in self._device_sets:
            det_dict = self._device_sets[det]
            
            if desc:
                det_dict.update({'desc': desc})

            if 'parameters' not in det_dict:
                self._device_sets[det]['parameters'] = {}

            self._device_sets[det]['parameters'].update(parameters)

            if module:
                module = module.split('.')[0]

            # First check for device configuration
            if 'module' in det_dict:
                module_name = det_dict['module']['name']
                if 'path' in det_dict['module']:
                    module_path = det_dict['module']['path']
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
                    det_dict['module'] = {}
                
                module_name = module
                det_dict['module']['name'] = module

            # Use defaults if not set by keyword or in device config
            if 'det' in det_dict and 'det_key' in det_dict['det']:
                det_key = det_dict['det']['det_key']
            else:
                det_key = None

            if not device and det_dict.get('det') and det_dict['det'].get('devName'):
                device = det_dict['det']['devName']

            det_dict['device'] = device

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
                    det_dict['module']['path'] = path
        
                if module_path:
                    print 'Using the path {module_path} for {module_name}'.format( \
                           module_path=module_path, module_name=module_name)
                else:
                    module_path = self._default_module_path

                import_module(module_name, module_path)
                try:
                    new_class =  getattr(globals()[module_name],module_name)
                except:
                    new_class =  getattr(globals()[module_name],module_name.capitalize())

                print 'Loading {det} as {new_class} from {module_path}'.format(
                       det=det,new_class=new_class,module_path=module_path)
                nomodule = False
                self._detectors[det] = new_class(det,self, **kwargs)
                initialized = True

            if is_default_class:
                print 'Loading {det} as standard Detector class'.format(det=det)
                self._detectors[det] = Detector(det,self)
                initialized = True

            path = [os.getcwd()]
            function_files = []
            if device in self._default_functions:
                function_files.append(self._default_functions[device])

            if 'functions' in det_dict:
                function_files.append(det_dict['functions']['file'])
                if 'path' in det_dict['functions']:
                    path.append(det_dict['functions']['path'])

#            for file in function_files:
##                try:
#                print 'Loading functions for ',det
#                load_func = getattr(self._detectors[det],'load_functions')
#                load_func(file,path=path)
##                except:
##                    print 'FAILED Loading functions for ',det, 'from', file, 'in', path
#
            if initialized and self._kwargs.get('quick_alias'):
                print 'Making quick alias for ',det
                setattr(sys.modules['__main__'], det, self._detectors[det])

        else:
            print 'ERROR:  Need to add ',det,' information to _device_sets.'

    def get_evt_data(self,det_list=None):
        """Returns dictionary of data results.
           If evt_keys dictionary provided only load data from thoses
           event keys.
           Name mangle and return as pandas series.
        """
        data = {} 
        if not det_list:
            det_list = self._det_list
#            det_list = list(set([self._det_aliases[evt_key['det_key']] 
#                                 for evt_key in self._evt_keys]))
       
        for det_name in det_list:
            det = getattr(self, det_name)
            if not det._book_attrs:
                det._set_book_attrs()
            if det.is_in_keys:
                for attr in det._book_attrs:
                    data['__'.join([det_name,attr.replace('.','__')])] = \
                            psutils.getattr_complete(det, attr)

        return pd.Series(data) 

#    def set_book_attrs(self):
#        """Auto set book attrs.
#        """
#        for det_name in det_list:
#            det = getattr(self, det_name)
#            if not det._book_attrs:
#                det._set_book_attrs()
#            if det.is_in_keys:

    def get_events(self,nevents,**kwargs):
        """Get Number of specified events and return as Pandas DataFrame.
        """
        vdata = []

        if not self.evt:
            t = self.next_event()

        for i in range(0,nevents):
            if i % 100 == 99:
                print 'Getting Event',i+1
            vdata.append(self.get_evt_data(**kwargs))
            t = self.next_event()
            if not t:
                break

        return pd.DataFrame(vdata) 

    def next_run(self):
        """Shortcut to load next run for same experiment.
        """
        self.load_run(run=self.run+1)

    def goto_next_event(self, eventCode=None, **kwargs):
        self.next_event(**kwargs)
        ievent0 = self.ievent
        while not self.is_eventCodePresent(eventCode):
            self.next_event(**kwargs)

        print self.event_info
        print '{:} events skipped'.format(self.ievent-ievent0)

    def next_event(self, *args, **kwargs):
        """Load next event and update _evt_keys for all detectors.
           Add any detectors that were not already defined.
        """
        if not self._no_evtData and self.ds:
            if hasattr(self, 'EventId'): 
                if hasattr(self.EventId,'time'):
                    self._evt_time_last = self.EventId.time
            
            if self._reloadOnNextEvent:
                self.load_run(reload=True)

            if self.indexed:
                if len(args) > 0:
                    evt_time = args[0]
#                    print 'Warning!!! Using indexed timestamps under development'
                    try:
                        self._evt = self._ds_run.event(evt_time)
                        self.evt = PsanaDictify(self._evt)
                        self.ievent += 1
                    except:
                        print 'Invalid Event Time Stamp'
                else:
                    self.ievent +=1
                    if self.ievent >= len(self.times):
                        print 'No more events in run.'
                        print ' -- to reload {:}.load_run()'.format(self._kwargs.get('base'))
                    else:
                        self._evt = self._ds_run.event(self.times[self.ievent])
                        self.evt = PsanaDictify(self._evt)
                        for kwarg,val in kwargs.items():
                            if (kwarg not in self.evt._alias_dict.values() and val is True) \
                                    or (kwarg in self.evt._alias_dict.values() and val is False):
                                self.evt = PsanaDictify(self._ds_run.event(self.times[self.ievent]))
                                self.ievent += 1

            else:
#                print 'getting event'
                try:
                    self._evt = self.ds.events().next()
                except:
                    return None

                self.evt = PsanaDictify(self._evt)
                self.ievent += 1
                for kwarg,val in kwargs.items():
                    if (kwarg not in self.evt._alias_dict.values() and val is True) \
                            or (kwarg in self.evt._alias_dict.values() and val is False):
                        self._evt = self.ds.events().next()
                        self.evt = PsanaDictify(self._evt)
#                        print 'getting event'
                        self.ievent += 1
            
            for det, key_dict in self.evt._keys_dict.items():
                if det not in self._device_sets:
                    self._device_sets[det] = {}
                self._device_sets[det].update({'det': key_dict['det']})
                if det not in self._det_aliases.values():
                    det_key = key_dict['det']['det_key']
                    self._det_aliases[det_key] = det
                    self._det_list.append(det)
#                    print 'adding', det
                    self.add_detector(det)

            if hasattr(self, 'EventId'): 
                if hasattr(self.EventId,'run'):
                    self.run = self.EventId.run

        self._reloadOnNextEvent = False
        self.exec_event_functions()
        
        if self._publish:
            self.psmon_publish()

        return self.EventId.time

    @property
    def detectors(self):
        return  DetectorDictify(self._evt, self.ds.env())

    @property
    def _master_evr(self):
        """Master evr from psana evt data.
        """
        if not self._evr_alias:
            self._set_master_evr()

        return getattr(self, self._evr_alias)
            
    def _set_master_evr(self, alias=None):
        """Set the maste evr.  By default automated as there should only be one in the evt keys.
        """
        if alias:
            self._evr_alias = alias
            return alias
        else:
            for key,item in self.evt._keys_dict.items():
                if item['det'].get('devName') == 'Evr':
                    self._evr_alias = key
                    return key

    @property
    def event_info(self):
        """
        """
        try:
            EventTimeStr = time.strftime('%H:%M:%S',
                    time.localtime(self.EventId.time[0]))
            EventTimeStr += '.{:04}'.format(int(self.EventId.time[1]/1e5))
            DeltaTime = (self.EventId.time[0] \
                         -self._evt_time_last[0]) \
                       +(self.EventId.time[1] \
                         -self._evt_time_last[1])/1.e9
            if DeltaTime > 0:
                RateStr = '{:8.1f} Hz'.format(1./DeltaTime)
                DeltaTimeStr = '{:8.4f}'.format(DeltaTime)
            else:
                RateStr = '   NA'
                DeltaTimeStr = 'NA'
        except:
            EventTimeStr = 'NA'
            DeltaTimeStr = 'NA'
            RateStr = '   NA'

        try:
            eventCodeStr = '{:>15}'.format(self._master_evr.eventCodes)
        except:
            eventCodeStr = '{:>15}'.format('')

        return  eventCodeStr+', {:}, Run {:}, Event {:}, '.format(self.exp, self.run, 
                    self.ievent)+EventTimeStr+RateStr

    def is_eventCodePresent(self, *args):
        """Check if the event has specified event code.
           Multiple event codes can be tested.
           e.g., 
              assume: 
                _master_evr.eventCodes = [41, 140]
              then:
                is_eventCodePresent(41, 140) = True
                is_eventCodePresent(42, 140) = Flase
            
            To check if an event code is not present use a negative number:
            e.g., 
                is_eventCodePreset(-41) = False
                is_eventCodePreset(-41, 140) = False
                is_eventCodePreset(-42) = True
                is_eventCodePreset(-42, 140) = True
                is_eventCodePreset(-42, 41, 140) = True
        """
        if args[0] is None:
            return True

        if len(args) == 1:
            if isinstance(args[0], list):
                eventCodes = {arg for arg in args[0]}
            else:
                eventCodes = args
        else:
            eventCodes = args
        
        for eventCode in eventCodes:
            if eventCode > 0:
                if hasattr(self,'_master_evr') and \
                        (not self._master_evr.is_in_keys \
                         or not self._master_evr.present(eventCode)):
                    return False
            elif eventCode < 0:
                if hassattr(self,'_master_evr') and not self._master_evr.is_in_keys: 
                    return True
                elif self._master_evr.present(-eventCode):
                    return False
            else:
                return False

        return True

    def exec_event_functions(self):
        """Execute event functions added at the detector level with
           Detector.add_event_function() 
        """
        for name, fdict in self._event_functions.items():
            exec_func=False
            if self.is_eventCodePresent(fdict['eventCode']) \
                     and (self.ievent % fdict['nevents']) == 0:
                exec_func = True
            
            det_class = psutils.getattr_complete(self,fdict['det'])
            
            if exec_func and det_class.is_in_keys:
#                print 'executing',det_class._name, fdict['attr']
                func = psutils.getattr_complete(det_class,fdict['attr']) 
                func(**fdict['kwargs'])
#            try:
#            if True:
#            except:
#                print 'Error -- not able to execture event function: ', name
#                print 'see _event_functions[func] for details on function'

#    def draw_histograms(self, attrs):

    def psmon_publish(self, force=False):
        """Publish _psplots.
        """
        if force or self.exp.startswith('dia') or (self.evt and self._master_evr.is_in_keys):
            for name, psmon_args in self._psplots.items():
                det_class = getattr(self,psmon_args['det'])
                
                if self.evt:
                    eventCode = psmon_args['pubargs'].get('eventCode')
                    ok_eventCode = self.is_eventCodePresent(eventCode)
                else:
                    eventCode = None
                    ok_eventCode = True

                if not self.evt or (getattr(det_class,'is_in_keys') and ok_eventCode):
                    print 'publish', name, eventCode, ok_eventCode
                    psplot_func = psmon_args['plot_function']
                    if psplot_func is Image:
                        image = psutils.getattr_complete(det_class,psmon_args['attr'][0])

                        psmon_fnc = psplot_func(
                                        self.event_info,
#                                        'Test',
                                        psmon_args['title'],
                                        image, 
                                        **psmon_args['kwargs'])
                    elif psplot_func is XYPlot:
                        ydata = [psutils.getattr_complete(det_class, attr) for attr in psmon_args['attr']]
                        psmon_fnc = psplot_func(self.event_info,
                                        psmon_args['title'],
                                        psmon_args['xdata'],
                                        ydata,
                                        **psmon_args['kwargs'])

                    publish.send(name,psmon_fnc)

    def del_psmon(self, *attrs):
        """Delete psmon plot.
        """
        if len(attrs) == 0:
            attrs = self._psplots.keys()
        for attr in attrs:
            item = self._psplots.pop(attr, None)
            subproc = item['subprocess']
            subproc.poll()

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

    def __init__(self,det,data, **kwargs):
        """Initializes detector set, which may be comprised of 
           epics pv's (e.g., motors) and/or a DAQ detector (e.g., camera).
        """
        self._data = data
        self._name = det
        self._module_attrs = []
        self._book_attrs = []
        if det in data._device_sets:
            if 'desc' in self._det:
                self.desc = self._det['desc']
            else:
                self.desc = self._name
            
        else:
            self.desc = det
                
        self._user_funcs = {}

    def _set_book_attrs(self):
        if self.evtData:
            self._book_attrs = [attr for attr in self.evtData._attrs if not attr[0].isupper()]

    @property
    def _det(self):
        return self._data._device_sets[self._name]

    @property
    def src(self):
        try:
            return self._det['det']['__str__']
        except:
            return None

    def set_parameter(self, **kwargs):
        for param, value in kwargs.items():
            setattr(self, param, value)
            self._det['parameters'][param] = value 

    @property
    def configStore(self):
        """ConfigStore data for detector.
        """
        return getattr(self._data.configStore, self._name)

    @property
    def evrConfig(self):
        """DAQ Evr info from configStore.
        """
        return getattr(getattr(self._data.evrConfig, self._name), 'evr')

    @property
    def evtData(self):
        return getattr(self._data.evt, self._name)

    @property
    def _evtData_attrs(self):
        if self._det.get('det'):
            attrs = self._det['det']['types'].keys()
            for attr in self._det['det']['attr_type'].keys():
                attrs.append(attr)
        else:
            attrs = []
            
        return attrs 

    @property
    def detector(self):
        """Dictified psana Detector class contains a collection
           of psana methods to access detector associated information
           including where relevant, pedestal from the calibStore,
           masks, common mode correction, and image generation.
        """
        return getattr(self._data.detectors, self._name)

    @property
    def epicsStore(self):
        return  getattr(self._data.epicsStore, self._name)

    @property 
    def _epicsStore_attrs(self):
        if self._det.get('epicsStore'):
            return self._det['epicsStore']['attrs'].keys()
        else:
            return []

    @property
    def epicsLive(self):
        return getattr(self._data.epicsLive, self._name)
   
    @property
    def _epicsLive_attrs(self):
        """Get epicsLive attrs.
        """
        if self._det.get('epicsLive'):
#            return self.epicsLive._attrs
            return self._det['epicsLive']['attrs'].keys()
        else:
            return []

    @property
    def _detectors_attrs(self):
        """Get included detector attributes.
        """
        if self._det.get('detectors'):
            return self._det['detectors'].keys()
        else:
            return []

    @property
    def parameters(self):
        if self._det.get('parameters'):
            return self._det['parameters']
        else:
            return {}

    @property
    def ami(self):
        """Ami for detector if present.
        """
        return getattr(self._data.ami, self._name, None)

    def add_psana_options(self, cfg_dict):
        """Add a psana config dictionary.
        """
        try:
            self._data.psana_cfg_dict.update(cfg_dict)
            self._data._reloadOnNextEvent = True
        except:
            print 'Invalid config dictionary to add to psana options'

    def del_psana_options(self, keys):
        """Delete psana config dictionary keys.
        """
        try:
            for key in keys:
                self._data.psana_cfg_dict.pop(key, None)
        except:
            print 'Invalid keys to remove from psana options:', keys

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

#        if 'module' in kwargs:
        if len(kwargs) > 0:
            self._data.add_detector(self._name, **kwargs)
#            self._data.add_detector(self._name, module=module, path=path, **kwargs)

    def include_detector(self, name, module=None, alias=None, **kwargs):
        """Include a different detector in this detector module.
           e.g., to make the sequencer conveniently available:
                self.include_detector('sequencer', module='sequencer')
        """
        if module or not getattr(self._data, name):
            self._data.add_detector(name, module=module, **kwargs)

        if not alias:
            alias = name
            
#        setattr(self, alias, getattr(self._data, name))

        if not self._det.get('detectors'):
            self._det['detectors'] = {}
        
        self._det['detectors'].update({alias: name})

    def load_functions(self, module_name, path=None):
        """Load functions from file that operate on the detector class attributes. 
           These functions will be held in self._user_funcs and printed out in self.show_info()
        """
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

    def add_device(self, noInit=True, **kwargs):
        """Add epics devices by keyward assignment.
           e.g., to load and asign the ims motor pv='CXI:SC1:MMS:02' to the attribute self.x 
                self.add_device(x='CXI:SC1:MMS:02')
           
           To add a dictionary of {alias: pv},
                epics_devices = {
                        'x': 'CXI:PI1:MMS:01',
                        'y': 'CXI:PI1:MMS:02', 
                        'z': 'CXI:PI1:MMS:03', 
                        }
                self.add_device(**epics_devices)
        """
        self.epicsLive.add_device(noInit=noInit, **kwargs)
        aliases = self.epicsLive._aliases
        if not self._det.get('epicsLive'):
            self._det['epicsLive'] = {}
        self._det['epicsLive'].update({'attrs': aliases})
 
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

    def add_event_function(self, attr, name=None, 
            nevents=1, eventCode=None,  
            *args, **kwargs):
        """Add function that will be performed for every nevents.
        """
        if not name:
            name = self._name+'_'+attr
        
        if hasattr(self, attr):
            self._data._event_functions[name] = {'det': self._name, 
                                                 'attr': attr, 
                                                 'nevents': nevents,
                                                 'eventCode': eventCode,
                                                 'kwargs': kwargs} 
        else:
            print 'Error adding event function:  {:} has no function ' \
                  'named {:}'.format(self._name, attr)

    def del_event_function(self, all=False, *attrs):
        """Delete event function.
        """
        if all:
            attrs = [f for f in self._data._event_functions if f.startswith(self._name)]

        for attr in attrs:
            if attr.startswith(self._name):
                self._data._event_functions.pop(attr)
            else:
                self._data._event_functions.pop(self._name+'__'+attr)

    def add_psplot(self, *attrs, **kwargs):
        """Update psplot.
           kwargs:
              local: if True open psplot locally
              eventCode: check if event code(s) are in data 
                         (or alternatively not in date with - sign)
                         see is_eventCodePresent
        """
        plot_error = '' 

        if isinstance(attrs[0],list):
            attrs = attrs[0]

        attr_name = '_and_'.join(attrs)
        attr = attrs[0]

        if kwargs.get('local'):
            local = True
        else:
            local = False
        
        if 'eventCode' in kwargs:
            ecstrs = []
            for ec in kwargs.get('eventCode'):
                if ec > 0:
                    ecstrs.append(str(ec))
                else:
                    ecstrs.append('not'+str(-ec))
            ecname = '_'+'_and_'.join(ecstrs)
            ectitle = ' '+' and '.join(ecstrs)
        else:
            ecname = ''
            ectitle = ''

        if 'name' in kwargs:
            name = kwargs['name']
        else:
            name = self._name+'_'+attr_name+ecname

        if 'title' in kwargs:
            title = kwargs['title']
        else:
            if self._desc:
                title = self._desc
            else:
                title = self._name+' '+attr_name+ectitle
        if 'ts' in kwargs:
            ts = kwargs['ts']
        else:
            ts = self._data.ievent

        if 'plot_type' in kwargs:
            plot_type = kwargs['plot_type']
        else:
            plot_type = None

        pub_opts = ['eventCode']
        pub_kwargs = {key: item for key, item in kwargs.items() \
                      if key in pub_opts}

        if not plot_error and plot_type not in ['Image','XYPlot']:
            try:
                ndim = psutils.getattr_complete(self,attr).ndim
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
                            'attr': attrs,  
                            'name': name,
                            'plot_function': Image,
                            'ts': ts,
                            'title': title,
                            'kwargs': plt_kwargs,
                            'pubargs': pub_kwargs}
#                for key, item in kwargs.items():
#                    if key in plt_opts:
#                        plt_args[key] = item
            
            elif plot_type is 'XYPlot':
                plt_opts = ['xlabel','ylabel','formats']
                plt_kwargs = {key: item for key, item in kwargs.items() \
                              if key in plt_opts}
                if 'xdata' in kwargs:
                    xdata = kwargs['xdata']
                else:
                    xdata = [np.arange(len(psutils.getattr_complete(self, attr))) for attr in attrs]
                plt_args = {'det': self._name,
                            'attr': attrs,
                            'xdata': xdata,
                            'name': name,
                            'plot_function': XYPlot,
                            'ts': ts,
                            'title': title,
                            'kwargs': plt_kwargs,
                            'pubargs': pub_kwargs}
            else: 
                plot_error = 'Unknown plot type {:} \n'.format(plot_type)

        if plot_error:
            print 'Error adding psplot:' 
            print plot_error
            return None
        else:
            if name in self._data._psplots:
                if 'subprocess' in self._data._psplots[name]:
                    self.psplot_kill(name)

            print 'psmon plot added -- use the following to view: '
            print '--> psplot -s {:} -p 12301 {:}'.format(os.uname()[1], name)
            print 'WARNING -- see notice when adding for -p PORT specification'
            print '           if default PORT=12301 not available'
            self._data._psplots[name] = plt_args
            if not self._data._publish:
                if local and self._data._ami:
                    # currently local option not compatible with ami
                    self.psplot_publish_local(name)
                else:
                    publish.init(local=local)
                
                self._data._publish = True
    

    def psplot_publish_local(self, name):
        """Open plot locallly.
        """
#        self.psplot_kill(name)
        subproc = subprocess.Popen('psplot {:} &'.format(name), 
                             stdout=subprocess.PIPE, shell=True)
        
        subproc.poll()
        self._data._psplots[name]['subprocess'] = subproc 
        

        self._data.psmon_publish()

    def psplot_kill(self, name):
        """Kill psplot subprocess.
        """
        try:
            subproc = self._data._psplots[name]['subprocess']
            print 'Killing old {:} plot with pid {:} ' \
                  +'before opening new local plot'.format(subproc.pid, name) 
            subproc.kill()
        except:
            pass

    def del_psplot(self, name):
        """Remove psplot.
        """
        self._data.del_psmon(name)
#        if name in self._data._psplots:
#            self._data._psplots.pop(name)

    def monitor(self, **kwargs):
        """Monitor detector attributes continuously 
           with show_info function.
        """
        self.show_info(monitor=True, **kwargs)

# in _data.next_event, specifying that a detector is True does not work
# properly to go to the next event where it is in the keys.
#    def next_event(self, sleep=0.,
#                        is_in_keys=True,
#                        nskip=0, **kwargs):
#        """Get next event where this detector is_in_keys.
#        """
#        if is_in_keys is not None:
#            kwargs.update(**{self._name: is_in_keys})
#        
#        if nskip > 0:
#            for i in range(nskip-1):
#                self._data.next_event()
#            
#        self._data.next_event(**kwargs)
    
    def show_all(self, **kwargs):
        self.show_info(no_evrConfig=False, no_configStore=False, **kwargs)

    def show_info(self, attrs=None,
                        next_event=False, 
                        nevents=1, monitor=False, sleep=0.2,
                        is_in_keys=None,
                        nskip=0,
                        no_epicsLive=False,
                        no_epicsStore=False,
                        no_evtData=False,
                        no_evrConfig=True,
                        no_configStore=True,
                        prefix='',
                        *args, **kwargs):
        """Show Detector attributes.
        """
        try:
            ievent = 0
            while ievent < nevents or monitor:
               
                if is_in_keys is not None:
                    kwargs.update(**{self._name: is_in_keys})
                
                if nskip > 0:
                    for i in range(nskip-1):
                        self._data.next_event()
                    
                    self._data.next_event(**kwargs)
                
                elif ievent > 0:
                    time.sleep(sleep)
                    self._data.next_event(**kwargs)

                elif next_event or monitor:
                    self._data.next_event(**kwargs)
                
                ievent += 1
                print ''
                if 'det' in self._det and not no_evtData and not self._data._no_evtData:
                    print '='*80
                    print self._data.event_info
                    if not no_configStore:
                        self.configStore.show_info()
                        print '-'*80
                    if not no_evrConfig:
                        try:
                            self.evrConfig.show_info()
                            print '-'*80
                        except:
                            pass
                    if self.is_in_keys:
                        self.evtData.show_info(attrs=attrs)

#                if hasattr(self.epicsLive, 'show_info') and self.epicsLive._attrs and not no_epicsLive:
                if self._epicsLive_attrs and hasattr(self.epicsLive, 'show_info') and not no_epicsLive:
                    print '-'*72
                    print self.desc+': Live Epics PVs'
                    print '-'*72
                    self.epicsLive.show_info(prefix=prefix)

                if self._epicsStore_attrs and hasattr(self.epicsStore, 'show_info') and not no_epicsStore:
                    print '-'*72
                    print self.desc+': Epics Store PVs'
                    print '-'*72
                    self.epicsStore.show_info()

                if self._detectors_attrs:
                    for attr in self._detectors_attrs:
                        if prefix is True:
                            detprefix = prefix=self._name+'.'+attr+'.'
                        else:
                            detprefix = prefix=attr+'.'

                        getattr(self, attr).show_info(prefix=detprefix)

        except KeyboardInterrupt:
            pass
    
    @property 
    def is_in_keys(self):
        """Return True if detector is in evt.keys().
        """
        return self._name in self._data.evt._keys_dict

    def __repr__(self):
        repr_str = '< {:} {:}: {:}>'.format(self._name, self.__class__.__name__,self.desc) 
#        print repr_str
#        self.show_info()
        return repr_str

    def __getattr__(self, attr):
        """Return detector attribues from detector functions and  pv aliases.
           Detector functions will be automatically defined for each data type.
        """
        if attr in self._evtData_attrs:
            return getattr(self.evtData, attr)
                
        if attr in self._epicsLive_attrs:
            return getattr(self.epicsLive, attr)

        if attr in self._epicsStore_attrs:
            return getattr(self.epicsStore, attr)

        if attr in self.parameters:
            return self.parameters[attr]

        if attr in self._user_funcs:
            return self.get_function(attr)

#        if 'detectors' in self._det and attr in self._det['detectors']:
        if attr in self._detectors_attrs:
            return getattr(self._data, self._det['detectors'][attr])

    def __dir__(self):
        # As noted in epics.device -- there's no cleaner method to do this until Python 3.3
        all_attrs = set(
                        self._evtData_attrs +
#                        self._epicsStore_attrs +
                        self._epicsLive_attrs +
                        self._detectors_attrs +
                        self.parameters.keys() +
                        self._user_funcs.keys() +
                        self.__dict__.keys() + dir(Detector))
        return list(sorted(all_attrs))

# read in and write out updated config dict
#for det in device_sets:
#    if 'pvs' in device_sets[det]:
#        device_sets[det]['pvs'] = {alias: {'base': pvbase} for alias, pvbase in device_sets[det]['pvs'].items()}

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
    parser.add_argument("--ami", action="store_true", 
                        help='Use ami data from proxy')
    parser.add_argument("--proxy_host", type=str,
                        help='Ami proxy host ' \
                             '-- by default use mon01 of appropriate instrument.')
    parser.add_argument("--quick_alias", action="store_true", 
                        help='Use quick alias in interactive python')
    parser.add_argument("--epics_file", type=str, 
                        help='epics alias file with epicsArch style file')
    parser.add_argument("--epics_dir", type=str, 
                        help='dir for epics_file used for epics aliases')
    parser.add_argument("--no_epics_aliases", action="store_true", 
                        help='Do not make epics aliases available')
    parser.add_argument("--show_errors", action="store_true", default=False,
                        help='Show Errors in cases that might not be explicit ' \
                             'due to try/except statements')
    parser.add_argument("--idx", action="store_true", default=False, 
                        help='idx index file instead of newer smd file')
    parser.add_argument("--indexed", action="store_true", default=False, 
            help='Use indexing, see: https://confluence.slac.stanford.edu/display/PSDM/psana+-+Python+Script+Analysis+Manual#psana-PythonScriptAnalysisManual-RandomAccesstoXTCFiles("Indexing")')
    parser.add_argument("-b", "--base", type=str, 
                        help='Base into which psdata is loaded.')
#    parser.add_argument("-d", "--detectors", type=str, 
#                        help='List of detector aliases to load.')
    parser.add_argument("-c", "--config_file", type=str, 
                        help='File with configuration dictionary.')
    parser.add_argument("--noload", action="store_true", 
                        help='Do not load psana data')
    parser.add_argument("--iocrc", type=str, 
                        help='Use local file of controls camera, ' \
                             'xtc_dir="/reg/d/camera/{iocrc}/daq/xtc/')
    parser.add_argument("-P", "--monshmserver", type=str, default='psana', 
                        help='-P monshmserver flag used in cnf file for live data')
    parser.add_argument("-n", "--nstart", type=int, default=2, 
                        help='Number of Events to load on start')
#    parser.add_argument("-d", "--det_list", type=str, help='List of detectors if nevents set')
    return parser.parse_args()

if __name__ == "__main__":
    time0 = time.time()
    args = initArgs()
    print "*"*80
    print 'Loading psdata with the following arguments:'
    for attr,val in vars(args).items():
        print "   {:} = {:}".format(attr, val)
    print "*"*80
#    base_default = 'data'
    if args.exp and not args.instrument:
        args.instrument = args.exp[0:3]
    
    if not args.instrument:
        args.instrument = psutils.instrument_guess()
    
    if not args.base:
        args.base = args.instrument

    if args.ami:
        if not args.proxy_host:
            args.proxy_host='daq-'+args.instrument+'-mon01'

    setattr(sys.modules['__main__'], args.base, psdata(**vars(args)))

    if args.epics_live:
        print 'setting up ioc for ', args.instrument
        ioc = psioc.IOC(instrument=args.instrument, no_init=True)

    run_info = getattr(sys.modules['__main__'], args.base)
    print ""
    print "*"*80

    print run_info

    print 'Load time = {:5.1f} sec'.format(time.time()-time0)

