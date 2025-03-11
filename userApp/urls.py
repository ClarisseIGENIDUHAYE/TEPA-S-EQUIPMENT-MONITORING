from django.urls import path
from .views import (
    register_user,
    login_user,
    reset_password,
    list_all_users,
    get_user_by_email,
    get_user_by_id,
    get_user_by_phone,
    update_user,
    delete_user_by_id,
    contact_us,
    activate_user,
    deactivate_user,
    index,
    get_login_form,
    get_forgetpassword_page,
    get_admin,
    get_updateForm,

)

urlpatterns = [
    # User Registration
    path('register/', register_user, name='register_user'),
    path('', index, name='index'),
    path('get_login/', get_login_form, name='get_login'),
    
    # User Login
    path('login/', login_user, name='login_user'),
    path('forgetpassword', get_forgetpassword_page, name='forgetpassword'),
   
    
    # Reset Password
    path('forget_password/', reset_password, name='reset_password'),
    path('get_updateForm', get_updateForm, name='get_updateForm'),
    
    path("adminDashboard/", get_admin, name="adminDashboard"),
    
    # User Management
    path('users/', list_all_users, name='list_all_users'),  # List all users (admin only)
    path('user/<int:user_id>/', get_user_by_id, name='get_user_by_id'),  # Get a user by ID
    path('update/', update_user, name='update_user'),  # Update a user
    path('activate/<int:user_id>/', activate_user, name='activate_user'),
    path('diactivate/<int:user_id>/', deactivate_user, name='diactivate_user'),
    path('delete/<int:user_id>/', delete_user_by_id, name='delete_user_by_id'),  # Delete a user by ID
    path('email/', get_user_by_email, name='get_user_by_email'),  # Get a user by email
    path('phone/', get_user_by_phone, name='get_user_by_phone'),  # Get a user by phone number
    path('contact/', contact_us, name='contact'),

]