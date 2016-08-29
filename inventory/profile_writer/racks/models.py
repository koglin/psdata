from django.db import models

class Hutch(models.Model):

    HUTCH_CHOICES = (
            ('XPP','XPP'),
            ('XCS','XCS'),
            ('AMO','AMO'),
            ('SXR','SXR'),
            ('CXI','CXI'),
            ('MEC','MEC')
    )

    name = models.CharField(max_length=3,choices=HUTCH_CHOICES)
    building = models.CharField(max_length=4)


    def __unicode__(self):
        return self.name


class Rack(models.Model):
    
    name = models.CharField(max_length=3)
    hutch = models.ForeignKey(Hutch)
    height = models.IntegerField(default=48)

    class Meta(object):
        unique_together=('name','hutch')

    def __unicode__(self):
        return self.name


class Device(models.Model):

    ORIENTATION_CHOICES = (('front','front of rack'),('back','back of rack'))

    name = models.CharField(max_length=40)
    rack = models.ForeignKey(Rack)
    height = models.IntegerField()
    description = models.CharField(max_length=30)
    orientation = models.CharField(max_length=20,choices=ORIENTATION_CHOICES)



    def __unicode__(self):
        return self.name
