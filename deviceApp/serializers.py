# deviceApp/serializers.py
from rest_framework import serializers
from .models import Device
from userApp.models import CustomUser
from schoolApp.models import School


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'phone_number', 'email', 'role', 'profile_picture']

class SchoolSerializer(serializers.ModelSerializer):
    created_by = CustomUserSerializer(read_only=True)

    class Meta:
        model = School
        fields = ['id', 'index_number', 'name', 'province', 'district', 'created_by', 'created_at']



class DeviceSerializer(serializers.ModelSerializer):
    created_by = CustomUserSerializer(read_only=True)
    school = SchoolSerializer(read_only=True)
    school_id = serializers.PrimaryKeyRelatedField(
        queryset=School.objects.all(),
        write_only=True,
        source='school'
    )
    
    class Meta:
        model = Device
        fields = ['id', 'name', 'mac_address', 'ip_address', 'type', 'status', 
                 'school', 'school_id', 'created_by', 'created_at', 'last_updated']
