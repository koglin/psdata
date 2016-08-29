## sspp.py
# first 

import epics
import string
import time

base_records = {
        'seq_length':      ('LEN',          'Sequence Length'),
        'play_mode':       ('PLYMOD',       'Play Mode'),
        'play_count':      ('PLYCNT',       'Play Count'),
        'play_control':    ('PLYCTL',       'Play Control (1=Start, 0=Stop)'),
        'play_status':     ('PLSTAT',       'Play Status'),
        'nrepeats_to_do':  ('REPCNT',       'Number of Repeats to do'),
        'total_count':     ('TPLCNT',       'Total play count'),
        'notify':          ('SEQ.PROC',     'Notify'),
        'sync_marker':     ('SYNCMARKER',   'Sync Marker'),
        'beam_request':    ('BEAMPULSEREQ', 'Beam Request'),
        'hutch_id':        ('HUTCH_ID',     'Hutch ID'),
        'event_codes':     ('SEQ.A',        'Event Code Array'),
        'beam_delays':     ('SEQ.B',        'Beam Delay Array'),
        'fiducial_delays': ('SEQ.C',        'Fiducial Delay Array'),
        'burst_counts':    ('SEQ.D',        'Burst Count Array'),
    }

other_records = {
        'beam_owner':      ('ECS:SYS0:0:BEAM_OWNER_ID',  'Beam Owner'),  
        'testburst_dep'    ('PATT:SYS0:1:TESTBURST.N',   'Test Burst Count'),
        'testburst_rate'   ('PATT:SYS0:1:TESTBURSTRATE', 'Test Burst Rate'),
        'beam_rate':       ('EVNT:SYS0:1:LCLSBEAMRATE',  'LCLS Beam Rate'),
    }

class event_sequencer(device.Device):


class SingleShot():
#global defines that are expected to stay the same for a given location in a given hutch
    global EVENTCODE_PPTRIG
    EVENTCODE_PPTRIG=185
    global EVENTCODE_DAQTRIG
    EVENTCODE_DAQTRIG=186
#values in ns
    global EVR_DELAY
    EVR_DELAY=37800
    global EVR_WIDTH
    EVR_WIDTH=16800
    def __init__(self):
#the event sequencer device
        self.es=epics.Device(prefix='ECS:SYS0:5',delim=':',\
        attrs=('PLSTAT','PLYCTL','SYNCMARKER','PLYMOD','SYNCNEXTTICK','BEAMPULSEREQ','LEN'))
        for i in range(0,18):
            #event code to send on this step
            str1='CXI:ECS:IOC:01:EC_5:%02d'%(i)
            str2='ECODE%02d'%i
            self.es.add_pv(str1,attr=str2)
            #delta-beams
            str1='CXI:ECS:IOC:01:BD_5:%02d'%(i)
            str2='DBEAM%02d'%i
            self.es.add_pv(str1,attr=str2)
            #delta-fiducials
            str1='CXI:ECS:IOC:01:FD_5:%02d'%(i)
            str2='DFID%02d'%i
            self.es.add_pv(str1,attr=str2)
            #number of bursts to request on this step
            str1='CXI:ECS:IOC:01:BC_5:%02d'%(i)
            str2='NBUR%02d'%i
            self.es.add_pv(str1,attr=str2)
            #label for this step
            str1='CXI:ECS:IOC:01:EC_5:%02d.DESC'%(i)
            str2='STEPDESC%02d'%i
            self.es.add_pv(str1,attr=str2)   
            #limited pulse picker device
            self.pp=epics.Device(prefix='CXI:ATC:MMS:29',delim=':',attrs=('SET_SE','SE','READ_DF','DF'))
            #simple evr device
            self.evr=epics.Device(prefix='CXI:R52:EVR:01:TRIG2',delim=':',\
            attrs=('TEC','TCTL.DESC','TCTL','TPOL','TWID','TDES','EC_RBV','BW_TDES'))
    
    def status(self):
        #check status of pulsepicker, evr and event sequencer settings
        print "Status of all:"
        print " [evr] EVR reacts to event code %d"%(self.evr.get('EC_RBV'))
        print " [evr] EVR trigger is %s"%(self.evr.get('TCTL',as_string=True))
        print " [evr] EVR width is %s"%(self.evr.get('TWID',as_string=True))
        print " [evr] EVR sends pulse delayed by %f ns"%(self.evr.get('BW_TDES'))
        print " [evr] EVR pulse is %s"%(self.evr.get('TPOL',as_string=True))
        print " [pp] Pulse Picker is in mode %d"%(self.pp.get('SE'))
        print " [pp] Pulse Picker is at position %s"%(self.pp.get('READ_DF',as_string=True))
        print " [es] Play status is %s"%(self.es.get('PLSTAT',as_string=True))
        print " [es] 'Sync Marker' is set to %s"%(self.es.get('SYNCMARKER',as_string=True))
        print " [es] 'Next sync' is set to %s"%(self.es.get('SYNCNEXTTICK',as_string=True))
        print " [es] 'Run using' is set to %s"%(self.es.get('BEAMPULSEREQ',as_string=True))
        print " [es] Step 0 sends event code %d"%(self.es.get('ECODE00'))
        print " [es] Step 0 waits %d generated beams"%(self.es.get('DBEAM00'))
        print " [es] Step 0 waits %d fiducials"%(self.es.get('DFID00'))
        print " [es] Step 0 requests %d bursts"%(self.es.get('NBUR00'))
        print " [es] Step 1 sends event code %d"%(self.es.get('ECODE01'))
        print " [es] Step 1 waits %d generated beams"%(self.es.get('DBEAM01'))
        print " [es] Step 1 waits %d fiducials"%(self.es.get('DFID01'))
        print " [es] Step 1 requests %d bursts"%(self.es.get('NBUR01'))
    
    def faststatus(self):
        #check pulsepicker readback and event sequencer play status
        print "Limited status is:"
        print " [pp] Pulse Picker is in mode %d"%(self.pp.get('SE'))
        print " [pp] Pulse Picker is at position %s"%(self.pp.get('READ_DF',as_string=True))
        print " [es] Play status is %s"%(self.es.get('PLSTAT',as_string=True))
    
    def shoot(self):
        #take a shot
        self.es.put('PLYCTL',1)
    
    def simshoot(self):
        print "Taking one shot with pulse picker"
        print " [es] writing '1' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['PLYCTL'])," ")[1],',')
    
    def simsetup(self):
        global EVENTCODE_PPTRIG
        global EVENTCODE_DAQTRIG
        global EVR_DELAY
        print "[sim] Setting up single shot mode for LCLS v2 pulse picker"
        print " [pp] writing '0' to "+string.rstrip(string.rsplit(repr(self.pp.__dict__['_pvs']['SET_SE'])," ")[1],',')
        print " [pp] writing '2' to "+string.rstrip(string.rsplit(repr(self.pp.__dict__['_pvs']['SET_SE'])," ")[1],',')
        print " [es] writing '120Hz' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['SYNCMARKER'])," ")[1],',')
        print " [es] writing 'Once' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['PLYMOD'])," ")[1],',')
        print " [es] writing 'Immediate' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['SYNCNEXTTICK'])," ")[1],',')
        print " [es] writing 'Timeslot' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['BEAMPULSEREQ'])," ")[1],',')
        print " [es] writing '2' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['LEN'])," ")[1],',')
        print " [es] writing '"+repr(EVENTCODE_PPTRIG)+"' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['ECODE00'])," ")[1],',')
        print " [es] writing '1' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['DBEAM00'])," ")[1],',')
        print " [es] writing '0' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['DFID00'])," ")[1],',')
        print " [es] writing '0' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['NBUR00'])," ")[1],',')
        print " [es] writing 'PulsePickerDSB' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['STEPDESC00'])," ")[1],',')
        print " [es] writing '"+repr(EVENTCODE_DAQTRIG)+"' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['ECODE01'])," ")[1],',')
        print " [es] writing '1' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['DBEAM01'])," ")[1],',')
        print " [es] writing '0' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['DFID01'])," ")[1],',')
        print " [es] writing '0' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['NBUR01'])," ")[1],',')
        print " [es] writing 'DAQ Readout' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['STEPDESC01'])," ")[1],',')
        print " [evr] writing '"+repr(EVENTCODE_PPTRIG)+"' to "+string.rstrip(string.rsplit(repr(self.evr.__dict__['_pvs']['TEC'])," ")[1],',')
        print " [evr] writing '"+repr(EVR_DELAY)+"' to "+string.rstrip(string.rsplit(repr(self.evr.__dict__['_pvs']['TDES'])," ")[1],',')
        print " [evr] writing '"+repr(EVR_TWID)+"' to "+string.rstrip(string.rsplit(repr(self.evr.__dict__['_pvs']['TWID'])," ")[1],',')
        print " [evr] writing 'Inverted' to "+string.rstrip(string.rsplit(repr(self.evr.__dict__['_pvs']['TPOL'])," ")[1],',')
        print " [evr] writing 'Enabled' to "+string.rstrip(string.rsplit(repr(self.evr.__dict__['_pvs']['TCTL'])," ")[1],',')
    
    def fastsetup(self):
        self.pp.put('SET_SE',0)
        time.sleep(0.5)
        self.pp.put('SET_SE',2)
        self.es.put('PLYCTL','0')
        self.es.put('SYNCMARKER','120Hz')
        self.es.put('PLYMOD','Once')
        self.es.put('SYNCNEXTTICK','Immediate')
        self.es.put('BEAMPULSEREQ','Timeslot')
        self.es.put('LEN',2)
        self.es.put('ECODE00',EVENTCODE_PPTRIG)
        self.es.put('DBEAM00',1)
        self.es.put('DFID00',0)
        self.es.put('NBUR00',0)
        self.es.put('STEPDESC00','PulsePickerDSB')
        self.es.put('ECODE01',EVENTCODE_DAQTRIG)
        self.es.put('DBEAM01',1)
        self.es.put('DFID01',0)
        self.es.put('NBUR01',0)
        self.es.put('STEPDESC01','DAQ Readout')
        self.evr.put('TEC',EVENTCODE_PPTRIG)
        self.evr.put('TDES',EVR_DELAY)
        self.evr.put('TCTL',1)
        self.evr.put('TWID',EVR_WIDTH)
        self.evr.put('TPOL',1)
        def setup(self):
        print "[act] Setting up  single shot mode for LCLS v2 pulse picker"
            print " [pp] writing '0' to "+string.rstrip(string.rsplit(repr(self.pp.__dict__['_pvs']['SET_SE'])," ")[1],',')
        self.pp.put('SET_SE',0)
        time.sleep(0.5)
        if self.pp.get('SE') is not 0:
            print "[err] write failed!"
            print " [pp] writing '2' to "+string.rstrip(string.rsplit(repr(self.pp.__dict__['_pvs']['SET_SE'])," ")[1],',')
        self.pp.put('SET_SE',2)
        time.sleep(0.5)
        print self.pp.get('SE')
        if self.pp.get('SE') is not 2:
            print "[err] write failed!"
            print " [es] Stopping event sequencer" 
        self.es.put('PLYCTL','0')
        time.sleep(0.5)
        if self.es.get('PLSTAT') is not 0:
            print "[err] write failed!"
            print " [es] writing '120Hz' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['SYNCMARKER'])," ")[1],',')
        self.es.put('SYNCMARKER','120Hz')
        time.sleep(0.5)
        if self.es.get('SYNCMARKER') is not '120Hz':
            print "[err] write failed!"
            print " [es] writing 'Once' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['PLYMOD'])," ")[1],',')
        self.es.put('PLYMOD','Once')
        time.sleep(0.5)
        if self.es.get('PLYMOD') is not 'Once':
            print "[err] write failed!"
            print " [es] writing 'Immediate' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['SYNCNEXTTICK'])," ")[1],',')
        self.es.put('SYNCNEXTTICK','Immediate')
        time.sleep(0.5)
        if self.es.get('SYNCNEXTTICK') is not 'Immediate':
            print "[err] write failed!"
            print " [es] writing 'Timeslot' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['BEAMPULSEREQ'])," ")[1],',')
        self.es.put('BEAMPULSEREQ','Timeslot')
        time.sleep(0.5)
        if self.es.get('BEAMPULSEREQ') is not 'Timeslot':
            print "[err] write failed!"
            print " [es] writing '2' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['LEN'])," ")[1],',')
        self.es.put('LEN',2)
        time.sleep(0.5)
        if self.es.get('LEN') is not 2:
            print "[err] write failed!"
            print " [es] writing '"+repr(EVENTCODE_PPTRIG)+"' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['ECODE00'])," ")[1],',')
        self.es.put('ECODE00',EVENTCODE_PPTRIG)
        time.sleep(0.5)
        if self.es.get('ECODE00') is not EVENTCODE_PPTRIG:
            print "[err] write failed!"
            print " [es] writing '1' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['DBEAM00'])," ")[1],',')
        self.es.put('DBEAM00',1)
        time.sleep(0.5)
        if self.es.get('DBEAM00') is not 1:
            print "[err] write failed!"
            print " [es] writing '0' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['DFID00'])," ")[1],',')
        self.es.put('DFID00',0)
        time.sleep(0.5)
        if self.es.get('DFID00') is not 0:
            print "[err] write failed!"
            print " [es] writing '0' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['NBUR00'])," ")[1],',')
        self.es.put('NBUR00',0)
        time.sleep(0.5)
        if self.es.get('NBUR00') is not 0:
            print "[err] write failed!"
            print " [es] writing 'PulsePickerDSB' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['STEPDESC00'])," ")[1],',')
        self.es.put('STEPDESC00','PulsePickerDSB')
        time.sleep(0.5)
        if self.es.get('STEPDESC00') is not 'PulsePickerDSB':
            print "[err] write failed!"
            print " [es] writing '"+repr(EVENTCODE_DAQTRIG)+"' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['ECODE01'])," ")[1],',')
        self.es.put('ECODE01',EVENTCODE_DAQTRIG)
        time.sleep(0.5)
        if self.es.get('ECODE01') is not EVENTCODE_DAQTRIG:
            print "[err] write failed!"
            print " [es] writing '1' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['DBEAM01'])," ")[1],',')
        self.es.put('DBEAM01',1)
        time.sleep(0.5)
        if self.es.get('DBEAM01') is not 1:
            print "[err] write failed!"
            print " [es] writing '0' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['DFID01'])," ")[1],',')
        self.es.put('DFID01',0)
        time.sleep(0.5)
        if self.es.get('DFID01') is not 0:
            print "[err] write failed!"
            print " [es] writing '0' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['NBUR01'])," ")[1],',')
        self.es.put('NBUR01',0)
        time.sleep(0.5)
        if self.es.get('NBUR01') is not 0:
            print "[err] write failed!"
            print " [es] writing 'DAQ Readout' to "+string.rstrip(string.rsplit(repr(self.es.__dict__['_pvs']['STEPDESC01'])," ")[1],',')
        self.es.put('STEPDESC01','DAQ Readout')
        time.sleep(0.5)
        if self.es.get('STEPDESC01') is not 'DAQ Readout':
            print "[err] write failed!"
            print " [evr] writing '"+repr(EVENTCODE_PPTRIG)+"' to "+string.rstrip(string.rsplit(repr(self.evr.__dict__['_pvs']['TEC'])," ")[1],',')
        self.evr.put('TEC',EVENTCODE_PPTRIG)
        time.sleep(0.5)
        if self.evr.get('EC_RBV') is not EVENTCODE_PPTRIG:
            print "[err] write failed!"
            print " [evr] writing '"+repr(EVR_DELAY)+"' to "+string.rstrip(string.rsplit(repr(self.evr.__dict__['_pvs']['TDES'])," ")[1],',')
        self.evr.put('TDES',EVR_DELAY)
        time.sleep(0.5)
        if self.evr.get('BW_TDES') is not EVR_DELAY:
            print "[err] write failed!"
            print " [evr] Setting EVR trigger to 'Enabled''"
        self.evr.put('TCTL',1)
        time.sleep(0.5)
        if self.evr.get('TCTL',as_string=True) is not 'Enabled':
            print "[err] write failed!"
            print " [evr] Setting EVR width to "
        self.evr.put('TWID',EVR_WIDTH)
        time.sleep(0.5)
        if self.evr.get('TWID') is not EVR_WIDTH:
            print "[err] write failed!"
            print " [evr] Setting EVR trigger to 'Inverted'"
        self.evr.put('TPOL',1)
        time.sleep(0.5)
        if self.evr.get('TPOL',as_string=True) is not 'Inverted':
            print "[err] write failed!"


