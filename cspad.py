import psdata
import os
from glob import glob

import psana
from ImgAlgos.PyAlgos import PyAlgos

from pylab import *
import numpy as np

# These need updating
_zoffset_defaults = {
        'DsaCsPad': 555.,
        'DscCsPad': 555.,
        'DsdCsPad': 2000.,
        }

_algos_keys = ['windows', 'mask', 'pbits']
_peak_keys = ['npix_min', 'npix_max', 'amax_thr', 'atot_thr', 'son_min']

class cspad(psdata.Detector):
    """cspad Detector Class of psdata.Detector.
    """

    _default_params = {
            'thr_saturated': 10000.,
            'thr_hit': 500, 
            'thr_low': 5,
            'thr_high': 3000,
            'radius': 5,
            'dr': 0.05,
            'windows': [(s, 0, 185, 0, 388) for s in (0,1,7,8,9,15,16,17,23,24,25,31)],
            'mask': np.ones((32,185,388)),
            'npix_min': 2,
            'npix_max': 500,
            'amax_thr': 10,
            'atot_thr': 20,
            'son_min': 5,
            'pbits': 0,
            }

    _peak_header = 'Seg  Row  Col  Npix      Amax      Atot   rcent   ccent rsigma  csigma '+\
          'rmin rmax cmin cmax    bkgd     rms     son'
    _peak_format = '%3d %4d %4d  %4d  %8.1f  %8.1f  %6.1f  %6.1f %6.2f  %6.2f '+\
           '%4d %4d %4d %4d  %6.2f  %6.2f  %6.2f'

    def __init__(self,*args,**kwargs):

        psdata.Detector.__init__(self,*args,**kwargs)
        init_params = {
                'vmin': -50.,
                'vmax': 50.,
                }
  
        self.set_parameter(**init_params)
        if 'zoffset' in kwargs:
            zoffset = kwargs.get('zoffset')
        elif self._name in _zoffset_defaults:
            zoffset = _zoffset_defaults.get(self._name)
        else:
            print 'No known zoffset for {:} CsPad.  Setting zoffset = 0'.format(self._name)
            zoffset = 0

        self.set_parameter(zoffset=zoffset)
        self.set_peak_parameters(**kwargs)

    def _init_proturacal(self):
#        enc0 = { 'enc1o': 765946,
#                 'enc2o': 734999,
#                 'enc3o': 744066,
#                 'enc4o': 684678,
#                 'enc5o': 902429,
        enc0 = { 'enc1o':  841320,
                 'enc2o':  644555,
                 'enc3o': 1035953,
                 'enc4o':  842152,
                 'enc5o':  811918,
                 'enc1scale':  20000.,
                 'enc2scale': -20000.,
                 'enc3scale':  20000.,
                 'enc4scale':  20000.,
                 'enc5scale': -20000.,
                 }
        print enc0
        self.set_parameter(**enc0)

    def show_rel(self):
       for i in range(1,6):
           desc = getattr(self, 'm'+str(i)).DESC
           enc = getattr(self, 'enc'+str(i)).value
           enco = getattr(self, 'enc'+str(i)+'o')
           encscale = getattr(self, 'enc'+str(i)+'scale')
           print '{:4} {:14} {:10.3f}'.format(i, desc, (enc-enco)/encscale)
           #print i, enc, enco,encscale 

    def set_peak_parameters(self, **kwargs):
        for param, value in self._default_params.items():
            if param not in kwargs:
                kwargs.update({param: value})
 
        self.set_parameter(**kwargs)

        algos_kwargs = {key: kwargs.get(key) for key in _algos_keys}
        self._algos = PyAlgos(**algos_kwargs)
        peak_kwargs = {key: kwargs.get(key) for key in _peak_keys}
        self._algos.set_peak_selection_pars(**peak_kwargs)
    
    @property
    def z_calibrated(self):
        """Calibrated CsPad Z position based on zoffset.
        """
        return self.zoffset - self.z.value

    @property
    def image(self):
        """Create image using psana PyDetector methods to access calib store.
        """
        image = self.detector.image

        return image

    @property
    def calib(self):
        return self.detector.calib

    @property
    def pixels_saturated(self):
        """Number of saturated pixels in calibrated data (self.calib)
           Set self.thr_saturated to adjust saturated pixel level.
        """
        try:
            return self._algos.number_of_pix_above_thr(self.calib, self.thr_saturated)
        except:
            print 'Error caclulating number pixels saturated'    

    @property
    def pixels_hit(self):
        """Number of pixels hit in calibrated data (self.calib)
           Set self.thr_hit to adjust hit pixel level.
        """
        try:
            return self._algos.number_of_pix_above_thr(self.calib, self.thr_hit)
        except:
            print 'Error caclulating number of pixels hit'

    @property
    def peaks(self): 
        """2-d array of peak parameters.
            
            PEAK FINDERS
            =========================
            Peak finders return list (numpy.array) of records with found peak parameters.

            # v1 - aka Droplet Finder - two-threshold peak-finding algorithm in restricted region
            #                           around pixel with maximal intensity.
            peaks = alg.peak_finder_v1(nda, thr_low=10, thr_high=150, radius=5, dr=0.05)

            # v2 - define peaks for regoins of connected pixels above threshold
            peaks = alg.peak_finder_v2(nda, thr=10, r0=5, dr=0.05)

            # v3 - define peaks in local maximums of specified rank (radius),
            #      for example rank=2 means 5x5 pixel region around central pixel.
            peaks = alg.peak_finder_v3(nda, rank=2, r0=5, dr=0.05)

        """
        peaks = self._algos.peak_finder_v1(self.calib, 
                                   thr_low=self.thr_low, 
                                   thr_high=self.thr_high, 
                                   radius=self.radius, 
                                   dr=self.dr)

        return peaks 

    def show_stats(self, **kwargs): 
        print '{:} saturated pixels (> {:} adu)'.format(self.pixels_saturated, self.thr_saturated)
        print '{:} hit pixels (> {:} adu)'.format(self.pixels_hit, self.thr_hit)
        
    def show_peaks(self, **kwargs):
        print self._peak_header
        for peak in self.peaks :
            seg,row,col,npix,amax,atot,rcent,ccent,rsigma,csigma,\
            rmin,rmax,cmin,cmax,bkgd,rms,son = peak[0:17]
             
            print self._peak_format % (seg, row, col, npix, amax, atot,\
                                       rcent, ccent, rsigma, csigma,\
                                       rmin, rmax, cmin, cmax, bkgd, rms, son)


#    totint = alg.intensity_of_pix_above_thr(nda, thr)
#    print '%.1f is a total intensity in pixels above threshold =%5.1f' % (totint, thr)

   
#    @property
#    def data_array(self):
#        """Cspad data array of shape (4, 8, 185, 388).
#           Use calibrated data if available
#        """
#        return self.quads_array(attr='calibrated')

    def make_hist(self, bins=(arange(400)-.5)*30):
        """Make histogram of CSpad.
        """
        self.yhist, self.xhist =  np.histogram(self.detector.calib, bins=bins)

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



