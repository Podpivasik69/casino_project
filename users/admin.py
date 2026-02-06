from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Profile

# Register your models here.

class ProfileInline(admin.StackedInline):
    """Inline admin for Profile"""
    model = Profile
    can_delete = False
    verbose_name_plural = 'Профиль'
    fields = ('balance', 'total_wagered', 'total_won', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')


class UserAdmin(BaseUserAdmin):
    """Custom User admin with Profile inline"""
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_balance')
    
    def get_balance(self, obj):
        """Display user balance in list"""
        return f"{obj.profile.balance} ₽" if hasattr(obj, 'profile') else 'N/A'
    get_balance.short_description = 'Баланс'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Admin for Profile model"""
    list_display = ('user', 'balance', 'total_wagered', 'total_won', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Пользователь', {
            'fields': ('user',)
        }),
        ('Финансы', {
            'fields': ('balance', 'total_wagered', 'total_won')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )


# Register custom User admin
admin.site.register(User, UserAdmin)
