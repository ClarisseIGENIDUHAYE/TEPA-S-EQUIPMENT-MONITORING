from django.db import models
from django.utils.timezone import now
from schoolApp.models import School
from userApp.models import CustomUser
from datetime import datetime
import json

from .utils import (
    check_device_connectivity_with_params,
    check_internet_connectivity,
    is_valid_ipv4
)

class Device(models.Model):
    DEVICE_TYPES = (
        ('router', 'Router'),
        ('phone', 'Phone'),
        ('pc', 'PC'),
        ('laptop', 'Laptop'),
        ('tablet', 'Tablet'),
        ('other', 'Other'),
    )
    
    name = models.CharField(max_length=255)
    mac_address = models.CharField(max_length=100, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    type = models.CharField(max_length=50, choices=DEVICE_TYPES)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='devices')
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='devices')
    created_at = models.DateTimeField(default=now)
    last_updated = models.DateTimeField(auto_now=True)
    last_connectivity = models.DateTimeField(null=True, blank=True)
    
    # Connectivity settings
    check_ports = models.CharField(max_length=255, blank=True, null=True, 
                                  help_text="Comma-separated ports to check (e.g., '80,443,22')")
    use_ping_fallback = models.BooleanField(default=True)
    ping_count = models.IntegerField(default=3)
    timeout = models.IntegerField(default=5)
    retry_count = models.IntegerField(default=2)
    
    # Status tracking fields
    last_check_attempt = models.DateTimeField(null=True, blank=True)
    connectivity_error = models.CharField(max_length=255, blank=True, null=True)
    connectivity_details = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-last_updated']
        unique_together = [
            ('name', 'school', 'ip_address'),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.type}) - {self.school.name}"
    
    @property
    def status(self):
        """Dynamic property that returns the current connectivity status"""
        try:
            latest_check = self.check_connectivity()
            return latest_check.get('status', 'unknown')
        except Exception as e:
            self.connectivity_error = str(e)
            self.save(update_fields=['connectivity_error'])
            return 'error'
    
    @property
    def connection_details(self):
        """Returns the latest connectivity check details as a dictionary"""
        if self.connectivity_details:
            try:
                return json.loads(self.connectivity_details)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def check_connectivity(self, save_result=True):
        """
        Check if the device is online using both port checks and ping based on the utils module.
        Updates device status fields and returns the detailed result dictionary.
        
        Parameters:
        - save_result: Whether to save the result to the database
        
        Returns: 
        - Dictionary with detailed connectivity information
        """
        # Update check attempt timestamp
        self.last_check_attempt = now()
        self.connectivity_error = None
        
        # Basic validation
        if not self.ip_address:
            self.connectivity_error = "No IP address configured"
            if save_result:
                self.save(update_fields=['last_check_attempt', 'connectivity_error'])
            return {'status': 'offline', 'error': self.connectivity_error}
            
        if not is_valid_ipv4(self.ip_address):
            self.connectivity_error = "Invalid IP address format"
            if save_result:
                self.save(update_fields=['last_check_attempt', 'connectivity_error'])
            return {'status': 'offline', 'error': self.connectivity_error}
        
        # Check if host machine has internet connectivity
        if not check_internet_connectivity():
            self.connectivity_error = "Host machine has no internet connection"
            if save_result:
                self.save(update_fields=['last_check_attempt', 'connectivity_error'])
            return {'status': 'unknown', 'error': self.connectivity_error}
        
        # Use the enhanced connectivity check function from utils
        result = check_device_connectivity_with_params(
            ip_address=self.ip_address,
            device_type=self.type,
            ports=self.check_ports,
            use_ping_fallback=self.use_ping_fallback,
            ping_count=self.ping_count,
            timeout=self.timeout,
            retry_count=self.retry_count
        )
        
        # Update device fields based on check results
        if result['status'] == 'online':
            self.last_connectivity = now()
            self.connectivity_error = None
        else:
            self.connectivity_error = result.get('error', 'Device is unreachable')
        
        # Store the detailed results 
        self.connectivity_details = json.dumps(result)
        
        if save_result:
            fields_to_update = [
                'last_check_attempt', 
                'connectivity_error', 
                'connectivity_details'
            ]
            
            if result['status'] == 'online':
                fields_to_update.append('last_connectivity')
                
            self.save(update_fields=fields_to_update)
        
        return result
    
    def get_connectivity_metrics(self):
        """
        Returns consolidated connectivity metrics based on the latest check
        """
        details = self.connection_details
        
        metrics = {
            'status': self.status,
            'last_check': self.last_check_attempt,
            'last_online': self.last_connectivity,
            'error': self.connectivity_error
        }
        
        # Extract ping metrics if available
        if details and 'ping_check' in details:
            ping_data = details['ping_check']
            if ping_data:
                metrics.update({
                    'latency_ms': ping_data.get('latency_ms'),
                    'packet_loss': ping_data.get('packet_loss')
                })
        
        # Extract port check metrics if available
        if details and 'port_check' in details:
            port_data = details['port_check']
            if port_data:
                metrics.update({
                    'ports_checked': port_data.get('ports_checked'),
                    'ports_open': port_data.get('ports_open'),
                    'open_ports': port_data.get('open_ports')
                })
        
        return metrics
    
    def bulk_check_devices(cls, school_id=None, device_type=None):
        """
        Class method to check connectivity for multiple devices with filtering options
        
        Parameters:
        - school_id: Optional filter by school
        - device_type: Optional filter by device type
        
        Returns:
        - Dictionary with summary and individual device results
        """
        filters = {}
        if school_id:
            filters['school_id'] = school_id
        if device_type:
            filters['type'] = device_type
            
        devices = cls.objects.filter(**filters)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'total_devices': devices.count(),
            'online_count': 0,
            'offline_count': 0,
            'error_count': 0,
            'details': {}
        }
        
        for device in devices:
            device_result = device.check_connectivity()
            
            # Update counts
            if device_result['status'] == 'online':
                results['online_count'] += 1
            elif device_result['status'] == 'offline':
                results['offline_count'] += 1
            else:
                results['error_count'] += 1
                
            # Store detailed result
            results['details'][device.id] = {
                'name': device.name,
                'ip': device.ip_address,
                'type': device.type,
                'status': device_result['status'],
                'error': device_result.get('error'),
                'school': device.school.name
            }
            
            # Add latency if available
            ping_data = device_result.get('ping_check', {})
            if ping_data and ping_data.get('latency_ms') is not None:
                results['details'][device.id]['latency_ms'] = ping_data['latency_ms']
        
        # Calculate summary statistics for online devices
        online_devices = [details for _, details in results['details'].items() 
                         if details['status'] == 'online' and 'latency_ms' in details]
        
        if online_devices:
            latencies = [device['latency_ms'] for device in online_devices]
            results['avg_latency_ms'] = sum(latencies) / len(latencies)
            results['min_latency_ms'] = min(latencies)
            results['max_latency_ms'] = max(latencies)
        
        return results