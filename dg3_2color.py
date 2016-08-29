import psdata

cxi = psdata.psdata(epics_live=True, instrument='cxi')
cxi.Dg3Pim.add_module('pim_2color')
cxi.Dg3Pim.monitor_summary()

