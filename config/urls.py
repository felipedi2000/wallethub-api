from django.contrib import admin
from django.urls import path
from config import settings


urlpatterns = [
    
]

if settings.ENABLE_ADMIN:
  urlpatterns.append(path("admin/", admin.site.urls))