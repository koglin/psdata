

def plot():
    from psmon import publish
    from psmon import plots
    from numpy import random
    publish.init(local=True)
    Z = random.random((50,50))
    im = plots.Image('2', 'title', Z)
    publish.send('foo', im)

# Work in progress
#class PSplots(object): 
#
#    _psplots = {}
#
#    def add_psplot(self, *attrs, **kwargs):
#        """Update psplot.
#           kwargs:
#              local: if True open psplot locally
#              eventCode: check if event code(s) are in data 
#                         (or alternatively not in date with - sign)
#                         see is_eventCodePresent
#        """
#        plot_error = '' 
#
#        attr_name = '_and_'.join(attrs)
#        attr = attrs[0]
#
#        if kwargs.get('local'):
#            local = True
#        else:
#            local = False
#        
#        if 'eventCode' in kwargs:
#            ecstrs = []
#            for ec in kwargs.get('eventCode'):
#                if ec > 0:
#                    ecstrs.append(str(ec))
#                else:
#                    ecstrs.append('not'+str(-ec))
#            ecname = '_'+'_and_'.join(ecstrs)
#            ectitle = ' '+' and '.join(ecstrs)
#        else:
#            ecname = ''
#            ectitle = ''
#
#        if 'name' in kwargs:
#            name = kwargs['name']
#        else:
#            name = self._name+'_'+attr_name+ecname
#
#        if 'title' in kwargs:
#            title = kwargs['title']
#        else:
#            if self._desc:
#                title = self._desc
#            else:
#                title = self._name+' '+attr_name+ectitle
#        if 'ts' in kwargs:
#            ts = kwargs['ts']
#        else:
#            ts = self._data.ievent
#
#        if 'plot_type' in kwargs:
#            plot_type = kwargs['plot_type']
#        else:
#            plot_type = None
#
#        pub_opts = ['eventCode']
#        pub_kwargs = {key: item for key, item in kwargs.items() \
#                      if key in pub_opts}
#
#        if not plot_error and plot_type not in ['Image','XYPlot']:
#            try:
#                ndim = getattr(self,attr).ndim
#                if ndim == 2:
#                    plot_type = 'Image'
#                elif ndim == 1:
#                    plot_type = 'XYPlot'
#                else:
#                    plot_error = 'Data with ndim = {:} not valid'.format(ndim)
#            except:
#                plot_error = 'Data must be numpy array of one or two dimensions.\n'               
#        if not plot_error:
#            if plot_type is 'Image':
#                plt_opts = ['xlabel', 'ylabel', 'aspect_ratio', 'aspect_lock']
#                plt_kwargs = {key: item for key, item in kwargs.items() \
#                              if key in plt_opts}
#                plt_args = {'det': self._name,
#                            'attr': attrs,  
#                            'name': name,
#                            'plot_function': Image,
#                            'ts': ts,
#                            'title': title,
#                            'kwargs': plt_kwargs,
#                            'pubargs': pub_kwargs}
##                for key, item in kwargs.items():
##                    if key in plt_opts:
##                        plt_args[key] = item
#            
#            elif plot_type is 'XYPlot':
#                plt_opts = ['xlabel','ylabel','formats']
#                plt_kwargs = {key: item for key, item in kwargs.items() \
#                              if key in plt_opts}
#                if 'xdata' in kwargs:
#                    xdata = kwargs['xdata']
#                else:
#                    xdata = [np.arange(len(getattr(self, attr))) for attr in attrs]
#                plt_args = {'det': self._name,
#                            'attr': attrs,
#                            'xdata': xdata,
#                            'name': name,
#                            'plot_function': XYPlot,
#                            'ts': ts,
#                            'title': title,
#                            'kwargs': plt_kwargs,
#                            'pubargs': pub_kwargs}
#            else: 
#                plot_error = 'Unknown plot type {:} \n'.format(plot_type)
#
#        if plot_error:
#            print 'Error adding psplot:' 
#            print plot_error
#            return None
#        else:
#            if name in self._data._psplots:
#                if 'subprocess' in self._data._psplots[name]:
#                    self.psplot_kill(name)
#
#            print 'psmon plot added -- use the following to view: '
#            print '--> psplot -s {:} -p 12301 {:}'.format(os.uname()[1], name)
#            print 'WARNING -- see notice when adding for -p PORT specification'
#            print '           if default PORT=12301 not available'
#            self._data._psplots[name] = plt_args
#            if not self._data._publish:
#                publish.init(local=local)
#                self._data._publish = True
#    
##            if kwargs.get('local'):
##                self.psplot_publish_local(name)
#
#    def psplot_publish_local(self, name):
#        """Open plot locallly.
#        """
##        self.psplot_kill(name)
#        subproc = subprocess.Popen('psplot {:} &'.format(name), 
#                             stdout=subprocess.PIPE, shell=True)
#        
#        subproc.poll()
#        self._data._psplots[name]['subprocess'] = subproc 
#self._data.psmon_publish()
#
#    def psplot_kill(self, name):
#        """Kill psplot subprocess.
#        """
#        try:
#            subproc = self._data._psplots[name]['subprocess']
#            print 'Killing old {:} plot with pid {:} ' \
#                  +'before opening new local plot'.format(subproc.pid, name) 
#            subproc.kill()
#        except:
#            pass
#
#    def del_psplot(self, name):
#        """Remove psplot.
#        """
#        self._data.del_psmon(name)
##        if name in self._data._psplots:
##            self._data._psplots.pop(name)
#
#    def publish(self):
#        """Publish _psplots.
#        """
#        if self.exp.startswith('dia') or self._master_evr.is_in_keys:
#            for name, psmon_args in self._psplots.items():
#                det_class = getattr(self,psmon_args['det'])
#
#                eventCode = psmon_args['pubargs'].get('eventCode')
#                ok_eventCode = self.is_eventCodePresent(eventCode)
#
#                if getattr(det_class,'is_in_keys') and ok_eventCode:
##                    print 'publish', name, eventCode, ok_eventCode
#                    psplot_func = psmon_args['plot_function']
#                    if psplot_func is Image:
#                        image = getattr(det_class,psmon_args['attr'][0])
#                        psmon_fnc = psplot_func(self.event_info,
#                                        psmon_args['title'],
#                                        image, 
#                                        **psmon_args['kwargs'])
#                    elif psplot_func is XYPlot:
#                        ydata = [getattr(det_class, attr) for attr in psmon_args['attr']]
#                        psmon_fnc = psplot_func(self.event_info,
#                                        psmon_args['title'],
#                                        psmon_args['xdata'],
#                                        ydata,
#                                        **psmon_args['kwargs'])
#
#                    publish.send(name,psmon_fnc)
#
#    def del_psmon(self, *attrs):
#        """Delete psmon plot.
#        """
#        if len(attrs) == 0:
#            attrs = self._psplots.keys()
#        for attr in attrs:
#            item = self._psplots.pop(attr, None)
#            subproc = item['subprocess']
#            subproc.poll()
#
#
