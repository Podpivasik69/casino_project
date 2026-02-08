"""
Management command to run crash game rounds automatically.

Usage:
    python manage.py run_crash_rounds
"""
import time
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from games.services.crash_service import CrashGameService
from games.models import CrashRound


class Command(BaseCommand):
    help = 'Run crash game rounds automatically'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Crash Game Round Manager...'))
        
        try:
            while True:
                self.process_rounds()
                time.sleep(0.1)  # Check every 100ms
                
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nStopping Crash Game Round Manager...'))
    
    def process_rounds(self):
        """Process current round state"""
        current_round = CrashGameService.get_current_round()
        
        # No round exists - create new one
        if not current_round:
            self.stdout.write('No active round. Creating new round...')
            round_instance = CrashGameService.start_new_round()
            self.stdout.write(self.style.SUCCESS(
                f'Round {round_instance.round_id} created. Crash point: {round_instance.crash_point}x'
            ))
            return
        
        # Round is waiting - check if it's time to activate
        if current_round.is_waiting():
            if current_round.next_round_at and timezone.now() >= current_round.next_round_at:
                self.stdout.write(f'Activating round {current_round.round_id}...')
                CrashGameService.activate_round(current_round)
                self.stdout.write(self.style.SUCCESS('Round activated!'))
            return
        
        # Round is active - check multiplier and process
        if current_round.is_active():
            current_multiplier = CrashGameService.get_current_multiplier(current_round)
            
            # Process auto cashouts
            auto_cashouts = CrashGameService.process_auto_cashouts(current_round, current_multiplier)
            if auto_cashouts > 0:
                self.stdout.write(f'Processed {auto_cashouts} auto-cashouts at {current_multiplier}x')
            
            # Check if we've reached crash point
            if current_multiplier >= current_round.crash_point:
                self.stdout.write(self.style.ERROR(
                    f'CRASH! Round {current_round.round_id} crashed at {current_round.crash_point}x'
                ))
                CrashGameService.crash_round(current_round)
                
                # Create next round immediately
                time.sleep(1)  # Brief pause
                next_round = CrashGameService.start_new_round()
                self.stdout.write(self.style.SUCCESS(
                    f'Next round {next_round.round_id} created. Crash point: {next_round.crash_point}x'
                ))
            return
        
        # Round is crashed - create new one
        if current_round.is_crashed():
            self.stdout.write('Round crashed. Creating new round...')
            round_instance = CrashGameService.start_new_round()
            self.stdout.write(self.style.SUCCESS(
                f'Round {round_instance.round_id} created. Crash point: {round_instance.crash_point}x'
            ))
            return
