# deviceApp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('get_device_page/', views.get_device_page, name='get_device_page'),
    path('devices/', views.get_device_list, name='get-all-devices'),
    path('create/', views.create_device, name='create-device'),
    path('<int:device_id>/', views.get_device_detail, name='get-device-by-id'),
    path('update/<int:device_id>/', views.update_device, name='update-device'),
    path('delete/<int:device_id>/', views.delete_device, name='delete-device'),
]
