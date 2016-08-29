from pylab import *

class psimage(object):

    def __init__(self, det, name, *args,**kwargs):

        self.vmin = -50
        self.vmax = 50
        self.roi = None
        self._det = det
        self.name = name
        self.data = getattr(det, name)

    @property 
    def image(self):
        """Create image from data_array.
        """
        if self.roi and len(self.roi) == 4:
            return self.data[self.roi[0]:self.roi[1],self.roi[2]:self.roi[3]]
        else:
            return self.data

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

    def new_plot(self):
        plt.ion()
        plt.imshow(self.image)
        plt.clim(vmin=self.vmin,vmax=self.vmax)
        plt.colorbar()
        plt.title(self.desc)

    def plot(self, nevents=1, projection=False, monitor=False, next_event=False):
        """Plot CSpad image.
        """
        ievent = 0
        try:
            plt.ion()
            plt.show()
            while ievent < nevents or monitor:
                if ievent > 0 or next_event or monitor:
                    self._det._data.next_event()

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
                start=True, stop=False):
        """Publish plot with psmon.
           Plot can be read on multiple machines with psplot.
        """
        if projection:
            if projection is 'y':
                plotdata = 'yprojection'
            else:
                plotdata = 'xprojection'

            if not name:
                name = self._det._name+'_'+plotdata

            if not title:
                if self._desc:
                    title = self._det._desc+' '+plotdata
                else:
                    title = self._det._name+' '+plotdata

        else:
            if not name:
                name = self._det._name+'_image'

            if not title:
                if self._det._desc:
                    title = self._det._desc
                else:
                    title = self._det._name

        if start:
            if projection:
                self._det.add_psplot(plotdata, plot_type='XYplot',
                                name=name, title=title)

            else:
                self._det.add_psplot('image', plot_type='Image',
                                name=name, title=title)

        if stop:
            self._det.del_psplot(name)


