from django.db import models
from django.utils.timezone import now
from schoolApp.models import School
from userApp.models import CustomUser
import socket
import subprocess
import platform
from datetime import datetime
from .utils import check_device_connectivity_with_params

# Add this utility function at the top of the file
def check_device_internet_connectivity():
    """
    Check if the host machine has internet connectivity
    Returns True if it has internet access, False otherwise
    """
    import socket
    try:
        # Try to connect to Google's DNS server
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        pass
    
    try:
        # Try to connect to Cloudflare's DNS server as a backup
        socket.create_connection(("1.1.1.1", 53), timeout=3)
        return True
    except OSError:
        pass
        
    return False

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
    
    # Adding ports to check for connectivity
    check_ports = models.CharField(max_length=255, blank=True, null=True, 
                                   help_text="Comma-separated ports to check (e.g., '80,443,22')")
    
    # Whether to use ping as fallback when port check fails
    use_ping_fallback = models.BooleanField(default=True)
    
    # New field to track last attempted connectivity check
    last_check_attempt = models.DateTimeField(null=True, blank=True)
    
    # New field to store internet connection error if occurred
    connectivity_error = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        ordering = ['-last_updated']
        # Add additional unique constraints to prevent duplicates
        unique_together = [
            ('name', 'school', 'ip_address'),  # Prevent same name+school+IP combinations
        ]
    
    def __str__(self):
        return f"{self.name} ({self.type}) - {self.school.name}"
    
    @property
    def status(self):
        """Dynamic property that always returns the current status based on connectivity check"""
        try:
            return 'online' if self.check_connectivity() else 'offline'
        except Exception as e:
            self.connectivity_error = str(e)
            self.save(update_fields=['connectivity_error'])
            return 'error'
    
    def check_connectivity(self):
        """
        Check if the device is online using both port checks and ping
        Also verifies that the device itself has internet connectivity
        Returns True if online and has internet access, False otherwise.
        Updates the last_check_attempt timestamp regardless of outcome.
        """
        # Always update the last check attempt time
        self.last_check_attempt = now()
        self.connectivity_error = None
        
        if not self.ip_address:
            self.connectivity_error = "No IP address configured"
            self.save(update_fields=['last_check_attempt', 'connectivity_error'])
            return False
        
        # First, check if host has internet connectivity
        try:
            if not check_device_internet_connectivity():
                self.connectivity_error = "Host machine has no internet connection"
                self.save(update_fields=['last_check_attempt', 'connectivity_error'])
                return False
        except Exception as e:
            self.connectivity_error = f"Error checking host connectivity: {str(e)}"
            self.save(update_fields=['last_check_attempt', 'connectivity_error'])
            return False
        
        # Use the enhanced connectivity check function
        result = check_device_connectivity_with_params(
            ip_address=self.ip_address,
            device_type=self.type,
            ports=self.check_ports,
            use_ping_fallback=self.use_ping_fallback
        )
        
        # Update device state based on check results
        if result['status'] == 'online':
            self.last_connectivity = now()
            self.save(update_fields=['last_connectivity', 'last_check_attempt', 'connectivity_error'])
            return True
        else:
            self.connectivity_error = result.get('error', 'Device is unreachable')
            self.save(update_fields=['last_check_attempt', 'connectivity_error'])
            return False
        
    
    
    
    
    def check_router_internet_connectivity(self):
        """
        For router devices, attempt to verify they have internet connectivity
        by checking common router APIs or interfaces
        """
        import requests
        from requests.exceptions import RequestException
        
        # Common router status URLs that might indicate internet status
        router_urls = [
            f"http://{self.ip_address}/status.html",
            f"http://{self.ip_address}/router_status.cgi",
            f"http://{self.ip_address}/cgi-bin/luci/admin/status/overview",
            f"http://{self.ip_address}/internet_status.asp"
        ]
        
        # Try each URL to see if we can get router status
        for url in router_urls:
            try:
                response = requests.get(url, timeout=2, verify=False)
                if response.status_code == 200:
                    # Check if response contains indicators of internet connectivity
                    content = response.text.lower()
                    if any(term in content for term in ['internet connected', 'wan up', 'online status: connected']):
                        return True
            except RequestException:
                continue
                
        # If no status page found, try probing the router's DNS functionality
        try:
            # Configure DNS resolution to use the router
            original_nameserver = socket.gethostbyname_ex
            
            def custom_resolver(host):
                return socket.getaddrinfo(host, None, family=socket.AF_INET, proto=socket.IPPROTO_TCP)
            
            # Test if router can resolve a reliable domain
            socket.gethostbyname_ex = custom_resolver
            try:
                socket.gethostbyname("www.google.com")
                return True
            except socket.gaierror:
                return False
            finally:
                # Restore original resolver
                socket.gethostbyname_ex = original_nameserver
        except Exception:
            pass
            
        # Default to true for routers that pass basic connectivity checks
        # but don't have accessible status pages
        return True