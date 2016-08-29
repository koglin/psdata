import psdata
import numpy as np
from scipy import signal

class epixSampler(psdata.Detector):
    """EpixSampler Class of psdata.Detector.
    """

    def __init__(self,*args,**kwargs):

        psdata.Detector.__init__(self,*args,**kwargs)

        parameters = {
            'nchannels': 8,
            'signal_width': 10,
            'threshold': 200,
            }

        self.set_parameter(**parameters)

        hw = self.signal_width/2
        self.set_parameter(filter=np.array([np.ones(hw),-np.ones(hw)]).flatten()/(hw*2))

        for ch in range(self.nchannels):
            name = 'Ch'+str(ch) 
            self.add_function(Channel(self,ch,name),name)

        self.add_event_function('book')

    @property
    def peaks(self):
        return [getattr(getattr(self, 'Ch'+str(ch)),'peak') for ch in range(self.nchannels)]

    def book(self):
        if 150 in self._data.evr0.eventCodes:
            for ch in range(self.nchannels):
                getattr(self, 'Ch'+str(ch)).book()

    @property
    def waveforms(self):
        """IMP data in numpy array.
        """
        return self.frame.transpose()

    def get_channel_attr(self, ch, attr):
        name = 'Ch'+str(ch) 
        return getattr(getattr(self, name), attr)

    def publish(self, channels=[0,1,2,3,4,5,6], local=True, **kwargs):
        """Publish with psmon.
             channels: list of channels to publish (default is all channels [0,1,2,3])
        """
        name = ['Ch'+str(ch)+'.waveform' for ch in channels]
        self.add_psplot(name, local=True)
        
        name = ['Ch'+str(ch)+'.filtered' for ch in channels]
        self.add_psplot(name, local=True)

        name = ['Ch'+str(ch)+'.hist4' for ch in channels]
        self.add_psplot(name, local=True)

    

class Channel(object):
    """Channel class for Imp Detector.
    """
    def __init__(self, imp, channel, name):
        self._imp = imp 
        self._channel = channel
        self._name = name
        self.baseline = 0.
        self.hist = np.zeros(2**14)
        self.hist4 = np.zeros(2**12)

    def book(self):
        self.hist[self.peak] += 1
        self.hist4[self.peak/4] += 1

    @property
    def waveform(self):
        """Waveform of channel.
        """
        return self._imp.waveforms[:,self._channel]

    @property
    def amplitude(self):
        """Amplitude of filtered channel.
        """
        return self.filtered.max()

    @property
    def filter(self):
        return self._imp.filter
    
    @property
    def filtered(self):
        hw = len(self.filter)/2
        f = -signal.convolve(self.waveform,self.filter)
        f[0:len(self.filter)+1] = 0
        f[-len(self.filter)-1:] = 0
        return f

    @property
    def time(self):
        """Time of signal in waveform. (currently channel number needs to be converted)
           Imp signals are step functions.
           Additional noise needs to be subtracted.
        """
        hw = len(self.filter)/2
        return self.filtered[hw:-hw-1].argmax()+hw

    @property
    def peak(self):
        """peak of signal in waveform.
        """
        # Simple max
        peak = self.filtered[self.time]
        if peak > self._imp.threshold:
            return peak
        else:
            return 0.

#crude calculation with no advanced background subtraction.
#        hw = len(self.filter)/2
#        wf = self.waveform
#        t0 = self.time
#        amp = wf[t0+hw:t0+hw*2].mean() \
#             -wf[t0-hw*2:t0-hw].mean()
#        
#        return amp

    def show_info(self):
        doc = 'waveform [min,max,std]'
        name = self._name
        attrs = ['min', 'max', 'std']
        value = map(int,[getattr(self.waveform,attr)() for attr in attrs])
        print '{:8s} {:26} {:}'.format(name, value, doc)



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

