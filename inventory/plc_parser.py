import subprocess
import os


class PLC_Reader(object):

    _db = '/reg/neh/home/trendahl/Python_Scripts/NetConfig_Scripts/bin/cached_plc'

    _plc_info = {}

    def __init__(self):
        wd = os.getcwd()
        print wd
        os.chdir(self._db)
        self.files = self._find_plc_cache()

        for file in self.files:
            if file:
                self._parse_plc_file(file)
        
        os.chdir(wd)

    def _find_plc_cache(self):
        files = subprocess.check_output(['ls']).split('\n')
        return files


    def _parse_plc_file(self,file):
        #Currently only inputs
        
        f = open(file,'r')
        spreadsheet = f.read().split('\n')
        #Read file line by line
        for i,line in enumerate(spreadsheet):
            line_info = line.split('\t')
            #Find the header
            if i == 0:

                attrs = self._parse_header(line_info)
            #Read each row
            else:
                #Stop at end of inputs
                if line_info[0] == 'OUTPUTS':
                    break

                #If line isn't empty
                elif line_info[1:3] != ['','']:
                    device = {}
                    #Take info and sort into header columns
                    for i,field in enumerate(line_info):
                        if i >= len(attrs):
                            pass
                        elif field:
                            device[attrs[i]]=field.replace(' ','_').replace('-','_')
                 
                    #Organize new information into plc_dictionary 
                    if not device.get('destination_drl') or not device.get('trunk'):
                        continue
                    
                    else:
                        drl = device['destination_drl']
                        trunk = device['trunk']

                        if not self._plc_info.get(drl):
                            self._plc_info[drl] = {}

                        if not self._plc_info[drl].get(trunk):
                            self._plc_info[drl][trunk] = {}

                        self._plc_info[drl][trunk].update({device['pv_names']:device})


    def _parse_header(self,line_list):
        keys = []
        for item in line_list:
            if item:
                keys.append(item.lower().replace(' ','_').replace('-','_'))
        
        return keys
    


    def __dir__(self):
        all_attrs = set(self._plc_info.keys()+self.__dict__.keys())
        return list(sorted(all_attrs))

    def __getattr__(self,attr):
        if attr in self._plc_info.keys():
            return PLC(attr)

class PLC(object):


        def __init__(self,name):

            self.name=name
            self._inputs = PLC_Reader._plc_info[name]

        def __dir__(self):
            all_attrs = set(self._inputs.keys()+self.__dict__.keys())
            return list(sorted(all_attrs))

        def __getattr__(self,attr):
            if attr in self._inputs.keys():
                return Trunk(self.name,attr)


class Trunk(object):

        def __init__(self,plc,name):
            self.plc = plc
            self.name = name
            self._devices = PLC_Reader._plc_info[self.plc][self.name]
            self._aliases = self._get_aliases()
        
        def _get_aliases(self):
            aliases = {}
            for key in self._devices.keys():
                alias = key.replace(':','_')
                aliases.update({alias:key})
            return aliases
        def __dir__(self):
            all_attrs = set(self._aliases.keys()+self.__dict__.keys())
            return list(sorted(all_attrs))

        def __getattr__(self,attr):
            if attr in self._devices.keys():
                return self._devices[attr]
            if attr in self._aliases.keys():
                return self._devices[self._aliases[attr]]


