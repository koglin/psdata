# load ipsdata
# to clear Power Cycled flag for all motors in epicsArch

mms = [d['pv'] for m,d in data.epics._attr_dict.items() if d['components'][2] in ['MMS','CLZ','CLF'] and d['components'][4] in 'RBV']
for m in mms:
    p = m.rstrip('.RBV')+':SEQ_SELN'
    try:                           
        stat = epics.caget(p,timeout=1)
        if stat == 0:
            epics.caput(p,36)
            print p, 'Cleared Power Cycled Flag'
        else:
            print p, 'OK'
    except: 
        print p, 'ERROR:  No Connect'



