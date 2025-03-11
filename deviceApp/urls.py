# deviceApp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('devices/', views.get_all_devices, name='get-all-devices'),
    path('devices/create/', views.create_device, name='create-device'),
    path('devices/<int:pk>/', views.get_device_by_id, name='get-device-by-id'),
    path('devices/<int:pk>/update/', views.update_device, name='update-device'),
    path('devices/<int:pk>/delete/', views.delete_device, name='delete-device'),
    path('my-devices/', views.get_user_devices, name='get-user-devices'),
    path('devices/status/<str:status_value>/', views.get_devices_by_status, name='get-devices-by-status'),
    path('devices/district/<str:district>/', views.get_devices_by_district, name='get-devices-by-district'),
    path('devices/province/<str:province>/', views.get_devices_by_province, name='get-devices-by-province'),
    path('devices/school/<int:school_id>/', views.get_devices_by_school, name='get-devices-by-school'),
]