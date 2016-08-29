import psana

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


def get_config(configStore, attr, cls='Config'):
    configs = getattr(getattr(psana, attr),cls)
    configs.reverse()
    for config in configs:
        obj = configStore.get(config)
        if obj:
            return obj


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

def edict(evt):
    d = {}
    for key in evt.keys():
        typ = key.type()
        src = key.src()
        if typ:
            srcstr = str(src)
            if srcstr not in d:
                d[srcstr] = {}

            f = evt.get(typ,src)
            d[srcstr].update(**fdict(f))
    return d

def fdict(f):
    fdict = {}
    try:
        m = f.__module__.lstrip('psana.')
        n = f.__class__.__name__
        for attr in psana_dict[m][n]:
            if not attr.startswith(('_','TypeId','Version','DamageMask')):
                fdict[attr] = fvalue(getattr(f,attr))
    except:
        print 'Skip', f

    return fdict

def fvalue(func):
    try:
        func = func()
    except:
        pass

    if isinstance(func, list):
        func = [fdict(f) for f in func]

    return func

class EvtKeys(object):

    _init_attrs = ['get','put','keys', 'remove', 'run']

    def __init__(self, evt, aliases=None):

        self._aliases = aliases
        self._src_alias = {v: a for a,v in self._aliases.items()} 
        self._evt = evt
        d = {}
        for key in evt.keys():
            typ = key.type()
            src = key.src()
            if typ:
                srcstr = str(src)
                if srcstr not in d:
                    d[srcstr] = []
                
                m = typ.__module__.lstrip('psana.')
                n = typ.__name__
                if m:
                    attrs = [attr for attr in psana_dict[m][n] \
                            if not attr.startswith(('_','TypeId','Version','DamageMask'))]
                else:
                    attrs = []

                d[srcstr].append({typ: attrs})

        self._src_attrs = d

    def show_info(self):
        """Show attributes in data object.
        """
        for typ in self._src_attrs:
            for attr in typ:
                getattr(self, attr).show_info()

    def __getattr__(self, attr):
        if attr in self._init_attrs:
            return getattr(self._evt, attr)
        
        if attr in self._aliases:
            return TypTab(self._src_attrs)

    def __dir__(self):
        all_attrs = set(self._aliases.keys() +
                        self._init_attrs +
                        self.__dict__.keys() + dir(EvtKeys))
        return list(sorted(all_attrs))


class TypTab(object):
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





