from rest_framework import serializers
from .models import Device
from userApp.models import CustomUser
from schoolApp.models import School
from django.db import IntegrityError
from django.db.models import Q
import re

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'phone_number', 'email', 'role']

class SchoolSerializer(serializers.ModelSerializer):
    created_by = CustomUserSerializer(read_only=True)

    class Meta:
        model = School
        fields = ['id', 'index_number', 'name', 'province', 'district', 'created_by', 'created_at']



# In serializers.py, update the DeviceSerializer:

class DeviceSerializer(serializers.ModelSerializer):
    created_by = CustomUserSerializer(read_only=True)
    school = SchoolSerializer(read_only=True)
    school_id = serializers.PrimaryKeyRelatedField(
        queryset=School.objects.all(),
        write_only=True,
        source='school'
    )
    created_by_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        write_only=True,
        source='created_by',
        required=False  # Make it not required since you set it in the view
    )
    status = serializers.SerializerMethodField()
    connectivity_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Device
        fields = ['id', 'name', 'mac_address', 'ip_address', 'type',
                 'check_ports', 'use_ping_fallback', 'created_by', 'created_by_id', 'status', 'connectivity_details',
                 'school', 'school_id', 'created_at', 'last_updated',
                 'last_connectivity', 'last_check_attempt', 'connectivity_error']
    
    def create(self, validated_data):
        # If there's no context or request, just use the validated data as is
        if 'request' not in self.context and 'created_by' not in validated_data:
            print("\nCreated by user is required\n")
            raise serializers.ValidationError("Created by user is required")
        
        # If created_by is not in validated_data but we have a request, use the request user
        if 'created_by' not in validated_data and 'request' in self.context:
            validated_data['created_by'] = self.context['request'].user
            
        return super().create(validated_data)
    
    def get_status(self, obj):
        """Get real-time status by checking device connectivity"""
        try:
            # Check if the method exists
            if not hasattr(obj, 'check_connectivity'):
                return 'error'
                
            # Force a new connectivity check
            result = obj.check_connectivity()
            
            # Check status from the result dictionary
            if isinstance(result, dict) and 'status' in result:
                status = result['status']
            else:
                # Fall back to boolean interpretation if result is not a dict
                is_online = bool(result)
                status = 'online' if is_online else 'offline'
            
            # Check if it's reachable but has connectivity error
            if status == 'online':
                return 'online'
            elif obj.connectivity_error and 'reachable but has no internet' in obj.connectivity_error:
                return 'no_internet'  # New status for devices that are up but can't access internet
            elif obj.connectivity_error and 'reachable but appears to be offline' in obj.connectivity_error:
                return 'offline'  # Device is technically reachable but failing deeper checks
            else:
                return 'offline'
        except Exception as e:
            obj.connectivity_error = str(e)
            obj.save(update_fields=['connectivity_error'])
            return 'error'
    
    def get_connectivity_details(self, obj):
        """Return detailed connectivity information"""
        details = {
            'timestamp': obj.last_connectivity,
            'last_check_attempt': obj.last_check_attempt,
            'human_readable': "Never connected" if not obj.last_connectivity else f"Last seen online: {obj.last_connectivity.strftime('%Y-%m-%d %H:%M:%S')}",
            'check_methods': {
                'ports_checked': obj.check_ports if obj.check_ports else "80,443,22,8080 (default)",
                'ping_fallback': "Enabled" if obj.use_ping_fallback else "Disabled"
            }
        }
        
        # Add error message if any
        if obj.connectivity_error:
            details['error'] = obj.connectivity_error
            
        # Add connectivity status information
        if obj.last_check_attempt:
            if obj.last_connectivity and obj.last_connectivity >= obj.last_check_attempt:
                details['status_detail'] = "Device is online and has internet connectivity"
            elif obj.connectivity_error and 'reachable but has no internet' in obj.connectivity_error:
                details['status_detail'] = "Device is reachable but has no internet access"
            elif obj.connectivity_error and 'reachable but appears to be offline' in obj.connectivity_error:
                details['status_detail'] = "Device is reachable but appears to be offline"
            else:
                details['status_detail'] = "Device is offline or unreachable"
        
        # Add connection metrics if available
        try:
            if hasattr(obj, 'get_connectivity_metrics'):
                metrics = obj.get_connectivity_metrics()
                if metrics:
                    details['metrics'] = metrics
            
            # Also add connection_details from the model if available
            if hasattr(obj, 'connection_details'):
                conn_details = obj.connection_details
                if conn_details:
                    # Add specific fields we want from connection_details
                    if 'ping_check' in conn_details:
                        details['ping_metrics'] = conn_details['ping_check']
                    if 'port_check' in conn_details:
                        details['port_metrics'] = conn_details['port_check']
        except Exception as e:
            details['metrics_error'] = str(e)
                
        return details  
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
# created_by_id = serializers.PrimaryKeyRelatedField(
#         queryset=CustomUser.objects.all(),
#         write_only=True,
#         source='created_by',
#         required=False  # Make it not required since you set it in the view
#     )
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    