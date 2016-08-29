# Frame scan used for cxim2716 experiment

import psdata
import epics
import time
import psutils 
import psmessage
import csv

from pylab import *
import math

#############################################################################################################################
## this is the class that defines a sample frame. We use the number of rows, and cols, and their separation
## to identify a frame. It is also possible to have sub steps. The roll angle of the sample is also there.
class Frame(object):

    def __init__(self, Nx=13,Ny=12,dx=1.5,dy=1.5,Nsubx=9,Nsuby=9,dsubx=0.06,dsuby=0.06,roll=0.0,pitch=0.):
        """Define sample frame and methods.
            size = Nx*Ny*Nsubx*Nsuby # total number of windows
            Nx = Nx # Number of large windows in x-axis
            Ny = Ny # Number of large windows in y-axis
            dx = dx # Large step size along x-axis
            dy = dy # Large step size along y-axis
            Nsubx = Nsubx # Number of sub-windows in x-axis
            Nsuby = Nsuby # Number of sub-windows in x-axis
            dsubx = dsubx # Sub-step size along x-axis
            dsuby = dsuby # Sub-step size along y-axis
            roll = roll # Roll
            pitch = pitch # Pitch
            index = 0 # Number of shots already done on this sample
            xscale = 1.0 #Scaling factor along x-axis
            yscale = 1.0 # Scaling factor along y-axis
            offsetx = 0.0 #Common offset to position list along x-axis
            offsety = 0.0 #Common offset to position list along y-axis
        """

        self.size = Nx*Ny*Nsubx*Nsuby # total number of windows
        self.Nx = Nx # Number of large windows in x-axis
        self.Ny = Ny # Number of large windows in y-axis
        self.dx = dx # Large step size along x-axis
        self.dy = dy # Large step size along y-axis
        self.Nsubx = Nsubx # Number of sub-windows in x-axis
        self.Nsuby = Nsuby # Number of sub-windows in x-axis
        self.dsubx = dsubx # Sub-step size along x-axis
        self.dsuby = dsuby # Sub-step size along y-axis
        self.roll = roll # Roll
        self.pitch = pitch # Pitch
        self.index = 0 # Number of shots already done on this sample
        self.xscale = 1.0 #Scaling factor along x-axis
        self.yscale = 1.0 # Scaling factor along y-axis
        self.offsetx = 0.0 #Common offset to position list along x-axis
        self.offsety = 0.0 #Common offset to position list along y-axis
        self.xstart = 0.0
        self.ystart = 0.0
        self.zstart = 0.0

    def set_start(self,xstart,ystart,zstart):
    
        self.xstart = xstart
        self.ystart = ystart
        self.zstart = zstart
    
    def print_info(self,fname=None):
    
        if fname:
            np.savetxt(fname,[self.size,self.Nx,self.Ny,self.dx])
        
        print "Size = ", self.size
        print  self.Nx
        print  self.Ny
        print  self.dx
        print self.dy
        print self.Nsubx
        print self.Nsuby
        print self.dsubx
        print  self.dsuby
        print  self.roll
        print  self.index
        print  self.xscale
        print  self.yscale
        print  self.offsetx
        print  self.offsety
        print  self.xstart
        print  self.ystart
        print  self.zstart

    #############################################################################################################################
    ## This function can be used to skip to the last column of the sample.
    ## This should be done for every sample to find the true roll and x-scaling.
    ## This function can be entered over and over until the proper roll and scaling is found
    ## it is important to manually enter the coordinate of the topmost, leftmost cell as arguments
    def get_lc(self,roll,xscale,yscale):

        yrot = self.ystart
        zrot = self.zstart
        self.roll = roll
        self.xscale=xscale
        dx = self.dx*xscale
        dsubx = self.dsubx*xscale
        pitch = self.pitch*pi/180.
        
        ##Coordinate transformation from rolled to non-rolled reference frame
        #xhat=(self.dx*(self.Nx-1)+self.dsubx*(self.Nsubx-1))*cos(self.roll)+(self.dy*0+self.dsuby*0)*sin(self.roll)
        #yhat=-(self.dx*(self.Nx-1)+self.dsubx*(self.Nsubx-1))*sin(self.roll)+(self.dy*0+self.dsuby*0)*cos(self.roll)
        
        #xhat=(dx*(self.Nx-1)+dsubx*(self.Nsubx-1))*cos(self.roll)
        #yhat=-(dx*(self.Nx-1)+dsubx*(self.Nsubx-1))*sin(self.roll)
        
        xhat=(self.dx*(self.Nx-1)+self.dsubx*(self.Nsubx-1))*cos(self.roll)*xscale
        yhat=-(self.dx*(self.Nx-1)+self.dsubx*(self.Nsubx-1))*sin(self.roll)*yscale
        
        x=xhat
        y=yhat
        z=self.zstart
        ##If pitch angle is non zero...
        ##coordinate transformation from pitched to non-pitched reference frame
        if (pitch!=0.0):
            y=yhat*cos(pitch)
            z=-(y+self.ystart-yrot)*sin(pitch)/cos(pitch)
            z=z+zrot
    
        ##coordinate transformation to motor reference frame
        x=x+self.xstart
        y=y+self.ystart
                
        return {'x':x,'y':y, 'z':z}

    #############################################################################################################################
    ## This function can be used to skip to the last row of the sample.
    ## This should be done for every sample to find the true roll and y-scaling.
    ## This function can be entered over and over until the proper roll and scaling is found
    ## it is important to manually enter the coordinate of the topmost, leftmost cell as arguments
    def get_lr(self,roll,xscale,yscale):
        
        yrot = self.ystart
        zrot = self.zstart
        self.roll = roll
        self.yscale = yscale
        dy = self.dy*yscale
        dsuby = self.dsuby*yscale
        pitch = self.pitch*pi/180.

        ##Coordinate transformation from rolled to non-rolled reference frame
        #xhat=(self.dx*(self.Nx-1)+self.dsubx*(self.Nsubx-1))*cos(self.roll)+(self.dy*0+self.dsuby*0)*sin(self.roll)
        #yhat=-(self.dx*(self.Nx-1)+self.dsubx*(self.Nsubx-1))*sin(self.roll)+(self.dy*0+self.dsuby*0)*cos(self.roll)
        
        #xhat=(dy*(self.Ny-1)+dsuby*(self.Nsuby-1))*sin(self.roll)
        #yhat=(dy*(self.Ny-1)+dsuby*(self.Nsuby-1))*cos(self.roll)

        xhat=(dy*(self.Ny-1)+dsuby*(self.Nsuby-1))*sin(self.roll)*xscale
        yhat=(dy*(self.Ny-1)+dsuby*(self.Nsuby-1))*cos(self.roll)*yscale

        x=xhat
        y=yhat
        z=self.zstart
       ##If pitch angle is non zero...
        ##coordinate transformation from pitched to non-pitched reference frame
        if (pitch!=0.0):
            y=yhat*cos(pitch)
            z=-(y+self.ystart-yrot)*sin(pitch)/cos(pitch)
            z=z+zrot
        
        ##coordinate transformation to motor reference frame
        x=x+self.xstart
        y=y+self.ystart
        
        return {'x':x,'y':y, 'z':z}

    #############################################################################################################################
    ## Only after the correct roll angle for the particular frame has been found, we can generate the coordinates for the windows.
    ##This is done with the following function. It returns a dictionary that can be passed to Jason's scan function.
    def get_scan_coords(self,index):
        #xstart = 0.0## to be replaced with read back value for x motor
        #ystart = 0.0## to be replaced with read back value for y motor
        #zstart = 0.0## to be replaced with read back value for y motor

        pitch = self.pitch*pi/180.
        yrot = self.ystart
        zrot = self.zstart

        dx = self.dx*self.xscale
        dy = self.dy*self.yscale
        dsubx = self.dsubx*self.xscale
        dsuby = self.dsuby*self.yscale
        
        x = np.zeros(self.size)
        y = np.zeros(self.size)
        z = np.zeros(self.size)
        ind =0
        
        for i in range(0,self.Ny):
            for j in range(0,self.Nx):
                for m in range (0,self.Nsuby):
                    if ((m%2)!=0):
                        #xoffset = 0.06
                        xoffset = 0.03
                        #xoffset = -0.03
                        #xoffset = 0.
                    else:
                        xoffset = 0.0
                    #for j in range(0,self.Nx):
                    for k in range(0,self.Nsubx):
                        if((i%2)==0 and (m%2)==0):
                            ##Coordinate transformation from rolled to non-rolled reference frame
                            xhat=(dx*j+dsubx*k)*cos(self.roll)+(dy*i+dsuby*m)*sin(self.roll)+xoffset
                            yhat=-(dx*j+dsubx*k)*sin(self.roll)+(dy*i+dsuby*m)*cos(self.roll)
                        elif((i%2)==0 and (m%2)!=0):
                            ##Coordinate transformation from rolled to non-rolled reference frame
                            xhat=(dx*j+dsubx*(self.Nsubx-1-k))*cos(self.roll)+(dy*i+dsuby*m)*sin(self.roll)+xoffset
                            yhat=-(dx*j+dsubx*(self.Nsubx-1-k))*sin(self.roll)+(dy*i+dsuby*m)*cos(self.roll)
                        if((i%2)!=0 and (m%2)==0):
                            ##Coordinate transformation from rolled to non-rolled reference frame
                            xhat=(dx*(self.Nx-1-j)+dsubx*k)*cos(self.roll)+(dy*i+dsuby*m)*sin(self.roll)+xoffset
                            yhat=-(dx*(self.Nx-1-j)+dsubx*k)*sin(self.roll)+(dy*i+dsuby*m)*cos(self.roll)
                        elif((i%2)!=0 and (m%2)!=0):
                            ##Coordinate transformation from rolled to non-rolled reference frame
                            xhat=(dx*(self.Nx-1-j)+dsubx*(self.Nsubx-1-k))*cos(self.roll)+(dy*i+dsuby*m)*sin(self.roll)+xoffset
                            yhat=-(dx*(self.Nx-1-j)+dsubx*(self.Nsubx-1-k))*sin(self.roll)+(dy*i+dsuby*m)*cos(self.roll)

                    
                        x[ind]=xhat
                        y[ind]=yhat
                        
                        ##If pitch angle is non zero...
                        ##coordinate transformation from pitched to non-pitched reference frame
                        if (pitch!=0.0):
                            #print "applying pitch correcton\n"
                            y[ind]=yhat*cos(pitch)
                            z[ind]=-(y[ind]+self.ystart-yrot)*sin(pitch)/cos(pitch)
                            z[ind]=z[ind]+zrot
                        else:
                            z[ind]=self.zstart
                        
                        ##coordinate transformation to motor reference frame
                        x[ind]=x[ind]+self.xstart
                        y[ind]=y[ind]+self.ystart
                        
                        #print j,i,m,k,x[ind],y[ind]
                        ind = ind +1
    
        #np.savetxt('frame',np.transpose([x[index:],y[index:],z[index:]]))
        return {'x': x[index:],
                'y': y[index:],
                'z':z[index:]}

#############################################################################################################################
## WE can use this fuction atfer the scan script has been aborted by the user for any reason. The stage will be at some coordinate
## on the sample. This function re-generates the dictionary for Jason's script starting from the coordiantes of the next window
    def reset_after_stop(self,d,step):
        
        return  {attr: item[step:] for attr, item in a.items()}

#        x_old = d['x']
#        y_old = d['y']
#        z_old = d['z']
#        
#        x = x_old[step:self.size]
#        y = y_old[step:self.size]
#        z = z_old[step:self.size]
#
##        np.savetxt('frame',np.transpose([x,y]))
#        return {'x': x,
#                'y': y,
#                'z': z}

#############################################################################################################################
## If the scan as been aborted because of some drifitng off the samples, we can use this fuction to recenter the cross on the CURRENT window
    def recenter(self,d,index,dx,dy):
    
        x = d['x']
        y = d['y']

        x_cur = x[index]
        y_cur = y[index]
        
        #scan.move(x=x_cur+dx, y=y_cur+dy)
        print "Is this centered\n? (y/n)"
        ans = raw_input()
        print ans
        if ans in ['n','N']:
            #scan.move(x=-(x_cur+dx), y=-(y_cur+dy))
            print "Try again\n"
        else:
            x=x+dx
            y=y+dy

#d = {'x':x,'y':y}

        #np.savetxt('frame',np.transpose([x,y]))
        return {'x': x,'y': y}


class Scan(psdata.Detector):
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
#        self.set_parameter(pedestal=0.)
        self.epicsLive.add_device(gdet='GDET:FEE1:241:ENRC')
        self.include_detector('burst', module='burst')
        self.include_detector('sequencer', module='sequencer')
        self.include_detector('picker', module='pulsepicker')
        if self.daq is None:
            self._data.load_daq()

        self.istep = 0

    def make_frame(self, **kwargs):
        self.frame = Frame(**kwargs)

    def move_to_lc(self, roll=0.0, xscale=1.0, yscale=1.0, move=True, wait=True):
        """Move to last column (in same row) of current frame.
        """
        move_dict = self.frame.get_lc(roll, xscale, yscale)
        c = self.get_coords() # regenerates coordinates with current roll and xscale
        print 'Moving to last column of current frame'
        print move_dict
        if move:
            self.epicsLive.move(wait=wait, **move_dict)

    def move_to_lr(self, roll=0.0, xscale=1.0, yscale=1.0, move=True, wait=True):
        """Move to last row (in same column) of current frame.
        """
        move_dict = self.frame.get_lr(roll, xscale, yscale)
        c = self.get_coords() # regenerates coordinates with current roll and xscale
        print 'Moving to last row of current frame'
        print move_dict
        if move:
            self.epicsLive.move(wait=wait, **move_dict)

    def move_delta(self, index=None, dx=0., dy=0., wait=True):
        if not index:
            index = self.istep

        xo = self.coords['x'][index]
        yo = self.coords['y'][index]
        x = xo+dx
        y = yo+dy
        print 'Moving [{:},{:}] to position {:} at [x,y] = [{:},{:}] mm'.format(dx, dy, index, x, y)
        self.move(x=x,y=y, wait=wait)

    def set_start(self, name='start'):
        """set start position of frame from current motor positions
        """
        start_dict = self.save_positions(name, attrs=['x', 'y', 'z'])
        apos = start_dict[name]
        self.frame.set_start(apos['x'],apos['y'],apos['z'])
        print 'Setting current position as start of current frame'
        print apos

    def get_coords(self, index=0, recalc=True):
        if recalc:
            coords = self.frame.get_scan_coords(index)
            self.set_parameter(coords=coords)
        return self.coords


    def tilt_to(self, tilt=0., axis_y=-13.5):
        print 'Assuming initial tilt is 0'
        d = self.epicsLive.get_all('RBV')
        del_y = axis_y - d['y'] 
        
        d['pitch'] += tilt
        tilt *= np.pi / 180.
        print 'old del_y =', del_y
        print 'tilt =', tilt
        print 'del_z =', del_y * np.sin(tilt)
        print 'new del_y =', del_y * np.cos(tilt)
        d['z'] += del_y * np.sin(tilt)
        d['y'] = axis_y + del_y * np.cos(tilt)
        self.epicsLive.move(wait=True, **d)

    def recenter(self, dx=0., dy=0., dz=0., repeat=None):
        d = self.epicsLive.get_all('RBV')
        d['x'] += dx
        d['y'] += dy
        d['z'] += dz
        print 'Moving to', d
        self.epicsLive.move(wait=True, **d)
        if repeat:
            self.sequencer.repeat(repeat)

        print 'Is this okay? [Y/Return or N]'
        ans = raw_input()
        #if ans.lower()[0] == 'y':
        if ans in ['y', 'Y']:
            print 'Accepting change'
            self.coords['x'] += dx
            self.coords['y'] += dy
            self.coords['z'] += dz
            return 1
        else:
            print 'Going back to old position'
            d['x'] -= dx
            d['y'] -= dy
            d['z'] -= dz
            self.epicsLive.move(wait=True, **d)
            return 0

    def scan_frame(self, start_index=0, stop_index=None, relative=False, start_tolerance=0.03, **kwargs):

        if True:
            # Use native index functionality in scan method to keep index positions for logging
            if stop_index is None:
                stop_index = self.coords['x'].shape[0]
            coords = self.coords
            
            x=coords['x']
            y=coords['y']
            z=coords['z']
 
            self.scan(x=x, y=y, z=z, start_index=start_index, stop_index=stop_index, relative=relative, **kwargs)

        else:

            if stop_index is None:
                stop_index = self.coords['x'].shape[0]
            coords = self.coords
            
            x=coords['x'][start_index:stop_index]
            y=coords['y'][start_index:stop_index]
            z=coords['z'][start_index:stop_index]
            current_dict = self.epicsLive.get_all('RBV')
            if relative:
                delta_pos = np.sqrt((current_dict['x']-x[0])**2
                                   +(current_dict['y']-y[0])**2
                                   +(current_dict['z']-z[0])**2)
                
                if delta_pos > start_tolerance:
                    print 'You are {:8.3f} mm from the nominal start postion'.format(delta_pos)
                    print 'Correct this and try again.'
            
                x -= x[0]
                y -= y[0]
                z -= z[0]
    #            x -= self.frame.xstart
    #            y -= self.frame.ystart
    #            z -= self.frame.zstart
            
            # TODO Need to pass start_index
            self.scan(x=x, y=y, z=z, relative=relative, **kwargs)

    def goto_start(self, name='start'):
        """Goto start position of frame from saved motor positions
        """
        print 'Going back to start of current frame'
        apos = self.goto_position(name)
        print apos

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

    def save_positions(self, name='default', attrs=[]):
        apos = self._save_positions
        if not apos:
            apos = {}

        cur_dict = self.epicsLive.get_all('RBV') 
        if attrs:
            cur_dict = {attr: val for attr, val in cur_dict.items() if attr in attrs}

        apos.update({name: cur_dict})
    
        self.set_parameter(_save_positions=apos)
        return apos

    def goto_position(self, name=None, wait=True):
        apos = self._save_positions.get(name)
        if apos:
            self.epicsLive.move(wait=wait, **apos)
        
        return apos

    def get_position(self, name=None):
        apos = self._save_positions.get(name)
        return apos

    @property
    def daq(self):
        return self._data.daq

    @property
    def run_number(self):
        try:
            return self.daq.runnumber
        except:
            return 0

    def scan(self, filename=None,  
                   daq=False,
                   cycle=None,
                   burst=False,
                   sequence=False,
                   picker=False,
                   record=False,
                   simulate=False,
                   post=None,
                   relative=False,
                   reset=False,
                   nshots=1,
                   title=None,
                   mon_rate=30,
                   shoot_rate=120,
                   start_index=0,
                   stop_index=None,
                   start_tolerance=None,
                   gdet_threshold=1., 
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
                start_index:   initial starting index (default = 0)
                stop_index:    ending index (default = None, i.e., to last event)
                start_tolerance:  check if within start_tolerance of first step 
                gdet_threshold: gas detector threshold [mJ]
        
            relative not allowed when starting from start_index = 0 

        """
#                start_index Staring index of position_dict arrays (default = 0)
        if not title:
            title = '{:} Scan'.format(self._name) 

        #print locals()

        istep = start_index
        if relative and start_index != 0:
            print 'relative not allowed when starting from start_index = 0' 

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
            
            init_dict[attr] = values[istep]
           
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

        if sequence:
            self.sequencer.stop()
            time.sleep(0.2)
            self.picker.make_sequence(nshots, burst=burst, picker=picker, 
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
        all_steps = range(scan_steps)
        if abs(start_index) > len(all_steps):
            self.message.add('Input Error:  start_index = {:} too large for scan range'.format(start_index))
            return 0

        if stop_index is not None:
            if abs(stop_index) > len(all_steps):
                self.message.add('Input Error:  stop_index = {:} too large for scan range'.format(stop_index))
                return 0

        if start_tolerance and not relative:
            move_dict ={attr: val[istep] for attr,val in scan_dict.items()}
            for attr, val in move_dict.items():
                sdiff = abs(val-orig_dict[attr]) 
                if sdiff > start_tolerance:
                    self.message.add('Start Tolerance Error:  {:} scan start position is {:} from current position'.format(attr, sdiff))
                    return 0

        for istep in all_steps[start_index:stop_index]:
            try:
                self.istep = istep
                if relative:
                    move_dict ={attr: val[istep]+orig_dict[attr] for attr,val in scan_dict.items()}
                else:
                    move_dict ={attr: val[istep] for attr,val in scan_dict.items()}
 
                if simulate:
                    # simulate scan -- do not move motors
                    pos_dict = move_dict
                    time.sleep(0.05)
                
                else:        
                    ok_move = self.epicsLive.move(wait=True, **move_dict)
                    while not ok_move:
                        self.message.add('Invalid Move Attepted -- exiting scan script')
                        if raw_input('Do you want to try move again (y/n)? -- otherwise exit.') in ['y','Y']:
                            ok_move = self.epicsLive.move(wait=True, **move_dict)
                        else:
                            return_status = 0
                            break
#                            if post == True:
#                                print 'Posting to e-log'
#                                time.sleep(0.5)
#                                self.message.post(name=self._data.exp, run_num=run_number, tag=title)
#                            return 0

                    pos_dict = {}
                    for attr in scan_dict:
                        pos_dict[attr] = getattr(getattr(self, attr), readback_dict[attr])

                time_current = time.time()

                if gdet_threshold:
                    iwait = 0
                    while self.gdet.VAL < gdet_threshold:
                        time.sleep(1.0)
                        iwait += 1
                        if iwait % 10:
                            print 'Low Beam = {:} mJ -- Waiting for beam to return.'.format(self.gdet.VAL)

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
                
                self.message.add(message_format.format(*vals))
                if time_current-time_last > 1.6:
                    self.message.add('-'*100)
                
                time_last = time.time()
 
            except KeyboardInterrupt:
                self.epicsLive.stop()
                self.message.add(' Entered from Keyboard')
                self.message.add('>'*80)
                if raw_input('Do you want to recenter and continue (y/n)?') in ['y','Y']:
                    self.picker.make_sequence(1, burst=False, picker=False, 
                            mon_rate=mon_rate, shoot_rate=shoot_rate)
                    continue_scan = False
                    while not continue_scan:
                        self.sequencer.repeat(4)
                        try:
                            dx = float(raw_input('Enter dx: '))
                        except:
                            dx = 0
                        
                        try:
                            dy = float(raw_input('Enter dy: '))
                        except:
                            dy = 0
                        
                        try:
                            dz = float(raw_input('Enter dz: '))
                        except:
                            dz = 0
                        
                        continue_scan = self.recenter(dx=dx,dy=dy,dz=dz, repeat=4)

                    if dx:
                        self.message.add('Sample recentered in x by {:8.3f} mm'.format(dx))
                    if dy:
                        self.message.add('Sample recentered in y by {:8.3f} mm'.format(dy))
                    if dz:
                        self.message.add('Sample recentered in z by {:8.3f} mm'.format(dz))
                   
                    self.message.add('Updating coords with recenter deltas and continuing')
                    scan_dict = self.coords
                    self.message.add('<'*80)

                    # set sequence back
                    self.picker.make_sequence(nshots, burst=burst, picker=picker, 
                            mon_rate=mon_rate, shoot_rate=shoot_rate)
                else:
                    self.message.add('Scan Aborted')
#                    self.daq.disconnect()
                    return_status = 0
                    break
                       
            return_status = 1

        if daq:
            self.daq.stop_run()
            #self.daq.disconnect()
            time.sleep(1.)
            self.free_run()

        self.message.add('-'*100)
        self.message.add(' - End Time:  '+time.ctime())
        self.message.add('-'*100)
        if post is None and not simulate:
            if raw_input('Post Message to experiment elog (y/n)?') in ['y', 'Y']:
                post = True
        if post:
            time.sleep(0.5)
            self.message.post(name=self._data.exp, run_num=run_number, tag=title)
        
        if reset:
            self.goto_position('scan_start_positions', wait=True)

        return return_status

    def free_run(self):
        self.picker.make_sequence(1, burst=False, picker=False)
        self.sequencer.repeat(-1)
        if self.daq.state != 'running':
            self.daq.begin(events=100000)

# moved to pulsepicker.py
#    def make_sequence(self, nevents=1, burst=False, picker=False,
#            shoot_code=187, mon_code=181, mon_rate=30, shoot_rate=120, picker_code=185):
#        """Helper function to set sequencer for shoot and monitor.
#        """
#        eventCodes = []
#        beam = []
#        burst_list = []
#        if picker:
#            if shoot_rate == 120:
#                self.picker.follower_mode()
#                eventCodes.append(picker_code)
#                beam.append(0)
#                burst_list.append(0)
#            else:
#                self.picker.flipflop_mode()
#
#        for i in range(nevents):
#            if picker and shoot_rate < 60:
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
#            if mod(i, shoot_rate/mon_rate) == 0:
#                eventCodes.append(mon_code)
#                beam.append(0)
#                burst_list.append(0)
#
#        if picker:
#            if shoot_rate == 120:
#                self.picker.follower_mode()
#                eventCodes.append(picker_code)
#                beam.append(0)
#                burst_list.append(0)
# 
#        self.sequencer.set_sequence(eventCodes=eventCodes, beam=beam, burst=burst_list)


