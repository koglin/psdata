import subprocess
import os
import pprint

from netconfig import NetConfig
from netconfig import Host 
from profile_parser import Rack_Profile_Reader
from plc_parser import PLC_Reader,PLC


class Rack_List(object):

    '''
    A class to gather information for all the racks inside LCLS. The information
    is pulled from both NetConfig and a cached versions of old rack profiles.
    Because the cached versions maybe less accurate the NetConfig information
    is automatically included, while the old profiles are added in only
    with the function Rack_List._include_old_profiles. 
    '''
    
    racks = {}
    _hutches =  {'1':'AMO','2':'SXR','3':'XPP','4':'XCS','5':'CXI','6':'MEC'}
    _buildings = ['B950','B999','B960']
    _db = '/reg/neh/home3/trendahl/Python_Scripts/NetConfig_Scripts/bin/cached_racks'

    def __init__(self):

        if not NetConfig._results:
            nc = NetConfig()

        if not self.racks:
            self._generate_rack_information()      
            self._include_old_profiles()
            self._include_plc_info()

    def _generate_rack_information(self):
        '''
        Load information from the Netconfig database with both a rack number and height
        and then organize
        '''

        for host,info in NetConfig._results.items():
            (bldg,hutch,rack,rack_height) = (info.get('building'),info.get('hutch'),info.get('rack'),info.get('rack_height'))
            #If host has rack and rack_height in dictionary
            if rack and rack_height:
           
                #Add rack if not there
                if rack not in self.racks.keys():
                    self.add_rack(rack)

                #Edit rack info if available
                if bldg:
                    self.racks[rack].rack_info['building'] = bldg
               
                if hutch:
                    self.racks[rack].rack_info['hutch'] = hutch


                #Add device to rack
                self.racks[rack].add_device(host,device_desc = info, source='NetConfig')


    def _include_plc_info(self):

        plc = PLC_Reader()
        self._plc_info = PLC_Reader._plc_info
    
    def _include_old_profiles(self):
        '''
        Loads all of the information in the cached rack profiles into the rack
        profiles. The function searchs the path specified by Rack_List._db
        for all availabe .tsv documents. The abreviation conversion ensures
        that duplicate of objects are not added if they are present in both 
        the rack profile and the NetConfig database
        '''

        _abrv_conversion = {'SER':'digi','PWR':'power','IOC':'ioc','DAQ':'daq'}


        #Use Rack_Profile Reader to gather information
        if not Rack_Profile_Reader.racks:

            dir = os.getcwd()
            os.chdir(self._db)
            profiles = subprocess.check_output('ls').split('\n')

            rp = Rack_Profile_Reader(profiles)
            os.chdir(dir)

        
        #Iterate through each rack found by the profile reader
        for p_rack_name,p_rack_info in Rack_Profile_Reader.racks.items():
            #Check to see if the rack included in our profile
            if p_rack_name in self.racks.keys():

                rack = self.racks[p_rack_name]
                #Iterate through devices found by profile reader
                for device,device_info in p_rack_info.get('devices').items():

                    #Locate the abbreviation/type of device and height in rack
                    type = device[:3]
                    h = device_info['rack_height']

                    #If the row is empty add the device
                    if rack._profile.get(h) == 'Empty':
                        rack.add_device(device,device_desc=device_info,source='Dated Rack Profile')
                    
                    else:
                        #If the row is not empty, check to see if the device currently in the row
                        #is a duplicate of the one found by the profile reader
                        if type in _abrv_conversion.keys():
                            full_name = _abrv_conversion.get(type)
                            row_devices =  rack._profile.get(h)

                            #If it is a duplicate, indicate whether the cached version indicated
                            #that the device was found on the front or back of the rack
                            duplicate = False
                            for dev in row_devices:
                                if full_name in dev:
                                    rack.devices[dev]['orientation'] = device_info['orientation']
                                    duplicate = True
                            #If it is not a duplicate add the device
                            if not duplicate:
                                rack.add_device(device,device_desc=device_info,source='Dated Rack Profile')

                        #If their is not a conversion from abbreviation type to NetConfig entry, add device
                        else:
                            rack.add_device(device,device_desc=device_info,source='Dated Rack Profile')
                   
            #If the rack is not currently in the profile add it, along with the devices found by the the
            #profile reader
            else:
                self.add_rack(p_rack_name,bldg =p_rack_info['building'])
                for device, device_info in p_rack_info.get('devices').items():
                    self.racks.get(p_rack_name).add_device(device,device_desc = device_info, source ='Dated Rack Profile')    
                
       



    def add_rack(self,name,hutch=None,bldg=None):
        '''
        Add rack to profile, building and hutch location
        not required
        '''
        self.racks[name] = Rack(name,hutch=hutch,bldg=bldg)
   
   
    def __dir__(self):
        all_attrs = set(self.__dict__.keys()+self._hutches.values()+self._buildings)
        return sorted(list(all_attrs))
   
    def __getattr__(self,attr):
        if attr in self.racks.keys():
            return self.racks[attr]
      
        if attr in self._hutches.values():
            return Rack_Group(hutch=attr)

        if attr in self._buildings:
            return Rack_Group(building=attr)




class Rack_Group(object):
    '''
    A subset of the entire Rack List. The smaller group is assembled
    either by a hutch location or building indicated by a keyword. 
    Hutch names are determined by their acronym and buildings by 
    a "B" followed by their three digit nomination.
    '''


    def __init__(self,**kwargs):
        self._racks = {}

        for name,rack in Rack_List.racks.items():
         
         
            if kwargs.get('hutch') and rack.rack_info.get('hutch')==kwargs.get('hutch'):
                self._racks[name]=rack

            if kwargs.get('building') and rack.rack_info.get('building')==kwargs.get('building'):
                self._racks[name] = rack

   
    def create_rack_profile(self):
        '''
        Print out rack profiles for all rack in the group
        '''

        for rack in self._racks.values():
            rack.show_profile()

    def __dir__(self):
        all_attrs = set(self.__dict__.keys()+self._racks.keys())
        return sorted(list(all_attrs))


    def __getattr__(self,attr):
        if attr in self._racks.keys():
            return self._racks.get(attr)         


class Rack(object):
    '''
    The class to represent an individual rack. By default, the rack
    is assumed to have 48 rows. The contained Rack.devices are stored in
    two seperate ways, devices, a dictionary with each devices' information
    displayed in a subdictionary. The second, Rack._profile, a database which
    organizes the devices by their elevation determined by rack_height 
    '''
    _height = 48

    def __init__(self,name,bldg=None,hutch=None):
        self.rack_info = {'name':name,'building':bldg,'hutch':bldg}
        self.plc_info = {}
        self.devices = {}
        self._aliases = {}
        self._profile = {}
        self._profile = self._profile.fromkeys(range(self._height,0,-1),'Empty')
        self._find_available_plc()


    def add_device(self,device_name,device_desc, source = 'Unknown'):
        '''
        Adds device into both the devices and profile dictionary

        Parameters
         ----------
        device_name  type:string
        The name of the device being entered

        device_desc type:dictionary
        This contains all the information on the device, this is
        either taken from confluence or NetConfig. Must include
        an integer at device_desc['rack_height']. If the device
        is known to be either on the front or back of the rack
        it can be indicated as device_desc['orientation']. If
        this is not specified upon entry, the device is assumed
        to be in the front of the rack

        source type:string
        The source the information was gathered from
        '''

        h = int(device_desc['rack_height'])

        self.devices[device_name] = device_desc
        self.devices[device_name]['source'] = str(source)
        
        #If front or back is not indicated, place in front
        if not device_desc.get('orientation'):
            self.devices[device_name]['orientation'] = 'front'

        
        #Create aliases to use as displayed dictionary keys
        alias = device_name.replace('-','_').replace(' ','_')
        self._aliases[alias] = device_name

        #If the spot is empty add
        if self._profile.get(h) =='Empty':
            self._profile[h] = [device_name]

        #If the spot is filled simply append to row
        else:
            self._profile[h].append(device_name)
      
    def show_profile(self):
        '''
        Prints a makeshift rack profile from the profile dictionary
        '''

        print '\n######***{:}***######'.format(self.name)
        for h in range(self._height,0,-1):
            #Empty Line
            if self._profile[h] == 'Empty':
                print '{:}-------------------'.format(h)
            else:
                row_devices = []
                for device in self._profile[h]:
                    #Find devices on row
                    device_info = self.devices[device]
                    #If the device name is an abbreviation, the component
                    #entry is displayed instead
                    if device_info.get('Component'):
                        row_devices.append(device_info.get('Component'))
                    else:
                        row_devices.append(device)

                print '{:}  {:}'.format(h,','.join(row_devices))





    def _find_available_plc(self):
        
        for device in self.devices.keys():
            if 'DRL' in device:
                tolerance = [0,-1,1]
                num = int(device[-2:])

                for range in tolerance:
                    name = '{:}_{:}_{:}'.format(self.rack_info['name'],'DRL',str(num+range).zfill(2))
                    if name in PLC_Reader._plc_info.keys():
                        self.plc_info[device] = PLC_Reader._plc_info[name]
                        self.plc_info[device].update({'name':name})

    def __dir__(self):
        all_attrs = set(self.__dict__.keys()+self._aliases.keys()+self.rack_info.keys())
        return sorted(list(all_attrs))

    def __getattr__(self,attr):
        if attr in self.rack_info.keys():
            return self.rack_info.get(attr)

        if attr in self._aliases.keys():
            device = self._aliases.get(attr)
            source = self.devices[device]['source']
            
            if source == 'NetConfig':
                return Host(device)

            elif device in self.plc_info.keys():
                return PLC(self.plc_info[device]['name']) 

            elif source == 'Dated Rack Profile':
                return Device(self.devices[device])



class Device(object):

    def __init__(self,device_dictionary):

        self.device_info = device_dictionary

    def show_info(self):
        
        pprint.pprint(self.device_info)

    def __dir__(self):
        all_attrs = set(self.__dict__.keys()+self.device_info.keys())
        return list(sorted(all_attrs))

    def __getattr__(self,attr):
        
        if attr in self.device_info.keys():
            return self.device_info.get(attr)

    def __repr__(self):
        self.show_info()

