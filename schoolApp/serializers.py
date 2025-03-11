from rest_framework import serializers
from .models import School, CustomUser

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'phone_number', 'email', 'role', 'profile_picture']

class SchoolSerializer(serializers.ModelSerializer):
    created_by = CustomUserSerializer(read_only=True)

    class Meta:
        model = School
        fields = ['id', 'index_number', 'name', 'province', 'district', 'created_by', 'created_at']

