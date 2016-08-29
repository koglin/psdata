import psdata
import epics
import time
import psioc

attn_info = {
        'amo': {
            'id': 1,
            },
        'sxr': {
            'id': 2,
            },
        'xpp': {
            'id': 3,
            },
        'xcs': {
            'id': 4,
            },
        'cxi': {
            'id': 5,
            'attn_base':  'XRT:DIA:MMS:16',
            },
        'mec': {
            'id': 6,
            },
        'dia': {
            'attn_base':  'XRT:DIA:ATT',
            },
        }

class attenuators(object):
#class attenuators(psdata.Detector):
    """lusi Attenuator Class of psdata.Detector.
    """

    def __init__(self, attn, verbose=True):

        if attn in attn_info:
            attn_base = attn_info[attn]['attn_base']
            self.pvs = psioc.get_device(attn_base,is_collection=True)
        
        self._verbose = verbose

    def all_in(self, wait=False):
        if self._verbose:
            print 'ok'            
        self.pvs.COM.GO = 1


#    def check_state(self):
#       for pv in self.pvs:
#          if pv.startswith('n'):
#             self.pv.
#

    def all_out(self):
        self.pvs.COM.GO = 0

    def goto_floor_energy(self):
        self.pvs.COM.GO = 2

    def goto_ceil_energy(self):
        self.pvs.COM.GO = 3

#    def show_info(self):


