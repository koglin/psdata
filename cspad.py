import psdata
import os
from glob import glob
from PSCalib.GeometryAccess import *

from pylab import *

#import numpy as np
#import matplotlib.pyplot as plt
#from matplotlib.widgets import Button, Slider
#import matplotlib.patches as plt_patches

quad_colors = ['k', 'g', 'purple', 'b']

class cspad(psdata.Detector):
    """cspad Detector Class of psdata.Detector.
    """

    data_shape = (4, 8, 185, 388)
#    module_attrs = ['data_array','image','geom_path','geom_file']

    def __init__(self,*args,**kwargs):

        psdata.Detector.__init__(self,*args,**kwargs)
        try:
            self.load_geometry(**kwargs)
            self.load_pixel_coord_indexes(**kwargs)
        except:
            print 'Cannot load geometry'

    def load_geometry(self,**kwargs):
        """Load psana geometry data.
        """
        if hasattr(self,'_det'):
            self.src_str = '{detName}.{detId}:{devName}.{devId}'.format(**self._det['det'])
        if 'geom_path' in kwargs:
            self.geom_path = kwargs['geom_path']
        else:
            dir = "/reg/d/psdm/{:}/{:}".format(self._data.instrument,self._data.exp)
            calibfolder = os.listdir(dir+'/calib')
            self.geom_path = '{:}/{:}/{:}/{:}/{:}'.format(dir,'calib',calibfolder[0],
                                                          self.src_str,'geometry')
        
        if 'geom_file' in kwargs:
            self.geom_file = kwargs['geom_file']
        else:
            geom_files = glob(self.geom_path+'/*.data')
            self.geom_file = geom_files[0].rsplit('geometry/')[1]
#            self.geom_file = geom_files[0].lstrip(self.geom_path).lstrip('/')

        try:
            self.geometry = GeometryAccess(self.geom_path+'/'+self.geom_file, 0377)
        except:
            self.geometry = None

#        self.geometry = GeometryAccess(self.geom_file, 0377)

    def load_pedestal(self, **kwargs):
        """Load pedestal data.
        """
        if hasattr(self,'_det'):
            self.src_str = '{detName}.{detId}:{devName}.{devId}'.format(**self._det['det'])
        if 'pedestal_path' in kwargs:
            self.pedestal_path = kwargs['geom_path']
        else:
            dir = "/reg/d/psdm/{:}/{:}".format(self._data.instrument,self._data.exp)
            calibfolder = os.listdir(dir+'/calib')
            self.pedestal_path = '{:}/{:}/{:}/{:}/{:}'.format(dir,'calib',calibfolder[0],
                                                          self.src_str,'pedestal')

        try:
            self.pedestal = None
        except:
            self.pedestal = None

    def load_pixel_coord_indexes(self,xy0_off_pix=(880, 880), **kwargs):
        """Load pixel coordinate indexes into (iX, iY).
        """
        if self.geometry:
            iX, iY = self.geometry.get_pixel_coord_indexes(
                                    xy0_off_pix=xy0_off_pix)         
            self.iX = iX.reshape(self.data_shape)
            self.iY = iY.reshape(self.data_shape)

    @property
    def data_array(self):
        """Put quads data into an array of shape (4, 8, 185, 388).
        """
        data_array = np.empty(self.data_shape, np.int)
        for i in xrange(self.quads_shape[0]):
            quad = self.quads(i).data()
            for j in xrange(8):
                data_array[i,j] = quad[j] 

        return data_array

    @property
    def image(self):
        """Create image from data_array.
        """
        return img_from_pixel_arrays(self.iX,self.iY,W=self.data_array)

    def plot(self):
        """Plot CSpad image.
        """
        plt.imshow(self.image)
        plt.show()

        return

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



