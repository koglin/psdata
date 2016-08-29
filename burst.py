import psdata

class burst(psdata.Detector):
    """LCLS Burst Control Detector Class of psdata.Detector.
       see also /reg/g/pcds/pyps/xpp/head/xpp/linac.py
    """

    def __init__(self,*args,**kwargs):

        psdata.Detector.__init__(self,*args,**kwargs)

        parameters = {
                '_nmenu_burst_rate': 8,
                '_nmenu_control': 2, 
                '_burst_rate_fields': ['ZR','ON','TW','TH','FR','FV','SX','SV'],
                }

        epics_devices = {
                'beam_rate':          'EVNT:SYS0:1:LCLSBEAMRATE', 
                'burst_rate':         'PATT:SYS0:1:MPSBURSTRATE',
                'number_to_burst':    'PATT:SYS0:1:MPSBURSTCNTMAX',
                'current_burst_cnt':  'PATT:SYS0:1:MPSBURSTCNT',         
                '_burst_control':     'PATT:SYS0:1:MPSBURSTCTRL',
                'bykik_enabled':      'IOC:BSY0:MP01:REQBYKIKBRST',
                }

        self.add_device(**epics_devices)
        self.set_parameter(**parameters)

    @property
    def xray_rate(self):
        if self.bykik_enabled.value:
            return self.burst_rate
        else:
            return self.beam_rate

    def start_burst(self, events=None):
        """Start Burst.
        """
        if events:
            self.number_to_burst.VAL = events

        self._burst_control.VAL = 1

    def stop_burst(self):
        """Stop Burst.
        """
        self._burst_control.VAL = 0
        self.number_to_burst.VAL = 1

    def burst_forever(self):
        """Set burst control to burst continuously.
        """
        self.number_to_burst.VAL = -1
        self.start_burst()

    def set_burst_rate(self, val):
        """Set Burst rate as either integer or value.
        """
        if isinstance(val, int) and val < self._nmenu_burst_rate:
            self.burst_rate.put('VAL', val)
        else:
            for num, rate_field in enumerate(self._burst_rate_fields):
                if val.lower() == self.burst_rate.get(rate_field+'ST'):
                    self.burst_rate('VAL', num)

    def show_burst_rates(self):
        """Show Burst rates.
        """ 
        print '{:8} {:12} {:12}'.format('#', 'Value', 'Name')
        for num, rate_field in enumerate(self._burst_rate_fields):
            rate_str = self.burst_rate.get(rate_field+'ST')
            rate_val = self.burst_rate.get(rate_field+'VL', as_string=True), 
            print '{:8} {:12} {:12}'.format(num, rate_val, rate_str)
            
#    def wait_for_shot(self, verbose=False):


