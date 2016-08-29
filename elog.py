import psutils

class elog(object):
    _elogs = {}

    def __init__(self, **kwargs):
        """Initialize the default elogs (current experiment and instrument)
        """
        self._add_default_elogs(**kwargs)
    
    def _add_default_elogs(self, exp=None, instrument=None, **kwargs):
        """Add the current experiment and instrument elog to dictionary of elogs.
        """
        if exp:
            if not instrument:
                instrument = exp[0:3]
                if instrument == 'dia':
                    instrument = exp[3:6]
            
            self.add_elog(exp, \
                    exp[0:3].upper(), exp, ws_login_user=instrument+'opr')
            
        if not instrument:
            instrument = psutils.instrument_guess()
       
        self.add_elog('instrument', \
                'NEH', instrument.upper()+' Instrument', ws_login_user=instrument+'opr')
        self.add_elog(instrument, \
                'NEH', instrument.upper()+' Instrument', ws_login_user=instrument+'opr')
        self.add_elog('current', \
                instrument.upper(), 'current', ws_login_user=instrument+'opr')

    def add_elog(self, name, *args, **kwargs):
        """Add an elog 
        """
        from LogBook import message_poster
        if 'ws_login_password' not in kwargs:
            kwargs['ws_login_password'] = 'pcds'
        
        elog_args = {key: item for key, item in kwargs.items() if key in \
                ['ws_base_url', 'ws_login_user', 'ws_login_password', 'child_cmd']} 
        self._elogs[name] = message_poster.message_poster(*args, **elog_args)

    def post(self, mesage, name='current', **kwargs):
        """Post message into an elog.
            name -- name of elog (default is 'current', the current experiment for the givent instrument)
        """
        if name in self._elogs:
            elog_args = {key: item for key, item in kwargs.items() if key in \
                    ['tags', 'attachments', 'parent_message', 'run_num']} 
#                    ['ws_base_url', 'ws_login_user', 'ws_login_password', 'child_cmd']} 
            self._elogs[name].post(message, **elog_args)

    def __getattr__(self, attr):
        if attr in self._elogs:
            return self._elogs[attr]

    def __dir__(self):
        all_attrs = set(self._elogs.keys() +
                        self.__dict__.keys() + dir(elog))
        return list(sorted(all_attrs))

def post(_message, name='current', **kwargs):
    """Post message into an elog.
        name -- name of elog (default is 'current', the current experiment for the givent instrument)
    """
    if name not in elog._elogs:
        _elog = elog()

    if name not in elog._elogs:
        experiment = name
        if name.startswith('DIA'):
            instrument = name[3:6]
        else:
            instrument = name[0:3]

        _elog.add_elog(experiment, \
                instrument.upper(), experiment, ws_login_user=instrument+'opr')

    if name in elog._elogs:
        elog_args = {key: item for key, item in kwargs.items() if key in \
                     ['tags', 'attachments', 'parent_message', 'run_num']} 
#                ['ws_base_url', 'ws_login_user', 'ws_login_password', 'child_cmd']} 
        elog._elogs[name].post(_message, **elog_args)
    else:
        print 'No elog to post to called', name

def instrument_post(_message, **kwargs):
    """Post message into instrument elog.
    """
    post(_message, name='instrument', **kwargs)



