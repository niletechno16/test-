from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def ping(request):
    return JsonResponse({"status": "alive"})


urlpatterns = [
    path('admin/',               admin.site.urls),
    path('keep-alive/ping/',     ping),
    path('',                     include('apps.dashboard.urls')),
    path('reports/',             include('apps.reports.urls')),
    path('customers/',           include('apps.customers.urls')),
    path('agents/',              include('apps.agents.urls')),
    path('users/',               include('apps.users.urls')),
]
