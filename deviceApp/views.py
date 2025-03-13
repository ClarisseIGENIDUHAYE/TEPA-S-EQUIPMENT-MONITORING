from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from django.shortcuts import get_object_or_404, render
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Device
from .serializers import DeviceSerializer

def get_device_page(request):
    return render(request, 'device/manage.html')




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_device_list(request):
    devices = Device.objects.all()
    serializer = DeviceSerializer(devices, many=True)
    
    # print(f"\n\n Retrived devices data: {serializer.data.name}\n\n")
    return JsonResponse(serializer.data, safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_device_detail(request, device_id):
    device = get_object_or_404(Device, id=device_id)
    serializer = DeviceSerializer(device)
    return JsonResponse(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_device(request):
    """
    Create a new device with duplicate validation and automatic connectivity check
    """
    data = JSONParser().parse(request)
    data['created_by'] = request.user
    
    # Normalize MAC address format if provided
    if 'mac_address' in data:
        mac = data['mac_address'].upper()
        mac = mac.replace(':', '').replace('-', '').replace('.', '')
        if len(mac) == 12:
            # Format consistently as XX:XX:XX:XX:XX:XX
            data['mac_address'] = ':'.join(mac[i:i+2] for i in range(0, 12, 2))
    
    # Check for duplicates manually before creating
    mac_address = data.get('mac_address')
    ip_address = data.get('ip_address')
    name = data.get('name')
    school_id = data.get('school_id')
    
    # MAC address must be unique across all schools
    if mac_address and Device.objects.filter(mac_address=data['mac_address']).exists():
        return JsonResponse({
            'error': 'duplicate_mac',
            'message': f"Device with MAC address '{mac_address}' already exists"
        }, status=400)
    
    # Name+School and IP+School should be unique combinations
    if school_id:
        if name and Device.objects.filter(name__iexact=name, school=school_id).exists():
            return JsonResponse({
                'error': 'duplicate_name',
                'message': f"Device with name '{name}' already exists in this school"
            }, status=400)
        
        if ip_address and Device.objects.filter(ip_address=ip_address, school=school_id).exists():
            return JsonResponse({
                'error': 'duplicate_ip',
                'message': f"Device with IP address '{ip_address}' already exists in this school"
            }, status=400)
    
    serializer = DeviceSerializer(data=data, context={'request': request})
    if serializer.is_valid():
        device = serializer.save()
        
        # Immediately check connectivity for the new device
        try:
            device.check_connectivity()
            # Re-serialize to include the updated connectivity information
            updated_serializer = DeviceSerializer(device)
            return JsonResponse(updated_serializer.data, status=201)
        except Exception as e:
            # Still return success but include the error
            return JsonResponse({
                **serializer.data,
                'connectivity_check_error': str(e)
            }, status=201)
    
    return JsonResponse(serializer.errors, status=400)




@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_device(request, device_id):
    """
    Update a device with duplicate validation and automatic connectivity check
    """
    device = get_object_or_404(Device, id=device_id)
    data = JSONParser().parse(request)
    
    # Normalize MAC address format if provided
    if 'mac_address' in data:
        mac = data['mac_address'].upper()
        mac = mac.replace(':', '').replace('-', '').replace('.', '')
        if len(mac) == 12:
            # Format consistently as XX:XX:XX:XX:XX:XX
            data['mac_address'] = ':'.join(mac[i:i+2] for i in range(0, 12, 2))
    
    # Check for duplicates manually before updating
    mac_address = data.get('mac_address')
    ip_address = data.get('ip_address')
    name = data.get('name')
    school_id = data.get('school_id')
    
    # MAC address must be unique across all schools
    if mac_address and Device.objects.filter(mac_address=data['mac_address']).exclude(id=device_id).exists():
        return JsonResponse({
            'error': 'duplicate_mac',
            'message': f"Device with MAC address '{mac_address}' already exists"
        }, status=400)
    
    # Name+School and IP+School should be unique combinations
    if school_id:
        if name and Device.objects.filter(name__iexact=name, school=school_id).exclude(id=device_id).exists():
            return JsonResponse({
                'error': 'duplicate_name',
                'message': f"Device with name '{name}' already exists in this school"
            }, status=400)
        
        if ip_address and Device.objects.filter(ip_address=ip_address, school=school_id).exclude(id=device_id).exists():
            return JsonResponse({
                'error': 'duplicate_ip',
                'message': f"Device with IP address '{ip_address}' already exists in this school"
            }, status=400)
    
    serializer = DeviceSerializer(device, data=data, partial=True)
    if serializer.is_valid():
        updated_device = serializer.save()
        
        # If IP address changed, immediately check connectivity
        ip_changed = 'ip_address' in data and data['ip_address'] != device.ip_address
        if ip_changed or request.query_params.get('check_connectivity') == 'true':
            try:
                updated_device.check_connectivity()
                # Re-serialize to include the updated connectivity information
                updated_serializer = DeviceSerializer(updated_device)
                return JsonResponse(updated_serializer.data)
            except Exception as e:
                # Still return success but include the error
                return JsonResponse({
                    **serializer.data,
                    'connectivity_check_error': str(e)
                })
        
        return JsonResponse(serializer.data)
    
    return JsonResponse(serializer.errors, status=400)




@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_device(request, device_id):
    device = get_object_or_404(Device, id=device_id)
    device.delete()
    return JsonResponse({'message': 'Device deleted successfully'}, status=204)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_device_status(request, device_id):
    device = get_object_or_404(Device, id=device_id)
    status = device.status  # Calls the property method
    return JsonResponse({'device_id': device_id, 'status': status})




















