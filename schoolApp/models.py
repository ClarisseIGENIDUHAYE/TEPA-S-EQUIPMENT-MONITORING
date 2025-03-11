from django.db import models
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from userApp.models import CustomUser

class School(models.Model):
    index_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    province = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="schools")
    created_at = models.DateTimeField(default=now)

    class Meta:
        unique_together = ('index_number', 'province', 'district')  # Prevent duplicate schools

    def __str__(self):
        return self.name
