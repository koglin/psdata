#!/usr/bin/env python
"""
 This module provides support for the EPICS IMS motor record at LCLS.
"""
# 
# Author:         Jason Koglin (based on Motor.py by Mark Rivers / Matt Newville)
# Created:        August, 2014
# Modifications:
#

import sys
import time
import epics 
import device

class ImsLimitException(Exception):
    """ raised to indicate a motor limit has been reached """
    def __init__(self, msg, *args):
        Exception.__init__(self, *args)
        self.msg = msg
    def __str__(self):
        return str(self.msg)

class ImsException(Exception):
    """ raised to indicate a problem with a motor"""
    def __init__(self, msg, *args):
        Exception.__init__(self, *args)
        self.msg = msg
    def __str__(self):
        return str(self.msg)

class MotorV7(device.Device):
    """Epics IMS Motor Class for pyepics3

   UNDER DEVELOPMENT!!! 
   This module provides a class library for the EPICS motor record.

   It uses the epics.Device and epics.PV classese

   Virtual attributes:
      These attributes do not appear in the dictionary for this class, but
      are implemented with the __getattr__ and __setattr__ methods.  They
      simply get or putthe appropriate motor record fields.  All attributes
      can be both read and written unless otherwise noted. 

      Attribute        Description                  Field
      ---------        -----------------------      -----
      drive            Motor Drive Value            .VAL
      readback         Motor Readback Value         .RBV    (read-only) 
      slew_speed       Slew speed or velocity       .VELO
      base_speed       Base or starting speed       .VBAS
      acceleration     Acceleration time (sec)      .ACCL
      description      Description of motor         .DESC
      resolution       Resolution (units/step)      .MRES
      high_limit       High soft limit (user)       .HLM
      low_limit        Low soft limit (user)        .LLM
      dial_high_limit  High soft limit (dial)       .DHLM
      dial_low_limit   Low soft limit (dial)        .DLLM
      backlash         Backlash distance            .BDST
      offset           Offset from dial to user     .OFF
      done_moving      1=Done, 0=Moving, read-only  .DMOV
 
   Exceptions:
      The check_limits() method raises an 'ImsLimitException' if a soft limit
      or hard limit is detected.  The move() method calls
      check_limits() unless they are called with the 
      ignore_limits=True keyword set.

   Example use:
      from epics import Motor
      m = Motor('13BMD:m38')
      m.move(10)               # Move to position 10 in user coordinates
      m.move(100, dial=True)   # Move to position 100 in dial coordinates
      m.move(1, step=True, relative=True) # Move 1 step relative to current position

      m.stop()                 # Stop moving immediately
      high = m.high_limit      # Get the high soft limit in user coordinates
      m.dial_high_limit = 100  # Set the high limit to 100 in dial coodinates
      speed = m.slew_speed     # Get the slew speed
      m.acceleration = 0.1     # Set the acceleration to 0.1 seconds
      p=m.get_position()       # Get the desired motor position in user coordinates
      p=m.get_position(dial=1) # Get the desired motor position in dial coordinates
      p=m.get_position(readback=1) # Get the actual position in user coordinates
      p=m.get_position(readback=1, step=1) Get the actual motor position in steps
      p=m.set_position(100)   # Set the current position to 100 in user coordinates
         # Puts motor in Set mode, writes value, puts back in Use mode.
      p=m.set_position(10000, step=1) # Set the current position to 10000 steps

    """
    # parameter name (short), PV suffix,  longer description
   fields = {
       'acceleration':           ('ACCL', 'acceleration time'),
       'back_accel':             ('BACC', 'backlash acceleration time'),
       'backlash':               ('BDST', 'backlash distance'),
       'back_speed':             ('BVEL', 'backlash speed'),
       'card':                   ('CARD', 'Card Number '),
       'dial_high_limit':        ('DHLM', 'Dial High Limit '),
       'direction':              ('DIR',  'User Direction '),
       'dial_low_limit':         ('DLLM', 'Dial Low Limit '),
       'settle_time':            ('DLY',  'Readback settle time (s) '),
       'done_moving':            ('DMOV', 'Done moving to value'),
       'dial_readback':          ('DRBV', 'Dial Readback Value'),
       'description':            ('DESC', 'Description'),
       'dial_drive':             ('DVAL', 'Dial Desired Value'),
       'units':                  ('EGU',  'Engineering Units '),
       'encoder_step':           ('ERES', 'Encoder Step Size '),
       'freeze_offset':          ('FOFF', 'Offset-Freeze Switch '),
       'move_fraction':          ('FRAC', 'Move Fraction'),
       'hi_severity':            ('HHSV', 'Hihi Severity '),
       'hi_alarm':               ('HIGH', 'High Alarm Limit '),
       'hihi_alarm':             ('HIHI', 'Hihi Alarm Limit '),
       'high_limit':             ('HLM',  'User High Limit  '),
       'high_limit_set':         ('HLS',  'High Limit Switch  '),
       'hw_limit':               ('HLSV', 'HW Lim. Violation Svr '),
#       'home_forward':           ('HOMF', 'Home Forward  '),
#       'home_reverse':           ('HOMR', 'Home Reverse  '),
       'high_op_range':          ('HOPR', 'High Operating Range'),
       'high_severity':          ('HSV',  'High Severity '),
       'integral_gain':          ('ICOF', 'Integral Gain '),
       'jog_accel':              ('JAR',  'Jog Acceleration (EGU/s^2) '),
#       'jog_forward':            ('JOGF', 'Jog motor Forward '),
#       'jog_reverse':            ('JOGR', 'Jog motor Reverse'),
       'jog_speed':              ('JVEL', 'Jog Velocity '),
       'last_dial_val':          ('LDVL', 'Last Dial Des Val '),
       'low_limit':              ('LLM',  'User Low Limit  '),
       'low_limit_set':          ('LLS',  'At Low Limit Switch'),
       'lo_severity':            ('LLSV', 'Lolo Severity  '),
       'lolo_alarm':             ('LOLO', 'Lolo Alarm Limit  '),
       'low_op_range':           ('LOPR', 'Low Operating Range '),
       'low_alarm':              ('LOW',  'Low Alarm Limit '),
       'last_rel_val':           ('LRLV', 'Last Rel Value  '),
       'last_dial_drive':        ('LRVL', 'Last Raw Des Val  '),
       'last_SPMG':              ('LSPG', 'Last SPMG  '),
       'low_severity':           ('LSV',  'Low Severity  '),
       'last_drive':             ('LVAL', 'Last User Des Val'),
       'soft_limit':             ('LVIO', 'Limit violation  '),
       'in_progress':            ('MIP',  'Motion In Progress '),
       'missed':                 ('MISS', 'Ran out of retries '),
       'moving':                 ('MOVN', 'Motor is moving  '),
       'resolution':             ('MRES', 'Motor Step Size (EGU)'),
       'motor_status':           ('MSTA', 'Motor Status  '),
       'offset':                 ('OFF',  'User Offset (EGU) '),
       'output_mode':            ('OMSL', 'Output Mode Select  '),
       'output':                 ('OUT',  'Output Specification '),
       'prop_gain':              ('PCOF', 'Proportional Gain '),
       'precision':              ('PREC', 'Display Precision '),
       'readback':               ('RBV',  'User Readback Value '),
       'retry_max':              ('RTRY', 'Max retry count    '),
       'retry_count':            ('RCNT', 'Retry count  '),
       'retry_deadband':         ('RDBD', 'Retry Deadband (EGU)'),
       'dial_difference':        ('RDIF', 'Difference rval-rrbv '),
       'raw_encoder_pos':        ('REP',  'Raw Encoder Position '),
       'raw_high_limit':         ('RHLS', 'Raw High Limit Switch'),
       'raw_low_limit':          ('RLLS', 'Raw Low Limit Switch'),
       'relative_value':         ('RLV',  'Relative Value    '),
       'raw_motor_pos':          ('RMP',  'Raw Motor Position '),
       'raw_readback':           ('RRBV', 'Raw Readback Value '),
       'readback_res':           ('RRES', 'Readback Step Size (EGU)'),
       'raw_drive':              ('RVAL', 'Raw Desired Value  '),
       'dial_speed':             ('RVEL', 'Raw Velocity '),
       's_speed':                ('S',    'Speed (RPS)  '),
       's_back_speed':           ('SBAK', 'Backlash Speed (RPS)  '),
       's_base_speed':           ('SBAS', 'Base Speed (RPS)'),
       's_max_speed':            ('SMAX', 'Max Velocity (RPS)'),
#       'set':                    ('SET',  'Set/Use Switch '),
       'stop_go':                ('SPMG', 'Stop/Pause/Move/Go '),
       's_revolutions':          ('SREV', 'Steps per Revolution '),
#       'stop':                   ('STOP', 'Stop  '),
       't_direction':            ('TDIR', 'Direction of Travel '),
#       'tweak_forward':          ('TWF',  'Tweak motor Forward '),
#       'tweak_reverse':          ('TWR',  'Tweak motor Reverse '),
       'tweak_val':              ('TWV',  'Tweak Step Size (EGU) '),
       'u_revolutions':          ('UREV', 'EGU per Revolution  '),
       'use_rdbl':               ('URIP', 'Use RDBL Link If Present'),
       'drive':                  ('VAL',  'User Desired Value'),
       'base_speed':             ('VBAS', 'Base Velocity (EGU/s)'),
       'slew_speed':             ('VELO', 'Velocity (EGU/s) '),
       'version':                ('VERS', 'Code Version '),
       'max_speed':              ('VMAX', 'Max Velocity (EGU/s)'),
       'use_home':               ('ATHM', 'uses the Home switch'),
       'deriv_gain':             ('DCOF', 'Derivative Gain '),
       'use_torque':             ('CNEN', 'Enable torque control '),
       'device_type':            ('DTYP', 'Device Type'),
       'record_type':            ('RTYP', 'Record Type'),
       'status':                 ('STAT', 'Status'),
       'use_encoder':            ('UEIP', 'Use Encoder If Present')}

    records = {
       'mcode_encoder':          ('EE', 'Encoder  '),
       'mcode_hold_current':     ('HC', 'Hold Current  '),
       'mcode_run_current':      ('RC', 'Run Current  '),
       'mcode_encoderlines':     ('EL', 'Encoder Lines (encoder counts/motor turn/4.)'),
       'mcode_s1':               ('S1', 'Switch 1 (CW) setting'),
       'mcode_s2':               ('S2', 'Switch 2 (CCW) setting'),
       'mcode_s3':               ('S3', 'Switch 3 Encoder Power'),
       'mcode_s4':               ('S4', 'Switch 4 Homing Switch'),
       'mcode_limitmode_l':      ('LM_L', 'Limit Mode (number)'),
       'mcode_limitmode':        ('LM', 'Limit Mode'),
       'mcode_pm':               ('PM', 'Position Maintanence'),
       'mcode_ht':               ('HT', 'Motor Hold Current Time'),
       'mcode_baudrate_l':       ('BD_L', 'Baud Rate (number)'),
       'mcode_baudrate':         ('BD', 'Baud Rate'),
       'mcode_motorsettling':    ('MT', 'Motor Settling time'),
       'mcode_microsteps':       ('MS', 'Microsteps'),
       'mcode_deadband':         ('DB', 'Deadband'),
       'mcode_stallfactor':      ('SF', 'Stall Factor'),
       'mcode_stallmode':        ('SM', 'Stall Mode'),
       'mcode_userreg1':         ('R1', 'User Register 1'),
       'mcode_userreg2':         ('R2', 'User Register 2'),
       'mcode_userreg3':         ('R3', 'User Register 3'),
       'mcode_userreg4':         ('R4', 'User Register 4'),
       'mcode_maxvelocity':      ('VM', 'Max Velocity'),
       'mcode_initialvelocity':  ('VI', 'Initial Velocity'),
       'mcode_acceleration':     ('A', 'Acceleration'),
       'mcode_deceleration':     ('D', 'Deceleration'),
       'mcode_numericenable':    ('NE', 'Numeric Enable'),
       'mcode_stallflag':        ('ST', 'Stall Flag'),
       'mcode_part_number':      ('PN', 'Part Number'),
       'mcode_serial_number':    ('SN', 'Serial Number'),
       'mcode_version':          ('VR', 'MCode Version'),
       'mcode_errorflag':        ('EF', 'MCode Error Flag'),
       'mcode_positivelimit':    ('I1', 'Positive Limit'),
       'mcode_negativelimit':    ('I2', 'Negative Limit'),
       'mcode_encoderpower':     ('I3', 'Encoder Power'),
       'mcode_homeswitch':       ('I4', 'Home Switch'),
       'mcode_encoderindex':     ('I6', 'Encoder Index'),
       'mcode_savedeadband':     ('SD', 'Save Deadband'),
       'mcode_numberofsaves':    ('NS', 'Number of Saves'),
       'mcode_timercounter':     ('R1', 'Timer Counter'),
       'mcode_checksum_enable':  ('CK', 'Checksum Enable'),
       'mcode_devicename':       ('DN', 'Device Name')}

    _attr_tuple = {}
    _alias = {}
    _mutable = False

    _nonpvs = ('_prefix', '_pvs', '_delim', '_init', '_init_list',
               '_alias', '_fields', '_records')
    _log_attrs = ['LOGA', 'LOGB', 'LOGC', 'LOGD', 'LOGE', 'LOGF', 'LOGG', 'LOGH']
    _info_attrs = ['DESC', 'VAL', 'RBV', 'EGU', 'PREC', 'VELO', 'ACCL', 
                   'STAT', 'TWV','LLM', 'HLM', 'EE', 'RC', 'HC', 'RTYP']
    _mcode_attrs = ['EE', 'RC', 'HC']
    _ioc_attrs = ['PORT']
    _init_list = _info_attrs

    def __init__(self, name=None, 
                 fields=fields, records=records, 
                 mutable=False, timeout=3.0):
        if name is None:
            raise ImsException("must supply motor name")

        self._attr_tuple = dict(records.items() + fields.items())
        self._alias = {item[0]: item[1][0] for item in records.items() + fields.items()}

        self._fields = [item[1][0] for item in fields.items()]
        self._records = [item[1][0] for item in records.items()]

        if name.endswith('.VAL'):
            name = name[:-4]
        if name.endswith('.'):
            name = name[:-1]

        self._prefix = name
        device.Device.__init__(self, name, delim='.', 
#                                     attrs=self._fields,
                                     attrs=self._init_list,
                                     mutable=False,
                                     timeout=timeout)

        for attr in self._records:
            pvrecord = name+':'+attr
#            print 'Adding {pvrecord}'.format(pvrecord=pvrecord)
            self.add_pv(pvrecord, attr=attr)

         # make sure this is really a motor!
        rectype = self.get('RTYP')
        if rectype != 'motor':
            raise ImsException("%s is not an old LCLS IMS V7 or V6 motor" % name)

        # self.put('disabled', 0)
        self._callbacks = {}

    def _ims_repr(self):
        return '<Old LCLS Motor: {:s} = {:.2f} {:s} : {:s}>'.format(
                self._prefix.rstrip('.'), self.VAL, self.EGU,  self.DESC)

    def __repr__(self):
        self.show_info()
        return self._ims_repr()

    def __str__(self):
        return self.__repr__()

    def __getattr__(self, attr):
        """ internal method 
        """
        if attr in self._alias:
            attr = self._alias[attr]

        if attr in self._pvs:
            return self.get(attr)
        elif attr in self.__dict__:
            return self.__dict__[attr]
        elif self._init and not attr.startswith('__') and (self._mutable or attr in self._fields):
            pv = self.PV(attr, connect=True)
            if not pv.connected:
                raise ImsException("EpicsMotor has no attribute %s" % attr)
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

    def check_limits(self):
        """ check motor limits:
        returns None if no limits are violated
        raises expection if a limit is violated"""
        for field, msg in (('LVIO', 'Soft limit violation'),
                           ('HLS',  'High hard limit violation'),
                           ('LLS',  'Low  hard limit violation')):
            if self.get(field) != 0:
                raise ImsLimitException(msg)
        return
    
    def within_limits(self, val, dial=False):
        """ returns whether a value for a motor is within drive limits
        with dial=True   dial limits are used (default is user limits)"""
        ll_name, hl_name = 'LLM', 'HLM'
        if dial:
            ll_name, hl_name = 'DLLM', 'DHLM'
        return (val <= self.get(hl_name) and val >= self.get(ll_name))

    def move(self, val=None, relative=False, wait=False, timeout=300.0,
             dial=False, step=False, raw=False,
             ignore_limits=False, confirm_move=False):
        """ moves motor drive to position

        arguments:
        ==========
         val            value to move to (float) [Must be provided]
         relative       move relative to current position    (T/F) [F]
         wait           whether to wait for move to complete (T/F) [F]
         dial           use dial coordinates                 (T/F) [F]
         raw            use raw coordinates                  (T/F) [F]
         step           use raw coordinates (backward compat)(T/F) [F]
         ignore_limits  try move without regard to limits    (T/F) [F]
         confirm_move   try to confirm that move has begun   (T/F) [F]
         timeout        max time for move to complete (in seconds) [300]

        return values:
          -13 : invalid value (cannot convert to float).  Move not attempted.
          -12 : target value outside soft limits.         Move not attempted.
          -11 : drive PV is not connected:                Move not attempted.
           -8 : move started, but timed-out.
           -7 : move started, timed-out, but appears done.
           -5 : move started, unexpected return value from PV.put()
           -4 : move-with-wait finished, soft limit violation seen
           -3 : move-with-wait finished, hard limit violation seen
            0 : move-with-wait finish OK.
            0 : move-without-wait executed, not cpmfirmed
            1 : move-without-wait executed, move confirmed 
            3 : move-without-wait finished, hard limit violation seen
            4 : move-without-wait finished, soft limit violation seen

        """
        step = step or raw

        NONFLOAT, OUTSIDE_LIMITS, UNCONNECTED = -13, -12, -11
        TIMEOUT, TIMEOUT_BUTDONE              =  -8,  -7
        UNKNOWN_ERROR                         =  -5
        DONEW_SOFTLIM, DONEW_HARDLIM          =  -4, -3
        DONE_OK                               =   0
        MOVE_BEGUN, MOVE_BEGUN_CONFIRMED      =   0, 1
        NOWAIT_SOFTLIM, NOWAIT_HARDLIM        =   4, 3
        try:
            val = float(val)
        except TypeError:
            return NONFLOAT

        drv, rbv = ('VAL', 'RBV')
        if dial:
            drv, rbv = ('DVAL', 'DRBV')
        elif step:
            drv, rbv = ('RVAL', 'RRBV')

        if relative:
            val += self.get(drv)

        # Check for limit violations
        if not ignore_limits and not step:
            if not self.within_limits(val, dial=dial):
                return OUTSIDE_LIMITS

        stat = self.put(drv, val, wait=wait, timeout=timeout)
        if stat is None:
            return UNCONNECTED
        
        if wait and stat == -1: # move started, exceeded timeout
            if self.get('DMOV') == 0:
                return TIMEOUT
            return TIMEOUT_BUTDONE
        if 1 == stat:
            if wait:  # ... and finished OK
                if 1 == self.get('LVIO'):
                    return DONEW_SOFTLIM
                elif 1 == self.get('HLS') or 1 == self.get('LLS'):
                    return DONEW_HARDLIM
                return DONE_OK
            else:
                if 1 == self.get('LVIO') or confirm_move:
                    epics.ca.poll(evt=1.e-2)
                moving = False
                if confirm_move:
                    t0 = time.time()
                    while self.get('MOVN')==0:
                        epics.ca.poll(evt=1.e-3)
                        if time.time() - t0 > 0.25: break
                if 1 == self.get('MOVN'):
                    return MOVE_BEGUN_CONFIRMED
                elif 1 == self.get('LVIO'):
                    return NOWAIT_SOFTLIM
                elif 1 == self.get('HLS') or 1 == self.get('LLS'):
                    return NOWAIT_HARDLIM
                else:
                    return MOVE_BEGUN
        return UNKNOWN_ERROR


    def get_position(self, dial=False, readback=False, step=False, raw=False):
        """
        Returns the target or readback motor position in user, dial or step
        coordinates.
      
      Keywords:
         readback:
            Set readback=True to return the readback position in the
            desired coordinate system.  The default is to return the
            drive position of the motor.
            
         dial:
            Set dial=True to return the position in dial coordinates.
            The default is user coordinates.
            
         raw (or step):
            Set raw=True to return the raw position in steps.
            The default is user coordinates.

         Notes:
            The "raw" or "step" and "dial" keywords are mutually exclusive.
            The "readback" keyword can be used in user, dial or step 
            coordinates.
            
      Examples:
        m=epicsMotor('13BMD:m38')
        m.move(10)                   # Move to position 10 in user coordinates
        p=m.get_position(dial=True)  # Read the target position in dial coordinates
        p=m.get_position(readback=True, step=True) # Read the actual position in steps
        """
        pos, rbv = ('VAL','RBV')
        if dial:
            pos, rbv = ('DVAL', 'DRBV')
        elif step or raw:
            pos, rbv = ('RVAL', 'RRBV')
        if readback:
            pos = rbv
        return self.get(pos)
        
    def tweak(self, direction='foreward', wait=False, timeout=300.0):
        """ move the motor by the tweak_val
       
        takes optional args:
         direction    direction of motion (forward/reverse)  [forward]
                         must start with 'rev' or 'back' for a reverse tweak.
         wait         wait for move to complete before returning (T/F) [F]
         timeout      max time for move to complete (in seconds) [300]
        """
        
        ifield = 'TWF'
        if direction.startswith('rev') or direction.startswith('back'):
            ifield = 'TWR'
            
        stat = self.put(ifield, 1, wait=wait, timeout=timeout)
        ret = stat
        if stat == 1:
            ret = 0
        if stat == -2:
            ret = -1
        try:
            self.check_limits()
        except ImsLimitException:
            ret = -1
        return ret

        
    def set_position(self, position, dial=False, step=False, raw=False):
        """
      Sets the motor position in user, dial or step coordinates.
      
      Inputs:
         position:
            The new motor position
            
      Keywords:
         dial:
            Set dial=True to set the position in dial coordinates.
            The default is user coordinates.
            
         raw:
            Set raw=True to set the position in raw steps.
            The default is user coordinates.
            
      Notes:
         The 'raw' and 'dial' keywords are mutually exclusive.
         
      Examples:
         m=epicsMotor('13BMD:m38')
         m.set_position(10, dial=True)   # Set the motor position to 10 in 
                                      # dial coordinates
         m.set_position(1000, raw=True) # Set the motor position to 1000 steps
         """

        # Put the motor in "SET" mode
        self.put('SET', 1)

        # determine which drive value to use
        drv = 'VAL'
        if dial:
            drv = 'DVAL'
        elif step or raw:
            drv = 'RVAL'

        self.put(drv, position)
        
        # Put the motor back in "Use" mode
        self.put('SET', 0)
      
    def get_pv(self, attr):
        """return  PV for a field.
        """
        return self.PV(attr)

    def clear_callback(self, attr='drive'):
        """clears callback for attribute.
        """
        try:
            index = self._callbacks.get(attr, None)
            if index is not None:
                self.PV(attr).remove_callback(index=index)
        except:
            self.PV(attr).clear_callbacks()

    def set_callback(self, attr='VAL', callback=None, kws=None):
        """define a callback for an attribute
        """
        self.get(attr)
        kw_args = {}
        kw_args['motor_field'] = attr
        if kws is not None:
            kw_args.update(kws)

        index = self.PV(attr).add_callback(callback=callback, **kw_args)
        self._callbacks[attr] = index

    def refresh(self):
        """Refresh all motor parameters currently in use:
        make sure all used attributes are up-to-date.
        """
        epics.ca.poll()

    def StopNow(self):
        """Stop motor as soon as possible.
        """
        self.stop()

    def stop(self):
        """Stop motor as soon as possible.
        """
        self.STOP = 1
            
#    def make_step_list(self, minstep=0.0, maxstep=None, decades=10):
#        """ create a reasonable list of motor steps, as for a dropdown menu
#        The list is based on motor range Mand precision"""
#
#        if maxstep is None:
#            maxstep = 0.6 * abs(self.HLM - self.LLM)
#        steplist = []
#        for i in range(decades):
#            for step in [j* 10**(i - self.PREC) for j in (1, 2, 5)]:
#                if (step <= maxstep and step > 0.98*minstep):
#                    steplist.append(step)
#        return steplist
        
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

    def show_log(self):
        """Show motor log.
        """
        epics.ca.poll()
        out = []
        out.append(repr(self))
        out.append("\n")
        out.append( "--------------------------------------")
        for attr in self._log_attrs:
            out.append(self.get(attr, as_string=True))
        out.append("--------------------------------------")
        epics.ca.write("\n".join(out))

    def show_cfg(self):
        """Show configuration file.
        """
        epics.ca.poll()
        out = []
#        out.append(repr(self))
        out.append( "--------------------------------------")
        out.append(self.get('CFG_FILE', as_string=True))
        out.append("--------------------------------------")
        epics.ca.write("\n".join(out))

    def write_all(self, fname, state=None):
        """Write all PVs to file.
           *** Obsolete -- use IMS motor record write ***
        """
        if state is None:
            state = self.save_state()
        out = ["#Device Saved State for %s, prefx='%s': %s\n" % (self.__class__.__name__,
                                                                 self._prefix, time.ctime())]
        for key in sorted(state.keys()):
            if (key in self._pvs):
                out.append("%s  %s\n" % (key, state[key]))
        fout = open(fname, 'w')
        fout.writelines(out)
        fout.close()

if (__name__ == '__main__'):
    for arg in sys.argv[1:]:
        m = Motor(arg)
        m.show_info()


