"""
URL configuration for games app.
Handles Mines, Plinko, Dice, Slots, and Crash game endpoints.
"""
from django.urls import path
from .views import mines_views, plinko_views, dice_views, slots_views, crash_views

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
    
    # Dice game endpoints
    path('dice/create/', dice_views.create_game, name='dice_create'),
    path('dice/history/', dice_views.get_history, name='dice_history'),
    path('dice/<int:game_id>/', dice_views.get_game, name='dice_get'),
    path('dice/verify/', dice_views.verify_game, name='dice_verify'),
    
    # Slots game endpoints
    path('slots/create/', slots_views.create_game, name='slots_create'),
    path('slots/history/', slots_views.get_history, name='slots_history'),
    path('slots/<int:game_id>/', slots_views.get_game, name='slots_get'),
    path('slots/verify/', slots_views.verify_game, name='slots_verify'),
    
    # Crash game endpoints
    path('crash/current/', crash_views.current_round, name='crash_current'),
    path('crash/bet/', crash_views.place_bet, name='crash_bet'),
    path('crash/cashout/', crash_views.cashout, name='crash_cashout'),
    path('crash/history/', crash_views.round_history, name='crash_history'),
]
