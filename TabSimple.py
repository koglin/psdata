
import psana
import TabPsanaEvent

class SimpleSource(object):
    """Most basic way to wrap psana.DataSource
    """

    _attrs = ['empty', 'end', 'env', 'liveAvail', 'runs', 'steps']

    def __init__(self, data_source):
        self._Events = Events(psana.DataSource(data_source))

    def events(self):
        return self._Events

    def __getattr__(self, attr):
        if attr in self._attrs:
            return getattr(self._ds, attr)

    def __dir__(self):
        all_attrs = set(self._attrs +
                        self.__dict__.keys() + dir(SimpleSource))
        return list(sorted(all_attrs))

class SimpleEvents(object):
    """Most basic way to get psana in TabEvent
    """

    def __init__(self, ds):
        self._ds = ds

    def __iter__(self):
        return self

    def next(self):
        
        return TabPsanaEvent.TabEvent(self._ds.events().next(), self._ds)


