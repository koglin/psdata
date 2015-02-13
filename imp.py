import psdata
import numpy

class imp(psdata.Detector):
    """Imp Class of psdata.Detector.
    """

    def __init__(self,*args,**kwargs):

        psdata.Detector.__init__(self,*args,**kwargs)

    @property
    def data(self):
        """IMP data in numpy array.
        """
        if self.data_attrs:
            return numpy.array([dat.channels() for dat in self.samples])
        else:
            return None

    @property
    def nchannels(self):
        """Number of IMP channels.
        """
        if self.data_attrs:
            vchannels = [dat.channelsPerDevice for dat in self.samples]
            if min(vchannels) != max(vchannels):
                print 'ERROR:  Non-uniform number of channels per device!!!'
                return None
            else:
                return vchannels[0]
        else:
            return None

# use add_function
#    @property
#    def adu(self):
#        """IMP adu caculated for fixed range.
#        """
#        return self.data[370:400,:].mean(axis=0)-self.data[320:350,:].mean(axis=0)

#    def monitor_position(self,nevents=40):
#        print '{:8} {:8} {:8} {:8}'.format('Id','dYrel','dXrel','GasDet')
#        for i in range(nevents):
#            adu = self.data[370:400,:].mean(axis=0)-self.data[320:350,:].mean(axis=0)
#            gdet = self._data.FEEGasDetEnergy.f_21_ENRC
#            print '{:8} {:8.3f} {:8.3f} {:8.3f}'.format(self._data.EventId.vector,adu[0]/adu[1],adu[2]/adu[3],gdet)
#            self._data.next_event()
#

