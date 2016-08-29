
#psana -m EventKeys -n 1 exp=sxri0414:run=55
#mpirun -n 2 python batch_timetoolbykick_i0414.py 53

#to run from ffb (need to change the DataSource line below)
#bsub -a mympi -q psnehq -n 24 -o %J.log python batch_timetoolbykick_i0414.py 53

#to run from offline (need to change the DataSource line below)
#bsub -a mympi -q psanaq -n 8 -R "span[ptile=1]" -o %J.log python batch_timetoolbykick_i0414.py 53

import sys
import psana
import math
import IPython
import numpy as np

from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

# this script runs the timetool on sxr data 
# where laser is off during bykick, and laser is always on for 
# every other shot

EVR_BYKICK = 162
put_key = 'TTANA'
ref_avg_fraction = 0.60
#opalSrcStr = 'TSS_OPAL'
opalSrcStr  ='DetInfo(SxrBeamline.0:Opal1000.0)'

wf_Sum = np.zeros(20000)
wf_Peak = np.zeros(1)

TTSpixeltotimecal = 0.0033444
acqNofsamples = 20000
acqsampleT = 5*10^(-10)

print "00000000000000000000000"

options = {'psana.modules':'TimeTool.Analyze',

           ####################################
           # Below are the TimeTool.Analyze options - copied from TimeTool/data/sxr_timetool.cfg

           #  Key for fetching timetool camera image
           'TimeTool.Analyze.get_key':opalSrcStr,
           #  Results are written to <put_key>
           'TimeTool.Analyze.put_key':put_key,
           #  Indicate absence of beam for updating reference
           'TimeTool.Analyze.eventcode_nobeam':EVR_BYKICK,
           #  Indicate events to skip (no laser, for example)
           'TimeTool.Analyze.eventcode_skip':0,
           #  Polynomial coefficients for position_time calculation
           'TimeTool.Analyze.calib_poly':'0 1 0',
           #  Project onto X axis?
           'TimeTool.Analyze.projectX':True,
           #  Minimum required bin value of projected data
           'TimeTool.Analyze.proj_cut':0,
           #  ROI (x) for signal
           'TimeTool.Analyze.sig_roi_x':'0 1023',
           #  ROI (y) for signal
           #'TimeTool.Analyze.sig_roi_y':'408 920',
           'TimeTool.Analyze.sig_roi_y':'400 650', 
           #  ROI (x) for sideband
           'TimeTool.Analyze.sb_roi_x':'' ,
           #  ROI (y) for sideband
           'TimeTool.Analyze.sb_roi_y':'', 
           #  Rolling average convergence factor (1/Nevents)
           'TimeTool.Analyze.sb_avg_fraction':0.0,
           #  Rolling average convergence factor (1/Nevents)
           'TimeTool.Analyze.ref_avg_fraction':ref_avg_fraction,
           #  Read weights from a text file
           'TimeTool.Analyze.weights_file':'',
           #  Indicate presence of beam from IpmFexV1::sum() [monochromator]
           'TimeTool.Analyze.ipm_get_key':'',
#           'TimeTool.Analyze.ipm_beam_threshold':'',
           #  Load initial reference from file
           'TimeTool.Analyze.ref_load':'',
           #  Save final reference to file
           'TimeTool.Analyze.ref_store':'timetool.ref',
           #  Generate histograms for initial events
           #'TimeTool.Analyze.dump':20,
           #  Filter weights
           'TimeTool.Analyze.weights':'0.00940119 -0.00359135 -0.01681714 -0.03046231 -0.04553042 -0.06090473 -0.07645332 -0.09188818 -0.10765874 -0.1158105  -0.10755824 -0.09916765 -0.09032289 -0.08058788 -0.0705904  -0.06022352 -0.05040479 -0.04144206 -0.03426838 -0.02688114 -0.0215419  -0.01685951 -0.01215143 -0.00853327 -0.00563934 -0.00109415  0.00262359  0.00584445  0.00910484  0.01416929  0.0184887   0.02284319  0.02976289  0.03677404  0.04431778  0.05415214  0.06436626  0.07429347  0.08364909  0.09269116  0.10163601  0.10940983  0.10899065  0.10079016  0.08416471  0.06855799  0.05286105  0.03735241  0.02294275  0.00853613',
          }
      
try:
    run = int(sys.argv[-1])
except:
    print "ERROR: You did not give a run for arg 1. Good runs: 138, 144, 157, 158"
    sys.exit(0)


psana.setOptions(options)
# to run from the offline using psanaq
ds = psana.DataSource('exp=sxri0414:run=%d:idx'%run)
# to run from FFB using psnehq
#ds = psana.DataSource('dir=/reg/d/ffb/sxr/sxri0414/xtc:exp=sxri0414:run=%d:idx'%run)
evrSrc = psana.Source('DetInfo(NoDetector.0:Evr.0)')
epics = ds.env().epicsStore()

opalSrc = psana.Source(opalSrcStr)
lastByKick = 0
ourOwnRef = None

acqsrc  = psana.Source('DetInfo(SxrEndstation.0:Acqiris.2)')
gmdsrc  = psana.Source('BldInfo(GMD)')


import math
class histaxis:
    def __init__(self,nbin,low,high):
        self.low = low
        self.high = high
        self.nbin = nbin
        self.binsize = (high-low)/float(nbin)
    def bin(self,val):
        return int(math.floor((val-self.low)/self.binsize))

class hist1d:
    def __init__(self,nbinx,xlow,xhigh):
        self.data = np.zeros(nbinx)
        self.nbinx = nbinx
        self.xaxis = histaxis(nbinx,xlow,xhigh)
    def fill(self,xval,weight=1.0):
        xbin=self.xaxis.bin(xval)
        if xbin>=0 and xbin<self.xaxis.nbin:
            self.data[xbin] += weight

class hist2d:
    def __init__(self,xlow,xhigh,nbinx,ylow,yhigh,nbiny):
        self.data = np.zeros((nbinx,nbiny))
        self.xaxis = histaxis(xlow,xhigh,nbinx)
        self.yaxis = histaxis(ylow,yhigh,nbiny)
    def fill(self,xval,yval,weight=1.0):
        xbin=self.xaxis.bin(xval)
        ybin=self.yaxis.bin(yval)
        if xbin>=0 and xbin<self.xaxis.nbin and ybin>=0 and ybin<self.yaxis.nbin:
            self.data[xbin,ybin] = self.data[xbin,ybin]+weight

TTSedgeposhist= hist1d(1024,0,1024)
poshist   = hist1d(1000,300,400)
intsignal = hist1d(1024,0,1024)
apdsignal = hist1d(100,320,360)
apdsignal_unc = hist1d(100,320,360)
apdcount = hist1d(100,320,360)
apdsignalN = hist1d(100,320,360)
apdcountN = hist1d(100,320,360)
apdtimescat2Dhist= hist2d(240, 330, 360, 1024, 0, 20480)
apdgmd = hist1d(100,0,7e+10)
apdgmdcount = hist1d(100,0,7e+10)

gmd_val=0

if rank==0:
    from psmon import publish
    from psmon.plots import XYPlot,Image
    publish.init()

dsrun = ds.runs().next()
times = dsrun.times()
mylength = len(times)/size
# this line selects a subset of events, so each
# cpu-core ("rank") works on a separate set of events
mytimes= times[rank*mylength:(rank+1)*mylength]

print "1111111111111111"

for ii in range(mylength):
    evt = dsrun.event(mytimes[ii])

    evr = evt.get(psana.EvrData.DataV3, evrSrc)
    if evr is None: continue
    evrCodes = [fifoEvent.eventCode() for fifoEvent in evr.fifoEvents()]
    evrCodes.sort()

    frame = evt.get(psana.Camera.FrameV1, opalSrc)
    acq   = evt.get(psana.Acqiris.DataDescV1,acqsrc)
    gmd   = evt.get(psana.Bld.BldDataGMDV2,gmdsrc) 

    #plotReference(np.array(frame.data16(), dtype=np.float))

    if (acq is None) : continue
    #else : print "!!!!!!!!!!!!Found acquiris!!!!!!!!!!!!!"
    
    if frame is None: continue

    if gmd is None: continue 
        
    aldelaypos =  epics.value('SXR:LAS:MCN1:08.RBV')    
    gmd_val = gmd.relativeEnergyPerPulse()
    apd_gmd_cal = 1997+232.9*(gmd_val*200/(7e+10))-1.365*(gmd_val*200/(7e+10))**2+0.004287*(gmd_val*200/(7e+10))**3

       
    #print "%18.10f:" % ii, gmd_val/40000000000
    if (gmd_val<0): print "!!!!!!!!!!!!!!!!Negative!!!!!!!!!!!!!!!!!", ii,rank
    if (gmd_val<0): continue
    if (gmd_val<4000000000) or (gmd_val>40000000000): continue
    
    acqnumchannels = acq.data_shape()
    chan = 0
    wf = acq.data(chan).waveforms()[0]
    wf_Sum += wf

    #Now the integral of the signal
    acqbaseline = wf[0:4850]
    #acqpeak = wf[9000:15000]
    acqpeak = wf[4850:20000]
    acqsignal = acqbaseline.sum()/float(acqbaseline.size)/float(acqpeak.size)-acqpeak.sum()

    if (ourOwnRef is None): ourOwnRef = np.array(frame.data16(),dtype=np.float)

    #Now Normalize by GMD value

    acqsignalSmall = acqsignal/apd_gmd_cal 
    acqsignalSmall_unc = acqsignal/10000
  
    #print "%18.10f:" % gmd_val, acqsignal, acqsignalSmall
    
    #plotAcq(wf,0,20000)
    #plotAcqInt(wf_Sum,0,20000)
    #acqbaseline = wf[5000:8600]
    #acqpeak = wf[9550:18000]
    #acqsignal = acqpeak.sum()-acqbaseline.sum()/float(acqbaseline.size)/float(acqpeak.size)
    #DiodeValues.append(acqsignal)
    #wf_Peak += acqsignal  
  
    timetool = evt.get(psana.TimeTool.DataV2, put_key)
    #print (timetool is None)
    #print (ourOwnRef is None)
    if EVR_BYKICK in evrCodes:
        if ourOwnRef is None:
            ourOwnRef = np.array(frame.data16(),dtype=np.float)
        else:
            ourOwnRef = ref_avg_fraction * np.array(frame.data16(),dtype=np.float) + (1.0-ref_avg_fraction)*ourOwnRef
            #ourOwnRef = np.array(frame.data16(),dtype=np.float)
        #print "##### FOUND BACKGROUND ###########"
        #print "### EVENT %4d BYKICK (last one %4d ago) ### evr codes: %s" % (ii, ii-lastByKick, ','.join(map(str,evrCodes)))
        #plotReference(np.array(frame.data16(), dtype=np.float))
        #print "!!!!!!!!!!!!!!Gets Here !!!!!!!!!!!!!!!!!!!"
        lastByKick=ii       
    if (timetool is not None) and (ourOwnRef is not None):
        #print "### EVENT %d TIMETOOL RES: ampl=%f posintsignal_pixel=%f" % (ii, timetool.amplitude(), timetool.position_pixel())
        #plotEvent(np.array(frame.data16(), dtype=np.float), 
        #          ourOwnRef, 
        #          timetool.position_pixel())
        TTSedgeposhist.fill(timetool.position_pixel(),1)
        corrdelaypos=(aldelaypos/0.15) + timetool.position_pixel()*TTSpixeltotimecal
        corrdelayneg=(aldelaypos/0.15) - timetool.position_pixel()*TTSpixeltotimecal
        #corrdelaypos=(valdelaypos/0.15) 
        #print "!!!!!!!!!!!!!!Gets Here !!!!!!!!!!!!!!!!!!!"
        #print "%18.10f:" % gmd_val, acqsignal, acqsignalSmall, valdelaypos
        #print corrdelaypos, gmd_val, apd_gmd_cal, acqsignal, acqsignalSmall

        poshist.fill(corrdelaypos)
        TTSedgeposhist.fill(timetool.position_pixel())        
        intsignal.fill(acqsignalSmall)
        apdtimescat2Dhist.fill(corrdelaypos,acqsignalSmall)
        apdsignal.fill(corrdelaypos,acqsignalSmall)
        apdsignal_unc.fill(corrdelaypos,acqsignalSmall_unc)
        apdcount.fill(corrdelaypos,1.0)
        apdsignalN.fill(corrdelayneg,acqsignalSmall)
        apdcountN.fill(corrdelayneg,1.0)
        apdgmd.fill(gmd_val,acqsignalSmall_unc)
        apdgmdcount.fill(gmd_val,1.0)
        
        
        #print "%18.10f:" % corrdelaypos
        
        #poshist.Draw()

        
    if ii % 100 == 0:
        #plothist1d(poshist,6)
        #plothist1d(TTSedgeposhist,7)
        #plothist2d(apdtimescat2Dhist,8)
        if rank==0:
            #ax = range(0,len(apdsignal.data))
            ax = np.linspace(apdsignal.xaxis.low,apdsignal.xaxis.high,apdsignal.nbinx)
            scan = XYPlot(ii, "Motor Scan", ax, np.divide(apdsignal.data,apdcount.data))
            publish.send("SCAN", scan)

signalall = np.empty_like(apdsignal.data)
comm.Reduce(apdsignal.data,signalall)
countall = np.empty_like(apdcount.data)
comm.Reduce(apdcount.data,countall)

signalall_unc = np.empty_like(apdsignal_unc.data)
comm.Reduce(apdsignal_unc.data,signalall_unc)

signalallN = np.empty_like(apdsignalN.data)
comm.Reduce(apdsignalN.data,signalallN)
countallN = np.empty_like(apdcountN.data)
comm.Reduce(apdcountN.data,countallN)

apdgmdall = np.empty_like(apdgmd.data)
comm.Reduce(apdgmd.data,apdgmdall)
gmdcountall = np.empty_like(apdgmdcount.data)
comm.Reduce(apdgmdcount.data,gmdcountall)



print "before creates file"

if rank==0:
    ax = np.linspace(apdsignal.xaxis.low,apdsignal.xaxis.high,apdsignal.nbinx)
    gmdax = np.linspace(apdgmd.xaxis.low,apdgmd.xaxis.high,apdgmd.nbinx)
    np.savez('run%s_mpi'%run,signalall,countall,ax,signalallN,countallN,ax,signalall_unc,countall,ax,apdgmdall,gmdcountall,gmdax)
