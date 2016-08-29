import psdata
import os
import pickle
import ROOT
import numpy
import pylab

class pim_ana(psdata.Detector):
    """Beamline PIM (Pop-in Monitor) Analysis
    Detector Class of psdata.Detector.
    """
    def __init__(self,*args,**kwargs):
        psdata.Detector.__init__(self,*args,**kwargs)

        self.fits = []

        self.trends = pimtrend()
        self.trends.add_trend('xmean'   )
        self.trends.add_trend('ymean'   )
        self.trends.add_trend('xrms'    )
        self.trends.add_trend('yrms'    )
        self.trends.add_trend('g1frac'  )
        self.trends.add_trend('g2frac'  )
        self.trends.add_trend('g3frac'  )
        self.trends.add_trend('chi2ndof')

        self.shotstograb = 10
        self.shotsgrabbed = 0
        self.last_image = None
        self._grabbedshots = []
        self._grab = False
        
        self._init_time = 0
        self._init_time = self.event_time()

        self._default_parameters = {'pedestal': 0, 'roi': None}
        self.set_parameter(**self._default_parameters)
        if self._name in ['Dg1Pim', 'Dg2Pim']:
            if self._name in 'Dg1Pim':
                pedfile = open('cxii6315_r103_Dg1Pim_pedestal.pkl','read')
            if self._name in 'Dg2Pim':
                pedfile=open('cxii6315_r104_Dg2Pim_pedestal.pkl','read')
            if pedfile:
                pedestal = pickle.load(pedfile).transpose()
                pedfile.close()
            else:
                pedestal = 0
        else:
            pedestal = 0


    def setup(self,method='pylab'):
        self.grabbedshotmethod = method
        if method == 'pylab':
            pylab.ion()
            self.figx = pylab.figure()
            self.figy = pylab.figure()
            self.figavgs = pylab.figure()
            self.add_event_function('_on_next_event')
        elif method == 'ROOT':
            self.canx = ROOT.TCanvas()
            self.cany = ROOT.TCanvas()
            #self.cana = ROOT.TCanvas()
        return

    def grab_shots(self):
        # if this shot is dropped: 
        if 163 in self._data.evr0.eventCodes:
            # and store the previous image, 
            self._grabbedshots.append(numpy.array(self.last_image))
            self._grabbedshots.append(numpy.array(self.image))
            # set the grabber flag, 
            self._grab = True
        # if the grabber flag is set:
        elif self._grab and len(self._grabbedshots) < self.shotstograb:
            # store the current image
            self._grabbedshots.append(numpy.array(self.image))
        # if the counter is greater than n (n = 5, 20, something)
        if len(self._grabbedshots) >= self.shotstograb:
            # write out the current stored images
            self.store_grabbed_shots()
            # perform some Analysis
            # make a pretty image
            self.grabbed_shot_analysis()
            # clear the memory.
            self._grab = False
            self._grabbedshots = []
        # always keep the last image, incase the next shot is dropped
        self.last_image = self.image
        return

    def store_grabbed_shots(self):
        return

    def grabbed_shot_analysis_ROOT(self):
        self.grabbedshot_avgs = [0]*len(self._grabbedshots)
        self.grabbedshot_histx = [0]*len(self._grabbedshots)
        self.grabbedshot_histy = [0]*len(self._grabbedshots)
        for ii,img in enumerate(self._grabbedshots):
            self.grabbedshot_histx[ii] = self.loadhist('',vals=img.sum(axis=0))
            self.grabbedshot_histy[ii] = self.loadhist('',vals=img.sum(axis=1))
            self.grabbedshot_avgs[ii] =  (self.grabbedshot_histx[ii].GetMean(),self.grabbedshot_histy[ii].GetMean())
            self.canx.cd()
            if ii == 0:
                self.grabbedshot_histx[ii].Draw()
            else:
                self.grabbedshot_histx[ii].Draw('same')
            self.cany.cd()
            if ii == 0:
                self.grabbedshot_histy[ii].Draw()
            else:
                self.grabbedshot_histy[ii].Draw('same')
            self.canx.Update()
            self.cany.Update()


    def grabbed_shot_analysis(self):
        avgs = [0]*len(self._grabbedshots)
        for ii,img in enumerate(self._grabbedshots):
            avgs[ii] =  (self.loadhist('',vals=img.sum(axis=0)).GetMean(),self.loadhist('',vals=img.sum(axis=1)).GetMean())
        fx = pylab.figure(self.figx.number)
        fx.clear()
        for ii,img in enumerate(self._grabbedshots):
            line = pylab.plot(img.sum(axis=0),label='n+{:0.0f} avg={:0.0f}'.format(ii-1,avgs[ii][0]))
            if ii in [0,2]:
                line[0].set_linewidth(4)
        pylab.legend(fontsize=9)
        pylab.draw()
        fx = pylab.figure(self.figy.number)
        fx.clear()
        for ii,img in enumerate(self._grabbedshots):
            line = pylab.plot(img.sum(axis=1),label='n+{:0.0f} avg={:0.0f}'.format(ii-1,avgs[ii][1]))
            if ii in [0,2]:
                line[0].set_linewidth(4)
        pylab.legend(fontsize=9)
        pylab.draw()
        fa = pylab.figure(self.figavgs.number)
        #fa.clear()
        pylab.plot([a[0] for a in avgs],'b',label='x',drawstyle='steps-mid',alpha=0.6,linewidth=3)
        pylab.plot([a[1] for a in avgs],'g',label='y',drawstyle='steps-mid',alpha=0.6,linewidth=3)
        pylab.legend(('x','y'))
        pylab.draw()
        return

    def event_time(self):
        return self._data.EventId.time[0]+self._data.EventId.time[1]/1.e9 - self._init_time

    def append_trends(self):
        thistime = self.event_time()
        xhist = self.loadhist('xprojection')
        yhist = self.loadhist('yprojection')
        self.trends.add_trend_val('xmean',thistime,xhist.GetMean())
        self.trends.add_trend_val('ymean',thistime,yhist.GetMean())
        self.trends.add_trend_val('xrms',thistime,xhist.GetRMS())
        self.trends.add_trend_val('yrms',thistime,yhist.GetRMS())
        return

    def loadhist(self, name,vals=None):                    
        if name != '':
            data = getattr(self, name)
        else:
            data = vals
        hist = ROOT.TH1F('hist_'+name+repr(self._data.ievent),name,len(data),0,len(data))
        mymin = data.min()
        for ii,val in enumerate(data):
            hist.SetBinContent(ii,val - mymin )
        return hist

    def _on_next_event(self, **kwargs):
        """Functions to be performed on each next_event.
        """
        self.append_trends()
        self.grab_shots()

    @property
    def raw_image(self):
        """Raw image -- currently supporting psana data16.
           This could in the future be updated to take other types of data
           including epics.
        """
        return self.data16.transpose()

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
        return self.image.sum(axis=0)
    
    @property
    def yprojection(self):
        """X projection of image.
        """
        return self.image.sum(axis=1)


class pimtrend(object):
    def __init__(self):
        self._trends = {}
        return

    def add_trend(self,trendname):
        self._trends[trendname] = []
        self._trends[trendname+'seconds'] = []
        return

    def add_trend_val(self,trendname,val,time):
        self._trends[trendname].append(val)
        self._trends[trendname+'seconds'].append(time)
        return

class plotter(object):
    def __init__(self):
        return

