# deviceApp/tasks.py
import datetime
from celery import shared_task
from django.utils.timezone import now
from .models import Device, check_device_internet_connectivity
import logging

logger = logging.getLogger(__name__)

@shared_task
def check_all_devices_connectivity():
    """
    Background task to check connectivity for all devices
    and update their last_connectivity timestamps
    """
    devices = Device.objects.all()
    results = {
        'total': devices.count(),
        'online': 0,
        'offline': 0,
        'errors': 0
    }
    
    for device in devices:
        try:
            if device.check_connectivity():
                results['online'] += 1
            else:
                results['offline'] += 1
        except Exception as e:
            results['errors'] += 1
            logger.error(f"Error checking connectivity for device {device.id} ({device.name}): {str(e)}")
    
    logger.info(f"Completed connectivity check: {results}")
    return results

@shared_task
def check_device_connectivity_by_id(device_id):
    """
    Background task to check connectivity for a specific device
    """
    try:
        device = Device.objects.get(id=device_id)
        is_online = device.check_connectivity()
        return {
            'device_id': device_id,
            'device_name': device.name,
            'status': 'online' if is_online else 'offline',
            'last_connectivity': device.last_connectivity.isoformat() if device.last_connectivity else None
        }
    except Device.DoesNotExist:
        logger.error(f"Device with ID {device_id} not found")
        return {'error': f'Device with ID {device_id} not found'}
    except Exception as e:
        logger.error(f"Error checking connectivity for device {device_id}: {str(e)}")
        return {'error': str(e)}






@shared_task
def check_all_devices_connectivity():
    """
    Background task to check connectivity for all devices
    and update their last_connectivity timestamps
    
    Intelligently groups devices by network to optimize checks
    """
    # First check if the host has internet connectivity
    if not check_device_internet_connectivity():
        logger.warning("Host machine has no internet connection, skipping device checks")
        return {
            'status': 'error',
            'message': 'Host machine has no internet connection',
            'total': 0
        }
    
    devices = Device.objects.all()
    results = {
        'total': devices.count(),
        'online': 0,
        'offline': 0,
        'errors': 0,
        'no_internet': 0,
        'details': []
    }
    
    # Group devices by network to optimize checks
    # (devices on same subnet likely share connectivity status)
    network_groups = {}
    for device in devices:
        if not device.ip_address:
            continue
        
        # Extract network part (first 3 octets for simple grouping)
        try:
            network = '.'.join(device.ip_address.split('.')[:3])
            if network not in network_groups:
                network_groups[network] = []
            network_groups[network].append(device)
        except:
            # Fallback for unusual IP formats
            network_groups.setdefault('others', []).append(device)
    
    # Process each network group
    for network, network_devices in network_groups.items():
        logger.info(f"Checking {len(network_devices)} devices on network {network}")
        
        for device in network_devices:
            try:
                previous_status = 'online' if device.last_connectivity and (
                    device.last_connectivity >= device.last_check_attempt) else 'offline'
                
                if device.check_connectivity():
                    results['online'] += 1
                    status = 'online'
                else:
                    if device.connectivity_error and 'reachable but has no internet' in device.connectivity_error:
                        results['no_internet'] += 1
                        status = 'no_internet'
                    else:
                        results['offline'] += 1
                        status = 'offline'
                
                # Record status change events
                if previous_status != status:
                    results['details'].append({
                        'device_id': device.id,
                        'name': device.name,
                        'previous': previous_status,
                        'current': status,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    logger.info(f"Device {device.name} ({device.ip_address}) changed from {previous_status} to {status}")
                    
                    # Possibly send notification here for status changes
                    
            except Exception as e:
                results['errors'] += 1
                logger.error(f"Error checking connectivity for device {device.id} ({device.name}): {str(e)}")
                results['details'].append({
                    'device_id': device.id, 
                    'name': device.name,
                    'error': str(e)
                })
    
    logger.info(f"Completed connectivity check: {results['online']} online, {results['offline']} offline, " 
                f"{results['no_internet']} no internet, {results['errors']} errors")
    return results