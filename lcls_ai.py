import epics
import device

class ai(device.Device):
    "Simple analog input device"

    fields = {
        'value':                  ('VAL', 'value'),
        'units':                  ('EGU',  'Engineering Units '),
        'high_opr':               ('HOPR', 'high opr'),
        'low_opr':                ('LOPR', 'low opr'), 
        'precision':              ('PREC', 'Display Precision '),
        'name':                   ('NAME', 'PV Name'),
        'description':            ('DESC', 'Description'),
        'device_type':            ('DTYP', 'Device type'),
        'record_type':            ('RTYP', 'Record Type'),
        'raw_drive':              ('RVAL', 'Raw Desired Value  '),
        'raw_offset':             ('ROFF', 'Raw Offset'),
        'linr':                   ('LINR', '??'),
        'eguf':                   ('EGUF', '??'),
        'egul':                   ('EGUL', '??'),
        'aoff':                   ('AOFF', '??'),
        'eslo':                   ('ESLO', '??'),
        'eoff':                   ('EOFF', '??'),
        'hihi':                   ('HIHI', '??'),
        'lolo':                   ('LOLO', '??'),
        'high':                   ('HIGH', '??'),
        'low':                    ('LOW', '??'),
        'hhsv':                   ('HHSV', '??'),
        'llsv':                   ('LLSV', '??'),
        'hsv':                    ('HSV', '??'),
        'lsv':                    ('LSV', '??'),
        'hyst':                   ('HYST', '??'),
    }
    records = {}        

    _attr_tuple = {}
    _alias = {}
    _fields = {}
    _records = {}
    _mutable = False

    _nonpvs = ('_prefix', '_pvs', '_delim', '_init', '_init_list',
               '_alias', '_fields', '_records')
    _info_attrs = ['DESC', 'VAL', 'EGU', 'PREC', 'RTYP']
    _log_attrs = []
    _init_list = _info_attrs

#    attrs = ('VAL', 'EGU', 'HOPR', 'LOPR', 'PREC', 'NAME', 'DESC',
#             'DTYP', 'RTYP', 'RVAL', 'ROFF', 'EGUF', 'EGUL', 'LINR', 
#             'AOFF', 'ASLO', 'ESLO', 'EOFF', 'HIHI', 'LOLO',
#             'HIGH', 'LOW', 'HHSV', 'LLSV', 'HSV', 'LSV', 'HYST')

    def __init__(self, name=None,
                 fields=fields, records=records,
                 mutable=False, timeout=3.0):

        if name is None:
            raise NewportException("must supply motor name")

        self._attr_tuple = dict(records.items() + fields.items())
        self._alias = {item[0]: item[1][0] for item in records.items() + fields.items()}

        self._fields = [item[1][0] for item in fields.items()]
        self._records = [item[1][0] for item in records.items()]
        
        if name.endswith('.'):
            name = name[:-1]

        self._prefix = name

        device.Device.__init__(self, name, delim='.',
                                     attrs=self._init_list,
                                     mutable=False,
                                     timeout=timeout)

        rectype = self.get('RTYP')
        if rectype != 'ai':
            raise ImsException("%s is not epics ai record" % name)

        # self.put('disabled', 0)
        self._callbacks = {}


    def _ai_repr(self):
        return '<ai epics record: {:s} = {:.2f} {:s} : {:s}>'.format(
                self._prefix.rstrip('.'), self.VAL, self.EGU,  self.DESC)

    def __repr__(self):
        self.show_info()
        return self._ai_repr()

    def __str__(self):
        return self.__repr__()

    def __getattr__(self, attr):
        " internal method "
        if attr in self._alias:
            attr = self._alias[attr]

        if attr in self._pvs:
            return self.get(attr)
        elif attr in self.__dict__:
            return self.__dict__[attr]
        elif self._init and not attr.startswith('__') and (self._mutable or attr in self._fields):
            pv = self.PV(attr, connect=True)
            if not pv.connected:
                raise NewportException("EpicsMotor has no attribute %s" % attr)
            return self.get(attr)

        else:
            return self._pvs[attr]

    def __setattr__(self, attr, val):
        # print 'SET ATTR ', attr, val
        if attr in ('name', '_prefix', '_pvs', '_delim', '_init',
                    '_alias', '_fields', '_records', '_attr_tuple',
                    '_nonpvs', '_callbacks'):
            self.__dict__[attr] = val
            return
        if attr in self._alias:
            attr = self._alias[attr]
        if attr in self._pvs:
            return self.put(attr, val)
        elif attr in self.__dict__:
            self.__dict__[attr] = val
        elif self._init and self._mutable:
            try:
                self.PV(attr)
                return self.put(attr, val)
            except:
                raise ImsException("EpicsMotor has no attribute %s" % attr)

    def __dir__(self):
        # taken from device.py: there's no cleaner method to do this until Python 3.3
        all_attrs = set(self._alias.keys() + self._pvs.keys() +
                        self._fields + self._records +
                        list(self._nonpvs) +
                        self.__dict__.keys() + dir(device.Device))
        return list(sorted(all_attrs))

#    def get_pv(self, attr):
#        "return  PV for a field"
#        return self.PV(attr)

    def get_info(self):
        """Return information, current field values.
        """
        out = {}
        for attr in self._info_attrs:
            out[attr] = self.get(attr, as_string=True)
        return out

    def show_info(self):
        """Show basic pv information. 
           (attributes in _info_attrs)
        """
        self.show_attrs(self._info_attrs)

    def show_all(self):
        """Show all pv attributes except for log messages. 
        """
        self.show_attrs()

    def show_attrs(self, *args):
        """Show pv attributes.
        """
        if len(args) == 1:
            if type(args[0]) is list:
                attrs = args[0]
            else:
                attrs = args
        elif len(args) > 1:
            attrs = args
        else:
            attrs = [attr for attr in self._alias.values()
                     if attr not in self._log_attrs]
            attrs.sort()

        attr_desc = {val[0]: val[1] for val in self._attr_tuple.values()}
        attr_alias = {val[0]: alias for alias,val in self._attr_tuple.items()}

        epics.ca.poll()
        out = []
        add = out.append
        add('#'+'-'*80)
        add('# {:14} -- {:50}'.format(self.name,self.DESC))
        add('# {:7} {:22} {:22} {:30}'.format("Attr","Alias","Value","Description"))
        add('#'+'-'*80)
        epics.ca.poll()
        for attr in attrs:
            desc = attr_desc[attr]
            alias = attr_alias[attr]
            value = self.get(attr, as_string=True)
            if value is None:
                value = 'Not Connected??'
            add('{:9} {:22} {:22} {:30}'.format(attr, alias, value, desc))

        epics.ca.write("\n".join(out))



