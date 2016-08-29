import epics
from lcls_devices import Device

#PvConfigV2 = {
#    'ims':     ['DESC', 'EGU', 'PREC', 'VERS', 'TYPE', 'PN', 'SN'],
#    'xps8p':   ['DESC', 'EGU', 'PREC', 'VERS', 'TYPE'],
#    'motor':   ['DESC', 'EGU', 'PREC', 'VERS'],
#    'pmc100':  ['DESC', 'EGU', 'PREC', 'VERS'],
#    'calc':    ['DESC', 'EGU', 'PREC'],
#    'sel':     ['DESC', 'EGU', 'PREC'],
#    'ai':      ['DESC', 'EGU', 'PREC'],
#    'ao':      ['DESC', 'EGU', 'PREC'],
#    'longSub': ['DESC', 'EGU'],
#    'longout': ['DESC', 'EGU'],
#    'longin':  ['DESC', 'EGU'],
#    'sub':     ['DESC', 'EGU'],
#    'bi':      ['DESC'],
#    'bo':      ['DESC'],
#}

#ipmiSrv record example
# ioc-ipmiSrv-cxi> dbpr IOC:CXI:CAM1 10
# ACKS: INVALID       ACKT: YES           ASG:                ASP: (nil)          
# BKPT: 00            CFLL: 5             CFLO: 50            CFLS: MAJOR         
# CFOS: MINOR         CMAP: 0             CPUF: no info       CPUT: no info       
# CTHH: 70            CTHI: 50            CTHS: MAJOR         CTIS: MINOR         
# DESC:               DISA: 0             DISP: 0             DISS: NO_ALARM      
# DISV: 1             DPVT: 0x9f682a8     DSET: (nil)         DTYP: <nil>         
# EVNT: 0             FLNK:DB_LINK IOC:CXI:CAM1:TS            HOST: ioc-cxi-misc1 
# IOCN: IOC:IPMISRV:CXI                   LCNT: 0             LSET: 0x9f6c890     
# MLIS: 20 a4 fc 09 38 79 fe 09 19 00 00 00                   MLOK: 90 82 f6 09   
# NAME: IOC:CXI:CAM1  NSEV: NO_ALARM      NSTA: NO_ALARM      PACT: 0             
# PHAS: 0             PINI: NO            PPN: (nil)          PPNR: (nil)         
# PRIO: LOW           PROC: 0             PUTF: 0             RDES: 0x9f35310     
# RPRO: 0             RSET: 0x819cc40     SCAN: Passive       SDIS:CONSTANT       
# SEVR: MAJOR         SFLL: 5             SFLO: 50            SFLS: MAJOR         
# SFOS: MINOR         SPVT: (nil)         SRVN: ioc-cxi-cam1  STAT: STATE         
# STHH: 70            STHI: 50            STHS: MAJOR         STIS: MINOR         
# STUP: 0             SYSF: no info       SYST: 26 degrees C                      
# TIME: 2015-09-30 13:21:29.094732000     TPRO: 0             TSE: 0              
# TSEL:CONSTANT       UDF: 1              UINT: 300           VAL: 0              

# transform record
#ioc-cxi-dg1-ims> dbpr CXI:DG1:MMS:08:ILK:SignalFault 10
#A: 2                ACKS: NO_ALARM      ACKT: YES           ASG:                
#ASP: (nil)          B: 0                BKPT: 00            C: 2                
#CAV: 0              CBV: 0              CCV: 0              CDV: 0              
#CEV: 0              CFV: 0              CGV: 0              CHV: 0              
#CIV: 0              CJV: 0              CKV: 0              CLCA: b?0:2         
#CLCB:               CLCC: b?0:2         CLCD:               CLCE:               
#CLCF:               CLCG:               CLCH:               CLCI:               
#CLCJ:               CLCK:               CLCL:               CLCM:               
#CLCN:               CLCO:               CLCP:               CLV: 0              
#CMTA:               CMTB:               CMTC:               CMTD:               
#CMTE:               CMTF:               CMTG:               CMTH:               
#CMTI:               CMTJ:               CMTK:               CMTL:               
#CMTM:               CMTN:               CMTO:               CMTP:               
#CMV: 0              CNV: 0              COPT: Conditional   COV: 0              
#CPV: 0              D: 0                DESC: Interlock Fanout                  
#DISA: 0             DISP: 0             DISS: NO_ALARM      DISV: 1             
#DPVT: (nil)         DSET: (nil)         DTYP: <nil>         E: 0                
#EGU:                EVNT: 0             F: 0                FLNK:CONSTANT 0     
#G: 0                H: 0                I: 0                IAV: Constant       
#IBV: Constant       ICV: Constant       IDV: Constant       IEV: Constant       
#IFV: Constant       IGV: Constant       IHV: Constant       IIV: Constant       
#IJV: Constant       IKV: Constant       ILV: Constant       IMV: Constant       
#INPA:CONSTANT       INPB:CONSTANT       INPC:CONSTANT       INPD:CONSTANT       
#INPE:CONSTANT       INPF:CONSTANT       INPG:CONSTANT       INPH:CONSTANT       
#INPI:CONSTANT       INPJ:CONSTANT       INPK:CONSTANT       INPL:CONSTANT       
#INPM:CONSTANT       INPN:CONSTANT       INPO:CONSTANT       INPP:CONSTANT       
#INV: Constant       IOV: Constant       IPV: Constant       IVLA: Ignore error  
#J: 0                K: 0                L: 0                LA: 2               
#LB: 0               LC: 2               LCNT: 0             LD: 0               
#LE: 0               LF: 0               LG: 0               LH: 0               
#LI: 0               LJ: 0               LK: 0               LL: 0               
#LM: 0               LN: 0               LO: 0               LP: 0               
#LSET: 0x9242758     M: 0                MAP: 0              
#MLIS: c8 d8 3c 09 b0 52 3e 09 06 00 00 00                   MLOK: b0 a1 22 09   
#N: 0                NAME: CXI:DG1:MMS:08:ILK:SignalFault    NSEV: NO_ALARM      
#NSTA: NO_ALARM      O: 0                OAV: Local PV       OBV: Local PV       
#OCV: Local PV       ODV: Constant       OEV: Constant       OFV: Constant       
#OGV: Constant       OHV: Constant       OIV: Constant       OJV: Constant       
#OKV: Constant       OLV: Constant       OMV: Constant       ONV: Constant       
#OOV: Constant       OPV: Constant       OUTA:DB_LINK CXI:DG1:MMS:08.SPG NPP NMS 
#OUTB:DB_LINK CXI:DG1:MMS:08.DISP NPP NMS                    
#OUTC:DB_LINK CXI:DG1:MMS:08.SPG NPP NMS OUTD:CONSTANT       OUTE:CONSTANT       
#OUTF:CONSTANT       OUTG:CONSTANT       OUTH:CONSTANT       OUTI:CONSTANT       
#OUTJ:CONSTANT       OUTK:CONSTANT       OUTL:CONSTANT       OUTM:CONSTANT       
#OUTN:CONSTANT       OUTO:CONSTANT       OUTP:CONSTANT       P: 0                
#PACT: 0             PHAS: 0             PINI: NO            PPN: (nil)          
#PPNR: (nil)         PREC: 0             PRIO: LOW           PROC: 0             
#PUTF: 0             RDES: 0x9187858     
#RPCA: 7d 5b 38 09 00 00 00 00 00 00 00 00 18 09 00 00 00 00 00 00               
#RPCB: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00               
#RPCC: 7d 5b 38 09 00 00 00 00 00 00 00 00 18 09 00 00 00 00 00 00               
#RPCD: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00               
#RPCE: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00               
#RPCF: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00               
#RPCG: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00               
#RPCH: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00               
#RPCI: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00               
#RPCJ: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00               
#RPCK: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00               
#RPCL: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00               
#RPCM: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00               
#RPCN: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00               
#RPCO: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00               
#RPCP: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00               
#RPRO: 0             RPVT: 0x922a1c8     RSET: 0x81fc820     SCAN: Passive       
#SDIS:CONSTANT       SEVR: NO_ALARM      SPVT: (nil)         STAT: NO_ALARM      
#TIME: 2015-09-22 09:37:45.802540000     TPRO: 0             TSE: 0              
#TSEL:CONSTANT       UDF: 0              VAL: 0              VERS: 5.8           


# mbbiDirect https://wiki-ext.aps.anl.gov/epics/index.php/RRM_3-14_Multi-Bit_Binary_Input_Direct
# seq https://wiki-ext.aps.anl.gov/epics/index.php/RRM_3-14_Sequence

record_dict = {
    'asyn': {
        'desc': 'asyn Record',
        'reference': 'http://aps.anl.gov/epics/modules/soft/asyn/R3-1/asynRecord.html',
        'usage':  'See referrence.', 
        'fields': {
            'value':                  ('VAL', 'value'),
            'name':                   ('NAME', 'PV Name'),
            'description':            ('DESC', 'Description'),
            'device_type':            ('DTYP', 'Device type'),
            'record_type':            ('RTYP', 'Record Type'),
            'port':                   ('PORT', 'asyn port'),
            'address':                ('ADDR', 'asyn address'),
            'socket':                 ('SOCK', 'asyn socket address'),
            'trans_mode':             ('TMOD', 'Transaction Mode'),
            'timeout':                ('TMOT', 'Timeout (sec)'),
            'output_string':          ('AOUT', 'Output String'),
            'output_byte':            ('BOUT', 'Output Byte Data'),
            'output_terminator':      ('OEOS', 'Output Terminator'),
            'bytes_to_write':         ('NOWT', 'Number of bytes to write'),
            'bytes_written':          ('NAWT', 'Number of bytes written'),
            'output_format':          ('OFMT', 'Output format'),
            'input_string':           ('AINP', 'Input string'),
            'input_byte':             ('BINP', 'Input byte data'),
            'input_terminator':       ('IEOS', 'Input terminator'),
            'input_max_size':         ('IMAX', 'Input array max size'),
            'bytes_to_read':          ('NRRD', 'Number of bytes to read'),
            'bytes_read':             ('NORD', 'Number of bytes read'),
            'input_format':           ('IFMT', 'Input format'),
            'translated_input':       ('TINP', 'Translated input'),
            'baud_rate':              ('BAUD', 'Serial port Baud rate'),
            'parity':                 ('PRTY', 'S3rial port Parity'),
            'data_bits':              ('DBIT', 'Serial port Data bits'),
            'stop_bits':              ('SBIT', 'Serial port Stop bits'),
            'flow_control':           ('FCTL', 'Serial port Flow control'),
            'serial_poll_resp':       ('SPR',  'Serial Poll Response for GPIB'),
            'universal_cmd':          ('UCMD', 'Universal command for GPIB'),
            'address_cmd':            ('ACMD', 'Address command for GPIB'),
            'autoconnect':            ('AUCT', 'Set Autoconnect Option'),
            'enable':                 ('ENBL', 'Enable or disable port'),
            'connect':                ('CNCT', 'Connect or disconnect the device'),
            'error_status':           ('ERRS', 'Error status string'),
            },
        'init':  ['NAME', 'DESC', 'VAL', 'RTYP', 'DTYP'],
        'config': ['DESC', 'DTYP']
        },
    'fanout': {
        'desc': 'fanout Record',
        'reference': 'https://wiki-ext.aps.anl.gov/epics/index.php/RRM_3-14_Fanout',
        'usage':  'See referrence.', 
        'fields': {
            'value':                  ('VAL', 'value'),
            'name':                   ('NAME', 'PV Name'),
            'description':            ('DESC', 'Description'),
            'device_type':            ('DTYP', 'Device type'),
            'record_type':            ('RTYP', 'Record Type'),
            'high_opr':               ('HOPR', 'high opr'),
            'low_opr':                ('LOPR', 'low opr'), 
            'select_mechanism':       ('SELM', 'Select mechanism'),
            'select_algorithm':       ('SELN', 'Link selection algorithm'),
            },
        'init':  ['NAME', 'DESC', 'VAL', 'RTYP', 'DTYP'],
        'config': ['DESC', 'DTYP']
        },
    'dfanout': {
        'desc': 'dfanout Record',
        'reference': 'https://wiki-ext.aps.anl.gov/epics/index.php/RRM_3-14_Fanout',
        'usage':  'See referrence.', 
        'fields': {
            'value':                  ('VAL', 'value'),
            'name':                   ('NAME', 'PV Name'),
            'description':            ('DESC', 'Description'),
            'device_type':            ('DTYP', 'Device type'),
            'record_type':            ('RTYP', 'Record Type'),
            'high_opr':               ('HOPR', 'high opr'),
            'low_opr':                ('LOPR', 'low opr'), 
#            'LNK1':                   ('LNK1', 'Forward Link 1'),
#            'LNK2':                   ('LNK2', 'Forward Link 2'),
#            'LNK3':                   ('LNK3', 'Forward Link 3'),
#            'LNK4':                   ('LNK4', 'Forward Link 4'),
#            'LNK5':                   ('LNK5', 'Forward Link 5'),
#            'LNK6':                   ('LNK6', 'Forward Link 6'),
            'select_mechanism':       ('SELM', 'Select mechanism'),
            'select_algorithm':       ('SELN', 'Link selection algorithm'),
#            'select_location':        ('SELLdd', 'Link selection algorithm'),
            },
        'init':  ['NAME', 'DESC', 'VAL', 'RTYP', 'DTYP'],
        'config': ['DESC', 'DTYP']
        },
    'lkup': {
        'desc': 'Lookup Record',
        'reference': '',
        'usage':  'None', 
        'fields': {
            'value':                  ('VAL', 'value'),
            'name':                   ('NAME', 'PV Name'),
            'description':            ('DESC', 'Description'),
            'device_type':            ('DTYP', 'Device type'),
            'record_type':            ('RTYP', 'Record Type'),
            'output':                 ('OUT',  'Output Link'),
            'input':                  ('INP',  'Input Link'),
            'scan':                   ('SCAN', 'Scan mode'),
            },
        'init':  ['NAME', 'DESC', 'VAL', 'RTYP', 'DTYP'],
        'config': ['DESC', 'DTYP']
        },
    'waveform': {
        'desc': 'waveform Record',
        'reference': 'https://wiki-ext.aps.anl.gov/epics/index.php/RRM_3-14_Waveform',
        'usage':  'These fields are configurable by the user to specify how and from \
                   where the record reads its data', 
        'fields': {
            'value':                  ('VAL', 'value'),
            'name':                   ('NAME', 'PV Name'),
            'units':                  ('EGU',  'Engineering Units '),
            'precision':              ('PREC', 'Display Precision '),
            'description':            ('DESC', 'Description'),
            'device_type':            ('DTYP', 'Device type'),
            'record_type':            ('RTYP', 'Record Type'),
            'high_opr':               ('HOPR', 'high opr'),
            'low_opr':                ('LOPR', 'low opr'), 
            'nelements':              ('NELM', 'Number of elements'),
            'field_type':             ('FTVL', 'Field type of value'),
            'rearm':                  ('RARM', 'Rearm'),
            },
        'init':  ['NAME', 'DESC', 'VAL', 'EGU', 'PREC', 'RTYP', 'DTYP'],
        'config': ['DESC', 'DTYP', 'EGU']
        },
 
    'calc': {
        'desc': 'Calculation',
        'reference': 'http://www.aps.anl.gov/epics/EpicsDocumentation/AppDevManuals/RecordRef/Recordref-13.html',
        'usage':  'The calculation or Calc record is used to perform algebraic,  \
                   relational, and logical operations on values retrieved from other records. \
                   The result of its operations can then be accessed by another record  \
                   so that it can be used.', 
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
            'calc':                   ('CALC', 'Calculation'),
            'input_a':                ('INPA', 'Input A'),
            'input_b':                ('INPB', 'Input B'),
            'input_c':                ('INPC', 'Input C'),
            'input_d':                ('INPD', 'Input D'),
            'input_e':                ('INPE', 'Input E'),
            'input_f':                ('INPF', 'Input F'),
            'input_g':                ('INPG', 'Input G'),
            'input_h':                ('INPH', 'Input H'),
            'input_i':                ('INPI', 'Input I'),
            'input_j':                ('INPJ', 'Input J'),
            'input_k':                ('INPK', 'Input K'),
            'input_l':                ('INPL', 'Input L'),
            'Avalue':                 ('A',    'Value A'),
            'Bvalue':                 ('B',    'Value B'),
            'Cvalue':                 ('C',    'Value C'),
            'Dvalue':                 ('D',    'Value D'),
            'Evalue':                 ('E',    'Value E'),
            'Fvalue':                 ('F',    'Value F'),
            'Gvalue':                 ('G',    'Value G'),
            'Hvalue':                 ('H',    'Value H'),
            'Ivalue':                 ('I',    'Value I'),
            'Jvalue':                 ('J',    'Value J'),
            'Kvalue':                 ('K',    'Value K'),
            'Lvalue':                 ('L',    'Value L'),
            },
        'init':  ['NAME', 'DESC', 'VAL', 'EGU', 'PREC', 'RTYP', 'DTYP'],
        'config': ['DESC', 'EGU', 'PREC', 'DTYP']
        },
    'calcout': {
        'desc': 'Calculation Output',
        'reference': 'http://www.aps.anl.gov/epics/EpicsDocumentation/AppDevManuals/RecordRef/Recordref-14.html#HEADING14-0',
        'usage':  'The Calculation Output or "Calcout" record is similar to the Calc record \
                   with the added feature of having outputs (an "output link" and an "output event") \
                   which are conditionally executed based on the result of the calculation. \
                   This feature allows conditional branching to be implemented within an \
                   EPICS database (e.g., process Record_A only if Record_B has a value of 0). \
                   The Calcout record is also similar to the Wait record (with additional features) \
                   but uses EPICS standard INLINK and OUTLINK fields rather than the DBF_STRING fields \
                   used in the Wait record. For new databases, it is recommended that the Calcout \
                   record be used instead of the Wait record.',
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
            'calc':                   ('CALC', 'Calculation'),
            'output':                 ('OUT',  'Output Specification'),
            'out_exec_opt':           ('OOPT', 'Output Execute Option'),
            'out_data_opt':           ('DOPT', 'Output Data Option'),
            'out_calc':               ('OCAL', 'Output Calculation'),
            'out_value':              ('OVAL', 'Output Value'),
            'input_a':                ('INPA', 'Input A'),
            'input_b':                ('INPB', 'Input B'),
            'input_c':                ('INPC', 'Input C'),
            'input_d':                ('INPD', 'Input D'),
            'input_e':                ('INPE', 'Input E'),
            'input_f':                ('INPF', 'Input F'),
            'input_g':                ('INPG', 'Input G'),
            'input_h':                ('INPH', 'Input H'),
            'input_i':                ('INPI', 'Input I'),
            'input_j':                ('INPJ', 'Input J'),
            'input_k':                ('INPK', 'Input K'),
            'input_l':                ('INPL', 'Input L'),
            'Avalue':                 ('A',    'Value A'),
            'Bvalue':                 ('B',    'Value B'),
            'Cvalue':                 ('C',    'Value C'),
            'Dvalue':                 ('D',    'Value D'),
            'Evalue':                 ('E',    'Value E'),
            'Fvalue':                 ('F',    'Value F'),
            'Gvalue':                 ('G',    'Value G'),
            'Hvalue':                 ('H',    'Value H'),
            'Ivalue':                 ('I',    'Value I'),
            'Jvalue':                 ('J',    'Value J'),
            'Kvalue':                 ('K',    'Value K'),
            'Lvalue':                 ('L',    'Value L'),
            'out_pv_status':          ('OUTV', 'Out PV Status'),
            'calc_valid':             ('CLCV', 'Calc Valid'),
            'ocal_valid':             ('OCLV', 'Ocal Valid'),
            },
        'init':  ['NAME', 'DESC', 'VAL', 'EGU', 'PREC', 'RTYP', 'DTYP'],
        'config': ['DESC', 'EGU', 'PREC', 'DTYP']
        },

    'scalcout': {
        'desc': 'String Calculation Output',
        'reference': 'https://wiki-ext.aps.anl.gov/epics/index.php/RRM_3-13_String_Calcout',
        'usage':  'Similar to calcout record.',
        'fields': {
            'value':                  ('VAL', 'value'),
            'high_opr':               ('HOPR', 'high opr'),
            'low_opr':                ('LOPR', 'low opr'), 
            'name':                   ('NAME', 'PV Name'),
            'description':            ('DESC', 'Description'),
            'device_type':            ('DTYP', 'Device type'),
            'record_type':            ('RTYP', 'Record Type'),
            'calc':                   ('CALC', 'Calculation'),
            'output':                 ('OUT',  'Output Specification'),
            'out_exec_opt':           ('OOPT', 'Output Execute Option'),
            'out_data_opt':           ('DOPT', 'Output Data Option'),
            'out_calc':               ('OCAL', 'Output Calculation'),
            'out_value':              ('OVAL', 'Output Value'),
            'input_a':                ('INPA', 'Input A'),
            'input_b':                ('INPB', 'Input B'),
            'input_c':                ('INPC', 'Input C'),
            'input_d':                ('INPD', 'Input D'),
            'input_e':                ('INPE', 'Input E'),
            'input_f':                ('INPF', 'Input F'),
            'input_g':                ('INPG', 'Input G'),
            'input_h':                ('INPH', 'Input H'),
            'input_i':                ('INPI', 'Input I'),
            'input_j':                ('INPJ', 'Input J'),
            'input_k':                ('INPK', 'Input K'),
            'input_l':                ('INPL', 'Input L'),
            'Avalue':                 ('A',    'Value A'),
            'Bvalue':                 ('B',    'Value B'),
            'Cvalue':                 ('C',    'Value C'),
            'Dvalue':                 ('D',    'Value D'),
            'Evalue':                 ('E',    'Value E'),
            'Fvalue':                 ('F',    'Value F'),
            'Gvalue':                 ('G',    'Value G'),
            'Hvalue':                 ('H',    'Value H'),
            'Ivalue':                 ('I',    'Value I'),
            'Jvalue':                 ('J',    'Value J'),
            'Kvalue':                 ('K',    'Value K'),
            'Lvalue':                 ('L',    'Value L'),
            'out_pv_status':          ('OUTV', 'Out PV Status'),
            'calc_valid':             ('CLCV', 'Calc Valid'),
            'ocal_valid':             ('OCLV', 'Ocal Valid'),
            },
        'init':  ['NAME', 'DESC', 'VAL', 'EGU', 'PREC', 'RTYP', 'DTYP'],
        'config': ['DESC', 'EGU', 'PREC', 'DTYP']
        },
    'bo': {
        'desc': 'Binary Output',
        'reference': 'http://www.aps.anl.gov/epics/EpicsDocumentation/AppDevManuals/RecordRef/Recordref-12.html',
        'usage': 'The normal use for this record type is to store a simple bit (0 or 1) \
                  value to be sent to a Digital Output module. It can also be used to write \
                  binary values into other records via database or channel access links. \
                  This record can implement both latched and momentary binary outputs \
                  depending on how the HIGH field is configured.',
        'fields': {
            'value':                  ('VAL', 'value'),
#            'high_opr':               ('HOPR', 'high opr'),
#            'low_opr':                ('LOPR', 'low opr'), 
            'name':                   ('NAME', 'PV Name'),
            'description':            ('DESC', 'Description'),
            'device_type':            ('DTYP', 'Device type'),
            'record_type':            ('RTYP', 'Record Type'),
            'raw_value':              ('RVAL', 'Raw Value'),
            'zero_name':              ('ZNAM', 'Zero Name'),
            'one_name':               ('ONAM', 'One Name'),
            },
        'init':  ['NAME', 'DESC', 'VAL', 'RVAL', 'PREC', 'RTYP', 'DTYP'],
        'config': ['DESC', 'DTYP']
        },
    'mbbo': {
        'desc': 'Multi Binary Output',
        'reference': 'http://www.aps.anl.gov/epics/EpicsDocumentation/AppDevManuals/RecordRef/Recordref-25.html',
        'usage': 'The normal use for the mbbo record type is to send a binary value \
                  (representing one of up to 16 states) to a Digital Output module. \
                  It is used for any device that uses more than one bit to control it. \
                  The mbbo record can also be used to write discrete values to other \
                  records via database or channel access links.',
        'fields': {
            'value':                  ('VAL', 'value'),
            'name':                   ('NAME', 'PV Name'),
            'description':            ('DESC', 'Description'),
            'device_type':            ('DTYP', 'Device type'),
            'record_type':            ('RTYP', 'Record Type'),
            'raw_value':              ('RVAL', 'Raw Value  '),
            'output_link':            ('OUT',  'Output Link'),
            'shift':                  ('SHFT', 'Shift'),
            'states_defined':         ('SDEF', 'States Defined'),
            'zero_value':             ('ZRVL', 'Zero Value'),
            'one_value':              ('ONVL', 'One Value'),
            'two_value':              ('TWVL', 'Two Value'),
            'three_value':            ('THVL', 'Three Value'),
            'four_value':             ('FRVL', 'Four Value'),
            'five_value':             ('FVVL', 'Five Value'),
            'six_value':              ('SXVL', 'Six Value'),
            'seven_value':            ('SVVL', 'Seven Value'),
            'eight_value':            ('EIVL', 'Eight Value'),
            'nine_value':             ('NIVL', 'Nine Value'),
            'ten_value':              ('TEVL', 'Ten Value'),
            'eleven_value':           ('ELVL', 'Eleven Value'),
            'twelve_value':           ('TVVL', 'Twelve Value'),
            'thirteen_value':         ('TTVL', 'Thirteen Value'),
            'fourteen_value':         ('FTVL', 'Fourteen Value'),
            'fifteen_value':          ('FFVL', 'Fifteen Value'),
            'zero_string':            ('ZRST', 'Zero String'),
            'one_string':             ('ONST', 'One String'),
            'two_string':             ('TWST', 'Two String'),
            'three_string':           ('THST', 'Three String'),
            'four_string':            ('FRST', 'Four String'),
            'five_string':            ('FVST', 'Five String'),
            'six_string':             ('SXST', 'Six String'),
            'seven_string':           ('SVST', 'Seven String'),
            'eight_string':           ('EIST', 'Eight String'),
            'nine_string':            ('NIST', 'Nine String'),
            'ten_string':             ('TEST', 'Ten String'),
            'eleven_string':          ('ELST', 'Eleven String'),
            'twelve_string':          ('TVST', 'Twelve String'),
            'thirteen_string':        ('TTST', 'Thirteen String'),
            'fourteen_string':        ('FTST', 'Fourteen String'),
            'fifteen_string':         ('FFST', 'Fifteen String'),
            },
        'init':  ['NAME', 'DESC', 'VAL', 'RVAL', 'PREC', 'RTYP', 'DTYP'],
        'config': ['DESC', 'DTYP']
        },
    'mbbi': {
        'desc': 'Multi Binary Input',
        'reference': 'http://www.aps.anl.gov/epics/EpicsDocumentation/AppDevManuals/RecordRef/Recordref-23.html',
        'fields': {
            'value':                  ('VAL', 'value'),
            'name':                   ('NAME', 'PV Name'),
            'description':            ('DESC', 'Description'),
            'device_type':            ('DTYP', 'Device type'),
            'record_type':            ('RTYP', 'Record Type'),
            'raw_value':              ('RVAL', 'Raw Value  '),
            'input_link':             ('INP',  'Input Link'),
            'shift':                  ('SHFT', 'Shift'),
            'states_defined':         ('SDEF', 'States Defined'),
            'zero_value':             ('ZRVL', 'Zero Value'),
            'one_value':              ('ONVL', 'One Value'),
            'two_value':              ('TWVL', 'Two Value'),
            'three_value':            ('THVL', 'Three Value'),
            'four_value':             ('FRVL', 'Four Value'),
            'five_value':             ('FVVL', 'Five Value'),
            'six_value':              ('SXVL', 'Six Value'),
            'seven_value':            ('SVVL', 'Seven Value'),
            'eight_value':            ('EIVL', 'Eight Value'),
            'nine_value':             ('NIVL', 'Nine Value'),
            'ten_value':              ('TEVL', 'Ten Value'),
            'eleven_value':           ('ELVL', 'Eleven Value'),
            'twelve_value':           ('TVVL', 'Twelve Value'),
            'thirteen_value':         ('TTVL', 'Thirteen Value'),
            'fourteen_value':         ('FTVL', 'Fourteen Value'),
            'fifteen_value':          ('FFVL', 'Fifteen Value'),
            'zero_string':            ('ZRST', 'Zero String'),
            'one_string':             ('ONST', 'One String'),
            'two_string':             ('TWST', 'Two String'),
            'three_string':           ('THST', 'Three String'),
            'four_string':            ('FRST', 'Four String'),
            'five_string':            ('FVST', 'Five String'),
            'six_string':             ('SXST', 'Six String'),
            'seven_string':           ('SVST', 'Seven String'),
            'eight_string':           ('EIST', 'Eight String'),
            'nine_string':            ('NIST', 'Nine String'),
            'ten_string':             ('TEST', 'Ten String'),
            'eleven_string':          ('ELST', 'Eleven String'),
            'twelve_string':          ('TVST', 'Twelve String'),
            'thirteen_string':        ('TTST', 'Thirteen String'),
            'fourteen_string':        ('FTST', 'Fourteen String'),
            'fifteen_string':         ('FFST', 'Fifteen String'),
            },
        'init':  ['NAME', 'DESC', 'VAL', 'RVAL', 'PREC', 'RTYP', 'DTYP'],
        'config': ['DESC', 'DTYP']
        },
    'bi': {
        'desc':  'Binary Input',
        'usage': 'The normal use for this record type is to obtain a binary value of 0 or 1. \
                  Most device support modules obtain values from hardware and place the value in RVAL. \
                  For these devices record processing sets VAL = (0,1) if RVAL is (0, not 0). \
                  Devices support modules may optionally read a value directly into VAL.',
        'fields': {
            'value':                  ('VAL', 'value'),
#            'high_opr':               ('HOPR', 'high opr'),
#            'low_opr':                ('LOPR', 'low opr'), 
            'name':                   ('NAME', 'PV Name'),
            'description':            ('DESC', 'Description'),
            'device_type':            ('DTYP', 'Device type'),
            'record_type':            ('RTYP', 'Record Type'),
            'raw_value':              ('RVAL', 'Raw Value  '),
            'zero_name':              ('ZNAM', 'Zero Name'),
            'one_name':               ('ONAM', 'One Name'),
            },
        'init':  ['NAME', 'DESC', 'VAL', 'RVAL', 'PREC', 'RTYP', 'DTYP'],
        'config': ['DESC', 'DTYP']
        },
    'ao': {
        'desc':  'Analog Output',
        'usage': 'The normal use for this record type is to output values to digital-analog \
                  converters. It is used for all analog outputs to hardware. It can also be \
                  used to write floating point values to other records via database or channel \
                  access links. How the user configures the output link determines if the \
                  record sends its value to a hardware device, a channel access link, or a \
                  database link. The desired output can be controlled by either an operator \
                  or a state program, or it can be fetched from another record. ',
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
        'desc':  'Analog Input',
        'usage': 'The normal use for this record type is to obtain an analog value from \
                  hardware and then convert it to engineering units. Most device support \
                  modules obtain values from hardware. The record supports alarm limits, \
                  conversion to engineering units, smoothing, and graphics and control limits.',
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
        'desc': 'Selection',
        'usage': 'Selection Record -- Used at LCLS for Vacuum devices',
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
            'select_mechanism':       ('SELM', 'Select Mechanism'),
            'select_number':          ('SELN', 'Select Number'),
            'inputA':                 ('INPA', 'Input A'),
            'inputB':                 ('INPB', 'Input B'),
            'inputC':                 ('INPC', 'Input C'),
            'inputD':                 ('INPD', 'Input D'),
            'inputE':                 ('INPE', 'Input E'),
            'inputF':                 ('INPF', 'Input F'),
            'inputG':                 ('INPG', 'Input G'),
            'inputH':                 ('INPH', 'Input H'),
            'inputI':                 ('INPI', 'Input I'),
            'inputJ':                 ('INPJ', 'Input J'),
            'inputK':                 ('INPK', 'Input K'),
            'inputL':                 ('INPL', 'Input L'),
            'avalue':                 ('a',    'value a'),
            'bvalue':                 ('b',    'value b'),
            'cvalue':                 ('c',    'value c'),
            'dvalue':                 ('d',    'value d'),
            'evalue':                 ('e',    'value e'),
            'fvalue':                 ('f',    'value f'),
            'gvalue':                 ('g',    'value g'),
            'hvalue':                 ('h',    'value h'),
            'ivalue':                 ('i',    'value i'),
            'jvalue':                 ('j',    'value j'),
            'kvalue':                 ('k',    'value k'),
            'lvalue':                 ('l',    'value l'),
            },
        'init':  ['NAME', 'DESC', 'VAL', 'EGU', 'PREC', 'RTYP', 'DTYP'],
        'config': ['DESC', 'EGU', 'PREC', 'DTYP']
        },
    'longin': {
        'desc': 'Long Input',
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
        'desc': 'Long Output',
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
        'desc': 'Subroutine',
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
            'initialization_name':    ('INAM', 'Initialization Name'),
            'subroutine_name':        ('SNAM', 'Subroutine Name'),
            'subroutine_severity':    ('BRSV', 'Severity for a subroutine return value less than 0'),
            'alarm_deadband':         ('HYST', 'Alarm Deadband'),
            'archive_deadband':       ('ADEL', 'Archive Deadband'),
            'monitor_deadband':       ('MDEL', 'Monitor, i.e. value change, Deadband'),
            'inputA':                 ('INPA', 'Input A'),
            'inputB':                 ('INPB', 'Input B'),
            'inputC':                 ('INPC', 'Input C'),
            'inputD':                 ('INPD', 'Input D'),
            'inputE':                 ('INPE', 'Input E'),
            'inputF':                 ('INPF', 'Input F'),
            'inputG':                 ('INPG', 'Input G'),
            'inputH':                 ('INPH', 'Input H'),
            'inputI':                 ('INPI', 'Input I'),
            'inputJ':                 ('INPJ', 'Input J'),
            'inputK':                 ('INPK', 'Input K'),
            'inputL':                 ('INPL', 'Input L'),
            'Avalue':                 ('A',    'Value A'),
            'Bvalue':                 ('B',    'Value B'),
            'Cvalue':                 ('C',    'Value C'),
            'Dvalue':                 ('D',    'Value D'),
            'Evalue':                 ('E',    'Value E'),
            'Fvalue':                 ('F',    'Value F'),
            'Gvalue':                 ('G',    'Value G'),
            'Hvalue':                 ('H',    'Value H'),
            'Ivalue':                 ('I',    'Value I'),
            'Jvalue':                 ('J',    'Value J'),
            'Kvalue':                 ('K',    'Value K'),
            'Lvalue':                 ('L',    'Value L'),
            },
        'init':  ['NAME', 'DESC', 'VAL', 'EGU', 'RTYP', 'DTYP'],
        'config': ['DESC', 'EGU', 'DTYP'],
        'reference': 'https://wiki-ext.aps.anl.gov/epics/index.php/RRM_3-14_Subroutine',
        },
    'longSub': {
        'desc': 'Long Subprocess',
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
    'aSub': {
        'fields': {
            'value':                  ('VAL', 'value'),
            'name':                   ('NAME', 'PV Name'),
            'description':            ('DESC', 'Description'),
            'device_type':            ('DTYP', 'Device type'),
            'record_type':            ('RTYP', 'Record Type'),
            'process':                ('PROC', 'Process'),
            'inputA':                 ('INPA',    'Input A'),
            'inputB':                 ('INPB',    'Input B'),
            'inputC':                 ('INPC',    'Input C'),
            'inputD':                 ('INPD',    'Input D'),
            'inputE':                 ('INPE',    'Input E'),
            'inputF':                 ('INPF',    'Input F'),
            'inputG':                 ('INPG',    'Input G'),
            'inputH':                 ('INPH',    'Input H'),
            'inputI':                 ('INPI',    'Input I'),
            'inputJ':                 ('INPJ',    'Input J'),
            'inputK':                 ('INPK',    'Input K'),
            'inputL':                 ('INPL',    'Input L'),
            'Avalue':                 ('A',    'Value A'),
            'Bvalue':                 ('B',    'Value B'),
            'Cvalue':                 ('C',    'Value C'),
            'Dvalue':                 ('D',    'Value D'),
            'Evalue':                 ('E',    'Value E'),
            'Fvalue':                 ('F',    'Value F'),
            'Gvalue':                 ('G',    'Value G'),
            'Hvalue':                 ('H',    'Value H'),
            'Ivalue':                 ('I',    'Value I'),
            'Jvalue':                 ('J',    'Value J'),
            'Kvalue':                 ('K',    'Value K'),
            'Lvalue':                 ('L',    'Value L'),
            },
        'init':  ['NAME', 'DESC', 'VAL', 'RTYP', 'DTYP', 'A', 'B', 'C', 'D'],
        'config': ['DESC', 'DTYP']
        },
    'hxs': {
        'desc': 'Hard X-ray Spectrometer',
        'fields': {
            'value':                  ('VAL', 'value'),
            'name':                   ('NAME', 'PV Name'),
            'description':            ('DESC', 'Description'),
            'device_type':            ('DTYP', 'Device type'),
            'record_type':            ('RTYP', 'Record Type'),
            'process':                ('PROC', 'Process'),
            'energy':                 ('XENG', 'Energy'),
            'bragg_angle':            ('BANG', 'Bragg Angle'),
            'crystal_name':           ('KRST', 'Crystal Name'),
            's110_in':                ('S110', 'S110 In'),
            's100_in':                ('S100', 'S100 In'),
            'energy_min':             ('EMIN', 'Energy Range Min'),
            'energy_max':             ('EMAX', 'Energy Range Max'),
            'vertical_beam_size':     ('XVUM', 'Vertical Beam Size'),
            'angle_offset1':          ('XTO1', 'Angle Offset 1'),
            'angle_offset2':          ('XTO2', 'Angle Offset 2'),
            'angle_offset3':          ('XTO3', 'Angle Offset 3'),
            'angle_offset4':          ('XTO4', 'Angle Offset 4'),
            'miscut1':                ('XTM1', 'Miscut 1'),
            'miscut2':                ('XTM2', 'Miscut 2'),
            'miscut3':                ('XTM3', 'Miscut 3'),
            'miscut4':                ('XTM4', 'Miscut 4'),
            'camera_xoffset1':        ('XTX1', 'Camera X Offset 1'),
            'camera_xoffset2':        ('XTX2', 'Camera X Offset 2'),
            'camera_xoffset3':        ('XTX3', 'Camera X Offset 3'),
            'camera_xoffset4':        ('XTX4', 'Camera X Offset 4'),
            },
        'init':  ['NAME', 'DESC', 'RTYP', 'XENG', 'BANG', 'KRST', 'S110', 'S100', \
                  'EMIN', 'EMAX', 'XVUM', 'ISOUT'],
        'config': ['DESC', 'XENG', 'BANG', 'KRST', 'S110', 'S100', 
                   'EMIN', 'EMAX', 'XVUM', 'ISOUT']
        },
    }

class EpicsRecordException(Exception):
    """ raised to indicate a problem with a motor"""
    def __init__(self, msg, *args):
        Exception.__init__(self, *args)
        self.msg = msg
    def __str__(self):
        return str(self.msg)


class lcls_record(Device):
    "General epics device for non-motor lcls records."

    _log_attrs = []
    _mutable = False
    _records = {}
    _fields = []
    _info_attrs = []

    _nonpvs = ('_prefix', '_pvs', '_delim', '_init', 
               '_alias', '_fields', '_records', '_info_attrs' )

    def __init__(self, name=None,
                 fields=None, records={}, init_list=None, 
                 record_dict=record_dict,
                 mutable=False, timeout=1.0):

        if name is None:
            raise EpicsRecordException("must supply record name")

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

               
        if not init_list:
            if rectype in record_dict and 'init' in record_dict[rectype]:
                init_list =  record_dict[rectype]['init']
            else: 
                init_list =  ('NAME', 'DESC', 'VAL', 'RTYP', 'DTYP')

        self._attr_tuple = fields
        self._alias = {item[0]: item[1][0] for item in fields.items()}

        self._fields = [item[1][0] for item in fields.items()]
        self._info_attrs = [item for item in init_list if item in self._fields]

        # Make sure _init_list is in the defined fields
#        set(_init_list).intersection([item[0] for attr, item in _fields.items()])

        Device.__init__(self, name, delim='.',
                                     records=records,
                                     attrs=init_list,
                                     mutable=False,
                                     timeout=timeout)

        # self.put('disabled', 0)
        self._callbacks = {}

        self._all_attrs = [attr for attr in self._alias.values()
                           if attr not in self._log_attrs]

    def _record_repr(self):
        value = self.get('VAL', as_string=True)
        if 'EGU' in self._fields:
            units = self.get('EGU', as_string=True)
        else:
            units = ''
        if 'DESC' in self._fields:
            desc = self.get('DESC', as_string=True)
        else:
            desc = ''
        return '<epics {:} record: {:s} = {:} {:s} : {:s}>'.format(
                self.RTYP, self._prefix.rstrip('.'), value, units, desc)

    def __repr__(self):
        self.show_info()
        return self._record_repr()

    def __str__(self):
        return self.get('VAL', as_string=True)

    def __getattr__(self, attr):
        " internal method "
        if attr in self._alias:
            attr = self._alias[attr]

        if attr in self._pvs:
            return self.get(attr)
        elif attr in self._records:
            return self.get_device(attr)
        elif attr in self.__dict__:
            return self.__dict__[attr]
        elif self._init and not attr.startswith('__') and (self._mutable or attr in self._fields):
            pv = self.PV(attr, connect=True)
            if not pv.connected:
                raise EpicsRecordException("Epics device has no attribute %s" % attr)
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
                raise EpicsRecordException("Record has no attribute %s" % attr)

    def __dir__(self):
        # taken from device.py: there's no cleaner method to do this until Python 3.3
        all_attrs = set(self._alias.keys() + self._pvs.keys() +
                        self._fields + self._records.keys() +
                        list(self._nonpvs) +
                        self.__dict__.keys() + dir(Device))
        return list(sorted(all_attrs))

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
#            attrs = self._info_attrs
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


