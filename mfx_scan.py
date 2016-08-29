import psdata
import epics
import time
import psutils 
import psmessage

from pylab import *

class Mfx_scan(psdata.Detector):
    """LCLS Laser Control Detector Class of psdata.Detector.
       see also /reg/g/pcds/pyps/xpp/head/xpp/linac.py
    """

    def __init__(self,  *args,**kwargs):

        psdata.Detector.__init__(self, *args,**kwargs)

#        epics_devices = {
#                'x': 'CXI:SC2:MMS:02',
#                'y': 'CXI:SC2:MMS:03', 
#                'z': 'CXI:SC2:MMS:04', 
#                }
#        self.epicsLive.add_device(**epics_devices)

#        self.include_detector('sequencer', module='sequencer')
#        self.set_parameter(pedestal=0.)
        self.include_detector('burst', module='burst')

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

    def init_scan(self, **kwargs):
        return 1

    def scan(self, x=[], y=[], z=[], 
                   xerr = 0.011,
                   yerr = 0.011,
                   zerr = 0.011,
                   title='Scan:',
                   daq=False,
                   burst=False,
                   record=False,
                   simulate=False,
                   nshots=1, post=False, **kwargs):
        """Scan motors and perform analysis.
            x = vector of X motor positions
            y = vector of Y motor positions
            z = vector of Z motor positions
            nshots = number of shots per position
            post = post in experiment elog if True 
                   (message can still be accessed afterwards in self.message)
        """
        run_number = self.run_number
        if run_number == 0 or run_number > 10000:
            run_str = 'NOT RECORDED'
#            if raw_input('This run is not being recorded.  Continue Anyway (y/n)?') != 'y':
#                return 0

        else:
            run_str = 'Run Number:  {:}'.format(run_number)

        if xerr < 0.001:
            fxs = '{:>10} '
            fxv = '{:10.6f} '
        else:
            fxs = '{:>7} '
            fxv = '{:7.3f} '

        if yerr < 0.001:
            fys = '{:>10} '
            fyv = '{:10.6f} '
        else:
            fys = '{:>7} '
            fyv = '{:7.3f} '

        if zerr < 0.001:
            fzs = '{:>10} '
            fzv = '{:10.6f} '
        else:
            fzs = '{:>7} '
            fzv = '{:7.3f} '

        self.init_scan(**kwargs)
        self.message = psmessage.message(title) 
        xarray = list(x)
        yarray = list(y)
        zarray = list(z)
        nx = len(xarray)
        ny = len(yarray)
        nz = len(zarray)
        scan_steps = max([nx,ny,nz])

        self.message.add(' - '+run_str)        
        self.message.add(' - Start Time:  '+time.ctime())
        self.message.add(' - Number of scan steps:      {:}'.format(scan_steps))
        self.message.add(' - Number of x steps:         {:}'.format(nx))
        self.message.add(' - Number of y steps:         {:}'.format(ny)) 
        self.message.add(' - Number of z steps:         {:}'.format(nz)) 
        self.message.add(' - Number of shots per step:  {:}'.format(nshots))

        scan_dict = {}
        
        abbort = False
        if not nx and not ny and not nz:
            self.message.add('INPUT ERROR -- Must provide vector of scan positions for x and/or y and/or z motors.')
            self.message.add(self.scan.__doc__)
            return

        else:
            if nx == scan_steps:
                self.message.add(' - Scanning X-axis')
                scan_dict.update({'x': xarray}) 
            elif nx > 1:
                abbort = True
            
            if ny == scan_steps:
                self.message.add(' - Scanning X-axis')
                scan_dict.update({'y': yarray}) 
            elif ny > 1:
                abbort = True
            
            if nz == scan_steps:
                self.message.add(' - Scanning Z-axis')
                scan_dict.update({'z': zarray}) 
            elif nz > 1:
                abbort = True

        if abbort:
            self.message.add('INPUT ERROR --  x and y and z vectors must be the same length or a single value')
            return 0


        if not self.epicsLive.within_limits(**scan_dict):
            self.message.add('SOFT LIMIT ERROR -- check scan values and try again.')
            return 0

        if burst:
            self.burst.stop_burst()
            time.sleep(1.)

        if daq:
            controls = [ (getattr(self, attr).NAME, getattr(self, attr).VAL) for attr in scan_dict ]
            self.daq.configure(record=record, controls=controls)
            time.sleep(1.)

        self.message.add('') 
        fheader = '{:>5} {:>8} {:>8} '+fxs+fys+fzs+fxs+fys+fzs+'{:>8}  {:>10}  {:10}'
        self.message.add(fheader.format( \
            'step', 'time', 'tstep', 'Xpos', 'Ypos', 'Zpos', 'dXpos', 'dYpos', 'dZpos', 'shots', 'ana', 'status'))
        self.message.add('-'*100)

        time0 = time_last = time.time()

        axval_start = []
        ayval_start = []
        azval_start = []
        axval_end = []
        ayval_end = []
        azval_end = []
        try:
            for istep in range(scan_steps):
                ana_status = 'OK'
                pos_dict ={alias: val[istep] for alias,val in scan_dict.items()}
                if not simulate:
                    ok_move = self.epicsLive.move(wait=True, **pos_dict)
                    if not ok_move:
                        self.message.add('Invalid Move Attepted -- exiting scan script')
                        return 0

                    if 'x' in pos_dict:
                        while abs(self.x.RBV-pos_dict['x']) > xerr or not ok_move:
                            if self.x.RTYP == 'ims':
                                self.x.clear_errors()
                                time.sleep(0.2)
                                self.x.update_status()
                                time.sleep(0.2)
                                ok_move = self.epicsLive.move(wait=True, x=pos_dict['x']-xerr*3)
                            
                            ok_move = self.epicsLive.move(wait=True, x=pos_dict['x'])
                            ana_status = 'Retry X Move'

                    if 'y' in pos_dict:
                        while abs(self.y.RBV-pos_dict['y']) > yerr or not ok_move:
                            if self.x.RTYP == 'ims':
                                self.y.clear_errors()
                                time.sleep(0.2)
                                self.y.update_status()
                                time.sleep(0.2)
                                ok_move = self.epicsLive.move(wait=True, y=pos_dict['y']-yerr*3)
                            
                            ok_move = self.epicsLive.move(wait=True, y=pos_dict['y'])
                            if ana_status == 'OK':
                                ana_status = 'Retry Y Move'
                            elif ana_status == 'Retry X Move':
                                ana_status = 'Retry X and Y Move'
     
                    if 'z' in pos_dict:
                        while abs(self.z.RBV-pos_dict['z']) > zerr or not ok_move:
                            if self.x.RTYP == 'ims':
                                self.z.clear_errors()
                                time.sleep(0.2)
                                self.z.update_status()
                                time.sleep(0.2)
                                ok_move = self.epicsLive.move(wait=True, z=pos_dict['z']-zerr*3)
                            
                            ok_move = self.epicsLive.move(wait=True, z=pos_dict['z'])
                            if ana_status == 'OK':
                                ana_status = 'Retry Z Move'
                            elif ana_status == 'Retry X Move':
                                ana_status = 'Retry X and Z Move'
                            elif ana_status == 'Retry Y Move':
                                ana_status = 'Retry Y and Z Move'
                            elif ana_status == 'Retry X and Y Move':
                                ana_status = 'Retry X, Y and Z Move'
                    xval = self.x.RBV
                    yval = self.y.RBV
                    zval = self.z.RBV
                
                else:        
                    xval= pos_dict.get('x', self.x.RBV)
                    yval= pos_dict.get('y', self.y.RBV)
                    zval= pos_dict.get('z', self.z.RBV)

                time_current = time.time()

                axval_start.append(xval)
                ayval_start.append(yval)
                azval_start.append(zval)
                
                controls = [ (getattr(self, attr).NAME, getattr(self, attr).VAL) for attr in pos_dict ]
                if daq:
                    self.daq.begin(events=nshots, controls=controls, quiet=True)
                    time.sleep(0.1)

                if burst:
                    self.burst.start_burst(events=nshots)

                if daq:
                    self.daq.end(quiet=True)

                #self.do_shots(nshots)
                #self.sequencer.repeat(nseq, wait=True)
                time_current = time.time()
                message_format = '{:5} {:8.3f} {:8.3f} '+fxv+fyv+fzv+fxv+fyv+fzv+'{:>8}  {:10.5g}  {:10}'
                self.message.add(message_format.format( \
                            istep, \
                            time_current-time0, \
                            time_current-time_last, \
                            xval, \
                            yval, \
                            zval, \
                            xval-pos_dict.get('x',xval), \
                            yval-pos_dict.get('y',yval), \
                            zval-pos_dict.get('z',zval), \
                            nshots, \
                            #self.sequencer.total_count.VAL, \
                            float(self.ana_result), \
                            ana_status))
                
                xval = self.x.RBV
                yval = self.y.RBV
                zval = self.z.RBV
                axval_end.append(xval)
                ayval_end.append(yval)
                azval_end.append(zval)
                time_last = time.time()
            
            self.set_parameter(axval_start=np.array(axval_start),
                               ayval_start=np.array(ayval_start),
                               azval_start=np.array(azval_start))
            self.set_parameter(axval_end=np.array(axval_end),
                               ayval_end=np.array(ayval_end),
                               azval_end=np.array(azval_end))
            return_status = 1

        except KeyboardInterrupt:
            self.epicsLive.stop()
            self.message.add(' Entered from Keyboard')
            self.message.add('>'*80)
            self.message.add('Scan Aborted')
            return_status = 0

        self.message.add('-'*100)
        self.message.add(' - End Time:  '+time.ctime())
        self.message.add('-'*100)
        if not post:
            if raw_input('Post Message to experiment elog (y/n)?') == 'y':
                post = True
        if post:
            self.message.post(self._data.exp)
        
        #if daq:
        #    self.daq.end_run()

        return return_status

