import device

#grep "^CXI:DG2:PIM" /reg/d/iocData/ioc-cxi-dg2-pim-ims/iocInfo/IOC.pvlist | sed 's/,/",/g' | cut -d ',' -f1 | sed 's/CXI:DG2:PIM:/"/g'

#grep "^CXI:DG2:IPM" /reg/d/iocData/ioc-cxi-dg2-ipm-ims/iocInfo/IOC.pvlist | sed 's/,/",/g' | cut -d ',' -f1 | sed 's/CXI:DG2:IPM:/"/g'
# grep "^CXI:DG2" /reg/d/iocData/ioc-cxi-slits-ims/iocInfo/IOC.pvlist | sed 's/,/",/g' | cut -d ',' -f1 | sed 's/CXI:DG2:/"/g' | grep 'JAWS'


class ai(device.Device):
    "Simple analog input device"

    _ims_config_attrs = {
        "pim": ("CENH", "CENV", 
                "PIXH", "PIXV", 
                "YAG:GO_IN", "YAG:GO_OUT", 
                "YAG:IN_DELTA", "YAG:IN_SET", 
                "YAG:OUT_DELTA", "YAG:OUT_SET", 
                "YAG:IN", "YAG:OUT", 
                "YAG:IN_CALC", "YAG:OUT_CALC", 
                "YAG:STATE_CALC", 
                "NOPH", "NOPV", 
                "YAG", "YAG:GO", "YAG:GO_SEQ", 
                "ZOOM"),
        "ipm": ("DIODE:GO_IN", "DIODE:GO_OUT", 
                "DIODE:IN_DELTA", "DIODE:IN_SET"
                "DIODE:OUT_DELTA", "DIODE:OUT_SET", 
                "TARGET:GO_OUT", 
                "TARGET:GO_TARGET1", "TARGET:GO_TARGET2", 
                "TARGET:GO_TARGET3", "TARGET:GO_TARGET4", 
                "TARGET:OUT_DELTA", "TARGET:OUT_SET", 
                "TARGET:TARGET1_DELTA", "TARGET:TARGET1_SET", 
                "TARGET:TARGET2_DELTA", "TARGET:TARGET2_SET", 
                "TARGET:TARGET3_DELTA", "TARGET:TARGET3_SET", 
                "TARGET:TARGET4_DELTA", "TARGET:TARGET4_SET", 
                "DIODE:IN", "DIODE:OUT", "TARGET:OUT", 
                "TARGET:TARGET1", "TARGET:TARGET2", 
                "TARGET:TARGET3", "TARGET:TARGET4", 
                "DIODE:IN_CALC", "DIODE:OUT_CALC", 
                "DIODE:STATE_CALC", "TARGET:OUT_CALC", 
                "TARGET:STATE_CALC", 
                "TARGET:TARGET1_CALC", "TARGET:TARGET2_CALC", 
                "TARGET:TARGET3_CALC", "TARGET:TARGET4_CALC", 
                "DIODE", "TARGET", "DIODE:GO", "TARGET:GO", 
                "DIODE:GO_SEQ", "TARGET:GO_SEQ"), 
        "jaws" ("XCDELTA"
                "XCEN_REQ"
                "XCEN_REQ:SETZERO"
                "XWDELTA"
                "XWID_REQ"
                "XWID_REQ:SETZERO"
                "YCDELTA"
                "YCEN_REQ"
                "YCEN_REQ:SETZERO"
                "YWDELTA"
                "YWID_REQ"
                "YWID_REQ:SETZERO"
                "DMOV"
                "ACTUAL_XCENTER"
                "ACTUAL_XWIDTH"
                "ACTUAL_YCENTER"
                "ACTUAL_YWIDTH"
                "BLOCKED_CALC"
                "DMOV_CALC"
                "EDGE:BOTTOM"
                "EDGE:LEFT"
                "EDGE:RIGHT"
                "EDGE:TOP"
                "MOVE_BOT1"
                "MOVE_BOT2"
                "MOVE_LFT1"
                "MOVE_LFT2"
                "MOVE_RHT1"
                "MOVE_RHT2"
                "MOVE_TOP1"
                "MOVE_TOP2"
                "X:CENTER:SETZERO:LFT"
                "X:CENTER:SETZERO:RHT"
                "X:WIDTH:SETZERO:LFT"
                "X:WIDTH:SETZERO:RHT"
                "XCEN_REQ:DRVH"
                "XCEN_REQ:DRVL"
                "XCNUDGE"
                "XWID_REQ:DRVH"
                "XWID_REQ:DRVH_INIT"
                "XWID_REQ:DRVL"
                "XWNUDGE"
                "Y:CENTER:SETZERO:BOT"
                "Y:CENTER:SETZERO:TOP"
                "Y:HEIGHT:SETZERO:BOT"
                "Y:HEIGHT:SETZERO:TOP"
                "YCEN_REQ:DRVH"
                "YCEN_REQ:DRVL"
                "YCNUDGE"
                "YWID_REQ:DRVH"
                "YWID_REQ:DRVH_INIT"
                "YWID_REQ:DRVL"
                "YWNUDGE"
                "X:CENTER:SETZERO"
                "X:WIDTH:SETZERO"
                "Y:CENTER:SETZERO"
                "Y:HEIGHT:SETZERO"
                "BLOCKED"
                "BLOCK"
                "CLOSE"
                "OPEN")}

    def __init__(self, prefix, **kwargs):
        
        device.Device.__init__(self, prefix, delim=':',
                              attrs=self.attrs, **kwargs)


