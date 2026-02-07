"""
Tests for Dice game service.
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from games.models import DiceGame
from games.services.dice_service import DiceGameService
from users.models import Profile
from wallet.services import InsufficientFundsError

User = get_user_model()


class DiceGameServiceTest(TestCase):
    """Test DiceGameService"""
    
    def setUp(self):
        """Set up test user"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Set initial balance
        self.user.profile.balance = Decimal('1000.00')
        self.user.profile.save()
    
    def test_validate_bet_min(self):
        """Test bet validation - minimum"""
        with self.assertRaises(ValueError):
            DiceGameService.validate_bet(Decimal('0.00'))
    
    def test_validate_bet_max(self):
        """Test bet validation - maximum"""
        with self.assertRaises(ValueError):
            DiceGameService.validate_bet(Decimal('10001.00'))
    
    def test_validate_bet_valid(self):
        """Test bet validation - valid"""
        # Should not raise
        DiceGameService.validate_bet(Decimal('10.00'))
    
    def test_validate_selected_number_invalid_type(self):
        """Test selected number validation - invalid type"""
        with self.assertRaises(ValueError):
            DiceGameService.validate_selected_number('3')
    
    def test_validate_selected_number_too_low(self):
        """Test selected number validation - too low"""
        with self.assertRaises(ValueError):
            DiceGameService.validate_selected_number(0)
    
    def test_validate_selected_number_too_high(self):
        """Test selected number validation - too high"""
        with self.assertRaises(ValueError):
            DiceGameService.validate_selected_number(7)
    
    def test_validate_selected_number_valid(self):
        """Test selected number validation - valid"""
        # Should not raise
        for num in range(1, 7):
            DiceGameService.validate_selected_number(num)
    
    def test_create_and_play_game_insufficient_balance(self):
        """Test game creation with insufficient balance"""
        self.user.profile.balance = Decimal('5.00')
        self.user.profile.save()
        
        with self.assertRaises(InsufficientFundsError):
            DiceGameService.create_and_play_game(
                user=self.user,
                bet_amount=Decimal('10.00'),
                selected_number=3
            )
    
    def test_create_and_play_game_success(self):
        """Test successful game creation and play"""
        initial_balance = self.user.profile.balance
        bet_amount = Decimal('10.00')
        selected_number = 3
        
        game = DiceGameService.create_and_play_game(
            user=self.user,
            bet_amount=bet_amount,
            selected_number=selected_number
        )
        
        # Check game was created
        self.assertIsNotNone(game)
        self.assertEqual(game.user, self.user)
        self.assertEqual(game.bet_amount, bet_amount)
        self.assertEqual(game.selected_number, selected_number)
        
        # Check rolled number is valid
        self.assertIn(game.rolled_number, range(1, 7))
        
        # Check multiplier
        if game.won:
            self.assertEqual(game.multiplier, DiceGameService.WIN_MULTIPLIER)
            self.assertEqual(game.rolled_number, selected_number)
        else:
            self.assertEqual(game.multiplier, DiceGameService.LOSE_MULTIPLIER)
            self.assertNotEqual(game.rolled_number, selected_number)
        
        # Check provably fair fields
        self.assertIsNotNone(game.server_seed)
        self.assertIsNotNone(game.client_seed)
        self.assertIsNotNone(game.server_seed_hash)
        self.assertEqual(game.nonce, 0)
        
        # Check balance was updated
        self.user.profile.refresh_from_db()
        if game.won:
            expected_balance = initial_balance + (bet_amount * DiceGameService.WIN_MULTIPLIER) - bet_amount
        else:
            expected_balance = initial_balance - bet_amount
        self.assertEqual(self.user.profile.balance, expected_balance)
    
    def test_create_and_play_game_with_custom_client_seed(self):
        """Test game creation with custom client seed"""
        game = DiceGameService.create_and_play_game(
            user=self.user,
            bet_amount=Decimal('10.00'),
            selected_number=3,
            client_seed='custom_seed_123'
        )
        
        self.assertEqual(game.client_seed, 'custom_seed_123')
    
    def test_get_user_games(self):
        """Test getting user's games"""
        # Create multiple games
        for i in range(5):
            DiceGameService.create_and_play_game(
                user=self.user,
                bet_amount=Decimal('10.00'),
                selected_number=(i % 6) + 1
            )
        
        # Get games
        games = DiceGameService.get_user_games(self.user, limit=3)
        
        self.assertEqual(len(games), 3)
        # Check they're ordered by created_at descending
        for i in range(len(games) - 1):
            self.assertGreaterEqual(games[i].created_at, games[i + 1].created_at)
    
    def test_get_game_by_id(self):
        """Test getting game by ID"""
        game = DiceGameService.create_and_play_game(
            user=self.user,
            bet_amount=Decimal('10.00'),
            selected_number=3
        )
        
        # Get by ID
        retrieved_game = DiceGameService.get_game_by_id(game.id)
        self.assertEqual(retrieved_game.id, game.id)
        
        # Get by ID with user filter
        retrieved_game = DiceGameService.get_game_by_id(game.id, user=self.user)
        self.assertEqual(retrieved_game.id, game.id)
        
        # Try to get with wrong user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        retrieved_game = DiceGameService.get_game_by_id(game.id, user=other_user)
        self.assertIsNone(retrieved_game)
    
    def test_verify_game(self):
        """Test game verification"""
        game = DiceGameService.create_and_play_game(
            user=self.user,
            bet_amount=Decimal('10.00'),
            selected_number=3
        )
        
        # Verify game
        is_valid = DiceGameService.verify_game(game)
        self.assertTrue(is_valid)
    
    def test_game_deterministic(self):
        """Test that same seeds produce same result"""
        from games.services.provably_fair import ProvablyFairService
        
        server_seed = 'test_server_seed'
        client_seed = 'test_client_seed'
        nonce = 0
        
        # Generate multiple times
        results = []
        for _ in range(10):
            result = ProvablyFairService.generate_dice_roll(
                server_seed=server_seed,
                client_seed=client_seed,
                nonce=nonce
            )
            results.append(result)
        
        # All results should be the same
        self.assertEqual(len(set(results)), 1)
        self.assertIn(results[0], range(1, 7))
    
    def test_game_distribution(self):
        """Test that dice rolls are distributed across 1-6"""
        from games.services.provably_fair import ProvablyFairService
        
        server_seed = 'test_server_seed'
        client_seed = 'test_client_seed'
        
        results = []
        for nonce in range(100):
            result = ProvablyFairService.generate_dice_roll(
                server_seed=server_seed,
                client_seed=client_seed,
                nonce=nonce
            )
            results.append(result)
        
        # Check all numbers appear
        unique_results = set(results)
        self.assertEqual(len(unique_results), 6)
        self.assertEqual(unique_results, {1, 2, 3, 4, 5, 6})
