import argparse
import sys
import operator
import re
import time
import traceback
import psana
from Detector.PyDetector import PyDetector

def live_source(monshmserver='psana', **kwargs):
    """Returns psana source string for live data from shared memory on the current node.
       The standard convention is to have the shared memry servers either named 'psana'
       or the instrument name in all caps.  This will return the source string for 
       the valid one based on searching the local file system.  The process will be
       found at:

          '/dev/shm/PdsMonitorSharedMemory_'+monshmserver
    """
    from glob import glob
    import os

    shm_srvs = glob('/dev/shm/PdsMonitorSharedMemory_'+monshmserver)
    if shm_srvs == []:
        hostsplit = os.uname()[1].split('-')
        instrument = hostsplit[1]
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

def evt_dict(self):
    """Used in TabEvent and TabKeys Classes.
    """
    evt_dict = {}
    for evt_key in self.keys():
        typ = evt_key.type()
        if typ:
            src = evt_key.src()
            alias = evt_key.alias()
            key = evt_key.key()
            psana_class = typ.__name__
            psana_module = typ.__module__
            module = psana_module.lstrip('psana').lstrip('.')
            typ_name = key+module.lstrip('Bld')+typ.__name__
            if re.search(r"V.?\b", typ_name):
                typ_name = typ_name[:-2]
            if not alias:
                if hasattr(src, 'typeName'):
                    alias = src.typeName()
                elif key:
                    alias = key
                elif module:
                    alias = module
                else:
                    alias = psana_class

            if alias:
                alias = alias.replace('-','_')
            evt_funcs = self.get(typ,src,key) 
            attrs =  [attr for attr in dir(typ) \
                      if not attr.startswith(('_','TypeId','Version','DamageMask'))]
            if alias not in evt_dict:
                evt_dict[alias] = {'src': src, 
                                   'alias': alias, 
                                   'type': {}, 
                                   'attrs': {}, 
                                   'module': module}
            
            attr_dict = {attr: evt_funcs for attr in attrs}
            evt_dict[alias]['type'].update({typ_name: {'typ': typ, 'src': src, 
                                                       'alias': alias, 'key': key, 
                                                       'attrs': attr_dict}})
            evt_dict[alias]['attrs'].update({attr: evt_funcs for attr in attrs})

    return evt_dict

def get_unit_from_doc(doc):
    """Parse the unit from the doc string.
    """
    invalid_units = ['this', 'long', 'all', 'setup', 'given', 'a']
    try:
        usplit = doc.rsplit(' in ')
        if 'Value' in doc and 'converted to' in doc:
            unit = '{:}'.format(doc.rsplit('converted to ')[-1].rstrip('.'))
        elif len(usplit) < 2:
            unit = ''
        else:
            unit = '{:}'.format(usplit[-1])
            unit = unit.rstrip('.').rstrip(',').rsplit(' ')[0].rstrip('.').rstrip(',')
            
            if unit.endswith('(') or unit in invalid_units:
                unit = ''
        
    except:
        unit = ''
    return unit

def get_type_from_doc(doc):
    """Parse the type from the doc string.
    """
    try:
        return  doc.replace('\n',' ').split('-> ')[1].split(' ')[0]
    except:
        return None

def func_dict(func):
    """psana attribute function dictionary.
    """
    fdict = {
             'doc': '',
             'unit': '',
             'str':  'NA',
             'func': func}

    value = func
    try:
        value = value()
    except:
        pass

    try:
        fdict['attr'] = func.__func__.__name__
    except:
        fdict['attr'] = None
    
    if isinstance(value,str):
        fdict['str'] = value
    else:
        if isinstance(value, list):
            fdict['str'] = 'list'
        elif hasattr(value,'mean'):
            fdict['str'] = '<{:.4}>'.format(value.mean())
        else:
            try:
                fdict['attr'] = func.__func__.__name__
                doc = func.__doc__.split('\n')[-1].lstrip(' ')
                fdict['doc'] = doc
                fdict['str'] = '{:10.5g}'.format(value)
                fdict['unit'] = get_unit_from_doc(doc)
                fdict['type'] = get_type_from_doc(doc)
            except:
                try:
                    fdict['attr'] = func.__func__.__name__
                    fdict['str'] = value.__str__()
                except:
                    pass

    fdict['value'] = value

    return fdict

def func_repr(func, name=None):
    """psana function represenatation
    """
    fdict = func_dict(func)
    if name:
        fdict['attr'] = name

    return '{attr:18s} {str:>12} {unit:7} {doc:}'.format(**fdict)

def func_value(func):
    try:
        func = func()
    except:
        pass

    if isinstance(func, list):
        func = [ReDictify(f) for f in func]

    return func

def get_config(configStore, attr, cls='Config'):
    configs = getattr(getattr(psana, attr),cls)
    configs.reverse()
    for config in configs:
        obj = configStore.get(config)
        if obj:
            return obj


class DataSourceInfo(object):
    """-------------------------------------------------------------------------------
       data_source class built from keyword arguments that can be accessed as attributes

            data_source = 'exp=CXI/cxic0115:run=10'

        The following are equivalent:

            data_source = DataSourceInfo(exp='cxic0115', run=10).data_source
            data_source = str(DataSourceInfo(exp='cxic0115', run=10))

        You can also load a data source with keyword options:
        (indexed is currently not supported)

            h5:   loads hdf5 data instead of xtc
            ffb:  appends ':one-stream' to data source

        The shared memory data_source can be automatically loaded with the live keyword:

            data_source = str(DataSource(live=True))

        But shared memory should alse be automatically detected if no arguments are
        supplied and you are on a shared memery server.
            
            data_source = str(DataSource())

    """
    _exp_defaults = {'instrument': None, 
                     'live':       None, 
                     'exp':        None, 
                     'h5':         None,
                     'run':        0,
                     'smd':        None, 
                     'station':    0,
                     'indexed':    None,
                     'ffb':        None,
                     'cfg':        None}

    def __init__(self, data_source=None, **kwargs):
        self.data_source = self._set_data_source(data_source=data_source, **kwargs)

    def _set_exp_defaults(self, **kwargs):
        """Sets experiment defaults based on kwargs and defaults.
        """
        for key, val in self._exp_defaults.items():
            setattr(self, key, kwargs.get(key, val))

        if self.exp is not None:
            self.instrument = self.exp[0:3]

#        inst_id = '{:}:{:}'.format(self.instrument.upper(), self.station)

    def _set_data_source(self, data_source=None, **kwargs): 
        self._set_exp_defaults(**kwargs)

        if self.live:
            self.indexed = False
            if not data_source:
                data_source = live_source(**kwargs)

        if not data_source:

            if self.exp and self.run:
                self.instrument = self.exp[0:3]
     
                data_source = "exp={exp}:run={run}".format(exp=self.exp,run=self.run)
                
                if self.ffb:
                    data_source += ":one-stream"
                elif self.smd:
                    data_source += ":smd"
                elif self.h5:
                    data_source += ":h5"
                elif self.indexed:
                    data_source += ":idx"

            else:
                print 'No data source specified, so assume this is shared memory.'
                data_source = live_source(**kwargs)
                self.live = True
                self.indexed = False

        return data_source

    def show_info(self):
        for attr in self._exp_defaults:
            print '{:20} {:}'.format(attr, getattr(self, attr))

    def __str__(self):
        return self.data_source

    def __repr__(self):
        return '< {:}: {:} >'.format(self.__class__.__name__, self.data_source)

class DataSource(object):
    """Python version of psana.DataSource with support for event and config
       data as well as PyDetector functions to access calibrated data.
    """

    _ds_attrs = ['empty', 'end', 'env', 'liveAvail', 'runs', 'steps']
    _env_attrs = ['calibDir']
    _detectors = {}
    _pbits = 0
    _srcs = {}

    def __init__(self, data_source=None, **kwargs):
        self.load_run(data_source=data_source, **kwargs)
        self._evt_time_last = (0,0)
        self._ievent = -1

    def load_run(self, initialize=None, **kwargs):
        self._evtData = None
        self._current_evt = None
        self.data_source = DataSourceInfo(**kwargs)
        self._ds = psana.DataSource(str(self.data_source))
        self.epicsStore = EpicsDictify(self._ds) 

        if self.data_source.indexed:
            self._Events = RunEvents(self, **kwargs)
        else:
            self._Events = Events(self, **kwargs)

        if not self._detectors.get(str(self.data_source)):
            initialize = True
        
        if initialize: 
            self._init_detectors()
 
    def _init_detectors(self):
        """Initialize psana.Detector classes based on psana env information.
        """
        configStore = self._ds.env().configStore()
        self.aliasConfig = AliasConfig(configStore) 
        csPartition = get_config(configStore, 'Partition')
        csEpics = get_config(configStore, 'Epics')
        csEvr = get_config(configStore, 'EvrData', cls='IOConfig')
        self._bldMask = csPartition.bldMask()
        self._partition = {str(s.src()): {'src': s.src(), 'group': s.group(), 'alias': None} \
                         for s in csPartition.sources()}
        self._aliases = {} 
        for alias, src in self.aliasConfig._aliases.items():
            srcstr = str(src)
            alias = re.sub('-|:|\.| ','_', alias)
            self._aliases[alias] = srcstr
            if srcstr in self._partition:
                self._partition[srcstr]['alias'] = alias
            else:
                # add data sources not in partition that come from recording nodes
                self._partition[srcstr] = {'src': src, 'group': None, 'alias': alias}

        self._sources = {}
        for srcstr, item in self._partition.items():
            if not item.get('alias'):
                try:
                    alias = srcstr.split('Info(')[1].rstrip(')')
                except:
                    alias = srcstr
                
                alias = re.sub('-|:|\.| ','_',alias)
                item['alias'] = alias
                self._aliases[alias] = srcstr

            if 'NoDetector' not in srcstr and 'NoDevice' not in srcstr:
                self._sources[srcstr] = item

        self.configStore = TabKeys(configStore)
        self.evrConfig = EvrDictify(self.configStore)

        for srcstr, item in self._sources.items():
            alias = item.get('alias')
            self._add_dets(**{alias: srcstr})

    def _add_dets(self, **kwargs):
        if str(self.data_source) not in self._detectors:
            self._detectors.update({str(self.data_source): {}})

        for alias, srcstr in kwargs.items():
            try:
                det = Detector(self, alias)
                self._detectors[str(self.data_source)].update({alias: det})
            except Exception as err:
                print 'Cannot add {:}:  {:}'.format(alias, srcstr) 
                traceback.print_exc()

    # This can be made more efficient
    def _get_evtData(self, alias):
        """Get the event data for the current event.
        """
        if not self._evtData:
            self._evtData = TabKeys(self._current_evt)
    
        if hasattr(self._evtData, alias):
            return getattr(self._evtData, alias)
        else:
            return None
 
    @property
    def _current_dets(self):
        """Current detectors from _detector dictionary.
        """
        return self._detectors.get(str(self.data_source), {})

    def show_info(self):
        for item in self._current_dets.values():
            print item.__repr__()

    @property
    def current(self):
        return EvtDetectors(self)

    def events(self):
        return self._Events

    def next(self, *args, **kwargs):
        return self.events().next(*args, **kwargs) 
 
    def __iter__(self):
        return self

    def __str__(self):
        return  str(self.data_source)

    def __repr__(self):
        repr_str = '{:}: {:}'.format(self.__class__.__name__,str(self))
        return '< '+repr_str+' >'

    def __getattr__(self, attr):
        if attr in self._ds_attrs:
            return getattr(self._ds, attr)
        
        if attr in self._env_attrs:
            return getattr(self._ds.env(), attr)()
        
    def __dir__(self):
        all_attrs =  set(self._ds_attrs + 
                         self._env_attrs +
                         self.__dict__.keys() + dir(DataSource))
        
        return list(sorted(all_attrs))


class RunEvents(object):
    """Event iterator from ds.runs() for indexed data 

       No support yet for multiple runs in a data_source
    """

    _ds_runs = []

    def __init__(self, ds, **kwargs):
        self._kwargs = kwargs
        self._ds = ds
        self.next_run()

    def next_run(self):
        self._ds_run = self._ds.runs().next()
        self._ds_runs.append(self._ds_run)
        self.times = self._ds_run.times()

    def __iter__(self):
        return self

    def next(self, evt_time=None):
        """Optionally pass either an integer for the event number in the data_source
           or a psana.EventTime time stamp to jump to an event.
        """
        self._ds._evtData = None
        if evt_time is not None:
            if isinstance(evt_time, int):
                self._ds._ievent = evt_time
            else:
                self._ds._ievent = self.times.index(evt_time)
        else:
            self._ds._ievent += 1
        
        if self._ds._ievent >= len(self.times):
            print 'No more events in run.'
        else:
            self._ds._current_evt = self._ds_run.event(self.times[self._ds._ievent])

        return EvtDetectors(self._ds)


class Events(object):
    """Event iterator
    """

    _nevents_cash = 10
    _events = []

    def __init__(self, ds, **kwargs):
        self._kwargs = kwargs
        self._ds = ds

    def __iter__(self):
        return self

    def next(self):
        if len(self._events) > self._nevents_cash:
            self._events.pop(0)
      
        self._ds._ievent += 1
        self._ds._evtData = None
        self._ds._current_evt = self._ds._ds.events().next()
        self._events.append(self._ds._current_evt)

        return EvtDetectors(self._ds)


class EvtDetectors(object):
    """Psana tab accessible event detectors.
       Preserves get, keys and run method of items in psana events iterators.
    """

    _init_attrs = ['get', 'keys', 'run']
    
    def __init__(self, ds): 
        self._ds = ds
        self._EventId = EventId(self._ds._current_evt)
        self.ievent = ds._ievent

    @property
    def EventId(self):
        return self._EventId

    @property
    def _attrs(self):
        """Detector names from _det.keys().
        """
        return self._dets.keys()

    @property
    def _dets(self):
        """Dictionary of detectors.
        """
        return self._ds._current_dets

    @property
    def Evr(self):
        """Master evr from psana evt data.
        """
        if not self._evr_typ_src:
            self._evr_typ, self._evr_src = self._get_evr_typ_src()

        return MasterEvr(self.get(self._evr_typ, self._evr_src))
            
    def _get_evr_typ_src(self):
        """Set the maste evr. By default automated as there should only be one in the evt keys.
        """
        for key in self._ds._current_evt.keys():
            if hasattr(key.src(),'devName') and getattr(key.src(),'devName')() == 'Evr':
                return (key.type(), key.src())

    def __str__(self):
        return  '{:}, Run {:}, Event {:}, {:}, {:}'.format(self._ds.data_source.exp, 
                self.run(), self.ievent, str(self.EventId), str(self.Evr))

    def __repr__(self):
        repr_str = '{:}: {:}'.format(self.__class__.__name__, str(self))
        return '< '+repr_str+' >'

    def __getattr__(self, attr):
        if attr in self._init_attrs:
            return getattr(self._ds._current_evt, attr)
        
        if attr in self._dets:
            return self._dets[attr]

    def __dir__(self):
        all_attrs =  set(self._attrs +
                         self._init_attrs +
                         self.__dict__.keys() + dir(EvtDetectors))
        
        return list(sorted(all_attrs))


class AliasConfig(object):
    """Tab Accessible configStore Alias information.
    """

    def __init__(self, configStore):

        self._aliases = {}
        for key in configStore.keys():
            if key.type() and key.type().__module__ == 'psana.Alias':
                a = configStore.get(key.type(),key.src())
                for alias in a.srcAlias():
                    self._aliases[alias.aliasName()] = alias.src()

    def show_info(self):
        for alias, src in self._aliases.items():
            print '{:18s} {:}'.format(alias, src)

    def __getattr__(self, attr):
        if attr in self._aliases:
            return self._aliases.get(attr)

    def __dir__(self):
        all_attrs =  set(self._aliases.keys() +
                         self.__dict__.keys() + dir(AliasConfig))
        
        return list(sorted(all_attrs))


class EpicsConfig(object):
    """Tab Accessible configStore Epics information.
       Currently relatively simple, but expect this to be expanded
       at some point with more PV config info with daq update.
    """

    _pv_attrs = ['description', 'interval', 'pvId']

    def __init__(self, configStore):

        self._pvs = {}
        for key in configStore.keys():
            if key.type() and key.type().__module__ == 'psana.Epics':
                a = configStore.get(key.type(),key.src())
                for pv in a.getPvConfig():
                    pvdict = {attr: getattr(pv, attr)() for attr in self._pv_attrs} 
                    self._pvs[pv.description()] = pvdict

    def show_info(self):
        for alias, items in self._pvs.items():
            print '{:18s} {:}'.format(alias, item.pvId)

    def __getattr__(self, attr):
        if attr in self._pvs:
            return self._pvs.get(attr)

    def __dir__(self):
        all_attrs =  set(self._pvs.keys() +
                         self.__dict__.keys() + dir(EpicsConfig))
        
        return list(sorted(all_attrs))


class MasterEvr(object):
    """Tab Accessible event Evr information for psana event.
    """

    _attrs = ['fifoEvents', 'numFifoEvents']

    def __init__(self, evr):

        self._evr = evr

    @property
    def eventCodes(self):
        """Event codes
        """
        return [a.eventCode() for a in self.fifoEvents]

    def preset(self, eventCode):
        """True if event code is present in event.
        """
        try:
            return self._evr.present(eventCode)
        except:
            return False

    def show_info(self):
        print '{:18s} {:>12}'.format('eventCodes', self.eventCodes)

    def __str__(self):
        try:
            eventCodeStr = '{:}'.format(self.eventCodes)
        except:
            eventCodeStr = ''
        
        return eventCodeStr

    def __repr__(self):
        return '< {:}: {:} >'.format(self.__class__.__name__, str(self))

    def __getattr__(self, attr):
        if attr in self._attrs:
            return getattr(self._evr, attr)()

    def __dir__(self):
        all_attrs =  set(self._attrs+
                         self.__dict__.keys() + dir(MasterEvr))
        
        return list(sorted(all_attrs))


class EventId(object):
    """Time stamp information from psana EventId. 
    """

    _attrs = ['fiducials', 'idxtime', 'run', 'ticks', 'time', 'vector']

    def __init__(self, evt):

        self._EventId = evt.get(psana.EventId)

    def show_info(self):
        for attr in self._attrs:
            if attr != 'idxtime': 
                print '{:18s} {:>12}'.format(attr, getattr(self, attr))

    def __str__(self):
        try:
            EventTimeStr = time.strftime('%H:%M:%S',
                    time.localtime(self.time[0]))
            EventTimeStr += '.{:04}'.format(int(self.time[1]/1e5))
        except:
            EventTimeStr = 'NA'

        return '{:}'.format(EventTimeStr)

    def __repr__(self):
        return '< {:}: {:} >'.format(self.__class__.__name__, str(self))

    def __getattr__(self, attr):
        if attr in self._attrs:
            return getattr(self._EventId, attr)()

    def __dir__(self):
        all_attrs =  set(self._attrs+
                         self.__dict__.keys() + dir(EventId))
        
        return list(sorted(all_attrs))


class Detector(object):
    """Includes epicsStore, configStore, evrConfig info 
       Uses full ds in order to be able to access epicsStore info on
       an event basis.
    """
    _ds_attrs = ['configStore', 'evrConfig', 'epicsStore']

    def __init__(self, ds, alias, pbits=0, **kwargs):
        """Initialize a psana Detector class for a given detector alias.
           Provides the attributes of the PyDetector functions for the current 
           event if applicable.  Otherwise provides the attributes from the
           raw data in the psana event keys for the given detector.
        """

        self._pbits = pbits
        self._alias = alias
        self._ds = ds
        self.src = ds._aliases.get(alias)

        print 'Adding Detector: {:20} {:40}'.format(alias, psana.Source(self.src))
        self._pydet = PyDetector(psana.Source(self.src), ds._ds.env(), self._pbits)
        
        if self._pydet.dettype in [16, 17]:
            self._det_class = WaveformDict
            self._tabclass = 'detector'
        elif self._pydet.dettype:
            self._det_class = ImageDict
            self._tabclass = 'detector'
        else:
            self._det_class = None
            self._tabclass = 'evtData'

    @property
    def _attrs(self):
        """Attributes of PyDetector functions if relevant, and otherwise
           attributes of raw psana event keys for the given detector.
        """
        attrs = getattr(self, self._tabclass)._attrs
        return attrs

    def monitor(self, nevents=-1):
        """Monitor detector attributes continuously with show_info function.
        """ 
        ievent = nevents
        try:
            while ievent != 0:
                self._ds.next()
                ievent -= 1
                try:
                    self.show_info()
                except:
                    pass

        except KeyboardInterrupt:
            ievent = 0

    def show_info(self):
        print '-'*80
        print '{:}: {:}'.format(self._alias, str(self._ds.current))
        print '-'*80
        getattr(self, self._tabclass).show_info()

    @property
    def evtData(self):
        """Tab accessible raw data from psana event keys.
        """
        return self._ds._get_evtData(self._alias)

    @property
    def detector(self):
        """Tab accessible PyDetector class
        """
        return self._det_class(self._pydet, self._ds._current_evt)

    def __str__(self):
        return '{:} {:}'.format(self._alias, self.src)

    def __repr__(self):
        return '< {:}: {:} >'.format(self.__class__.__name__, str(self))

    def __getattr__(self, attr):
        if hasattr(getattr(self._ds, attr), self._alias):
            return getattr(getattr(self._ds, attr), self._alias)
        if attr in self._attrs:
            return getattr(getattr(self, self._tabclass), attr)

    def __dir__(self):
        all_attrs =  set(self._ds_attrs+
                         self._attrs+
                         self.__dict__.keys() + dir(Detector))
        
        return list(sorted(all_attrs))


class WaveformDict(object):
    """Tab accessibile dictified psana PyDetector object.
       
       Attributes come from Detector.PyDetector in psana 
       with low level implementation done in C++ or python.  
       Boost is used for the C++.
    """

    _attrs = ['raw'] 

    _attr_docs = {
            'raw': 'Raw waveform Volts vs time in sec', 
            } 

    def __init__(self, det, evt):
        self._evt = evt
        self._det = det

    @property
    def instrument(self):
        """Instrument to which this detector belongs.
        """
        return self._det.instrument()

    def set_print_bits(self, pbits):
        """Set the level of printing.
        """
        self._det.set_print_bits(pbits)

    def print_attributes(self):
        """Print detector attributes.
        """
        self._det.print_attributes()

    def show_info(self):
        """Show information for relevant detector attributes.
        """
        if self.size > 0:
            items = sorted(self._attr_docs.items(), key = operator.itemgetter(0))
            for attr, doc in items:
                fdict = {'attr': attr, 'unit': '', 'doc': doc}
                value = getattr(self, attr)
                if isinstance(value, str):
                    fdict['str'] = value
                elif isinstance(value, list):
                    if len(value) < 5:
                        fdict['str'] = str(value)
                    else:
                        fdict['str'] = 'list'
                elif hasattr(value,'mean'):
                    if value.size < 5:
                        fdict['str'] = str(value)
                    else:
                        fdict['str'] = '<{:.5}>'.format(value.mean())
                else:
                    try:
                        fdict['str'] = '{:12.5g}'.format(value)
                    except:
                        fdict['str'] = str(value)

                print '{attr:18s} {str:>12} {unit:7} {doc:}'.format(**fdict)
        else:
            print 'No Event'

    def __getattr__(self, attr):
        if attr in self._attrs:
            return getattr(self._det, attr)(self._evt)

    def __dir__(self):
        all_attrs =  set(self._attrs +
                         self.__dict__.keys() + dir(WaveformDict))
        
        return list(sorted(all_attrs))


class ImageDict(object):
    """Tab accessibile dictified psana PyDetector object.
       
       Attributes come from Detector.PyDetector in psana 
       with low level implementation done in C++ or python.  
       Boost is used for the C++.
    """

    _attrs = ['shape', 'size', 'ndim', 'pedestals', 'rms', 'gain', 'bkgd', 'status',
              'status_as_mask', 'mask_calib', 'common_mode', 'raw', 'calib',
              'areas', 'indexes_x', 'indexes_y', 'pixel_size',
              'coords_x', 'coords_y', 'coords_z', 
              'image',
             ] 

    _attr_docs = {
            'shape': 'Shape of raw data array', 
            'size': 'Total size of raw data', 
            'ndim': 'Number of dimensions of raw data', 
            'pedestals': 'Pedestals from calibStore', 
            'rms': '', 
            'gain': 'Pixel Gain factor from calibStore', 
            'bkgd': '', 
            'status': '',
            'common_mode': 'Common mode parameters', 
            'raw': 'Raw data', 
            'calib': 'Calibrated data',
            'areas': 'Pixel area correction factor', 
            'indexes_x': 'Pixel X index', 
            'indexes_y': 'Pixel Y index', 
            'pixel_size': 'Pixel Size',
            'coords_x': 'Pixel X coordinate', 
            'coords_y': 'Pixel Y coordinate', 
            'coords_z': 'Pixel Z coordinate', 
            'image': 'Reconstruced 2D image from calibStore geometry',
            } 

    def __init__(self, det, evt):
        self._evt = evt
        self._det = det

    @property
    def configStore(self):
        return self._det.configStore

    @property
    def evrConfig(self):
        return self._det.evrConfig
    
    @property
    def epicsStore(self):
        return self._det.epicsStore
    
    @property
    def evtData(self):
        return self._det.evtData
    
    @property
    def instrument(self):
        """Instrument to which this detector belongs.
        """
        return self._det.instrument()

    def make_image(self, nda):
        """Make an image from the input numpy array based on the 
           geometry in the calib directory for this event.
        """
        return self._det.image(self._evt, nda)

    def set_do_offset(do_offset=True):
        """Not sure what do offset does?
        """
        self._det.set_do_offset(do_offset=do_offset)

    def common_mode_correction(self, nda):
        """Return the common mode correction for the input numpy 
           array (pedestal-subtracted). 
        """
        return self._det.common_mode_correction(self._evt, nda)
        
    def common_mode_apply(self, nda):
        """Apply in place the common mode correction for the input 
           numpy array (pedestal-subtracted). 
        """
        self._det.common_mode_apply(self._evt, nda)

    def mask(self, calib=False, status=False, 
                   edges=False, central=False, 
                   unbond=False, unbondnbrs=False):
        """Returns combined mask.
                calib:      mask from file in calib directory.
                status:     pixel status from file in calib director.
                edges:      mask detector module edge pixels (mbit +1 in mask_geo).
                central:    mask wide central columns (mbit +2 in mask_geo).
                unbond:     mask unbonded pixels (mbit +4 in mask_geo).
                unbondnbrs: mask unbonded neighbour pixels (mbit +8 in mask_geo).
        """
        return self._det.mask(self._evt, calib=False, status=False, edges=False, 
                              central=False, unbond=False, unbondnbrs=False)

    def mask_geo(self, mbits=15): 
        """Return geometry mask for given mbits keyword.
           Default is mbits=15 to mask edges, wide central columns,
             non-bo pixels and their neighbors

           mbits =  +1-edges; 
                    +2-wide central cols; 
                    +4 unbonded pixel; 
                    +8-unbonded neighbour pixels;
        """
        return self._det.mask_geo(self._evt, mbits=mbits)

    def set_print_bits(self, pbits):
        """Set the level of printing.
        """
        self._det.set_print_bits(pbits)

    def print_attributes(self):
        """Print detector attributes.
        """
        self._det.print_attributes()

#    def print_config(self):
#        """Print detector configuration.
#        """
#        self._det.print_config(self._evt)

    def show_info(self):
        """Show information for relevant detector attributes.
        """
        if self.size > 0:
            items = sorted(self._attr_docs.items(), key = operator.itemgetter(0))
            for attr, doc in items:
                fdict = {'attr': attr, 'unit': '', 'doc': doc}
                value = getattr(self, attr)
                if isinstance(value, str):
                    fdict['str'] = value
                elif isinstance(value, list):
                    if len(value) < 5:
                        fdict['str'] = str(value)
                    else:
                        fdict['str'] = 'list'
                elif hasattr(value,'mean'):
                    if value.size < 5:
                        fdict['str'] = str(value)
                    else:
                        fdict['str'] = '<{:.5}>'.format(value.mean())
                else:
                    try:
                        fdict['str'] = '{:12.5g}'.format(value)
                    except:
                        fdict['str'] = str(value)

                print '{attr:18s} {str:>12} {unit:7} {doc:}'.format(**fdict)
        else:
            print 'No Event'

    def __getattr__(self, attr):
        if attr in self._attrs:
            return getattr(self._det, attr)(self._evt)
        
    def __dir__(self):
        all_attrs =  set(self._attrs +
                         self.__dict__.keys() + dir(ImageDict))
        
        return list(sorted(all_attrs))


class TabKeys(object):
    """Tab accessible dictified data from psana keys.
       e.g., 
            evt = TabKeys(ds.events().next())
            configStore = TabKeys(ds.env().configStore())
    """

    _init_attrs = ['get','put','keys', 'remove', 'run']

    def __init__(self, evt):

        self._evt = evt
        self._evt_dict = evt_dict(evt)

    def show_info(self):
        """Show attributes in data object.
        """
        for attr in self._evt_dict:
            getattr(self, attr).show_info()

    def __getattr__(self, attr):
        if attr in self._init_attrs:
            return getattr(self._evt, attr)
        
        if attr in self._evt_dict:
            return TabDet(self._evt_dict[attr])

    def __dir__(self):
        all_attrs = set(self._evt_dict.keys() +
                        self._init_attrs +
                        self.__dict__.keys() + dir(TabKeys))
        return list(sorted(all_attrs))


class TabDet(object):
    """Dictify the detectors with types.
       Used from TabKeys class.
    """
    def __init__(self, ddict):

        self._ddict = ddict
        self._attrs = ddict['attrs'].keys()

    def show_info(self):
#        print '-'*80
#        print self._ddict['alias']
#        print '-'*80
        for attr, func in self._ddict.get('attrs').items():
            try:
                print func_repr(getattr(func, attr))
            except:
                print 'Warngin: {:} attribute {:} not valid'.format(det, attr)

    def __getattr__(self, attr):
        func = self._ddict['attrs'].get(attr)
        if func:
            return func_value(getattr(func, attr))
        
        if attr in self._ddict.get('type'):
            return TabType(self._ddict['type'][attr])

    def __dir__(self):
        all_attrs = set(self._attrs +
                        self._ddict['type'].keys() +
                        self.__dict__.keys() + dir(TabDet))
        return list(sorted(all_attrs))


class TabType(object):
    """Dictified psana data type.
       Used from TabDet Class.
    """

    def __init__(self, tdict):

        self._tdict = tdict

    def show_info(self):
#        print '-'*80
#        print self._tdict['alias']
#        print '-'*80
        for attr, func in self._tdict['attrs'].items():
            try:
                print func_repr(getattr(func, attr))
            except:
                print 'Warngin: {:} attribute {:} not valid'.format(det, attr)

    def __getattr__(self, attr):
        func = self._tdict['attrs'].get(attr)
        if func:
            return getattr(func, attr)

    def __dir__(self):
        all_attrs = set(self._tdict['attrs'].keys() +
                        self.__dict__.keys() + dir(TabType))
        return list(sorted(all_attrs))


class ReDictify(object):
    """Class for re-dictifying psana data attributes that are lists.
    """

    def __init__(self, obj):
        self._obj = obj
        attrs = [attr for attr in dir(obj) if not attr.startswith('_')]
        self._attrs = {}
        for attr in attrs:
            value = getattr(obj, attr)
            try:
                value = value()
            except:
                pass
            
            self._attrs[attr] = value
        
        self._show_attrs = self._attrs.keys()

    def get_info(self, attrs=None, **kwargs):
        info = ''
        if not attrs:
            attrs = list(sorted(self._show_attrs))
        for attr in attrs:
            if hasattr(self._obj, attr):
                value = getattr(self._obj,attr)
            else:
                value = getattr(self,attr)
            if isinstance(value, ReDictify):
                reinfo = value.get_info()
                for line in reinfo.split('\n'):
                    if line:
                        info += attr+'.'+line+'\n' 
            else:
                info += func_repr(value, name=attr)+'\n'

        return info

    def show_info(self, **kwargs):
        print self.get_info(**kwargs)

    def add_property(self, show=True, **kwargs):
        """Add additional dictified functions to _attrs dictionary
           By default these are added to _show_attrs list (unless show=False).
           Ex. for configStore.Alias.AliasConfig data:
            attr_dict = {item.aliasName(): item.src for item in self.srcAlias}
            self.add_property(**attr_dict)
        """
        if kwargs:
            self._attrs.update(**kwargs)
            if show:
                for attr in kwargs:
                    self._show_attrs.append(attr)
 
    def __repr__(self):
        repr_str = '< {:}.{:} >'.format(self._obj.__class__.__module__, \
                self._obj.__class__.__name__) 
#        self.show_info()
        return repr_str

    def __getattr__(self, attr):
        if attr in self._attrs:
            return self._attrs[attr]

    def __dir__(self):
        all_attrs = set(self._attrs.keys() + 
                        self.__dict__.keys() + dir(ReDictify))
           
        return list(sorted(all_attrs))


class SrcDictify(ReDictify):
    """Psana Source Redictified.
    """

    def __init__(self, src):

        ReDictify.__init__(self, src)

        if hasattr(src,'detName'):
            if src.detName() in ['NoDetector']:
                det_key = '_'.join([src.devName(),str(src.devId())])
            else:
                det_key = '_'.join([src.detName(),str(src.detId()),
                                    src.devName(),str(src.devId())])
            src_attrs = ['__str__','detName','detId','devName','devId']
        elif hasattr(src,'typeName'):
            det_key = '_'.join([src.typeName(),str(src.type())])
            src_attrs = ['__str__','typeName']
        else:
            det_key = None
            src_attrs = []

        det_str = src.__str__()
        self.add_property(det_key=det_key)
        self.add_property(src=src.__str__())
        self.add_property(_src_attrs=src_attrs, show=False)
        self._show_attrs.remove('Device')
        self._show_attrs.remove('Detector')


class EvrDictify(object):
    """Psana Evr Information Dictified from Alias.AliasConfig, EvrData.EvrDataIOConfig and
       the evr modules in the configStore, which have the psana type EvrDataConfig.

        evr = EvrDictify(ds.env().configStore())
    """

    def __init__(self, configStore):
        if configStore.__class__.__name__ is not 'TabKeys':
            configStore = TabKeys(configStore)
        
        self._evr_dict = {}
        self._src_dict = {}
        self._output_maps = {}
        self._alias_dict = {str(a.src): a.aliasName for a in configStore.Alias.srcAlias}
        self._evr_keys = [attr for attr,item in configStore._evt_dict.items() \
                          if 'EvrDataConfig' in item['type']]

        for evr_key in self._evr_keys:
            evr_module = getattr(configStore, evr_key)
            for output_map in evr_module.output_maps:
                map_key = 'module{:}_conn{:02}'.format(output_map.module, output_map.conn_id)
                if str(output_map.source) == 'Pulse':
                    pulse_id = output_map.source_id
                    pulse=evr_module.pulses[pulse_id]
                else:
                    pulse_id = None
                    pulse = None

                output_map.add_property(evr=pulse)
                self._output_maps[map_key] = output_map
        try:
            for ch in configStore.EvrData.channels:
                output_map = ReDictify(ch.output)
                map_key = 'module{:}_conn{:02}'.format(output_map.module, output_map.conn_id)
                for i in range(ch.ninfo):
                    src = SrcDictify(ch.infos[i])
                    src.add_property(alias=self._alias_dict.get(src.src))
                    src.add_property(evr=self._output_maps[map_key].evr)
    #                src.add_property(output=output_map)
    #                src.add_property(map_key=map_key)
    #                src.add_property(output_map=self._output_maps[map_key])
                    self._evr_dict[src.src] = src
                    self._src_dict[src.src] = src.det_key
        except:
            pass

        for key, src in self._evr_dict.items():
            alias = self._alias_dict.get(key)
            if alias:
                setattr(self, alias, src)


class EpicsDictify(object):
    """Tab accessible dictified epics data from psana epicsStore.
       e.g., 
         epicsStore = EpicsDictify(ds)
         returns dictified representation of ds.env().epicsStore()
    """

    def __init__(self, ds):

        self._ds = ds

        pv_dict = {}
        epicsStore = self._ds.env().epicsStore()
        self.epicsConfig = EpicsConfig(self._ds.env().configStore())

        for pv in  epicsStore.names():
            name = re.sub(':|\.','_',pv)
            #check if valid -- some old data had aliases generated from comments in epicsArch files.
            if re.match("[_A-Za-z][_a-zA-Z0-9]*$", name) and not ' ' in name and not '-' in name:
                pvname = epicsStore.pvName(pv)
                if pvname:
                    pvalias = pv
                else:
                    pvalias = epicsStore.alias(pv)
                    pvname = pv

                pvalias = re.sub(':|\.|-| ','_',pvalias)

                components = re.split(':|\.|-| ',pv)
                if len(components) == 1:
                    components = re.split('_',pv,1)
                
                # check if alias has 2 components -- if not fix
                if len(components) == 1:
                    pv = '_'.join([components[0], components[0]])
                    components = re.split('_',pv,1)

                for i,item in enumerate(components):
                    if item[0].isdigit():
                         components[i] = 'n'+components[i]

                pv_dict[name] =  { 'pv': pvname,
                                   'alias': pvalias,
                                   'components': components,
                                 }
        self._pv_dict = pv_dict
        self._attrs = list(set([val['components'][0] for val in self._pv_dict.values()]))

    def __getattr__(self, attr):
        if attr in self._attrs:
            attr_dict = {key: pdict for key,pdict in self._pv_dict.items()
                         if pdict['components'][0] == attr}
            return PVdictify(attr_dict, self._ds, level=1)
        
        if attr in dir(self._ds.env().epicsStore()):
            return getattr(self._ds.env().epicsStore(),attr)

    def __dir__(self):
        all_attrs = set(self._attrs +
                        dir(self._ds.env().epicsStore()) +
                        self.__dict__.keys() + dir(EpicsDictify))
        return list(sorted(all_attrs))


class PVdictify(object):
    """Dot.dictifies a dictionary of {PVnames: values}.
    """

    def __init__(self, attr_dict, ds, level=0):
        self._attr_dict = attr_dict
        self._ds = ds
        self._level = int(level)
        self._attrs = list(set([pdict['components'][level]
                                for key,pdict in attr_dict.items()]))

    def _get_pv(self, pv):
        return EpicsStorePV(self._ds.env().epicsStore(), pv)

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
        items = sorted(self._attr_dict.items(), key=operator.itemgetter(0))
        for key,pdict in items:
            alias = pdict['alias']
            if alias:
                name = alias
                pv = pdict['pv']
            else:
                name = pdict['pv']
                pv = ''

            pvfunc = self._get_pv(pdict['pv'])
            value = pvfunc.value
            if pvfunc.isCtrl:
                comment = 'isCtrl'
            else:
                comment = ''

            try:
                info += '{:30s} {:12.4g} -- {:30s} {:10}\n'.format( \
                        name, value, pv, comment)
            except:
                info += '{:30s} {:>12} -- {:30s} {:10}\n'.format( \
                        name, value, pv, comment)
        return info

    def __getattr__(self, attr):
        if attr in self._attrs:
            attr_dict = {key: pdict for key,pdict in self._attr_dict.items()
                         if pdict['components'][self._level] == attr}
            if len(attr_dict) == 1:
                key = attr_dict.keys()[0]
                if len(self._attr_dict[key]['components']) == (self._level+1):
                    pv = self._attr_dict[key]['pv']
                    return self._get_pv(pv)
            if len(attr_dict) > 0:
                return PVdictify(attr_dict, self._ds, level=self._level+1)

    def __repr__(self):
        return self.get_info()

    def __dir__(self):
        all_attrs = set(self._attrs +
                        self.__dict__.keys() + dir(PVdictify))
        return list(sorted(all_attrs))


class EpicsStorePV(object):
    """Dictified psana class for epicsStore PV's. 
    """

    def __init__(self, epicsStore, pv):
        self._epicsStore = epicsStore
        self._pvname = pv
        self._store = epicsStore.getPV(pv)
        self._attrs = [attr for attr in dir(self._store) \
                if not attr.startswith('_')]
        self._show_attrs = [attr for attr in self._attrs \
                if attr not in ['dbr','stamp']]

    def get_info(self):
        info = '-'*80+'\n'
        info += '{:} = {:} -- {:}\n'.format(self._pvname, \
                                self.value, self.stamp)
        info += '-'*80+'\n'
        for attr in self._show_attrs:
            val = self.get(attr)
            info += '{:20} {:12}\n'.format(attr, val)
        
        return info

    def show_info(self):
        print self.get_info()

    def get(self, attr):
        if attr in self._attrs:
            if attr is 'value':
                return self._epicsStore.value(self._pvname)
            else:
                val = getattr(self._store,attr)
                try:
                    if attr is 'stamp':
                        return TimeStamp(val())
                    else:
                        return val() 
                except:
                    return val
        else:
            return None

    def __str__(self):
        return '{:}'.format(self.value)

    def __repr__(self):
        return '< {:} = {:}, {:} -- {:} >'.format(self._pvname, \
                self.value, self.stamp, \
                self.__class__.__name__)

    def __getattr__(self, attr):
        if attr in self._attrs:
            return self.get(attr)

    def __dir__(self):
        all_attrs = set(self._attrs +
                        self.__dict__.keys() + dir(EpicsStorePV))
        return list(sorted(all_attrs))


class TimeStamp(object):

    def __init__(self, stamp):
        self.sec = stamp.sec()
        self.nsec = stamp.nsec()

    @property
    def date(self):
        return time.strftime('%Y-%m-%d', 
                time.localtime(self.sec))

    @property
    def time(self): 
        EventTimeStr = time.strftime('%H:%M:%S',
                time.localtime(self.sec))
        EventTimeStr += '.{:04}'.format(int(self.nsec/1e5))
        return EventTimeStr

    def __str__(self):
        return '{:}.{:} sec'.format(self.sec, self.nsec)

    def __repr__(self):
        return '< {:}: {:} >'.format(self.__class__.__name_, _self.__str__)

def initArgs():
    """Initialize argparse arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("data_source", nargs='?', default=None, 
                        help='psana data_source')
    parser.add_argument("-e", "--exp", type=str, 
                        help='Experiment number')
    parser.add_argument("-r", "--run", type=int, default=-1, 
                        help='Run number')
    parser.add_argument("-i", "--instrument", type=str, 
                        help='Instrument')
    parser.add_argument("-s", "--station", type=int, 
                        help='Station')
#    parser.add_argument("--cfg", type=str, 
#                        help='psana cfg config file')
    parser.add_argument("--smd", action="store_true", 
                        help='Load smd small XTC data')
    parser.add_argument("--h5", action="store_true", 
                        help='Use hdf5 data instead of xtc')
    parser.add_argument("--xtc_dir", type=str, 
                        help='xtc file directory')
    parser.add_argument("-l", "--live", action="store_true", 
                        help='Use live data stream')
    parser.add_argument("--ffb", action="store_true", 
                        help='Use FFB data')
#    parser.add_argument("--epics_file", type=str, 
#                        help='epics alias file with epicsArch style file')
#    parser.add_argument("--epics_dir", type=str, 
#                        help='dir for epics_file used for epics aliases')
    parser.add_argument("--show_errors", action="store_true", default=False,
                        help='Show Errors in cases that might not be explicit ' \
                             'due to try/except statements')
    parser.add_argument("--indexed", action="store_true", default=False, 
            help='Use indexing, see: https://confluence.slac.stanford.edu/display/PSDM/psana+-+Python+Script+Analysis+Manual#psana-PythonScriptAnalysisManual-RandomAccesstoXTCFiles("Indexing")')
    parser.add_argument("-b", "--base", type=str, default='ds', 
                        help='Base into which DataSource object is initiated.')
    parser.add_argument("-P", "--monshmserver", type=str, default='psana', 
                        help='monshmserver source base for live data')
    return parser.parse_args()

def main():
    """Main script to initialize DataSource object in interactive python.
       Currently using ipsana.sh bash script to start this, but should look
       to using example Dan D. provided for IPython startup.
       /reg/neh/home/ddamiani/Workarea/psana-dev/psmon-dev/psmon/src/console.py

       Left some code from psutils module for automatically guessing experiment
       and instrument based on the user and local machine from which this is started.
       
       In future should add detection of data files to avoid trying to load 
       run data that does not exist, including checks that the code is being
       run on an appropriate machine.  If someone tries loading a file they do 
       not have access to, a message should be given how to get access (i.e., 
       ask the PI of the experiment to be added, and if sure are on experiment
       then submit ticket to appropriate mail list for assistance).
    """
    time0 = time.time()
    args = initArgs()
    print "*"*80
    print 'Loading interactive TabPsana with the following arguments:'
    for attr,val in vars(args).items():
        print "   {:} = {:}".format(attr, val)
    print "*"*80
#    if args.exp and not args.instrument:
#        args.instrument = args.exp[0:3]
#    
#    if not args.instrument:
#        args.instrument = psutils.instrument_guess()
#    
#    if not args.base:
#        args.base = args.instrument

    setattr(sys.modules['__main__'], args.base, DataSource(**vars(args)))

    run_info = getattr(sys.modules['__main__'], args.base)
    print ""
    print 'Load time = {:5.1f} sec'.format(time.time()-time0)
    print 'Data loaded for the psana data source', run_info
    print ""
    print "*"*80
    print '{:} is an python iterator for tab accessible psana data, e.g.,'.format(args.base)
    print ""
    print 'In [1]: evt = {:}.next()'.format(args.base)
    print 'In [2]: evt.Evr.eventCodes'
    print 'Out[2]: [140, 40]'
    print ""
    print "The current event is also available in the {:} object, e.g.,".format(args.base) 
    print ""
    print 'In [3]: ds.current.Evr.eventCodes'
    print 'Out[3]: [140, 40]'
    print ""
    print "*"*80

if __name__ == "__main__":
    sys.exit(main())

