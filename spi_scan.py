
import psdata
import epics
import time
import psutils 

from pylab import *

class spi_scan(psdata.Detector):
    """LCLS Laser Control Detector Class of psdata.Detector.
       see also /reg/g/pcds/pyps/xpp/head/xpp/linac.py
    """

    def __init__(self,  *args,**kwargs):

        psdata.Detector.__init__(self, *args,**kwargs)

#        epics_devices = {
#                'x': 'CXI:PI1:MMS:01',
#                'y': 'CXI:PI1:MMS:02', 
#                'z': 'CXI:PI1:MMS:03', 
#                }
#        self.epicsLive.add_device(**epics_devices)

        #self.include_detector('sequencer', module='sequencer')
        self.include_detector('Dg2CsPad2x2')

    def make_pedestal(self):
        self.backpad.ami_clear()
        time.sleep(5.)
        self.set_parameter(pedestal=backpad.data)

    @property
    def backpad(self):
        return self.Dg2CsPad2x2.ami

    @property
    def data_corrected(self):
        return self.backpad.data #-self.pedestal

    @property
    def data1(self):
        return np.array(self.data_corrected[0][2])

    @property
    def data2(self):
        return np.array(self.data_corrected[1][2])

    @property
    def ana_result(self):
#        ana_result = self.sequencer.total_count.VAL
        if self.Dg2CsPad2x2.ami:
            ana_result =  mean(self.data1)+mean(self.data2)
        else:
            ana_result = 0.
        
        return ana_result

    @property
    def run_number(self):
        try:
            self._data.ami.RunNumber.ami_clear()
            time.sleep(0.1)
            run_number = self._data.ami.RunNumber.mean
        except:
            run_number = 0

        return run_number

    def scan(self,  
                    nscans=1,
                    xo='current', xbin=0.005, xwidth=0.1,
                    yo='current', ybin=0.005, ywidth=0.0,
                    zo='current', zbin=0.005, zwidth=0.0,
                    tbin=2.,
                    title='SPI Injector Scan:', 
                    post=False):
        """Scan motors and perform analysis.  
            xo = initial horizontal position [default = 'current']
            yo = initial vertical position [default = 'current']
            zo = initial focus position [default = 'current']
            xwidth = horizontal scan width of scan in mm
            ywidth = vertical scan width of scan in mm
            zwidth = focus scan width of scan in mm
            xbin = horizontal 'bin' size in mm
            ybin = vertical 'bin' size in mm
            zbin = focus 'bin' size in mm
            tbin = time that motor is within the specified bins
            nscans = Number of scans [default = 1]
            title = title of scan that will go in the first line of the post
            post = post in experiment elog if True 
                   (message can still be accessed afterwards in self.message)
        """
        run_number = self.run_number
#        if run_number == 0 or run_number > 10000:
#            run_str = 'NOT RECORDED'
#            if raw_input('This run is not being recorded.  Continue Anyway (y/n)?') != 'y':
#                return 0
#
#        else:
#            run_str = 'Run Number:  {:}'.format(run_number)

        # self.init_scan(**kwargs)

        self.message = psutils.message(title)
        if xo is 'current':
            xo = self.x.get('RBV')
        
        if yo is 'current':
            yo = self.y.get('RBV')

        if zo is 'current':
            zo = self.z.get('RBV')

        xarray = []
        yarray = []
        zarray = []
        init_pos = {'x': xo, 'y': yo, 'z':zo}

        for i in range((nscans+1)/2):
            if xwidth:
                xarray.append(xo-xwidth/2.)
                xarray.append(xo+xwidth/2.)
            if ywidth:
                yarray.append(yo-ywidth/2.)
                yarray.append(yo+ywidth/2.)
            if zwidth:
                zarray.append(zo-zwidth/2.)
                zarray.append(zo+zwidth/2.)

        xarray.append(xo)
        yarray.append(yo)
        zarray.append(zo)

        nx = int(xwidth/xbin)
        ny = int(ywidth/ybin)
        nz = int(zwidth/zbin)
        nsteps = max([nx,ny,nz])
        scan_time = nsteps*tbin
        nscan_str = '{:}'.format(nscans)
        
#        self.message.add(' - '+run_str) 
        self.message.add(' - Start Time:  '+time.ctime())
        self.message.add(' - Number of scans:       {:>10}'.format(nscan_str))
        self.message.add(' - Time per bin:          {:>10} s'.format(tbin))
        self.message.add(' - Time per scan:         {:>10} s'.format(scan_time))
        self.message.add(' - Total time:            {:>10} s'.format(scan_time*nscans))

        scan_dict = {}
        if xwidth:
            xspeed = xwidth/float(nx*tbin)
            scan_dict.update({'x': xarray})
            self.message.add(' - x scan bins:           {:>10}'.format(nx))
            self.message.add(' - x scan range:          {:10.6f} mm'.format(xwidth))
            self.message.add(' - x bin size:            {:10.6f} mm'.format(xbin))
            self.message.add(' - x speed:               {:10.6f} mm/s'.format(xspeed))
            if self.x.VBAS > xspeed:
                self.x.put('VBAS', xspeed)
            self.x.put('VELO', xspeed)

        if ywidth:
            yspeed = ywidth/float(ny*tbin)
            scan_dict.update({'y': yarray})
            self.message.add(' - y scan bins:           {:>10}'.format(ny))
            self.message.add(' - y scan range:          {:10.6f} mm'.format(ywidth))
            self.message.add(' - y bin size:            {:10.6f} mm'.format(ybin))
            self.message.add(' - y speed:               {:10.6f} mm/s'.format(yspeed))
            if self.y.VBAS > yspeed:
                self.y.put('VBAS', yspeed)
            self.y.put('VELO', yspeed)
        
        if zwidth:
            zspeed = zwidth/float(nz*tbin)
            scan_dict.update({'z': zarray})
            self.message.add(' - z scan bins:           {:>10}'.format(nz))
            self.message.add(' - z scan range:          {:10.6f} mm'.format(zwidth))
            self.message.add(' - z bin size:            {:10.6f} mm'.format(zbin))
            self.message.add(' - z speed:               {:10.6f} mm/s'.format(zspeed))
            if self.z.VBAS > zspeed:
                self.z.put('VBAS', zspeed)
            self.z.put('VELO', zspeed)
       
        if nx > 1 and nx != nsteps:
            print 'Bad X scan parameters'
        
        if ny > 1 and ny != nsteps:
            print 'Bad Y scan parameters'
            
        if nz > 1 and nz != nsteps:
            print 'Bad Z scan parameters'
        
        print scan_dict

        self.set_parameter(xvals=xarray)
        self.set_parameter(yvals=yarray)
        self.set_parameter(zvals=zarray)

        if not self.epicsLive.within_limits(**scan_dict):
            self.message.add('SOFT LIMIT ERROR -- check scan values and try again.')
            return 0

        if raw_input('Do you want to execute this scan (y/n)?') != 'y':
            return 0
            
        ok_move = self.epicsLive.move(wait=True, **init_pos)
        if not ok_move:
            self.message.add('Motors did not reach start position. -- Aborting Scan.')
            return 0

        self.message.add('') 
        self.message.add('{:>5} {:>8} {:>8} {:>10} {:>10} {:>10} {:>8}  {:10}'.format( \
            'step', 'time', 'tstep', 'Xpos', 'Ypos', 'Zpos', 'ana', 'status'))
        self.message.add('-'*100)

        time0 = time_last = time.time()

        try:
            for iscan in range(nscans+2):
                ana_status = 'OK'
                pos_dict ={alias: val[iscan] for alias,val in scan_dict.items()}
                ok_move = self.epicsLive.move(use_complete=True, **pos_dict)
                tscan0 = time.time()
                if iscan == 0 or iscan == nscans+1:
                    nscansteps = nsteps/2
                else:
                    nscansteps = nsteps

                for istep in range(nscansteps):
                    self.backpad.ami_clear()
                    while time.time()-tscan0 < (istep+1)*tbin:
                        time.sleep(0.05)

                    xval = self.x.RBV
                    yval = self.y.RBV
                    zval = self.z.RBV
                    time_current = time.time()
                    self.message.add('{:5} {:8.3f} {:8.3f} {:10.6f} {:10.6f} {:10.6f} {:>8}  {:10}'.format( \
                                istep, \
                                time_current-time0, \
                                time_current-time_last, \
                                xval, \
                                yval, \
                                zval, \
                                float(self.ana_result), \
                                ana_status))
                   
                    time_last = time.time()
                
            return_status = 1

        except KeyboardInterrupt:
            self.epicsLive.stop()
            self.message.add(' Entered from Keyboard')
            self.message.add('>'*80)
            self.message.add('Scan Aborted')
            if raw_input('Do you want to move motors back to original position (y/n)?') != 'y':
                ok_move = self.epicsLive.move(wait=True, **init_pos)
            return_status = 0

        self.message.add('-'*100)
        self.message.add(' - End Time:  '+time.ctime())
        self.message.add('-'*100)
        if not post:
            if raw_input('Post Message to experiment elog (y/n)?') == 'y':
                post = True
        if post:
            self.message.post()
        
        return return_status


#    def scan_seq(self, x=[], z=[], 
#                   title='SPI Injector Scan:', 
#                   shots_per_step=40, post=False, **kwargs):
#        """Scan motors and perform analysis.
#            x = vector of X motor positions
#            Z = vector of Z motor positions
#            shots_per_step = number of shots per position (using sequencer)
#            post = post in experiment elog if True 
#                   (message can still be accessed afterwards in self.message)
#        """
#        run_number = self.run_number
#        if run_number == 0 or run_number > 10000:
#            run_str = 'NOT RECORDED'
#            if raw_input('This run is not being recorded.  Continue Anyway (y/n)?') != 'y':
#                return 0
#
#        else:
#            run_str = 'Run Number:  {:}'.format(run_number)
#
#        self.init_scan(**kwargs)
#        self.message = psutils.message(title) 
#        xarray = list(x)
#        zarray = list(z)
#        nx = len(xarray)
#        nz = len(zarray)
#        scan_steps = max([nx,nz])
#        shots_per_sequence = self.shots_per_sequence
#        nseq = int(ceil(shots_per_step*1. / shots_per_sequence))
#        nshots = nseq * shots_per_sequence
#        xtollerance = 0.0021
#        ytollerance = 0.0021
#
#        self.message.add(' - '+run_str)        
#        self.message.add(' - Start Time:  '+time.ctime())
#        self.message.add(' - Number of scan steps:      {:}'.format(scan_steps))
#        self.message.add(' - Number of x steps:         {:}'.format(nx))
#        self.message.add(' - Number of z steps:         {:}'.format(nz)) 
#        self.message.add(' - Number of shots per seq:   {:}'.format(shots_per_sequence))
#        self.message.add(' - Number of shots per step:  {:}'.format(nshots))
#
#        if not nx and not nz:
#            self.message.add('INPUT ERROR -- Must provide vector of scan positions for x and/or z motors.')
#            self.message.add(self.scan.__doc__)
#            return
#
#        elif nx != nz:
#            if nx <= 1:
#                self.message.add(' - Only scan Z-axis')
#                scan_dict = {'z': zarray}  
#            elif nz <= 1:
#                self.message.add(' - Only scan X-axis')
#                scan_dict = {'x': xarray}
#            else:
#                self.message.add('INPUT ERROR --  x and y vectors must be the same length or a single value')
#                return 0
#
#        else:
#            scan_dict = {'x': xarray, 'z': zarray}
#
#        if not self.epicsLive.within_limits(**scan_dict):
#            self.message.add('SOFT LIMIT ERROR -- check scan values and try again.')
#            return 0
#
#        self.message.add('') 
#        self.message.add('{:>5} {:>8} {:>8} {:>10} {:>10} {:>10} {:>10} {:>8}  {:>10}  {:10}'.format( \
#            'step', 'time', 'tstep', 'Xpos', 'Ypos', 'dXpos', 'dYpos', 'shots', 'ana', 'status'))
#        self.message.add('-'*100)
#
#        time0 = time_last = time.time()
#
#        axval_start = []
#        azval_start = []
#        axval_end = []
#        azval_end = []
#        try:
#            for istep in range(scan_steps):
#                ana_status = 'OK'
#                self.backpad.ami_clear()
#                pos_dict ={alias: val[istep] for alias,val in scan_dict.items()}
#                ok_move = self.epicsLive.move(wait=True, **pos_dict)
#                if not ok_move:
#                    self.message.add('Invalid Move Attepted -- exiting scan script')
#                    return 0
#
#                # Try to move x motor again to get within tollerance if does not the first time
#                while abs(self.x.RBV-pos_dict['x']) > xtollerance or not ok_move:
#                    self.x.clear_errors()
#                    time.sleep(0.2)
#                    self.x.update_status()
#                    time.sleep(0.2)
#                    ana_status = 'Retry X Move'
#                    ok_move = self.epicsLive.move(wait=True, x=pos_dict['x']-0.005)
#                    ok_move = self.epicsLive.move(wait=True, x=pos_dict['x'])
#
#                # Try to move x motor again to get within tollerance if does not the first time
#                while abs(self.z.RBV-pos_dict['z']) > ytollerance or not ok_move:
#                    self.z.clear_errors()
#                    time.sleep(0.2)
#                    self.z.update_status()
#                    time.sleep(0.2)
#                    if ana_status == 'OK':
#                        ana_status = 'Retry Z Move'
#                    elif ana_status == 'Retry X Move':
#                        ana_status = 'Retry X and Z Move'
#                    ok_move = self.epicsLive.move(wait=True, z=pos_dict['z']-0.005)
#                    ok_move = self.epicsLive.move(wait=True, z=pos_dict['z'])
#                
#                xval = self.x.RBV
#                zval = self.z.RBV
#                time_current = time.time()
#
#                axval_start.append(xval)
#                azval_start.append(zval)
#                self.sequencer.repeat(nseq, wait=True)
#                time_current = time.time()
#                self.message.add('{:5} {:8.3f} {:8.3f} {:10.6f} {:10.6f} {:10.6f} {:10.6f} {:>8}  {:10.5g}  {:10}'.format( \
#                            istep, \
#                            time_current-time0, \
#                            time_current-time_last, \
#                            xval, \
#                            zval, \
#                            xval-pos_dict['x'], \
#                            zval-pos_dict['y'], \
#                            self.sequencer.total_count.VAL, \
#                            float(self.ana_result), \
#                            ana_status))
#                
#                xval = self.x.RBV
#                zval = self.y.RBV
#                axval_end.append(xval)
#                azval_end.append(zval)
#                time_last = time.time()
#            
#            self.set_parameter(axval_start=np.array(axval_start),azval_start=np.array(azval_start))
#            self.set_parameter(axval_end=np.array(axval_end),azval_end=np.array(azval_end))
#            return_status = 1
#
#        except KeyboardInterrupt:
#            self.epicsLive.stop()
#            self.message.add(' Entered from Keyboard')
#            self.message.add('>'*80)
#            self.message.add('Scan Aborted')
#            return_status = 0
#
#        self.message.add('-'*100)
#        self.message.add(' - End Time:  '+time.ctime())
#        self.message.add('-'*100)
#        if not post:
#            if raw_input('Post Message to experiment elog (y/n)?') == 'y':
#                post = True
#        if post:
#            self.message.post()
#        
#        return return_status
#
#
#
