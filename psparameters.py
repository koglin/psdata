class Parameters(object):
    """Class for storing parameters
    """
    _parameters = {}

    def show_info(self):
        for det, ddict in self._parameters.items():
            print '--- {:} ---'.format(det)
            for attr, val in ddict.items():
                print '{:16} {:10}'.format(attr,val)

    def write_parameters(self, file):
        """To be added.
        """
        pass

    def read_parameters(self, file):
        """read pareters from file.
        """
        pass

    def __repr__(self):
        self.show_info()
        return '< {:} Parameters stored >'.format(len(self._parameters))

#class ParameterSet(object):
#
#    def __init__(self, name, *args, **kwargs):


def get_parameter(*args):
    if len(args) == 1:
        det, arg = args[0].split('_', 1)
    else:
        det = args[0]
        arg = args[1]

    ddict = Parameters._parameters.get(det)
    if ddict:
        return ddict.get(arg)
    else:
        return None

def set_parameter(det, arg, val):
    params = Parameters()
    if not params._parameters.get(det):
        params._parameters[det] = {arg: val}
    else:
        params._parameters[det].update({arg: val})



