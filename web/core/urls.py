from django.contrib import admin
from django.urls import path

from web.core.admin import site


urlpatterns = [
    path('admin/', site.urls),
]
