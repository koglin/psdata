import psdata
import epics
import time
import psutils 
import psmessage
import csv

from pylab import *


class Step_fly(psdata.Detector):
    """cxi02116 IH Liang Detector Class of psdata.Detector.
    """

    def __init__(self,  *args,**kwargs):

        psdata.Detector.__init__(self, *args,**kwargs)

        self.include_detector('burst', module='burst')
        self.include_detector('sequencer', module='sequencer')
        self.include_detector('picker', module='pulsepicker')
        if self.daq is None:
            self._data.load_daq()

    # needs work
    def freerun(self, rate=30, events=40000, **kwargs):
        if rate == 30:
            self.sequencer.seq_length.VAL = 2
        elif rate == 120:
            self.sequencer.seq_length.VAL = 5
        else:
            print 'rate must be 30 or 120'
            return

        self.daq.begin(events=events, **kwargs)
        self.sequencer.repeat(-1)

    def step_fly(self, 
                   title=None,
                   daq=False,
#                   cycle=None,
                   burst=False,  # do not use
                   sequence=False,
                   picker=False,
                   record=False,
                   post=None,
#                   simulate=False,
#                   relative=True,
#                   reset=True,
#                   xstart=None,
#                   ystart=None,
#                   zstart=None,
                   accwait=0.1, # time to wait for x motor to accelerate
                   shoot_wait=0.1, # extra time to shoot wait on top of 2*accwait
                   xspeed=1.5,    # mm/sec width speed
                   trange=1,   # target range in mm
                   tangle=0.,  # target angle (z w.r.t. x)
                   ynumsteps=1,
                   ystepsize=0.05,
                   mon_rate=30,
                   shoot_rate=30,
                   **kwargs):
 
        if not title:
            title = '{:} Line Scan'.format(self._name) 
       
        self.message = psmessage.message(title, exp=self._data.exp) 
        self.message.add('-'*100)
        self.message.add(' - Start Time:  '+time.ctime())
        self.message.add('-'*100)

        theta=tangle*pi/180.

        self.x.VELO = abs(xspeed)

        move_attrs = ['x']
        delta_dict = {'x': trange}
        self.message.add(' - sample x speed = {:} mm/s'.format(xspeed))
        if tangle:
            move_attrs.append('z')
            zdist = trange*tan(theta)
            zspeed = xspeed*tan(theta)
            delta_dict.update({'z': zdist})
            self.z.VELO = abs(zspeed)
            self.message.add(' - sample z speed = {:} mm/s'.format(zspeed))
        
        apos_dict = {}
        bpos_dict = {}
        for attr in move_attrs:
            apos_dict.update({attr: getattr(self, attr).RBV})
            bpos_dict.update({attr: apos_dict[attr]+delta_dict[attr]})

        if not self.epicsLive.within_limits(**apos_dict):
            self.message.add('SOFT LIMIT ERROR -- check scan values and try again.')
            return 0

        if not self.epicsLive.within_limits(**bpos_dict):
            self.message.add('SOFT LIMIT ERROR -- check scan values and try again.')
            return 0

        if not self.epicsLive.within_limits(y=self.y.RBV+ynumsteps*ystepsize):
            self.message.add('SOFT LIMIT ERROR -- check scan y step parameters and try again.')
            return 0

        scan_attrs = move_attrs
        scan_attrs.append('y')

        tshots = abs(trange/xspeed)-2*accwait-shoot_wait
        nshots = int(shoot_rate*tshots)
        
        header_format = {}
        value_format = {}
        for attr in scan_attrs:
            header_format[attr] = '{:>10} '
            value_format[attr] = '{:10.3f} '
       
        self.save_positions('scan_start_positions')
        time.sleep(0.2)

        if sequence:
            self.sequencer.stop()
            self.sequencer.set_sync('30Hz')
            time.sleep(0.2)
            self.make_sequence(1, burst=burst, picker=picker, 
                    mon_rate=mon_rate, shoot_rate=shoot_rate)
        elif burst:
            self.burst.stop_burst()
            time.sleep(1.)

        if daq:
            # Make sure daq run is ended and daq is connected
            try:
                self.daq.stop()
                self.daq.end_run()
            except:
                self.daq.connect()

            time.sleep(0.5)
            controls = [ (getattr(self, attr).NAME, getattr(self, attr).RBV) for attr in scan_attrs ]
            self.daq.configure(record=record, controls=controls)
            time.sleep(1.)
            daq_events = ynumsteps*nshots*1.1

            self.daq.begin(events=int(daq_events))
            time.sleep(0.1)
            
            run_number = self.run_number
            if run_number == 0 or run_number > 10000:
                run_str = 'NOT RECORDED'
                run_number = None

            else:
                run_str = 'Run Number:  {:}'.format(run_number)
           
            self.message.add(' - '+run_str)        

        self.message.add('') 
        fheader = '{:>5} {:>8} {:>8} {:>8}'
        sheader = ['step', 'time', 'tstep', 'tmove']
        for attr in move_attrs:
            sheader.append(attr)
            fheader += header_format[attr]

        fheader += '{:>8}'
        sheader.append('shots')

        self.message.add('') 
        self.message.add(fheader.format(*sheader))
        self.message.add('-'*100)

        time0 = time_last = time.time()
        #print 'Starting scan' 
        try:
            for istep in range(ynumsteps):
                if istep % 2 == 0:
                    # Move from apos to bpos on even steps
                    move_dict = bpos_dict
                else:
                    # Move from bpos to apos on odd steps
                    move_dict = apos_dict

                # Step the y position after first step
                if istep != 0:
                    self.y.move(ystepsize, relative=True, wait=True)

                # Start moving x (and z if at angle)
                #print 'Moving', move_dict 
                self.epicsLive.move(**move_dict)
                tmove0 = time.time()

                # Wait for acceleration to start shooting
                time.sleep(accwait)

                #print 'Start shooting'
                # Start shooting
                if sequence:
                    self.sequencer.repeat(nshots)
                elif burst:
                    self.burst.start_burst(events=nshots)
                    time.sleep(0.1)

                #print 'Wait for done move'
                time.sleep(0.1)
                # Wait until X motor is done moving
                while not self.x.done_moving:
                    time.sleep(0.1)

                tmove = time.time()-tmove0

                self.sequencer.stop()
                #print 'Done move'
             
                # Write out message
                time_current = time.time()
                message_format = '{:5} {:8.3f} {:8.3f} {:8.3f} '
                vals = [istep, time_current-time0, time_current-time_last, tmove]
                pos_dict = self.epicsLive.get_all('RBV')
                for attr in scan_attrs:
                    vals.append(pos_dict[attr])
                    message_format += value_format[attr]
                
                message_format += '{:>8}'
                vals.append(nshots)
                
                self.message.add(message_format.format(*vals))
                time_last = time.time()

        except KeyboardInterrupt:
            self.epicsLive.stop()
            self.message.add(' Entered from Keyboard')
            self.message.add('>'*80)
            self.message.add('Scan Aborted')
            return_status = 0

        if daq:
            self.message.add(' - {:} shots in scan'.format(self.daq.eventnum))
        
        self.message.add('-'*100)
        self.message.add(' - End Time:  '+time.ctime())
        self.message.add('-'*100)
        self.message.add('') 
        self.message.add(self.epicsLive.epics_table())

        if post is None and not simulate:
            if raw_input('Post Message to experiment elog (y/n)?') == 'y':
                post = True
        if post:
            time.sleep(0.5)
            self.message.post(name=self._data.exp, run_num=run_number, tag=title)
 
#        if daq:
#            self.daq.stop_run()
#            time.sleep(1.0)
#            self.daq.begin(events=40000)
#            self.sequencer.seq_length.VAL = 2
#            self.sequencer.repeat(-1)
#
#        if reset:
#            self.goto_position('scan_start_positions', wait=True)
#


    def read_scan_csv(self, infile, init=True):
        """Read csv file with pv names and aliases as first two lines in header 
           followed by table of positions.
        """
        with open(infile, 'rb') as f:
            reader = csv.reader(f)

        # Read headers    
            pvs = reader.next()
            aliases = reader.next()
            apos = []
            for row in reader:
                apos.append(row)

        if init:
            self.add_device(**dict(zip(aliases, pvs)))
        
        apos = np.array(apos)
        return {alias: {'pv': pvs[i], 'positions': np.array([float(b) for b in apos[:,i]])} \
                for i, alias in enumerate(aliases)}

    def save_positions(self, name='default'):
        apos = self._save_positions
        if not apos:
            apos = {}

        apos.update({name: self.epicsLive.get_all('RBV')})
        self.set_parameter(_save_positions=apos)

    def goto_position(self, name=None, wait=True):
        apos = self._save_positions.get(name)
        if apos:
            self.epicsLive.move(wait=wait, **apos)

    @property
    def daq(self):
        return self._data.daq

    @property
    def run_number(self):
        try:
            return self.daq.runnumber
        except:
            return 0

    @property
    def ana_result(self):
        return 0

    def do_shots(self, nshots=0):
        return 1

    def make_sequence(self, nevents=1, burst=False, picker=False,
            shoot_code=187, mon_code=181, mon_rate=30, shoot_rate=120, picker_code=185):
        """Helper function to set sequencer for shoot and monitor.
        """
        eventCodes = []
        beam = []
        burst_list = []
        if picker:
            delta_beam = 1
            if shoot_rate == 120:
                self.picker.follower_mode()
                eventCodes.append(picker_code)
                beam.append(0)
                burst_list.append(0)
            else:
                self.picker.flipflop_mode()
        else:
            delta_beam = 120/shoot_rate

        for i in range(int(nevents)):
            if picker and shoot_rate < 60:
                eventCodes.append(picker_code)
                beam.append(0)
                burst_list.append(0)

            eventCodes.append(shoot_code)
            beam.append(delta_beam)
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
                self.picker.follower_mode()
                eventCodes.append(picker_code)
                beam.append(0)
                burst_list.append(0)
 
        self.sequencer.set_sequence(eventCodes=eventCodes, beam=beam, burst=burst_list)

    def scan(self, filename=None,  
                   daq=False,
                   cycle=None,
                   burst=False,
                   sequence=False,
                   picker=False,
                   record=False,
                   simulate=False,
                   post=None,
                   relative=True,
                   reset=True,
                   nshots=1,
                   title=None,
                   mon_rate=30,
                   shoot_rate=120,
                   **position_dict):
        """Scan motors and perform analysis.
        
            Keywords:
                nshots:   Number of shots per position (default = 1)
                title:    Title of scan
                post:     Post in experiment elog if True 
                          (message can still be accessed afterwards in self.message)
                reset:    Reset positions to starting positions
                relative: Scan reletive to current positions
                simulate: Simulate the scan (do not move motors)
                daq:      Control the daq
                cycle:    Make a calibration cycle transition between each step
                sequence: Use event sequencer
                burst:    Use burst mode

        """
        if not title:
            title = '{:} Scan'.format(self._name) 

        self.message = psmessage.message(title, exp=self._data.exp) 
        self.message.add(' - Start Time:  '+time.ctime())
        
        if filename:
            self.message.add(' - Loading motor positions from '+filename)        
            file_dict = self.read_scan_csv(filename)
            position_dict = {}
            for attr, item in file_dict.items():
                position_dict[attr] = np.array(item['positions'])
#                mot = getattr(self, attr)
#                if mot.EGU == 'um':
#                    # convert from mm to um (e.g., for pp-30 piezo motors)
#                    position_dict[attr] = np.array(item['positions'])*1000.
#                else:
#                    position_dict[attr] = np.array(item['positions'])

        scan_steps = 1
        header_format = {}
        value_format = {}
        scan_dict = {}
        init_dict = {}
        orig_dict = {}
        offset_dict = {}
        pvname_dict = {}
        readback_dict = {}
        for attr, values in position_dict.items():
            mot = getattr(self, attr)
            if not mot:
                self.message.add('INPUT ERROR -- Motor {:} is not defined.'.format(attr))
                return 0

            if hasattr(mot, 'RBV'):
                readback_dict[attr] = 'RBV'
            else:
                readback_dict[attr] = 'VAL'

            pvname_dict[attr] = mot.NAME
            orig_dict[attr] = getattr(mot, readback_dict[attr])

            try:
                values = np.array(values)
            except:
                self.message.add('INPUT ERROR -- Motor {:} position values not well defined:'.format(attr))
                self.message.add('               Values = {:}'.format(values))
                return 0

            if len(values) > 1: 
                if scan_steps == 1:
                    scan_steps = len(values)
                elif len(values) != scan_steps:
                    self.message.add('INPUT ERROR -- All motors must have the same number of positions')
                    self.message.add('               or be a single initial value.')
                    return 0

                scan_dict[attr] = values
                self.message.add(' - {:4} steps for {:} {:}'.format(len(values), attr, pvname_dict[attr]))
                
                if hasattr(mot, 'retry_deadband') and mot.retry_deadband < 0.001:
                    header_format[attr] = '{:>10} '
                    value_format[attr] = '{:10.6f} '
                else:
                    header_format[attr] = '{:>10} '
                    value_format[attr] = '{:10.3f} '
           
            init_dict[attr] = values[0]
        
        if relative:
            init_dict = {attr: val+orig_dict[attr] for attr,val in init_dict.items()}
            scan_dict = {attr: val+orig_dict[attr] for attr,val in scan_dict.items()}

        self.save_positions('scan_start_positions')

        self.message.add(' - {:4} shots per step'.format(nshots))

        if not self.epicsLive.within_limits(**scan_dict):
            self.message.add('SOFT LIMIT ERROR -- check scan values and try again.')
            return 0

        if not self.epicsLive.within_limits(**init_dict):
            self.message.add('SOFT LIMIT ERROR -- check initial positions and try again.')
            return 0
        elif relative:
            self.message.add('') 
            self.message.add('Scanning relative to current positions.')
        elif simulate:
            self.message.add('') 
            self.message.add('Simulating motor move to start position.')
        else:
            self.message.add('') 
            self.message.add('Moving motors to start position.')
            time0 = time_last = time.time()
            self.epicsLive.move(wait=True, **init_dict)
            self.message.add(' - Initialiazation Time: {:8.3f} sec'.format(time.time()-time0))

        self.message.add('') 
        self.message.add(self.epicsLive.epics_table(*init_dict.keys()))

        print 'Taking shots ',nshots
        if sequence:
            self.sequencer.stop()
            time.sleep(0.2)
            self.make_sequence(nshots, burst=burst, picker=picker, 
                    mon_rate=mon_rate, shoot_rate=shoot_rate)
        elif burst:
            self.burst.stop_burst()
            time.sleep(1.)

        if daq:
            # Make sure daq run is ended and daq is connected
            try:
                self.daq.end_run()
            except:
                self.daq.connect()

            time.sleep(0.5)
            controls = [ (getattr(self, attr).NAME, getattr(self, attr).VAL) for attr in scan_dict ]
            self.daq.configure(record=record, controls=controls)
            time.sleep(1.)
        
        self.message.add('') 
        fheader = '{:>5} {:>8} {:>8} '
        sheader = ['step', 'time', 'tstep']
        for attr in scan_dict:
            sheader.append(attr)
            fheader += header_format[attr]
        for attr in scan_dict:
            sheader.append('d_'+attr)
            fheader += header_format[attr]

        fheader += '{:>8}'
        sheader.append('shots')
#        fheader += ' {:>10}  {:10}'
#        sheader.append('ana')
#        sheader.append('status')

        self.set_parameter(scan_positions=position_dict)

        time0 = time_last = time.time()

        # Make cycle default if not in burst or sequence mode for daq to get correct number of events
        if cycle is None and daq and not ( burst or sequence):
            cycle = True

        if daq and not cycle:
            if sequence:
                daq_events = self.sequencer.seq_length.VAL*scan_steps*2
            else:
                daq_events = nshots*scan_steps*1.1

            self.daq.begin(events=int(daq_events), quiet=True)

            time.sleep(0.1)
            
            run_number = self.run_number
            if run_number == 0 or run_number > 10000:
                run_str = 'NOT RECORDED'
                run_number = None

            else:
                run_str = 'Run Number:  {:}'.format(run_number)
           
            self.message.add(' - '+run_str)        

        self.message.add('') 
        self.message.add(fheader.format(*sheader))
        self.message.add('-'*100)

        try:
            for istep in range(scan_steps):
#                current_dict = {attr: getattr(getattr(self, attr), readback_dict[attr]) for attr in scan_dict}
#                ana_status = 'OK'
                move_dict ={attr: val[istep] for attr,val in scan_dict.items()}
 
                if simulate:
                    # simulate scan -- do not move motors
                    pos_dict = move_dict
                    time.sleep(0.05)
                
                else:        
                    ok_move = self.epicsLive.move(wait=True, **move_dict)
                    if not ok_move:
                        self.message.add('Invalid Move Attepted -- exiting scan script')
                        return 0

                    pos_dict = {}
                    for attr in scan_dict:
                        pos_dict[attr] = getattr(getattr(self, attr), readback_dict[attr])

                time_current = time.time()

                if daq and cycle:
                    controls = [ (pvname_dict[attr], val) for attr, val in move_dict.items() ]
                    if sequence:
                        daq_events = self.sequencer.seq_length.VAL*1.2
                        self.daq.begin(events=int(daq_events), controls=controls, quiet=True)
                    elif burst:
                        self.daq.begin(events=nshots, controls=controls, quiet=True)
                    else:
                        self.daq.begin(events=nshots, quiet=True, wait=True)

                if sequence:
                    self.sequencer.repeat(1, wait=True)
                elif burst:
                    self.burst.start_burst(events=nshots)
                    time.sleep(0.1)

                if daq and cycle:
                    self.daq.end(quiet=True, wait=True)

                #self.do_shots(nshots)
                #self.sequencer.repeat(nseq, wait=True)
                time_current = time.time()
                message_format = '{:5} {:8.3f} {:8.3f} '
                vals = [istep, time_current-time0, time_current-time_last]
                for attr in pos_dict:
                    vals.append(pos_dict[attr])
                    message_format += value_format[attr]
                for attr in pos_dict:
                    vals.append(pos_dict[attr]-move_dict[attr])
                    message_format += value_format[attr]
                        
                message_format += '{:>8}'
                vals.append(nshots)
#                message_format += ' {:10.5g}  {:10}'
#                vals.append(float(self.ana_result))
#                vals.append(ana_status)
                
                self.message.add(message_format.format(*vals))
                
                time_last = time.time()

            return_status = 1

        except KeyboardInterrupt:
            self.epicsLive.stop()
            self.message.add(' Entered from Keyboard')
            self.message.add('>'*80)
            self.message.add('Scan Aborted')
            return_status = 0

        if daq:
            self.daq.disconnect()

        self.message.add('-'*100)
        self.message.add(' - End Time:  '+time.ctime())
        self.message.add('-'*100)
        if post is None and not simulate:
            if raw_input('Post Message to experiment elog (y/n)?') == 'y':
                post = True
        if post:
            time.sleep(0.5)
            self.message.post(name=self._data.exp, run_num=run_number, tag=title)
        
        if reset:
            self.goto_position('scan_start_positions', wait=True)

        return return_status

