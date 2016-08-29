#####################################################################
## performs 2d scan, row by row, on a square Si3N4 membrane allowing for pitch angles differnet from zero;
##Call sequence:
# python square.py --Nx=10 --Ny=10 --dx=200.0e-3 --dy=200.0e-3 [--Nsubx=1] [--dsubx=70.0e-3]  [--xstart=0.0] [--ystart=0.0] [--x2=133.0e-3] [--y2=50.0e-3] [--theta=0.01] [-o, for offline] [-q, to disable shot] [-p, to enable pitch angle correction]

##INPUT VARIABLES
#Nx=Number of rows; must be specified
#Ny=Number of columns; must be specified
#dx=cell length in mm. Must be specified
#dy=cell height in mm. Must be specified

##OPTIONAL INPUT VARIABLES
#Nsubx=Number of shots per cell; default is 1
#dsubx=separtation between shots in a cell, in units of mm; default is 0.07mm
#xstart=optional x coordinate of initial location in mm. If not specified, script will start from current position.
#ystart=optional y coordinate of initial location in mm. If not specified, script will start from current position.
#x2=optional x coordinate in mm of a point ON THE SAME ROW AS THE INITIAL ONE, to compute misalginmet angle
#y2=optional x coordinate in mm of a point ON THE SAME ROW AS THE INITIAL ONE, to compute misalginmet angle
#theta=optional value of the misalignment error in radians. Default value is 0.
#####################################################################

from optparse import OptionParser
parser = OptionParser()
parser.add_option("-o", action="store_false", dest="flag",default="true",help="To run script while offline.")
parser.add_option("-q", action="store_false", dest="shot_flag",default="true",help="To run script disabling shots.")
parser.add_option("-p", action="store_true", dest="pitchflag",default="false",help="To run script with pitch correction.")
parser.add_option("--Nx=", type="int", dest="Nx")
parser.add_option("--Ny=", type="int", dest="Ny")
parser.add_option("--dx=", type="float", dest="dx")
parser.add_option("--dy=", type="float", dest="dy")
parser.add_option("--Nsubx=", type="int", dest="Nsubx",default=1)
parser.add_option("--dsubx=", type="float", dest="dsubx",default=0.48)
parser.add_option("--Nsuby=", type="int", dest="Nsuby",default=1)
parser.add_option("--dsuby=", type="float", dest="dsuby",default=0.48)
parser.add_option("--xstart=", type="float", dest="xstart",default=-1111.0)
parser.add_option("--ystart=", type="float", dest="ystart",default=-1111.0)
parser.add_option("--zstart=", type="float", dest="zstart",default=-1111.0)
parser.add_option("--y2=", type="float", dest="y2",default=-1111.0)
parser.add_option("--x2=", type="float", dest="x2",default=-1111.0)
parser.add_option("--theta=", type="float", dest="theta",default=0.0)
parser.add_option("--sfc", dest="skip_first_column",default=0,type="int")
parser.add_option("--sfr", dest="skip_first_row",default=0,type="int")
parser.add_option("--nr", dest="goto_new_row",default=0,type="int")

(options,args)=parser.parse_args()

from math import *
import time
import sys
from datetime import datetime

import psdata
import psioc

#cd '/reg/neh/operator/cxiopr/userexpts/cxii8715/'

##Assigning command line variables
Nx = options.Nx
Ny = options.Ny
xstart = options.xstart
ystart =options.ystart
zstart =options.zstart
dx = options.dx
dy = options.dy
Nsubx= options.Nsubx
dsubx = options.dsubx
Nsuby= options.Nsuby
dsuby = options.dsuby
y2 = options.y2
x2 = options.x2
theta = options.theta

#logdir = '/reg/neh/operator/cxiopr/cxii8715/'
logdir = ''

import logging
logger = logging.getLogger('shot')
logger.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler(logdir+'logs/square_scan_'+time.strftime('%y%m%d_%H%M%S')+'.log')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

skip_first_column = options.skip_first_column
skip_first_row = options.skip_first_row
goto_new_row = options.goto_new_row

################################################
# use psdata for motors
#cxi = psdata.psdata(epics_live=True, ami=True, noload=True, epics_file='epicsArch_1.txt')

chamber = 'SC1'
use_picker = True

def burst150():
    psioc.get_device('PATT:SYS0:1:MPSBURSTCTRL').VAL = 1

if 'cxi' not in dir():

    if chamber is 'SC1':
        seq_eventCodes = [185,180,181]
        cxi = psdata.psdata(epics_live=True, ami=True, noload=True, epics_file='epicsArch.txt', \
                            instrument='cxi',station=0, proxy_host='daq-cxi-mon01')
        cxi.add_detector('sample', pvs={'x': 'CXI:SC1:MMS:02', 'y': 'CXI:USR:MMS:20', 'z': 'CXI:USR:MMS:22'})
    else:
        seq_eventCodes = [187,180,181]
        cxi = psdata.psdata(epics_live=True, ami=True, noload=True, epics_file='epicsArch_1.txt', \
                            instrument='cxi',station=1, proxy_host='daq-cxi-mon03')
        cxi.add_detector('sample', pvs={'x': 'CXI:SC3:MMS:02', 'y': 'CXI:SC3:MMS:03', 'z': 'CXI:SC3:MMS:04'})

    cxi._default_module_path = '/reg/neh/home1/koglin/src/psdata/'
    # Add pulse picker (automatically uses XRT picker for SC1 and DS1@DSC picker for SC3 based on the instrument:station
    cxi.add_detector('picker', module='pulsepicker')

    # Setup event sequencer
    seq_beam = [1,1,0]
    cxi.picker.sequencer.set_sequence(eventCodes=seq_eventCodes, beam=seq_beam)
    cxi.picker.sequencer.sync_marker.VAL = '30Hz'
    cxi.picker.sequencer.seq_length.VAL = len(seq_eventCodes)

    # Use the pulse picker for bursting -- add to cxi for convenience 
    # in switching to accelerator burst mode if desired
    if use_picker:
        setattr(cxi, 'burst', cxi.picker.burst)
    else:
        setattr(cxi, 'burst', burst150)

    # if no rot then make dummy rot PV that returns rot.VAL = 0
    class rot(object):
        VAL = 0

    if cxi.sample.rot is None:
        setattr(cxi.sample, 'rot', rot())

################################################

##defining the roll angle (if any; default is zero)
if (theta==0.0) and (x2!=-1111.0) and (y2!=-1111.0):
    theta=atan(-(y2-ystart)/(x2-xstart))

###############################################
##### On-line script: to be run at the beamline
###############################################
if options.flag:

    try:
    # *********need to add single shot mode setup***********
        if options.shot_flag:
            print 'Make sure you setup the EVR Sequencer'
    #        xfelburst.fastsetup()

        ##set current position as start position
        ##and reading current value of pitch angle
        if((xstart==-1111.0) and (ystart==-1111.0)):
            print_startup = 1
            xstart,ystart,pitch,zstart1 = cxi.sample.x.RBV, cxi.sample.y.RBV, cxi.sample.rot.VAL, cxi.sample.z.RBV
        else:
            print_startup = 0
            dummy,dummy,pitch,zstart1 = cxi.sample.x.RBV, cxi.sample.y.RBV, cxi.sample.rot.VAL, cxi.sample.z.RBV

        if (zstart==-1111.0):
            zstart=zstart1

        ##pitch = 90-(90-pitch)*180.0/(100*pi)
        #pitch = 65.28 ##25 degrees
        #pitch = 60.25 ##30,0 degrees
        #pitch = 75.25 ##15.0 degrees
        #pitch = 50.4
        #pitch = 85.3 ## 5 deg
        #pitch = 69.9 ## 20.0 degrees

        #    pitch = 19.8
        pitch = 10.0
       # pitch = (pitch - 90.0) ##garth set the vertical position as 0.
        pitch=pitch/180.0*pi
        yrot = ystart
        zrot = zstart
            
        ##logging entered input variables
        a=datetime.now()
        b=time.time()
        of=open(logdir+"logs/commands","a")
        of.write(str(a)+" "+str(time.time())+" square_scan_V04.py"+" --Nx="+str(Nx)+" --Ny="+str(Ny)+" --xstart="+str(xstart)+" --ystart="+str(ystart)+" --dx="+str(dx)+" --dy="+str(dy)+" --Nsubx="+str(Nsubx)+" --dsubx="+str(dsubx)+" --y2="+str(y2)+" --x2="+str(x2)+" --theta="+str(theta)+str('\n'))
        of.close()    

        logger.info(cxi.picker.sequencer.get_sequence())
        logger.info('-'*80)
        logger.info(cxi.sample.epicsLive.epics_table())
        logger.info('-'*80)

        logstr = '{:3} {:3} {:3} {:3} {:>9} {:>9} {:>9} {:>9} {:>9} {:>9} {:>9} {:>9} {:>9} {:>9}'.format( \
                    'jx', 'kx', 'iy', 'my', 'ditime', 'dtime', 'xpos', 'ypos', 'pitch', 'zpos', 'yrot', 'zrot', 'dx', 'dy')
        logger.info(logstr)
        logger.info('-'*80)

        for i in range(0,Ny):
            if (i>0) or (skip_first_row==False):
                tistart = time.time()
                for m in range (0,Nsuby):
                    for j in range(0,Nx):
                        if (j>0) or (skip_first_column==False): 
                            for k in range(0,Nsubx):
                                tstart = time.time()
                                if((i%2)==0):
                                    ##Coordinate transformation from rolled to non-rolled reference frame
                                    xhat=(dx*j+dsubx*k)*cos(theta)+(dy*i+dsuby*m)*sin(theta)
                                    yhat=-(dx*j+dsubx*k)*sin(theta)+(dy*i+dsuby*m)*cos(theta)
                                else:
                                    ##Coordinate transformation from rolled to non-rolled reference frame
                                    xhat=(dx*(Nx-1-j)+dsubx*(Nsubx-1-k))*cos(theta)+(dy*i+dsuby*m)*sin(theta)
                                    yhat=-(dx*(Nx-1-j)+dsubx*(Nsubx-1-k))*sin(theta)+(dy*i+dsuby*m)*cos(theta)

                                #x=xhat+i*0.04
                                x=xhat
                                y=yhat

                                ##If pitch angle is non zero...
                                ##coordinate transformation from pitched to non-pitched reference frame
                                if options.pitchflag==True:   
                                    y=yhat*cos(pitch)
                                    z=(y+ystart-yrot)*sin(pitch)/cos(pitch)
                                    z=z+zrot

                                ##coordinate transformation to motor reference frame
                                x=x+xstart
                                y=y+ystart

                                if (x>=-27.0) and (y<=-70):
                                    print "This coordinate is not accessible\n"
                                    break

    #                            xstatus = 1
    #                            ystatus = 1
    #                            while xstatus != 0:
    #                                xstatus = cxi.sample.x.move(x, wait=True, quiet=True)
    #                                if xstatus != 0:
    #                                    logger.warning('Did not finish X motor move -- retry move to {:}'.format(x))
    #                            
    #                            while ystatus != 0:
    #                                ystatus = cxi.sample.y.move(y, wait=True, quiet=True)
    #                                if ystatus != 0:
    #                                    logger.warning('Did not finish y motor move -- retry move to {:}'.format(y))

#                                    cxi.sample.epicsLive.move(x=x, y=y, wait=True, quiet=True)
                                
                                if abs(y-cxi.sample.y.RBV) > 0.01:
                                    ystatus = 1
                                    while ystatus != 0 or abs(y-cxi.sample.y.RBV) > 0.01:
                                        ystatus = cxi.sample.y.move(y, wait=True, quiet=True)
#                                        if ystatus != 0 or abs(y-cxi.sample.y.RBV) > 0.01:
#                                            logger.warning('Did not finish y motor move -- retry move to {:}'.format(y))
                                
                                if abs(x-cxi.sample.x.RBV) > 0.01:
                                    xstatus = 1
                                    while xstatus != 0 or abs(x-cxi.sample.x.RBV) > 0.01:
                                        xstatus = cxi.sample.x.move(x, wait=True, quiet=True)
#                                        if xstatus != 0 or abs(x-cxi.sample.x.RBV) > 0.01:
#                                            logger.warning('Did not finish X motor move -- retry move to {:}'.format(x))
     
                                if options.pitchflag==True:
                                    zstatus = cxi.sample.z.move(z, wait=True)

                                if options.shot_flag:
                                    time.sleep(0.15)
                                    xnow = cxi.sample.x.RBV
                                    ynow = cxi.sample.y.RBV
#                                    logger.info( '{:3} {:3} {:9.3f} {:9.3f} {:9.4f} {:9.4f} {:9.4f} {:9.4f} {:9.4f} {:9.4f} {:9.4f} {:9.4f}'.format( \
#                                                j, i, time.time()-tistart, time.time()-tstart, xnow, ynow, 
#                                                cxi.sample.rot.VAL, cxi.sample.z.RBV, yrot, zrot, xnow-x, ynow-y) )
                                    cxi.burst()
                                    time.sleep(0.2)
                                    xnow = cxi.sample.x.RBV
                                    ynow = cxi.sample.y.RBV
                                    logger.info( '{:3} {:3} {:3} {:3} {:9.3f} {:9.3f} {:9.4f} {:9.4f} {:9.4f} {:9.4f} {:9.4f} {:9.4f} {:9.4f} {:9.4f}'.format( \
                                                j, k, i, m, time.time()-tistart, time.time()-tstart, xnow, ynow, 
                                                cxi.sample.rot.VAL, cxi.sample.z.RBV, yrot, zrot, xnow-x, ynow-y) )

                                else:  
                                    print "BANG!"

    #                            time.sleep(0.2)
                                tend = time.time()
                                cur_x,cur_y,cur_pitch,cur_z = cxi.sample.x.RBV, cxi.sample.y.RBV, cxi.sample.rot.VAL, cxi.sample.z.RBV
                                
                            # SPHR_START
#                                if options.shot_flag:
    #                                xnow = cxi.sample.x.RBV
    #                                ynow = cxi.sample.y.RBV
    #                                logger.info( '{:3} {:3} {:9.3f} {:9.3f} {:9.4f} {:9.4f} {:9.4f} {:9.4f} {:9.4f} {:9.4f} {:9.4f} {:9.4f}'.format( \
    #                                            j, i, time.time()-tistart, time.time()-tstart, xnow, ynow, 
    #                                            cxi.sample.rot.VAL, cxi.sample.z.RBV, yrot, zrot, xnow-x, ynow-y) )
#                                    logger.info('-'*80)
                        # SPHR_END

        if (goto_new_row==1):
            i=Ny
        j=0
        k=0
        if((i%2)==0):
            ##Coordinate transformation from rolled to non-rolled reference frame
            xhat=(dx*j+dsubx*k)*cos(theta)+(dy*i)*sin(theta)
            yhat=-(dx*j+dsubx*k)*sin(theta)+(dy*i)*cos(theta)
        else:
            ##Coordinate transformation from rolled to non-rolled reference frame
            xhat=(dx*(Nx-1-j)+dsubx*(Nsubx-1-k))*cos(theta)+(dy*i)*sin(theta)
            yhat=-(dx*(Nx-1-j)+dsubx*(Nsubx-1-k))*sin(theta)+(dy*i)*cos(theta)

        x=xhat
        y=yhat

        ##If pitch angle is non zero...
        ##coordinate transformation from pitched to non-pitched reference frame
        if options.pitchflag==True:   
            y=yhat*cos(pitch)
            z=(y+ystart-yrot)*sin(pitch)/cos(pitch)
            z=z+zrot

        ##coordinate transformation to motor reference frame
        x=x+xstart
        y=y+ystart

        if (x>=-27.0) and (y<=-70):
            print "This coordinate is not accessible\n"

        cxi.sample.x.move(x, wait=True, quiet=True)
        cxi.sample.y.move(y, wait=True, quiet=True)
        if options.pitchflag==True:
            cxi.sample.z.move(z, wait=True, quiet=True)

        if (print_startup):
            s = "python square_scan_V04.py"+" --Nx="+str(Nx)+" --Ny="+str(Ny)+" --xstart="+str(xstart)+" --ystart="+str(ystart)+" --dx="+str(dx)+" --dy="+str(dy)+" --Nsubx="+str(Nsubx)+" --dsubx="+str(dsubx)+" --theta="+str(theta)
            if not(options.shot_flag):
                s += " -q"
            s+=str('\n')
            print s

    except KeyboardInterrupt:
        print 'Aborting Scan'

