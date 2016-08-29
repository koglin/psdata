import subprocess
import re



def Search(*args,**kwargs):
    '''
    Parameters
    ----------
    Searches through all of the hosts in the netconfig database. Search
    constraints can be specified as arguements or keywords. If the term 
    is place as in args, the search will look through all of the
    available information for the host, while if specified as a keyword
    the search will only look through a specific entry in the netconfig
    data.

    Return: 
    ----------
    A dictionary of all the hosts that match the search

    Example
    --------
    feh_digis = Search('digi',location='B999')
    '''

    search_info = {}
   
    #Load NetConfig
    if not NetConfig._results:
        nc = NetConfig()

    #Search through hosts
    for host,host_info in NetConfig._results.items():
        info = host_info.values()
        #Create a dictionary of criteria and indicate their presence by True/False
        check_list = {}
        check_list = check_list.fromkeys(list(args)+kwargs.keys(),False)
     
        #Check if supplied args are present 
        for arg in args:
             #In case arguments are given as a single list
             if type(arg) ==list:
                 args=arg+args
                 continue
             for piece in info:
                 #When found set to ture
                 if arg.lower() in str(piece).lower() or arg.lower() in host.lower():
                     check_list[arg] = True
                     break
                 else:
                     continue

        #Check if supplied kwargs are present
        for kw,pattern in kwargs.items():
            try:
                #If found set to true
                if pattern in host_info[kw].lower():
                    check_list[kw] = True
            except KeyError:
                pass

        #If all criteria found in host entry add to returned dictinoary
        if all(check_list.values()):
            search_info[host] = host_info
      
    return search_info    


def Location_Parser(string):
    '''
    A parser built to extract location information from 
    NetConfig strings
    '''

    _parsed_info = {}

    #words to look for that indicate rack_height
    _height_conditions = ['elevation','height','pwr','ser']
    #Find which delimeters in the string to help split info
    delims = Find_Delimeters(string)
    #Split string by found delimeters and search for rack_info
    for d in delims:
        raw_info = string.split(d)
        for index,piece in enumerate(raw_info):
           
            if piece.lower()[0]=='b' and piece[1:].isdigit():
                _parsed_info['building'] = piece 
   
            if piece[0].lower()=='r':
                if piece[1:].isdigit() or piece[1:-1].isdigit():
                    _parsed_info['rack'] = piece.upper()
       
            if piece[0].lower()=='e' and piece[1:].isdigit():
                _parsed_info['rack_height'] = int(piece[1:])
   
            if piece.lower() == 'rack':
                rack = raw_info[index+1]
                if rack.isdigit() or rack[:-1].isdigit():
                    _parsed_info['rack'] = 'R{:}'.format(raw_info[index+1])
    
            if piece.lower() in _height_conditions:
                if raw_info[index+1].isdigit():
                    _parsed_info['rack_height'] = int(raw_info[index+1].strip())   
    return _parsed_info


def get_aliases(list):
    '''
    Create aliases for host names to be displayed
    '''
    dict = {}
   
    for host in list:
        key=host.replace('-','_') 
        dict[key]=host
   
    return dict


def Find_Delimeters(string):
    '''
    Find which of delimeters from list are present in string
    in order to help with parsing
    '''
    
    _delimeters = [' ',':','-']
    _found_delim = []

    for delim in _delimeters:
        if delim in string:
            _found_delim.append(delim)
    
    return _found_delim


class NetConfig(object):
    '''
    The overarching class to encompass all of the data gathered from 
    NetConfig. All of the hosts found from the search are a stored in 
    the dicitionary NetConfig._results
    '''
    _results = {}
    _aliases = {}
    _search_keys = ['subnet']
    _hutches =  {'1':'AMO','2':'SXR','3':'XPP','4':'XCS','5':'CXI','6':'MEC'}

    def __init__(self):
        #Scrape information from NetConfig
        self._run_netconfig()
        #Parse to find additional info
        self._parse_for_locations()
        #Eliminate impossible/wrongly parsed data
        self._clean_parsed_info()
        #Associate hosts-ipmi and host-ib with parent
        self._find_nested_hosts()
        #Create aliases for display
        self._aliases.update(get_aliases(self._results.keys()))

    
    def _run_netconfig(self):
        '''
        Run a netconfig search and store information to Netconfig._results
        '''

        search_string = ['netconfig','search','*']

        try:
            raw_netconfig_info = subprocess.check_output(search_string)
            self._results.update(self._parse_netconfig(raw_netconfig_info))
   
        except subprocess.CalledProcessError as e:
            print 'Improper search'
            print e

    def _parse_netconfig(self,raw_nc_info):
        '''
        A first levelparsing algorithm for the output of netconfig search *
        Designed to take raw return of netconfig search and sort into a 
        dictionary
        '''
        nc_info={}

        hosts = re.split('\n\n',raw_nc_info)
        
        for host in hosts:
            lines= host.splitlines()[:-1]  
            i = 0
            #Iterate through lines
            while i < len(lines):

                #Grab host name
                if '\t' not in lines[i]:
                    host_name=lines[i].rstrip().strip(':')
                    if host_name:
                        nc_info[host_name]= {'name':host_name}
                
                #If not a hostname find a key value pair        
                elif '\t' in lines[i] and ':' in lines[i]:
                    key,value = lines[i].split(':',1)
                    #If key value pair found, enter in dictionary
                    if value:
                       nc_info[host_name][key.strip('\t').lower().replace(' ','_')] = value[1:]

                #If key,value pair split between lines, associate with each other
                elif ';' in lines[i]:
                    key = lines[i-1][:-1].strip('\t').lower().replace(' ','_')
                    value = lines[i].replace(';','').strip()
                    nc_info[host_name][key] = value

                #Move to next line
                i+=1

        return nc_info


    def _parse_for_locations(self):
        '''
        Look through netconfig information and identify hutch names
        '''
        
        #Netconfig fields to look for hutch information
        _hutch_search_locations = ['subnet','aliases','name']

        #Netconfig fields to look for rack,rack height and building information
        _location_keywords = ['cnames','aliases','location','name','description']
        

        for host, info in self._results.items():
            #Find Hutch Information
            
            _possible_hutch = []

            #Look for each hutch
            for hutch in self._hutches.values():
                #in each search location
                for search_loc in _hutch_search_locations:
                    
                    try:
                        
                        if hutch.lower() in info.get(search_loc).lower():
                            _possible_hutch.append(hutch)
                    except:
                        pass

            #If more than one hutch is found for an object, don't enter it
            if len(set(_possible_hutch)) > 1:
                pass

            #Ammend found hutch information to database
            elif _possible_hutch:
                info['hutch'] = _possible_hutch[0] 


            #Find location information
            
            _searchable_info = []
           
            #Create list of all phrases from relevant Netconfig fields
            for ky in _location_keywords:

                try:
                    string = info.get(ky)

                    
                    if ',' in string:
                        _searchable_info.extend(string.split(','))
                    
                    else:
                        _searchable_info.append(string)
                except:
                    pass
            
            #Parse each item in list for new location information
            for s in _searchable_info:
               
                try:
                    #If found ammend to database
                    loc_info = Location_Parser(s.lstrip())
                    info.update(loc_info)
                
                except Exception as e:
                    pass

   
    def _find_nested_hosts(self):
        '''
        Gather all devices with -ipmi and -ib suffixes and look
        to see if their parent host has location information
        '''
        #Keywords to indicate a host with a parent
        _nested_keywords = ['-ipmi','-ib']

        for host,info in self._results.items():
            for key in _nested_keywords:
       
                #See if host has a parent
                cut_size = len(key)
                if key in host:
                    parent = host[:-cut_size]
                    
                    #Look at parent to find location info
                    try:
                        parent_info = self._results[parent]

                        #If found edit location information for host
                        if parent_info.get('rack'):
                            info['rack'] = parent_info.get('rack')
                   
                        if parent_info.get('rack_height'):
                            info['rack_height'] = parent_info.get('rack_height')
                
                    except Exception as e:
                        pass

    
    def _clean_parsed_info(self):
       '''
       Check information to find any glaring illogical location
       entries
       '''
        
       for host,info in self._results.items():
           if info.get('rack_height') >48.0:
               info['rack_height'] = None

    
    def search(self,*args,**kwargs):
        '''
        Parameters
        ----------
        Searches through all of the hosts in the netconfig database. Search
        constraints can be specified as arguements or keywords. If the term 
        is place as in args, the search will look through all of the
        available information for the host, while if specified as a keyword
        the search will only look through a specific entry in the netconfig
        data.
    
        Return: 
        ----------
        A Host Group object filled with hosts meeting search conditions
    
        Example
        --------
        feh_digis = Search('digi',location='B999')
        '''
        return Host_Group(*args,**kwargs)

    def __dir__(self):
        all_attrs=set(self._hutches.values()+self._search_keys+self.__dict__.keys())
        return list(sorted(all_attrs))

    def __getattr__(self,attr):
        
        if attr=='subnet':
            return Subnets()
      
        if attr in self._hutches.values():
            return Host_Group(hutch=attr)

        if attr in self._aliases.keys():
            return Host(self._aliases[attr])

        if attr in self._results.keys():
            return Host(attr)


class Subnets(object):
    '''
    A class to organize the NetConfig information by subnets
    '''
    def __init__(self):
 
        if not NetConfig._results:
            nc = NetConfig()
   
        self._subnet_list = self._get_subnet_list()
        self._aliases = get_aliases(self._subnet_list)
  

    def _get_subnet_list(self):
        '''
        Gather a list of all the subnets listed in NetConfig
        '''

        subnet_list = []

        for host,info in NetConfig._results.items():
            #If host has a subnet listed, add it to the list 
            try:
                subnet_list.append(info['subnet'][:-6])  
         
            except KeyError:
                continue    
        
        #Return list with duplicate subnets removed
        return list(set(subnet_list))

   
    def __dir__(self):
        
        all_attrs = set(self._aliases.keys()+self.__dict__.keys())
        return list(sorted(all_attrs))

    
    def __getattr__(self,attr):

        if attr in self._aliases.keys():
            return Host_Group(subnet=self._aliases[attr])

        if attr in self._subnet_list:
            return Host_Group(subnet=attr)


class Host_Group(object):
    '''
    A subgroup of the hosts found in NetConfig. This is usually initialized
    by a netconfig.search call. 
    '''
  
    #Attributes to be shown when the show_group_info function is called
    _show_attrs = ['name','description','subnet','ethernet_address','ip']  


    def __init__(self,*args,**kwargs):
      
        self._hosts=Search(*args,**kwargs)
        self._aliases=get_aliases(self._hosts.keys())




    def show_group_info(self):
        '''
        A function to print the information for each host in the group.
        Shown attributes are determined by Host_Group._show_attrs
        '''

        #The Header
        print '\n{:30} {:40} {:20} {:20} {:20}'.format(*self._show_attrs)
        print '-'*150
        #Host information printed alphabetically
        sorted_keys = list(sorted(self._hosts.keys()))
        for host in sorted_keys:
            info = []
            
            for attr in self._show_attrs:
                
                try:
                    piece = self._hosts[host][attr]
                    
                    if len(piece)>35:
                        piece = piece[:40]
                    
                    info.append(piece)             
                #If field is not present in dictionary say "Not Available"
                except:
                    info.append('Not Available') 
        
            #Print host information
            print '{:30} {:40} {:20} {:20} {:20}'.format(*info)


    
    def __dir__(self):
      
        all_attrs=set(self._aliases.keys()+self.__dict__.keys())
        return list(sorted(all_attrs))

    
    def __getattr__(self,attr):

        if attr in self._aliases.keys():
            return Host(self._aliases[attr])

        if attr in self._hosts.keys():
            return Host(attr)



class Host(object):
    '''
    A class for a individual host in NetConfig
    '''

    def __init__(self,host_name):
        self.name = host_name
        self._info = NetConfig._results[host_name]


    def show_host_info(self):
        '''
        Display the host information
        '''

        sorted_keys = list(sorted(self._info.keys()))
        #Header
        print '\nInformation for {:}'.format(self.name)
        print '-'*80
        #Print information in alphabetical order
        for key in sorted_keys:
            print '{:20}  {:30}'.format(key,str(self._info[key])) 


    def __repr__(self):
        self.show_host_info()

    def __dir__(self):
        all_attrs = set(self.__dict__.keys()+self._info.keys())
        return list(sorted(all_attrs))

    def __getattr__(self,attr):
   
        if attr in self._info.keys():
            return self._info.get(attr)
