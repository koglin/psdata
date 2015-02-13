import psdata
import os

from pylab import *
from xtcav.GenerateDarkBackground import *
from xtcav.GenerateLasingOffReference import *
from xtcav.ShotToShotCharacterization import *

#import numpy as np
#import matplotlib.pyplot as plt
#from matplotlib.widgets import Button, Slider
#import matplotlib.patches as plt_patches

class xtcav_det(psdata.Detector):
    """xtcav Detector Class of psdata.Detector.

       XTCAV is a detector that is used to determine the laser-power vs. time of each LCLS shot.  
       Alvaro Sanchez-Gonzalez has written psana-python code to do the rather complex analysis 
       of images from the XTCAV camera to determine these quantities.

       Two things must be done before XTCAV analysis will function: 
          1) A "dark run" must be analyzed to get the pedestal values for cameras, 
          2) A "no lasing" run must be analyzed to generate sets of "no lasing" images 
             (quite a complex process).

       How Often to Take a Lasing Off Run  (courtesy of Tim Maxwell):
          "For very stable accelerator conditions, you might not really need to but 
          every hour or two. But, for example with that AMO experiment it drifted 
          measurably over as short as twenty minutes as the beam was a trick setup 
          and some feedbacks needed disabling.  There's not really a hard, fast rule here. 
          When necessary or when time allows has been the practical answer so far."

       See Confluence page:
         https://confluence.slac.stanford.edu/display/PSDM/XTCAV+Analysis
    """

    def __init__(self,*args,**kwargs):

        psdata.Detector.__init__(self,*args,**kwargs)
        self.pedestal = 0
        self.vmin = -50
        self.vmax = 50
        XTCAVRetrieval=ShotToShotCharacterization()
        XTCAVRetrieval._datasource = self._data.ds
        XTCAVRetrieval._datasourceinfo = False
        self.XTCAVRetrieval = XTCAVRetrieval
        self.add_event_function('_retrieve_event_for_processing')

    def _retrieve_event_for_processing(self):
        """The XTCAV code already has an event retrieval function built in.
           Use this instead of accessing the event data through psdata.
        """
        self.XTCAVRetrieval.SetCurrentEvent(self._data.evt)

    def make_dark_background(self, runs, exp=None, 
                             maxshots=150, validity_range=None, **kwargs):
        """Analyze a "dark run" to get the pedestal values for cameras.
        """
        if not exp:
            exp = self._data.exp
        
        if not validity_range:
            validity_range = (85, 109)
            print 'Using default validity range of', validity_range
        
        GDB = GenerateDarkBackground()
        GDB.experiment = exp
        GDB.runs = runs
        GDB.maxshots = maxshots
        GDB.SetValidityRange(validity_range)
        GDB.Generate()
        self.Background = DGB
        
    def make_lasing_off_reference(self, runs, exp=None, 
                                  maxshots=150, validity_range=None,
                                  nb=1, groupsize=5, **kwargs):
        """Analyze a "dark run" to get the pedestal values for cameras.
        """
        if not exp:
            exp = self._data.exp
        
        if not validity_range:
            validity_range = (85, 109)
            print 'Using default validity range of', validity_range

        GLOC=GenerateLasingOffReference()
        GLOC.experiment = exp
        GLOC.runs = runs
        GLOC.maxshots = maxshots
        GLOC.SetValidityRange(validity_range)
        GLOC.nb=1
        GLOC.groupsize=5
        GLOC.Generate()
        self.LasingOff = GLOC

    @property
    def image(self):
        """Create image from data16.
        """
        if isinstance(self.data16, ndarray):
            return self.data16[425:675,475:725]
        else:
            return np.zeros([250,250])

    def new_plot(self):
        plt.ion()
        plt.imshow(self.image)
        plt.clim(vmin=self.vmin,vmax=self.vmax)
        plt.colorbar()
        plt.title(self.desc)

    def plot(self, nevents=1, monitor=False, next_event=False):
        """Plot XTCAV image.
        """
        ievent = 0
        try:
            plt.ion()
            plt.show()
            while ievent < nevents or monitor:
                if ievent > 0 or next_event or monitor:
                    self._data.next_event()
                plt.imshow(self.image)
                plt.draw()
                ievent += 1
        except KeyboardInterrupt:
            pass

    def publish(self, name=None, title=None, 
                start=True, stop=False):
        """Publish plot with psmon.
           Plot can be read on multiple machines with psplot.
        """
        if not name:
            name = self._name
        if not title:
            title = self._desc
        if not title:
            title = self._name

        if start:
            self.add_psplot('image', plot_type='Image', 
                            name=name, title=title)
        
        if stop:
            self.del_psplot(name)




