"""
Slots game service.
"""
from decimal import Decimal
from django.db import transaction

from games.models import SlotsGame
from games.services.provably_fair import ProvablyFairService
from wallet.services import WalletService


class SlotsGameService:
    """Service for Slots game logic."""
    
    # Game constants
    MIN_BET = Decimal('0.01')
    MAX_BET = Decimal('10000.00')
    SYMBOLS = ['🍒', '🍋', '🍊', '⭐', '🔔', '7️⃣', '🎁']
    
    # Symbol weights for weighted random selection (RTP ~85%)
    SYMBOL_WEIGHTS = {
        '🍒': 30,   # 30% - самый частый
        '🍋': 24,   # 24%
        '🍊': 18,   # 18%
        '⭐': 12,   # 12%
        '🔔': 8,    # 8%
        '7️⃣': 5,    # 5%
        '🎁': 3,    # 3% - Wild символ (бонусный)
    }
    
    # Win multipliers for 3-reel mode (RTP ~82-85%)
    # 3 matching symbols
    MULTIPLIERS_3_MATCH = {
        '🍒': Decimal('4.50'),
        '🍋': Decimal('6.10'),
        '🍊': Decimal('9.00'),
        '⭐': Decimal('13.20'),
        '🔔': Decimal('22.50'),
        '7️⃣': Decimal('45.00'),
        '🎁': Decimal('28.00'),
    }
    
    # 2 matching symbols (partial win)
    MULTIPLIERS_2_MATCH = {
        '🍒': Decimal('1.12'),
        '🍋': Decimal('0.92'),
        '🍊': Decimal('1.32'),
        '⭐': Decimal('1.80'),
        '🔔': Decimal('2.25'),
        '7️⃣': Decimal('3.30'),
        '🎁': Decimal('1.32'),
    }
    
    # Win multipliers for 5-reel mode - BALANCED SYSTEM (RTP target: ~85%)
    # Format: {symbol: {2: multiplier, 3: multiplier, 4: multiplier, 5: multiplier}}
    # Multipliers < 1.0 = partial loss (player gets back less than bet)
    # Multiplier = 1.0 = return bet (no win/loss)
    # Multiplier > 1.0 = actual win
    # Philosophy: Frequent small wins keep players engaged, rare big wins create excitement
    MULTIPLIERS_5_REELS = {
        '🍒': {2: Decimal('0.5'), 3: Decimal('0.8'), 4: Decimal('2.0'), 5: Decimal('5.0')},
        '🍋': {2: Decimal('0.6'), 3: Decimal('1.0'), 4: Decimal('2.5'), 5: Decimal('7.0')},
        '🍊': {2: Decimal('0.7'), 3: Decimal('1.2'), 4: Decimal('3.5'), 5: Decimal('10.0')},
        '⭐': {2: Decimal('0.8'), 3: Decimal('1.8'), 4: Decimal('5.0'), 5: Decimal('15.0')},
        '🔔': {2: Decimal('1.0'), 3: Decimal('2.5'), 4: Decimal('6.5'), 5: Decimal('20.0')},
        '7️⃣': {2: Decimal('1.2'), 3: Decimal('3.5'), 4: Decimal('8.5'), 5: Decimal('30.0')},
    }
    
    # Win multipliers for 5-reel mode (5-of-a-kind) - OLD SYSTEM (keep for backwards compatibility)
    MULTIPLIERS_5X = {
        '7️⃣': Decimal('100.00'),
        '⭐': Decimal('50.00'),
        '🔔': Decimal('25.00'),
        '🍊': Decimal('15.00'),
        '🍋': Decimal('10.00'),
        '🍒': Decimal('5.00')
    }
    
    # Win multipliers for 5-reel mode (3-consecutive) - OLD SYSTEM (keep for backwards compatibility)
    MULTIPLIERS_3X = {
        '7️⃣': Decimal('20.00'),
        '⭐': Decimal('10.00'),
        '🔔': Decimal('5.00')
    }
    
    @classmethod
    def validate_bet(cls, bet_amount: Decimal) -> None:
        """Validate bet amount."""
        if bet_amount < cls.MIN_BET:
            raise ValueError(f'Минимальная ставка: {cls.MIN_BET}')
        if bet_amount > cls.MAX_BET:
            raise ValueError(f'Максимальная ставка: {cls.MAX_BET}')
    
    @classmethod
    def validate_reels_count(cls, reels_count: int) -> None:
        """Validate reels count."""
        if reels_count not in [3, 5]:
            raise ValueError('Количество барабанов должно быть 3 или 5')
    
    @classmethod
    def generate_reels(
        cls,
        server_seed: str,
        client_seed: str,
        nonce: int,
        reels_count: int = 5
    ) -> list:
        """Generate random symbols for reels using Provably Fair with weighted selection."""
        import hmac
        import hashlib
        
        # Create weighted symbol list
        weighted_symbols = []
        for symbol, weight in cls.SYMBOL_WEIGHTS.items():
            weighted_symbols.extend([symbol] * weight)
        
        total_weight = sum(cls.SYMBOL_WEIGHTS.values())
        
        reels = []
        for i in range(reels_count):
            # Create message for HMAC
            message = f"{client_seed}{nonce + i}".encode()
            
            # Generate HMAC-SHA256
            hmac_hash = hmac.new(
                server_seed.encode(),
                message,
                hashlib.sha256
            ).digest()
            
            # Use first 4 bytes to get random number
            rand_val = int.from_bytes(hmac_hash[:4], byteorder='big')
            
            # Map to weighted symbol index
            symbol_index = rand_val % total_weight
            reels.append(weighted_symbols[symbol_index])
        return reels
    
    @classmethod
    def check_win_5_reels_new(cls, reels: list) -> tuple:
        """
        Check for winning combinations in 5-reel mode with Wild symbol support.
        🎁 acts as Wild and replaces any symbol.
        Wild does NOT turn losses into wins - it only enhances combinations with multiplier >= 1.0x
        Returns: (multiplier, winning_combination_text)
        """
        from collections import Counter
        
        # Count each symbol (excluding Wild for now)
        non_wild_symbols = [s for s in reels if s != '🎁']
        wild_count = reels.count('🎁')
        
        # If all wilds, treat as special case (mega jackpot)
        if wild_count == 5:
            # 5 wilds = highest payout (use 7️⃣ multiplier)
            return (cls.MULTIPLIERS_5_REELS['7️⃣'][5], "5x 🎁 MEGA JACKPOT!")
        
        # If no non-wild symbols, no win
        if not non_wild_symbols:
            return (Decimal('0.00'), "")
        
        # Count non-wild symbols
        symbol_counts = Counter(non_wild_symbols)
        
        # Find the best winning combination
        best_multiplier = Decimal('0.00')
        best_combination = ""
        best_symbol = None
        best_count = 0
        
        for symbol, count in symbol_counts.items():
            # Add wild count to this symbol's count
            total_count = count + wild_count
            
            # Cap at 5
            if total_count > 5:
                total_count = 5
            
            # Check if this symbol has a multiplier for this count
            if symbol in cls.MULTIPLIERS_5_REELS and total_count >= 2:
                multiplier = cls.MULTIPLIERS_5_REELS[symbol].get(total_count, Decimal('0.00'))
                
                if multiplier > best_multiplier:
                    best_multiplier = multiplier
                    best_symbol = symbol
                    best_count = total_count
        
        # Build combination text and apply Wild bonus
        if best_multiplier > Decimal('0.00'):
            if wild_count > 0:
                # Wild bonus: only apply if base multiplier > 1.0 (actual win, not break-even)
                if best_multiplier > Decimal('1.0') and best_count >= 3:
                    # Apply Wild bonus: multiply by 1.2x
                    best_multiplier = best_multiplier * Decimal('1.2')
                    best_combination = f"{best_count}x {best_symbol} + 🎁 БОНУС!"
                else:
                    # Wild used but no bonus (loss or break-even)
                    best_combination = f"{best_count}x {best_symbol} (с 🎁)"
            else:
                best_combination = f"{best_count}x {best_symbol}"
        
        return (best_multiplier, best_combination)
    
    @classmethod
    def check_win(cls, reels: list, reels_count: int) -> tuple:
        """Check for winning combinations."""
        if reels_count == 3:
            # Count occurrences of each symbol
            from collections import Counter
            symbol_counts = Counter(reels)
            
            # Check for 🎁 bonus multiplier
            has_bonus = '🎁' in reels
            bonus_count = symbol_counts.get('🎁', 0)
            
            # Special case: 🎁🎁🎁
            if bonus_count == 3:
                return (cls.MULTIPLIERS_3_MATCH['🎁'], "3x 🎁 ДЖЕКПОТ!")
            
            # Special case: 🎁🎁 + any
            if bonus_count == 2:
                return (cls.MULTIPLIERS_2_MATCH['🎁'], "2x 🎁")
            
            # Find the most common non-bonus symbol
            non_bonus_symbols = [s for s in reels if s != '🎁']
            
            if len(non_bonus_symbols) == 0:
                # Only bonus symbols (already handled above)
                return (Decimal('0.00'), "")
            
            non_bonus_counts = Counter(non_bonus_symbols)
            most_common_symbol, most_common_count = non_bonus_counts.most_common(1)[0]
            
            # Check for 3 matching (with or without bonus)
            if most_common_count == 3:
                base_multiplier = cls.MULTIPLIERS_3_MATCH.get(most_common_symbol, Decimal('0.00'))
                if base_multiplier > 0:
                    return (base_multiplier, f"3x {most_common_symbol}")
            
            # Check for 2 matching + bonus
            if most_common_count == 2 and has_bonus:
                base_multiplier = cls.MULTIPLIERS_2_MATCH.get(most_common_symbol, Decimal('0.00'))
                if base_multiplier > 0:
                    # Apply bonus multiplier ×1.5
                    final_multiplier = base_multiplier * Decimal('1.5')
                    return (final_multiplier, f"2x {most_common_symbol} + 🎁 БОНУС!")
            
            # Check for 2 matching (without bonus)
            if most_common_count == 2:
                base_multiplier = cls.MULTIPLIERS_2_MATCH.get(most_common_symbol, Decimal('0.00'))
                if base_multiplier > 0:
                    return (base_multiplier, f"2x {most_common_symbol}")
            
            # No win
            return (Decimal('0.00'), "")
        
        elif reels_count == 5:
            # Use new system with Wild support
            return cls.check_win_5_reels_new(reels)
        
        # No win
        return (Decimal('0.00'), "")
    
    @classmethod
    def calculate_payout(cls, bet_amount: Decimal, multiplier: Decimal) -> Decimal:
        """Calculate payout amount."""
        return bet_amount * multiplier
    
    @classmethod
    @transaction.atomic
    def create_and_play_game(
        cls,
        user,
        bet_amount: Decimal,
        reels_count: int = 5,
        client_seed: str = None
    ) -> SlotsGame:
        """Create and play a slots game."""
        # Validate inputs
        cls.validate_bet(bet_amount)
        cls.validate_reels_count(reels_count)
        
        # Place bet
        WalletService.place_bet(
            user=user,
            amount=bet_amount,
            description=f'Ставка в Slots: {reels_count} барабанов'
        )
        
        # Generate provably fair seeds
        server_seed = ProvablyFairService.generate_server_seed()
        server_seed_hash = ProvablyFairService.hash_seed(server_seed)
        if not client_seed:
            client_seed = ProvablyFairService.generate_client_seed()
        nonce = 0
        
        # Generate reels
        reels = cls.generate_reels(
            server_seed=server_seed,
            client_seed=client_seed,
            nonce=nonce,
            reels_count=reels_count
        )
        
        # Check for win
        multiplier, winning_combination = cls.check_win(reels, reels_count)
        
        # Calculate win amount
        win_amount = cls.calculate_payout(bet_amount, multiplier) if multiplier > 0 else Decimal('0.00')
        
        # Create game record
        game = SlotsGame.objects.create(
            user=user,
            bet_amount=bet_amount,
            reels_count=reels_count,
            reels=reels,
            multiplier=multiplier,
            win_amount=win_amount,
            winning_combination=winning_combination,
            server_seed=server_seed,
            client_seed=client_seed,
            nonce=nonce,
            server_seed_hash=server_seed_hash
        )
        
        # Add winnings if won
        if win_amount > 0:
            WalletService.add_winnings(
                user=user,
                amount=win_amount,
                description=f'Выигрыш в Slots ({reels_count} барабанов, x{multiplier})'
            )
        
        return game
    
    @classmethod
    def get_user_games(cls, user, limit: int = 10):
        """Get user's recent slots games."""
        return SlotsGame.objects.filter(user=user).order_by('-created_at')[:limit]
    
    @classmethod
    def get_game_by_id(cls, game_id: int, user=None):
        """Get game by ID."""
        try:
            if user:
                return SlotsGame.objects.get(id=game_id, user=user)
            return SlotsGame.objects.get(id=game_id)
        except SlotsGame.DoesNotExist:
            return None
    
    @classmethod
    def verify_game(cls, game: SlotsGame) -> bool:
        """Verify game result using provably fair."""
        expected_reels = cls.generate_reels(
            server_seed=game.server_seed,
            client_seed=game.client_seed,
            nonce=game.nonce,
            reels_count=game.reels_count
        )
        return expected_reels == game.reels
