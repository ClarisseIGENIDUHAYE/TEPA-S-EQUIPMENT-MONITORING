# deviceApp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('<int:device_id>/routers/', views.get_routers_by_device, name='get-routers-by-device'),
    path('create/', views.create_Router, name='create-device'),
    path('<int:router_id>/', views.get_Router_detail, name='get-device-by-id'),
    path('update/<int:router_id>/', views.update_Router, name='update-device'),
    path('delete/<int:router_id>/', views.delete_Router, name='delete-device'),
    
]
