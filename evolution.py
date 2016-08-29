
import psdata
import epics
import time
import psutils 

from pylab import *

class evolution(psdata.Detector):
    """ Detector Class of psdata.Detector.
    """

    def __init__(self,  *args,**kwargs):

        psdata.Detector.__init__(self, *args,**kwargs)
        epics_devices = {
                'laser_delay':    'CXI:R52:EVR:01:TRIG2:TDES',
                'nozzle_delay':   'CXI:R52:EVR:01:TRIG2:TDES',
                }

        self.add_device(**epics_devices)


    def scan_delay(self, min, max, step, dwell=0.2):
        for t in arange(min, max, step):
            self.nozzle_delay.VAL = t
            print 'setting delay:', t
            time.sleep(dwell)


