# import standard python system tools
import re
import operator
import time
import numpy as np
import psana

psana_omit_list = ['logging', 'os', 'setConfigFile', 'setOption', 'setOptions']

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

def func_dict(attr, func):
    """psana attribute function dictionary.
    """
    fdict = {'attr': attr,
             'doc': '',
             'unit': '',
             'str':  'NA',
             'func': func}

    value = func
    try:
        value = value()
    except:
        pass

    if isinstance(value,str):
        fdict['str'] = value
    else:
        if hasattr(value,'mean'):
            fdict['str'] = '<{:.4}>'.format(value.mean())
        else:
            try:
                doc = func.__doc__.split('\n')[-1].lstrip(' ')
                fdict['doc'] = doc
                fdict['str'] = '{:10.5g}'.format(value)
                fdict['unit'] = get_unit_from_doc(doc)
                fdict['type'] = get_type_from_doc(doc)
            except:
                try:
                    fdict['str'] = value.__str__()
                except:
                    pass

    fdict['value'] = value

    return fdict

def func_repr(attr, func):
    """psana function represenatation
    """
    fdict = func_dict(attr, func)

    return '{attr:18s} {str:>10} {unit:6} {doc:}'.format(**fdict)


psana_dict = {a: {} for a in dir(psana) if not a.startswith('_') and not a.startswith('ndarray') and a not in psana_omit_list}
for mod_name in psana_dict:
    mod = getattr(psana,mod_name)
    psana_dict[mod_name] = {a: {} for a in dir(mod) if not a.startswith('_')}
    for typ_name in psana_dict[mod_name]:
        typ = getattr(mod, typ_name)
        psana_dict[mod_name][typ_name] = {a: {} for a in dir(typ) if not a.startswith('_')}
        for attr in psana_dict[mod_name][typ_name]:
            func = getattr(typ, attr)
            doc = func.__doc__
            if doc:
                doc = doc.split('\n')[-1].lstrip(' ')
            info = {'doc': doc, 
                    'unit': get_unit_from_doc(func.__doc__), 
                    'type': get_type_from_doc(func.__doc__)}
            psana_dict[mod_name][typ_name][attr] = info 

def psana_evt_dict(evt):
    evt_dict = {}
    for evt_key in evt.keys():
        key_dict = psana_key_dict(evt_key)
        if key_dict and key_dict['det_name'] not in evt_dict:
            evt_dict[key_dict['det_name']] = {}

        evt_dict
    return evt_dict

def psana_key_dict(evt_key):
    if evt_key:
        typ = evt_key.type()
    else:
        return None

    if typ:
        typ = evt_key.type()
        src = evt_key.src()
        alias = evt_key.alias()
        key = evt_key.key()
        psana_class = typ.__name__
        psana_module = typ.__module__
        module = psana_module.lstrip('psana').lstrip('.')
        typ_name = key+module.lstrip('Bld')+typ.__name__
        det_name = alias
        if re.search(r"V.?\b", typ_name):
            typ_name = typ_name[:-2]
        if not det_name:
            if hasattr(src, 'typeName'):
                det_name = src.typeName()
            elif key:
                det_name = key
            else:
                det_name = module+psana_class
        det_name = det_name.replace('-','_')
        attrs =  {attr: {} for attr in dir(typ) if not attr.startswith(('_','TypeId','Version'))}
        return {'det_name': det_name, 'typ_name': typ_name,
                'typ': typ, 'src': src, 'alias': alias, 'key': key, 
                'attrs': attrs}
    else:
        return None

class PsanaDict(object):
    """Tab accessible dictified data from psana keys.
       e.g., 
            evt = PsanaDict(ds.events().next())
            configStore = PsanaDict(ds.env().configStore())
    """

    _init_attrs = ['get','put','keys']

    def __init__(self, evt, ):
        for attr in self._init_attrs:
            setattr(self, attr, getattr(evt, attr))

        self._det_dicts = {}
        self._evt_dict = psana_evt_dict(evt)

    def __getattr__(self, attr):
        if attr in self._alias_dict:
            attr = self._alias_dict[attr]
        if attr in self._evt_dict:
            if attr not in self._det_dicts:
                self._det_dicts[attr] = DetDictify(self._evt_dict[attr])

            return self._det_dicts.get(attr, None)

    def __dir__(self):
        all_attrs = set(self._evt_dict.keys() + 
                        self.__dict__.keys() + dir(PsanaDict))
           
        return list(sorted(all_attrs))

class DetDictify(object):
    """Dictify the detectors with types.
    """
    def __init__(self, evt_dict, det, show_attrs=False):
        self._det = det
        self._evt_dict = evt_dict
        self._det_dict = evt_dict[det]
        self._typ_dicts = {}

    def show_info(self, **kwargs):
        for typ in self._det_dict:
            getattr(getattr(self,typ),'show_info')(**kwargs)

    def __repr__(self):
        repr_str = '< {:} {:}>'.format(self._det, self.__class__.__name__)
        self.show_info()
        return repr_str

    def __getattr__(self, attr):
        if attr in self._det_dict:
            if attr not in self._typ_dict:
                self._typ_dict[attr] = TypeDictify(self._det_dict, attr)
            
            return self._typ_dict[attr]

    def __dir__(self):
        all_attrs = set(self._det_dict.keys() + 
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

    def __init__(self, det_dict, typ):
        self._typ = typ
        self._attrs = det_dict[det][typ]['attrs'] 
        self._show_attrs = self._attrs.keys()

    def get_attr(self, attr):
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
            if item.__class__.__name__ is 'ReDictify':
                print func_repr(attr, self._attrs[attr]) 
            else:
                print func_repr(attr, self._attrs[attr]) 

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
                info += func_repr(attr, value)+'\n'

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


class PsanaProperty(object):
    """Psana data property class, which parses doc string from psana get function.
    """

    def __init__(self,  func):
        self._func = func
        self._value = None

    @property
    def value(self):
        value = self._func
        try:
#            print 'was func'
            value = value()
        except:
            pass

        if hasattr(value, '__dict__'):
#            print 'has dict'
            if hasattr(value,'__func__'):
#                print 'still has func'
                try:
                    value = value()
                except:
                    pass

        elif isinstance(value, list):
#            print 'is list'
            try:
                return [ReDictify(val) for val in value]
            except:
                return [val() for val in value]
        elif hasattr(value, '__func__'):
#            print 'is func'
            try:
                value = value()
            except:
                pass

        if value.__class__.__module__.startswith('psana'):
            try:
                print 'ReDictify'
                value = ReDictify(value)
            except:
                print 'could not redictify'
                pass

        return value

    @property
    def doc(self):
        if hasattr(self.value,'mean'):
            return ''
        else:
            return self._func.__doc__.split('\n')[-1].lstrip(' ')

    @property
    def unit(self):
        """Parse the unit from the function doc string.
        """
        if hasattr(self.value,'mean'):
            return 'NA'
        else:
            try:
                unit = '{:}'.format(self.doc.rsplit(' in ')[-1])
                unit = unit.rstrip('.').rstrip(',').rsplit(' ')[0].rstrip('.').rstrip(',')
                if unit in 'Value':
                    unit = '{:}'.format(self.doc.rsplit('converted to ')[-1].rstrip('.'))
                
                if unit.endswith('(') or unit in ['long', 'all', 'setup', 'given']:
                    unit = ''
            
            except:
                unit = ''
            
            return unit

    @property
    def name(self):
        return self._func.__name__

    @property
    def type(self):
        """Parse the type from the doc string
        """
        return get_type_from_doc(self.doc)

    def __str__(self):
        try:
            return '{:10.5g}'.format(self.value)
        except:
            return str(self.value)

    def __repr__(self):
        return '{:18s} {:>10} {:6} {:}'.format(self.name, self.__str__(), self.unit, self.doc)


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
            if re.match("[_A-Za-z][_a-zA-Z0-9]*$", name):
                pvname = epicsStore.pvName(pv)
                if pvname:
                    pvalias = pv
                else:
                    pvalias = epicsStore.alias(pv)
                    pvname = pv

                components = re.split(':|\.',pv)
                if len(components) == 1:
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
                         if pdict['components'][0] in attr}
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
    """

    def __init__(self, configStore):
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

        for key, src in self._evr_dict.items():
            alias = self._alias_dict[key]
            setattr(self, alias, src)
        



