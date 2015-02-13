import re
import time

import epics
import ims
import newport
import pmc100
import motor_pcds
import lcls_records

def get_pv_connections(pvnamelist):
    pvdata = {}
    for name in pvnamelist:
        chid = epics.ca.create_channel(name, connect=False, auto_cb=False) # note 1
        pvdata[name] = (chid, None)

    for name, data in pvdata.items():
        epics.ca.connect_channel(data[0], timeout=0.1)
    
    epics.ca.poll()

    for name, data in pvdata.items():
        data = (data[0], epics.ca.isConnected(data[0]))
        if not data[1]:
            print 'No connect to', name

def get_live_pv(pv, attrs={}, delim='', module=None, report_connected=False, **kwargs):
    """Add live epics PV as pyepics device class.
    """
    epics_device = None
    try:
        epicsPV = epics.PV(pv)
        connected = epicsPV.connect(timeout=0.1)
        if not connected:
            time.sleep(0.1)
            connected = epicsPV.connect(timeout=0.2)
        
        if connected:
            try:
                rtyp = epics.caget(pv+'.RTYP')
                if rtyp in 'ims':
                    epics_device = ims.IMS(pv)
                    connect_message = 'Connected epics IMS PV {pv}'.format(pv=pv)
                elif rtyp in 'motor':
                    epics_device = motor_pcds.Motor(pv)
                    connect_message ='Connected epics motor PV {pv}'.format(pv=pv)
                elif rtyp in 'xps8p':
                    epics_device = newport.Newport(pv)
                    connect_message = 'Connected epics Newport PV {pv}'.format(pv=pv)
                elif rtyp in 'arcus':
                    epics_device = pmc100.Arcus(pv)
                    connect_message = 'Connected epics Piezo PV {pv}'.format(pv=pv)
                else:
                    epics_device = lcls_records.lcls_record(pv)
                    connect_message = 'Connected lcls record type {rtyp} for PV {pv}'.format(rtyp=rtyp,pv=pv)
                if report_connected:
                    print connect_message
            except:
                print 'WARNING: No RTYP field for PV {pv}'.format(pv=pv)
        else:
            print 'Timeout trying to connect {pv}'.format(pv=pv)
    except:
        if not pv:
            pv = None
        print 'Failed Adding {pv} as Motor Device'.format(pv=pv)
        epics_device = None

    return epics_device

                   
def epicsArch_dict(archfile_name,file_dir):
    arch_dict = {}
    file_list = [archfile_name]
    try:
        with open(file_dir+'/'+archfile_name,'r') as f:
            for line in f:
                if line.startswith('<'):
                    file_list.append(line.strip('<').strip(' ').strip('\n'))

        arch_list = []
        for file in file_list:
            with open(file_dir+'/'+file,'r') as f:
                arch_list.append(f.read().split('\n'))
                    
        arch_list = [item.strip(' ') for sublist in arch_list for item in sublist]

        pvalias = None
        for item in arch_list:
            if item.startswith(('#','<')):
                pvalias = None
            elif item.startswith('*'):
                pvalias = item.strip('*').strip(' ')
            elif len(item) > 1:
                pvname = item.strip(' ')
                pvbase = pvname.split('.')[0]
                if pvalias:
                    if pvalias in arch_dict:
                        print 'Warning: duplicate alias {:}'.format(pvalias)
                else:
                    pvalias = re.sub(':|\.','_',pvname) 

                components = re.split(':|\.',pvname)
                for i,item in enumerate(components):
                    if item[0].isdigit():
                         components[i] = 'n'+components[i]
     
                arch_dict[pvname] = {'name': pvname,
                                     'alias': pvalias,
                                     'base':  pvbase,
                                     'components': components} 

    except:
        print 'Error loading {:} from {:}'.format(archfile_name,file_dir)

    return arch_dict

def camviewer_dict(file_name,file_dir):
    cam_dict = {}
    cam_list = []
    with open(file_dir+'/'+file_name,'r') as f:
        for line in f:
            if not line.startswith('#') and not line.strip(' ').startswith('\n'):
                cam_list.append(line)
 

