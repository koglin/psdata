import re
import time
import traceback
import sys

import epics
import psutils
import psmessage
import elog
import psioc
import psdevice

import numpy as np

def get_rtyp(base, connection_timeout=0.5):
    epicsPV = epics.PV(base+'.RTYP',connection_timeout=connection_timeout)
    if epicsPV.connected:
        rtyp = epicsPV.get()
    else:
        rtyp = None

    return rtyp
             
def epicsArch_dict(archfile_name,file_dir):
    arch_dict = {}
    file_list = [archfile_name]
    #try:
    if True:
        with open(file_dir+'/'+archfile_name,'r') as f:
            for line in f:
                if line.startswith('<'):
                    file_list.append(line.strip('<').strip().strip('\n').strip())

        arch_list = []
        for file in file_list:
            with open(file_dir+'/'+file,'r') as f:
                arch_list.append(f.read().split('\n'))
                    
        arch_list = [item.strip(' ') for sublist in arch_list for item in sublist]

        pvalias = None
        for item in arch_list:
            if item.startswith(('#','<')):
                pvalias = None
            elif item.startswith('*'):
                pvalias = item.strip('*').strip(' ')
            elif len(item) > 1:
                pvname = item.strip(' ')
                pvbase = pvname.split('.')[0]
                if pvalias:
                    if pvalias in arch_dict:
                        print 'Warning: duplicate alias {:}'.format(pvalias)
                else:
                    pvalias = re.sub(':|\.','_',pvname) 

                components = re.split(':|\.',pvname)
                for i,item in enumerate(components):
                    if item[0].isdigit():
                         components[i] = 'n'+components[i]
     
                arch_dict[pvname] = {'name': pvname,
                                     'alias': pvalias,
                                     'base':  pvbase,
                                     'components': components} 

    else:
    #except:
        print 'Error loading {:} from {:}'.format(archfile_name,file_dir)

    return arch_dict

def camviewer_dict(file_name,file_dir):
    cam_dict = {}
    cam_list = []
    with open(file_dir+'/'+file_name,'r') as f:
        for line in f:
            if not line.startswith('#') and not line.strip(' ').startswith('\n'):
                cam_list.append(line)

    for cam in cam_list:
        try:
            info = cam.rsplit(',')
            key = info[1].lstrip()
            cam_dict.update({key: 
                            { 'base': info[1].lstrip(), 
                              'evr': info[2].lstrip(), 
                              'alias': info[3].replace('\n','').lstrip(), 
                              'type': info[0].lstrip()}
                            })
            if len(info) > 4:
                cam_dict[key].update({'other': info[4].replace('\n','').lstrip()})
        except:
            print 'Cannot load', cam

    return cam_dict

def camrecord_dict(file_name, file_dir):
    cam_dict = {}
    fp=open(file_dir+'/'+file_name)
    lns=fp.readlines()
    fp.close()
    host = "*"
    for ln in lns:
        ln = ln.strip()
        if ln == "" or ln.startswith("#"):
            continue
        sln=ln.split()
        kind = sln[0].strip()
        if (kind == "experiment"):
            experiment = sln[1].strip()
        elif (kind == "defhost"):
            x = sln[1].strip().split(":")
            defhost = x[0]
            if len(x) > 1:
                defport = x[1]
        elif (kind == "defport"):
            defport = int(sln[1].strip())
        elif (kind == "host"):
            host = sln[1].strip()
            if not ((":" in host) or (host == "*")):
                host = host + ":" + str(defport)
        elif (kind == "camera-per-row"):
            try:
                cpr = int(sln[1].strip())
            except:
                pass
            if (cpr <= 0):
                cpr = 1
        elif (kind == "bld-per-row"):
            try:
                bpr = int(sln[1].strip())
            except:
                pass
            if (bpr <= 0):
                bpr = 1
        elif (kind == "pv-per-row"):
            try:
                ppr = int(sln[1].strip())
            except:
                pass
            if (ppr <= 0):
                ppr = 1
#        elif (kind == "group"):
#            self.uia.add_group(sln[1].strip(), sln[2].strip())
#        elif (kind == "endgroup"):
#            self.uia.end_group()
        elif (kind == "camera"):
            key = sln[4].lstrip()
            cam_dict.update({key: 
                        { 'base':  sln[4].lstrip(),
                          'host':  host, 
                          'alias': sln[1].lstrip(), 
                          'desc':  sln[2].lstrip(),
                          'type':  sln[3].lstrip()}
                        })
            if len(sln) > 5: 
                cam_dict[key].update({'rtyp':  sln[5].lstrip()})
#        elif (kind == "bld"):
#            self.uia.add_bld(sln[1].strip(), host, ln)
#        elif (kind == "pv"):
#            self.uia.add_pv(sln[1].strip(), host, ln)
    return cam_dict

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


class Device(epics.Device):
    """LCLS implementation of pyepics epics.Device.
    """
    
    _mutable = False
    _records = {}
    _expand_records = False
    _nonpvs = ('_prefix', '_pvs', '_delim', '_init', 
               '_expand_records', 
               '_alias', '_fields', '_records', '_info_attrs' )

    def __init__(self, name,
              records={},
              mutable=False, timeout=1.0, **kwargs):

        self._prefix = name
        epics.Device.__init__(self, name,
                     mutable=mutable,
                     timeout=timeout, **kwargs)

        if not records:
            records = psioc.get_record_dict(self._prefix)

        base = records.pop('',{})
        self._records = records

    @property
    def ioc(self):
        if self._fields:
            pvbase = self._prefix
        else:
            pvbase = self._records.values()[0]

        if pvbase:
            return psioc.get_ioc(pvbase)

    def get_device(self, attr):
        """Get an epics device either directly from pvbase
           or with an alias defined in self._records
        """
        attr = self._records.get(attr, attr)
        return psdevice.get_device(attr)

    def add_device(self, **kwargs):
        """Add device records by keyward assignment.
           e.g., to load and asign the ims motor pv='CXI:SC1:MMS:02' to the attribute self.x 
                self.add_record(x='CXI:SC1:MMS:02')
           
           To add a dictionary of {alias: pv},
                epics_devices = {
                        'x': 'CXI:PI1:MMS:01',
                        'y': 'CXI:PI1:MMS:02', 
                        'z': 'CXI:PI1:MMS:03', 
                        }
                self.add_device(**epics_devices)
        """
        self._records.update(**kwargs)

    def show_records(self, attrs=None, expand=False, prefix=None):
        """Show all additional records associated with the IMS motor.
        """
        if not attrs:
            attrs = self._records.keys()
            attrs.sort()
        else:
            attrs = [attr for attr in attrs if attr in self._records]

        for attr in attrs:
            if prefix:
                alias = '.'.join([prefix, attr])
            else:
                alias = attr
            
            pvbase = self._records.get(attr)
            rec = self.get_device(pvbase)
            if get_rtyp(pvbase):
                if hasattr(rec, 'RBV'):
                    value = rec.get('RBV', as_string=True)
                else:
                    value = rec.get('VAL', as_string=True)
                desc = rec.DESC
                if hasattr(rec, 'EGU'):
                    units = rec.EGU
                else:
                    units = ''
               
                print '{:30s} {:>12} {:6} {:30}'.format(alias, value, units, desc)

            if expand:
                rec.show_records(expand=expand, prefix=alias)

    def show_info(self, **kwargs):
        self.show_records(**kwargs)

    def __getattr__(self, attr):
        if attr in self._records:
            return self.get_device(self._records[attr])

    def __dir__(self):
        all_attrs = set(self._records.keys() +
                        self.__dict__.keys() + dir(Device))
        return list(sorted(all_attrs))


class EpicsSets(object):
    """Set of epics devices.
    """
    _sets = {}
    _aliases = {}

    def __init__(self, instrument=None, station=None, pvs=None, 
            no_auto_load=False, **kwargs):

        self.instrument = instrument
        self.station = station
        if pvs:
            self.add_device(**pvs)
        elif not no_auto_load and not self._sets:
            self.load_epicsArch(**kwargs)
            self.load_epicsCameras(**kwargs)

    def load_epicsCameras(self, cfg_file='camviewer.cfg', cfg_dir=None, **kwargs):
        """Load epics camera viewer config file to define aliases.
        """
        if not cfg_dir and self.instrument:
            cfg_dir = '/reg/g/pcds/pyps/config/'+self.instrument+'/'

        if cfg_dir:
            print 'instrument: {:}'.format(self.instrument)
            print 'loading epics pvs from', cfg_file, ' in', cfg_dir
            self._epics_camdict = camviewer_dict(cfg_file,cfg_dir)
            if self._epics_camdict:
                for pv,item in self._epics_camdict.items():
                    pvbase = item['base']
                    alias = item['alias']
                    evr = item.get('evr')
                    self.add_device(**{alias+'_IMAGE': pvbase})
                    if evr and evr.lower() is not 'none':
#                        self.add_alias(**{alias+'_EVR': evr})
                        self.add_device(**{alias+'_EVR': evr})

    def load_epicsArch(self, epics_dir=None, epics_file=None, **kwargs):
        """Load epicsArch file to define aliases.
        """
        if not epics_file:
            if self.station:
                epics_file = 'epicsArch_{:}.txt'.format(self.station)
            else:
                epics_file = 'epicsArch.txt'

        if not epics_dir and self.instrument:
            epics_dir = '/reg/g/pcds/dist/pds/'+self.instrument+'/misc/'

        if epics_dir:
            print 'instrument: {:}'.format(self.instrument)
            print 'loading epics pvs from', epics_file, ' in', epics_dir
            self._epics_dict = epicsArch_dict(epics_file,epics_dir)
            if self._epics_dict:
                for pv,item in self._epics_dict.items():
                    pvbase = item['base']
                    alias = item['alias']
#                    self.add_alias(**{alias: pvbase})
                    self.add_device(**{alias: pvbase})

    def add_device(self, noInit=True, **kwargs):
        """Add epics devices by keyward assignment.
           e.g., to make or update an EpicsDeviceSet and asign the 
           ims motor pv='CXI:SC1:MMS:02' it
 
                In:  self.add_device(sample_x='CXI:SC1:MMS:02')

           such that the complete motor record is loaded and can be viewed:
           
                In:  self.sample.x
                Out: #--------------------------------------------------------------------------------
                # CXI:SC1:MMS:02 -- SC1 Sample X                                      
                # Attr    Alias                  Value                  Description                   
                #--------------------------------------------------------------------------------
                DESC      description            SC1 Sample X           Description                   
                NAME      name                   CXI:SC1:MMS:02         PV Name                       
                VAL       drive                  -105.9861              User Desired Value            
                RBV       readback               -105.9785              User Readback Value           
                EGU       units                  mm                     Engineering Units             
                PREC      precision              4                      Display Precision             
                VELO      slew_speed             2.0000                 Velocity (EGU/s)              
                ACCL      acceleration           3.0000                 acceleration time             
                DIR       direction              Neg                    User Direction                
                STAT      status                 STATE                  Status                        
                TWV       tweak_val              50.0000                Tweak Step Size (EGU)         
                LLM       low_limit              -150.0000              User Low Limit                
                HLM       high_limit             -50.0000               User High Limit               
                EE        encoder_enabled        Enable                 Encoder                       
                RC        run_current            8                      Run Current                   
                HC        hold_current           0                      Hold Current                  
                RTYP      record_type            ims                    Record Type                   
                <IMS Motor: CXI:SC1:MMS:02 = -105.99 mm : SC1 Sample X>

           To add a dictionary of {alias: pv},
                In:  epics_devices = {
                        'sample_x': 'CXI:PI1:MMS:01',
                        'sample_y': 'CXI:PI1:MMS:02', 
                        'sample_z': 'CXI:PI1:MMS:03', 
                        }
                In:  self.add_device(**epics_devices)

           A summary of the epics information is given by: 

                In:  self.sample.show_info()
                x                         -0.8289 mm     CXI:PI1:MMS:01.RBV - PI X
                y                         30.7872 mm     CXI:PI1:MMS:02.RBV - PI Y
                z                               0 mm     CXI:PI1:MMS:03.RBV - PI Z

        """
        for alias, pvbase in kwargs.items():
            avals = alias.split('_',1)
            devices = psioc.get_record_dict(pvbase)
            if len(avals) == 2:
                det, attr = avals
                alias_dict = {attr: pvbase}
            elif len(devices) > 0:
                det = alias
                attr = alias
                alias_dict = devices
            else:
                det = alias
                attr = alias
                alias_dict = {alias: pvbase}

            print "adding", alias, det, attr,pvbase
            if det in self._sets:
                self._sets[det].add_device(noInit=noInit, **alias_dict)
            else:
                self._sets[det] = EpicsDeviceSet(det, alias_dict, noInit=True)

    def add_alias(self, **kwargs): 
        for alias, pvbase in kwargs.items():
            avals = alias.split('_',1)
            devices = psioc.get_record_dict(pvbase)
            if len(avals) == 2:
                det, attr = avals
                alias_dict = {attr: pvbase}
            elif len(devices) > 0:
                det = alias
                attr = alias
                alias_dict = devices
            else:
                det = alias
                attr = alias
                alias_dict = {alias: pvbase}

            print "adding", alias, det, attr,pvbase
            if det not in self._sets:
                self._aliases[det] = {}
            
            self._aliases[det].update(alias_dict)

    def __getattr__(self, attr):
        if attr not in self._sets: 
            self._sets[attr] = EpicsDeviceSet(attr, {}, noInit=True)
        
        return self._sets[attr]

    def __dir__(self):
        all_attrs = set(self._sets.keys() +
                        self.__dict__.keys() + dir(EpicsSets))
        return list(sorted(all_attrs))


class EpicsDeviceSet(object):
    """Set of epics devices.
    """
    _devices = {}
    _put_all_attrs = ['STOP', 'ESTP', 'HLM', 'LLM', 'DISP', 'SBAS', 
                      'VBAS', 'VELO', 'S', 'A', 'HCTG', 'EGU', 'MT', 'CMD']
    
    def __init__(self, name, alias_dict, noInit=True, **kwargs):
        self._name = name
        self._aliases = alias_dict
        if alias_dict:
            self.add_device(noInit=noInit, **alias_dict)

    @property
    def _attrs(self):
        return self._aliases.keys()

    def add_device(self, device_base=None, noInit=False, **kwargs):
        """Add epics devices to an existing DeviceSet by keyward assignment.
           e.g., to load and asign the ims motor pv='CXI:SC1:MMS:02' to the attribute self.x 
                self.add_device(x='CXI:SC1:MMS:02')
           
           To add a dictionary of {alias: pv},
                epics_devices = {
                        'x': 'CXI:PI1:MMS:01',
                        'y': 'CXI:PI1:MMS:02', 
                        'z': 'CXI:PI1:MMS:03', 
                        }
                self.add_device(**epics_devices)

            Alternatively, add a device that consists of records by expanding
            automatically expanding the pvbase (from psioc.get_record_dict)
                epics_devices = psioc.get_record_dict('CXI:DG1:PIM') 
              
                loads the following dictionary into epics_devices
                    {
                     'CENH': 'CXI:DG1:PIM:CENH',
                     'CENV': 'CXI:DG1:PIM:CENV',
                     'NOPH': 'CXI:DG1:PIM:NOPH',
                     'NOPV': 'CXI:DG1:PIM:NOPV',
                     'PIXH': 'CXI:DG1:PIM:PIXH',
                     'PIXV': 'CXI:DG1:PIM:PIXV',
                     'YAG': 'CXI:DG1:PIM:YAG',
                     'ZOOM': 'CXI:DG1:PIM:ZOOM'
                     }

                self.add_device('CXI:DG1:PIM')

            is equivalent to loading epics_devices from psioc.get_recrod_dict above and,
                
                self.add_device(**epics_devices)

        """
 
        if device_base:
            kwargs.update(**get_record_dict(device_base))

        for alias, attr in kwargs.items():
            pvbase = attr.rsplit('.')[0]
            self._aliases[alias] = attr

            if not noInit:
                self._devices[pvbase] = psdevice.get_device(pvbase)
#                self._devices[pvbase] = get_live_pv(pvbase, **kwargs)

#    def new_device(self, alias, prefix, **kwargs):
#        """Add a new type of epics device that is completely specified
#           with either attrs or aliases keywords.
#        """
#        self._aliases[alias] = prefix
##        self._devices[prefix] = epics.Device(prefix, **kwargs)
#        self._devices[prefix] = get_live_pv(prefix, **kwargs)

    def del_device(self, attr):
        """Remove a pv from _devices and _aliases dictionaries.
        """
        if attr in self._aliases:
            self._aliases.pop(attr)
        else:
            print 'No attribute {:} in {:} to remove'.format(attr, self._name)
         

    def get_device(self, attr):
        """Get a live epics device (i.e., epics record) from _devices
           based either on the pv name or alias as defined in _aliases.
           Epics devices will be loaded on demand.
           Generally will be accessed through the Detector class
           where aliases are used to represent epics pvs.
        """
        if attr in self._aliases:
            pvbase = self._aliases[attr]
        elif attr in self._aliases.values():
            pvbase = attr
        else:
            return None

        return psdevice.get_device(pvbase)
#        if pvbase not in self._devices:
#            alias_dict = {attr: pvbase}
#            self.add_device(**alias_dict)
#
#        return self._devices.get(pvbase, None)

    def __str__(self):
        return '{:}: {:}'.format(self.__class__.__name__, self._name)

    def __repr__(self):
        print self.show_table()
        return '< {:} >'.format(str(self))

    def __getattr__(self, attr):
        if attr in self._aliases:
            return self.get_device(attr)

    def __dir__(self):
        all_attrs = set(self._aliases.keys() +
                        self.__dict__.keys() + dir(EpicsDeviceSet))
        return list(sorted(all_attrs))

    def get_alias(self, pv):
        """Get alias from pv.
        """
        if pv in self._aliases.values():
            return self._aliases.keys()[self._aliases.values().index(pv)]
        else:
            return None

#    def epics_table(self, show_all=False, *aliases, **kwargs):
    def epics_table(self, *args, **kwargs):
        """Show epics table.
           Optionally provide list of epics devices as input args.
           Keywords:
              show_all=True to show all the pv attributes
        """ 
        pv_dict = {}
        pv_alias = {}
        pv_types = {}
        plines = ''
        if args:
            if isinstance(args[0], list):
                aliases = args[0]
            else:
                aliases = args
            aliases = [a for a in aliases if a in self._aliases.keys()]
        else:
            aliases = self._aliases.keys()

        for alias in aliases:
            pv = self._aliases[alias]
            epics_device = self.get_device(alias)
            if epics_device:
#                rtyp = getattr(epics_device,'RTYP')
                rtyp = epics_device.RTYP
                if rtyp not in pv_types:
                    pv_types[rtyp] = []
                pv_types[rtyp].append(pv)

                if 'attrs' in kwargs:
                    attrs = kwargs['attrs']
                elif 'show_all' in kwargs:
                    if hasattr(epics_device, '_all_attrs'):
                        attrs = epics_device._all_attrs
                    else:
                        attrs = epics_device._alias.values()
                else:
                    attrs = epics_device._info_attrs

                if attrs:
                    pv_dict[pv] = {attr: epics_device.get(attr, as_string=True) \
                                   for attr in attrs}
                    pv_alias[pv] = alias

        for pvtype, pvs in pv_types.items():
            if pvtype:
                attrs = list(sorted(set(pv_dict[pvs[0]].keys())))
                first_attrs = ['NAME', 'DESC']
                for i, attr in enumerate(first_attrs):
                    if attr in attrs:
                        attrs.remove(attr)
                        attrs.insert(i, attr)

                pline = '{:10}'.format('Attrs')
                wmax = 1
                for pv in pvs:
                    for attr in attrs:
                        wmax = max(wmax, len(pv_dict[pv][attr]))

                column_format = '{:>'+str(min(max(12,140/len(pvs)),wmax+1))+'}'
                for pv in pvs:
                    pline += column_format.format(pv_alias[pv])

                plines += '-'*len(pline)+'\n'
                plines += pline+'\n'
                plines += '-'*len(pline)+'\n'
                for attr in attrs:
                    pline = '{:10}'.format(attr)
                    for pv in pvs:
                        pline += column_format.format(pv_dict[pv][attr])

                    plines += pline+'\n'

        return plines

#    def scan(self, title=None, **kwargs):
#        """Scan function
#        """
#        message = elog.message(title) 
#        xarray = list(x)
#        yarray = list(y)
#        nx = len(xarray)
#        ny = len(yarray)
#        scan_steps = max([nx,ny])
#
#        if not nx and not ny:
#            message.add('INPUT ERROR -- Must provide vector of scan positions for x and/or y motors.')
#            message.add(self.scan.__doc__)
#            return
#
#        elif nx != ny:
#            if nx <= 1:
#                message.add(' - Only scan Y-axis')
#                scan_dict = {'y': yarray}  
#            elif ny <= 1:
#                message.add(' - Only scan X-axis')
#                scan_dict = {'x': xarray}
#            else:
#                message.add('INPUT ERROR --  x and y vectors must be the same length or a single value')
#                return
#
#        else:
#            scan_dict = {'x': xarray, 'y': yarray}
#
#        message.add(' - Number of scan steps:      {:}'.format(scan_steps))
#        message.add(' - Number of x steps:         {:}'.format(nx))
#        message.add(' - Number of y steps:         {:}'.format(ny)) 
#        message.add(' - Number of shots per step:  {:}'.format(shots_per_step))
#
#        message.add('') 
#        message.add('{:>6} {:>10} {:>10} {:>10} {:>10} {:>10} {:>10}  {:10}'.format( \
#            'step', 'time', 'tstep', 'Xpos', 'Ypos', 'shots', 'Cspad', 'status'))
#        message.add('-'*80)
#
#        time0 = time_last = time.time()
#
#        try:
#            for istep in range(scan_steps):
#                pos_dict ={alias: val[istep] for alias,val in scan_dict.items()}
#                ok_move = self.epicsLive.move(wait=True, **pos_dict)
#                if not ok_move:
#                    message.add('Invalid Move Attepted -- exiting scan script')
#
#                xval = self.x.RBV
#                yval = self.y.RBV
#                self.sequencer.repeat(shots_per_step, wait=True)
#                ana_result = 0.
#                ana_status = 'OK'
#                time_current = time.time()
#                message.add('{:6} {:10.4} {:10.4} {:10.3} {:10.3} {:>10} {:10.5}  {:10}'.format( \
#                            istep, \
#                            time_current-time0, \
#                            time_current-time_last, \
#                            xval, \
#                            yval, \
#                            str(shots_per_step), \
#                            float(ana_result), \
#                            ana_status))
#                
#                time_last = time.time()
#            
#        except KeyboardInterrupt:
#            message.add('>'*80)
#            message.add('Scan Aborted')
#            pass
#
    def within_limits(self, quiet=False, **kwargs):
        """Check if motors are within limits.
        """
        ok_limits = True
        for alias, val in kwargs.items():
            mot = self.get_device(alias)
            if hasattr(mot, 'within_limits') and val is not None:
                ok_limit = mot.within_limits(np.array([val]).flatten().max())
                ok_limits &= ok_limit
                ok_limit = mot.within_limits(np.array([val]).flatten().min())
                ok_limits &= ok_limit
                if not ok_limit:
                    print '{:} Motor value = {:} is not within the soft limits'.format( \
                            alias, val)

        return ok_limits

    def set_limits(self, wait=True, **kwargs):
        """Set motor limits with dictionary of [LLM, HLM] values.
        """
        for alias, val in kwargs.items():
            mot = self.get_device(alias)
            if len(val) == 2:
                if hasattr(mot, 'LLM'):
                    mot.put('LLM', val[0], wait=wait)
                if hasattr(mot, 'HLM'):
                    mot.put('HLM', val[1], wait=wait)
 
    def move(self, wait=False, confirm_move=True, timeout=30., **kwargs):
        """Move devices as given by keyword aliases.
           First check that all motors are within limits
        """
        ok_limits = self.within_limits(**kwargs)
        if not ok_limits:
            print 'Warning:  Some motors are not within their limits'
            return 0

        for alias, val in kwargs.items():
            if np.isnan(val):
                print 'Warning:  No move made!'
                print 'Invalid number assigend {:} = {:}'.format(alias, val)
                return 0
        
        for alias, val in kwargs.items():
            if val is not None and alias in self._attrs:
                motor = self.get_device(alias)
                if hasattr(motor, 'move'):
                    motor.move(val, confirm_move=confirm_move)
                else:
                    motor.put('VAL', val, wait=True)
        
        if wait:
            status = self.all_done_moving(wait=True, timeout=timeout)
            return status
        else:
            return 1

    def all_done_moving(self, wait=False, timeout=30., **kwargs):
        """Return true if all devices are done moving.
           Set wait=True to wait until all devices are done moving.
            - timeout: max time for move to complete (in seconds) [100]
        """
        for alias in self._attrs:
            motor = self.get_device(alias)
            if hasattr(motor, 'done_moving'):
                if wait:
                    try:
                        time0 = time.time()
                        while not motor.done_moving and time.time()-time0 < timeout:
                            epics.poll(evt=1.e-5, iot=0.1)
                    except KeyboardInterrupt:
                        self.stop()
                        print 'Stopping all motors'
                        return 0
                else:
                    if not motor.done_moving:
                        return 0

        return 1

    def enable_hold_current(self):
        """Enable hold current for all motors.
        """
        self.put_conditional('HCTG', 1, RTYP='ims')

    def disable_hold_current(self):
        """Disable hold for all motors.
        """
        self.put_conditional('HCTG', 0, RTYP='ims')

    def clear_errors(self):
        """Clear erorrs for all motors.
        """
        for alias in self._attrs:
            motor = self.get_device(alias)
            if hasattr(motor, 'clear_errors'):
                motor.clear_errors()

    def set_tight_limits(self):
        """set tight limits for all motors.
        """
        for alias in self._attrs:
            motor = self.get_device(alias)
            try:
                pos = motor.get_position()
                motor.put('HLM', pos+0.001)
                motor.put('LLM', pos-0.001)
            except:
                print alias, 'is not a valid motor'

    def disable_all(self):
        """Disable all motors.
        """
        self.put_all('DISP', 1)

    def enable_all(self):
        """Enable all motors.
        """
        self.put_all('DISP', 0)

    def stop(self):
        """stop all motors.
        """
        for alias in self._attrs:
            motor = self.get_device(alias)
            if hasattr(motor, 'stop'):
                motor.stop()

    def StopNow(self):
        """Stop all motors.
        """
        for alias in self._attrs:
            motor = self.get_device(alias)
            if hasattr(motor, 'StopNow'):
                motor.StopNow()
    
    def put_conditional(self, attr, value, **kwargs):
        """Put value or dictionary of {alias: value} to specified attr.
           Example of setting the high limit to all motors:
                self.put_all('HLM', 0.)

           Optionally add kwargs conditions of pv attributes are true.
           For example only set ims motor types:
                self.put_all('HLM', 0, RTYP='ims')


           Note: attributes need to be included in _put_all_attrs list.
        """
        if attr in self._put_all_attrs:
            for alias in self._attrs:
                device = self.get_device(alias)
                ok_put = True
                for arg, val in kwargs.items():
                    if hasattr(device, arg):
                        pv_testval = device.get(arg)
                        if pv_testval and pv_testval != val:
                            ok_put = False

                if ok_put and hasattr(device, attr):
                    device.put(attr, value)

    def put_all(self, attr, *args, **kwargs):
        """Put value or dictionary of {alias: value} to specified attr.
           Example of setting the high limit to all motors:
                self.put_all('HLM', 0.)

           Examples of valid ways to set the high limit to motors with alias x and y.
                hlms = {'x':0., 'y':10.}
                self.put_all('HLM', x=0., y=10.)
                self.put_all('HLM', **hlms)
                self.put_all('HLM', hlms)

           Note: attributes need to be included in _put_all_attrs list.
        """
        if len(args) == 1:
            value = args[0]
        else:
            value = {kw: val for kw,val in kwargs.items() if kw in self._attrs}

        if attr in self._put_all_attrs:
            for alias in self._attrs:
                device = self.get_device(alias)
                if device is not None:
                    print attr, alias, value
                    if isinstance(value, dict):
                        val = value.get(alias)
                        print '    ', val
                        if val is not None and not np.isnan(val):
                            device.put(attr, val)
                    else:
                        device.put(attr, value)

    def get_all(self, attr):
        """Return dictionary of all devices.
        """
        values = {}
        for alias in self._aliases:
            device = self.get_device(alias)
            if hasattr(device, 'RTYP'):
                try:
                    values[alias] = device.get(attr)
                except:
                    pass

        return values

    def post_table(self, title=None, name='instrument', *args, **kwargs):
        """Post the epics table to the elog.
        """
        if not title:
            title = '{:} Epics Device Table:'.format(self._name)
        
        if not isinstance(title, list):
            title = [title]        

        message = message.message(*title, **kwargs)
        message.add(self.epics_table(*args, **kwargs))
        message.post(name=name, **kwargs)
        return message

    def show_table(self, *args, **kwargs):
        """Show epics table.
           Optionally provide list of epics devices.
        """
        epics_table = self.epics_table(*args, **kwargs)
        if epics_table:
            print epics_table
        else:
            print 'No live epics data to show'

    def post_info(self, name='instrument', **kwargs):
        info = psutils.capture_print('self.show_info(**kwargs)')
        elog.post(name=name, **kwargs)

    def show_info(self, attrs=None, aliases=None, prefix='', **kwargs):
        """Show info for a list of epics live pvs.
           If motor pv then show RBV otherwise show VAL.
        """
#        if not isinstance(attrs,list):
#            attrs = [attrs]
#        
#        if not aliases or len(aliases) != len(attrs):
#            aliases = attrs       

        if prefix is True:
            prefix = self._name+'.'

        aliases = sorted(self._aliases.keys())

        for alias in aliases:
            epics_device = self.get_device(alias)

            if epics_device:
                if epics_device._delim == '.':
                    if hasattr(epics_device,'RBV'):
                        value = epics_device.get('RBV', as_string=True)
                        pv = epics_device.PV('RBV')
                    elif hasattr(epics_device,'VAL'):
                        value = epics_device.get('VAL', as_string=True)
                        pv = epics_device.PV('VAL')
                    else:
                        value = 'NA'
                        pv = None
#                    if hasattr(epics_device,'precision'):
#                        precision = epics_device.precision
#                    else:
#                        precision = 4
#                    if hasattr(epics_device, 'EGU'):
#                        units = epics_device.EGU
#                        if len(units) > 10 or units.rfind('\n') > 0:
#                            units = ''
#                    else:
#                        units = ''
#                        precision = 0

                    if hasattr(epics_device, 'DESC'):
                        doc = epics_device.DESC
                    else:
                        doc = ''
#                    name = epics_device.NAME
                    name = pv.pvname
                    if pv.units:
                        units = pv.units
                    else:
                        units = ''

                    formatstr = '{:30s} {:>12} {:6} {:>14} - {:}'
    #                if precision > 5:
    #                    formatstr = '{:18s} {:10.5g} {:6} {:>14} - {:}'
    #                elif precision == 0:
    #                    formatstr = '{:18s} {:10} {:6} {:>14} - {:}'
    #                else:
    #                    formatstr = '{:18s} {:10.3f} {:6} {:>14} - {:}'
                    print formatstr.format(prefix+alias, value, units, name, doc)
                else:
                    formatstr = '{:30s} {:>12} {:6} {:>14}'
                    try:
                        for pvalias, pv in epics_device._pvs.items():
                            print formatstr.format(prefix+alias+'.'+pvalias, pv.value, pv.units, pv.pvname) 
                    except:
                        pass

def get_pv_connections(pvnamelist):
    pvdata = {}
    connected = []
    for name in pvnamelist:
        chid = epics.ca.create_channel(name, connect=False, auto_cb=False) # note 1
        pvdata[name] = (chid, None)

    for name, data in pvdata.items():
        epics.ca.connect_channel(data[0], timeout=0.02)
    
    epics.ca.poll()

    for name, data in pvdata.items():
        data = (data[0], epics.ca.isConnected(data[0]))
        if not data[1]:
            print 'No connect to', name
        else:
            connected.append(name)

    return connected


