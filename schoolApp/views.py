from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import School
from .serializers import SchoolSerializer
from django.shortcuts import render

def display_schools_page(request):
    return render(request, 'school/allSchools.html')


def get_createSchool_page(request):
    return render(request, 'school/createSchool.html')

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_school(request):
    """Create a new school with validations"""
    try:
        index_number = request.data.get('index_number')
        name = request.data.get('name')
        province = request.data.get('province')
        district = request.data.get('district')

        # Validation
        if not index_number or not name or not province or not district:
            return Response({"error": "All fields (index_number, name, province, district) are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Check for duplicate school
        if School.objects.filter(index_number=index_number, province=province, district=district).exists():
            return Response({"error": "A school with the same index number, province, and district already exists."},
                            status=status.HTTP_400_BAD_REQUEST)

        school = School.objects.create(
            index_number=index_number,
            name=name,
            province=province,
            district=district,
            created_by=request.user
        )
        return Response(SchoolSerializer(school).data, status=status.HTTP_201_CREATED)

    except IntegrityError:
        return Response({"error": "A school with this index number already exists."}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": f"An unexpected error occurred: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_all_schools(request):
    """Retrieve all schools"""
    try:
        schools = School.objects.all()
        serializer = SchoolSerializer(schools, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": f"An unexpected error occurred: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_school_by_id(request, school_id):
    """Retrieve school by ID"""
    try:
        school = get_object_or_404(School, id=school_id)
        return Response(SchoolSerializer(school).data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": f"An unexpected error occurred: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def update_school(request, school_id):
    """Update school details"""
    try:
        school = get_object_or_404(School, id=school_id)

        # Only allow the creator of the school to update it
        if school.created_by != request.user:
            return Response({"error": "You are not allowed to update this school."},
                            status=status.HTTP_403_FORBIDDEN)

        index_number = request.data.get('index_number', school.index_number)
        name = request.data.get('name', school.name)
        province = request.data.get('province', school.province)
        district = request.data.get('district', school.district)

        # Check for duplicate school if index_number, province, and district change
        if School.objects.filter(index_number=index_number, province=province, district=district).exclude(id=school_id).exists():
            return Response({"error": "A school with the same index number, province, and district already exists."},
                            status=status.HTTP_400_BAD_REQUEST)

        school.index_number = index_number
        school.name = name
        school.province = province
        school.district = district
        school.save()

        return Response(SchoolSerializer(school).data, status=status.HTTP_200_OK)

    except IntegrityError:
        return Response({"error": "A school with these details already exists."}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": f"An unexpected error occurred: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_school(request, school_id):
    """Delete a school"""
    try:
        school = get_object_or_404(School, id=school_id)

        # Only allow the creator of the school to delete it
        if school.created_by != request.user:
            return Response({"error": "You are not allowed to delete this school."},
                            status=status.HTTP_403_FORBIDDEN)

        school.delete()
        return Response({"message": "School deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

    except Exception as e:
        return Response({"error": f"An unexpected error occurred: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_schools_by_user(request):
    """Retrieve all schools created by the logged-in user"""
    try:
        schools = School.objects.filter(created_by=request.user)
        serializer = SchoolSerializer(schools, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": f"An unexpected error occurred: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
