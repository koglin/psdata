import sys

from django.shortcuts import get_object_or_404,render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views import generic

from .models import Hutch,Rack,Device

sys.path.append('/reg/neh/home3/trendahl/Python_Scripts/NetConfig_Scripts')
import rack_profile as racks
# Create your views here.


def load_rack_profiles():

    if not racks.Rack_List.racks:
        rl = racks.Rack_List()

    for hutch_name in racks.Rack_List._hutches.values():
        
        if not Hutch.objects.filter(name=hutch_name).exists():
            h = Hutch(name=hutch_name,building='LCLS')
            h.save()

    for rack_name,rack_obj in racks.Rack_List.racks.items():

        if not Rack.objects.filter(name=rack_name).exists() and Hutch.objects.filter(name=rack_obj.hutch).exists():
            r = Rack(name=rack_name,hutch=Hutch.objects.filter(name=rack_obj.hutch)[0])
            r.save()




class Hutch_Index_View(generic.ListView):


    template_name = 'racks/hutch_index.html'
    context_object_name = 'hutch_list'
    
    def __init__(self):
        load_rack_profiles()

    
    def get_queryset(self):
        return Hutch.objects.order_by('name')


class Hutch_View(generic.DetailView):
   
    template_name = 'racks/rack_index.html'

    model = Hutch  






def trial(request):

    return render(request,'racks/rack.html', {'racks',Rack.objects.all()})
