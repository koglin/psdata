import epics
import device

record_dict = {
    'calc': {
        'reference': 'http://www.aps.anl.gov/epics/EpicsDocumentation/AppDevManuals/RecordRef/Recordref-13.html',
#        'description':  'The calculation or "Calc" record is used to perform algebraic, 
#                         relational, and logical operations on values retrieved from other records. 
#                         The result of its operations can then be accessed by another record 
#                         so that it can be used.', 
        'fields': {
            'value':                  ('VAL', 'value'),
            'units':                  ('EGU',  'Engineering Units '),
            'high_opr':               ('HOPR', 'high opr'),
            'low_opr':                ('LOPR', 'low opr'), 
            'precision':              ('PREC', 'Display Precision '),
            'name':                   ('NAME', 'PV Name'),
            'description':            ('DESC', 'Description'),
            'device_type':            ('DTYP', 'Device type'),
            'record_type':            ('RTYP', 'Record Type'),
            },
        'init':  ['NAME', 'DESC', 'VAL', 'EGU', 'PREC', 'RTYP', 'DTYP'],
        'config': ['DESC', 'EGU', 'PREC', 'DTYP']
        },
    'bo': {
        'reference': 'http://www.aps.anl.gov/epics/EpicsDocumentation/AppDevManuals/RecordRef/Recordref-12.html',
#        'description': 'The normal use for this record type is to store a simple bit (0 or 1) 
#                        value to be sent to a Digital Output module. It can also be used to write 
#                        binary values into other records via database or channel access links. 
#                        This record can implement both latched and momentary binary outputs 
#                        depending on how the HIGH field is configured.',
        'fields': {
            'value':                  ('VAL', 'value'),
            'high_opr':               ('HOPR', 'high opr'),
            'low_opr':                ('LOPR', 'low opr'), 
            'name':                   ('NAME', 'PV Name'),
            'description':            ('DESC', 'Description'),
            'device_type':            ('DTYP', 'Device type'),
            'record_type':            ('RTYP', 'Record Type'),
            'raw_value':              ('RVAL', 'Raw Value  '),
            },
        'init':  ['NAME', 'DESC', 'VAL', 'RVAL', 'PREC', 'RTYP', 'DTYP'],
        'config': ['DESC', 'DTYP']
        },
    'bi': {
#        'description': 'The normal use for this record type is to obtain a binary value of 0 or 1. 
#                        Most device support modules obtain values from hardware and place the value in RVAL. 
#                        For these devices record processing sets VAL = (0,1) if RVAL is (0, not 0). 
#                        Devices support modules may optionally read a value directly into VAL.',
        'fields': {
            'value':                  ('VAL', 'value'),
            'high_opr':               ('HOPR', 'high opr'),
            'low_opr':                ('LOPR', 'low opr'), 
            'name':                   ('NAME', 'PV Name'),
            'description':            ('DESC', 'Description'),
            'device_type':            ('DTYP', 'Device type'),
            'record_type':            ('RTYP', 'Record Type'),
            'raw_value':              ('RVAL', 'Raw Value  '),
            },
        'init':  ['NAME', 'DESC', 'VAL', 'RVAL', 'PREC', 'RTYP', 'DTYP'],
        'config': ['DESC', 'DTYP']
        },
    'ao': {
#        'description': 'The normal use for this record type is to output values to digital-analog 
#                        converters. It is used for all analog outputs to hardware. It can also be 
#                        used to write floating point values to other records via database or channel 
#                        access links. How the user configures the output link determines if the 
#                        record sends its value to a hardware device, a channel access link, or a 
#                        database link. The desired output can be controlled by either an operator 
#                        or a state program, or it can be fetched from another record. ',
        'fields': {
            'value':                  ('VAL', 'value'),
            'units':                  ('EGU',  'Engineering Units '),
            'high_opr':               ('HOPR', 'high opr'),
            'low_opr':                ('LOPR', 'low opr'), 
            'precision':              ('PREC', 'Display Precision '),
            'name':                   ('NAME', 'PV Name'),
            'description':            ('DESC', 'Description'),
            'device_type':            ('DTYP', 'Device type'),
            'record_type':            ('RTYP', 'Record Type'),
            'raw_value':              ('RVAL', 'Raw Value  '),
            'raw_offset':             ('ROFF', 'Raw Offset'),
            },
        'init':  ['NAME', 'DESC', 'VAL', 'RVAL', 'EGU', 'PREC', 'RTYP', 'DTYP'],
        'config': ['DESC', 'EGU', 'PREC', 'DTYP']
        },
    'ai': {
#        'description': 'The normal use for this record type is to obtain an analog value from 
#                        hardware and then convert it to engineering units. Most device support 
#                        modules obtain values from hardware. The record supports alarm limits, 
#                        conversion to engineering units, smoothing, and graphics and control limits.',
        'fields': {
            'value':                  ('VAL', 'value'),
            'units':                  ('EGU',  'Engineering Units '),
            'high_opr':               ('HOPR', 'high opr'),
            'low_opr':                ('LOPR', 'low opr'), 
            'precision':              ('PREC', 'Display Precision '),
            'name':                   ('NAME', 'PV Name'),
            'description':            ('DESC', 'Description'),
            'device_type':            ('DTYP', 'Device type'),
            'record_type':            ('RTYP', 'Record Type'),
            'raw_value':              ('RVAL', 'Raw Value  '),
            'raw_offset':             ('ROFF', 'Raw Offset'),
            'linr':                   ('LINR', 'Type of Conversion'),
            'eguf':                   ('EGUF', 'Engineering Units Full'),
            'egul':                   ('EGUL', 'Engineering Units Low'),
            'aoff':                   ('AOFF', 'Adjustment Offset'),
            'eslo':                   ('ESLO', 'Slope for Linear Conversions'),
#            'eoff':                   ('EOFF', '??'),
#            'hihi':                   ('HIHI', '??'),
#            'lolo':                   ('LOLO', '??'),
#            'high':                   ('HIGH', '??'),
#            'low':                    ('LOW', '??'),
#            'hhsv':                   ('HHSV', '??'),
#            'llsv':                   ('LLSV', '??'),
#            'hsv':                    ('HSV', '??'),
#            'lsv':                    ('LSV', '??'),
#            'hyst':                   ('HYST', '??'),
            },
        'init':  ['NAME', 'DESC', 'VAL', 'RVAL', 'EGU', 'PREC', 'RTYP', 'DTYP'],
        'config': ['DESC', 'EGU', 'PREC', 'DTYP']
        },
     'sel': {
        'description': 'Used for Vacuum devices',
        'fields': {
            'value':                  ('VAL', 'value'),
            'units':                  ('EGU',  'Engineering Units '),
            'high_opr':               ('HOPR', 'high opr'),
            'low_opr':                ('LOPR', 'low opr'), 
            'precision':              ('PREC', 'Display Precision '),
            'name':                   ('NAME', 'PV Name'),
            'description':            ('DESC', 'Description'),
            'device_type':            ('DTYP', 'Device type'),
            'record_type':            ('RTYP', 'Record Type'),
            },
        'init':  ['NAME', 'DESC', 'VAL', 'EGU', 'PREC', 'RTYP', 'DTYP'],
        'config': ['DESC', 'EGU', 'PREC', 'DTYP']
        },
     'longin': {
        'fields': {
            'value':                  ('VAL', 'value'),
            'units':                  ('EGU',  'Engineering Units '),
            'name':                   ('NAME', 'PV Name'),
            'description':            ('DESC', 'Description'),
            'device_type':            ('DTYP', 'Device type'),
            'record_type':            ('RTYP', 'Record Type'),
            },
        'init':  ['NAME', 'DESC', 'VAL', 'EGU', 'RTYP', 'DTYP'],
        'config': ['DESC', 'EGU', 'DTYP']
        },
     'longout': {
        'fields': {
            'value':                  ('VAL', 'value'),
            'units':                  ('EGU',  'Engineering Units '),
            'name':                   ('NAME', 'PV Name'),
            'description':            ('DESC', 'Description'),
            'device_type':            ('DTYP', 'Device type'),
            'record_type':            ('RTYP', 'Record Type'),
            },
        'init':  ['NAME', 'DESC', 'VAL', 'EGU', 'RTYP', 'DTYP'],
        'config': ['DESC', 'EGU', 'DTYP']
        },
     'sub': {
        'fields': {
            'value':                  ('VAL', 'value'),
            'units':                  ('EGU',  'Engineering Units '),
            'name':                   ('NAME', 'PV Name'),
            'description':            ('DESC', 'Description'),
            'device_type':            ('DTYP', 'Device type'),
            'record_type':            ('RTYP', 'Record Type'),
            },
        'init':  ['NAME', 'DESC', 'VAL', 'EGU', 'RTYP', 'DTYP'],
        'config': ['DESC', 'EGU', 'DTYP']
        },
     'longSub': {
        'fields': {
            'value':                  ('VAL', 'value'),
            'units':                  ('EGU',  'Engineering Units '),
            'name':                   ('NAME', 'PV Name'),
            'description':            ('DESC', 'Description'),
            'device_type':            ('DTYP', 'Device type'),
            'record_type':            ('RTYP', 'Record Type'),
            },
        'init':  ['NAME', 'DESC', 'VAL', 'EGU', 'RTYP', 'DTYP'],
        'config': ['DESC', 'EGU', 'DTYP']
        }
}

class EpicsRecordException(Exception):
    """ raised to indicate a problem with a motor"""
    def __init__(self, msg, *args):
        Exception.__init__(self, *args)
        self.msg = msg
    def __str__(self):
        return str(self.msg)


class lcls_record(device.Device):
    "General epics device for non-motor lcls records."

    _log_attrs = []
    _mutable = False

    _nonpvs = ('_prefix', '_pvs', '_delim', '_init', 
               '_alias', '_fields', '_records', '_info_attrs', '_myinfo')

    def __init__(self, name=None,
                 myinfo=None, fields=None, records=None, init_list=None, 
                 record_dict=record_dict,
                 mutable=False, timeout=1.0):

        if name is None:
            raise NewportException("must supply motor name")

        if name.endswith('.'):
            name = name[:-1]

        self._prefix = name

        try:
            rectype = epics.caget(name+'.RTYP')
        except:
            raise EpicsRecordException('WARNING:  {:} is not a valid epics record.'.format(name))
      
        if not fields:
            if rectype in record_dict and 'fields' in record_dict[rectype]:
                fields = record_dict[rectype]['fields']
            else: 
                fields = {
                    'name':                   ('NAME', 'PV Name'),
                    'description':            ('DESC', 'Description'),
                    'value':                  ('VAL', 'value'),
                    'record_type':            ('RTYP', 'Record Type'),
                    'device_type':            ('DTYP', 'Device type'),
                    'status':                 ('STAT', 'Current Alarm Status'),
                    'severity':               ('SEVR', 'Current Alarm Severity')
                }

        if not records:
            if rectype in record_dict and 'records' in record_dict[rectype]:
                records = record_dict[rectype]['records']
            else: 
                records = {}        
                
        if not init_list:
            if rectype in record_dict and 'init' in record_dict[rectype]:
                init_list =  record_dict[rectype]['init']
            else: 
                init_list =  ('NAME', 'DESC', 'VAL', 'RTYP', 'DTYP')

        self._attr_tuple = dict(records.items() + fields.items())
        self._alias = {item[0]: item[1][0] for item in records.items() + fields.items()}

        self._fields = [item[1][0] for item in fields.items()]
        self._records = [item[1][0] for item in records.items()]
        self._info_attrs = [item for item in init_list if item in self._fields]

        # Make sure _init_list is in the defined fields
#        set(_init_list).intersection([item[0] for attr, item in _fields.items()])

        device.Device.__init__(self, name, delim='.',
                                     attrs=init_list,
                                     mutable=False,
                                     timeout=timeout)

        # self.put('disabled', 0)
        self._callbacks = {}

        self._all_attrs = [attr for attr in self._alias.values()
                           if attr not in self._log_attrs]

    def _ai_repr(self):
        value = self.value
        if 'EGU' in self._fields:
            units = self.EGU
        else:
            units = ''
        if 'DESC' in self._fields:
            desc = self.DESC
        else:
            desc = ''
        return '<ai epics record: {:s} = {:.2f} {:s} : {:s}>'.format(
                self._prefix.rstrip('.'), value, units, desc)

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
        if attr in ('name', '_prefix', '_pvs', '_delim', '_init',
                    '_alias', '_fields', '_records', '_attr_tuple',
                    '_info_attrs', '_mutable',
                    '_nonpvs', '_callbacks', '_all_attrs'):
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



