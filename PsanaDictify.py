# import standard python system tools
import re
import operator
import time
import numpy as np

class PsanaDictify(object):
    """Tab accessible dictified data from psana keys.
       e.g., 
            evt = PsanaDictify(ds.events().next())
            configStore = PsanaDictify(ds.env().configStore())
    """

    _init_attrs = ['get','put','keys']

    def __init__(self, dat, ):
        for attr in self._init_attrs:
            setattr(self, attr, getattr(dat,attr))
        
        if self.__class__.__name__ == 'Event':
            attr = 'run'
            setattr(self, attr, getattr(dat,attr))

        self._dat = dat
        self._det_dicts = {}
        self._build_keys_dict()
    

    def __getattr__(self, attr):
        if attr in self._alias_dict:
            attr = self._alias_dict[attr]
        if attr in self._keys_dict:
            if attr not in self._det_dicts:
                self._det_dicts[attr] = DetDictify(self._keys_dict, attr)

            return self._det_dicts.get(attr, None)

    def __dir__(self):
        all_attrs = set(self._keys_dict.keys() + 
#                        self._alias_dict.keys() +
                        self.__dict__.keys() + dir(PsanaDictify))
           
        return list(sorted(all_attrs))

    def _build_keys_dict(self, keys_dict={}):
        """Builds self._keys_dict dictionary from psana keys.
           Builds self._alias_dict dictionary of aliases based on info in psana keys.
        """
        keys_dict = {}
        for evt_key in self.keys():
            if evt_key.type() is not None:
                key_dict = {}
                if hasattr(evt_key,'src'):
                    src = evt_key.src()
                else:
                    src = evt_key
                
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
                elif evt_key.key():
                    key_split = re.split(':|_|-|',evt_key.key())
                    det_key = '_'.join(key_split)
                    src_attrs = []
                else:
                    src_attrs = []
                    det_key = None

                if hasattr(evt_key,'alias'):
                    alias = evt_key.alias()

# Put the event object with attributes into a dictionary 
# in order to better handle evaluating the functions 
# as properties and to keep the functions in order
# to extract the relevant part of the doc string as
# a description and units.

                key_dict['data_key'] = evt_key.key()

                psana_module = evt_key.type().__module__
                module = psana_module.lstrip('psana.')
                psana_class = evt_key.type().__name__

                if not det_key and hasattr(src, 'processId'):
                    det_key = module

        # Bld data do not yet have aliases -- ask daq group to add consistent ones.
        # The psana_class names all begin with Bld, so the module 'Bld' is redundant and can be ommitted.
                if module == 'Bld':
                    device = evt_key.key()+psana_class
                    if not alias:
                        if det_key[-2] in '_':
                            alias = det_key[:-2]
                        else:
                            alias = det_key
                else:
                    device = evt_key.key()+module+psana_class

                type_key = device
        ## strip of Version Number
                if re.search(r"V.?\b", device):
                     device = device[:-2]

                if psana_class == 'EventId':
                    alias = psana_class
                    key_dict.update({'TypeId': 0,
                                     'Version': 0})
                elif psana_class == 'DgramList':
                    alias = psana_class
                    key_dict.update({'TypeId': 9998,
                                     'Version': 0})
                else:
                    if evt_key.type() is None or not hasattr(evt_key.type(),'TypeId'):
                        key_dict.update({'TypeId': 9999,
                                         'Version': 0})
                    else:
                        key_dict.update({'TypeId': evt_key.type().TypeId,
                                         'Version': evt_key.type().Version})

                key_dict.update({'psana_module': psana_module,
                                 'psana_class': psana_class,
                                 'device': device})
                
                if det_key:
                    det_key = det_key.replace('-','_')
                else:
                    det_key = psana_class

                if not alias:
                    alias = det_key

                if alias:
                    alias = alias.replace('-','_')

                if alias in keys_dict:
                    det_dict = keys_dict[alias]['det']
                else:
                    keys_dict[alias] = {}
                    det_dict = {'alias': alias,
                                'det_key': det_key,
                                'attr_type': {},
                                'type_list': [],
                                'types': {},
                                'duplicate_attrs': []}
                    for attr in src_attrs:
                        det_dict[attr] = getattr(src,attr)()

                evt_funcs = self.get(evt_key.type(), 
                                     evt_key.src(), 
                                     evt_key.key())
                det_dict['type_list'].append(device)
                det_dict['types'][device] = evt_key.type()
                if key_dict.get('data_key') and src_attrs:
                    attr = key_dict['data_key']
                    key_dict['attrs'] = {attr: evt_funcs}
                    if attr in det_dict['attr_type']:
                        det_dict['duplicate_attrs'].append(attr)
                    det_dict['attr_type'][attr] = device
                else:
                    key_dict['attrs'] = {}
                    for attr in dir(evt_key.type()):
                        if not attr.startswith(('_','TypeId','Version')):
                            key_dict['attrs'][attr] = getattr(evt_funcs, attr)
                            det_dict['attr_type'][attr] = device

                key_dict.update({'det_key': det_key,
                                 'evt_key': evt_key,
                                 'type_key': type_key})

                keys_dict[alias]['det'] = det_dict
                keys_dict[alias][device] = key_dict

        self._keys_dict = keys_dict
        self._alias_dict = {item['det']['det_key']: alias for alias,item in keys_dict.items()}

class DetDictify(object):
    """Dictify the detectors with types.
    """
#    _typ_module_path = ''
#    
#    _default_types = {
#            'AliasConfig': {
#                'module': 'PsanaTypeClasses',
#                'class':  'AliasConfig'
#                },
#            'EpicsConfig': {
#                'module': 'PsanaTypeClasses',
#                'class':  'EpicsConfig'
#                },      
#            }

    def __init__(self, keys_dict, det, show_attrs=True):
        import PsanaTypeConfig
        self._det = det
        self._keys = keys_dict[det]
        if show_attrs:
            self._attr_type = self._keys['det']['attr_type']
        else:
            self._attr_type = {}
        self._attrs = self._attr_type.keys()

        self._types = {}
        for typ in keys_dict[det]['det']['type_list']:
            self._types[typ] = TypeDictify(keys_dict, det, typ)
            typ_def = getattr(PsanaTypeConfig, typ, None)
            if typ_def:
                typ_def(self._types[typ])

#            typ_class = getattr(PsanaTypeClasses, typ, TypeDictify) 
#            if typ in self._default_types:
#                mod_dict = self._default_types[det] 
#                print mod_dict['module']
#                print mod_dict['class']
#                typ_class = getattr(PsanaTypeClasses, \
#                                    mod_dict['class'])
#            else:
#                typ_class = TypeDictify

#            self._types[typ] = typ_class(keys_dict, det, typ)

    def get_det_type(self, type):
        return self._types.get(type)

    def get_det_attr(self, attr):
        if attr in self._attr_type:
            type = self._attr_type[attr]
            return self._types[type].get_attr(attr)
        else:
            return None

    def show_info(self, **kwargs):
        for typ in self._types:
            getattr(getattr(self,typ),'show_info')(**kwargs)

    def __repr__(self):
        repr_str = '< {:} {:}>'.format(self._det, self.__class__.__name__)
        self.show_info()
        return repr_str

    def __getattr__(self, attr):
        if attr in self._types.keys():
            return self._types[attr]
        elif attr in self._attr_type.keys():
            type = self._attr_type[attr]
            return self._types[type].get_attr(attr)

    def __dir__(self):
        all_attrs = set(self._types.keys() + 
                        self._attr_type.keys() +
                        self.__dict__.keys() + dir(DetDictify))
           
        return list(sorted(all_attrs))

class TypeDictify(object):
    """Dictified psana data type.
       If the data attribute is a list of length less than 100, 
       currently the data list will be re-dictified once it is
       looked at.  In the future will try to anticipate that the
       data will be a list from the configStore, but for now
       only expand when it is looked at to avoid overhead in 
       creating dictified un-relevant dictified data.
    """

    def __init__(self, keys_dict, det, typ):
        self._det = det
        self._typ = typ
        self._attrs = keys_dict[det][typ]['attrs'] 
        self._show_attrs = self._attrs.keys()

    def get_attr(self, attr):
        if attr in self._attrs:
            value = self._attrs[attr]        
#            print 'getting', attr, value
            try:
#                print 'was func'
                value = value()
            except:
                pass
            
            if hasattr(value, '__dict__'):
#                print 'has dict'
                if hasattr(value,'__func__'):
#                    print 'still has func'
                    try:
                        value = value()
                    except:
                        pass
                
            elif isinstance(value, list):
#                print 'is list'
                value_list = []
                for val in value:
                    if val.__class__.__module__.startswith('psana'):
                       value_list.append(ReDictify(val))
                    else:
                        try:
                            value_list.append(val())
                        except:
                            value_list.append(val)
                        
                return value_list
#                try:
#                    return [ReDictify(val) for val in value]
#                except:
#                    return [val() for val in value]
            elif hasattr(value, '__func__'):
#                print 'is func'
                try:
                    value = value()
                except:
                    pass
        
        else:
            return None
        
        if value.__class__.__module__.startswith('psana'):
            try:
#                print 'ReDictify'
                value = ReDictify(value)
            except:
                print 'could not redictify'
                pass

        return value

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
    
    def show_info(self, attrs=None, **kwargs):
        print '-'*80
        print self._det, self._typ
        print '-'*80
        if not attrs:
            attrs = list(sorted(self._show_attrs))
        for attr in attrs:
            item = self._attrs[attr]
            print func_repr(self._attrs[attr], name=attr) 

    def __repr__(self):
        repr_str = '< {:} {:} {:}>'.format(self._det, self._typ, self.__class__.__name__) 
        self.show_info()
        return repr_str

    def __getattr__(self, attr):
        if attr in self._attrs:
            return self.get_attr(attr)

    def __dir__(self):
        all_attrs = set(self._attrs.keys() + 
                        self.__dict__.keys() + dir(TypeDictify))
           
        return list(sorted(all_attrs))

class ReDictify(object):
    """Class for re-dictifying psana data attributes that are lists.
    """

    def __init__(self, obj):
        self._obj = obj
        attrs = [attr for attr in dir(obj) if not attr.startswith('_')]
        self._attrs = {}
        for attr in attrs:
#            self._attrs[attr] = PsanaProperty(getattr(obj, attr))
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
        self.show_info()
        return repr_str

    def __getattr__(self, attr):
        if attr in self._attrs:
            return self._attrs[attr]

    def __dir__(self):
        all_attrs = set(self._attrs.keys() + 
                        self.__dict__.keys() + dir(ReDictify))
           
        return list(sorted(all_attrs))


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
        if hasattr(value,'mean'):
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
#                         if pdict['components'][0] in attr}
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
#        return self._ds.env().epicsStore().getPV(pv)

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
#                    pvdata = self._get_pv(pv)
##                    if pvdata.isCtrl():
##                        val = None
##                        print 'Warning: {pv} pv is ctrl'.format(pv=pv)
##                    else:
#                    val = pvdata.value(0)
#                    return val
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

        evr = PsanaDictify.EvrDictify(ds.env().configStore())

    """

    def __init__(self, configStore):
        if not hasattr(configStore, '_alias_dict'):
            configStore = PsanaDictify(configStore)
        
        self._evr_dict = {}
        self._src_dict = {}
        self._output_maps = {}
        self._alias_dict = {str(a.src): a.aliasName for a in configStore.Alias.AliasConfig.srcAlias}
        self._evr_keys = [attr for attr,item in configStore._keys_dict.items() if 'EvrDataConfig' in item]

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
        


#class PsanaProperty(object):
#    """Psana data property class, which parses doc string from psana get function.
#    """
#
#    def __init__(self,  func):
#        self._func = func
#        self._value = None
#
#    @property
#    def value(self):
#        value = self._func
#        try:
##            print 'was func'
#            value = value()
#        except:
#            pass
#
#        if hasattr(value, '__dict__'):
##            print 'has dict'
#            if hasattr(value,'__func__'):
##                print 'still has func'
#                try:
#                    value = value()
#                except:
#                    pass
#
#        elif isinstance(value, list):
##            print 'is list'
#            try:
#                return [ReDictify(val) for val in value]
#            except:
#                return [val() for val in value]
#        elif hasattr(value, '__func__'):
##            print 'is func'
#            try:
#                value = value()
#            except:
#                pass
#
#        if value.__class__.__module__.startswith('psana'):
#            try:
#                print 'ReDictify'
#                value = ReDictify(value)
#            except:
#                print 'could not redictify'
#                pass
#
#        return value
#
#    @property
#    def doc(self):
#        if hasattr(self.value,'mean'):
#            return ''
#        else:
#            return self._func.__doc__.split('\n')[-1].lstrip(' ')
#
#    @property
#    def unit(self):
#        """Parse the unit from the function doc string.
#        """
#        if hasattr(self.value,'mean'):
#            return 'NA'
#        else:
#            try:
#                unit = '{:}'.format(self.doc.rsplit(' in ')[-1])
#                unit = unit.rstrip('.').rstrip(',').rsplit(' ')[0].rstrip('.').rstrip(',')
#                if unit in 'Value':
#                    unit = '{:}'.format(self.doc.rsplit('converted to ')[-1].rstrip('.'))
#                
#                if unit.endswith('(') or unit in ['long', 'all', 'setup', 'given']:
#                    unit = ''
#            
#            except:
#                unit = ''
#            
#            return unit
#
#    @property
#    def name(self):
#        return self._func.__name__
#
#    @property
#    def type(self):
#        """Parse the type from the doc string
#        """
#        return get_type_from_doc(self.doc)
#
#    def __str__(self):
#        try:
#            return '{:10.5g}'.format(self.value)
#        except:
#            return str(self.value)
#
#    def __repr__(self):
#        return '{:18s} {:>10} {:6} {:}'.format(self.name, self.__str__(), self.unit, self.doc)
#
#
