import sys
import time
import epics 
import lcls_records
import psioc

_mbbi_states = ['ZR','ON','TW','TH','FR','FV','SX','SV']

class Yag(lcls_records.lcls_record):

    def __init__(self, pvbase, records=None, **kwargs):

#        self._yag_stats = {}

#        if not records:
        records = psioc.get_record_dict(pvbase)

        lcls_records.lcls_record.__init__(self, pvbase, records=records, **kwargs)
        
#        self._myrecs = records

#        self._update_states()

    def _update_states(self):
        for state in _mbbi_states:
            ststr = getattr(self, state+'ST')
            stval = getattr(self, state+'VL')
            if ststr and stval:
                self._yag_states.update({ststr.replace(' ','_'): state})

#    def __getattr__(self, attr):
#        if attr in self._pv_states:
#             self.

    def __dir__(self):
        return self._yag_states.keys()




