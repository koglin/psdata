import psdata
from pylab import *

class spectrometer(psdata.Detector):
    """Fee Spectrometer Detector Class of psdata.Detector.
    """

    def __init__(self,*args,**kwargs):
        """Initialize Fee spectrometer as a psdata Detector.
        """
        psdata.Detector.__init__(self,*args,**kwargs)
        self._plot_initialized = False

    @property
    def data_array(self):
        """Use data_array as the common name of an ndarray image.
        """
        return self.data16

    @property
    def projection(self):
        """Spectrometer Projection.
        """
        return self.data_array.sum(axis=0)

    def new_figure(self):
        """Make a new matplotlib figure.
        """
        self._plot_initialized = True
        plt.ion()
        plt.figure()
        plt.suptitle('Spectrometer')
        return

    def plot(self, image=True):
        """Plot Spectrometer Projection.
        """
        if not self._plot_initialized:
            self.new_figure()

        if image:
            if self.data_array is not None:
                plt.imshow(self.data_array)
        else:
            plt.cla()
            if self.projection is not None:
                plt.plot(self.projection)
                plt.draw()
        
        return


