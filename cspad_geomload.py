import psdata
import os
from glob import glob

import psana
from Detector.PyDetector import PyDetector

from PSCalib.GeometryAccess import GeometryAccess, img_from_pixel_arrays

from pylab import *
import numpy as np

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
        self.vmin = -50
        self.vmax = 50
        self.zoffset = 555.

#        self.doPedestals = 'yes'
#        self.doPixelStatus = 'no'
#        self.doCommonMode = 'no'

#        self.set_cfg()

#        try:
#            self.load_geometry(**kwargs)
#            self.load_pixel_coord_indexes(**kwargs)
#            self.load_pixel_coords(**kwargs)
#        except:
#            print 'Cannot load geometry'

#    def set_cfg(self, calibrated=True, reconstructed=True, peak_finder=False, **kwargs):
#        """Set psana cfg configuration with python dictionary 
#        """
#        if calibrated:
#            self.add_psana_options( { 
#                'cspad_mod.CsPadCalib': {
#                        'inputKey': '', 
#                        'outputKey': 'calibrated',
#                        'doPedestals': self.doPedestals,
#                        'doPixelStatus': self.doPixelStatus,
#                        'doCommonMode': self.doCommonMode}
#                } )
#
#        if reconstructed:
#            self.add_psana_options( { 
#                'CSPadPixCoords.CSPadImageProducer': {
#                        'source': '{:}'.format(self.src),
#                        'typeGroupName': 'CsPad::CalibV1',
#                        'key': 'calibrated',
#                        'imgkey': 'reconstructed',
#                        'tiltIsApplied': True,
#                        'print_bits': 0},
#                } )
#
#        if peak_finder:
#            self.add_psana_options( {
#                'ImgAlgos.CSPadArrPeakFinder': {
#                        'source':              '{:}'.format(self.src),
#                        'key':                 'calibrated',
#                        'key_peaks_out':       'peaks_out',
#                        'key_peaks_nda':       'peaks_nda',
#                        'rmin':                kwargs.get('rmin', 8),
#                        'dr':                  kwargs.get('dr', 1),
#                        'SoNThr_noise':        3,
#                        'SoNThr_signal':       4,
#                        'frac_noisy_imgs':     0.9,
#                        'peak_npix_min':       3,
#                        'peak_npix_max':       500,
#                        'peak_amp_tot_thr':    0.,
#                        'peak_SoN_thr':        5.,
#                        'event_npeak_min':     1,
#                        'event_npeak_max':     1000,
#                        'event_amp_tot_thr':   0.,
#                        'nevents_mask_update': 0,
#                        'nevents_mask_accum':  50,
#                        'selection_mode':      'SELECTION_ON',
#                        'out_file_bits':       15,
#                        'print_bits':          3681,},
#                'pyimgalgos.ex_peaks_nda': {
#                         'source':         '{:}'.format(self.src),
#                         'key_in':         'peaks_nda',
#                         'print_bits':     255},
#                } )
#
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
            self.load_pixel_coord_indexes(**kwargs)
            self.load_pixel_coords(**kwargs)
        except:
            self.geometry = None

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

    def load_pixel_coords(self, **kwargs):
        if self.geometry:
            self.pixel_coords = np.array(self.geometry.get_pixel_coords())
            self.xdata = self.pixel_coords[0].reshape(self.data_shape)
            self.ydata = self.pixel_coords[1].reshape(self.data_shape)
            self.zdata = self.pixel_coords[2].reshape(self.data_shape) \
                    -1000000.+1000.*self.z_calibrated
            self.rdata = np.sqrt(self.xdata**2+self.ydata**2)
            self.phidata = np.arctan2(self.rdata, self.zdata)
            self.thetadata = np.arctan2(self.ydata, self.xdata)
            phiapprox = np.arctan2(self.rdata, 1000.*self.z_calibrated)
            self.pixel_error_phi_approx = (self.zdata*(self.phidata-phiapprox)) 

    @property
    def z_calibrated(self):
        return self.zoffset - self.z.value

    def quads_array(self, attr=None):
        """Flatten the data with the given attr name.
        """
        if attr:
            qfunc = getattr(self, attr)
        else:
            qfunc = None

        if qfunc is None:
            attr = 'quads'
            qfunc = self
            quads_shape = getattr(qfunc, 'quads_shape')
        else:
            quads_shape = getattr(qfunc, 'quads_shape')()
        
        quads = getattr(qfunc, 'quads')
        data_array = np.empty(self.data_shape, np.int)
        for i in xrange(quads_shape[0]):
            quad = quads(i).data()
            for j in xrange(8):
                data_array[i,j] = quad[j] 

        return data_array

    @property
    def data_array(self):
        """Cspad data array of shape (4, 8, 185, 388).
           Use calibrated data if available
        """
        return self.quads_array(attr='calibrated')

    def make_hist(self, bins=arange(400)*30):
        """Make histogram of CSpad.
        """
        self.yhist, self.xhist =  np.histogram(self.data_array, bins=bins)

    def make_image(self, data=None, iX=None, iY=None):
        """Make an image from data and iX,iY coordinates.
        """
        if not data:
            data = self.data_array

        if not iX:
            if not iX:
                self.load_geometry()

            iX = self.iX

        if not iY:
            iY = self.iY

        image = img_from_pixel_arrays(iX, iY, W=data)

        return image


    @property
    def image(self):
        """Create image from data_array.
        """
        if hasattr(self,'reconstructed'):
            image = np.array(self.reconstructed)
        else:
            image = None
       
        if not image:
            image = self.get_image()

#        klow = image < self.vmin
#        khigh = image > self.vmax 
#        image[klow] = self.vmin
#        image[khigh] = self.vmax
        return image

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
                start=True, stop=False, **kwargs):
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
                            name=name, title=title, local=True)
        
        if stop:
            self.del_psplot(name)



#                'ImgAlgos.ImgPeakFinder': { 
#                        'source': '{:}'.format(self.src),
##                        'key': 'reconstructed',
#                        'key': 'calibrated',
#                        'peaksKey': 'peaks',
#                        'threshold_low': 2,
#                        'threshold_high': 5,
#                        'sigma': 1.5,
#                        'smear_radius': 5,
#                        'peak_radius': 7,
#                        'xmin': 20,
#                        'xmax': 1700,
#                        'ymin': 20,
#                        'ymax': 1700,
##                        'testEvent': 5,
#                        'print_bits': 3,
##                        'finderIsOn': True,
#                        },
#                'ImgAlgos.ImgPeakFilter': { 
#                        'source':          '{:}'.format(self.src),
#                        'key':             'peaks',
#                        'threshold_peak':  5,
#                        'threshold_total': 0,
#                        'n_peaks_min':     10,
#                        'print_bits':      11,
#                        'fname':           'cspad-img',
#                        'selection_mode':  'SELECTION_ON'},

