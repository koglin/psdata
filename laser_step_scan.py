import psdata
import time

from pylab import *

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
                'evr_ns_delay': 'LAS:R52B:EVR:31:TRIG0:TDES',
                'evr_control': 'LAS:R52B:EVR:31:CTRL',
                },
            'parameters': {
                'time_zero_evr_ticks': 77093,
                '_acqiris_ch': 1
                }
            },
        'mec': {
            'id': 6,
            },
        }

class laser(psdata.Detector):
    """LCLS Laser Control Detector Class of psdata.Detector.
       see also /reg/g/pcds/pyps/xpp/head/xpp/linac.py
    """

    def __init__(self,  *args,**kwargs):

        psdata.Detector.__init__(self, *args,**kwargs)

        instrument = kwargs.get('instrument', self._data.instrument)

        hutch_id = hutch_info[instrument]['id']
        laser_base = 'LAS:FS{:}'.format(hutch_id)
        epics_devices = { 
                'time_delay': laser_base+':VIT:FS_TGT_TIME_DIAL',
                'time_phase_calc': laser_base+':VIT:CH1_CALC_PHASE',
                'time_phase_locked': laser_base+':VIT:PHASE_LOCKED',
                'time_phase_motor_pos': laser_base+':VIT:PHASE_MOTOR_POS',
                'time_piezo_amp_mon': laser_base+':VIT:PIEZO_AMP_MON',
                'time_set': laser_base+':VIT:FS_CTR_TIME',
                'time_status': laser_base+':VIT:FS_STATUS',
                'time_target': laser_base+':VIT:FS_TGT_TIME',
                'time_zero': laser_base+':VIT:FS_TGT_TIME_OFFSET',
                'phase_control': laser_base+':MMS:PH',
                'time_control': laser_base+':VIT:FS_ENABLE_TIME_CTRL'
                }

        self.epicsLive.add_device(**epics_devices)

        if hutch_info[instrument].get('parameters'):
            param_dict = hutch_info[instrument].get('parameters')
            self.set_parameter(**param_dict)

        if hutch_info[instrument].get('pvs'):
            pv_dict = hutch_info[instrument].get('pvs')
            self.epicsLive.add_device(**pv_dict)

        if not getattr(self._data, 'sequencer') \
                or self._data.sequencer.__class__.__name__ == 'Detector':
            self._data.add_detector('sequencer', module='sequencer')

    @property
    def sequencer(self):
        return self._data.sequencer

    @property
    def acqiris(self):
        return getattr(self._data.ami, 'Acqiris_{:}'.format(self._acqiris_ch))

    def init_ns_scan(self, scan_time=1., ns_time=15., **kwargs):
        """Initialize the timing system for a scan over 15 nsec using the phase control
           motor to slowly scan over a ns_time length with period in sec.

            Arguments:
                scan_time:  Time to make a ns_time move
                ns_time:    Move in ns

            Initialization Steps:
                - Disable Time Control
                - Drop both LAS:FS5:MMS:PH.SMAX and LAS:FS5:MMS:PH.S down to 3.75e6
                - Put in a 1.5e5ps move to LAS:FS5:MMS:PH. 
            
            This move should take ~20 seconds and LAS:FS5:VIT:FS_CTR_TIME 
            should wrap 10 times at a 15ns period.
            
            For more cycles, just put in more ps into the motor. 
            
            Its internal representation for position is signed 32-bit, 
            so there's not much chance of overflow.
        """
        ns_per_rev = self.phase_control.UREV/1000.
        phase_control_speed = ns_time/ns_per_rev/scan_time
        self.phase_control.put('SET_ZERO', 1, wait=True)
        self.phase_control.put('S', phase_control_speed, wait=True)
        self.time_control.put('VAL', 0, wait=True)
        time.sleep(0.1)

        print 'Disable time control:'
        print '  - prevents timing control of the phase motor and EVR'
        print '  - phase lock remains in effect'
        
        print 'Set phase control speed to {:12.1} Rev/s'.format(phase_control_speed)
        print '                           {:12} ps/s'.format(self.phase_control.get('VELO'))

    def enable_time_control(self, phase_control_speed=None):
        """Enable the timing system python control.
           
           Set the phase control speed to the SMAX setting
              -- should be 5e6 Rev/s
        """
        print 'Enable time control:'
        self.time_control.VAL = 0
        
        if not phase_control_speed:
            phase_control_speed = self.phase_control.get('SMAX')
        
        if phase_control_speed > (5.e6*1.1):
            print 'Warning phase control speed > than recommended'
            print ' {:20} > 5.e7 Rev/s recommened setting'.format(phase_control_speed)

        print 'Set phase control speed to {:10.0} Rev/s'.format(phase_control_speed)
        print '                           {:10} ps/s'.format(self.phase_control.get('VELO'))
        self.phase_control.put('S', phase_control_speed, wait=True)

    def delay_step_scan(self, start, stop, step, 
                             ns_time=15., sleep=0.002, 
                             repeat=1):
        """Scan delay in tick steps with time control disabled and phase control 
           motor repeatedly scanning over 15 ns window.  
           
            start  -- approx ns start time relative to evr_time_zero_ticks
            stop   -- approx ns stop time releative to evr_time_zero_ticks
            step   -- approx ns step time per 120 Hz trigger rate
            repeat -- number of times to repeat the scan (-1 = forever)

           Redundant data will be recorded for some time points within a 8.4 ns bucket.
           Data will need to be sorted offline.
        """
        # number of ticks to scan over
        nticks = int((stop-start)/8.4)

        # set to initial evr tick time 
        itick = 0
        evr_tick = self.time_zero_evr_ticks+itick
        self.evr_control.put('DG0D', evr_tick, wait=True)
        
        # initialize ns scan setup with time control disabled
        scan_time = ns_time/120./step
        step_events = ns_time/step 
        self.sequencer.nrepeats_to_do.put('VAL', step_events, wait=True) 
        
        self.sequencer.show_sequence()
        print ''
        print '='*80

        self.init_ns_scan(scan_time=scan_time, ns_time=ns_time)
        
        evr_ns_time0 = self.evr_ns_delay.value
        
        self._time0 = time.time()
        time_last = time.time()

        total_scan_time = (nticks)*(scan_time+1.0)
        phase_control_steps = (scan_time)*self.phase_control.get('VELO')
        total_events = 0

        print 'Step scan time {:} sec plus latency'.format(scan_time)
        print 'Starting scan that will last ~{:} sec'.format(total_scan_time)

        try:
            while repeat != 0:
                print '' 
                print '{:>10} {:>10} {:>10} {:>10} {:>10} {:>10}  {:10}'.format( \
                    'time', 'tstep', 'ns_set', 'ns_delay', 'cnt', 'acqiris', 'status')
                print '-'*80

                # make scan over ticks
                for itick in range(nticks):
                    self.acqiris.ami_clear()
                    evr_tick = self.time_zero_evr_ticks+start/8.4+itick
                    self.evr_control.put('DG0D', evr_tick, wait=True)
                    self.phase_control.move(phase_control_steps, relative=True, confirm_move=True)
                    self.sequencer.repeat(step_events, wait=True)
                    self.phase_control.stop()
                    acqiris_bin = self.acqiris.data.argmax()
                    time_current = time.time()
                    total_events += step_events
                    print '{:10.4} {:10.4} {:10} {:10.4} {:>10} {:10.5}  {:10}'.format( \
                            time_current-self._time0, \
                            time_current-time_last, \
                            float(evr_tick*8.4), \
                            float(self.evr_ns_delay.value) - evr_ns_time0, \
                            str(step_events), \
                            float(acqiris_bin), \
                            self.time_status)
                    time_last = time.time()

                print '-'*80
                print '{:g} Total Events acquired in {:g} sec'.format( \
                        total_events, time.time()-self._time0)
                repeat -=1

        except KeyboardInterrupt:
            pass

#    def scan_delay(self, start, stop, step, sleep=0.002, deadband=None):
#        if not deadband:
#            deadband = step*0.05
#
#        self.time_delay.put('VAL', start, wait=True)
#        time.sleep(sleep)
#        self._time0 = time.time()
#        time_last = time.time()
#        self._time_target0 = self.time_target.value
#        for val in arange(start, stop, step):
#            self.acqiris.ami_clear()
#            fs_tgt_time = self.time_zero.value + val
#            self.time_target.put('VAL', fs_tgt_time)
##            while self.time_status.value != 'Laser OK':
##                time.sleep(sleep)
#            
#            while self.phase_control.DMOV:
#                time.sleep(sleep)
#            print 'DMOV', time.time()-time_last,self.phase_control.RBV
#
#            while abs(self.time_target.value-fs_tgt_time) > deadband:
#                time.sleep(sleep)
#
#            while not self.phase_control.DMOV:
#                time.sleep(sleep)
#            print 'moved', time.time()-time_last,self.phase_control.RBV
#                                
#            acqiris_bin = self.acqiris.data.argmax()
#            time_current = time.time()
#            print '{:10.4} {:10.4} {:10.4} {:10.4} {:10.5} {:10.5} {:10}'.format( \
#                    time_current-self._time0, \
#                    time_current-time_last, \
#                    float(self.time_delay.value), \
#                    float(self.time_target.value), \
#                    float(acqiris_bin), \
#                    abs(self.time_target.value-fs_tgt_time),
##                    float(self.time_target.value-self._time_target0), \
#                    self.time_status)
#            time_last = time_current



