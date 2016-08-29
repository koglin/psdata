import psdata
import os

from pylab import *

class Questar(psdata.Detector):
    """Questar Camera - Detector Class of psdata.Detector.
       Typically either an Opal2k, Opal4k or Questar.
    """

    _use_ami = False

    def __init__(self,*args,**kwargs):

        psdata.Detector.__init__(self,*args,**kwargs)
        
        self._properties = {'pedestal': 0, 'roi': None}
        self.set_properties(**self._properties)
        
    def set_properties(self, **kwargs):
        for prop, default in kwargs.items():
            if prop in self._det:
                setattr(self, prop, self._det[prop])
            else:
                setattr(self, prop, default)

    @property
    def raw_image(self):
        """Raw image -- currently supporting psana data16.
           This could in the future be updated to take other types of data
           including epics.
        """
        if self._use_ami:
            return self.ami.data /self.ami.entries
        else:
            if self.data16.any():
                return self.data16
            else:
                return self.data8

    @property
    def calibrated_image(self):
        """Create calibrated_image.
        """
        return self.raw_image - self.pedestal 

    @property
    def image(self):
        """Create image from data_array.
        """
        if self.roi and len(self.roi) == 4:
            return self.calibrated_image[self.roi[0]:self.roi[1],self.roi[2]:self.roi[3]]
        else:
            return self.calibrated_image

    @property
    def xprojection(self):
        """X projection of image.
        """
        return self.image.sum(axis=1)
    
    @property
    def yprojection(self):
        """X projection of image.
        """
        return self.image.sum(axis=0)

    def make_pedestal(self,nevents=1000):
        self.pedestal = self.raw_image*0.
        print 'Recording Pedestal for {:} with {:} Events'.format(self.desc, nevents)
        ievent = 0
        iempty = 0
        while ievent < nevents:
            self._data.next_event()
            if self.raw_image is not None:
                self.pedestal += self.raw_image
                ievent += 1
                if ievent % 100 == 0:
                    print '{:6.1f}% Complete'.format(ievent*100./float(nevents))
            else:
                iempty += 1
                if iempty % 100 == 0:
                    print '{:} out of {:} events empty'.format(iempty,ievent)

        self.pedestal /= float(nevents)

    def new_plot(self, **kwargs):
        plt.ion()
        plt.imshow(self.image)
        plt.clim(**kwargs)
        plt.colorbar()
        plt.title(self.desc)

    def plot(self, nevents=1, projection=False, monitor=False, next_event=False):
        """Plot CSpad image.
        """
        ievent = 0
        try:
            plt.ion()
            plt.show()
            while ievent < nevents or monitor:
                if ievent > 0 or next_event or monitor:
                    self._data.next_event()
                
                if projection:
                    if projection in ['y', 'yprojection', 'Y']:
                        plotdata = self.yprojection
                    else:
                        plotdata = self.xprojection
                    
                    plt.plot(plotdata)
                
                else:
                    plt.imshow(self.image)
                
                plt.draw()
                ievent += 1
        except KeyboardInterrupt:
            pass
    
    def publish(self, name=None, title=None,
                projection=None, 
                start=True, stop=False, local=True, **kwargs):
        """Publish plot with psmon.
           Plot can be read on multiple machines with psplot.
        """
        if projection:
            if projection is 'y':
                plotdata = 'yprojection'
            else:
                plotdata = 'xprojection'
            
            if not name:
                name = self._name+'_'+plotdata
            
            if not title:
                if self._desc:
                    title = self._desc+' '+plotdata
                else:
                    title = self._name+' '+plotdata

        else:
            if not name:
                name = self._name+'_image'
            
            if not title:
                if self._desc:
                    title = self._desc
                else:
                    title = self._name

        if start:
            if projection:
                self.add_psplot(plotdata, plot_type='XYplot', 
                                name=name, title=title, local=local, **kwargs)
            
            else:
                self.add_psplot('image', plot_type='Image', 
                                name=name, title=title, local=local, **kwargs)
        
        if stop:
            self.del_psplot(name)


