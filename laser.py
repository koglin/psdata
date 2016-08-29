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

        self.include_detector('burst', module='burst')
        self.include_detector('sequencer', module='sequencer')
        self.include_detector('picker', module='pulsepicker')
        
#        if not getattr(self._data, 'sequencer') \
#                or self._data.sequencer.__class__.__name__ == 'Detector':
#            self._data.add_detector('sequencer', module='sequencer')

        if getattr(self._data, 'EVR'):
            self.include_detector('EVR')

    @property
    def acqiris(self):
        return getattr(self._data.ami, 'Acqiris_{:}'.format(self._acqiris_ch))

    def show_evr(self):
        attrs = ['event_code', 'state', 'polarity', 'width_calc', 'delay_calc', 'rate']
        str_fmt = '{event_code:4}  {desc:30} {state:8} {polarity:8} {delay_calc:10} {width_calc:10} {rate:8}'
        prefix = ['laser0', 'laser1']
        info = {'event_code': 'Code', 'desc': 'Description', 'state': 'State', 'polarity': 'Polarity', 
                'width_calc': 'Width', 'delay_calc': 'Delay', 'rate': 'Rate'}
        print str_fmt.format(**info) 
        print '-'*84
        for pre in prefix:
            info = {attr: str(getattr(self.EVR, pre+'_'+attr)) for attr in attrs}
            info['desc'] = getattr(self.EVR, pre+'_state').DESC
            print str_fmt.format(**info) 


