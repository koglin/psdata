"""Acqiris Functions.
"""

def _init(self):
    """Initialize function called when this file is loaded using
       the psdata Detector class load_functions call.  
       All other functions are loaded in the _user_functions 
       dictionary and called dynaically.
       e.g.,
          data.acqiris.load_functions('acqiris') 
    """
    for ch in range(self.data_shape[0]):
        name = 'Ch'+str(ch+1) 
        self.add_function(Channel(self,ch,name),name)

def nchannels(self):
    """Number of Acqiris channels.
    """
    return self.data_shape[0] 

def ch_sum(self):
    """Dictionary of max value from waveforms for acqiris channels.
       (no doc in show_info)
    """
    return [getattr(self,ch).waveform.sum() 
            for ch in self._channel_dict]

def ch_max(self):
    """Dictionary of max value from waveforms for acqiris channels.
       (no doc in show_info)
    """
    return [getattr(self,ch).waveform.max() 
            for ch in self._channel_dict]

def ch_min(self):
    """Dictionary of max value from waveforms for acqiris channels.
       (no doc in show_info)
    """
    return [getattr(self,ch).waveform.min() 
            for ch in self._channel_dict]

def ch_std(self):
    """Dictionary of max value from waveforms for acqiris channels.
       (no doc in show_info)
    """
    return [int(getattr(self,ch).waveform.std()) 
            for ch in self._channel_dict]

def _channel_dict(self):
    """Dictionary of acqiris psana data attribute index values 
       for acqiris channels.
       (no doc in show_info)
    """
    return {'Ch'+str(num+1):num for num in range(self.data_shape[0])}


class Channel(object):
    """Channel class for Acqiris Detector.
       Warning -- potential problem with order loading functions.  
       Currently loads according to .__dir__ order (i.e., alphabetically)
       instead of seqentially.
    """
    def __init__(self,acqiris,channel,name):
        self._acqiris = acqiris
        self._channel = channel
        self._name = name
        self.baseline = 0.

    @property
    def waveform(self):
        """Waveform of channel.
        """
        return self._acqiris.data(self._channel).waveforms()[0]

    @property
    def max(self):
        """Sum of Waveform of channel.
        """
        return self.waveform.max()

    @property
    def sum(self):
        """Sum of Waveform of channel.
        """
        return self.waveform.sum()-self.baseline*self.waveform.shape[0]

    def show_info(self):
        doc = 'Acqiris waveform [min,max,std]'
        name = self._name
        attrs = ['min', 'max', 'std']
        value = map(int,[getattr(self.waveform,attr)() for attr in attrs])
        print '{:8s} {:26} {:}'.format(name, value, doc)

#    @propert
#    def tdc(self):
        

#    self.waveform.__func__.__doc__ = psana.Acqiris.DataDescV1Elem.waveforms.__doc__

#    @property
#    def nbrSegments(self):
#        return self.

#    def __getattr__(self,attr):
#        if attr in 


