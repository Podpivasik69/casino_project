"""
URL configuration for users app.
Handles authentication endpoints.
"""
from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Authentication endpoints
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('me/', views.current_user_view, name='current_user'),
    
    # Profile endpoints
    path('profile/', views.profile_view, name='profile'),
]
