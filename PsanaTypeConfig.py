#def EvrDataConfig(self):


def AliasConfig(self):
    """Expand detector aliases in AliasConfig.srcAlias list.
    """
    pass
#   {a.aliasName: a.src for a in  cxi.configStore.Alias.AliasConfig.srcAlias}  

#    attr_dict = {item.aliasName: str(item.src for item in self.srcAlias}
#    self.add_property(**attr_dict)
#    self._show_attrs.remove('srcAlias')

def EpicsConfig(self):
    """Expand PvConfig from epicsArch list.
    """
    pass
#    self.alias_pvId_dict = {p.description(): p.pvId() \
#            for p in self.getPvConfig}

#    self.add_property(**self.alias_pvId_dict)

def ControlDataConfig(self):
    """Expand detector aliases in pvControls and 
       pvMonitors list for psana ControlDataConfig.
    """
    pass

def IpimbConfig(self):
    """IpimbConfig
    """
    pass
#    capacitorDescriptions = [self.capacitorValue(int(val)) \
#            for val in self.capacitorValues]
#    self.add_property(capacitorDescriptions=capacitorDescriptions)
#    self._show_attrs.remove('capacitorValue')

#def EvrDataData(self):
#    if hasattr(self, 'fifoEvents'):
#        attrs = ['eventCode', 'timestampHigh' 'timestampLow']
#        for attr in 
#


#        for item in self.srcAlias:
#            setattr(self, item.aliasName(), item.src())

# {pv.description:pv.interval for pv in cxi.configStore.EpicsArch_0_NoDevice_0.EpicsConfig.getPvConfig}

#  {s.src(): s.group() for s in cxi.configStore.Partition.sources}

# None type not relevant
# [e for e in cxi.configStore.keys() if e.type()]


