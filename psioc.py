import psutils
from iocmanager import utils as iocutils
import re
import operator
from glob import glob
import subprocess

import epics
import lcls_devices
import psdevice

_iocData_dir = '/reg/d/iocData/'

def get_ioc_pvlist(file, quiet=False):
    pv_dict = {}
    try:
        with open(file,'r') as f:
            for line in f:
                items = line.split(',')
                pv_dict.update({items[0]: items[1].split('\n')[0].strip().strip('"')})
    except:
        if not quiet:
            print 'No pvlist file', file

    return pv_dict

def get_ioc_archive(file, quiet=False):
    pv_dict = {}
    try:
        with open(file,'r') as f:
            for line in f:
                items = line.split()
                if len(items) == 3:
                    if '.' in items[0]:
                        pvbase, attr = items[0].split('.')
                    else:
                        pvbase, attr = items[0].rsplit(':',1)

                    ditem = pv_dict.get(pvbase)
                    if not ditem:
                        pv_dict.update({pvbase: {}})
                        
                    pv_dict[pvbase].update({attr: (items[1], items[2])})

    except:
        if not quiet:
            print 'No archive file', file

    return pv_dict

def get_ioc_autosave(file, quiet=False):
    pv_dict = {}
    try:
        with open(file,'r') as f:
            for line in f:
                items = line.split()
                if not line.startswith('#') and len(items) > 1:
                    if '.' in items[0]:
                        pvbase, attr = items[0].split('.')
                    else:
                        pvbase, attr = items[0].rsplit(':',1)

                    ditem = pv_dict.get(pvbase)
                    if not ditem:
                        pv_dict.update({pvbase: {}})
                        
                    pv_dict[pvbase].update({attr: ' '.join(items[1:])})

    except:
        if not quiet:
            print 'No autosave file', file

    return pv_dict

def open_xterm_less(file):
    try:
        subproc = subprocess.Popen('xterm -fn 80x60 -e less {:}'.format(file), 
                         stdout=subprocess.PIPE, shell=True)
    except:
        print 'Cannot open log file', file


class IOC(object):
    """Tab accessible dictified ioc information from iocmanager.cfg.
    """

    _cfg = {}
    _aliases = {}
    _hioc_list = []
    _pv_ioc = {}
    _pv_rtyp = {}
    _cfg_iocs = {}
    _cfg_hosts = {}
    _cfg_last_save_time = {}
    _pv_autosave = {}
    _pv_archive = {}

    _hioc_dir = '/reg/d/iocCommon/hioc/'
    _cfg_dir = '/reg/g/pcds/pyps/config/'

    def __init__(self, no_init=False, **kwargs):

        if not no_init:
            self.load_cfg(**kwargs)

        self.rtypes = RecordTypes()

    def load_cfg(self, instrument=None, quiet=False, **kwargs):
        if not instrument:
            instrument = psutils.instrument_guess()
        else:
            instrument = instrument.lower()

        if not quiet:
            print 'Loading IOC manager config for {:}'.format(instrument)
        cfg_file = '{:}{:}/iocmanager.cfg'.format(self._cfg_dir, instrument)
        time, iocs, hosts, dump = iocutils.readConfig(cfg_file)
        ioc_dict = {}
        host_dict = {host: {'instrument': instrument, 'siocs': [], 'hioc': False} for host in hosts}
        for ioc in iocs:
            alias = ioc['alias']
            if not alias:
                alias = ioc['id']

            alias = re.sub('-| ', '_', alias)
            alias = re.sub('[\W]+', '', alias)
#            key = ioc['id'].replace('-','_').replace(' ', '_').rsplit('ioc_')[1]
            key = ioc['id'] #.rsplit('ioc-')[1]
            if ioc.get('dir').startswith('/reg/g/pcds/controls'):
                if not quiet:
                    print 'skipping recording ioc', key
            else:
                self._aliases[alias] = key
                ioc_dict[key] = ioc
                host_dict[ioc['host']]['siocs'].append(key)

        self._cfg.update({'last_save_time': time, 'iocs': ioc_dict, 'hosts': hosts})

        hioc_files = glob('{:}/ioc-{:}-*'.format(self._hioc_dir,instrument))

        for file in hioc_files:
            hioc = file.replace(self._hioc_dir,'')
            if len(hioc.split('.')) == 1:
                key = hioc #.replace('ioc-','')
                host_dict[hioc] = {'instrument': instrument, 'siocs': [], 'hioc': True}
                self._hioc_list.append(hioc)
                alias = key.replace('-','_')
                self._aliases[alias] = hioc
                self._cfg['iocs'][key] = {'host': hioc, 'alias': alias, 'id': hioc} 

        self._cfg_hosts.update(**host_dict)
        self._cfg_last_save_time.update({instrument: time}) 

        for ioc_name, ioc_cfg in self._cfg['iocs'].items():
            if not quiet:
                print 'loading', ioc_name
            
            if ioc_cfg and ioc_cfg.get('disable') is not True:
                file = '{:}/{:}/iocInfo/IOC.pvlist'.format(_iocData_dir, ioc_name)
                pv_rtyp = get_ioc_pvlist(file, quiet=quiet) 
                file = '{dir}/{ioc}/autosave/{ioc}.sav'.format(dir=_iocData_dir, ioc=ioc_name)
                pv_autosave = get_ioc_autosave(file, quiet=quiet)
                file = '{dir}/{ioc}/archive/{ioc}.archive'.format(dir=_iocData_dir, ioc=ioc_name)
                pv_archive = get_ioc_archive(file, quiet=quiet)
            else:
                pv_rtyp = {}
                pv_archive = {}
                pv_autosave = {}

            ioc_cfg.update(**{'pvs': pv_rtyp})
            self._pv_rtyp.update(**pv_rtyp)
            self._pv_archive.update(**pv_archive)
            self._pv_autosave.update(**pv_autosave)
            self._pv_ioc.update(**{pv: ioc_name for pv in pv_rtyp})
        
        self._cfg_iocs.update(**self._cfg['iocs'])

    def show_info(self):
        print '-'*80
        print 'Information for {:}'.format('iocs')
        print '-'*80
        for attr in list(sorted(self._cfg_iocs)):
            print str(getattr(self, attr))

    def __getattr__(self, attr):
        if attr in self._aliases:
            return SIOC(self._aliases[attr])

    def __dir__(self):
        all_attrs = set(self._aliases.keys() +
                        self.__dict__.keys() + dir(IOC))
        return list(sorted(all_attrs))

class RecordTypes(object):
    
    _rtypes = {}

    def __init__(self):
        self._rtypes.update({rtyp: rtyp for rtyp in set(IOC._pv_rtyp.values())})

    def __getattr__(self, attr):
        if attr in self._rtypes:
            devices = {pv.replace(':','_'): pv for pv,rtyp in IOC._pv_rtyp.items() \
                       if rtyp == attr}

        return lcls_devices.EpicsDeviceSet(attr, devices)

    def __dir__(self):
        all_attrs = set(self._rtypes.keys() +
                        self.__dict__.keys() + dir(RecordTypes))
        return list(sorted(all_attrs))


class SIOC(object):

    _info_attrs = ['id', 'alias', 'host', 'port', 'dir', 'cmd', 
                   'st_cmd_file', 'IOCPV']

    _ioc_records = ['LOCATION', 'ACCESS', 'HOSTNAME', 
                   'UPTIME', 'STARTTOD', 'TOD', 
                   'SR_rebootTime', 'SR_recentlyStr']

    def __init__(self, name, reload=False):
        self._name = name
        if not IOC._cfg:
            ioc = IOC()

        self._cfg = IOC._cfg['iocs'].get(name, {})

        expand = False
        devices = {}
        for pvs in self.pvs:
            vals = pvs.split(':')
            if 'IOC' in vals:
                nmax = len(vals)-1
            else:
                nmax = 4
            
            nlen = min([len(vals),nmax])
            alias = '_'.join(vals[:nlen])
            pvbase = ':'.join(vals[:nlen])

            if not devices.get(alias):
                devices.update({alias: {'pvbase': pvbase, 'records': {}}})
            
            if len(vals) > nmax:
                if expand:
                    devices[alias]['records'].update({'_'.join(vals[nmax:]): ':'.join(val)})
                else:
                    devices[alias]['records'].update({vals[nmax]: ':'.join(vals[:nmax+1])})

        self._device_sets = devices

        iocpvs = {pv: item['pvbase'] for pv,item in self._device_sets.items() if 'IOC' in pv}
        for pv in iocpvs:
            self._device_sets.pop(pv)

        iocpv = iocpvs.values()
        iocpv.sort(key=len)

        self.IOCPV = iocpv[0]

    @property
    def _attrs(self):
        return IOC._cfg_iocs[self._name].keys() 

    @property
    def _autosave_dict(self):
        file = '{dir}/{ioc}/autosave/{ioc}.sav'.format(dir=_iocData_dir, ioc=self._name)
        return get_ioc_autosave(file)

    @property
    def _archive_dict(self):
        file = '{dir}/{ioc}/archive/{ioc}.archive'.format(dir=_iocData_dir, ioc=self._name)
        return get_ioc_archive(file)

    def view_log(self):
        file = '{dir}/{ioc}/iocInfo/ioc.log'.format(dir=_iocData_dir, ioc=self._name)
        open_xterm_less(file)

    @property
    def st_cmd_file(self):
        file = '{top}/{dir}/build/iocBoot/{ioc}/st.cmd'.format(top=iocutils.EPICS_SITE_TOP, 
                    dir=self.dir,ioc=self.id)
        
        if not glob(file):
            file = '{top}/{dir}/iocBoot/{ioc}/st.cmd'.format(top=iocutils.EPICS_SITE_TOP, 
                    dir=self.dir,ioc=self.id)

        return file

    def view_st_cmd(self):
        file = self.st_cmd_file
        print 'Opening xterm for',file

        try:
            open_xterm_less(file)
        except:
            print 'Did not find st.cmd file', file

    def show_info(self):
        print '-'*80
        print 'Information for {:}'.format(self._name)
        print '-'*80
        for attr in self._info_attrs:
            print '{:15} {:<40}'.format(attr, getattr(self, attr))  
        for attr in self._ioc_records:
            try:
                value = getattr(self.IOC, attr).get('VAL', as_string=True)
                print '{:15} {:<40}'.format(attr, value) 
            except:
                pass

        if not self._archive_dict:
            print 'WARNING: No Archived Data'
        if not self._autosave_dict:
            print 'WARNING: No Autosave Data'

    def show_records(self, attrs=None, expand=True, prefix=None):
        """Show all additional records associated with the IMS motor.
        """
        if not attrs:
            attrs = self._device_sets.keys()
            attrs.sort()
        else:
            attrs = [attr for attr in attrs if attr in self._device_sets]

        for attr in attrs:
            if prefix:
                alias = '.'.join([prefix, attr])
            else:
                alias = attr
           
            try:
                rec = getattr(self, attr)
                rec.show_records(expand=expand, prefix=alias)
            except:
                pass

    def __getattr__(self, attr):
        if attr in self._attrs:
            return IOC._cfg_iocs[self._name].get(attr)
        if attr == 'IOC':
            return psdevice.get_device(self.IOCPV)
        if attr == 'PVS':
            devices = {pv: item['pvbase'] for pv, item in self._device_sets.items()}
            return lcls_devices.EpicsDeviceSet(self._name, devices)

#        if attr in self._device_sets:
#            records = self._device_sets[attr]['records']
#            pvbase = self._device_sets[attr]['pvbase']
#            return psdevice.new_device(pvbase,records=records)

    def __dir__(self):
        all_attrs = set(self._attrs + ['IOC','PVS'] +
#                        self._device_sets.keys() +
                        self.__dict__.keys() + dir(SIOC))
        return list(sorted(all_attrs))

    def __str__(self):
        item = IOC._cfg_iocs[self._name]
        return '< {id} on {host} {port} from {dir} >'.format(**item)

    def __repr__(self):
        return self.__str__()


def get_alias_dict(pvbase):
    devices = {}
    for device in IOC._pv_ioc:
        if device and pvbase in device:
            alias = device
            if alias.startswith(pvbase):
                alias = alias.replace(pvbase,'').lstrip(':')
            
            alias = alias.replace(':','_')
            if alias and alias[0].isdigit():
                alias = 'n'+alias
        
            devices[alias] = device
    
    return devices
    
def format_alias(attr):
    alias = attr.replace(':','_').replace('-','_')
    if alias and alias[0].isdigit():
        alias = 'n'+alias

    return alias

def get_record_details(pvbase):
    if not IOC._pv_rtyp:
        ioc = IOC()
    devices = {}
    pvbase = pvbase.rstrip(':').rstrip('.')
    pv_rtyp = {key: rtyp for key,rtyp in IOC._pv_rtyp.items() if key.startswith(pvbase)}
    pvlist = pv_rtyp.keys()
    pvlist.sort(key=len)
    for record in pvlist:
        rtyp = pv_rtyp.get(record)
        attr = record.replace(pvbase,'').lstrip(':')
        vals = attr.split(':')
        alias = format_alias(vals[0])
        if not devices.get(alias):
            devices.update({alias: {'base': record, 'records': {}, 'components': {}}}) 

        if alias == attr:
            devices[alias].update({'rtyp': rtyp}) 

        else:
            devices[alias]['records'].update({record: rtyp})
            if len(vals) > 1:
                comp = ':'.join([pvbase, vals[0], vals[1]])
                
                if not devices[alias]['components'].get(comp): 
                    devices[alias]['components'].update({comp: {}})

                devices[alias]['components'][comp].update({record: rtyp})
                
    return devices

def make_record_dict(pv_rtyp, pvbase):
    """Make a record dictionary from {pv: rtyp} dict
    """
    record_dict = {}
    pvlist = pv_rtyp.keys()
    pvlist.sort(key=len)
    for record in pvlist:
        attr = record.replace(pvbase,'').lstrip(':')
        vals = attr.split(':')
        alias = format_alias(vals[0])
        if not record_dict.get(alias):
            record_dict.update({alias: pvbase+vals[0]})

    return record_dict


def get_record_dict(pvbase):
    if not IOC._pv_rtyp:
        ioc = IOC()
    pvbase = pvbase.rstrip(':').rstrip('.')+':'
    pv_rtyp = {key: rtyp for key,rtyp in IOC._pv_rtyp.items() if key.startswith(pvbase)}

    record_dict = {}
    pvlist = pv_rtyp.keys()
    pvlist.sort(key=len)
    for record in pvlist:
        attr = record.replace(pvbase,'').lstrip(':')
        vals = attr.split(':')
        alias = format_alias(vals[0])
        if not record_dict.get(alias):
            record_dict.update({alias: pvbase+vals[0]})

    return record_dict

def get_rtyp(pvbase, connection_timeout=0.5):
    if not IOC._pv_rtyp:
        ioc = IOC()
    rtyp =  IOC._pv_rtyp.get(pvbase) 
    if not rtyp:
        epicsPV = epics.PV(pvbase+'.RTYP',connection_timeout=connection_timeout)
        if epicsPV.connected:
            rtyp = epicsPV.get()

    return rtyp

def get_ioc(attr):
    """Return ioc object for a pv or ioc name
    """
    if not IOC._pv_ioc:
        ioc = IOC()

    if attr in IOC._cfg_iocs:
        return SIOC(attr)

    pvbase = attr
    if not get_rtyp(pvbase):
        pvbase = get_record_dict(attr)
        if pvbase:
            pvbase = pvbase.values()[0]

    pvbase = IOC._pv_ioc.get(pvbase,pvbase)

    return SIOC(pvbase)

def show_pv_status(pvbase):
#    try:
        pvioc = get_ioc(pvbase)
        pvioc.show_info()
        print '-'*80
        pv = psdevice.get_device(pvbase)    
        if pv:
            pv.show_info()

#    except:
#        print pvbase, 'is not a known PV'

def show_ioc_status(iocname):
    try:
        sioc = get_ioc(iocname)
        sioc.show_info()
    except:
        print iocname, 'is not a known ioc'

def initArgs():
    """Initialize argparse arguments.
    """
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help='Input')
    parser.add_argument("launchtype", nargs='?', default=None, help='Input2')
    parser.add_argument("-p", "--pv", type=str, 
                        help='Instrument')
    parser.add_argument("-i", "--instrument", type=str, default='', 
                        help='Instrument')
    parser.add_argument("-s", "--station", type=int, 
                        help='Station')
    return parser.parse_args()

if __name__ == "__main__":
    args = initArgs()

    pvbase = None
    iocname = None
    instrument = args.instrument

    arginputs = args.input.split(' ')
    ninput = len(arginputs)

    inputname = arginputs[0]

    launchtype = args.launchtype

    if args.pv:
        pvbase = args.pv
    else:
        if ':' in inputname:
            pvbase = inputname
            if not instrument:
                instrument = pvbase.split(':')[0]
        elif '-' in inputname:
            iocname = inputname
        else:
            print 'Unknown input'

    ioc = IOC(quiet=True, instrument=instrument)
    try:
        if iocname:
            sioc = get_ioc(iocname)
            if launchtype.lower() == 'iocpv':
                print sioc.IOCPV
            elif launchtype:
                print getattr(sioc.IOC, launchtype)
            else:
                show_ioc_status(iocname)
        
        elif pvbase:
            pv = psdevice.get_device(pvbase)    
            if launchtype.lower() == 'iocpv':
                print pv.ioc.IOCPV    
            else:
                show_pv_status(pvbase)

    except:
        print ''

