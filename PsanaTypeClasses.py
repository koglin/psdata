#import PsanaDictify

#class AliasConfig(PsanaDictify.TypeDictify):
#    """Class to expand detector aliases in AliasConfig.srcAlias list.
#    """
#
#    def __init__(self, *args, **kwargs):
#        PsanaDictify.TypeDictify.__init__(self, *args, **kwargs)
#
def AliasConfig(self):
    attr_dict = {item.aliasName(): item.src for item in self.srcAlias}
    self.add_property(**attr_dict)
    self._show_attrs.remove('srcAlias')

#class EpicsConfig(PsanaDictify.TypeDictify):
#    """Class to expand PvConfig from epicsArch list.
#    """
#
#    def __init__(self, *args, **kwargs):
#        PsanaDictify.TypeDictify.__init__(self, *args, **kwargs)
#
#
#def 
#        self.alias_pvId_dict = {p.description(): p.pvId() \
#                for p in self.getPvConfig}
#
#        self.add_property(**self.alias_pvId_dict)
#
#
#class ControlDataConfig(PsanaDictify.TypeDictify):
#    """Class to expand detector aliases in pvControls and 
#       pvMonitors list for psana ControlDataConfig.
#    """
#
#    def __init__(self, *args, **kwargs):
#        PsanaDictify.TypeDictify.__init__(self, *args, **kwargs)
#

#class IpimbConfig(PsanaDictify.TypeDictify):
#
#    def __init__(self, *args, **kwargs):
#        PsanaDictify.TypeDictify.__init__(self, *args, **kwargs)
#
#        capacitorDescriptions = [self.capacitorValue(val) \
#                for val in self.capacitorValues]



#        for item in self.srcAlias:
#            setattr(self, item.aliasName(), item.src())

# {pv.description:pv.interval for pv in cxi.configStore.EpicsArch_0_NoDevice_0.EpicsConfig.getPvConfig}

#  {s.src(): s.group() for s in cxi.configStore.Partition.sources}

# None type not relevant
# [e for e in cxi.configStore.keys() if e.type()]


