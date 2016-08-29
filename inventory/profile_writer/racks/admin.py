from django.contrib import admin

from .models import Hutch,Rack,Device


class RacksInline(admin.TabularInline):

   model = Rack
   extra = 1

class HutchAdmin(admin.ModelAdmin):

    list_display = ['name','building']

    inlines = [RacksInline]



admin.site.register(Hutch,HutchAdmin)
