import psdata
import epics
import time

picker_info = {
        'amo:0': {
            'id': 1,
            },
        'sxr:0': {
            'id': 2,
            },
        'xpp:0': {
            'id': 3,
            },
        'xcs:0': {
            'id': 4,
            },
        'mfx:0': {
            'id': 5,
            'evr_base': 'CXI:R48:EVR:41:TRIG0',
            'pvs': {
                'y':   'MFX:DG2:MMS:11',
                'x':   'MFX:DG2:MMS:10',
                'pp':  'MFX:DG2:MMS:09',
                },
            'parameters': {
                }
            },
        'cxi:0': {
            'id': 5,
            'evr_base': 'CXI:R48:EVR:41:TRIG0',
            'pvs': {
                'y':   'XRT:DIA:MMS:12',
                'x':   'XRT:DIA:MMS:15',
                'pp':  'XRT:DIA:MMS:16',
                },
            'parameters': {
                }
            },
        'cxi:1': {
            'id': 5,
#            'evr_base': 'CXI:R48:EVR:41:TRIG0',
#            'pvs': {
#                'y':   'XRT:DIA:MMS:12',
#                'x':   'XRT:DIA:MMS:15',
#                'pp':  'XRT:DIA:MMS:16',
#                },
            'evr_base': 'CXI:DS1:EVR:01:TRIG0',
            'pvs': {
                'y':  'CXI:DS1:MMS:12',
                'x':  'CXI:DS1:MMS:13',
                'pp':  'CXI:DS1:MMS:14',
                },
            'parameters': {
                }
            },
        'mec:0': {
            'id': 6,
            },
        }

class pulsepicker(psdata.Detector):
    """XIP Pulse Picker Class of psdata.Detector.
    """

    _follower_mode = False
    _sequencer_mode = None
    #_path = '/reg/neh/home/koglin/src/psdata/'
  
    def __init__(self,*args,**kwargs):

        psdata.Detector.__init__(self,*args,**kwargs)

        instrument = kwargs.get('instrument', self._data.instrument)
        station = kwargs.get('station', self._data.station)
        if not station:
            station = 0
        inst_id = '{:}:{:}'.format(instrument,station)
#        hutch_id = picker_info[inst_id]['id']

        pvs = picker_info[inst_id].get('pvs')
        if pvs:
            self.add_device(**pvs)

        self.add_device(beam_rate='EVNT:SYS0:1:LCLSBEAMRATE')

        evr_base = picker_info[inst_id].get('evr_base')
#        self.include_detector('ppevr', module='evr_channel', path=self._path, alias='evr', base=evr_base)
#        self.include_detector('sequencer', module='sequencer', path=self._path)
        self.include_detector('ppevr', module='evr_channel', alias='evr', base=evr_base)
        self.include_detector('sequencer', module='sequencer')

    def burst(self, nevents=1, wait=True, **kwargs):
        """
        """
        if self.pp.SE.VAL != 2:
            self.flipflop_mode()

        self.sequencer.repeat(nevents, wait=wait)

    def open(self, wait=True):
        """Open pulse picker.  
           If pulse picker is in follower mode set EVR polarity.
        """
        if self.pp.SE.VAL == 6:
            self.evr.polarity.put('VAL', 1, use_complete=True)
        else:
            self.pp.RESET_PG.put('VAL', 0, use_complete=True, wait=wait)
            if self._follower_mode:
                self.follower_mode()
                self.evr.polarity.put('VAL', 1, use_complete=True)
            else:
                self.pp.S_OPEN.put('VAL', 1, use_complete=True, wait=wait)

    def close(self, wait=False):
        """Close pulse picker.
           If pulse picker is in follower mode set EVR polarity.
        """
        if self.pp.SE.VAL == 6:
            self.evr.polarity.put('VAL', 0, wait=wait)
        else:
            self.pp.S_CLOSE.put('VAL', 1, use_complete=True, wait=wait)

    def stop_beam(self, wait=False):
        """Quicky close picker with EVR polarity if in follower mode.
           Make sure it is closed by setting to closed mode.
        """
        if self.pp.SE.VAL == 6:
            self.evr.polarity.put('VAL', 0, use_complete=True)
        
        self.pp.S_CLOSE.put('VAL', 1, use_complete=True, wait=wait)


    def flipflop_mode(self, wait=True):
        """Set Flip-flop mode.
        """
        self.reset_mode()
        self.pp.RUN_FLIPFLOP.put('VAL', 1, use_complete=True, wait=wait) 
    
    def follower_mode(self, wait=True):
        """Set Follower mode.
        """
        self.reset_mode()
        self.pp.RUN_FOLLOWERMODE.put('VAL', 1, use_complete=True, wait=wait)
        self._follower_mode = True

    def reset_mode(self, wait=True):
        self.pp.RESET_PG.put('VAL', 1, use_complete=True, wait=wait)

    def home_motor(self, wait=True):
        """Home Pulse picker motor.
        """
        self.pp.HOME_MOTOR.put('VAL', 1, use_complete=True, wait=wait)
        self._follower_mode = False

# Should eventually go in sequencer.py instead of here
    def make_sequence(self, nevents=1, burst=False, picker=True,
            shoot_code=187, mon_code=181, mon_rate=30, shoot_rate=120, picker_code=185, sync=None):
        """Helper function to set sequencer for shoot and monitor.
        """
        if sync:
            self.sequencer.set_sync(sync)

        sync_rate = self.sequencer.sync_rate 
        beam_rate = self.sequencer.beam_rate.VAL
        if sync_rate > beam_rate:
            print 'Setting sync_rate to be beam_rate'
            self.sequencer.sync_marker.VAL = beam_rate

        eventCodes = []
        beam = []
        burst_list = []
        if picker:
            if shoot_rate == 120 and nevents > 1:
                self.follower_mode()
                self._sequencer_mode = 'follower'
                eventCodes.append(picker_code)
                beam.append(0)
                burst_list.append(0)
            else:
                self.flipflop_mode()
                self._sequencer_mode = 'flipflop'

        for i in range(nevents):
            nnext = (120/shoot_rate)-1
            if picker and (shoot_rate < 60 or nevents == 1): 
                eventCodes.append(picker_code)
                beam.append(nnext)
                burst_list.append(0)

            eventCodes.append(shoot_code)
            if shoot_rate == 120 or picker:
                beam.append(1)
            else:
                beam.append(nnext)
            
            if burst:
                burst_list.append(1)
            else:
                burst_list.append(0)

            if mon_rate and (i % (shoot_rate/mon_rate)) == 0:
                eventCodes.append(mon_code)
                beam.append(0)
                burst_list.append(0)

        if picker:
            if shoot_rate == 120 and nevents > 1:
                self.follower_mode()
                self._sequencer_mode = 'follower'
                eventCodes.append(picker_code)
                beam.append(0)
                burst_list.append(0)
 
        self.sequencer.set_sequence(eventCodes=eventCodes, beam=beam, burst=burst_list)

        if shoot_rate > beam_rate:
            raise Exception('ERROR:  (shoot_rate = {:} Hz) > (beam_rate = {:} Hz) results in no X-rays'.format(shoot_rate, beam_rate))


        # in future will want to automatically load all the relevant PV records.
#        epics_devices = {
#                'SD_SIMPLE':       pp_base+':SD_SIMPLE',   #  'Mode Status Simple'
#                'SD':              pp_base+':SD',          #  'Mode Status'
#                'SE':              pp_base+':SE',          #  'Program Mode'
#                'SET_SE':          pp_base+':SET_SE',      #  'Set Program Mode'
#                'RESET_PG':        pp_base+':RESET_PG',    #  'Reset Mode'
#                'S_OPEN':          pp_base+':S_OPEN',      #  'Open'
#                'S_CLOSE':         pp_base+':S_CLOSE',      #  'Open'
#                'DF':              pp_base+':DF',          #  'Motor Position'
#                'drift_upper':     pp_base+':UD',          #  'Upper Limit Violations'
#                'drift_lower':     pp_base+':LD',          #  'Lower Limit Violations'
#                'fan_status':      pp_base+':I4_L',        #  'Fan Status'
#                'heartbeat':       pp_base+':HB',          #  'MCode Heartbeat'
#                'mcode_version':   pp_base+':NS',          #  'MCode Version'
#                'moving':          pp_base+':MV',          #  'Motor Moving' 
#                'beam_rate':       'EVNT:SYS0:1:LCLSBEAMRATE',
#                }

#        self.add_device(**epics_devices)


