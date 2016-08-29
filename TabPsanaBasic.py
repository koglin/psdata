import psana
import TabPsanaEvent

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


def get_data_source(data_source=None, instrument=None, exp=None, run=None,
             live=False, ffb=False, h5=False,
             indexed=None, **kwargs): 
    """-------------------------------------------------------------------------------
       Returns the data_source from keyword arguments

            data_source = 'exp=CXI/cxic0115:run=10'

        The following are equivalent:

            data_source = get_data_source(exp='cxic0115', run=10)

        You can also load a data source with keyword options:
        (indexed is currently not supported)

            h5:   loads hdf5 data instead of xtc
            ffb:  appends ':one-stream' to data source

        The shared memory data_source can be automatically loaded with the live keyword:

            data_source = get_data_source(live=True)

        But shared memory should alse be automatically detected if no arguments are
        supplied and you are on a shared memery server.

    """
    if live:
        indexed = False
        if not data_source:
            data_source = live_source(**kwargs)

#    if not indexed:
#        indexed = True
        
    if not data_source:

        if exp and run:
            instrument = exp[0:3]
 
            data_source = "exp={exp}:run={run}".format(exp=exp,run=run)
            
            if ffb:
                data_source += ":one-stream"
            elif h5:
                data_source += ":h5"
#            elif indexed:
#                data_source += ":idx"

        else:
            print 'No data source specified, so assume this is shared memory.'
            data_source = live_source(**kwargs)
            live = True
            indexed = False

    return data_source

def live_source(monshmserver='psana', **kwargs):
    """Returns psana source string for live data from shared memory on the current node.
       The standard convention is to have the shared memry servers either named 'psana'
       or the instrument name in all caps.  This will return the source string for 
       the valid one based on searching the local file system.  The process will be
       found at:

          '/dev/shm/PdsMonitorSharedMemory_'+monshmserver
    """
    from glob import glob
    import os

    shm_srvs = glob('/dev/shm/PdsMonitorSharedMemory_'+monshmserver)
    if shm_srvs == []:
        hostsplit = os.uname()[1].split('-')
        instrument = hostsplit[1]
        monshmserver = instrument.upper()
        shm_srvs = glob('/dev/shm/PdsMonitorSharedMemory_'+monshmserver)
    
    if shm_srvs != []:
        try:
            MPI_RANK = 0
            source_str = 'shmem={:}.0:stop=no'.format(monshmserver)
        except:
            print 'Exception in finding shared memory server: ',shm_srvs
            source_str = None
    else:
        source_str = None

    return source_str

class DataSource(object):

    _attrs = ['empty', 'end', 'env', 'liveAvail', 'runs', 'steps']
    _ds = []

    def __init__(self, **kwargs):
        self.load_run(**kwargs)

    def load_run(self, **kwargs):
        self._data_source  = get_data_source(**kwargs)
        self._ds = psana.DataSource(self._data_source)
        self._Events = Events(self._ds, **kwargs)

    @property
    def current(self):
        if self._Events._events:
            return self._Events._events[-1]
        else:
            return None

    def next(self, **kwargs):
        return self.events(**kwargs).next() 
        
    def events(self, **kwargs):
        return self._Events

    def __getattr__(self, attr):
        if attr in self._attrs:
            return getattr(self._ds, attr)

    def __dir__(self):
        all_attrs = set(self._attrs +
                        self.__dict__.keys() + dir(DataSource))
        return list(sorted(all_attrs))

class Events(object):

    _nevents_cash = 10
    _events = []

    def __init__(self, ds, **kwargs):
        self._kwargs = kwargs
        self._ds = ds

    def __iter__(self):
        return self

    def next(self):
        if len(self._events) > self._nevents_cash:
            self._events.pop(0)
        
        self._events.append(TabPsanaEvent.TabEvent(self._ds.events().next(), self._ds))
        
        return self._events[-1]

class DetectorSource(object):
    """Wrap psana.DataSource with Detector classes.
    """

    _ds_attrs = ['empty', 'end', 'env', 'liveAvail', 'runs', 'steps']
    _env_attrs = ['calibDir','instrument','expNum','experiment']

    _detectors = {}
    _pbits = 0

    def __init__(self, data_source=None, **kwargs):
        self.data_source  = get_data_source(data_source=data_source, **kwargs)
        self._ds = psana.DataSource(self.data_source)
        self._Events = Events(self._ds)

        if not self._detectors.get(self.data_source):
            initialize = True
        
        if initialize or kwargs.get('initialize'): 
            self._init_detectors()

    def events(self):
        return self._Events

    @property
    def run(self):
        """Run number.
        """
        return self._ds.evt().run()
    
    def _init_detectors(self):
        """Initialize PyDetectors based on source and psana env.
        """
         
        for key in self._ds.env().configStore().keys():
            alias = key_alias(key)
            if alias:
                src = key.src()
                self._add_dets(**{alias: src})

    def _add_dets(self, **kwargs):
        runnum = self.run
        exp = self.experiment
        
        if self.data_source not in self._detectors:
            self._detectors.update({self.data_source: {}})
        
        for alias, src in kwargs.items():
            try:
                det = psana.Detector(psana.Source(src), self._ds.env(), self._pbits)
                self._detectors[self.data_source].update({alias: det})
            except Exception as err:
                print 'Cannot add {:}:  {:}'.format(alias, src) 
                traceback.print_exc()

    @property
    def _current_dets(self):
        """Current detectors from _detector dictionary.
        """
        runnum = self.run
        exp = self.experiment

        return self._detectors.get('data_source')
 
    def __getattr__(self, attr):
        if attr in self._ds_attrs:
            return getattr(self._ds, attr)
        
        if attr in self._env_attrs:
            return getattr(self._ds.env(), attr)()
        
#        dets = self._current_dets
#        if dets and attr in dets:
#            det = dets[attr]
#            if det.dettype in [16, 17]:
#                # return WaveformDict for waveform type Acqiris and Imp data
#                return WaveformDict(det, self._evt)
#            else:
#                # all other data types currently return ImageDict
#                return ImageDict(det, self._evt)

    def __dir__(self):
        all_attrs =  set(self._ds_attrs + 
                         self._env_attrs +
#                         self._current_dets.keys() +
                         self.__dict__.keys() + dir(DetectorSource))
        
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


