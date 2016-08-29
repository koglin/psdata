import psdata
import epics
import time
import numpy as np

hutch_info = {
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
            'pvs': {
                },
            'parameters': {
                }
            },
        'mec': {
            'id': 6,
            },
        'mfx': {
            'id': 5,
            },
        }


class sequencer(psdata.Detector):
    """Event Sequencer Class of psdata.Detector.

       Confluence User guide:
         https://confluence.slac.stanford.edu/display/PCDS/Event+Sequencer+User+Guide

       User manual for more details:
         https://confluence.slac.stanford.edu/download/attachments/146714251/Event%20Sequencer%20User%20Manual%20-%20rev%20N.docx?version=1&modificationDate=1426303866000&api=v2

    """

    def __init__(self,*args,**kwargs):

        psdata.Detector.__init__(self,*args,**kwargs)

        instrument = kwargs.get('instrument', self._data.instrument)
        hutch_id = hutch_info[instrument]['id']
        seq_base = 'ECS:SYS0:{:}:'.format(hutch_id)

        # in future will want to automatically load all the relevant PV records.
        epics_devices = {
                'play_status':      seq_base+'PLSTAT',
                'beam_request':     seq_base+'BEAMPULSEREQ',
                'play_mode':        seq_base+'PLYMOD',
                'play_count':       seq_base+'PLYCNT',
                'hutch_id':         seq_base+'HUTCH_ID',
                'nrepeats_to_do':   seq_base+'REPCNT',
                'total_count':      seq_base+'TPLCNT',
                'seq_length':       seq_base+'LEN',
                'play_control':     seq_base+'PLYCTL',
                'sync_marker':      seq_base+'SYNCMARKER',
                'sync_next_tick':   seq_base+'SYNCNEXTTICK',
                'current_step':     seq_base+'CURSTP',
                'array_subroutine': seq_base+'SEQ',
                'beam_rate':        'EVNT:SYS0:1:LCLSBEAMRATE',
                }

        self.add_device(**epics_devices)

# Need to chose where make_sequence goes -- for now put in pulsepicker to avoid recursion
#        self.include_detector('picker', module='pulsepicker')
        
        # Teddy found that this PROC field was set to zero when we 
        # were not able to update the event sequencer.  
        # Just set it by default when loading this to 1 to make sure.
        try:
            self.array_subroutine.put('PROC', 1)
        except:
            print 'Cannot Set array_subroutine PROC -- are you the owner???'

        self.show_sequence()
        #print 'Use {:}.{:} to setup sequencer'.format(self.__module__, self.set_on_off_odd.__func__.__name__)
        #print self.set_on_off_odd.__doc__
    
    def start(self, wait=False, use_complete=True):
        """Start Event Sequencer.
             wait -- wait until scan is complete before returning
        """
        self.play_control.put('VAL', 1, use_complete=use_complete)
        while wait and self.play_status.VAL == 0:
            time.sleep(0.001)
        while wait and self.play_status.VAL > 0:
            time.sleep(0.004)

    def stop(self, wait=False, use_complete=True):
        """Stop Event Sequencer.
             wait -- wait until scan is complete before returning
        """
        self.play_control.put('VAL', 0, use_complete=True)
        while wait and self.play_status.VAL > 0:
            time.sleep(0.004)

    def repeat(self, value, start=True, verbose=False, wait=False, **kwargs):
        """Set number of times to repeat and start sequencer.
                1:  set self.play_mode.VAL = 1 ('Once')
                N:  set self.play_mode.VAL = 2 ('Repeat N Times') 
                    and self.nrepeats_to_do = N
                -1: set self.play_mode.VAL = 3 ('Repeat Forever')
        """
        if value == 1:
            self.play_mode.put('VAL', 0, wait=True)
        elif value > 1:
            if verbose:
                print 'Change play mode and repeat', value
            self.play_mode.put('VAL', 1, wait=True)
            self.nrepeats_to_do.put('VAL', value, wait=True)
        elif value < 0:
            self.play_mode.put('VAL', 2, wait=True)
        else:
            return

        start_count = self.total_count.VAL
        if start:
            if wait and value > 0:
                self.start(**kwargs)
                while self.total_count.VAL < (start_count+value):
                    time.sleep(0.008*value)
            else:
                self.start(wait=wait, **kwargs)

    @property
    def seq_dict(self):
        '''Dictionary of sequencer information.
        '''
        seq_dict = {
            'Hutch ID': self.hutch_id,
#            'Beam Rate': epics.pv.PV('EVNT:SYS0:1:LCLSBEAMRATE').get(),
            'Beam Rate': str(self.beam_rate),
            'Play Count': str(self.play_count),
            'Total Play Cnt': str(self.total_count),
            'Play Status': str(self.play_status),
            'Current Step': str(self.current_step),
            }

        return seq_dict

    def get_sequence(self):
        """Get the seqeunce from the A, B, C and D fields in the ECS:SYS:#:SEQ record.
        """
        info = ''
        for attr, val in self.seq_dict.items():
            info += '{:20} {:>12}\n'.format(attr, val)
        
        info += '-'*80+'\n'

        seq_len = self.seq_length.value
        ec_array = self.array_subroutine.A[0:seq_len]
        beam_array = self.array_subroutine.B[0:seq_len]
        fiducial_array = self.array_subroutine.C[0:seq_len]
        burst_array = self.array_subroutine.D[0:seq_len]
        info += '{:>6} {:>6} {:>6} {:>6} {:>6}  {:30}\n'.format( \
                'Step', 'Code', 'Beam', 'Fiduc', 'Burst', 'Desc')
        info += '-'*80+'\n'
        if hasattr(self, 'array_subroutine'):
            for i in range(seq_len):
                ec = ec_array[i]
                beam = beam_array[i]
                fiducial = fiducial_array[i]
                burst = burst_array[i]
                try:
                    desc = epics.pv.PV('EVNT:SYS0:1:NAME'+str(ec)).get()
                except:
                    desc = ''

                info += '{:6} {:6} {:6} {:6} {:6}  {:30}\n'.format( \
                        i, ec, beam, fiducial, burst, desc)
                
        return info

    def show_sequence(self):
        """Show the event sequncer'
        """
        self.show_info()
        print '-'*80
        print self.get_sequence()

    def set_off_rate(self, nthoff=7, on=183, off=184, sync='120Hz'):
        eventCodes = [on for i in range(nthoff-1)]
        eventCodes.append(off)
        beam = [1 for ec in eventCodes]
        self.set_sync(sync)
        self.set_sequence(eventCodes=eventCodes, beam=beam)
        self.show_sequence()

    def set_psuedo_random(self, on=183, off=184, sync='120Hz'):
        """Set standard psuedo random on/off sequence.
        """
        # Old sequence we have done that had 18 steps but with 2/1 high/low phase
        #eventCodes = [on, off, on, on, off, off, off, on, off, on, off, on, off, on, off, on, on, off]
        # Sequence of 10 on and 10 off with 1/1 high/low phase
        #eventCodes = [on, off, on, off, on, off, on, off, on, off, off, on, off, on, off, on, off, on, off, on]
        # Sequence of 9 on and 8 off repeating so that phase is swapped every 17 events
        eventCodes = [on, off, on, off, on, off, on, off, on, off, on, off, on, off, on, off, on]

        beam = [1 for ec in eventCodes]
        self.set_sync(sync)
        self.set_sequence(eventCodes=eventCodes, beam=beam)
        self.show_sequence()

    def set_sync(self, sync):
        """Set the sequencer Sync Marker.
        """
        if sync:
            try:
                self.sync_marker.put('VAL', sync)
            except:
                print 'Invalid sync setting -- enter one of the following:'
                print '   120Hz, 60Hz, 30Hz, 10Hz, 5Hz, 1Hz, 0.5Hz'
                return -1 


    def set_on_off_odd(self, steps=119, odd=183, even=192, picker=None, 
                             sync='120Hz',
                             beam_even=None, beam_odd=None, beam_dark=1, dark=None, daq=None):
        """
        Primary keyword arguments:
            steps:      Number of steps in the sequence
            sync:       Sync Marker -- 120Hz, 60Hz, 30Hz, 10Hz, 5Hz, 1Hz, 0.5Hz
            odd:        Odd event code
            even:       Even event code
            daq:        daq event code for every shot
            
        If not using sync keyword, the delta beam before odd and even events can be separately set
            beam_even:  delta_beam before even event code
            beam_odd:   delta_beam before odd event code
        
        Other keyword arguments:  (CsPad not stable with these) 
            beam_dark:  delta_beam before dark at end of sequence
            dark:       dark event code at end of sequence

        # Example to set laser on/off sequence with laser at 60 Hz with extra off once every second
        # to laser on and laser off alternate every second to be on event code 41 
        --> cxi.sequencer.set_on_off_odd(steps=119,odd=183,even=192,picker=None)
        # Example of 15 Hz laser
        --> cxi.sequencer.set_on_off_odd(steps=29,odd=183,even=192,picker=None,sync='30Hz') 
        """
        if sync:
            self.set_sync(sync)
            if not beam_even or not beam_odd:
                beam_even = beam_odd = int(120/float(sync.rstrip('Hz')))

        eventCodes = []
        beam = []
        for i in range(steps):
            if i % 2 == 0:
                beam.append(beam_even)
            else:
                beam.append(beam_odd)

            if picker:
                eventCodes.append(picker)
                beam.append(0)
            
            if daq:
                eventCodes.append(daq)
                beam.append(0)
            
            if i % 2 == 0:
                eventCodes.append(even)
            else:
                eventCodes.append(odd)

        if dark:
            beam.append(beam_dark)
            if daq:
                eventCodes.append(daq)
                beam.append(0)
            
            eventCodes.append(dark)

        self.set_sequence(eventCodes=eventCodes, beam=beam)
        self.show_sequence()

    def set_sequence(self, eventCodes=[0], beam=[0], fiducial=[0], burst=[0], 
                           seq_length=None):
        """Set event sequencer.
        """
        if not seq_length:
            seq_length = len(eventCodes)
        
        self.array_subroutine.put('A', filled_array(eventCodes))
        self.array_subroutine.put('B', filled_array(beam))
        self.array_subroutine.put('C', filled_array(fiducial))
        self.array_subroutine.put('D', filled_array(burst))

        for i in range(20):
            if i < seq_length:
                ec = eventCodes[i]
                pvname = 'CXI:ECS:IOC:01:EC_5:{:02}.DESC'.format(i)
                ecname = epics.pv.PV('EVNT:SYS0:1:NAME'+str(ec)).get()
                epics.pv.PV(pvname).put(ecname)
            else:
                pvname = 'CXI:ECS:IOC:01:EC_5:{:02}.DESC'.format(i)
                epics.pv.PV(pvname).put('')

        self.seq_length.VAL = seq_length
        time.sleep(0.2)
        self.array_subroutine.put('PROC', 1)
        time.sleep(0.2)

#    def make_sequence(self, nevents=1, burst=False, picker=True,
#            shoot_code=187, mon_code=181, mon_rate=30, shoot_rate=120, picker_code=185):
#        """Helper function to set sequencer for shoot and monitor.
#        """
#        eventCodes = []
#        beam = []
#        burst_list = []
#        if picker:
#            if shoot_rate == 120 and nevents > 1:
#                self.picker.follower_mode()
#                eventCodes.append(picker_code)
#                beam.append(0)
#                burst_list.append(0)
#            else:
#                self.picker.flipflop_mode()
#
#        for i in range(nevents):
#            if picker and (shoot_rate < 60 or nevents == 1): 
#                eventCodes.append(picker_code)
#                beam.append(0)
#                burst_list.append(0)
#
#            eventCodes.append(shoot_code)
#            beam.append(1)
#            if burst:
#                burst_list.append(1)
#            else:
#                burst_list.append(0)
#
#            if (i % (shoot_rate/mon_rate)) == 0:
#                eventCodes.append(mon_code)
#                beam.append(0)
#                burst_list.append(0)
#
#        if picker:
#            if shoot_rate == 120 and nevents > 1:
#                eventCodes.append(picker_code)
#                beam.append(0)
#                burst_list.append(0)
# 
#        self.set_sequence(eventCodes=eventCodes, beam=beam, burst=burst_list)


def filled_array(values, **kwargs):
    if 'size' in kwargs:
        size = kwargs['size']
    else:
        size = 2048

    farray = [0] * size
    farray[:len(values)] = values
    return np.array(farray)


