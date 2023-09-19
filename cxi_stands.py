import psdata
import os
import time
import psmessage

from pylab import *

class cxi_stands(psdata.Detector):
    """Beamline PIM (Pop-in Monitor)  Detector Class of psdata.Detector.
    """

#    _stands = ['standDG2', 'stand1MS', 'standDG3', 'standDG4']

    _stand_detectors = {
#         'stand1MS': {
#                      'Ax': {'kb1': 84.3998, 'kb2': 64.18,    'pv': 'CXI:1MS:MMS:04'},
#                      'Ay': {'kb1': 81.5299, 'kb2': 55.2699,  'pv': 'CXI:1MS:MMS:05'},
##                      'Az': {'kb1': 9.3998,  'kb2': 9.39978,  'pv': 'CXI:1MS:MMS:06'},
#                      'By': {'kb1': 52.281,  'kb2': 31.4952,  'pv': 'CXI:1MS:MMS:01'},
#                      'Cx': {'kb1': 54.9002, 'kb2': 37.3503,  'pv': 'CXI:1MS:MMS:02'},
#                      'Cy': {'kb1': 52.3008, 'kb2': 31.415,   'pv': 'CXI:1MS:MMS:03'},
#                     },
         'standDG2': {
                      'Ax': {'kb1': 36.0798, 'kb2': 20.33,    'pv': 'CXI:DG2:MMS:14'},
                      'Ay': {'kb1': 34.41,   'kb2': 16.58,    'pv': 'CXI:DG2:MMS:15'},
#                      'Az': {'kb1': 0.2002,  'kb2': 0.20021,  'pv': 'CXI:DG2:MMS:16'},
                      'By': {'kb1': 39.88,   'kb2': 21.018,   'pv': 'CXI:DG2:MMS:11'},
                      'Cx': {'kb1': 41.8487, 'kb2': 25.662,   'pv': 'CXI:DG2:MMS:12'},
                      'Cy': {'kb1': 39.9501, 'kb2': 20.988,   'pv': 'CXI:DG2:MMS:13'},
                     },
#         'standDG3': {
#                      'Ax': {'kb1': 90.7329, 'kb2': 70.0217,  'pv': 'CXI:DG3:MMS:09'},
#                      'Ay': {'kb1': 88.406,  'kb2': 60.16,    'pv': 'CXI:DG3:MMS:10'},
##                      'Az': {'kb1': -0.0034, 'kb2': -0.00323, 'pv': 'CXI:DG3:MMS:11'},
#                      'By': {'kb1': 91.088,  'kb2': 61.9193,  'pv': 'CXI:DG3:MMS:06'},
#                      'Cx': {'kb1': 91.8417, 'kb2': 70.53,    'pv': 'CXI:DG3:MMS:07'},
#                      'Cy': {'kb1': 95.2873, 'kb2': 65.8574,  'pv': 'CXI:DG3:MMS:08'},
#                     },
#         'standDG4': {
#                      'Ax': {'kb1': 107.911, 'kb2': 85.4314,  'pv': 'CXI:DG4:MMS:09'},
#                      'Ay': {'kb1': 107.333, 'kb2': 76.101,   'pv': 'CXI:DG4:MMS:10'},
##                      'Az': {'kb1': 3.033,   'kb2': 3.03418,  'pv': 'CXI:DG4:MMS:11'},
#                      'By': {'kb1': 112.969, 'kb2': 80.77,    'pv': 'CXI:DG4:MMS:06'},
#                      'Cx': {'kb1': 113.263, 'kb2': 90.2427,  'pv': 'CXI:DG4:MMS:07'},
#                      'Cy': {'kb1': 112.63,  'kb2': 80.35,    'pv': 'CXI:DG4:MMS:08'},
#                     },
          }


    def __init__(self,*args,**kwargs):

        psdata.Detector.__init__(self,*args,**kwargs)

        pv_dict = {}
        for stand, item in self._stand_detectors.items():
            pv_dict.update({stand+'_'+attr: vals['pv'] for attr, vals in item.items()})
#            self.epicsLive.add_device(**pv_dict)
            self.add_device(**pv_dict)
        
        self.set_parameter(_init=False)

    def init_move(self, start='kb1', end='kb2', nsteps=20, step_time=5.):
        """Initialize beamline move.
        """
        self.set_parameter(istep=0)
        self.set_parameter(nsteps=nsteps)
        self.set_parameter(step_time=step_time)
        
        self.set_parameter(_move_error=True)
        self.set_parameter(_move_ready=False)

        tweek_dict = {}
        step_dict = {}
        self.enable_all()

        for stand, items in self._stand_detectors.items():
            for attr, vals in items.items():
                pv = vals['pv']
                attr = '_'.join([stand,attr])
                if end == 'straight':
                    end_pos = 0.
                else:
                    end_pos = vals[end]
                
                mot = self.epicsLive.get_device(attr)
                if start == 'current':
                    start_pos = mot.get_position()
                else:
                    start_pos = vals[start]
                
                tweek_val = (end_pos-start_pos)/float(self.nsteps)
                velocity = abs(tweek_val)/self.step_time 
                tweek_dict[attr] = tweek_val
                step_dict[attr] = start_pos + arange(nsteps+1)*tweek_val
        
        self.set_parameter(scan_step=tweek_dict)
        self.set_parameter(scan_array=step_dict)

        title = 'Move Beamline from {:} to {:} Beam Axis'.format(start.upper(),end.upper())
        self.message = psmessage.message(title)
        self.message.add(time.ctime())
        self.message.add('-'*80)
        self.message.add(' - Number of steps:         {:}'.format(self.nsteps))
        self.message.add(' - Time to make step:       {:} sec'.format(self.step_time))
        self.message.add('-'*80)

        status = self.confirm_move()
        self.message.add('-'*80)
        if not status:
            self.message.add('*** WARNING:  Motors not in a valid position to move ***')
            self.set_parameter(_init=False)
            self.set_parameter(_move_error=True)
        else:
            self.message.add('Motors are all in valid start positions to move.')
            self.set_parameter(_init=True)
            self.set_parameter(_move_error=False)
        
        self.message.add('-'*80)

    def move_beamline(self):
        """Move beamline in steps after initializing move with move_init().
        """
        if not self._init:
            print 'Initialize Move before Begininng Move'
        else:
            try:
                for i in range(self.nsteps):
                    ok_move = self.move_next_step()
                    if not ok_move:
                        self.message.add('Error in Moving -- Exiting Beamline Move')
                        return 0

                self.message.instrument_post()

            except KeyboardInterrupt:
                self.message.add('Keyboard Interrupt -- Exiting Beamline Move')
                return 0

        return 1


    def confirm_move(self, quiet=False):
        """Confirm that the 
        """
        if not self._init and not self._move_error:
            self.init_move()

        self.message.add('Currently at step {:} of {:}'.format(self.istep+1, self.nsteps), quiet=quiet)
        self.message.add('-'*80, quiet=quiet)
        self.message.add('{:15} {:15} {:>8} {:>8} {:>8} {:>8} {:>8}'.format( \
                'Name', 'PV', 'current', 'last', 'next', 'final', 'step'), quiet=quiet)
        self.message.add('-'*80, quiet=quiet)
        
        status = True
        for attr in list(sort(self.epicsLive._attrs)):
            mot = self.epicsLive.get_device(attr)
            current_pos = mot.get_position()
            desired_pos = self.scan_array[attr][self.istep]
            tweek_val = self.scan_step[attr]
            final_pos = self.scan_array[attr][-1]
            if self.istep < self.nsteps:
                next_pos = self.scan_array[attr][self.istep+1]
            else:
                next_pos = current_pos

            pv = self.epicsLive._aliases[attr]
            mes = '{:15} {:15} {:8.3f} {:8.3f} {:8.3f} {:8.3f} {:8.3f}'.format( \
                    attr, pv, current_pos, desired_pos, next_pos, final_pos, tweek_val)
            if abs(current_pos-desired_pos) > 0.1:
                mes += ' *** Not OK ***'
                status = False
                self.set_parameter(_move_error=True)
                self.set_parameter(_move_ready=False)

            self.message.add(mes, quiet=quiet)
        
        if self.istep == self.nsteps:
            self.message.add('!!! Move Complete !!!')
            self.set_parameter(_move_ready=False)

        return status

    def move_next_step(self):
        """Make next step.
        """
        if self._move_ready:
            self.confirm_move(quiet=True)
        else:
            self.setup_next_step()

        if self._move_error:
            self.message.add('*** Warning:  Move Status Error -- Fix Problem and try again ***')
        elif self._move_ready:
            ok_setup = self.setup_next_step()
            self.istep += 1
            pos_dict = {attr: pos[self.istep] for attr, pos in self.scan_array.items()} 
            self.set_parameter(_move_ready=False)
            if ok_setup:
                self.message.add('Moving step {:} of {:}'.format(self.istep, self.nsteps))
                ok_move = self.epicsLive.move(wait=True, **pos_dict)
                if not ok_move:
                    print 'Bad move on step', self.istep
                return ok_move
            else:
                self.message.add('Aborted Move')
                return 0
        elif self.istep < self.nsteps:
            print 
        elif self.istep == self.nsteps:
            print 'Move complete'
            return 0

    def position_dict(self, istep=None):
        """Return dictionary of positions for given step.
        """
        if not istep:
            istep = self.istep

        return {attr: vals[istep] for attr, vals in self.scan_array.items()}

    def setup_next_step(self, istep=None):
        """Setup next step in move.
        """
        if not self._init:
            print '*** Need to init_move before beginning ***'
            return 0
            
        if not istep:
            istep = self.istep+1

        if istep > self.nsteps:
            print 'Move Completed'
            return 0
        else:
            ok_limits = True
            current_vals = self.epicsLive.get_all('VAL')
            desired_vals = self.position_dict
            for attr in self.epicsLive._attrs:
                mot = self.epicsLive.get_device(attr)
                desired_pos = self.scan_array[attr][istep]
                tweek_val = self.scan_step[attr]
                current_pos = mot.get_position()
                mot.put('TWV', abs(tweek_val), wait=True)
                mot.put('VELO', abs(tweek_val)/self.step_time, wait=True)
                if desired_pos > current_pos:
                    mot.put('HLM', desired_pos+0.1, wait=True)
                    mot.put('LLM', current_pos-0.01, wait=True)
                else:
                    mot.put('HLM', current_pos+0.01, wait=True)
                    mot.put('LLM', desired_pos-0.1, wait=True)
                
                time.sleep(0.2)
                # Make sure next step is within the soft limits 
                ok_limits = ok_limits and mot.within_limits(current_pos+tweek_val) 
                if not ok_limits:
                    print attr, current_pos, desired_pos, desired_pos-current_pos, tweek_val
                    print attr, mot.get('HLM'), mot.get('LLM'), current_pos+tweek_val
                    print attr, 'step not valid'
                
                # Make sure motor is not at the lower limit switch.
                if mot.get('LLS'):
                    print attr, 'is at the lower limit switch!!!'
                    print attr, 'step not valid'
                    ok_limits = 0 

                # Make sure motor is not at the upper limit switch.
                if mot.get('HLS'):
                    print attr, 'is at the upper limit switch!!!'
                    print attr, 'step not valid'
                    ok_limits = 0
                   
            if not ok_limits:
                self.epicsLive.disable_all()
                self.set_parameter(_move_ready=False)
            else:
                self.set_parameter(_move_ready=True)

            return ok_limits


    def disable_all(self):
        """Disable all ims motors.
        """
        self.epicsLive.disable_all()

    def enable_all(self):
        """Enable all ims motors.
        """
        self.epicsLive.enable_all()

    def stop(self):
        """Stop all ims motors.
        """
        self.epicsLive.stop()

    def clear_errors(self):
        """Clear all errors of epics ims motors.
        """
        self.epicsLive.clear_errors()

#    def show_ims(self):
#        for standname in self._stands:
#            getattr(self, standname).show_info()
# 
#    def load_stand_scan_array(self, file_name=None,file_dir=None,to_kb1=False,to_kb2=False, **kwargs):
#        if not file_dir:
#            file_dir = '/reg/g/pcds/package/epics/3.14-dev/screens/edm/cxi/current/stand_motion/'
#
#        if not file_name:
#            if to_kb1:
#                file_name = 'KB2toKB1_StandPositions_DG2extraZgap.txt'
#            elif to_kb2:
#                file_name = 'KB1toKB2_StandPositions_DG2extraZgap.txt'
#            else:
#                file_name = 'KB1toKB2_StandPositions_DG2extraZgap.txt'
#
#        print file_dir
#        print file_name
#        with open(file_dir+'/'+file_name) as f:
#            motlist = f.read().split('\n')
#
#        print file_dir+'/'+file_name
#        stand_scan_array = {}
#        for mot in motlist:
#            if mot:
#                attrs = mot.split()
#                if attrs and attrs[0] and not attrs[0].startswith('#'):
#                    stand_scan_array[attrs[0]] = {'start': float(attrs[1]), 'end': float(attrs[2])}
#        
#        self.stand_scan_array = stand_scan_array
   #
    ##stand_scan_array = load_stand_scan_array(to_kb1=True)
    #
    ##show_ims(cxi)
    #
    #def show_pos(self,stand_scan_array):
    #    for pv,pos in stand_scan_array.items():
    #        epv = self._data._epics_devices[pv]
    #        print '{:} {:8.3f} -- {:10.3f} < {:10.3f} < {:10.3f}'.format(pv, \
    #               (epv.RBV-pos['start'])/(pos['end']-pos['start'])*20,epv.LLM, epv.RBV,epv.HLM)
    #

    #def set_limits(self

#d = {}
#for alias, item in cxi.stands._stand_detectors.items():
#    d[alias] = {}
#    for attr, pv in item.items():
#        d[alias][attr] = {'pv': pv, 'kb1': cxi.stands.stand_scan_array[pv]['start'], 'kb2': cxi.stands.stand_scan_array[pv]['end']}
#
