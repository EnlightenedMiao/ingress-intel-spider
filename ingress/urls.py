from django.conf import settings
from django.conf.urls import  include, url
from django.contrib import admin

urlpatterns = [
    url(r'^', include('ingress.ingress.urls')),
    url(r'^admin/', admin.site.urls),
]


