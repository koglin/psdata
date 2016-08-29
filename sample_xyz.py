import psdata
import numpy
import time
class sample_xyz(psdata.Detector):
    """Imp Class of psdata.Detector.
    """

    def __init__(self,*args,**kwargs):

        psdata.Detector.__init__(self,*args,**kwargs)


    def myscan(self,nsteps=1,stepsize=1):
        for i in range(nsteps):
#            self.x.move(stepsize, relative=True,wait=True)
            self.move(stepsize, relative=True,wait=True)
            time.sleep(0.2)
            print 'just moved to', self.x.RBV

    def mscan(self,motor='x',nsteps=1,stepsize=1,wait=True,relative=True):
        for i in range(nsteps):
            val = i
            if relative:
                rbv = getattr(self, motor).RBV
                val += rbv
            print motor, val, rbv
            mdict = {motor: val}
            self.epicsLive.move(wait=wait, **mdict)
            time.sleep(0.2)
            print 'just moved to', self.x.RBV

