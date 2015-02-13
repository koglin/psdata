import psdata

class evr(psdata.Detector):
    """Evr Class of psdata.Detector.
    """

    def __init__(self,*args,**kwargs):

        psdata.Detector.__init__(self,*args,**kwargs)

    @property
    def eventCodes(self):
        if hasattr(self,'fifoEvents'):
            return [fifo.eventCode() for fifo in self.fifoEvents]
        else:
            return []

    @property
    def timestampsHigh(self):
        if hasattr(self,'fifoEvents'):
            return [fifo.timestampHigh() for fifo in self.fifoEvents]
        else:
            return []

    @property
    def timestampsLow(self):
        if hasattr(self,'fifoEvents'):
            return [fifo.timestampLow() for fifo in self.fifoEvents]
        else:
            return []


