import psdata
import os
#from glob import glob
#from PSCalib.GeometryAccess import *

from pylab import *

#import numpy as np
#import matplotlib.pyplot as plt
#from matplotlib.widgets import Button, Slider
#import matplotlib.patches as plt_patches

quad_colors = ['k', 'g', 'purple', 'b']

class epix100(psdata.Detector):
    """cspad Detector Class of psdata.Detector.
    """

    def __init__(self,*args,**kwargs):

        psdata.Detector.__init__(self,*args,**kwargs)
        self.pedestal = 0
        self.vmin = -50
        self.vmax = 50

    @property
    def data_array(self):
        """Create image from data_array.
        """
        return self.frame - self.pedestal 

    @property
    def image(self):
        """Create image from data_array.
        """
        return self.data_array[352:,384:] 

    def make_pedestal(self,nevents=1000):
        self.pedestal = self.frame*0.
        print 'Recording Pedestal for {:} with {:} Events'.format(self.desc, nevents)
        ievent = 0
        iempty = 0
        while ievent < nevents:
            self._data.next_event()
            if self.frame is not None:
                self.pedestal += self.frame
                ievent += 1
                if ievent % 100 == 0:
                    print '{:6.1f}% Complete'.format(ievent*100./float(nevents))
            else:
                iempty += 1
                if iempty % 100 == 0:
                    print '{:} out of {:} events empty'.format(iempty,ievent)

        self.pedestal /= float(nevents)

    def new_plot(self):
        plt.ion()
        plt.imshow(self.image)
        plt.clim(vmin=self.vmin,vmax=self.vmax)
        plt.colorbar()
        plt.title(self.desc)

    def plot(self, nevents=1, monitor=False, next_event=False):
        """Plot CSpad image.
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


