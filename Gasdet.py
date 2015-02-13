import psdata

class Gasdet(psdata.Detector):
    """Gas Detector Class of psdata.Detector.
    """

    def __init__(self,*args,**kwargs):

        psdata.Detector.__init__(self,*args,**kwargs)

    @property
    def E(self):
        return (self.f_11_ENRC+self.f_12_ENRC)/2. 


