import psdata
import os
import time
import pickle

from pylab import *

from psmon import publish
from psmon.plots import Image, XYPlot, MultiPlot

write = sys.stdout.write
def onConnectionChange(pvname=None, conn= None, **kws):
    write('PV connection status changed: %s %s\n' % (pvname,  repr(conn)))
    sys.stdout.flush()

def onValueChange(pvname=None, value=None, host=None, **kws):
    write('PV value changed: %s (%s)  %s\n' % ( pvname, host, repr(value)))
    sys.stdout.flush()

# matplot lib does not update in a loop -- try Image
def onArrayChange(pvname=None, value=None, host=None, **kws):
#    plt.imshow(ahst
    ahst = value[0:640*120].reshape(120,640)
    psmon_img_publish('Dg3summary', ahst)
    write('PV value changed: %s (%s)  %s\n' % ( pvname, host, repr(value)))
    sys.stdout.flush()

def psmon_img_publish(name, image):
    psmon_func = Image(name, name, image)
    publish.send(name, psmon_func)

class pim_2color(psdata.Detector):
    """Beamline PIM (Pop-in Monitor)  Detector Class of psdata.Detector.
    """

    def __init__(self,*args,**kwargs):

        psdata.Detector.__init__(self,*args,**kwargs)

# Note x axis is backwards from AMI        
        if self._name == 'Sc2Questar':
            parameters = {
                    'pedestal': 0, 
                    'roi': [0,640,0,480],
                    'nshots': 60,
                    'ninfo': 10,
                    }
        elif self._name == 'Dg2Pim':
            parameters = {
                    'pedestal': 0, 
                    'roi': [170,470,325,625],
                    'nshots': 200,
                    'ninfo': 10,
                    }
        else:
            parameters = {
                    'pedestal': 0, 
                    'roi': [170,470,325,625],
                    'nshots': 200,
                    'ninfo': 10,
                    }

        epics_devices = {
                'hst1':  'CXI:EXS:HST:01:data',        
                'hst1x': 'CXI:EXS:HST:01:x',
                'hst1y': 'CXI:EXS:HST:01:y',
                'hst2':  'CXI:EXS:HST:02:data',
                'hst2x': 'CXI:EXS:HST:02:x',
                'hst2y': 'CXI:EXS:HST:02:y',
                }

        print 'setting parameters:'
        print parameters 
        
        self.set_parameter(**parameters)
        self.set_roi_parameters()
        self.epicsLive.add_device(**epics_devices)
        self.load_pedestal()

        if not self._data._kwargs.get('noload'): 
            self.add_event_function('_on_book_event_hist')
#            self.add_event_function('_on_print', nevents=self.nshots)
#            self.add_event_function('_on_put_epics', nevents=self.nshots)
            self._init_event_hist()

        publish.init()

    def set_roi_parameters(self):
        nx=self.roi[1]-self.roi[0]
        ny=self.roi[3]-self.roi[2]
        nbook = nx+ny+self.ninfo
        self.set_parameter(nx=nx)
        self.set_parameter(ny=ny)
        self.set_parameter(nbook=nbook)

    def _init_event_hist(self):
        self._hst1 = empty(self.hst1.VAL.size)
        self._hst2 = empty(self.hst2.VAL.size)
        self._hst1x = empty(self.hst1x.VAL.size)
        self._hst2x = empty(self.hst2x.VAL.size)
        self._hst1y = empty(self.hst1y.VAL.size)
        self._hst2y = empty(self.hst2y.VAL.size)
        self._init = True
        self._ievent0 = self._data.ievent
        self.time0 = time.time()

    @property
    def _ihist(self):
        if self._data._kwargs.get('noload'):
            return 0
        else:
            return mod(self._data.ievent-self._ievent0-1, self.nshots)

    def _on_book_event_hist(self):
        ebeam = self._data.EBeam
        gasdet = self._data.FEEGasDetEnergy
        eventid = self._data.EventId
        evr = self._data.evr0
        nshots = self.nshots
        i = self._ihist
        nx = self.nx
        ny = self.ny
        ninfo = self.ninfo
        ainfo = np.zeros(ninfo)
        nbook = nx+ny+ninfo
        if ebeam and ebeam.is_in_keys:
            ainfo[0] = ebeam.ebeamL3Energy
            ainfo[1] = ebeam.ebeamEnergyBC1
            ainfo[2] = ebeam.ebeamEnergyBC2
        if gasdet and gasdet.is_in_keys:
            ainfo[3] = gasdet.f_11_ENRC
            ainfo[4] = gasdet.f_12_ENRC
        if eventid and eventid.is_in_keys:
            ainfo[5] = eventid.time[0]
            ainfo[6] = eventid.time[1]
            ainfo[7] = eventid.fiducials
            ainfo[8] = eventid.ticks
        if evr and evr.is_in_keys:
            ainfo[9] = max([a for a in mod(evr.eventCodes,100) if a < 50])
        if self.is_in_keys:
            dat = np.concatenate((ainfo, self.xprojection, self.yprojection))
            ka = i*nbook
            kb = (i+1)*nbook
            self._hst1[ka:kb] = dat
#            self._hst1[i*nx:(i+1)*nx] = self.xprojection
#            self._hst2[i*ny:(i+1)*ny] = self.yprojection
#        print i, ainfo, self.xprojection.sum(), self.yprojection.sum()

    def _on_put_epics(self):
        if self._init:
#            self.hst1y.put('VAL', array(self._hst1y), use_complete=True)
#            self.hst2y.put('VAL', array(self._hst2y), use_complete=True)
            self.hst1.put('VAL', array(self._hst1), use_complete=True)
#            self.hst2.put('VAL', array(self._hst2), use_complete=True)
           
    def _on_print(self):
        kind = self._ihist*self.nbook+arange(5,8)
        dtime = time.time()-self.time0
        nshots = self._ihist+1 
        print dtime, nshots, float(nshots)/dtime, self._hst1[kind]

    def next_summary(self):
        self._init_event_hist()
        for i in range(self.nshots):
            self._data.next_event()
        
        self._on_put_epics()
        self._on_print()
        psmon_img_publish('Dg3Pim_xsummary', self.xsummary)
        psmon_img_publish('Dg3Pim_ysummary', self.ysummary)

    def monitor_summary(self):
        try:
            while True:
                self.next_summary()

        except KeyboardInterrupt:
            pass

    @property
    def xsummary(self):
        kxdata = np.concatenate([self.ninfo+ishot*self.nbook+arange(self.nx) for ishot in range(self.nshots)])
        return self.hst1.VAL[kxdata].reshape(self.nshots,self.nx)

    @property
    def ysummary(self):
        kydata = np.concatenate([self.ninfo+self.nx+ishot*self.nbook+arange(self.ny) for ishot in range(self.nshots)])
        return self.hst1.VAL[kydata].reshape(self.nshots,self.ny)
 
    @property
    def ratio(self):
        kydata = np.concatenate([self.ninfo+self.nx+ishot*self.nbook+arange(self.ny) for ishot in range(self.nshots)])
        knorm = arange(self.nshots)*self.nbook+7
        return self.hst1.VAL[kydata].reshape(self.nshots,self.ny)
    
    def init_xsummary(self):
#        self.hst1.add_callback('VAL', onValueChange)
        publish.init()
        psmon_img_publish('Dg3Pim_xsummary', self.xsummary)
        psmon_img_publish('Dg3Pim_ysummary', self.ysummary)

    def show_xsummary(self):
        ny = self.nshots
        ky = arange(ny)
#        hst1y = PV('CXI:EXS:HST:01:y')
        hst1_ydata = self.hst1y.VAL
        # L3 Energy is in the 1st set of 128 elements of CXI:EXS:HST:01:y 
        ebeamL3Energy = hst1_ydata[ky]
        # BC1 Energy is in the 2nd set of 128 elements of CXI:EXS:HST:01:y 
        ebeamEnergyBC1 = hst1_ydata[ky+ny]
#        # BC2 Energy is in the 3rd set of 128 elements of CXI:EXS:HST:01:y 
#        ebeamEnergyBC2 = hst1_ydata[ky+2*ny]
        # eventCode is in the 3rd set of 128 elements of CXI:EXS:HST:01:y 
        eventCode = hst1_ydata[ky+2*ny]
        # Gas Det E f_11 is in the 4th set of 128 elements of CXI:EXS:HST:01:y 
        gasdetf_11_ENRC = hst1_ydata[ky+3*ny]
        # Gas Det E f_12 is in the 5th set of 128 elements of CXI:EXS:HST:01:y 
        gasdetf_12_ENRC = hst1_ydata[ky+4*ny]
        # Event Time is in the 6th set of 128 elements of CXI:EXS:HST:01:y 
        eventid_time = hst1_ydata[ky+5*ny]
        # Event Fiducial is in the 7th set of 128 elements of CXI:EXS:HST:01:y 
        eventid_fiducials = hst1_ydata[ky+6*ny]
        # Event Ticks is in the 8th set of 128 elements of CXI:EXS:HST:01:y 
        eventid_ticks = hst1_ydata[ky+7*ny]

    @property
    def raw_image(self):
        """Raw image -- currently supporting psana data16.
           This could in the future be updated to take other types of data
           including epics.
        """
        return self.data16

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

    def save_pedestal(self, file_name=None):
        if not file_name:
            file_name = self._name+'_pedestal.pkl'
        
        with open(file_name,'w') as f:
                pickle.dump(self.pedestal, f)

    def load_pedestal(self, file_name=None):
        try:
            if not file_name:
                file_name = self._name+'_pedestal.pkl'
            
            with open(file_name,'r') as f:
                self.pedestal = pickle.load(f)
        
        except:
            print 'cannot load pedestal for ', self._name

    def new_plot(self, **kwargs):
        plt.ion()
        plt.imshow(self.image)
        plt.clim(**kwargs)
        plt.colorbar()
        plt.title(self.desc)

    def plot(self, nevents=1, projection=False, monitor=False, next_event=False):
        """Plot image using matplotlib.
        """
        ievent = 0
        try:
            plt.ion()
            plt.show()
            while ievent < nevents or monitor:
                if ievent > 0 or next_event or monitor:
                    self._data.next_event()
                
                if projection:
                    if projection is 'y':
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
                start=True, stop=False, **kwargs):
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
                                name=name, title=title, **kwargs)
            
            else:
                self.add_psplot('image', plot_type='Image', 
                                name=name, tle=title, **kwargs)
        
        if stop:
            self.del_psplot(name)

   


