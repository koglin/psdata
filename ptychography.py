import psdata
import epics
import time
import psutils 
import psmessage

from pylab import *

class ptychography(psdata.Detector):
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

        self.include_detector('sequencer', module='sequencer')
        self.include_detector('Dg2CsPad2x2')
        self.set_parameter(pedestal=0.)

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

    def init_scan(self, nskip=1, **kwargs):
        """Set sequencer and motor parameters here.
            - nskip is the number of events to skip between shots
        """
        A = [0] * 2048
        B = [0] * 2048
        C = [0] * 2048
        D = [0] * 2048
        A[0] = 187
        A[1] = 187
        A[2] = 187
        A[3] = 187
        A[4] = 189
        B[0] = nskip 
        B[1] = nskip
        B[2] = nskip
        B[3] = nskip
        B[4] = 0

        seq_length = 5
        self.sequencer.sync_marker.put('VAL', 6, wait=True)
        self.sequencer.array_subroutine.put('A', A, wait=True)
        self.sequencer.array_subroutine.put('B', B, wait=True)
        self.sequencer.array_subroutine.put('C', C, wait=True)
        self.sequencer.array_subroutine.put('D', D, wait=True)
        self.sequencer.seq_length.put('VAL', seq_length, wait=True)
        self.set_parameter(shots_per_sequence=4)
        for i in range(20):
            desc = epics.pv.PV('EVNT:SYS0:1:NAME'+str(A[i])).get()
#            epics.pv.PV('{:}:ECS:IOC:01:EC_{:}:14.DESC'.format( \
#                    self.sequencer._instrument.upper(), int(self.sequencer.VAL)).put(desc)

    @property
    def run_number(self):
        try:
            self._data.ami.RunNumber.ami_clear()
            time.sleep(0.1)
            run_number = self._data.ami.RunNumber.mean
        except:
            run_number = 0

        return run_number

    def scan(self, x=[], y=[], 
                   title='Ptychography scan:', 
                   shots_per_step=40, post=False, **kwargs):
        """Scan motors and perform analysis.
            x = vector of X motor positions
            y = vector of Y motor positions
            shots_per_step = number of shots per position (using sequencer)
            post = post in experiment elog if True 
                   (message can still be accessed afterwards in self.message)
        """
        run_number = self.run_number
        if run_number == 0 or run_number > 10000:
            run_str = 'NOT RECORDED'
            if raw_input('This run is not being recorded.  Continue Anyway (y/n)?') != 'y':
                return 0

        else:
            run_str = 'Run Number:  {:}'.format(run_number)

        self.init_scan(**kwargs)
        self.message = psmessage.message(title) 
        xarray = list(x)
        yarray = list(y)
        nx = len(xarray)
        ny = len(yarray)
        scan_steps = max([nx,ny])
        shots_per_sequence = self.shots_per_sequence
        nseq = int(ceil(shots_per_step*1. / shots_per_sequence))
        nshots = nseq * shots_per_sequence

        self.message.add(' - '+run_str)        
        self.message.add(' - Start Time:  '+time.ctime())
        self.message.add(' - Number of scan steps:      {:}'.format(scan_steps))
        self.message.add(' - Number of x steps:         {:}'.format(nx))
        self.message.add(' - Number of y steps:         {:}'.format(ny)) 
        self.message.add(' - Number of shots per seq:   {:}'.format(shots_per_sequence))
        self.message.add(' - Number of shots per step:  {:}'.format(nshots))

        if not nx and not ny:
            self.message.add('INPUT ERROR -- Must provide vector of scan positions for x and/or y motors.')
            self.message.add(self.scan.__doc__)
            return

        elif nx != ny:
            if nx <= 1:
                self.message.add(' - Only scan Y-axis')
                scan_dict = {'y': yarray}  
            elif ny <= 1:
                self.message.add(' - Only scan X-axis')
                scan_dict = {'x': xarray}
            else:
                self.message.add('INPUT ERROR --  x and y vectors must be the same length or a single value')
                return 0

        else:
            scan_dict = {'x': xarray, 'y': yarray}

        if not self.epicsLive.within_limits(**scan_dict):
            self.message.add('SOFT LIMIT ERROR -- check scan values and try again.')
            return 0

        self.message.add('') 
        self.message.add('{:>5} {:>8} {:>8} {:>10} {:>10} {:>10} {:>10} {:>8}  {:>10}  {:10}'.format( \
            'step', 'time', 'tstep', 'Xpos', 'Ypos', 'dXpos', 'dYpos', 'shots', 'ana', 'status'))
        self.message.add('-'*100)

        time0 = time_last = time.time()

        axval_start = []
        ayval_start = []
        axval_end = []
        ayval_end = []
        try:
            for istep in range(scan_steps):
                ana_status = 'OK'
                self.backpad.ami_clear()
                pos_dict ={alias: val[istep] for alias,val in scan_dict.items()}
                ok_move = self.epicsLive.move(wait=True, **pos_dict)
                if not ok_move:
                    self.message.add('Invalid Move Attepted -- exiting scan script')
                    return 0

                while abs(self.x.RBV-pos_dict['x']) > 0.000101 or not ok_move:
                    self.x.clear_errors()
                    time.sleep(0.2)
                    self.x.update_status()
                    time.sleep(0.2)
                    ana_status = 'Retry X Move'
                    ok_move = self.epicsLive.move(wait=True, x=pos_dict['x']-0.005)
                    ok_move = self.epicsLive.move(wait=True, x=pos_dict['x'])

                while abs(self.y.RBV-pos_dict['y']) > 0.000101 or not ok_move:
                    self.y.clear_errors()
                    time.sleep(0.2)
                    self.y.update_status()
                    time.sleep(0.2)
                    if ana_status == 'OK':
                        ana_status = 'Retry Y Move'
                    elif ana_status == 'Retry X Move':
                        ana_status = 'Retry X and Y Move'
                    ok_move = self.epicsLive.move(wait=True, y=pos_dict['y']-0.005)
                    ok_move = self.epicsLive.move(wait=True, y=pos_dict['y'])
                
                xval = self.x.RBV
                yval = self.y.RBV
                time_current = time.time()
#                self.message.add('{:5} {:8.3f} {:8.3f} {:10.6f} {:10.6f} {:10.6f} {:10.6f} {:>8}  {:10.5g}  {:10}'.format( \
#                            istep, \
#                            time_current-time0, \
#                            time_current-time_last, \
#                            xval, \
#                            yval, \
#                            xval-pos_dict['x'], \
#                            yval-pos_dict['y'], \
#                            self.sequencer.total_count.VAL, \
#                            float(self.ana_result), \
#                            ana_status))
 
                axval_start.append(xval)
                ayval_start.append(yval)
                self.sequencer.repeat(nseq, wait=True)
                time_current = time.time()
                self.message.add('{:5} {:8.3f} {:8.3f} {:10.6f} {:10.6f} {:10.6f} {:10.6f} {:>8}  {:10.5g}  {:10}'.format( \
                            istep, \
                            time_current-time0, \
                            time_current-time_last, \
                            xval, \
                            yval, \
                            xval-pos_dict['x'], \
                            yval-pos_dict['y'], \
                            self.sequencer.total_count.VAL, \
                            float(self.ana_result), \
                            ana_status))
                
                xval = self.x.RBV
                yval = self.y.RBV
                axval_end.append(xval)
                ayval_end.append(yval)
                time_last = time.time()
            
            self.set_parameter(axval_start=np.array(axval_start),ayval_start=np.array(ayval_start))
            self.set_parameter(axval_end=np.array(axval_end),ayval_end=np.array(ayval_end))
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
            self.message.post()
        
        return return_status

    def round_scan(self, **kwargs):
        """Input the parameters for scanning.
            # diameter of round scan [microns]
            D = 10;
            # radial step size [microns]
            Delta_r = 0.2;
            # center coordinates [microns]
            x_c = 0;
            y_c = 0;
            
            shots_per_step = number of shots per position (using sequencer)
        """
        self.input_params(**kwargs)
        if raw_input('Values ok (y/n)?') == 'y':
            self.scan(x=self.xvals, y=self.yvals, **kwargs)

    def input_params(self, D=10., Delta_r=0.2,
            x_c='current', y_c='current',
            int_param=False, answer='n', **kwargs):
        """Input the parameters for scanning.
            # diameter of round scan [microns]
            D = 10
            # radial step size [microns]
            Delta_r = 0.2
            # center coordinates [microns]
            x_c default is current motor VAL
            y_c default is current motor VAL
            
        """
        values_ok = False;
        while  not(values_ok):
            
            if int_param:
                # radial step size [in microns]
                Delta_r = input("Radial step size [in microns]: ");
                # diameter of the scan [in microns]
                D = input("Diameter of the round scan [in microns]: ");
                # center coordinates of the scan
                x_c = input("Center coordinate x [in microns]: "); 
                y_c = input("Center coordinate y [in microns]: ");

            # Parameter calculation--------------------------------------------------------

            # number of shells
            N_r = ceil(D/(2*Delta_r));
            print '#', int(N_r), 'shells,'
            # number of points in first shell, assuming an arc step size of ca. Delta r
            N_theta = ceil(2*pi);
            print '#', int(N_theta), 'points in the first shell,'
            # total number of required scan points
            N_tot = N_theta/2*N_r*(N_r+1);
            print '#', int(N_tot+1), 'scan points.'
            if int_param:
                answer = raw_input('Values ok (y/n)?')
                if answer == "y":
                    values_ok = True;
            else:
                values_ok = True;

                
        # Coordinate generation--------------------------------------------------------

        # coordinate arrays
        x = zeros(N_tot+1);
        y = zeros(N_tot+1);

        # center point
        if x_c == 'current':
            x_c = self.x.VAL*1000.
        
        if y_c == 'current':
            y_c = self.y.VAL*1000.
        
        x[0] = x_c;
        y[0] = y_c;

        # loop to generate the coordinates
        for k in range(1,int(N_r)+1):
            for m_k in range(1,int(N_theta*k)+1):
                x[N_theta*k/2*(k-1) + m_k] = x_c + Delta_r*k*cos((m_k-1)*2*pi/(N_theta*k));
                y[N_theta*k/2*(k-1) + m_k] = y_c + Delta_r*k*sin((m_k-1)*2*pi/(N_theta*k));

        self.set_parameter(xvals=x/1000.)
        self.set_parameter(yvals=y/1000.)



