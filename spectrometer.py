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
        return self.hproj

    def new_figure(self):
        """Make a new matplotlib figure.
        """
        self._plot_initialized = True
        plt.ion()
        plt.figure()
        return

    def plot(self, init=False, image=False, title='Spectrometer'):
        """Plot Spectrometer Projection.
        """
        if init or not self._plot_initialized:
            self.new_figure()
            self.add_event_function('plot', image=image, title=title)

        if image:
            if self.data_array is not None:
                plt.imshow(self.data_array)
        else:
            plt.cla()
            if self.projection is not None:
                plt.plot(self.projection)
                plt.draw()
                plt.suptitle(self._data.event_info)
                plt.title(title)
        
        return

    def publish(self, name=None, title=None,
                start=True, stop=False, **kwargs):
        """Publish plot with psmon.
           Plot can be read on multiple machines with psplot.
        """
        plotdata = 'hproj' 
           
        if not title:
            if self._desc:
                title = self._desc
            else:
                title = self._name

        if start:
            self.add_psplot(plotdata, plot_type='XYplot', 
                                name=name, title=title, **kwargs)
            
        if stop:
            self.del_psplot(name)


