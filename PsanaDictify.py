# import standard python system tools
#import argparse
#from glob import glob
import re
import operator
#import sys
#import os
#import imp
#import subprocess
#import inspect
import pprint
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

        self._det_dicts = {}
        self._build_keys_dict()

    def _get_det_dict(self, det):
        """Get attribute.
        """
        if det not in self._det_dicts and det in self._keys_dict:
            self._det_dicts[det] = DetDictify(self._keys_dict, det)
        
        if det in self._det_dicts:
            return self._det_dicts[det]
        else:
            return None

    def __getattr__(self, attr):
        if attr in self._alias_dict:
            attr = self._alias_dict[attr]
        if attr in self._keys_dict:
            return self._get_det_dict(attr)

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
#        alias_dict = {}
        for evt_key in self.keys():
            if hasattr(evt_key,'type') and evt_key.type():
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

                if evt_key.key():
                    key_dict['data_key'] = evt_key.key()

                psana_module = evt_key.type().__module__
                module = psana_module.lstrip('psana.')
                psana_class = evt_key.type().__name__
                if key_dict.get('data_key'):
                    device = key_dict.get('data_key')+psana_class.lstrip('ndarray')
                
                elif module:
                    if module == 'Bld':
                        device = psana_class.strip('BldData')

                    elif module == 'Lusi':
                        device = psana_class.strip('Fex')
                    else:
                        device = module

                else:
                    device = psana_class
                    if not det_key:
                        det_key = psana_class

                    if not det_key:
                        det_key = '_'.join([module,psana_class])

        # Bld data do not yet have aliases -- ask daq group to add consistent ones.
                if module == 'Bld':
                    if not alias:
                        if det_key[-2] in '_':
                            alias = det_key[:-2]
                        else:
                            alias = det_key

                if det_key:
                    det_key = det_key.replace('-','_')
 
        ## strip of Version Number           
                if re.search(r"V.?\b", device):
                     device = device[:-2]

                if psana_class == 'EventId':
                    alias = psana_class
                    key_dict.update({'TypeId': 0,
                                     'Version': 0})
                else:
                    if key_dict.get('data_key'):
                        key_dict.update({'TypeId': 9999,
                                         'Version': 0})
                    else:
                        key_dict.update({'TypeId': evt_key.type().TypeId,
                                         'Version': evt_key.type().Version})

                key_dict.update({'psana_module': psana_module,
                                 'psana_class': psana_class,
                                 'device': device})
                type_key = '_'.join([key_dict['device'],
                                     str(key_dict['TypeId']),
                                     str(key_dict['Version'])])
                
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
                if key_dict.get('data_key'):
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

#                key_dict['attrs'] = {attr: getattr(evt_funcs, attr) for attr
#                                     in dir(evt_key.type())
#                                     if not attr.startswith(('_','TypeId','Version'))}:

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
    def __init__(self, keys_dict, det, show_attrs=True):
        self._det = det
        self._keys = keys_dict[det]
        if show_attrs:
#            self._attr_type = {attr: typ for typ, item in self._keys.items() 
#                                for attr in item['attrs'].keys()}
            self._attr_type = self._keys['det']['attr_type']
        else:
            self._attr_type = {}
        self._attrs = self._attr_type.keys()

        self._types = {typ: TypeDictify(keys_dict, det, typ) \
                       for typ in keys_dict[det]['det']['type_list']}

    def get_det_type(self, type):
        return self._types.get(type)
#        return self._attr_type[attr]

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
    
    def __init__(self, keys_dict, det, typ):
        self._det = det
        self._typ = typ
        self._attrs = keys_dict[det][typ]['attrs'] 
        self._show_attrs = self._attrs.keys()

    def get_attr(self, attr):
        if attr in self._attrs:
            value = self._attrs[attr]        
            if type(value).__module__ != np.__name__:
                try:
                    value = value()
                except:
                    pass
                if hasattr(value,'__func__'):
                    try:
                        value = value()
                    except:
                        pass
        else:
            value = None
            
        if isinstance(value, list):
            try:
                value = [val() for val in value]
            except:
                if len(value) < 100:
                    for i, val in enumerate(value):
                        try:
                            val = val()
                        except:
                            pass
                        setattr(self, '{:}{:02}'.format(attr,i), ReDictify(val))

        return value

    def show_info(self, attrs=None, **kwargs):
        print '-'*80
        print self._det, self._typ
        print '-'*80
        if not attrs:
            attrs = list(sorted(self._show_attrs))
        for attr in attrs:
            item = self._attrs[attr]
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

    def __init__(self, obj):
        self._attrs = [attr for attr in dir(obj) if not attr.startswith('_')]
        for attr in self._attrs:
            value = getattr(obj, attr)
            try:
                value = value()
            except:
                pass

            setattr(self, attr, value)

    def show_info(self, attrs=None):
        if not attrs:
            attrs = list(sorted(self._attrs))
        for attr in attrs:
            value = getattr(self,attr)
            print func_repr(attr, value)

    def __repr__(self):
        repr_str = '< {:}>'.format(self.__class__.__name__) 
        self.show_info()
        return repr_str


def get_unit_from_doc(doc):
    try:
        unit = '{:}'.format(doc.rsplit(' in ')[-1])
        unit = unit.rstrip('.').rstrip(',').rsplit(' ')[0].rstrip('.').rstrip(',')
        if unit in 'Value':
            unit = '{:}'.format(doc.rsplit('converted to ')[-1].rstrip('.'))
        
        if unit.endswith('(') or unit in ['long', 'all', 'setup', 'given']:
            unit = ''
    
    except:
        unit = ''
    return unit

def func_dict(attr, func):
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
            except:
                try:
                    fdict['str'] = value.__str__()
                except:
                    pass

    fdict['value'] = value

    return fdict

def func_repr(attr, func):
    fdict = func_dict(attr, func)

    return '{attr:18s} {str:>10} {unit:6} {doc:}'.format(**fdict)


class EpicsDictify(object):

    def __init__(self, epicsStore):
        """Show epics PVs with tabs.
        """

        pv_dict = {}
        for pv in  epicsStore.names():
            name = re.sub(':|\.','_',pv)
            #check if valid -- some old data had aliases generated from comments in epicsArch files.
            if re.match("[_A-Za-z][_a-zA-Z0-9]*$", name):
                func = epicsStore.getPV(pv)
                pvname = epicsStore.pvName(pv)
                if pvname:
                    pvalias = pv
                else:
                    pvalias = epicsStore.alias(pv)
                    pvname = pv

                components = re.split(':|\.|_',pv)
                for i,item in enumerate(components):
                    if item[0].isdigit():
                         components[i] = 'n'+components[i]

                pv_dict[name] =  { 'pv': pvname,
                                   'alias': pvalias,
                                   'components': components,
                                   'func': func}

        self._pv_dict = pv_dict
        self.epics = PVdictify(pv_dict)


class PVdictify(object):
    """Dot.dictifies a dictionary of {PVnames: values}.
    """

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





#class PVdictify(object):
#    """Dot.dictifies a dictionary of {PVnames: values}.
#    """
##    _levels = ['location','region','component','number','field']
#
#    def __init__(self,attr_dict,level=0):
#        self._attr_dict = attr_dict
#        self._level = int(level)
#        self._attrs = list(set([pdict['components'][level]
#                                for key,pdict in attr_dict.items()]))
#
#    def show_info(self):
#        """Show information from PVdictionary for all PV's starting with 
#           the specified dictified base.
#           (i.e. ':' replaced by '.' to make them tab accessible in python)
#        """
#        print self.get_info()
#
#    def get_info(self):
#        """Return string representation of all PV's starting with 
#           the specified dictified base.
#           (i.e. ':' replaced by '.' to make them tab accessible in python)
#        """
#        info = ''
##        for key,pdict in self._attr_dict.items():
#        items = sorted(self._attr_dict.items(), key=operator.itemgetter(0))
#        for key,pdict in items:
#            alias = pdict['alias']
#            if alias:
#                name = alias
#                pv = pdict['pv']
#            else:
#                name = pdict['pv']
#                pv = ''
#
#            value = pdict['func'].value(0)
#            try:
#                info += '{:30s} {:10.4g} -- {:30s}\n'.format(name,value,pv)
#            except:
#                info += '{:30s} {:>10} -- {:30s}\n'.format(name,value,pv)
#        return info
#


