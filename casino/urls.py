"""
URL configuration for casino project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Page routes
    path('', views.home_view, name='home'),
    path('login/', views.login_page, name='login'),
    path('register/', views.register_page, name='register'),
    path('profile/', views.profile_page, name='profile'),
    path('mines/', views.mines_game_page, name='mines'),
    path('plinko/', views.plinko_game_page, name='plinko'),
    path('dice/', views.dice_game_page, name='dice'),
    path('slots/', views.slots_game_page, name='slots'),
    
    # API endpoints
    path('api/auth/', include('users.urls', namespace='users')),
    path('api/wallet/', include('wallet.urls', namespace='wallet')),
    path('api/games/', include('games.urls', namespace='games')),
]
