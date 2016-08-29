import psdata
import os

from pylab import *

import ROOT
import pickle

class pim_fit(psdata.Detector):
    """Beamline PIM (Pop-in Monitor)  Detector Class of psdata.Detector.
    """

    def __init__(self,*args,**kwargs):

        psdata.Detector.__init__(self,*args,**kwargs)
        
        self._default_parameters = {'pedestal': 0, 'roi': None}
        self.set_parameter(**self._default_parameters)
       
        self.fits = []
        self.trends = {
                'xmean': [],
                'ymean': [],
                'xrms' : [],
                'yrms' : [],
                'time' : [],
                'g1frac': [],
                'g2frac': [],
                'g3frac': [],
                'chi2ndof': [],
                }

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
        
        if self._name in 'Dg2Pim':
            mar = [ # for Dg2
                    [60, 15, 75],
                    [90, 60, 100],
                    [135, 100, 160],
                    ]

            war = [
                    [5,3,15],
                    [5,3,25],
                    [5,3,25],
                    ]
        else:
            mar = [ # for Dg1
                    [100 ,60 ,120 ],
                    [120 ,100 ,200 ],
                    [230 ,200 ,300 ],
                    ]

            war = [
                    [15, 3, 50],
                    [15, 3, 50],
                    [15, 3, 80],
                    ]
   
        self.set_parameter(pedestal=pedestal, mar=mar, war=war)

        self._init_time = self._data.EventId.time[0] + self._data.EventId.time[1]/1.e9

    def root_plot_init(self):
        """Initialize Justin's root plots.
        """

        self.canvas = ROOT.TCanvas()
        self.myplots = myplotsclass()

        self.add_event_function('_on_next_event')
        self.add_event_function('_on_next_summary', nevents=30)
        self.add_event_function('_on_next_plot', nevents=5)
        self.add_event_function('_on_next_eventCode163', eventCode=163)

    def append_fits(self):
        self.fits.append((self.fit0(), self.fit1()))

    def append_trends(self):
        self.trends['xmean'].append(self.fits[-1][1][1].GetMean())
        self.trends['xrms'].append(self.fits[-1][1][1].GetRMS())
        self.trends['ymean'].append(self.fits[-1][0][1].GetMean())
        self.trends['yrms'].append(self.fits[-1][0][1].GetRMS())
        self.trends['time'].append(self._data.EventId.time[0] \
                                  +self._data.EventId.time[1]/1.e9 - self._init_time )
        self.trends['chi2ndof'].append( self.fits[-1][1][2].GetChisquare() \
                                        / self.fits[-1][1][2].GetNDF() )
        if self.trends['chi2ndof'][-1] < 100:
            self.total = self.fits[-1][1][2].GetParameter(1) \
                       + self.fits[-1][1][2].GetParameter(4) \
                       + self.fits[-1][1][2].GetParameter(7)
            self.trends['g1frac'].append( self.fits[-1][1][2].GetParameter(1) / self.total )
            self.trends['g2frac'].append( self.fits[-1][1][2].GetParameter(4) / self.total )
            self.trends['g3frac'].append( self.fits[-1][1][2].GetParameter(7) / self.total )
        else:
            self.trends['g1frac'].append(0 )
            self.trends['g2frac'].append(0 )
            self.trends['g3frac'].append(0 )

    def _on_next_event(self, **kwargs):
        """Functions to be performed on each next_event.
        """
        self.append_fits()
        self.append_trends()

    def _on_next_plot(self, **kwargs):
        """Functions to be performed to summarize data.
        """
        self.update_plots()
    
    def _on_next_summary(self, **kwargs):
        """Functions to be performed to summarize data.
        """
        self.show_fit_summary()

    def _on_next_eventCode163(self, **kwargs):
        """Functions to be performed for each eventCode 163.
        """
        for i in range(4):
            print "here "*10

    def show_fit_summary(self): 
        print "{:>7s} {:>7s} {:>7s} {:>7s} N={:0.0f}".format( \
                "xmean","xrms","ymean","yrms",self._data.ievent)
        print "{:7.1f} {:7.1f} {:7.1f} {:7.1f} {:}".format( \
                self.fits[-1][1][1].GetMean(), 
                self.fits[-1][1][1].GetRMS(),
                self.fits[-1][0][1].GetMean(), 
                self.fits[-1][0][1].GetRMS(),
                repr(self._data.evr0.eventCodes))

    def update_plots(self):
        self.myplots.update_image(self.image)
        self.myplots.update_trends(self.trends)
        self.myplots.update_projections(self.image, self.fits)
        self.myplots.update_modes(self.trends,self.fits)

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


    def publish_fits(self):
        self.add_psplot('xprojection','xfit', eventCode=[-162], 
                        local=True, plot_type='XYPlot')
        self.add_psplot('yprojection','yfit', eventCode=[-162], 
                        local=True, plot_type='XYPlot')

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

    def loadhist(self, name):
        data = getattr(self, name)
        hist = ROOT.TH1F('hist_'+name+repr(self._data.ievent),name,len(data),0,len(data))
        mymin = data.min()
        for ii,val in enumerate(data):
            hist.SetBinContent(ii,val - mymin )
        return hist

    @property
    def xfit(self):
        _, h, f = self.fit1()
        return [f.Eval(i) for i in range(self.xprojection.size)]

    @property
    def yfit(self):
        _, h, f = self.fit0()
        return [f.Eval(i) for i in range(self.yprojection.size)]

    def fit0(self, draw=False):
        fitrange = [0,len(self.yprojection)]
        hist = self.loadhist('yprojection')
        tf1 = ROOT.TF1('ff_y_{:}'.format(self._data.ievent),"[0]+gaus(1)", fitrange[0], fitrange[1])
        tf1.FixParameter(0,hist.GetMinimum())
        tf1.SetParameter(1,100)
        tf1.SetParameter(2,0.5*len(self.yprojection))
        tf1.SetParameter(3,20)

        if draw:
            self.canvas.cd()
            hist.Fit(tf1,'QR')
            self.canvas.Update()
            return self.canvas, hist, tf1
        else:
            hist.Fit(tf1,'NQ0R')
            return None, hist, tf1

    def fit1(self, draw=False):
        fitrange = [0,len(self.xprojection)]
        hist = self.loadhist('xprojection')
        tf1  = ROOT.TF1('ff_x_{:}'.format(self._data.ievent), \
                "[0]+gaus(1)+gaus(4)+gaus(7)",fitrange[0],fitrange[1])
        tf1.FixParameter(0,hist.GetMinimum()) # offset

        tf1.SetParameter(1,10) # gaus1 area
        tf1.SetParLimits(1,0 ,1000000 )
        tf1.SetParameter(2,self.mar[0][0]) # gaus1 mean
        tf1.SetParLimits(2,self.mar[0][1], self.mar[0][2] )
        tf1.SetParameter(3,self.war[0][0]) # gaus1 width
        tf1.SetParLimits(3,self.war[0][1], self.war[0][2] )

        tf1.SetParameter(4,50) # gaus2 area
        tf1.SetParLimits(4,0 ,1000000 )
        tf1.SetParameter(5,self.mar[1][0]) # gaus2 mean
        tf1.SetParLimits(5,self.mar[1][1], self.mar[1][2] )
        tf1.SetParameter(6,self.war[1][0]) # gaus2 width
        tf1.SetParLimits(6,self.war[1][1], self.war[1][2] )

        tf1.SetParameter(7,20) # gaus3 area
        tf1.SetParLimits(7,0  ,1000000 )
        tf1.SetParameter(8,self.mar[2][0]) # gaus3 mean
        tf1.SetParLimits(8,self.mar[2][1], self.mar[2][2] )
        tf1.SetParameter(9,self.war[2][0]) # gaus3 width
        tf1.SetParLimits(9,self.war[2][1], self.war[2][2] )

        if draw==True:
            self.canvas.cd()
            hist.Fit(tf1,'QR')
            self.canvas.Update()
            return self.canvas,hist,tf1
        else:
            hist.Fit(tf1,'NQ0R')
            return None,hist,tf1


class myplotsclass:
    def __init__(self):
        matplotlib.pyplot.ion()
        self.fig0 = matplotlib.pyplot.figure() # trends
        #self.thismanager0 = matplotlib.pyplot.get_current_fig_manager()
        #self.thismanager0.window.wm_geometry("+10+10")
        self.fig2 = matplotlib.pyplot.figure() # image
        #self.thismanager2 = matplotlib.pyplot.get_current_fig_manager()
        #self.thismanager2.window.wm_geometry("+800+10")
        self.fig3 = matplotlib.pyplot.figure() # projections
        #self.thismanager3 = matplotlib.pyplot.get_current_fig_manager()
        #self.thismanager3.window.wm_geometry("+10+800")
        self.fig5 = matplotlib.pyplot.figure() # modal content
        #self.thismanager5 = matplotlib.pyplot.get_current_fig_manager()
        #self.thismanager5.window.wm_geometry("+800+800")
        return

    def update_trends(self,trends):
        matplotlib.pyplot.figure(self.fig0.number)
        matplotlib.pyplot.clf()
        self.fig0.add_subplot(2,1,1)
        matplotlib.pyplot.plot(trends['time'],trends['xmean'],label='x mean')
        matplotlib.pyplot.plot(trends['time'],trends['ymean'],label='y mean')
        matplotlib.pyplot.title('MEAN')
        #matplotlib.pyplot.xlabel('time (s)')
        matplotlib.pyplot.legend()

        self.fig0.add_subplot(2,1,2)
        matplotlib.pyplot.plot(trends['time'],trends['xrms'],label='x rms')
        matplotlib.pyplot.plot(trends['time'],trends['yrms'],label='y rms')
        matplotlib.pyplot.title('RMS')
        matplotlib.pyplot.xlabel('time (s)')
        matplotlib.pyplot.legend()
        matplotlib.pyplot.draw()
        return

    def update_image(self, image):
        matplotlib.pyplot.figure(self.fig2.number)
        matplotlib.pyplot.clf()
        imgplot = matplotlib.pyplot.imshow( image, interpolation=None )
        imgplot.set_cmap('hot')
        matplotlib.pyplot.colorbar()
        matplotlib.pyplot.draw()
        return

    def update_projections(self, image, fits):
        matplotlib.pyplot.figure(self.fig3.number)
        matplotlib.pyplot.clf()
        matplotlib.pyplot.subplot(2,1,1)
        xproj = image.sum(axis=0)
        matplotlib.pyplot.plot( xproj, drawstyle='steps' )
        matplotlib.pyplot.title('X Projection')
        shapex = [fits[-1][1][2].Eval(i)+xproj.min() for i in xrange(xproj.size)]
        matplotlib.pyplot.plot( shapex, label='fit')

        matplotlib.pyplot.subplot(2,1,2)
        yproj = image.sum(axis=1)
        matplotlib.pyplot.plot( yproj, drawstyle='steps' )
        matplotlib.pyplot.title('Y Projection')
        shapey = [fits[-1][0][2].Eval(i)+yproj.min() for i in xrange(yproj.size)]
        matplotlib.pyplot.plot( shapey, label='fit')
        matplotlib.pyplot.draw()
        return

    def update_modes(self,trends,fits):
        matplotlib.pyplot.figure(self.fig5.number)
        matplotlib.pyplot.clf()

        self.locsg1 = [ ft[1][2].GetParameter(2)/320 for ft in fits ]
        self.locsg2 = [ ft[1][2].GetParameter(5)/320 for ft in fits ]
        self.locsg3 = [ ft[1][2].GetParameter(8)/320 for ft in fits ]

        matplotlib.pyplot.subplot(2,1,1)
        matplotlib.pyplot.scatter( trends['time'], self.locsg1, \
                s=[100.*v for v in trends['g1frac']], color='r', label='G1 frac.')
        matplotlib.pyplot.scatter( trends['time'], self.locsg2, \
                s=[100.*v for v in trends['g2frac']], color='g', label='G2 frac.')
        matplotlib.pyplot.scatter( trends['time'], self.locsg3, \
                s=[100.*v for v in trends['g3frac']], color='b', label='G3 frac.')
        matplotlib.pyplot.title('modal content')
        #matplotlib.pyplot.xlabel('time (s)')
        matplotlib.pyplot.legend()

        matplotlib.pyplot.subplot(2,1,2)
        matplotlib.pyplot.plot( trends['time'], trends['chi2ndof'], \
                label='chi2/ndof', drawstyle='steps')
        matplotlib.pyplot.title('ChiSquare/NDF')
        matplotlib.pyplot.xlabel('time (s)')
        matplotlib.pyplot.draw()
        return


