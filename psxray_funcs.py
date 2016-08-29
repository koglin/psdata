import re
import time
import psana
import numpy as np

psana_omit_list = ['logging', 'os', 'setConfigFile', 'setOption', 'setOptions']
psana_dict = {a: {} for a in dir(psana) if not a.startswith('_') \
              and not a.startswith('ndarray') and a not in psana_omit_list}

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

def func_dict(func, attr=None):
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

    if hasattr(func, '__func__'):
        fdict['attr'] = func.__func__.__name__
    else:
        try:
            fdict['attr'] = func.__name__
        except:
            if attr:
                fdict['attr'] = attr
            else:
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

def func_repr(func, name=None, attr=None):
    """psana function represenatation
    """
    fdict = func_dict(func, attr=attr)
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


func_omit_list = ['DamageMask', 'TypeId', 'Version']
for mod_name in psana_dict:
    mod = getattr(psana,mod_name)
    psana_dict[mod_name] = {a: {} for a in dir(mod) if not a.startswith('_')}
    for typ_name in psana_dict[mod_name]:
        typ = getattr(mod, typ_name)
        psana_dict[mod_name][typ_name] = {a: {} for a in dir(typ) \
                    if not a.startswith('_') and a not in func_omit_list}
        for attr in psana_dict[mod_name][typ_name]:
            func = getattr(typ, attr)
            doc = func.__doc__
            if doc:
                doc = doc.split('\n')[-1].lstrip(' ')
            info = {'doc': doc, 
                    'unit': get_unit_from_doc(func.__doc__), 
                    'type': get_type_from_doc(func.__doc__)}
            psana_dict[mod_name][typ_name][attr] = info 


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

def edict(evt, smd=True, quiet=True):
    evt_dict = {}
    for evt_key in evt.keys():
        typ = evt_key.type()
        if typ:
            src = evt_key.src()
            key = evt_key.key()
            alias = evt_key.alias()
            psana_class = typ.__name__
            psana_module = typ.__module__
            module = psana_module.lstrip('psana').lstrip('.')
            if not module:
                module = psana_class
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
 
            pdict =  { 'class': psana_class, 
                       'module': module,
                       'type': typ,
                       'src': src,
                       'key': key,
                       'evt_key': evt_key, 
                       'alias': alias
                      }
            
            if module in ['Epics']:
                alias = module
            elif module in ['EvrData']: # and typ_name == 'EvrDataConfig':
                alias = module
                typ_name = str(src) 
            elif str(src).startswith('ProcInfo'):
                alias = module
                typ_name = str(src) 

            if alias not in evt_dict:
                evt_dict[alias] = {}
           
            if not quiet:
                print alias, module, typ_name 
            
            if alias == 'EventId':
                f = evt.get(typ,src)
                evt_dict[alias] = get_EventId(f)
            
            elif alias == 'EvrData' and typ_name == 'EvrDataData':
                f = evt.get(typ,src)
                evt_dict[alias] = get_EvrData(f)
            
#            elif alias == 'DgramList':
#                f = evt.get(typ,src)
#                evt_dict[alias] = get_DgramList(f)
            
            elif module == 'Bld':
                f = evt.get(typ,src)
                evt_dict[alias].update({typ_name: get_key_dict(f)})
   
            elif not smd:
                f = evt.get(typ,src)
                evt_dict[alias].update({typ_name: get_key_dict(f)})

#           evt_dict[alias][typ_name]['psana'] = pdict
 
    return evt_dict

def xevt(evt, xdict=None):
    e = edict(evt)
    if not xdict:
        new_xdict = {}
    for alias, item in e.items():
        if alias == 'EventId':
            typ, data = alias, item
            if not xdict:
                new_xdict.update(**{'_'.join([alias,attr]): [val] \
                                    for attr,val in data.items()})
            else:
                for attr, val in data.items():
                    xdict['_'.join([alias,attr])].append(val)
        elif item:
            for typ, data in item.items():
                if not xdict:
                    new_xdict.update(**{'_'.join([alias,attr]): [val] \
                                        for attr,val in data.items()})
                else:
                    for attr, val in data.items():
                        xdict['_'.join([alias,attr])].append(val)

    if not xdict:
        xdict = new_xdict

    return  xdict

def make_xray(xdict):
    import xray
    x = {attr: (['time'], np.array(item)) for attr, item in xdict.items()}
    return xray.Dataset(x,coords={'time': x['EventId_timef64'][1]})

def get_key_dict(f):
    """Return a dictionary of a psana evt key.
    """
    m = f.__module__.lstrip('psana.')
    n = f.__class__.__name__
    return {attr: get_func_value(getattr(f,attr)) for attr in psana_dict[m][n]}

def func_redict(f):
    """Resolve the full function.
    """
    if hasattr(f, '__module__') and f.__module__.startswith('psana'):
        m = f.__module__.lstrip('psana.')
        n = f.__class__.__name__
        if n in psana_dict[m]:
            return {attr: get_func_value(getattr(f,attr)) for attr in psana_dict[m][n]}

        else:
            attrs = [attr for attr in dir(f) if not attr.startswith('_')]
            try:
                return {attrs: getattr(f,attr) for attrs in attrs}
            except:
                return f
    
    else:
        return f

def get_func_value(func):
    """Return the value of a psana object.
    """
    try:
        func = func()
    except:
        pass

    if isinstance(func, list):
        func = [func_redict(f) for f in func]
    else:
        try:
            func = func_redict(func)
        except:
            pass

    return func


def get_EpicsConfig(f):
    attrs = ['description', 'interval', 'pvId']
    pvs = {}
    for pv in f.getPvConfig():
        pvdict = {attr: getattr(pv, attr)() for attr in attrs} 
        pvs[pv.description()] = pvdict
    
    epicsdict =  {'numPv': f.numPv(), 
                  'getPvConfig': pvs,  
                  'TypeId': f.TypeId, 
                  'Version': f.Version}

    return epicsdict

def get_EvrData(f):
    fifoattrs = ['eventCode', 'timestampHigh', 'timestampLow']
    fifoEvents = [{a: getattr(b,a)() for a in fifoattrs} for b in f.fifoEvents()]

    evrdict = {'numFifoEvents': f.numFifoEvents(),
               'fifoEvents': fifoEvents}

    for attr in fifoattrs:
        evrdict.update({attr+'s': [a[attr] for a in fifoEvents]})

    return evrdict

def get_DgramList(f):
    attrs = ['getFileNames', 'getOffsets']
    return {attr: getattr(f, attr)() for attr in attrs}

def get_EventId(f):
    attrs = ['fiducials', 'idxtime', 'run', 'ticks', 'vector']
    eid = {attr: getattr(f, attr)() for attr in attrs}
    etime = getattr(f, 'time')()
    eid['timef64'] = np.float64(etime[1])+np.float64(etime[0])/1.e9

    try:
        EventTimeStr = time.strftime('%H:%M:%S',
                time.localtime(etime[0]))
        EventTimeStr += '.{:04}'.format(int(etime[1]/1e5))
    except:
        EventTimeStr = 'NA'

    eid['str'] = EventTimeStr
    
    return eid

def get_config_map(f):
    output_attrs = [a for a in dir(f) if not a.startswith('__') and not a[0].isupper()]
#    output_attrs = ['conn', 'conn_id', 'map', 'module', 'source', 'source_id', 'value']
    return {attr: getattr(f,attr)() for attr in output_attrs}

def get_IOConfig(f):
    channels = {}
    for c in f.channels():
        channels[c.name()] = {'infos': c.infos()[0:c.ninfo()], 
                              'ninfo': c.ninfo(),
                              'output': get_config_map(c.output())} 

    return channels

# elif module == 'Epics' and n.startswith('Config'):

#            nn = ''
#            if nn == 'Source':
#                return {f.src(): f.group()}
#            elif nn == 'SrcAlias':
#                return {f.src(): f.aliasName()}
#            else:

#def get_EvrConfig(f):
#    attrs = ['neventcodes','noutputs','npulses']
#    evrdict =  {attr: getattr(f, attr)() for attr in attrs}
#    evrdict['output_maps'] = {}
#    for output_map in f.output_maps():
#        map_key = 'module{:}_conn{:02}'.format(output_map.module(), output_map.conn_id())
#        evrdict['output_maps'].update({map_key: get_config_map(output_map)})
#
#    evrattrs = [a for a in dir(f.pulses()[0]) if not a.startswith('__')]
#    print evrattrs
#    evrdict['pulses'] = [{attr: getattr(a, attr)() for attr in evrattrs} \
#                         for a in f.pulses()]
#    evrattrs = [a for a in dir(f.eventcodes()[0]) \
#                if not a.startswith('__') and not a[0].isupper()]
#    evrdict['eventcodes'] = [{attr: getattr(a, attr)() for attr in evrattrs} \
#                             for a in f.eventcodes()]
#
#    return evrdict



#    cdict = {}
#    try:
#        m = f.__module__.lstrip('psana.')
#        n = f.__class__.__name__
##        if n.startswith('IOConfig'):
##            cdict = get_IOConfig(f)
##        elif m == 'Epics' and n.startswith('Config'):
##            cdict = get_EpicsConfig(f)
###        elif m == 'EvrData':
###            cdict = get_EvrConfig(f)
##        else:
#        for attr in psana_dict[m][n]:
#            if not attr.startswith(('_','TypeId','Version','DamageMask')):
#                cdict[attr] = fvalue(getattr(f,attr))
#    except:
#        print 'Handle:', f
#        cdict = {f:f}
#
#    return cdict

_work_dict = {}



def get_evrconfig(cdict):

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
                self._evr_dict[src.src] = src
                self._src_dict[src.src] = src.det_key
    except:
        pass

    for key, src in self._evr_dict.items():
        alias = self._alias_dict.get(key)
        if alias:
            setattr(self, alias, src)


