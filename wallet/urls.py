"""
URL configuration for wallet app.
Handles wallet and transaction endpoints.
"""
from django.urls import path
from . import views

app_name = 'wallet'

urlpatterns = [
    # Balance
    path('balance/', views.get_balance, name='balance'),
    
    # Deposit
    path('deposit/', views.demo_deposit, name='deposit'),
    
    # Transactions
    path('transactions/', views.get_transactions, name='transactions'),
    
    # Summary
    path('summary/', views.get_balance_summary, name='summary'),
]
