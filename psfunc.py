
from glob import glob

_inventory_dir = '/var/lib/func/inventory/'
_folder_extension = '.pcdsn'

class FuncHosts(object):

    _hosts_dir = {}
    _aliases = {}

    def __init__(self):
        folders = glob('*'.join([_inventory_dir,_folder_extension]))
        hosts_dir = {f.replace(_inventory_dir,'').replace('.pcdsn',''): f for f in folders}
        self._hosts_dir.update(hosts_dir)
        for host in self._hosts_dir:
            self._aliases.update({host.replace('-','_'): host})

    def __getattr__(self, attr):
        if attr in self._aliases:
            attr = self._aliases[attr]

        if attr in self._hosts_dir:
            return FuncCatagories(attr)
        

    def __dir__(self):
        return self._aliases.keys()

def get_func_dict(host, attr):
    if not FuncHosts._hosts_dir:
        func_hosts = FuncHosts()

    try:
        folder = FuncHosts._hosts_dir.get(host)
        if folder:
            with open('{:}/{:}/inventory'.format(folder, attr), 'r') as f:
                 func_dict = eval(f.read())
            return func_dict

    except:
        print 'Cannot load hardware for {:}'.format(host)

    return {}

class FuncHardware(object):

    _hardware = {}

    def __init__(self, host):
        self._host = host

        if not FuncHosts._hosts_dir:
            func_hosts = FuncHosts()

        self._hardware.update(get_func_dict(host, 'hardware'))

    def show_info(self, noheader=False, attrs=[]):
        if not attrs:
            attrs = self._hardware.keys()

        if not noheader:
            print '--- {:} Hardware ---'.format(self._host)

        for attr in attrs:
            item = self._hardware.get(attr)
            if item.__class__ is list:
                print '{:20} {:40}'.format(attr, '<{:} element list>'.format(len(item)))    
            else:
                print '{:20} {:40}'.format(attr, item)    

    def __getattr__(self, attr):
        if attr in self._hardware:
            return self._hardware[attr]

    def __dir__(self):
        return self._hardware.keys()

    def __repr__(self):
        self.show_info()
        return '< {:} Hardware>'.format(self._host)

class FuncMount(object):

    def __init__(self, host):
        self._host = host

        self._mount = get_func_dict(host, 'mount')

    def show_info(self, noheader=False, attrs=[]):

        if not noheader:
            print '--- {:} Mount ---'.format(self._host)

        for item in self._mount:
            try:
                print '{type:14} {dir:30} {device:40} {options:20}'.format(**item)    
            except:
                pass

    def __repr__(self):
        self.show_info()
        return '< {:} Mount Info>'.format(self._host)

class FuncRpms(object):

    def __init__(self, host):
        self._host = host

        self._rpms = get_func_dict(host, 'rpms')

    def show_info(self, *args, **kwargs):
        if 'noheader' in kwargs and not kwargs.get('noheader'):
            print '--- {:} rpms ---'.format(self._host)

        for item in self._rpms:
            arg = item.split(' ')
            try:
                if not args or arg[0] in args or arg[0].startswith(args[0]):
                    print '{:30} {:3} {:10} {:20} {:20}'.format(arg[0], arg[1], arg[2], arg[3], arg[4]) 
            except:
                pass

    def __repr__(self):
        self.show_info()
        return '< {:} rpms Info>'.format(self._host)

class FuncCatagories(object):
    
    _catagories = {
#            'filetracker': FuncFiletracker, 
            'hardware': FuncHardware, 
#            'iptables': FuncIpTables, 
            'mount': FuncMount, 
            'rpms': FuncRpms, 
#            'service': FuncService, 
#            'system': FuncSystem,
            }

    def __init__(self, host):
        self._host = host

    def __getattr__(self, attr):
        if attr in self._catagories:
            return self._catagories[attr](self._host)

    def __dir__(self):
        return self._catagories.keys()




