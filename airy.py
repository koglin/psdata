import psdata

from pylab import *
from scipy.special import airy


class airy(psdata.Detector):
    """Airy sim  Detector Class of psdata.Detector.
    """

    def __init__(self,*args,**kwargs):
        self.x = np.arange(-850,851,1).reshape(1701,1)
        self.y = np.arange(-850,851,1)
        self.r = np.sqrt(self.x**2+self.y**2)
        self.desc = 'sim'
        self._ifig = -1
        self.spacing = 2 

    def model(self, offset=0., sigma=500., period=50., amplitude=300., **kwargs):
        return np.exp(-self.r**2/sigma**2)*(1.+np.sin(self.r/period))/2.*amplitude+offset

    def back(self, **kwargs):
#        return np.random.poisson(self.model(**kwargs)*20.)/20.
        return self.model(**kwargs)

    @property
    def ixsig(self):
        return range(0,1701-5,self.spacing)
    
    @property
    def iysig(self):
        return range(0,1701-5,self.spacing)
  
    @property
    def xsig(self):
        return np.arange(1701)[self.ixsig]

    @property
    def ysig(self):
        return np.arange(1701)[self.iysig]

    @property
    def axsig(self):
        return self.xsig*(self.ysig*0.+1)
        
    @property
    def aysig(self):
        return self.ysig*(self.xsig*0.+1)

    def signal(self, signal=10., spacing=10, **kwargs):
        asig = self.r*0

        for ix in self.ixsig:
            for iy in self.iysig:
                asig[ix,iy] = signal

        return asig

    @property
    def noise(self, **kwargs):
        return np.random.normal(1.,1., (1701,1701))

    def ana(self, resolution=False, subtracted=False, signal=10, npix=1, 
            threshold=3., switch=100., lownoise=10., highnoise=0.1, **kwargs):

        back = self.back(**kwargs)
        sig = self.signal(signal=signal, **kwargs)
        
        noiselevel = back*0.+ highnoise
        thresh = (sig+back)
        aswitch = np.where(thresh > switch)
        print switch, lownoise, highnoise
        print (thresh > switch).sum()
        noiselevel[aswitch] = lownoise
       
        noise = self.noise*noiselevel

        print 'noise: ', noise.sum()
        ana = back + sig # + noise  
#        ana[ ana < 0. ] = 0.

        if resolution:
            asub = ana*0.
            asig = ana*0.
            aesig = ana*0.
            asuberr2 = ana*0.
            ansub = ana*0.
            ares = ana*0.
            abad = ana*0.
            abaderr2 = ana*0.
            anois = ana*0.
            aenois = ana*0.
            amis = ana*0.
            ibad = 2
            for ix in self.ixsig:
                for iy in self.iysig:
                    ixb = ix + ibad
                    iyb = iy + ibad
                    for jx in range(ix-npix,ix+npix):
                        for jy in range(iy-npix,iy+npix):
                            if jx != ix and jy != iy:
                                asub[ix,iy] += ana[jx,jy]
                                asuberr2[ix,iy] += ana[jx,jy]+noiselevel[jx,jy]**2
                                ansub[ix,iy] +=1
                            jxb = jx + ibad
                            jyb = jy + ibad
                            if jxb != ixb and jyb != iyb:
                                abad[ix+ibad,iy+ibad] += ana[jx+ibad,jy+ibad]
                                abaderr2[ix+ibad,iy+ibad] += ana[jx+ibad,jy+ibad]+noiselevel[jx+ibad,jy+ibad]**2

                    asig[ix,iy] = ana[ix,iy] - asub[ix,iy]/float(ansub[ix,iy])
                    aesig[ix,iy] = sqrt(ana[ix,iy] + noiselevel[ix,iy]**2 
                                        + asuberr2[ix,iy]/float(ansub[ix,iy]))
                    ares[ix,iy] = asig[ix,iy]/aesig[ix,iy]
                    anois[ix+ibad,iy+ibad] = ana[ix+ibad,iy+ibad] - abad[ix+ibad,iy+ibad]/ansub[ix,iy]
                    aenois[ix+ibad,iy+ibad] = sqrt(ana[ix+ibad,iy+ibad] + noiselevel[ix+ibad,iy+ibad]**2 
                                        + abaderr2[ix+ibad,iy+ibad]/ansub[ix,iy])
                    amis[ix+ibad,iy+ibad] = anois[ix+ibad,iy+ibad]/aenois[ix+ibad,iy+ibad]

            if threshold:
                ares[ares < threshold] = 0.

            nres = (ares > threshold).sum()
            nmis = (amis > threshold).sum()
            nsig = len(self.ixsig)*len(self.iysig)
            print nres,nsig

            print 'Found ratio = {:} %'.format(nres/float(nsig)*100.)
            print 'Mistake ratio = {:} %'.format(nmis/float(nsig)*100.)

            self.asig = asig
            self.aesig = aesig
            self.ares = ares

            return self.ares

        else:             
            if subtracted is True:
                ana -= self.model(**kwargs)
           
            return ana

    def plot(self, new=False, ifig=None, **kwargs):

        if new or self._ifig == -1:
            self.new_plot(ifig=ifig, **kwargs)
        else:
            if not ifig:
                ifig = self._ifig
            plt.figure(ifig)
            plt.ion()
            self._plot_data = self.ana(**kwargs)
            plt.imshow(self._plot_data)
            plt.title(self.desc)

    def new_plot(self, ifig=None, **kwargs):

        if not ifig:
            self._ifig +=1
            ifig = self._ifig

        plt.figure(ifig)
        plt.ion()
        self._plot_data = self.ana(**kwargs)
        plt.imshow(self._plot_data)
        plt.colorbar()
        plt.title(self.desc)



