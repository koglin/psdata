
import psdata
import os
import time

from pylab import *

from psmon import publish
from psmon.plots import Image, XYPlot, MultiPlot

#write = sys.stdout.write

class cxi_info(psdata.Detector):
    """cxi_info Detector Class of psdata.Detector.
    """

    def __init__(self,*args,**kwargs):

        psdata.Detector.__init__(self,*args,**kwargs)

# Note x axis is backwards from AMI        
        parameters = {
                'ds1gap': 0, 
                'ds2pap': 0, 
                }

#        a=["DS1 position","DS1 gap","DS2 position","DS2 gap",\ 
#     "Photon Energy","Pulse Duration","Pulse Energy","Rep Rate",\ 
#     "Trans Factor","Si Thickness"],\ 
#     ["CXI:DS1:MMS:06.RBV","CXI:DS1:MMN:01.RBV","CXI:DS2:MMS:06.RBV",\ 
#     "CXI:DS2:MMN:01.RBV","SIOC:SYS0:ML00:AO627","SIOC:SYS0:ML00:AO820",\ 
#     "GDET:FEE1:241:ENRC","SIOC:SYS0:ML00:AO467","CXI:INS:CLC:DSBT1",\ 
#     "CXI:INS:CLC:DSBTH"] 
#
        epics_devices = {
                'info_ds1z':  'CXI:DS1:MMS:06',        
                }

        self.set_parameter(**parameters)
        self._data.epicsLive.add_device(**epics_devices)
 


