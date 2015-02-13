import psdata
import os
from glob import glob
from PSCalib.GeometryAccess import *
from PSCalib.SegGeometryCspad2x1V1 import cspad2x1_one as sg

from pylab import *

#import numpy as np
#import matplotlib.pyplot as plt
#from matplotlib.widgets import Button, Slider
#import matplotlib.patches as plt_patches

# https://pswww.slac.stanford.edu/swdoc/releases/ana-current/pyana-ref/html/PSCalib/#module-PSCalib.SegGeometryCspad2x1V1

quad_colors = ['k', 'g', 'purple', 'b']

class cspad2x2(psdata.Detector):
    """cspad2x2 Detector Class of psdata.Detector.

       In this class we use natural matrix notations like in data array 
       (that is different from the DAQ notations where rows and cols are swapped).

        We assume that:
            - 2x1 has 185 rows and 388 columns,
            - X-Y coordinate system origin is in the sensor center,
            - pixel (r,c)=(0,0) is in the top left corner of the matrix, 
              has coordinates (xmin,ymax), as shown below

    """
#    module_attrs = ['data_array','image','geom_path','geom_file']

    def __init__(self,*args,**kwargs):

        psdata.Detector.__init__(self,*args,**kwargs)
#        self.load_geometry(**kwargs)
#        self.load_pixel_coord_indexes(**kwargs)

        self.sg = sg
        self.pedestal = 0.
        self.vmin = -10
        self.vmax = 10
#        sg.print_seg_info(0377)

##        size_arr = sg.size()
#        self.rows     = sg.rows()
#        self.cols     = sg.cols()
#        self.shape    = sg.shape()
##        pix_size = pixel_scale_size()
#
#        self.area  = sg.pixel_area_array()
#        self.mask = sg.pixel_mask_array(mbits=0377)
#        # where mbits = +1-edges, +2-wide pixels, +4-non-bounded pixels, +8-neighbours of non-bounded
#
#        sizeX = sg.pixel_size_array('X')
#        sizeX, sizeY, sizeZ = sg.pixel_size_array()
#
#        X     = sg.pixel_coord_array('X')
#        X,Y,Z = sg.pixel_coord_array()
#        print 'X.shape =', X.shape
#
#        xmin, ymin, zmin = sg.pixel_coord_min()
#        xmax, ymax, zmax = sg.pixel_coord_max()
#        xmin = sg.pixel_coord_min('X')
#        ymax = sg.pixel_coord_max('Y')
#
#
#    def load_geometry(self,**kwargs):
#        """Load psana geometry data.
#        """
#        if hasattr(self,'_det'):
#            self.src_str = '{detName}.{detId}:{devName}.{devId}'.format(**self._det['det'])
#        if 'geom_path' in kwargs:
#            self.geom_path = kwargs['geom_path']
#        else:
#            dir = "/reg/d/psdm/{:}/{:}".format(self._data.instrument,self._data.exp)
#            calibfolder = os.listdir(dir+'/calib')
#            self.geom_path = '{:}/{:}/{:}/{:}/{:}'.format(dir,'calib',calibfolder[0],
#                                                          self.src_str,'geometry')
#        
#        if 'geom_file' in kwargs:
#            self.geom_file = kwargs['geom_file']
#        else:
#            geom_files = glob(self.geom_path+'/*.data')
#            self.geom_file = geom_files[0].lstrip(self.geom_path).lstrip('/')
#
#        print self.geom_path
#        print self.geom_file
#        self.geometry = GeometryAccess(self.geom_path+'/'+self.geom_file, 0377)
##        self.geometry = GeometryAccess(self.geom_file, 0377)
#
#    def load_pixel_coord_indexes(self,xy0_off_pix=(1000, 1000), **kwargs):
#        """Load pixel coordinate indexes into (iX, iY).
#        """
#        iX, iY = self.geometry.get_pixel_coord_indexes(
#                                xy0_off_pix=xy0_off_pix)         
#        
#        self.iX = iX.reshape(self.data_shape)
#        self.iY = iY.reshape(self.data_shape)


# global method for rotation of numpy arrays:
#Xrot, Yrot = rotation(X, Y, C, S)

    @property
    def data_array(self):
        """Put 2x2 Cspad data into data_array .
        """
        return self.data - self.pedestal

    @property
    def image(self):
        """Create image from data_array.
        """
        return self.data_array.reshape(370,388)
#        return img_from_pixel_arrays(self.iX,self.iY,W=self.data_array)

    def make_pedestal(self,nevents=1000):
        self.pedestal = self.data*0.
        print 'Recording Pedestal for {:} with {:} Events'.format(self.desc, nevents)
        ievent = 0
        iempty = 0
        while ievent < nevents:
            self._data.next_event()
            if self.data is not None:
                self.pedestal += self.data
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




