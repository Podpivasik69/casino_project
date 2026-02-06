from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal

# Create your models here.

class User(AbstractUser):
    """
    Extended Django user model.
    Uses Django's built-in authentication.
    """
    email = models.EmailField(unique=True, blank=False, null=False)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
    
    def __str__(self):
        return self.username


class Profile(models.Model):
    """
    User profile with demo balance and statistics.
    One-to-one relationship with User.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Пользователь'
    )
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('1000.00'),
        verbose_name='Баланс'
    )
    total_wagered = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Всего поставлено'
    )
    total_won = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='Всего выиграно'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    
    class Meta:
        db_table = 'profiles'
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'
        constraints = [
            models.CheckConstraint(
                check=models.Q(balance__gte=0),
                name='balance_non_negative'
            ),
            models.CheckConstraint(
                check=models.Q(total_wagered__gte=0),
                name='total_wagered_non_negative'
            ),
            models.CheckConstraint(
                check=models.Q(total_won__gte=0),
                name='total_won_non_negative'
            ),
        ]
    
    def __str__(self):
        return f"Profile of {self.user.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to automatically create Profile when User is created.
    """
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Signal to save Profile when User is saved.
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()

