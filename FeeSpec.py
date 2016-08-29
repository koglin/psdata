import psdata
import os

from pylab import *

class FeeSpec(psdata.Detector):
    """General Camera implementation of Detector Class of psdata.Detector.
    """

    def __init__(self,*args,**kwargs):

        psdata.Detector.__init__(self,*args,**kwargs)

        cam_dict = {'ArrayData': 'CAMR:FEE1:441:IMAGE2:ArrayData',
                    'ArraySize0_RBV': 'CAMR:FEE1:441:IMAGE2:ArraySize0_RBV', 
                    'ArraySize1_RBV': 'CAMR:FEE1:441:IMAGE2:ArraySize1_RBV'}

        self.add_device(**cam_dict)
        self.set_parameter(nx=self.ArraySize0_RBV.VAL)
        self.set_parameter(ny=self.ArraySize1_RBV.VAL)

    @property
    def image(self):
        """Create image from data_array.
        """
        return self.ArrayData.VAL[0:self.nx*self.ny].reshape(self.ny,self.nx)

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





