# deviceApp/views.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Device
from .serializers import DeviceSerializer
from schoolApp.models import School
import re

# Completely independent functions for each operation

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_devices(request):
    """Get all devices"""
    devices = Device.objects.all()
    serializer = DeviceSerializer(devices, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_device(request):
    """Create a new device with validation"""
    data = request.data
    
    # Validate required fields
    required_fields = ['name', 'mac_address', 'type', 'school_id']
    for field in required_fields:
        if field not in data:
            return Response({'error': f'Field {field} is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate MAC address format
    mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
    mac_address = data.get('mac_address')
    if not mac_pattern.match(mac_address):
        return Response({'error': 'Invalid MAC address format'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if MAC address is unique
    if Device.objects.filter(mac_address=mac_address).exists():
        return Response({'error': 'Device with this MAC address already exists'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate device type
    if data.get('type') not in dict(Device.DEVICE_TYPES):
        return Response({'error': 'Invalid device type'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate status if provided
    if 'status' in data and data.get('status') not in dict(Device.STATUS_CHOICES):
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate school exists
    try:
        school = School.objects.get(id=data.get('school_id'))
    except School.DoesNotExist:
        return Response({'error': 'School with given ID does not exist'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Create the device
    device = Device.objects.create(
        name=data.get('name'),
        mac_address=data.get('mac_address'),
        ip_address=data.get('ip_address'),
        type=data.get('type'),
        status=data.get('status', 'unknown'),
        school=school,
        created_by=request.user
    )
    
    serializer = DeviceSerializer(device)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_device_by_id(request, pk):
    """Get a single device by its ID"""
    try:
        device = Device.objects.get(pk=pk)
        serializer = DeviceSerializer(device)
        return Response(serializer.data)
    except Device.DoesNotExist:
        return Response({'error': 'Device not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_device(request, pk):
    """Update a device with validation"""
    try:
        device = Device.objects.get(pk=pk)
    except Device.DoesNotExist:
        return Response({'error': 'Device not found'}, status=status.HTTP_404_NOT_FOUND)
        
    data = request.data
    
    # Validate MAC address format if provided
    if 'mac_address' in data:
        mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
        mac_address = data.get('mac_address')
        if not mac_pattern.match(mac_address):
            return Response({'error': 'Invalid MAC address format'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if MAC address is unique (excluding this device)
        if Device.objects.filter(mac_address=mac_address).exclude(id=pk).exists():
            return Response({'error': 'Device with this MAC address already exists'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate device type if provided
    if 'type' in data and data.get('type') not in dict(Device.DEVICE_TYPES):
        return Response({'error': 'Invalid device type'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate status if provided
    if 'status' in data and data.get('status') not in dict(Device.STATUS_CHOICES):
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate school exists if provided
    if 'school_id' in data:
        try:
            school = School.objects.get(id=data.get('school_id'))
            device.school = school
        except School.DoesNotExist:
            return Response({'error': 'School with given ID does not exist'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Update fields
    if 'name' in data:
        device.name = data.get('name')
    if 'mac_address' in data:
        device.mac_address = data.get('mac_address')
    if 'ip_address' in data:
        device.ip_address = data.get('ip_address')
    if 'type' in data:
        device.type = data.get('type')
    if 'status' in data:
        device.status = data.get('status')
    
    device.save()
    serializer = DeviceSerializer(device)
    return Response(serializer.data)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_device(request, pk):
    """Delete a device by its ID"""
    try:
        device = Device.objects.get(pk=pk)
        device.delete()
        return Response({'message': 'Device deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
    except Device.DoesNotExist:
        return Response({'error': 'Device not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_devices(request):
    """Get all devices created by the logged-in user"""
    devices = Device.objects.filter(created_by=request.user)
    serializer = DeviceSerializer(devices, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_devices_by_status(request, status_value):
    """Get devices filtered by status"""
    # Validate status
    if status_value not in dict(Device.STATUS_CHOICES):
        return Response({'error': 'Invalid status value'}, status=status.HTTP_400_BAD_REQUEST)
        
    devices = Device.objects.filter(status=status_value)
    serializer = DeviceSerializer(devices, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_devices_by_district(request, district):
    """Get devices filtered by school district"""
    devices = Device.objects.filter(school__district=district)
    serializer = DeviceSerializer(devices, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_devices_by_province(request, province):
    """Get devices filtered by school province"""
    devices = Device.objects.filter(school__province=province)
    serializer = DeviceSerializer(devices, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_devices_by_school(request, school_id):
    """Get devices for a specific school"""
    try:
        school = School.objects.get(id=school_id)
        devices = Device.objects.filter(school=school)
        serializer = DeviceSerializer(devices, many=True)
        return Response(serializer.data)
    except School.DoesNotExist:
        return Response({'error': 'School not found'}, status=status.HTTP_404_NOT_FOUND)
