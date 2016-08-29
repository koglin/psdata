
import psdata
import epics
import time
import psutils 

from pylab import *

class sample_scan(psdata.Detector):
    """Sample Control for cxic0315 Detector Class of psdata.Detector.
       Includes sequencer, burst and picker 'detectors' for convenience in scanning.
       Parameters set on initialization:
         xo = Default line scan starting position
         zo = Default sample focus Z position
    """

    def __init__(self,  *args,**kwargs):

        psdata.Detector.__init__(self, *args,**kwargs)

        parameters = {
                'xo': 15.,
                'zo': 0.,
                }

        self.set_parameter(**parameters)

        self.include_detector('sequencer', module='sequencer')
        self.include_detector('burst', module='burst')
        self.include_detector('picker', module='pulsepicker')

    @property
    def image(self):
        return self.Dg3Pim.image

    def ami_clear(self):
        """Clear AMI accumulation.
        """
        return self.Dg3Pim.ami.ami_clear()

    @property
    def ami_entries(self):
        """Number of event enties in ami data.
           Use ami_clear to reset
        """
        return self.Dg3Pim.ami.entries

    @property
    def ana_result(self):
        ana_result = self.sequencer.total_count.VAL
        
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

    def next_y(self, ystep=0.1):
        self.y.move(ystep,relative=True, confirm_move=True, wait=True)

    def carrage_return(self, ystep=0.1, xo=None):
        """Return to start of next scan after moving sample ystep down.
            ystep = sample Y step down [default = 0.1 mm]
            xo = sample X start position [default = self.xo]
        """
        if not xo:
            xo = getattr(self, 'xo')
        
        self.y.move(ystep,relative=True, confirm_move=True)
        
        if x0:
            self.x.move(x0, confirm_move=True, wait=True)
        else:
            print 'Warning:  No self.xo parameter set'

    def line_scan(self, nscans=1,
            xo='current', xwidth=1., 
            yo='current',
            zo='current', zwidth=None, 
            xstep=0.1, 
            burst=False,
            rate=120,
            carrage_return=False,
            post=False):
        """Perform a line scan.
            xo = initial horizontal position [default = 'current']
            yo = initial vertical position [default = 'current']
            zo = initial focus position [default = 'current']
            xwidth = horizontal scan width of scan in mm [default=1 mm]
            zwidth = focus scan width of scan in mm [default=None]
            xstep = step size per shot in mm at input rate [default = 0.05 mm]
            rate = beam repetition [default = 120 Hz]
            burst = accelerator burst mode on [default = False] 
            title = title of scan that will go in the first line of the post
            post = post in experiment elog if True 
                   (message can still be accessed afterwards in self.message)
            carrage_return = Go to start of next line if set true.
        """
        number_of_shots = xwidth/xstep
        xspeed = xstep*rate
        scan_time = number_of_shots/rate

        max_speed = 8 # mm/s
        speed_error_str = '{:} motor speed {:} > {:} mm/s too fast.  Aborting...'
        if xspeed > max_speed:
            self.message.add(speed_error_str.format('X', xspeed, max_speed))
            return 0
        
        if zwidth:
            zspeed = zwidth/scan_time
            if zspeed > max_speed:
                self.message.add(speed_error_str.format('Z', zspeed, max_speed))
                return 0

        self.message = psutils.message(title)
        if xo is 'current':
            xo = self.x.get('RBV')
        
        if yo is 'current':
            yo = self.y.get('RBV')

        if zo is 'current':
            zo = self.z.get('RBV')

        init_pos = {'x': xo, 'y': yo, 'z':zo}
        if not self.epicsLive.within_limits(**init_pos):
            self.message.add('SOFT LIMIT ERROR -- check initial scan values and try again.')
            return 0

        print xo, xwidth,zo, zwidth
        final_pos = {'x': xo+xwidth}
        if zwidth:
            final_pos.update({'z':zo+zwidth})
        
        if not self.epicsLive.within_limits(**final_pos):
            self.message.add('SOFT LIMIT ERROR -- check scan width values and try again.')
            return 0

        self.message.add(' - Start Time:  '+time.ctime())
        self.message.add(' - Scan Time:             {:>10} s'.format(scan_time))
        self.message.add(' - Number of Shots: {:10.6f}'.format(number_of_shots))
        self.message.add(' - y position (no scan):  {:10.6f} mm'.format(yo))
        
        self.message.add(' - x start position:      {:10.6f} mm'.format(xo))
        if xwidth:
            self.message.add(' - x end position:        {:10.6f} mm'.format(xo+xwidth))
            self.message.add(' - x scan range:          {:10.6f} mm'.format(xwidth))
            self.message.add(' - x step size:           {:10.6f} mm'.format(xstep))
            self.message.add(' - x speed:               {:10.6f} mm/s'.format(xspeed))
            if self.x.VBAS > xspeed:
                self.x.put('VBAS', xspeed)
            self.x.put('VELO', xspeed)
        
        if zwidth:
            self.message.add(' - z start position:      {:10.6f} mm'.format(zo))
            self.message.add(' - z end position:        {:10.6f} mm'.format(zo+zwidth))
            self.message.add(' - z scan range:          {:10.6f} mm'.format(zwidth))
            self.message.add(' - z speed:               {:10.6f} mm/s'.format(zspeed))
            if self.z.VBAS > zspeed:
                self.z.put('VBAS', zspeed)
            self.z.put('VELO', zspeed)
        else:
            self.message.add(' - z position (no scan):  {:10.6f} mm'.format(zo))
       
        if burst:
            if rate == 120:
                self.burst.burst_rate.put('VAL', 'Full', use_complete=True)
            elif rate == 30:
                self.burst.burst_rate.put('VAL', '30Hz', use_complete=True)
            elif rate == 10:
                self.burst.burst_rate.put('VAL', '10Hz', use_complete=True)
            elif rate == 5:
                self.burst.burst_rate.put('VAL', '5Hz', use_complete=True)
            elif rate == 1:
                self.burst.burst_rate.put('VAL', '1Hz', use_complete=True)
            else:
                self.message.add('Invalit burst rate setting. -- Aborting Scan.')
                return 0

            burst_rate = self.burst.burst_rate.get('VAL', as_string=True) 
            self.message.add(' - Burst rate:            {:10}'.format(burst_rate))

        if raw_input('Do you want to execute this scan (y/n)?') != 'y':
            return 0
       
        try:
            ok_move = self.epicsLive.move(wait=True, **init_pos)
            if not ok_move:
                self.message.add('Motors did not reach start position. -- Aborting Scan.')
                return 0

            ok_move = self.epicsLive.move(use_complete=True, **final_pos)
            if burst:
                epics.caput('PATT:SYS0:1:MPSBURSTCNTMAX', number_of_shots)
                self.burst.start_burst() 

            status = self.epicsLive.all_done_moving(wait=True)

            "cxi.sample.burst.stop_burst()"

            epics.caput('PATT:SYS0:1:MPSBURSTCNTMAX', 1)

            if carrage_return:
                self.carrage_return(xo=xo)

        except KeyboardInterrupt:
            self.epicsLive.stop()
            self.message.add(' Entered from Keyboard')
            self.message.add('>'*80)
            self.message.add('Scan Aborted')
            if raw_input('Do you want to move motors back to original position (y/n)?') != 'y':
                ok_move = self.epicsLive.move(wait=True, **init_pos)
            return_status = 0

        self.message.add('-'*100)
        if not post:
            if raw_input('Post Message to experiment elog (y/n)?') == 'y':
                post = True
        if post:
            self.message.post()
 

    def repeated_scan(self,  
                    nscans=1,
                    xo='current', xbin=0.005, xwidth=0.1,
                    yo='current', ybin=0.005, ywidth=0.0,
                    zo='current', zbin=0.005, zwidth=0.0,
                    tbin=0.0083333,
                    title='Continuous Scan:', 
                    post=False):
        """Scan motors and perform analysis.
           -- Note: example from SPI injector scan.
            xo = initial horizontal position [default = 'current']
            yo = initial vertical position [default = 'current']
            zo = initial focus position [default = 'current']
            xwidth = horizontal scan width of scan in mm
            ywidth = vertical scan width of scan in mm
            zwidth = focus scan width of scan in mm
            xbin = horizontal 'bin' size in mm
            ybin = vertical 'bin' size in mm
            zbin = focus 'bin' size in mm
            tbin = time that motor is within the specified bins [default = 0.008333 sec = 1 shot]
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
#                    self.backpad.ami_clear()
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


