
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('userApp.urls')),
    path('school/', include('schoolApp.urls')),
    path('device/', include('deviceApp.urls')),
]
