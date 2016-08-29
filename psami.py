# import standard python system tools
import argparse
import re
import os
import imp
import socket
import struct
import time

#from glob import glob
#import operator
#import sys
#import subprocess
#import inspect
#import pprint
#import math

# epics device interface
#import lcls_devices

# import standard python scientific data analysis packages from ana-release
#from pylab import *
import numpy as np

# import PCDS specific python packages from ana-release
import pyami
#import pydaq

#daq_config = {'host':      'cxi-daq', 
#              'platform':  4,
#              'proxy':     'daq-cxi-mon03'}

#class Daq(object):
#
#    def __init__(self, 
#                 daq_host=None, 
#                 platform=4, 
#                 **kwargs):
#        """Initialize Daq connection.
#        """
#        self.daq_host = daq_host
#        self.platform = platform
#        self.control = pydaq.Control(self.daq_host,self.platform)

class Ami(object):

#    _epics_devices = {}
#    _epics_live = False
    _ami_detectors = {}
#    _device_sets = {}
    _defaults = {'xvariable': 'ProcTime',
                 'nbins':     100}

    def __init__(self, 
                 proxy_host=None, 
#                 proxy_host='daq-cxi-mon02', 
#                 daq_host=None, 
#                 platform=4, 
                 instrument=None,
                 **kwargs):
        """Initialize AMI connection.
        """
#        for attr,val in daq_config.items():
#            setattr(self, attr, val)
#        self.connect(proxy_host)
#
#    def connect(self,proxy_host):
        if proxy_host:
            self.proxy_host = proxy_host
        elif instrument:
            self.proxy_host = 'daq-'+instrument+'-mon01'
        else:
            raise NameError('Cannot load psami.')
            print 'Neither proxy_host or instrument are specified' 

        if not instrument:
            try:
                instrument = self.proxy_host.split('-')[1]
            except:
                instrument = None

        self.instrument = instrument
#        self.load_epics_dict()

#        for attr,item in self._epics_dict.items():
#            pv = item['base']
 
        self._pname = socket.gethostbyname(self.proxy_host)
        self._paddr = struct.unpack('>I',socket.inet_aton(self._pname))[0]
        self._pyami = pyami
#        self._pyami.connect(self._paddr)
        self._pyami.connect(self._pname)

        if hasattr(self._pyami,'list_env'):
            self._env = AmiEnv(self, self._env_dict)
            self._env_attrs = list(set([val['components'][0] for key,val 
                                        in self._env_dict.items()]))

#    def load_epics_dict(self, instrument=None,epics_dir=None,epics_file=None):
#        """Load dictionary of epics pvs into _epics_dict based on
#           an epicsArch.txt file used by the daq to archive epics
#           data in the xtc data files.
#        """
#        if not epics_file:
#            epics_file = 'epicsArch.txt'
#        
#        if not epics_dir:
#            epics_dir = '/reg/g/pcds/dist/pds/'+instrument+'/misc/'
#        
#        self._epics_dict = lcls_devices.epicsArch_dict(epics_file,epics_dir)
#
#    def add_live_pv(self, pv):
#        """Add live epics PV as pyepics device class.
#           _epics_devices is a dictionary of pyepics PV Devices
#           that will can be called from the pv alias in the 
#           psami.AmiDetector class. 
#        """
#        if pv not in self._epics_devices:
#            self._epics_devices[pv] = lcls_devices.get_live_pv(self, pv)        

    @property
    def _ami_dict(self):
        """Dictionary of AMI data from pyami.discovery().
        """
#        ami_dict = {}
#        for det in self._pyami.discovery():
#            alias = d['name'].replace('-','_')
#
        return {d['name'].replace('-','_'): d for d in self._pyami.discovery()}

    @property
    def _ami_dets(self):
        """List of detectors available from AMI.
        """
        return self._ami_dict.keys()

    @property 
    def _env_dict(self):
        env_dict = {}
        for env_item in self._pyami.list_env():
            item = env_item['name'].replace('-','_').replace(' ','_')
            item = item.replace('[','_').replace(']','')
            components = re.split(':|\.|-',item)
            for i,val in enumerate(components):
                if val[0].isdigit():
                     components[i] = 'n'+components[i]
 
            env_dict[item] =  {'name':item,  
                               'alias': re.sub(':|\.','_',item),
                               'components':components} 

        return env_dict 

    def Scan(self,name,xvariable=None,nbins=None):
        """Monitors data from the scalar variable 'name'.  A dictionary of
        (type='Scan', time=<last event time in seconds since the Epoch>,
            nbins=<value>, current=<index of most recent entry>, 
            xbins=( x0, x1, ...), yentries=( n0, n1, ...),
            ysum=( y0, y1, ...), y2sum=( y2_0, y2_1, ...)) is accumulated; where
        'current' is the bin with the most recent entry, 
        'xbins' is a list of unique x-variable values,
        'yentries' is a list of the number of summed entries with that x-variable value,
        'sum' is a list of the sum of y-variables values in each bin, 
        'y2sum' is a list of the sum of y-variable values squared in each bin.  
        The lists are of length 'nbins' with only the most recent entries retained.
        """
        if not xvariable:
            xvariable = self.get_default('xvariable')
        if not nbins:
            nbins = self.get_default('nbins')
        try:
            return ami._pyami.Entry(name, 'Scan', xvariable, nbins)
        except:
            print 'Cannot setup AMI scan for ', name

    def add_detector(self, attr):
        """Add an AMI Detector.
        """
        self._ami_detectors[attr] = AmiDetector(self, attr)
        
    def get_default(self, attr):
        """Get a default value.
        """
        if attr in self._defaults:
            return self._defaults[attr]
        else:
            return None

    def set_default(self, attr, val):
        """Set a default value.
        """
        self._defaults[attr] = val

#    def show_defaults(self, *args, **kwargs):
#        """Show default settings.
#        """
#        if len(args) = 1:
#            if type(args[0]) is list:
#                attrs = args[0]
#            else:
#                attrs = args
#        elif len(args) > 1:
#            attrs = args
#        else:
#            attrs = self._defaults.keys()
#
#        for attr in attrs:
#            print 
#
    def get_detector(self, attr):
        if attr not in self._ami_detectors:
            self.add_detector(attr)
        return self._ami_detectors[attr]

    def __getattr__(self, attr):
        if attr in self._ami_dict:
            return self.get_detector(attr)
        if attr in self._env_attrs:
            return getattr(self._env, attr)

    def __dir__(self):
        all_attrs = set(self._ami_dets +
                        self._env_attrs + 
                        self.__dict__.keys() + dir(Ami))
        return list(sorted(all_attrs))


class AmiDetector(object):

    _ami_attrs = []
#    _user_funcs = {} 
    _init = None

    def __init__(self, ami, name):
        """Initialize an AMI detector.
        """
        self._pyami = ami._pyami
        if name in ami._ami_dict:
            det_dict = ami._ami_dict[name]
            det_type = det_dict['type']
            det_id = det_dict['det_id']
            if det_id == 0L:
                det_id = det_dict['name']
        elif name in ami._env_dict:
            det_dict = None
            det_id = name 
            det_type = 'Scalar'
        if det_type in 'Image':
            self._entry = ami._pyami.Entry(det_id, 0)
        elif det_type in 'Scalar':
            self._entry = ami._pyami.Entry(det_id)
        elif det_type in 'Waveform':
            try:
                channel = int(name.split('_')[-1]-1)
            except:
                channel = 0
            self._entry = ami._pyami.Entry(det_id, channel)
        else:
            self._init = False

        if self._init is not False:
            self._init = True
            if det_dict:
                for attr,val in det_dict.items():
                    setattr(self, attr, val)
            self.ami_connect()
        
    def ami_connect(self,max_attempts=5,iattempt=0):
        """Recursively try to connect to the ami detector up to max_attempts times.
        """
        try:
            self.ami_clear()
            self.ami_get()
            self._ami_connected = True
            print 'Connected on attempt #',iattempt+1
        except:
            print 'No AMI connect for ',self._name
            self._ami_connected = False 
            if iattempt < max_attempts:
                self.ami_connect(iattempt=iattempt+1)

    def ami_clear(self):
        """Resets the data accumulation.
        """
        self._time0 = time.time()
        self._entry.clear()

    def ami_get(self):
        """Get next events since connected or last clear.
        """
        self._event = self._entry.get()
        self._ami_attrs = self._event.keys()
        return self._event

#    def load_functions(self, module_name, path=None):
#        """Load functions from file that operate on the detector class attributes. 
#           These functions will be held in self._user_funcs and printed out in self.show_info()
#        """
#        if True:
##        try:
#            if not path:
#                path = os.getcwd()
#            if not isinstance(path,list):
#                path = [path]
#            file,filename,desc = imp.find_module(module_name,path)
#            funcs = imp.load_module(module_name, file, filename, desc)
#            if hasattr(funcs,'_init'):
#                getattr(funcs,'_init')(self)
#            attrs = [attr for attr in funcs.__dict__
#                     if not attr.startswith('__')
#                     and attr is not '_init'
#                     and not hasattr(getattr(funcs,attr),'__base__')]
#            for attr in attrs:
#                if True:
##                try:
#                    print 'Adding', attr, 'to', self._name
#                    self.add_function(getattr(funcs,attr))
##                except:
##                    print 'Error adding', attr, 'to', self._name

#        except:
#            print 'ERROR loading ',module_name, ' from ', path, ' for ',self._name

#    def add_function(self, func_name, *args, **kwargs):
#        """Add a function that operates on this detector object.
#                add_function(func_name [, attr])
#           The result will be added as an attribute to the detecor with the
#           name of the function unless attr is provided.
#           For example:
#            > def myfunc(self):       
#                  return self.ebeamL3Energy
#            > data.ebeam.add_function(myfunc, 'energy')
#
#           Or alternatively using lambda:
#            > data.ebeam.add_function(lambda self: self.ebeamL3Energy, 'energy')
#        """
#        if len(args) > 0:
#            attr = args[0]
#        else:
#            attr = func_name.func_name
#        self._user_funcs[attr] = func_name

#    def get_function(self,attr):
#        """Return a user defined function from self._user_funcs.
#        """
#        func_name = self._user_funcs[attr]
#        if hasattr(func_name,'__call__'):
#            func_name = func_name(self)
#        return func_name
#
#    def del_functions(self, *args):
#        if len(args) > 0:
#            attrs = args
#        else:
#            self._user_function.clear()

    def get_ami_attr(self, attr):
        """Get ami attribute.
        """
        if attr in self._ami_attrs:
            if not self._ami_connected:
                self.ami_connect()
            try:
                self._event = self._entry.get()
                val = self._event[attr]
                try:
                    if isinstance(val, list):
                        val = np.array(val)
                except:
                    pass
                
                return val
            except:
                return None

    def __getattr__(self, attr):
        if attr in self._ami_attrs:
            return self.get_ami_attr(attr)
#        if attr in self._user_funcs:
#            return self.get_function(attr)

    def get_ami_info(self):
        """String of basic inforamtion for AMI Detector.
        """
        if not self._ami_connected:
            self.ami_connect()
#        try:
        if True:
            event = self.ami_get()
            delta_time = max([event['time']-self._time0,0])
            if delta_time > 0:
                event_rate = event['entries']/delta_time
            else:
                event_rate = float('NaN')
            if event['type'] in 'Scalar':
                info_str = '{:s} = {:.1f}+-{:.1f}, {:} entries in {:.2f} sec ({:.0f} Hz): {:s}'.format(
                            event['type'], event['mean'], event['rms'], event['entries'], 
                            delta_time, event_rate, time.ctime(event['time']))
            elif event['type'] in 'Image':
                info_str = '{:s} {:}x{:}, {:} entries in {:.2f} sec ({:.0f} Hz): {:s}'.format(
                            event['type'], self.nbinsx, self.nbinsy, event['entries'], 
                            delta_time, event_rate, time.ctime(event['time']))
            elif event['type'] in 'Waveform':
                info_str = '{:s}, {:} entries in {:.2f} sec ({:.0f} Hz): {:s}'.format(
                            event['type'], event['entries'], 
                            delta_time, event_rate, time.ctime(event['time']))
            else:
                info_str = '{:}, entries in {:.2f} sec ({:.0f} Hz): {:s}'.format(
                            event['type'], event['entries'], 
                            delta_time, event_rate, time.ctime(event['time']))
#        except:
#            print 'Error Getting AMI Information'

        return info_str

    def __repr__(self):
        try:
            repr_str = '<AMI Detector '+self.get_ami_info()+'>'
        except:
            repr_str = '<AMI Detector -- Unknown Type in get_ami_info() method>'
        
        return repr_str

    def __dir__(self):
        all_ami_attrs = set(self._ami_attrs +
#                        self._user_funcs.keys() +
                        self.__dict__.keys() + dir(AmiDetector))
        return list(sorted(all_ami_attrs))


class AmiEnv(object):
    """Dot.dictifies Ami Env.
    """

    def __init__(self,ami,attr_dict,level=0):
        self._pyami = ami
        self._attr_dict = attr_dict
        self._level = int(level)
        self._baselist = list(set(['.'.join(pdict['components'][0:self._level]) 
                                   for key,pdict in self._attr_dict.items()]))
        self._attrs = list(set([pdict['components'][level]
                                for key,pdict in attr_dict.items()]))

    def __getattr__(self,attr):
        if attr in self._attrs:
            attr_dict = {key: pdict for key,pdict in self._attr_dict.items()
                         if pdict['components'][self._level] in attr}
            if len(attr_dict) == 1:
                key = attr_dict.keys()[0]
                if len(self._attr_dict[key]['components']) == (self._level+1):
                    return self._pyami.get_detector(key)
            if len(attr_dict) > 0:
                return AmiEnv(self._pyami,attr_dict,level=self._level+1)

    def get_info(self):
        info = ''
        for attr in list(sorted(self._attr_dict.keys())):
            try:
                info += '{:20} {:}\n'.format(attr,self._pyami.get_detector(attr).get_info())
            except:
                pass

        return info

    def show_info(self):
        print self.get_info()

    def __repr__(self):
        print '-'*72
        self.show_info()
        return '< Ami Env Variables starting with {:} >'.format(' '.join(self._baselist))

    def __dir__(self):
        all_attrs = set(self._attrs +
                        self.__dict__.keys() + dir(AmiEnv))
        return list(sorted(all_attrs))   

def initArgs():
    parser = argparse.ArgumentParser()
#    parser.add_argument("-e", "--exp", type=str, help='Experiment number')
#    parser.add_argument("-r", "--run", type=int, default=0, help='Run number')
#    parser.add_argument("-i", "--instrument", type=str, help='Instrument')
#    parser.add_argument("-s", "--station", type=int, help='Station')
#    parser.add_argument("-l", "--live", action="store_true", help='Use live data stream')
    parser.add_argument("-p", "--proxy_host", type=str, default='daq-cxi-mon01', help='AMI proxy host')
    parser.add_argument("-z", "--epics_live", action="store_true", help='Use live epics')
#    parser.add_argument("--noload", action="store_true", help='Do not load psana data')
#    parser.add_argument("-n", "--nevents", type=int, help='Number of Events')
#    parser.add_argument("-d", "--det_list", type=str, help='List of detectors if nevents set')
    return parser.parse_args()

if __name__ == "__main__":
    args = initArgs()
    print "*"*80
    print 'Loading psami with the following arguments:'
    for attr,val in vars(args).items():
        print "   {:} = {:}".format(attr, val)
    print "*"*80
    try:
        print "*"*80
        ami = Ami(**vars(args))
#        run_info = "psami loaded from {:} ".format(ami.proxy_host)
##        if ami.live:
##            run_info += ' -- Live Data from Shared Memory'
#        print run_info
        print "*"*80
    except:
        print "*"*80
        print "*"*80
        print 'ERROR loading psami'
        print "*"*80
        print "*"*80
#    if args.nevents:
#        data.get_events(args.nevents,det_list=args.det_list)




