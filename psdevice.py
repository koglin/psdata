import epics
import os
import imp
import traceback
import sys
import time

import psioc 
import psutils

motor_dict = {
        'ims':    {'desc':   'IMS Motor Record',
                   'module': 'ims',
                   'class':  'IMS'},
        'motor':  {'desc':   'LCLS Version of Motor Record',
                   'module': 'motor_pcds',
                   'class':  'Motor'},
        'xps8p':  {'desc':   'Newport XPS Record',
                   'module': 'newport',
                   'class':  'Newport'},
        'arcus':  {'desc':   'Piezo PMC 100 Motor Record',
                   'module': 'pmc100',
                   'class':  'Arcus'},
        'mmca':   {'desc':   'Piezo MCA100 Motor Record',
                   'module': 'mmca',
                   'class':  'Mmca'},
        }

# Use path of lcls_records
module_path = os.path.dirname(psioc.__file__)

def import_module(module_name,module_path):
    """Import a module from a given path.
    """
    try:
        if not isinstance(module_path,list):
            module_path = [module_path]
        file,filename,desc = imp.find_module(module_name,module_path)
        globals()[module_name] = imp.load_module(module_name, file, filename, desc)
        return
    except Exception as err:
        print 'import_module error', err
        traceback.print_exc()

    sys.exit()


def new_device(base, attrs={}, records={}, delim='', module=None, 
                report_connected=False, connection_timeout=0.5,
                device_set=True, 
                **kwargs):
    
    import lcls_records
    import lcls_devices
    # import all the motor records
    for rtyp, minfo in motor_dict.items():
        import_module(minfo['module'],'')
  
    epicsPV = epics.PV(base+'.RTYP',connection_timeout=connection_timeout)
    connected = epicsPV.connect(timeout=0.05)
    if not connected:
        time.sleep(0.05)
        connected = epicsPV.connect(timeout=0.2)

    if connected:
        rtyp = epicsPV.get()
        if rtyp in motor_dict:
            minfo = motor_dict[rtyp]
            mclass = getattr(globals()[minfo['module']],minfo['class'])
            epics_device = mclass(base, records=records)
            connect_message = 'Connected epics {:} for PV {:}'.format(minfo['desc'],base)
        else:
            epics_device = lcls_records.lcls_record(base, records=records)
            connect_message = 'Connected epics {:} record for PV {:}'.format(rtyp,base)
        if report_connected:
            print connect_message
    else:
        if device_set:
            if not records:
                records = psioc.get_record_dict(base)
            name = base.replace(':','_')
            epics_device = lcls_devices.EpicsDeviceSet(name, records) 
        else:
            aliases = {alias: record.replace(base+':', '') for alias, record in records.items()}
            epics_device = lcls_devices.Device(base, records=records,aliases=aliases,delim=delim,mutable=False) 

    return epics_device

class IocDevices(object):
    """Collection of IOC Devices.
       Use _get_device as a functional interface to the class global dictionary
       where the devices are stored.
    """
    _devices = {}
    _aliases = {}

    def __init__(self):
        if not psioc.IOC._cfg:
            ioc = psioc.IOC(quiet=True)
        
#        self._aliases.update(psioc.IOC._pv_aliases)

    def add_device(self, base, alias=None, **kwargs):
        if not alias:
            alias = base.replace(':','_')

        self._aliases.update({alias: base})
        self._devices.update({base: new_device(base, **kwargs)})

    def get_device(self, attr, **kwargs):
        if attr in self._aliases:
            attr = self._aliases[attr]
        
        if attr not in self._devices:
            self.add_device(attr, **kwargs)

        return self._devices.get(attr)

    def __getattr__(self, attr):
        if attr in self._aliases:
            return self.get_device(attr)

    def __dir__(self):
        all_attrs = set(self._aliases.keys() +
                        self.__dict__.keys() + dir(IocDevices))
        return list(sorted(all_attrs))

def get_device(base, reload=False, **kwargs):
    """Get an epics device from the IocDevices storage class.
    """
    if base in IocDevices._aliases:
        base = IocDevices._aliases[base]

    if base in IocDevices._devices and not reload:
        return IocDevices._devices.get(base)
    
    else:
        ioc_devices = IocDevices()
        return ioc_devices.get_device(base, **kwargs)

