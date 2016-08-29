import psdata
import epics
import time

class evr_channel(psdata.Detector):
    """XIP Pulse Picker Class of psdata.Detector.
    """

    def __init__(self, *args, **kwargs):

        psdata.Detector.__init__(self,*args,**kwargs)
        
        self._evrbase = kwargs.get('base')
        if self._evrbase:
            epics_devices = {
                   'count':            self._evrbase+':CNT',
                   'event_code':       self._evrbase+':EC_RBV',
                   'polarity':         self._evrbase+':TPOL',
                   'rate':             self._evrbase+':RATE',
                   'state':            self._evrbase+':TCTL',
                   'width_set':        self._evrbase+':TWID',
                   'delay_set':        self._evrbase+':TDES',
                   'width_calc':       self._evrbase+':BW_TWIDCALC',
                   'delay_calc':       self._evrbase+':BW_TDES',
                   'delay_tick_calc':  self._evrbase+':BW_TDLY',
                   'event_code':       self._evrbase+':EC',
                   'ec_name':          self._evrbase+':EC_NAME',
                    }

            self.add_device(**epics_devices)

    @property
    def delay(self):
        """EVR delay.
        """
        return self.delay_calc.get('VAL')

    @delay.setter
    def delay(self, value):
        return self.delay_set.put('VAL', value)

    @property
    def width(self):
        """EVR width.
        """
        self.width_calc.get('VAL')

    @width.setter
    def width(self, value):
        self.width_set.put('VAL', value)



