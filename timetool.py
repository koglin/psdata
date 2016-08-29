import psdata
import os
import numpy
import scipy.signal
import pandas

from pylab import *
ion()

class ttrespVSdelay(object):
    def __init__(self):
        self._delay  = []
        self._ttresp = []
        self._ttdelta = []
        self._ttmax = []
        self._figure = figure()
        self.threshold_max = 10
        self.threshold_delta_low = 0.05
        self.threshold_delta_high = 0.12
        self.ran = (-0.0003,0.00061)
        xlabel('laser delay dial')
        ylabel('timetool response pixel')
        return

    @property
    def weights(self):
        return self._weights

    @weights.getter
    def weights(self):
        return self._weights

    @weights.setter
    def weights(self,vals):
        self._weights = vals
        return

    def ttrespVSdelay(self,xnorm=None, tdelay=None):
        try:
            delta, ttmax, edge = find_edge2(xnorm)
            self._ttresp.append(edge  )
            self._ttdelta.append(delta)
            self._ttmax.append(ttmax)
            #self._ttresp.append( find_edge(xnorm, wgts=self._weights) )
        except Exception as err:
            print err
            return
        self._delay.append(  tdelay )

    def update_figure(self):
        fig = figure( self._figure.number )
        cla()
        scatter( self._delay, self._ttresp )
        xlabel('laser delay dial')
        ylabel('timetool response pixel')
        return

    def draw_hists(self):
        figure()
        self.df = pandas.DataFrame({'delay': self._delay, 'resp': self._ttresp, 'delta': self._ttdelta, 'max': self._ttmax, } )
        self.df = self.df.dropna(subset=['max'])
#        bins = numpy.arange(-2000,2000,40)
        bins = numpy.arange(0,1000,20)
        self._summary_data = {'delay': [], 'mean': [] }
        uniq = self.df.delay.unique()
        for u in uniq :
            vals = self.df[ (self.df.delay == u) & (self.df['max'] > self.threshold_max) & (self.threshold_delta_low <self.df.delta ) & (self.df.delta < self.threshold_delta_high) ]
            #thishist = numpy.histogram(vals.resp.values,bins=bins)
            #maxbin = thishist[1][ list(thishist[0]).index( thishist[0].max() ) ]
            maxbin = vals.resp.mean()
            self._summary_data['delay'].append( u )
            self._summary_data['mean'].append(maxbin)
            label = "{:0.2f} delay ({:0.0f})".format(u*1000.,maxbin)
            hist(vals.resp.values, bins=bins,alpha=0.5,label=label,edgecolor='none')
            print "{:0.2f} {:0.0f}".format( u*1000., maxbin)
        legend(fontsize='x-small')
        return

    def draw_summary(self):
        figure()
        vals = self.df[ (self.df['max'] > self.threshold_max) & (self.df.delta > self.threshold_delta_low) & (self.df.delta < self.threshold_delta_high) ]
        scatter(vals.delay, vals.resp, edgecolor='none', alpha=0.1, s=60 )
        scatter(self._summary_data['delay'], self._summary_data['mean'] , marker='*', s=180, c='r', edgecolor='none')
        xlim(-0.00103, 0.00103)
        ylim(-10, 1040 )
        xlabel('laser delay dial (s)')
        ylabel('timetool response (pixel)')
        self.fitx = []
        self.fity = []
        for v in vals.delay.unique():
            print v
            if self.ran[0] < v < self.ran[1]:
                vv = vals[ vals.delay == v ]
                self.fitx.append( v )
                self.fity.append( vv.resp.mean() )
        self.pfit = numpy.polyfit( self.fitx, self.fity, 1)
        self.poly = numpy.poly1d(self.pfit)
        yys = [ self.poly(xx) for xx in self.ran ]
        plot(self.ran, yys, lw=3, c='g', linestyle='-', alpha=0.6)
        text( 0.0003, 30, "fit: "+str(self.poly).strip())


        return
        

def find_edge2(xnorm):
    startedge = xnorm[:10].mean()
    endedge   = xnorm[-10:].mean()
    delta = endedge- startedge
    xnorm2 = (xnorm - startedge ) / delta
    xnorm3 = 1. - xnorm2
    intermediate = (xnorm3 * xnorm2)**2
    return delta, intermediate.max(), numpy.argmax(intermediate)

def find_edge3(xnorm):
    startedge = xnorm[:10].mean()
    endedge   = xnorm[-10:].mean()
    xnorm2 = (xnorm - startedge ) / (endedge - startedge )
    xnorm3 = 1. - xnorm2
    intermediate = (xnorm3 * xnorm2)
    plot(xnorm3 - xnorm2)
    plot(xnorm2,label="xnorm2 (scaled)")
    plot(xnorm3,label="1-xnorm2")
    plot(intermediate, label="xnorm3*xnorm2")
    plot(intermediate**2,label="(xnorm3*xnorm2)**2")
    plot(xnorm3 - xnorm2,label="(xnorm3-xnorm2)")
    plot((xnorm3 - xnorm2)**2,label="(xnorm3-xnorm2)**2")
    legend(loc=2,fontsize='small')
    return numpy.argmax(intermediate)


def psalg_finite_impulse_response(filt,sample):
    # this is faster
    result = numpy.convolve(sample,filt[::-1],mode='valid')
    return result

def psalg_finite_impulse_response_orig(filt,sample):
    # speed this up, possibly with the TimeTool/data/timetool_setup.py example
    if len(sample) < len(filt):
        return numpy.array([])
    else :
        llen = len(sample) - len(filt)
        result = numpy.array([0]*llen,dtype=numpy.double)
        for i in xrange(llen):
            v = 0.
            for j in xrange(len(filt)):
                v += sample[i+j] * filt[j]
            result[i] = v
    return result


def find_peaks(resp,maxpeaks=2):
    widths = numpy.linspace(10,160,30)
    peaks = scipy.signal.find_peaks_cwt(resp,widths)
    if len(peaks) > maxpeaks:
        return peaks[:maxpeaks]
    else:
        return peaks

def parab_fit(inpt, ix, afrac):
    """
    inpt = data points
    ix   = center of peak
    afrac = fraction of amplitude of input at ix to cut at
    """
    trf = afrac * inpt[ix]
    abvtrf = [ii>=trf for ii in inpt]
    strt = abvtrf.index(True)
    fnsh = abvtrf[strt:].index(False)
    data = inpt[strt:strt+fnsh]
    xx   = range(strt,strt+fnsh)
    pFit0 = numpy.polyfit(xx, data, 2)
    return pFit0

def get_parab_max(self,pfit):
    return


def find_edge(xnorm,wgts=[],draw=False):
    position_pixel = 0
    resp = psalg_finite_impulse_response(wgts,xnorm)
    #resporig = psalg_finite_impulse_response_orig(wgts,xnorm)
    #peaks = scipy.signal.find_peaks_cwt(resp,numpy.linspace(10,160,num=60))
    peaks=find_peaks(resp)
    trf = 0.8 * resp[peaks[0]]
    abvtrf = [ii>=trf for ii in resp]
    strt = abvtrf.index(True)                                                     
    fnsh = abvtrf[strt:].index(False)
    data = resp[strt:strt+fnsh]
    xx = range(strt,strt+fnsh)
    pFit0    = numpy.polyfit(xx,data,2)
    polfun   = numpy.poly1d( pFit0 )
    dpolfun  = numpy.polyder( polfun )
    yy = [polfun(x) for x in xx]
    try:
        roots = dpolfun.r
    except Exception as err:
        roots = []
    if len( roots ) > 0:
        maxx = dpolfun.r[0]
        maxy = polfun(maxx)
    else:
        maxx = 0
        maxy = 0
    if draw==True:
        figure()
        plot(xnorm)
        offset = (resp[0]-xnorm[0])
        plot(resp-offset)
        #plot(resporig-offset)
        plot(xx,yy-offset)
        print polfun
        plot([maxx], [maxy-offset], 'r*', markersize=25)

    position_pixel = maxx
    return position_pixel
        

class timetool(psdata.Detector): 
    """Timetool Detector Class of psdata.Detector.
    """

    def __init__(self,*args,**kwargs):

        psdata.Detector.__init__(self,*args,**kwargs)
        
        self._properties = {
                'pedestal': 0., 
                'roi': None,
                'eventcode_nobeam': 162,
                }
        self.set_parameter(**self._properties)
#        if not hasattr(self, 'weights'):
#            self.set_cfg()

        self._ttrespVSdelay = ttrespVSdelay()

        self.add_event_function('_on_next_nobeam', eventCode=self.eventcode_nobeam)
        self._ready = False
        self._count = 0
        self.add_event_function('_on_next_beam', eventCode=self.eventcode_beam)

    def get_reference(self):
        self._data.goto_next_event(eventCode=162)
        self._data.next_event()

    def set_cfg(self):
        """First we define some options for TimeTool that we want to use between
           steps. These are from TimeTool/data/sxr_timetool.cfg. Typically options are 
           defines in a psana config file such as sxr_timetoo.cfg. However one can also
           define the options through psana's python interface as we are doing. Note - 
           this configuration applies to all datasources that are created.

           The ROI where the TimeTool does it's analysise. 
           This will be plotted in a white box. Users can change this if it looks
           like the signal to measure is somewhere else on the opal.
           Rolling average convergence factor (1/Nevents)
         
           The reference that TimeTool.Analyze uses is built up from all the 
           previous shots using a rolling average. The default is for the TimeTool 
           to uses the last no beam shot for the reference weighed at 1.0 (meaning
           it won't use the previous shots). For this behavior, you would set the 
           option ref_avg_fraction = 1.0. However we want to build an average out
           of all the data in run 144. So we will use a much smaller value:
           This weighs the most recently seen shot
           at 1% and the previous shots at 99%
          
           Something specific with this data is telling TimeTool.Analyze that the
           beam is always off for run 144 so that it builds a reference from everything,
           and that it is always on for run 150, so it calculates timetool values for
           everything. The TimeTool will look at Evr Codes to determine beam on/off 
           laser on/off. We need to tell it what Evr codes are associated with what.
          
           Often specific evr codes are programmed to fire with the beam or laser. In
           this case no evr codes were programmed, just which run was a no-beam and which
           run was a beam+laser run are known by the scientists. Hence we need to identify
           an evr code that is always present (this is code 140). For run 144, we say
           code 140 is associated with no beam. Then TimeTool.Analyze builds a reference
           from all the data. For run 150, we say code 0 is associated with no beam. Evr code
           0 is illegal and will never be present. Hence TimeTool.Analyze treat every 
           event as having beam, and laser.
        """
        weights = [0.0235, 0.0237, 0.0236, 0.0229, 0.0223, 0.0221, 0.0216, 0.0212, 0.0205, 0.0209, 0.0202, 0.0202, 0.0184, 0.0197, 0.019, 0.0199, 0.0178, 0.0187, 0.0177, 0.0186, 0.0166, 0.0179, 0.0172, 0.0168, 0.0171, 0.0169, 0.0167, 0.0171, 0.0158, 0.0162, 0.0158, 0.0147, 0.0145, 0.0153, 0.0142, 0.0139, 0.0138, 0.0143, 0.0135, 0.0123, 0.013, 0.0126, 0.0129, 0.0117, 0.0104, 0.0114, 0.0114, 0.0107, 0.0095, 0.0092, 0.0087, 0.0083, 0.007, 0.0076, 0.0064, 0.0064, 0.0054, 0.0045, 0.004, 0.0051, 0.0029, 0.0031, 0.0018, 0.0019, 0.001, 0.0001, -0.0001, -0.0025, -0.0022, -0.0024, -0.0038, -0.0046, -0.0056, -0.0059, -0.0074, -0.0082, -0.0099, -0.0093, -0.0107, -0.0121, -0.0125, -0.0136, -0.0151, -0.0158, -0.0167, -0.0183, -0.0203, -0.018, -0.0218, -0.0219, -0.0229, -0.0246, -0.0248, -0.0265, -0.0281, -0.0285, -0.0291, -0.0294, -0.0307, -0.0315, -0.0325, -0.0326, -0.0357, -0.0342, -0.0358, -0.037, -0.0376, -0.0381, -0.04, -0.0395] 
        self.weights = weights

        self._ttrespVSdelay.weights = weights
       
        wstr = ' '.join([str(w) for w in weights]) 

        print 'weights', wstr

        cfg_options = {
            'get_key': '{:}'.format(self.src),
            'put_key': self._name,
            'sig_roi_x': [0, 1023],
            'sig_roi_y': [425, 724],
            'sb_avg_fraction': 0.05,
            'ref_avg_fraction': 0.01,        
            'eventCodeWhichDoesntExist': 0,
            'evrCodeAlwaysPresent': 140,
            'eventcode_nobeam': 162,
            'eventcode_skip': 0,
            'calib_poly': '2 0',
            'ref_load': False,
            'projectX': True,
            'proj_cut': 0,
            'weights': "{:}".format(wstr), 
            }

        parameters = {
            'reference_image': 1,
            'cfg_options': cfg_options,
            'weights': np.array(weights),
            'sig_roi_x': [0, 1023],
            'sig_roi_y': [425, 724],
            }

        self.set_parameter(**parameters)  
        self.add_psana_options({'TimeTool.Analyze': cfg_options})

    def get_next_timetool_reference(self):
        self._data.goto_next_event(eventCode=self.eventcode_nobeam)

    def _on_next_nobeam(self, **kwargs):
        """Function to set the reference_image each time an event with
           eventcode_nobeam occurs
        """
        self.set_parameter(reference_image=self.calibrated_image)

    def _on_next_beam(self):
        if self._ready == True :
            self._ttrespVSdelay.ttrespVSdelay(xnorm=self.xnormalized, tdelay=self._data.epicsStore.laser.time_delay.value)
        if self._count % 1000 == 0:
            self._ttrespVSdelay.update_figure()
        self._count += 1

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
    def ref_image(self):
        if self.roi and len(self.roi) == 4:
            return self.reference_image[self.roi[0]:self.roi[1],self.roi[2]:self.roi[3]]
        else:
            return self.reference_image

    @property
    def xprojection(self):
        """X projection of image.
        """
        if hasattr(self,'_yroi'):
            img = self.image
            imgslice = img[self._yroi[0]:self._yroi[1],:]
            return imgslice.sum(axis=0)
        else:
            return self.image.sum(axis=0)
    
    @property
    def yprojection(self):
        """X projection of image.
        """
        return self.image.sum(axis=1)

    @property
    def xreference(self):
        if hasattr(self,'_yroi'):
            img = self.ref_image
            imgslice = img[self._yroi[0]:self._yroi[1],:]
            return imgslice.sum(axis=0)
        else:
            return self.ref_image.sum(axis=0)

    @property
    def xnormalized(self):
        xnorm = self.xprojection/(self.xreference*1.)
        #self.position_pixel = self.corr(xnorm)
        if self.position_pixel:
            v = 200
            position_corr = min([self.position_pixel+v,xnorm.size-1])
            xnorm[position_corr] = 1.5
        
        return xnorm

    def publish(self):
        self.add_psplot('xnormalized', eventCode=[-162],
                        local=True, plot_type='XYPlot')
        self.add_psplot('xprojection','xreference', eventCode=[-162],
                        local=True, plot_type='XYPlot')
        self.add_psplot('image')

    def yroi(self,draw=False):
        xmean = list(self.yprojection).index( self.yprojection.max() )
        self._yroi = [xmean-20, xmean+20]
        if draw:
            plot(self.yprojection)
            plot([self._yroi[0],self._yroi[0]],[self.yprojection.min(),self.yprojection.max()],'r-')
            plot([self._yroi[1],self._yroi[1]],[self.yprojection.min(),self.yprojection.max()],'r-')
        return self._yroi

    def corr(self,norm):
        if not hasattr(self,'lin'):
            self.lin = numpy.linspace(0.7,1.06,140)
        xcorr = numpy.correlate(norm,self.lin)
        n = list(xcorr).index(xcorr.max())
        return n
    def setup_ttdelay(self):
#        self.set_cfg()
        self.show_info()
        self.yroi()
        self.get_reference()
        self._ready = True
        return




#    def makeReferenceFiles(dataSource, 
#                           ttRefFile, 
#                           numpyRefFile, 
#                           refNumEvents,
#                           opal_src,
#                           put_key,
#                           sxr_timetool_weights):
#        if os.path.exists(ttRefFile):
#            os.unlink(ttRefFile)
#        if os.path.exists(numpyRefFile):
#            os.unlink(numpyRefFile)
#        global eventCodeWhichDoesntExist
#        global evrCodeAlwaysPresent
#        psana.setOption('TimeTool.Analyze.get_key',opal_src)
#        psana.setOption('TimeTool.Analyze.put_key',put_key)
#
#        # this is a new option to get the time tool data as ndarrays, visible by Python
#        psana.setOption('TimeTool.Analyze.put_ndarrays',True)
#
#        # we went to build a reference from all shots.
#        psana.setOption('TimeTool.Analyze.eventcode_nobeam',evrCodeAlwaysPresent)
#
#        #don't skip any events, laser is always on, set to jnk event code
#        psana.setOption('TimeTool.Analyze.eventcode_skip',eventCodeWhichDoesntExist)
#
#        # don't use ipm to detect presence of beam, we alway get beam
#        psana.setOption('TimeTool.Analyze.ipm_get_key','')
#        psana.setOption('TimeTool.Analyze.calib_poly','0 1 0')   # no calibration
#        psana.setOption('TimeTool.Analyze.projectX',True) 
#        psana.setOption('TimeTool.Analyze.proj_cut',0)
#        global sig_roi_x
#        global sig_roi_y
#        psana.setOption('TimeTool.Analyze.sig_roi_x','%d %d' % (sig_roi_x[0],sig_roi_x[1]))
#        psana.setOption('TimeTool.Analyze.sig_roi_y','%d %d' % (sig_roi_y[0],sig_roi_y[1]))
#
#        # no side band analysis
#        psana.setOption('TimeTool.Analyze.sb_roi_x','')
#        psana.setOption('TimeTool.Analyze.sb_roi_y','')
#        psana.setOption('TimeTool.Analyze.sb_avg_fraction',sb_avg_fraction)
#
#        psana.setOption('TimeTool.Analyze.ref_avg_fraction',ref_avg_fraction)
#        psana.setOption('TimeTool.Analyze.ref_load', '')
#        # store the final reference 
#        psana.setOption('TimeTool.Analyze.ref_store', ttRefFile)
#        psana.setOption('TimeTool.Analyze.weights', sxr_timetool_weights)
#
#        # when the psana option events is 0, psana goes through all the data
#        if refNumEvents is None:
#            psana.setOption('psana.events',0)
#        else:
#            psana.setOption('psana.events',refNumEvents)
#        psana.setOption('modules','TimeTool.Analyze')
#        ds = psana.DataSource(dataSource)
#        events = ds.events()
#        reportEventInterval = 50
#        global evrSrc
#
#        # we will also build up a average of these images to use in interactive plotting.
#        numBkg = 0
#        bkg = None
#
#        opalPsanaSource = psana.Source(opal_src)
#
#        print "-----Building Reference:-----"
#        for ii, evt in enumerate(events):
#            evrData = evt.get(psana.EvrData.DataV3, evrSrc)
#            if evrData is None:
#                print "   no evr data in event %d, could be xtcav data, set stream=0-12 in datasource" % ii
#                continue
#            hasAlwaysPresent = False
#            hasDoesntExist = False
#            for fifoEvent in evrData.fifoEvents():
#                if fifoEvent.eventCode() == evrCodeAlwaysPresent:
#                    hasAlwaysPresent = True
#                if fifoEvent.eventCode() == eventCodeWhichDoesntExist:
#                    hasDoesntExist = True
#            if not hasAlwaysPresent:
#                print "   Unexpected: evr code %d not found in fifoList - should always be there" % evrCodeAlwaysPresent
#            if hasDoesntExist:
#                print "   Unexpected: evr code %d found in fifoList - it should not be present"  %eventCodeWhichDoesntExist
#
#            opal = evt.get(psana.Camera.FrameV1, opalPsanaSource)
#            if opal is not None:
#                if bkg is None:
#                    bkg = np.array(opal.data16(),np.float)
#                    numBkg = 1
#                else:
#                    bkg *= numBkg/float((numBkg+1))
#                    bkg += ((1.0/float((numBkg+1))) * np.array(opal.data16(),np.float))
#                    numBkg += 1
#
#            if ii % reportEventInterval == 0:
#                print "   event: %d" % ii
#        np.save(numpyRefFile,bkg)
#
#    def analyze(dataSource, 
#                overwrite, 
#                ttRefFile,
#                ttResultFile, 
#                analNumEvents,
#                opal_src,
#                put_key,
#                sxr_timetool_weights):
#        assert os.path.exists(ttRefFile), "time tool reference file doesn't exist"
#
#        if os.path.exists(ttResultFile):
#            if (overwrite):
#                os.unlink(ttResultFile)
#            else:
#                raise Exception("analyze: ttResultFile %s already exists and overwrite is False" % ttResultFile)
#
#        global eventCodeWhichDoesntExist
#        psana.setOption('TimeTool.Analyze.get_key',opal_src)
#        psana.setOption('TimeTool.Analyze.put_key',put_key)
#
#        # we need to override any option that was set above as psana remembers config options
#        # now we want TimeTool.Analyze to always see laser on and beam
#        psana.setOption('TimeTool.Analyze.eventcode_nobeam',eventCodeWhichDoesntExist)
#
#        #don't skip any events, laser is always on, set to jnk event code
#        psana.setOption('TimeTool.Analyze.eventcode_skip',eventCodeWhichDoesntExist)
#
#        # don't use ipm to detect presence of beam, we alway get beam
#        psana.setOption('TimeTool.Analyze.ipm_get_key','')
#        psana.setOption('TimeTool.Analyze.calib_poly','0 1 0')   # no calibration
#        psana.setOption('TimeTool.Analyze.projectX',True) 
#        psana.setOption('TimeTool.Analyze.proj_cut',0)
#        global sig_roi_x
#        global sig_roi_y
#        psana.setOption('TimeTool.Analyze.sig_roi_x','%d %d' % (sig_roi_x[0],sig_roi_x[1]))
#        psana.setOption('TimeTool.Analyze.sig_roi_y','%d %d' % (sig_roi_y[0],sig_roi_y[1]))
#        psana.setOption('TimeTool.Analyze.sb_roi_x','')
#        psana.setOption('TimeTool.Analyze.sb_roi_y','')
#        psana.setOption('TimeTool.Analyze.sb_avg_fraction',sb_avg_fraction)
#        psana.setOption('TimeTool.Analyze.ref_avg_fraction',ref_avg_fraction)
#
#        # load reference from previous step
#        psana.setOption('TimeTool.Analyze.ref_load', ttRefFile)
#        # do not store a reference
#        psana.setOption('TimeTool.Analyze.ref_store', '')
#        psana.setOption('TimeTool.Analyze.weights', sxr_timetool_weights)
#
#        # configure the Translator to only translate the ndarrays that TimeTool.Analyze will emit
#        psana.setOption('Translator.H5Output.output_file',ttResultFile)
#        # turn off compression and shuffle, shuffle is only useful if compression is on
#        psana.setOption('Translator.H5Output.deflate',-1)
#        psana.setOption('Translator.H5Output.shuffle',False)
#        psana.setOption('Translator.H5Output.overwrite',overwrite)
#
#        # key options: exclude all the psana data and epics data
#        psana.setOption('Translator.H5Output.type_filter','include TimeTool')
#        psana.setOption('Translator.H5Output.store_epics','no')
#        # now only ndarrays will be translated
#
#        if analNumEvents is None:
#            psana.setOption('psana.events',0)
#        else:
#            psana.setOption('psana.events',analNumEvents)
#        # important: load Translator.H5Output after TimeTool.Analyze so that it sees the
#        # ndarrays that it puts in the Event
#        psana.setOption('modules','TimeTool.Analyze Translator.H5Output')
#
#        ds = psana.DataSource(dataSource)
#        events = ds.events()
#        reportEventInterval = 50
#        global evrSrc
#        print "---Analyze---"
#        for ii, evt in enumerate(events):
#            evrData = evt.get(psana.EvrData.DataV3, evrSrc)
#            if evrData is None:
#                print "   no evr data in event %d, could be xtcav data, set stream=0-12 in datasource" % ii
#                continue
#            hasDoesntExist = False
#            for fifoEvent in evrData.fifoEvents():
#                if fifoEvent.eventCode() == eventCodeWhichDoesntExist:
#                    hasDoesntExist = True
#            if hasDoesntExist:
#                print "   Unexpected: evr code %d found in fifoList - it should not be present"  %eventCodeWhichDoesntExist
#            if ii % reportEventInterval == 0:
#                print "   event: %d" % ii
#
#######################################
#    
#class TimeToolValues(object):
#    '''Class to get the timeTool values from an h5 group.
#    Loads entire datasets for timeTool values on initialization for performance, and to
#    get around HDF5 bug in 1.8.13:
#        https://github.com/h5py/h5py/issues/480
#         which boils down to a hdf5 bug - I believe HDFFV-8917. The bug seems to be triggered
#         by many repeated accesses to a dataset.
#    '''
#    def __init__(self, h5calibCycle, put_key):
#        '''ARGS:
#        h5calibCycle  - h5group for a calib cycle, as returned by h5py
#        put_key       - the timeTool prefix used for data stored in the hdf5 file
#        '''
#        self.h5calibCycle = h5calibCycle
#        self.put_key = put_key
#
#        # what TimeTool data types are available in this release?
#        timeToolDataVersions = [dataVersion for dataVersion in \
#                                dir(psana.TimeTool) if dataVersion.startswith('DataV')]
#
#        ttGroup = None
#        for timeToolDataVersion in timeToolDataVersions:
#            ttGroupPath = 'TimeTool::%s/noSrc__%s' % (timeToolDataVersion, put_key)
#            try:
#                ttGroup = h5calibCycle[ttGroupPath]
#            except KeyError,e:
#                pass
#        if ttGroup is None:
#            groupsThatStartWithTimeTool = [key for key in h5calibCycle.keys() \
#                                           if key.startswith('TimeTool')]
#            raise Exception(("Could not find a TimeTool group in the translated " + \
#                             "hdf5. Tried these types: %s. The groups that start " + \
#                             "with TimeTool in the calib cycle are: %s. Maybe the " + \
#                             "TimeTool package in this release doesn't write the " + \
#                             "high level object, or TimeTool is not finding anything " + \
#                             "to analyze") %  (timeToolDataVersions, \
#                                               groupsThatStartWithTimeTool))
#
#        self.ttTime = ttGroup['time'][:]
#        ttData = ttGroup['data']
#        self.amplitude = ttData['amplitude']
#        self.nxt_amplitude = ttData['nxt_amplitude']
#        self.position_pixel = ttData['position_pixel']
#        self.position_fwhm = ttData['position_fwhm']
#        self.position_time = ttData['position_time']
#        self.ref_amplitude = ttData['ref_amplitude']
#
#    def findSecondFiducial(self, sec,fid):
#        '''finds index in ttTime from sec/fid
#        ARGS:
#          sec  - seconds to match
#          fid  - fiducials to match
#        RET:
#          index  - the 0-up index of the time dataset which has a matching second and fiducial value,
#                   or None if not found, or more than one record matched
#        '''
#        fidMatch = self.ttTime['fiducials']==fid
#        secMatch = self.ttTime['seconds']==sec
#        matchBoth = fidMatch & secMatch
#        whereArray = np.where(matchBoth)[0]
#        if len(whereArray) == 0:
#            return None
#        if len(whereArray)>1:
#            print "warning: sec/fid matches more than one position in h5 time dataset, possible with damaged data/split events. sec=%r fid=%r" % (sec, fid)
#            return None
#        return whereArray[0]
#
#    def get(self, sec, fid):
#        '''ARGS:
#        sec - seconds
#        fid - fiducials
#        Returns a dict with the keys 
#        'amplitude', 'nxt_amplitude', 'position_pixel', 
#        'position_fwhm', 'position_time', 'ref_amplitude'
#        
#        values will be None or the TimeTool value found
#        '''
#        ttVals = {'amplitude':None, 
#                  'nxt_amplitude':None, 
#                  'position_pixel':None, 
#                  'position_fwhm':None, 
#                  'position_time':None, 
#                  'ref_amplitude':None}
#
#        matchIndex = self.findSecondFiducial(sec,fid)
#        if matchIndex is not None: 
#            ttVals['amplitude'] = self.amplitude[matchIndex]
#            ttVals['nxt_amplitude'] = self.nxt_amplitude[matchIndex]
#            ttVals['position_pixel'] = self.position_pixel[matchIndex]
#            ttVals['position_fwhm'] = self.position_fwhm[matchIndex]
#            ttVals['position_time'] = self.position_time[matchIndex]
#            ttVals['ref_amplitude'] = self.ref_amplitude[matchIndex]
#        return ttVals
#            
#def plotEvent(evt, evtIdx, timeToolValues,  opalSrc, opalBkg, plot_offset_x):
#    global sig_roi_x
#    global sig_roi_y
#    eventId = evt.get(psana.EventId)
#    sec = eventId.time()[0]
#    fid = eventId.fiducials()
#    ttVals = timeToolValues.get(sec, fid)
#    opal = evt.get(psana.Camera.FrameV1, opalSrc)
#    if ttVals['position_pixel'] is None or opal is None:
#        print "this event not found in h5 file, or no opal found for in this event (eventIdx=%d)" % evtIdx
#    else:
#        print "evtIdx=%4d fltpos=%7.2f ampl=%7.5f nxtampl=%7.5f" % (evtIdx, \
#                           ttVals['position_pixel'], ttVals['amplitude'], ttVals['nxt_amplitude'])
#        opalArr = np.array(opal.data16(), np.float)-opalBkg
#        opalArr[opalArr<0.0]=0.0
#        plt.figure(1)
#        plt.clf()
#        plt.imshow(np.log(1.0+opalArr))
#        plt.hold(True)
#        plt.xlim([0,opalArr.shape[1]])
#        plt.ylim([opalArr.shape[0],0])
#        plt.plot([ttVals['position_pixel'] + plot_offset_x, 
#                  ttVals['position_pixel'] + plot_offset_x],sig_roi_y, '-r')
#        # plot the ROI box
#        plt.plot([sig_roi_x[0], sig_roi_x[1], sig_roi_x[1], sig_roi_x[0], sig_roi_x[0] ],
#                 [sig_roi_y[0], sig_roi_y[0], sig_roi_y[1], sig_roi_y[1], sig_roi_y[0] ], '-w')
#        plt.title('event %d' % evtIdx)
#        plt.draw()
#
#    res = raw_input("hit enter for next event, +/- n to jump n events, e for ipython, q to quit: ")
#    res = res.lower().strip()
#    if res == 'q':
#        return 'quit'
#    if res == '':
#        return int(1)
#    if res == 'e':
#        IPython.embed()
#        return int(1)
#    return int(res)
#
##### end helper functions
##########################
#
#    
#def interactivePlots(dataSource, 
#                     ttResultFile, 
#                     opal_src,
#                     put_key,
#                     sxr_timetool_weights,
#                     plot_offset_x,
#                     numpyRefFile):
#    assert os.path.exists(ttResultFile), "time tool result file doesn't exist"
#    assert os.path.exists(numpyRefFile), "numpy background ref doesn't exist"
#        
#    bkg = np.load(numpyRefFile)
#    h5 = h5py.File(ttResultFile,'r')
#    h5Run0 = h5['/Configure:0000/Run:0000']
#    assert 'CalibCycle:0001' not in h5Run0.keys(), "Did not expect more than one calib cycle in output data. Script will have to be changed"
#    calibCycle0 = h5Run0['CalibCycle:0000']
#    timeToolValues = TimeToolValues(calibCycle0, put_key)
#    plt.ion()
#    # clear psana options set from above functions (in case 
#    psana.setOption('psana.modules','') 
#    psana.setOption('psana.events',0)    
#    ds = psana.DataSource(dataSource)
#    opalSrc = psana.Source(opal_src)
#    runs = ds.runs()
#    for run in runs:
#        times = run.times()
#        idx = 0
#        while idx >=0 and idx < len(times):
#            evt = run.event(times[idx])
#            res = plotEvent(evt,idx,timeToolValues,opalSrc,bkg,plot_offset_x)
#            del evt
#            if isinstance(res,str):
#                if res == 'quit':
#                    print "exiting due to quit"
#                    sys.exit(0)
#                else:
#                    print "unkown"
#                    sys.exit(1)
#            idx += res
#            if idx < 0:
#                idx = 0
#                print "warning: you jumped past the start, reset index to 0"
#    print "finished run: %r idx=%d" % (run,idx)
