import psana
import traceback
import operator
import sys

def key_alias(key):
    """Return the alias for a key if it is a valid detector.
    """

    if hasattr(key, 'src') and hasattr(key.src(), 'detName') \
            and key.src().detName() != 'NoDetector' \
            and hasattr(key, 'type') and key.type():
        
        module = key.type().__module__.replace('psana.','')
       
        src = key.src()
        
        if hasattr(key,'alias'):
            alias = key.alias()
        
        if not alias:
            alias = '_'.join([src.detName(),str(src.detId()),
                              src.devName(),str(src.devId())])

        if alias:
            alias = alias.replace('-','_')

        return alias

    else:
        return None


class DetectorDictify(object):
    """Tab accessibile dictified set of psana.Detector objects
       based on aliases of relevant detectors in evt.keys().

       Each time a new run is loaded, use initialize keyword
       to make sure the calib directory information is updated
       based on the new env for the 
    """

    _detectors = {}
    _pbits = 0

    def __init__(self, evt, env, initialize=False, pbits=None):

        self._evt = evt
        self._env = env
        if pbits:
            self._pbits = pbits

        if not self._detectors.get(self.experiment):
            initialize = True
        elif not self._detectors[self.experiment].get(self.run):
            initialize = True
        
        if initialize: 
            self._init_detectors()

    @property
    def experiment(self):
        """Experiment name.
        """
        return self._env.experiment()
    
    @property
    def expNum(self):
        """Experiment number
        """
        return self._env.expNum()
    
    @property
    def instrument(self):
        """Instrument name (upper case).
        """
        return self._env.instrument()
    
    @property
    def calibDir(self):
        """Calibration Directory path.
        """
        return self._env.calibDir()
    
    @property
    def run(self):
        """Run number.
        """
        return self._evt.run()
    
    def _init_detectors(self):
        """Initialize psana.Detectors based on source and psana env.
        """
         
        for key in self._env.configStore().keys():
            alias = key_alias(key)
            if alias:
                src = key.src()
#                try:
                self._add_dets(**{alias: src})
#                except:
#                    print 'ERROR trying to make psana.Detector for {:}'.format(alias)
#                    print src, key

    def _add_dets(self, **kwargs):
        runnum = self.run
        exp = self.experiment
        
        if exp not in self._detectors:
            self._detectors.update({exp: {}})
        
        if runnum not in self._detectors[exp]:
            self._detectors[exp].update({runnum: {}})

#        print runnum, exp
#        print self._detectors 
        for alias, src in kwargs.items():
            try:
                srcname = str(src).split('(')[1].split(')')[0]
                self._detectors[exp][runnum].update({alias: psana.Detector(srcname, self._env)})
            except Exception as err:
                print 'Cannot add {:}:  {:}'.format(alias, src) 
#                traceback.print_exc()

    @property
    def _current_dets(self):
        """Current detectors from _detector dictionary.
        """
        runnum = self.run
        exp = self.experiment

        return self._detectors[exp][runnum]
 
    def __getattr__(self, attr):
        dets = self._current_dets
        if attr in dets:
            det = dets[attr]
            if det.dettype in [16, 17]:
                # return WaveformDict for waveform type Acqiris and Imp data
                return WaveformDict(det, self._evt)
            else:
                # all other data types currently return ImageDict
                return ImageDict(det, self._evt)

    def __dir__(self):
        all_attrs =  set(self._current_dets.keys() +
                         self.__dict__.keys() + dir(DetectorDictify))
        
        return list(sorted(all_attrs))

class WaveformDict(object):
    """Tab accessibile dictified psana PyDetector object.
       
       Attributes come from Detector.PyDetector in psana 
       with low level implementation done in C++ or python.  
       Boost is used for the C++.
    """

    _attrs = ['raw'] 

    _attr_docs = {
            'raw': 'Raw waveform Volts vs time in sec', 
            } 

    def __init__(self, det, evt):
        self._evt = evt
        self._det = det

    @property
    def instrument(self):
        """Instrument to which this detector belongs.
        """
        return self._det.instrument()

    def set_print_bits(self, pbits):
        """Set the level of printing.
        """
        self._det.set_print_bits(pbits)

    def print_attributes(self):
        """Print detector attributes.
        """
        self._det.print_attributes()

    def show_info(self):
        """Show information for relevant detector attributes.
        """
        if self.size > 0:
            items = sorted(self._attr_docs.items(), key = operator.itemgetter(0))
            for attr, doc in items:
                fdict = {'attr': attr, 'unit': '', 'doc': doc}
                value = getattr(self, attr)
                if isinstance(value, str):
                    fdict['str'] = value
                elif isinstance(value, list):
                    if len(value) < 5:
                        fdict['str'] = str(value)
                    else:
                        fdict['str'] = 'list'
                elif hasattr(value,'mean'):
                    if value.size < 5:
                        fdict['str'] = str(value)
                    else:
                        fdict['str'] = '<{:.5}>'.format(value.mean())
                else:
                    try:
                        fdict['str'] = '{:10.5g}'.format(value)
                    except:
                        fdict['str'] = str(value)

                print '{attr:18s} {str:>10} {unit:6} {doc:}'.format(**fdict)
        else:
            print 'No Event'

    def __getattr__(self, attr):
        if attr in self._attrs:
            return getattr(self._det, attr)(self._evt)

    def __dir__(self):
        all_attrs =  set(self._attrs +
                         self.__dict__.keys() + dir(WaveformDict))
        
        return list(sorted(all_attrs))



class ImageDict(object):
    """Tab accessibile dictified psana PyDetector object.
       
       Attributes come from Detector.PyDetector in psana 
       with low level implementation done in C++ or python.  
       Boost is used for the C++.
    """

    _attrs = ['shape', 'size', 'ndim', 'pedestals', 'rms', 'gain', 'bkgd', 'status',
              'status_as_mask', 'mask_calib', 'common_mode', 'raw', 'calib',
              'areas', 'indexes_x', 'indexes_y', 'pixel_size',
              'coords_x', 'coords_y', 'coords_z', 
              'image',
             ] 

    _attr_docs = {
            'shape': 'Shape of raw data array', 
            'size': 'Total size of raw data', 
            'ndim': 'Number of dimensions of raw data', 
            'pedestals': 'Pedestals from calibStore', 
            'rms': '', 
            'gain': 'Pixel Gain factor from calibStore', 
            'bkgd': '', 
            'status': '',
            'common_mode': 'Common mode parameters', 
            'raw': 'Raw data', 
            'calib': 'Calibrated data',
            'areas': 'Pixel area correction factor', 
            'indexes_x': 'Pixel X index', 
            'indexes_y': 'Pixel Y index', 
            'pixel_size': 'Pixel Size',
            'coords_x': 'Pixel X coordinate', 
            'coords_y': 'Pixel Y coordinate', 
            'coords_z': 'Pixel Z coordinate', 
            'image': 'Reconstruced 2D image from calibStore geometry',
            } 

    def __init__(self, det, evt):
        self._evt = evt
        self._det = det

    @property
    def instrument(self):
        """Instrument to which this detector belongs.
        """
        return self._det.instrument()

    def make_image(self, nda):
        """Make an image from the input numpy array based on the 
           geometry in the calib directory for this event.
        """
        return self._det.image(self._evt, nda)

    def set_do_offset(do_offset=True):
        """Not sure what do offset does?
        """
        self._det.set_do_offset(do_offset=do_offset)

    def common_mode_correction(self, nda):
        """Return the common mode correction for the input numpy 
           array (pedestal-subtracted). 
        """
        return self._det.common_mode_correction(self._evt, nda)
        
    def common_mode_apply(self, nda):
        """Apply in place the common mode correction for the input 
           numpy array (pedestal-subtracted). 
        """
        self._det.common_mode_apply(self._evt, nda)

    def mask(self, calib=False, status=False, 
                   edges=False, central=False, 
                   unbond=False, unbondnbrs=False):
        """Returns combined mask.
                calib:      mask from file in calib directory.
                status:     pixel status from file in calib director.
                edges:      mask detector module edge pixels (mbit +1 in mask_geo).
                central:    mask wide central columns (mbit +2 in mask_geo).
                unbond:     mask unbonded pixels (mbit +4 in mask_geo).
                unbondnbrs: mask unbonded neighbour pixels (mbit +8 in mask_geo).
        """
        return self._det.mask(self._evt, calib=False, status=False, edges=False, 
                              central=False, unbond=False, unbondnbrs=False)

    def mask_geo(self, mbits=15): 
        """Return geometry mask for given mbits keyword.
           Default is mbits=15 to mask edges, wide central columns,
             non-bo pixels and their neighbors

           mbits =  +1-edges; 
                    +2-wide central cols; 
                    +4 unbonded pixel; 
                    +8-unbonded neighbour pixels;
        """
        return self._det.mask_geo(self._evt, mbits=mbits)

    def set_print_bits(self, pbits):
        """Set the level of printing.
        """
        self._det.set_print_bits(pbits)

    def print_attributes(self):
        """Print detector attributes.
        """
        self._det.print_attributes()

#    def print_config(self):
#        """Print detector configuration.
#        """
#        self._det.print_config(self._evt)

    def show_info(self):
        """Show information for relevant detector attributes.
        """
        if self.size > 0:
            items = sorted(self._attr_docs.items(), key = operator.itemgetter(0))
            for attr, doc in items:
                fdict = {'attr': attr, 'unit': '', 'doc': doc}
                value = getattr(self, attr)
                if isinstance(value, str):
                    fdict['str'] = value
                elif isinstance(value, list):
                    if len(value) < 5:
                        fdict['str'] = str(value)
                    else:
                        fdict['str'] = 'list'
                elif hasattr(value,'mean'):
                    if value.size < 5:
                        fdict['str'] = str(value)
                    else:
                        fdict['str'] = '<{:.5}>'.format(value.mean())
                else:
                    try:
                        fdict['str'] = '{:10.5g}'.format(value)
                    except:
                        fdict['str'] = str(value)

                print '{attr:18s} {str:>10} {unit:6} {doc:}'.format(**fdict)
        else:
            print 'No Event'

    def __getattr__(self, attr):
        if attr in self._attrs:
            return getattr(self._det, attr)(self._evt)

    def __dir__(self):
        all_attrs =  set(self._attrs +
                         self.__dict__.keys() + dir(ImageDict))
        
        return list(sorted(all_attrs))


