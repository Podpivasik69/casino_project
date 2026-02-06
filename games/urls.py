"""
URL configuration for games app.
Handles Mines and Plinko game endpoints.
"""
from django.urls import path
from .views import mines_views, plinko_views

app_name = 'games'

urlpatterns = [
    # Mines game endpoints
    path('mines/create/', mines_views.create_mines_game, name='mines_create'),
    path('mines/<int:game_id>/', mines_views.get_game, name='mines_get'),
    path('mines/<int:game_id>/open/', mines_views.open_cell, name='mines_open'),
    path('mines/<int:game_id>/cashout/', mines_views.cashout_game, name='mines_cashout'),
    path('mines/<int:game_id>/verify/', mines_views.verify_game, name='mines_verify'),
    
    # Plinko game endpoints
    path('plinko/create/', plinko_views.create_plinko_game, name='plinko_create'),
    path('plinko/<int:game_id>/', plinko_views.get_plinko_game, name='plinko_get'),
    path('plinko/<int:game_id>/drop/', plinko_views.drop_ball, name='plinko_drop'),
    path('plinko/auto/', plinko_views.auto_play, name='plinko_auto'),
    path('plinko/multipliers/', plinko_views.get_multipliers, name='plinko_multipliers'),
]
