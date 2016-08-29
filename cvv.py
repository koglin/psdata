import psdata
import os

from pylab import *

class Cvv(psdata.Detector):
    """General Camera implementation of Detector Class of psdata.Detector.
    """

    def __init__(self,*args,**kwargs):

        psdata.Detector.__init__(self,*args,**kwargs)
        
        init_params = {'pedestal': 0, 'roi': None}
        self.set_parameter(**init_params)
        
    @property
    def raw_image(self):
        return self.IMAGE.LIVE_IMAGE_FULL.VAL.reshape(self.IMAGE.N_OF_ROW.VAL,
                                                      self.IMAGE.N_OF_COL.VAL)

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
                                name=name, tle=title, local=local, **kwargs)
        
        if stop:
            self.del_psplot(name)





