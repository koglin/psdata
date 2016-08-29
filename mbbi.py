import lcls_records

class Mbbo(lcls_records.lcls_record):

    _mbbi_states = ['ZR','ON','TW','TH','FR','FV','SX','SV']

    def __init__(self, *args, **kwargs):

        self._pv_stats = {}

        lcls_records.lcls_record.__init__(self, *args, **kwargs)

        self._update_states()


    def _update_states(self):
        for state in _mbbi_states:
            ststr = getattr(self, state+'ST')
            stval = getattr(self, state+'VL')
            if ststr and stval:
                self._pv_states.update({ststr.replace(' ','_'): state})

#    def __getattr__(self, attr):
#        if attr in self._pv_states:
#             self.

    def __dir__(self):
        return self._pv_states.keys()




