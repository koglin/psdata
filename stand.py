import psdata

from math import sin,cos,tan,fabs
from collections import Counter

_params = {
        #Lift motor angle
        'alpha': 0.261799387,

        #Detector Displacement
        '_xd':  0,
        '_yd':  480.0346,
        '_zd': -914.5525,

        #Vee Displacement
        '_xvb':  342.9,
        '_yvb':  361.3404,
        '_zvb': -609.6508,

        #Flat Displacement
        '_xfb': -342.9,
        '_yfb':  361.3404,
        '_zfb': -609.6508,
    }

class Stand(psdata.Detector):
    """
    An object to represent the motors present on the DS1 and DS2 detector
    stands. Using the five external motor positions as well as the internal z
    motor, the detector has six degrees of freedom; cartesian coordinates as
    well as pitch, yaw and roll.
    """
#    vee_slide  = m5 = 'CXI:DS1:MMS:01' 
#    vee_lift   = m4 = 'CXI:DS1:MMS:02' 
#    flat_lift  = m3 = 'CXI:DS1:MMS:03' 
#    cone_slide = m2 = 'CXI:DS1:MMS:04' 
#    cone_lift  = m1 = 'CXI:DS1:MMS:05' 

    _mots = {'m1': 'cone_lift',
             'm2': 'cone_slide',
             'm3': 'flat_lift',
             'm4': 'vee_lift',
             'm5': 'vee_slide'}

    def __init__(self,*args,**kwargs):

        psdata.Detector.__init__(self,*args,**kwargs)

        self.set_parameter(**_params)
        self._init()

    def _init(self):
        print 'init'
        self._detrest = StandPoint(self._xd,self._yd,self._zd)
        self._vee     = StandPoint(self._xvb,self._yvb,self._zvb)
        self._flat    = StandPoint(self._xfb,self._yfb,self._zfb)
         
        self.pitch = 0
        self.yaw   = 0 
        self.roll  = 0
        self.find_angles(verbose=False)

    @property
    def cone_x(self):
        return self.cone_lift.RBV*cos(self.alpha)+self.cone_slide.RBV
    
    @property
    def cone_y(self):
        return self.cone_lift.RBV*sin(self.alpha)

    def detectorPosition(self):
        """
        Return the current position of the detector in stand coordinates.
        """
        x,y,z = self._detrest.room_position(self.cone_x,self.cone_y,self.pitch,
                                                     self.yaw,self.roll)
        z += self.z.VAL
        return {'x':x,'y':y,'z':z}

    def estimate_room_coordinates(self,dPitch=0.0,dYaw=0.0,dRoll=0.0,verbose=True):
        """
        Estimate the room coordinates of the cone, vee and flat joints based on
        a set of angles. By default, the coordinates are computed for the current
        position and angles, but a relative change in angle can be entered as well.
        
        Parameters
        ===========
            dpitch  : Estimate based on a changed pitch value (float) [0.0]
            dyaw    : Estimate based on a changed yaw value (float) [0.0]
            droll   : Estimate based on a changed roll value (float) [0.0]
            verbose : Enable or disable print statements. (bool) [F]
        Returns
        ===========
            coords : A dictionary with each joint name and corresponding
                     estimated cartesian coordinates.
        """
        coords = {}
        if verbose:
            print 'Cone motor is located at x,y -> ({:},{:})'.format(self.cone_x,
                                                                     self.cone_y)
        for name,point in [('detector rear limit',self._detrest),
                           ('vee',self._vee),
                           ('flat',self._flat)]: 
            x,y,z = point.room_position(self.cone_x,self.cone_y,
                                        self.pitch+dPitch,self.yaw+dYaw,
                                        self.roll+dRoll
                                        )
            coords[name] = {'x':x,'y':y,'z':z}
            if verbose:
                print 'Estimated {:} position:'.format(name)
                print 'x={:} y={:} z={:}'.format(x,y,z)
        
        return coords

    def find_angles(self,precision=0.001,min_iterations=30,verbose=True):
        """
        Return the value of the pitch, yaw, and roll through an iterative
        process of comparing estimated angles and motor encoder readbacks.

        Parameters
        ===========
            precision      : The precision required for the estimated motor
                             positions. (float) [0.001]
            min_iterations : The minimum number of iterations before the 
                             function will exit. (int) [30]
            verbose        : Enable or disable print statements. (bool) [F]
        """

        crnt = {attr: getattr(self, m).VAL for attr, m in self._mots.items()}
        est = {}

        it = 0

        while True:
            
            if verbose:
                print 'Iteration {:}'.format(it)
            
            #Estimate motor positions based on current angle estimate
            #Compare difference and adjust angle estimate
            pos = self.estimate_room_coordinates(verbose=verbose)
            est['m3'] = (pos['flat']['y']-14.226*25.4)/sin(self.alpha)
            est['m4'] = (pos['vee']['y']-14.226*25.4)/sin(self.alpha)
            est['m5'] = pos['vee']['x']-13.5*25.4
             
            self.roll  += (est['m3']-crnt['m3']-(est['m4']-crnt['m4'])) \
                            /(3*(sin(self.alpha)+self._xvb-self._xfb))
            self.pitch += (est['m4']-crnt['m4']+est['m5']-crnt['m5'])/(3*self._zvb)
            self.yaw   += (est['m5']-crnt['m5'])/(-3*self._zvb)
            
            it+=1
            if verbose:
                print 'Inferring motor positions of: ({m3},{m4},{m4})'.format(**est)
                print 'While actual motor values are: ({m3},{m4},{m5})'.format(**crnt)
            #End iteration if loop and precision thresholds have been met
            if (it>min_iterations and precision > max([fabs(crnt['m3']-est['m3']),
                                                      fabs(crnt['m4']-est['m4']),
                                                      fabs(crnt['m5']-est['m5']),
                                                      ])):
                break

            #End iteration if twice the minimum number of loops 
            if it > 2*min_iterations:
                break
        
        if verbose:
            for angle,value in  (('pitch',self.pitch),
                                 ('yaw',self.yaw),
                                 ('roll',self.roll)):
                print 'Determined {:} to be {:} [rad]'.format(angle,value)

        return self.pitch,self.yaw,self.roll

    def translate(self,dx=0.0,dy=0.0,verbose=True,execute=False,from_angles=None):
        """
        Move stand by dx and dy from current position without changing the
        angle.

        Parameters
        ===========
            dx : The relative motion requested in x. (float)
            dy : The relative motion requested in y. (float)
            verbose : Enable/Disable print statements [True]
            execute : Determines whether the move is actually
                      processed.
            from_angles : A dictionary of pitch,yaw and roll that the stand is
                        assumed to be at before the translation. Useful for
                        planning motion without having to adjust the stand.
        Returns
        ==========
            If execute has been selected the function will return whether or
            not the move has been successfully executed. Otherwise, the change
            in position required from each motor to complete the requested
            translation is returned as a tuple.
        """
        dx,dy = float(dx),float(dy)

        if not from_angles:
            self.find_angles(verbose=False)
            orig_pitch,orig_yaw,orig_roll = self.pitch,self.yaw,self.roll

        else:
            orig_pitch,orig_yaw,orig_roll = (from_angles['pitch'],from_angles['yaw'],
                                             from_angles['roll'])
        
        if verbose:
            print 'Starting x,y -> ({:},{:})'.format(self.cone_x, self.cone_y)
        
        #Calculate motion
        mx = dx*cos(orig_yaw)*cos(orig_roll) + dy*sin(orig_roll)*cos(orig_yaw)
        my = ((sin(orig_pitch)*sin(orig_yaw)*cos(orig_roll) - sin(orig_roll)*cos(orig_pitch))*dx 
             + (sin(orig_pitch)*sin(orig_yaw)*sin(orig_roll) + cos(orig_pitch)*cos(orig_roll))*dy)

        print 'mx = {:}, my = {:}, alpha = {:}'.format(mx, my, self.alpha)
        m1 = my/sin(self.alpha)
        #m2 = mx - my/tan(self.alpha) # This was Teddy's calc but cannot be right
        m2 = mx # This should be good enough
        m3 = dy/sin(self.alpha)
        m4 = dy/sin(self.alpha)
        m5 = dx

        move_dict = {'cone_lift':  m1,
                     'cone_slide': m2,
                     'flat_lift':  m3,
                     'vee_lift':   m4,
                     'vee_slide':  m5}

        if verbose:
            print '\nMoving motors the following distances:'
            for mtr, distance in move_dict.items():
                print '{:} to a final position of  {:} [mm]'.format(mtr,distance)

        #Execute
        if execute and not from_angles:
            #success = self.epicsLive.move(**move_dict, relative=True, wait=True)

            self.find_angles(verbose=False)
            if verbose:
                print '\nEnd Position:'
                print 'x = {:}, y = {:}'.format(self.cone_x, self.cone_y)
                print '\nResulting angles:'
                coords = self.estimate_room_coordinates(verbose=False)
                for angle,initial_value,end_value in [('pitch',orig_pitch,self.pitch),
                                                      ('yaw',orig_yaw,self.yaw),
                                                      ('roll',orig_roll,self.roll)
                                   ]:
                    print '{:} : Initial = {:} => Final ={:}'.format(angle,
                                                                     initial_value,
                                                                     end_value,
                                                                    )
            return success

        else:
            return move_dict

    def rotate(self,dPitch=0.0,dYaw=0.0,dRoll=0.0,verbose=True,execute=False):
        """
        Rotate the detector stand in pitch, yaw, or roll while keeping the
        back of the stand stationary.
        
        Parameters
        ===========
            dPitch  : Desired change in pitch angle. (float) [0.0]
            dYaw    : Desired change in yaw angle. (float) [0.0]
            dRoll   : Desired change in roll angle. (float) [0.0]
            verbose : Enable or disable print statements. (bool) [F]
        """
        self.find_angles(verbose=False)
        req_coords = self.estimate_room_coordinates(dPitch=dPitch,dYaw=dYaw,
                                                    dRoll=dRoll,verbose=False) 
        m3 = (req_coords['flat']['y']-14.226*25.4)/sin(self.alpha)
        m4 = (req_coords['vee']['y']-14.226*25.4)/sin(self.alpha)
        m5 = (req_coords['vee']['x']-13.5*25.4)
        
        move_dict = {'flat_lift':  m3,
                     'vee_lift':   m4,
                     'vee_slide':  m5}
        
        if verbose:
            print '\nMoving motors to the following positions:'
            for mtr, distance in move_dict.items():
                print '{:} to a final position of  {:} [mm]'.format(mtr,distance)
            return move_dict
        
        success = True
        if execute:
            #success = self.epicsLive.move(**move_dict, wait=True)
            self.find_angles(verbose=False)
            return success
        else:
            return move_dict


    def align(self,fixed=0.0,dx=0,dy=0,mobile=None,retries=2,verbose=True,execute=False):
        """
        Move a point on the Z axis while keeping another fixed.

        Parameters
        ===========
            fixed    : The Z position to stay fixed in room
                       coordinates. (float)
            mobile   : The Z value to adjust. [Default = current z position] (float) 
            dx       : The amount to displace the mobile Z point 
                       by dx in X. (float) [0.0]
            dy       : The amount to displace the mobile Z point
                       by dy in Y (float) [0.0]
            retries  : Number of adjustment attempts to correct the 
                       final position. (int) [2]
            verbose  : Enable or disable print statements. (bool) [F]
        """
        
        if mobile is None:
            mobile = self.z.RBV

        #Find Initial Fixed Point
        fixed = float(fixed)
        mobile = float(mobile)
        
        crnt = {m: getattr(self, m).VAL for attr, m in self._mots.items()}
        fixedPoint = StandPoint(self._xd,self._yd,self._zd-fixed)
        int_coords = fixedPoint.room_position(self.cone_x,self.cone_y,
                                              self.pitch,self.yaw,
                                              self.roll
                                             )
                
        #Small angle approximate change in Angles
        dPitch = float(dy)/(mobile-fixed)
        dYaw   = float(dx)/(fixed-mobile)

        if verbose:
            print 'Changing Pitch angle by {:}.'.format(dPitch)
            print 'Changing Yaw angle by {:}'.format(dYaw)
        
        rot_dict = self.rotate(dPitch=dPitch,dYaw=dYaw,
                                verbose=verbose,execute=False)
        #Find fixed position in room coordinates after rotation.
        cone_x = float(self.cone_x)
        cone_y = float(self.cone_y)
        
        #Adjust fixed position 
        its = 0
        
        while its < retries:
            its +=1
            final_coords = fixedPoint.room_position(cone_x, cone_y,
                                                    self.pitch+dPitch,
                                                    self.yaw+dYaw,
                                                    self.roll)
            #Calculate change in position
            dx   = final_coords[0]-int_coords[0]
            dy   = final_coords[1]-int_coords[1]
            dz   = final_coords[2]-int_coords[2]

            if verbose:
                print '\nFixed point has travelled (x,y,z) : {:},{:},{:}'.format(dx,dy,dz)
                print 'Attempting to adjust.'
            
            #Small angle approximate neccesary translate
            xslope =  ((self.yaw+dYaw)+(self.pitch+dPitch)*self.roll)*dz
            yslope = -((self.pitch+dPitch)+(self.yaw+dYaw)*self.roll)*dz

            print 'dx, dy, dz', dx, dy, dz
            print 'x/y slope', xslope, yslope
            trans_dict = self.translate(-dx+xslope,-dy+yslope,
                                        verbose=verbose,execute=False,
                                        from_angles = {'pitch':self.pitch+dPitch,
                                                        'yaw':self.yaw+dYaw,
                                                        'roll':self.roll})
            mot_dict = trans_dict.copy()
            mot_dict['cone_lift'] += crnt['cone_lift']
            mot_dict['cone_slide'] += crnt['cone_slide']
            mot_dict['flat_lift'] += rot_dict['flat_lift']
            mot_dict['vee_lift'] += rot_dict['vee_lift']
            mot_dict['vee_slide'] += rot_dict['vee_slide']
            
            print 'crnt ', crnt
            print 'rot  ', rot_dict
            print 'trans', trans_dict
            print 'mot  ', mot_dict
            m1 = mot_dict.get('cone_lift',0.)
            m2 = mot_dict.get('cone_slide',0.)
            cone_x = m1*cos(self.alpha)+m2
            cone_y = m1*sin(self.alpha)
            
            if verbose:
                print '\nClosest motors set to realignment is:'
                for mtr, distance in mot_dict.items():
                    print '{:} to a final position of  {:} [mm]'.format(mtr,distance)
        
        if execute:
            #result = self.epicsLive.move(**mot_dict, wait=True)
            self.find_angles()
            return result
        
        else:
            return mot_dict


class StandPoint(object):

    def __init__(self,x0,y0,z0):
        self.x0 = x0
        self.y0 = y0
        self.z0 = z0

    def stand_position(self,cone_x,cone_y):
        """
        Return the x,y,z  position relative to the stand based on the current cone
        position.
        """
        return cone_x+self.x0,cone_y+self.y0,self.z0


    def room_x(self,cone_x,cone_y,ax,ay,az):
        """
        Return the room x position based on the x,y position of the cone and
        the pitch,yaw, and roll of the stand.
        """
        x,y,z = self.stand_position(cone_x,cone_y)
        return (x*cos(ay)*cos(az) 
                + (sin(ay)*cos(ax)*cos(az)+sin(ax)*sin(az))*z
                + (sin(ax)*sin(ay)*cos(az)-sin(az)*cos(ax))*y)


    def room_y(self,cone_x,cone_y,ax,ay,az):
        """
        Return the room x position based on the x,y position of the cone and
        the pitch,yaw, and roll of the stand.
        """
        x,y,z = self.stand_position(cone_x,cone_y)
        return (x*sin(az)*cos(ay) 
                + (sin(ay)*cos(ax)*sin(az)-sin(ax)*cos(az))*z
                + (sin(ax)*sin(ay)*sin(az)+cos(az)*cos(ax))*y)
    
    def room_z(self,cone_x,cone_y,ax,ay,az):
        """
        Return the room x position based on the x,y position of the cone and
        the pitch,yaw, and roll of the stand.
        """
        x,y,z = self.stand_position(cone_x,cone_y)
        return (y*sin(ax)*cos(ay)
                +z*cos(ax)*cos(ay)
                -x*sin(ay))


    def room_position(self,cone_x,cone_y,ax,ay,az):
        """
        Return the room x,y,z  position based on the x,y position of the cone and
        the pitch,yaw, and roll of the stand.
        """
        return (self.room_x(cone_x,cone_y,ax,ay,az),
               self.room_y(cone_x,cone_y,ax,ay,az),
               self.room_z(cone_x,cone_y,ax,ay,az))
