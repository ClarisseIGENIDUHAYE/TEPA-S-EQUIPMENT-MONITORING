from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from django.shortcuts import get_object_or_404, render
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Router
from .serializers import RouterSerializer
from deviceApp.models import Device


@api_view(['GET'])
@permission_classes([AllowAny])
def get_routers_by_device(request, device_id):
    """
    Get all routers associated with a specific access point device
    """
    # Get the device or return 404
    device = get_object_or_404(Device, id=device_id)
    
    # Get all routers that have this device as their access_point
    routers = Router.objects.filter(access_point_id=device_id)

    # Serialize the data
    serializer = RouterSerializer(routers, many=True)
    
    # Print the returned data to the terminal
    print("Returned Data:", serializer.data)  # This will display the data in the terminal
  
    # Check if the request is asking for HTML
    if request.accepted_media_type == 'text/html' or 'html' in request.query_params.get('format', ''):
        # If HTML is requested, render the template
        context = {
            'device': device,
            'routers': routers
        }
        return render(request, 'router/manage.html', context)
    else:
        # Otherwise return JSON
        return JsonResponse(serializer.data, safe=False)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_Router_detail(request, router_id):
    router_obj = get_object_or_404(Router, id=router_id)
    serializer = RouterSerializer(router_obj)
    return JsonResponse(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_Router(request):
    """
    Create a new Router with duplicate validation and automatic connectivity check
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
    access_point_id = data.get('access_point_id')
    
    if not mac_address or not ip_address or not name or not access_point_id:
        print("All fields are required")
        
    
    # MAC address must be unique across all schools
    if mac_address and Router.objects.filter(mac_address=data['mac_address']).exists():
        error_message = f"Router with MAC address '{mac_address}' already exists"
        print(f"ERROR: {error_message}")  # Log to terminal
        return JsonResponse({
            'error': 'duplicate_mac',
            'message': error_message
        }, status=400)
    
    # Name+AccessPoint and IP+AccessPoint should be unique combinations
    if access_point_id:
        if name and Router.objects.filter(name__iexact=name, access_point_id=access_point_id).exists():
            error_message = f"Router with name '{name}' already exists for this access point"
            print(f"ERROR: {error_message}")  # Log to terminal
            return JsonResponse({
                'error': 'duplicate_name',
                'message': error_message
            }, status=400)
        
        if ip_address and Router.objects.filter(ip_address=ip_address, access_point_id=access_point_id).exists():
            error_message = f"Router with IP address '{ip_address}' already exists for this access point"
            print(f"ERROR: {error_message}")  # Log to terminal
            return JsonResponse({
                'error': 'duplicate_ip',
                'message': error_message
            }, status=400)
    
    serializer = RouterSerializer(data=data, context={'request': request})
    if serializer.is_valid():
        router_instance = serializer.save()
        
        # Immediately check connectivity for the new Router
        try:
            router_instance.check_connectivity()
            # Re-serialize to include the updated connectivity information
            updated_serializer = RouterSerializer(router_instance)
            print("SUCCESS: Router created and connectivity check passed")  # Log success to terminal
            return JsonResponse(updated_serializer.data, status=201)
        except Exception as e:
            error_message = f"Connectivity check failed: {str(e)}"
            print(f"WARNING: {error_message}")  # Log connectivity check error to terminal
            return JsonResponse({
                **serializer.data,
                'connectivity_check_error': str(e)
            }, status=201)
    else:
        print(f"VALIDATION ERROR: {serializer.errors}")  # Log validation errors to terminal
        return JsonResponse(serializer.errors, status=400)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_Router(request, router_id):
    """
    Update a Router with duplicate validation and automatic connectivity check
    """
    # Rename local variable to avoid conflict
    router = get_object_or_404(Router, id=router_id)
    print(f"INFO: Updating router with ID: {router_id}")

    data = JSONParser().parse(request)

    # Normalize MAC address format if provided
    if 'mac_address' in data:
        mac = data['mac_address'].upper()
        mac = mac.replace(':', '').replace('-', '').replace('.', '')
        if len(mac) == 12:
            data['mac_address'] = ':'.join(mac[i:i+2] for i in range(0, 12, 2))
            print(f"INFO: Normalized MAC address to {data['mac_address']}")

    # Check for duplicates manually before updating
    mac_address = data.get('mac_address')
    ip_address = data.get('ip_address')
    name = data.get('name')
    access_point_id = data.get('access_point_id')

    # MAC address must be unique across all schools
    if mac_address and Router.objects.filter(mac_address=data['mac_address']).exclude(id=router_id).exists():
        error_message = f"Router with MAC address '{mac_address}' already exists"
        print(f"ERROR: {error_message}")
        return JsonResponse({
            'error': 'duplicate_mac',
            'message': error_message
        }, status=400)

    # Name+School and IP+School should be unique combinations
    if access_point_id:
        if name and Router.objects.filter(name__iexact=name, access_point=access_point_id).exclude(id=router_id).exists():
            error_message = f"Router with name '{name}' already exists"
            print(f"ERROR: {error_message}")
            return JsonResponse({
                'error': 'duplicate_name',
                'message': error_message
            }, status=400)

        if ip_address and Router.objects.filter(ip_address=ip_address, access_point=access_point_id).exclude(id=router_id).exists():
            error_message = f"Router with IP address '{ip_address}' already exists"
            print(f"ERROR: {error_message}")
            return JsonResponse({
                'error': 'duplicate_ip',
                'message': error_message
            }, status=400)

    # Update the router instance
    serializer = RouterSerializer(router, data=data, partial=True)
    if serializer.is_valid():
        updated_router = serializer.save()

        # If IP address changed, immediately check connectivity
        ip_changed = 'ip_address' in data and data['ip_address'] != router.ip_address
        if ip_changed or request.query_params.get('check_connectivity') == 'true':
            try:
                updated_router.check_connectivity()
                updated_serializer = RouterSerializer(updated_router)
                print(f"SUCCESS: Connectivity check passed for router ID: {router_id}")
                return JsonResponse(updated_serializer.data)
            except Exception as e:
                error_message = f"Connectivity check failed: {str(e)}"
                print(f"WARNING: {error_message}")
                return JsonResponse({
                    **serializer.data,
                    'connectivity_check_error': str(e)
                })

        print(f"SUCCESS: Router updated successfully with ID: {router_id}")
        return JsonResponse(serializer.data)

    print(f"VALIDATION ERROR: {serializer.errors}")
    return JsonResponse(serializer.errors, status=400)



@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_Router(request, router_id):
   
    router = get_object_or_404(Router, id=router_id)
    print(f"INFO: Deleting router with ID: {router_id}")

    router.delete()
    print(f"SUCCESS: Router with ID {router_id} deleted successfully")

    return JsonResponse({'message': 'Router deleted successfully'}, status=204)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_Router_status(request, router_id):
    Router = get_object_or_404(Router, id=router_id)
    status = Router.status  # Calls the property method
    return JsonResponse({'Router_id': router_id, 'status': status})






















