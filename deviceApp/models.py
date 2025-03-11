# deviceApp/models.py
from django.db import models
from django.utils.timezone import now
from schoolApp.models import School
from userApp.models import CustomUser

class Device(models.Model):
    DEVICE_TYPES = (
        ('router', 'Router'),
        ('phone', 'Phone'),
        ('pc', 'PC'),
        ('laptop', 'Laptop'),
        ('tablet', 'Tablet'),
        ('other', 'Other'),
    )
    
    STATUS_CHOICES = (
        ('online', 'Online'),
        ('offline', 'Offline'),
    )
    
    name = models.CharField(max_length=255)
    mac_address = models.CharField(max_length=100, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    type = models.CharField(max_length=50, choices=DEVICE_TYPES)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='unknown')
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='devices')
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='devices')
    created_at = models.DateTimeField(default=now)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.type}) - {self.school.name}"
    
    class Meta:
        ordering = ['-last_updated']