
import psana
import PsanaDictify

ds = psana.DataSource('exp=CXI/cxic0415:run=88')

#Tab accessible event
evt = PsanaDictify.PsanaDictify(ds.events().next())

#Tab accessible configStore
cs = PsanaDictify.PsanaDictify(ds.env().configStore())

#Tab accessible evr configuration from configStore
evr = PsanaDictify.EvrDictify(ds.env().configStore())


# Getting units and relevant doc strings from standard psana evt access

from PsanaDictify import get_unit_from_doc, get_type_from_doc, func_dict, func_repr

ds = psana.DataSource('exp=CXI/cxic0415:run=88')
evt = ds.events().next()
typ = psana.Bld.BldDataEBeamV7
src = psana.Source('BldInfo(EBeam)')
ebeam = evt.get(typ,src)

# To retrieve a dict that returns the parsed psana evt.get data function for the 
# relevant doc string and units as well as evaluated function:
func_dict(ebeam.ebeamCharge)

# This function represents it in one line:
func_repr(ebeam.ebeamCharge)

# to show all the info in a detector evt object:
def show_info(det):
    for attr in dir(det):
        if not attr.startswith(('_','TypeId','Version')):
            try:
                print func_repr(getattr(det,attr))
            except:
                print 'Warngin: {:} attribute {:} not valid'.format(det, attr)


# from PsanaDictify module in psdata usr repository 

def get_unit_from_doc(doc):
    """Parse the unit from the doc string.
    """
    invalid_units = ['this', 'long', 'all', 'setup', 'given', 'a']
    try:
        usplit = doc.rsplit(' in ')
        if 'Value' in doc and 'converted to' in doc:
            unit = '{:}'.format(doc.rsplit('converted to ')[-1].rstrip('.'))
        elif len(usplit) < 2:
            unit = ''
        else:
            unit = '{:}'.format(usplit[-1])
            unit = unit.rstrip('.').rstrip(',').rsplit(' ')[0].rstrip('.').rstrip(',')
            
            if unit.endswith('(') or unit in invalid_units:
                unit = ''
        
    except:
        unit = ''
    return unit

def get_type_from_doc(doc):
    """Parse the type from the doc string.
    """
    try:
        return  doc.replace('\n',' ').split('-> ')[1].split(' ')[0]
    except:
        return None

def func_dict(func):
    """psana attribute function dictionary.
    """
    fdict = {
             'doc': '',
             'unit': '',
             'str':  'NA',
             'func': func}

    value = func
    try:
        value = value()
    except:
        pass

    try:
        fdict['attr'] = func.__func__.__name__
    except:
        fdict['attr'] = None
    
    if isinstance(value,str):
        fdict['str'] = value
    else:
        if hasattr(value,'mean'):
            fdict['str'] = '<{:.4}>'.format(value.mean())
        else:
            try:
                fdict['attr'] = func.__func__.__name__
                doc = func.__doc__.split('\n')[-1].lstrip(' ')
                fdict['doc'] = doc
                fdict['str'] = '{:10.5g}'.format(value)
                fdict['unit'] = get_unit_from_doc(doc)
                fdict['type'] = get_type_from_doc(doc)
            except:
                try:
                    fdict['attr'] = func.__func__.__name__
                    fdict['str'] = value.__str__()
                except:
                    pass

    fdict['value'] = value

    return fdict

def func_repr(func, name=None):
    """psana function represenatation
    """
    fdict = func_dict(func)
    if name:
        fdict.update({'attr', Name})

    return '{attr:18s} {str:>10} {unit:6} {doc:}'.format(**fdict)


