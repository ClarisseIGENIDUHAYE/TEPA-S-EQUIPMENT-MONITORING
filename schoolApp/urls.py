from django.urls import path
from .views import (
    create_school, get_all_schools, get_school_by_id,
    update_school, delete_school, get_schools_by_user,
    display_schools_page, get_createSchool_page,
)

urlpatterns = [
    
    path('display_schools_page/', display_schools_page, name='display_schools_page'),
    path('schools/', get_all_schools, name='get_all_schools'),
    
    path('get_createSchool_page', get_createSchool_page, name='get_createSchool_page'),
    path('create/', create_school, name='create_school'),
    path('<int:school_id>/', get_school_by_id, name='get_school_by_id'),
    path('update/<int:school_id>/', update_school, name='update_school'),
    path('delete/<int:school_id>/', delete_school, name='delete_school'),
    path('my-schools/', get_schools_by_user, name='get_schools_by_user'),
]
