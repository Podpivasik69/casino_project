from django.contrib import admin
from .models import Transaction

# Register your models here.

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin interface for Transaction model"""
    
    list_display = (
        'id',
        'user',
        'transaction_type',
        'formatted_amount',
        'balance_before',
        'balance_after',
        'status',
        'created_at'
    )
    
    list_filter = (
        'transaction_type',
        'status',
        'created_at',
    )
    
    search_fields = (
        'user__username',
        'user__email',
        'description',
    )
    
    readonly_fields = (
        'created_at',
        'balance_before',
        'balance_after',
    )
    
    fieldsets = (
        ('Пользователь', {
            'fields': ('user',)
        }),
        ('Детали транзакции', {
            'fields': ('transaction_type', 'amount', 'description', 'status')
        }),
        ('Баланс', {
            'fields': ('balance_before', 'balance_after')
        }),
        ('Даты', {
            'fields': ('created_at',)
        }),
    )
    
    date_hierarchy = 'created_at'
    
    def formatted_amount(self, obj):
        """Display amount with sign"""
        return obj.get_amount_display()
    formatted_amount.short_description = 'Сумма'
    
    def has_add_permission(self, request):
        """Disable manual transaction creation in admin"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable transaction deletion in admin"""
        return False
