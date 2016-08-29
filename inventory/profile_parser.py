import json

def find_delimeters(string):
    '''
    Find delimeters in string to aid in parsing
    '''

    possible = [',','-',' ',':']
    found = []
    for delim in possible:
        if delim in string:
            found.append(delim)
    return found


def _decode_dict(data):
    '''
    Converts unicode keys and values loaded by JSON
    into python types
    '''

    rv = {}

    for key,value in data.iteritems():
        #key to string    
        if isinstance(key,unicode):
            key = key.encode('utf-8')
        #value to string
        if isinstance(value,unicode):
            value = value.encode('utf-8')
            #See if it could be a int
            try:
                value = int(value)

            except:
                #See if it could be a float
                try:
                    value = float(value)

                except:
                    pass

        #Accounts for nested dictionaries
        elif isinstance(value,dict):
            value = _decode_dict(value)

        rv[key] = value

    return rv




class Rack_Profile_Reader(object):
    
    '''
    A reader to convert tsv rack profiles into a python dictionary. The parser 
    looks specifically for abbreviation codes with their rack height for
    instance: MCN-15,SER-04. The code determines whether this was found 
    on either the front or the back of the rack. It also uses information 
    from Confluence to fill in information about the device itself.
    This is dependant on a json object whose path must be specified
    as Rack_Profile_Reader._mnemonics.

    Attributes
    -----------
    The Reader accepts a list of file path to tsv files containing rack
    information. The parser depends on the file name to determine the building
    and rack number

    rp = Rack_Profile_Reader(['B999-R56.tsv','B950S-64.tsv'])
    
    Returns
    -------
    
    Rack_Profile_Reader.racks

    A nested dictionary with a list of racks as the first set of keys, each
    containing the devices and information within subdictionaries
    '''


    _mnemonics = '/reg/neh/home3/trendahl/Python_Scripts/NetConfig_Scripts/bin/mnemonics.json'
    _acronyms = {}
    racks = {}

    def __init__(self,file_list):
        self._acronyms.update(json.load(open(self._mnemonics,'r'),object_hook = _decode_dict))
        self._files = file_list

        for file in self._files:
            # Read tsv files
            if file.endswith('.tsv'):
                print file    
                try:
                    rack,building, devices = self._read_tsv(file)
                
                except Exception as e:
                    print 'Failed to read {:}'.format(file)
                    print e
                    continue

                #Format found rack name
                if rack[0] != 'R':
                    rack = 'R' +rack
                #Add information to dictionary
                self.racks[rack] = {'building':building, 'devices':devices}
  
  
  
    def _read_tsv(self,file):
        '''
        A protocol to read in tsv rack profile
        '''

        f = open(file)
        devices = {}
        #Determine building and rack name
        building,rack = file.split('-')

        #Iterate through lines
        for i,line in enumerate(f):
            
            try:
                devices.update(self._parse_row(line))
            
            except Exception as e:
                    pass
        
        #If no information is found 
        if not devices:
            print 'No devices found in file {:}'.format(file)
            return

        #Return found information
        return rack.rstrip('.tsv'),building.rstrip('S'), devices



    def _parse_row(self,line):
        '''
        A parser for each row in the tsv document. 
        '''

        #Split data into a list
        line_data = map(str.strip,line.split('\t')) 
        index = line_data[0]
        
        #Find device abbreviations
        device_info = self._find_abrv(line_data)

        #Determine whether the device was found
        #on the front or the back 
        for device in device_info.keys():
            orientation = 'front'
            
            for piece in line_data[1:]:
                
                if device in piece:
                    break
                
                if piece == index:
                    orientation = 'back'
                    break

            device_info[device]['orientation'] = orientation



        return device_info
    


    def _find_abrv(self,list):
        '''
        Find abbreviations within a list of strings
        '''

        device_info = {}
 
        
        for item in list:
            delims = find_delimeters(item)

            #If additional delimeters split up string and add to end of the list
            if delims:
                for delim in delims:
                    list.extend(item.split(delim))

            #If abbreviation found add it to dictionary along with
            #associated confluence information
            if len(item.rstrip('A').rstrip('B'))==6 and item[3] == '-':
                device_abrv = item
                elevation = int(item[4:6])
                device_info[device_abrv] = {'rack_height':elevation}

                confluence_info = self._acronyms.get(device_abrv[:3])
                device_info[device_abrv].update(confluence_info)

        return device_info






#def load_acronyms():
#    acronyms = {}
#    file = '/reg/neh/home3/trendahl/Python_Scripts/NetConfig_Scripts/LCLS_Naming_Convention.txt'
#    f = open(file,'r')
#
#    for line in f:
#        abrv, info = line.split('\t')
#        acronyms[abrv] = {} 
#        for pair in info.split('$'):
#            try:
#                key, value = pair[1:-2].split(',',1)
#                acronyms[abrv][key.replace("'",'')] = value.replace("'",'').lstrip()
#            except Exception as e:
#                print pair 
#                print e
#                pass 
#
#
#    return acronyms
            




