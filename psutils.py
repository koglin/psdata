# import standard python system tools
import argparse
from glob import glob
import re
import operator
import sys
import os
import imp
import subprocess
import inspect
import pprint
import time

_lcls_instruments = ['amo','sxr','xpp','xcs','cxi','mec','xrt']
_default_exp = {'exp': 'cxitut13', 'run': 22}
_instrument_good_guess = None 
_exp_good_guess = None

def interactive_mode():
    try:
        __IPYTHON__
    except NameError:
        if hasattr(sys,'ps1'):
            return 'interactive'
        else:
            return None
    else:
        return 'ipython'

def import_module(module_name, module_path, name=None):
    """Import a module from a given path.
    """
    try:
        if not isinstance(module_path,list):
            module_path = [module_path]
        file,filename,desc = imp.find_module(module_name,module_path)
        if not name:
            name = module_name

        globals()[name] = imp.load_module(module_name, file, filename, desc)
#        setattr(sys.modules[__name__],module_name,
#                imp.load_module(module_name, file, filename, desc)) 
    except ImportError, err:
        print 'ImportError:', err
    except:
        print 'import_module error'

def getattr_complete(base, args):
    """Recursive getattr
    """
    attrs = args.split('.')
    while len(attrs) > 0:
        base = getattr(base, attrs.pop(0))

    return base

def group_members(*args, **kwargs):
    """Return dictionary of members in group.
    """
    if len(args) == 1:
        if type(args[0]) is list:
            groups = args[0]
        else:
            groups = args
    elif len(args) > 1:
        groups = args
    else:
        groups = [get_groups()]

    member_dict = group_member_dict()
    members = {}
    for group in groups:
        item = member_dict.get(group)
        if item:
            members[group] = item.get('members')
        else:
            members[group] = []

    return members

def group_member_dict():
    """Dictionary of members in groups.
    """
    
    getent_group = subprocess.Popen(["getent", "group"],
                    stdout=subprocess.PIPE).communicate()[0].split('\n')

    member_dict = {}
    for group in getent_group:
        item = group.split(':')
        if len(item) > 3:
            member_dict[item[0]] = {'id': item[2], 'members':item[3].split(',')}
    
    return member_dict

def get_user():
    """Return the username.
    """
    return os.getlogin()

def get_groups(*args, **kwargs):
    """Return dictionary of groups for list of usernames.  
    If username(s) are not input get groups for current login user.
    """
    try:
        if len(args) == 1:
            if type(args[0]) is list:
                usernames = args[0]
            else:
                usernames = args
        elif len(args) > 1:
            usernames = args
        else:
            usernames = [get_user()]

        groups = {}
        for user in usernames:
            try:
                groupinfo = subprocess.Popen(["groups",user],
                                stdout=subprocess.PIPE).communicate()[0]
                groupstr = groupinfo.split(':')[1]
                groups[user] = groupstr.split()
            except:
                groups[user] = [] 
        return groups
    except:
        print 'No groups found'
        return None

def get_experiments(*args, **kwargs):
    """Return dictionary of experiments for list of users.
    If username(s) are not input get experiments for current login user.
    """
    groups = get_groups(*args)
    experiments = {}
    for user in groups:
        try:
            experiments[user] = [exp for exp in groups[user] 
                             if len(exp) == 8 and len(exp.split('-')) == 1]
        except:
            experiments[user] = []
    return experiments

def parse_instrument(**kwargs):
    """Return (instrument, station) tuple from instrument and station keywords.
       Guess instrument and station if keywords not supplied.
    """
    if len(kwargs) > 0 and 'instrument' in kwargs.keys():
        instrument = kwargs['instrument']
    else:
        instrument = instrument_guess()
    if len(kwargs) > 0 and 'station' in kwargs.keys():
        station = kwargs['station']
    else:
        station = 0

    if len(instrument) > 3:
        try:
            station = int(instrument[4])
            if station > 1:
                station = 0
        except:
            station = 0
        instrument = instrument[0:3]

    return (instrument,station)

def active_experiment(*args, **kwargs):
    """Returns active experiment. 
    Will parse input as instrument:station where station is optional.
    Or instrument and station can be input as keywords with station=0 as default.

    PARAMETERS:

      @param instrument: the name of the instrument
      @param station: the optional station number 
            (default is 0, for cxi station 1 is the parasitic daq experiment)
      @return: the list of run descriptors as explained above
    
    """
    return 'cxic00318'
    from RegDB import experiment_info
    if len(args) > 0:
        kwargs['instrument'] = args[0]
    instrument, station = parse_instrument(**kwargs)

    try: 
        active_experiment = \
            experiment_info.active_experiment(instrument.upper(),station)[1]
    except:
        raise NameError('instrument:',instrument,'station:',station)
        print 'Cannot determint active experiment!'
        active_experiment = None

    return active_experiment

def live_source(*args, **kwargs):
    """Returns psana source string for live data from shared memory on the current node.
    """
    if 'monshmserver' in kwargs:
        monshmserver = kwargs['monshmserver']
    else:
        monshmserver = None

    if not monshmserver:
        monshmserver='psana'

    shm_srvs = glob('/dev/shm/PdsMonitorSharedMemory_'+monshmserver)
    if shm_srvs == []:
        instrument = instrument_guess()
        monshmserver = instrument.upper()
        shm_srvs = glob('/dev/shm/PdsMonitorSharedMemory_'+monshmserver)
    
    if shm_srvs != []:
        try:
            MPI_RANK = 0
            source_str = 'shmem={:}.0:stop=no'.format(monshmserver)
        except:
            print 'Exception in finding shared memory server: ',shm_srvs
            source_str = None
    else:
        source_str = None

    return source_str

def experiment_guess(*args, **kwargs):
    """Returns best guess as to what your experiment is based on
    most recent experiment for which you have been added.
    Use get_experiments to get a list of all of your experiments.
    instrument is an optional keyword to narrow the search
    """
    return 'cxic00318'
    from RegDB import experiment_info
    if len(args) == 0:
        global _exp_good_guess
        global _instrument_good_guess
    else:
        _exp_good_guess = None
        _instrument_good_guess = None

    instrument = kwargs.get('instrument')
    if instrument:
        _exp_good_guess = True
        return active_experiment(instrument)
    else:
        if _instrument_good_guess is None:
            instrument = instrument_guess() 
        else:
            instrument = None

    if instrument and is_in_group('ps-'+instrument) or is_in_psdata():
        exp_best = active_experiment(instrument)
    else:
        experiments = get_experiments(*args).values()[0]
        if len(experiments) > 0:
            nruns = 0
            iexp = 0
            while nruns == 0 and iexp < len(experiments):
                exp = experiments[-1-iexp]
                inst = exp[0:3]
                runs = experiment_info.experiment_runs(inst.upper(),exp)
                nruns = len(runs)
    #            print 'tryiing: ',exp,inst,nruns
                if nruns > 0:
                    exp_best = exp
                    nruns_best = nruns
                    if _instrument_good_guess is True and inst != instrument:
                        nruns = 0
                        _exp_good_guess = False 
                    else:
                        _exp_good_guess = True
                iexp += 1
            if nruns_best == 0:
                exp_best =  _default_exp['exp']
                _exp_good_guess = False 
        else:
            exp_best = _default_exp['exp'] 
            _exp_good_guess = False 

    return exp_best

def instrument_guess(*args):
    """Return the instrument on which you are working based. 
    """
    if len(args) > 0:
        global _instrument_good_guess
    else:
        _instrument_good_guess = None
    
    hostsplit = os.uname()[1].split('-')
    cwdsplit = os.getcwd().split('/')
    if len(hostsplit) == 2 and hostsplit[0] in _lcls_instruments:
        instrument = hostsplit[0]
        _instrument_good_guess = True
    elif len(hostsplit) > 2 and hostsplit[1] in _lcls_instruments:
        instrument = hostsplit[1]
        _instrument_good_guess = True
    elif len(cwdsplit) > 4 and cwdsplit[4] in _lcls_instruments:
        instrument = cwdsplit[4]
        _instrument_good_guess = True 
    elif len(get_ps_instruments(*args)) > 0:
        _instrument_good_guess = False
        instrument = get_ps_instruments(*args)[0]
    else:
        instrument = experiment_guess(*args)[0:3]
        _instrument_good_guess = False

    return instrument

def get_ps_instruments(*args):
    """Return list of instruments for which user is an instrument member.
       e.g., in the group 'ps-cxi'
    """
    # should add all instrument accounts if in ps-data?
    groupdict = {'ps-'+inst: inst for inst in _lcls_instruments}
    groups = get_groups(*args).values()[0]
    return [groupdict[key] for key 
            in list(set(groups) & set(groupdict.keys()))]

def get_opr_accounts(*args):
    """Return list of instruments for which user is an operator.
       e.g., in the group 'cxiopr'
    """
    groupdict = {inst+'opr': inst for inst in _lcls_instruments}
    groups = get_groups(*args).values()[0]
    return [groupdict[key] for key in list(set(groups) & set(groupdict.keys()))]

def is_in_group(group,*args):
    """Return True if user is in specified group.  
       If no username is supplied assume current user.
       Usage:
           is_in_group(group,[username])
    """
    groups = get_groups(*args).values()[0]
    return group in groups

def is_in_psdata(*args):
    """Return True if user is in 'ps-data' group.
    """
    return is_in_group('ps-data',*args)

def is_in_pcds(*args):
    """Return True if user is in 'ps-pcds' group.
    """
    return is_in_group('ps-pcds',*args)

def is_in_psusers(*args):
    """Return True if user is in 'ps-users' group.
    """
    return is_in_group('ps-users',*args)

def read_dictionary(file_name):
    """Read and return a python dictionary from file.
    """
    try: 
        with open(file_name,'r') as f:
            read_dict = eval(f.read())
    except:
        print "Failed reading ", file_name
        read_dict = None

    return read_dict

def write_dictionary(out_dict, file_name, **kwargs):
    """Write out a dictionary to file (using pprint for easy to read formatting).
    """
    print out_dict,file_name
    try:
        with open(file_name,'w') as f:
            f.write(pprint.pformat(out_dict))
    except:
        print "Failed writing to ", file_name

def capture_print(executableStrThatPrints):
    """Redirect stdout to StringIO()
        The following python code will use the capturePrint function to redirect stdio to StringIO() 
        so you can capture info that would normally just be printed. 
        --from https://joecodeswell.wordpress.com/2012/07/28/378/

       This is meant to be used temporarily while show_info procedures in psdata are moved to a class 
       for ease in posting messages as well as logging. 
       
       Note:ipython also has %%capture
    """

    import sys, StringIO

    # redir sys.stdout
    stdout = sys.stdout
    sys.stdout = reportSIO = StringIO.StringIO()

    eval(executableStrThatPrints)
    reportStr = reportSIO.getvalue()

    # restore sys.stdout so we can print
    sys.stdout = stdout 

    return reportStr

