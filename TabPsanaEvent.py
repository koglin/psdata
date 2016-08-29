import re
from DetectorDictify import DetectorDictify
import operator

def next_event(ds):
    """Return the next event from a psana data source.
    """
    return TabEvent(ds.events().next(), ds)

def load_run(data_source=None, instrument=None, exp=None, run=None,
             live=False, ffb=False, h5=False,
             indexed=None, **kwargs): 
    """-------------------------------------------------------------------------------
       TabPsanaEvent.load_run is a helper function to return psana.DataSource
       from the input data_source, e.g., given

            data_source = 'exp=CXI/cxic0115:run=10'

        The following are equivalent:

            ds = psana.DataSource(data_source)
            ds = TabPsanaEvent.load_run(data_source)
            ds = TabPsanaEvent.load_run(exp='cxic0115', run=10)

        You can also load a data source with keyword options:
        (indexed is currently not supported)

            h5:   loads hdf5 data instead of xtc
            ffb:  appends ':one-stream' to data source

        The shared memory data_source can be automatically loaded with the live keyword:

            ds = TabPsanaEvent.load_run(live=True)

        But shared memory should alse be automatically detected if no arguments are
        supplied and you are on a shared memery server.

    """
    import psana

    if live:
        indexed = False
        if not data_source:
            data_source = live_source(**kwargs)

#    if not indexed:
#        indexed = True
        
    if not data_source:

        if exp and run:
            instrument = exp[0:3]
 
            data_source = "exp={exp}:run={run}".format(exp=exp,run=run)
            
            if ffb:
                data_source += ":one-stream"
            elif h5:
                data_source += ":h5"
#            elif indexed:
#                data_source += ":idx"

        else:
            print 'No data source specified, so assume this is shared memory.'
            data_source = live_source(**kwargs)
            live = True
            indexed = False

    if data_source:
        try:
            ds = psana.DataSource(data_source)
            print 'You have successfully loaded data from', data_source
            print 'This is equivalent to loading it with the psana function:'
            print '   import psana'
            print '   ds = psana.DataSource({:})'.format(data_source)
            print ''
            print 'To get a tab accessible event structure for the next event:'
            print '   evt = TabPsanaEvent.next_event(ds)'
            return ds

        except:
            print 'Error loading', data_source
            print 'Check to make sure the data is present and try again'
    else:
        print 'You must supply either the data_source as an argument.'
        print 'or suplly exp and run kwargs.  For example.'
        print load_run.__doc__
        return None

#print load_run.__doc__

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
                evt_dict[alias] = {'src': src, 'alias': alias, 'type': {}, 'attrs': {}, 'module': module}
            evt_dict[alias]['type'].update({typ_name: {'typ': typ, 'src': src, 'alias': alias, 'key': key, 
                                                       'attrs': {attr: evt_funcs for attr in attrs}}})
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

    return '{attr:18s} {str:>10} {unit:6} {doc:}'.format(**fdict)

def func_value(func):
    try:
        func = func()
    except:
        pass

    if isinstance(func, list):
        func = [ReDictify(f) for f in func]

    return func

class TabEvent(object):
    """Tab access to reconstructed detector, evtData, configStore, epicsStore, and evrConfig. 
    """

    def __init__(self, evt, ds):
        """Initialize evtData and reconstructed detector classes.
           Lazy load configStore, evrConfig and epicsStore classes.
        """

        self._evt = evt
        self._ds = ds
        self._configStore = None
        self._evrConfig = None
        self._epicsStore = None
        self.evtData = TabKeys(self._evt)
        self.detector = DetectorDictify(self._evt, self._ds.env())
        self._attrs = self.evtData._evt_dict.keys() 

    @property
    def configStore(self):
        """ConfigStore.
        """
        if self._configStore is None:
            self._configStore = TabKeys(self._ds.env().configStore())

        return self._configStore

    @property
    def evrConfig(self):
        """Evr Configuration from objects in configStore.
        """
        if self._evrConfig is None:
            self._evrConfig = EvrDictify(self.configStore)

        return self._evrConfig

    @property
    def epicsStore(self):
        """Epics Store.
        """
        if self._epicsStore is None:
            self._epicsStore = EpicsDictify(self._ds)

        return self._epicsStore

    def show_all(self):
        """Show event summaries for each detector.
        """
        for attr in self._attrs:
            dat = getattr(self, attr)
            if dat and hasattr(dat, 'show_all') and attr != 'EventId':
                print ''
                print '*'*80
                print attr, 'Event Data Summary:'
                dat.show_all()

    def __getattr__(self, attr):
        if attr in self._attrs:
            return DetData(attr, self)

    def __dir__(self):
        all_attrs = set(self._attrs +
                        self.__dict__.keys() + dir(TabEvent))
        return list(sorted(all_attrs))

class DetData(object):
    """Combined data objects for a given detector with alias _det.
    """

    _data_attrs =  ['detector','evtData','epicsStore','configStore','evrConfig']
    
    def __init__(self, det, data):
        """If calibrated detector information is available provide it 
           in the first level of data access (e.g., for cameras, CsPad, ect.), 
           otherwise provide standard event data in first level of access 
           (e.g. Bld data such as EBeam and PhaseCavity).
        """
        self._det = det
        self._data = data
        if det in self._data.detector._current_dets:
            self._main_data = getattr(self._data.detector, det)
        else:
            self._main_data = getattr(self._data.evtData, det)
        
        self._main_attrs = [attr for attr in dir(self._main_data) \
                            if not attr.startswith('_')]

    def show_all(self):
        """Show data summary for detector including configStore, evrConfig and epicsStore.
        """
        for attr in self._data_attrs:
            dat = getattr(self, attr)
            if dat and hasattr(dat, 'show_info'):
                print '-'*80
                print self._det, attr
                print '-'*80
                dat.show_info()

    def __getattr__(self, attr):
        if attr in self._main_attrs:
            return getattr(self._main_data, attr)

        if attr in self._data_attrs:
            dat = getattr(self._data, attr)
            if dat and hasattr(dat, self._det):
                return getattr(dat, self._det)

    def __dir__(self):
        all_attrs = set(self._main_attrs +
                        self._data_attrs +
                        self.__dict__.keys() + dir(DetData))
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
        all_attrs = set(self._ddict['attrs'].keys() +
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
        repr_str = '<{:}.{:}>'.format(self._obj.__class__.__module__, \
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

        evr = TabPsana.EvrDictify(ds.env().configStore())

    """

    def __init__(self, configStore):
        if configStore.__class__.__name__ is not 'TabKeys':
            configStore = TabKeys(configStore)
        
        self._evr_dict = {}
        self._src_dict = {}
        self._output_maps = {}
        self._alias_dict = {str(a.src): a.aliasName for a in configStore.Alias.srcAlias}
        self._evr_keys = [attr for attr,item in configStore._evt_dict.items() if 'EvrDataConfig' in item['type']]

        print 

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
                info += '{:30s} {:10.4g} -- {:30s} {:10}\n'.format( \
                        name, value, pv, comment)
            except:
                info += '{:30s} {:>10} -- {:30s} {:10}\n'.format( \
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
        return '< {:} = {:}, {:} -- {:}>'.format(self._pvname, \
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
        return '< {:} -- {:}>'.format(self.__str__, \
                self.__class__.__name__)

def evt_aliases(self):
    """Currently not actively used.
       Faster than evt_dict, eventually want to build a 
       dictionary of psana modules upon loading this class.
    """
    evt_aliases = {}
    for evt_key in self.keys():
        typ = evt_key.type()
        if typ:
            alias = evt_key.alias()
            if not alias:
                src = evt_key.src()
                key = evt_key.key()
                psana_module = typ.__module__
                module = psana_module.lstrip('psana').lstrip('.')
                if hasattr(src, 'typeName'):
                    alias = src.typeName()
                elif key:
                    alias = key
                elif module:
                    alias = module
                else:
                    psana_class = typ.__name__
                    alias = psana_class
                    
            if alias:
                alias = alias.replace('-','_')

            evt_aliases.update({alias: evt_key})

    return evt_aliases


