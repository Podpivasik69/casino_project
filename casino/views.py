"""
Main views for the casino application.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


def home_view(request):
    """Home page"""
    return render(request, 'home.html')


def login_page(request):
    """Login page"""
    if request.user.is_authenticated:
        return redirect('/')
    return render(request, 'login.html')


def register_page(request):
    """Registration page"""
    if request.user.is_authenticated:
        return redirect('/')
    return render(request, 'register.html')


@login_required
def profile_page(request):
    """User profile page"""
    return render(request, 'profile.html')


@login_required
def mines_game_page(request):
    """Mines game page"""
    return render(request, 'mines.html')


@login_required
def plinko_game_page(request):
    """Plinko game page"""
    return render(request, 'plinko.html')


@login_required
def dice_game_page(request):
    """Dice game page"""
    return render(request, 'dice.html')


@login_required
def slots_game_page(request):
    """Slots game page"""
    return render(request, 'slots.html')
