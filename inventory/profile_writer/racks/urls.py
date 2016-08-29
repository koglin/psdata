from django.conf.urls import url

from . import views


urlpatterns = [
        url(r'^$',views.Hutch_Index_View.as_view(), name = 'Hutch_Index_View'),
        url(r'^(?P<pk>[0-9]+)/$',views.Hutch_View.as_view(),name = 'Hutch_View'),
        url(r'^blah/$',views.trial,name='rks')
]
