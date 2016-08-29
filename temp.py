class foo(object):
    _kwargs = {}
    def __init__(self, **kwargs):
        self._kwargs.update(**kwargs)

    def __getattr__(self, attr):
        if attr in self._kwargs:
            return self._kwargs.get(attr)

    def __setattr__(self, attr, val):
        self._kwargs.update({attr: val})

    def __dir__(self):
        all_attrs =  set(self._kwargs.keys())
        return list(sorted(all_attrs))

    def __repr__(self):
        return str(self._kwargs)

def set(**kwargs):
    foo._kwargs.update(**kwargs)

def get(*args):
    return tuple([foo._kwargs.get(arg) for arg in args])


