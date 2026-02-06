"""
Admin configuration for games app.
"""
from django.contrib import admin
from .models import MinesGame


@admin.register(MinesGame)
class MinesGameAdmin(admin.ModelAdmin):
    """Admin interface for MinesGame"""
    
    list_display = [
        'id',
        'user',
        'bet_amount',
        'mine_count',
        'state',
        'current_multiplier',
        'opened_cells_count',
        'created_at'
    ]
    
    list_filter = [
        'state',
        'mine_count',
        'created_at'
    ]
    
    search_fields = [
        'user__username',
        'user__email'
    ]
    
    readonly_fields = [
        'id',
        'user',
        'bet_amount',
        'mine_count',
        'state',
        'opened_cells',
        'current_multiplier',
        'server_seed',
        'client_seed',
        'nonce',
        'server_seed_hash',
        'mine_positions',
        'created_at',
        'ended_at'
    ]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'user', 'bet_amount', 'mine_count', 'state')
        }),
        ('Игровое состояние', {
            'fields': ('opened_cells', 'current_multiplier')
        }),
        ('Provably Fair', {
            'fields': (
                'server_seed',
                'client_seed',
                'nonce',
                'server_seed_hash',
                'mine_positions'
            )
        }),
        ('Временные метки', {
            'fields': ('created_at', 'ended_at')
        }),
    )
    
    def opened_cells_count(self, obj):
        """Display number of opened cells"""
        return obj.get_opened_cells_count()
    opened_cells_count.short_description = 'Открыто клеток'
    
    def has_add_permission(self, request):
        """Disable manual creation in admin"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable deletion in admin"""
        return False
