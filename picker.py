
from motor_pcds import Motor

_picker_info = { 
           'XRT:DIA:MMS:16': {
               'alias': 'picker',
               'instrument': 'cxi',
               'evr': 'CXI:R48:EVR:41:TRIG0',
               'sequencer': 'ECS:SYS0:5', 
               },
           'CXI:DS1:MMS:14': {
               'alias': 'sc3picker',
               'instrument': 'cxi',
               'evr': 'CXI:R52:EVR:01:TRIG0',
               'sequencer': 'ECS:SYS0:5',
               }
         }
 
class picker(Motor):
    """XIP Pulse Picker Class of psdata.Detector.
    """

    _follower_mode = False
    #_path = '/reg/neh/home/koglin/src/psdata/'
  
    def __init__(self, name, **kwargs):

        Motor.__init__(self, name, **kwargs)

        self.add_device(beam_rate='EVNT:SYS0:1:LCLSBEAMRATE')

        evr = _picker_info.get(name,{}).get('evr')
        if evr:
            print 'adding evr', evr
            self.add_device(evr=evr)
            # need option dir=True to put in tab accessible dir

        sequencer = _picker_info.get(name,{}).get('sequencer')
        if sequencer:
            print 'adding sequencer', sequencer
            self.add_device(sequencer=sequencer)

    def burst(self, nevents=1, wait=True, **kwargs):
        """
        """
        if self.SE != 2:
            self.flipflop_mode()

        self.sequencer.repeat(nevents, wait=wait)

    def open(self, wait=True):
        """Open pulse picker.  
           If pulse picker is in follower mode set EVR polarity.
        """
        if self.SE == 6:
            self.evr.polarity.put('VAL', 1, use_complete=True)
        else:
            self.RESET_PG = 0
            if self._follower_mode:
                self.follower_mode()
                self.evr.polarity.put('VAL', 1, use_complete=True)
            else:
                self.records.S_OPEN.put('VAL', 1, use_complete=True, wait=wait)

    def close(self):
        """Close pulse picker.
           If pulse picker is in follower mode set EVR polarity.
        """
        if self.SE == 6:
            self.evr.polarity.put('VAL', 0)
        else:
            self.S_CLOSE = 1

    def stop_beam(self, wait=False):
        """Quicky close picker with EVR polarity if in follower mode.
           Make sure it is closed by setting to closed mode.
        """
        if self.SE == 6:
            self.evr.polarity.put('VAL', 0, use_complete=True)
        
        self.records.S_CLOSE.put('VAL', 1, use_complete=True, wait=wait)

    def flipflop_mode(self, wait=True):
        """Set Flip-flop mode.
        """
        self.reset_mode()
        self.records.RUN_FLIPFLOP.put('VAL', 1, use_complete=True, wait=wait) 
    
    def follower_mode(self, wait=True):
        """Set Follower mode.
        """
        self.reset_mode()
        self.records.RUN_FOLLOWERMODE.put('VAL', 1, use_complete=True, wait=wait)
        self._follower_mode = True

    def reset_mode(self, wait=True):
        self.records.RESET_PG.put('VAL', 1, use_complete=True, wait=wait)

    def home_motor(self, wait=True):
        """Home Pulse picker motor.
        """
        self.records.HOME_MOTOR.put('VAL', 1, use_complete=True, wait=wait)
        self._follower_mode = False


    def make_sequence(self, nevents=1, burst=False, picker=True,
            shoot_code=187, mon_code=181, mon_rate=30, shoot_rate=120, picker_code=185):
        """Helper function to set sequencer for shoot and monitor.
        """
        eventCodes = []
        beam = []
        burst_list = []
        if picker:
            if shoot_rate == 120:
                self.follower_mode()
                eventCodes.append(picker_code)
                beam.append(0)
                burst_list.append(0)
            else:
                self.flipflop_mode()

        for i in range(nevents):
            if picker and shoot_rate < 60: 
                eventCodes.append(picker_code)
                beam.append(0)
                burst_list.append(0)

            eventCodes.append(shoot_code)
            beam.append(1)
            if burst:
                burst_list.append(1)
            else:
                burst_list.append(0)

            if mod(i, shoot_rate/mon_rate) == 0:
                eventCodes.append(mon_code)
                beam.append(0)
                burst_list.append(0)

        if picker:
            if shoot_rate == 120:
                self.follower_mode()
                eventCodes.append(picker_code)
                beam.append(0)
                burst_list.append(0)
 
        self.sequencer.set_sequence(eventCodes=eventCodes, beam=beam, burst=burst_list)


