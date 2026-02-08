# Generated manually to delete Crash models

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0006_crashround_crashbet'),
    ]

    operations = [
        migrations.DeleteModel(
            name='CrashBet',
        ),
        migrations.DeleteModel(
            name='CrashRound',
        ),
    ]
