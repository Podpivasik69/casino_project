"""
Tests for Dice game API endpoints.
"""
import json
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from games.models import DiceGame
from games.services.dice_service import DiceGameService

User = get_user_model()


class DiceAPITest(TestCase):
    """Test Dice API endpoints"""
    
    def setUp(self):
        """Set up test client and user"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user.profile.balance = Decimal('1000.00')
        self.user.profile.save()
        
        # Login
        self.client.login(username='testuser', password='testpass123')
    
    def test_create_game_success(self):
        """Test successful game creation"""
        response = self.client.post(
            '/api/games/dice/create/',
            data=json.dumps({
                'bet_amount': '10.00',
                'selected_number': 3
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        
        game_data = data['data']
        self.assertIn('game_id', game_data)
        self.assertEqual(game_data['bet_amount'], '10.00')
        self.assertEqual(game_data['selected_number'], 3)
        self.assertIn(game_data['rolled_number'], range(1, 7))
        self.assertIn('multiplier', game_data)
        self.assertIn('won', game_data)
        self.assertIn('winnings', game_data)
        self.assertIn('balance', game_data)
        self.assertIn('server_seed_hash', game_data)
        self.assertIn('client_seed', game_data)
        self.assertIn('nonce', game_data)
    
    def test_create_game_with_custom_client_seed(self):
        """Test game creation with custom client seed"""
        response = self.client.post(
            '/api/games/dice/create/',
            data=json.dumps({
                'bet_amount': '10.00',
                'selected_number': 3,
                'client_seed': 'my_custom_seed'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['client_seed'], 'my_custom_seed')
    
    def test_create_game_invalid_bet(self):
        """Test game creation with invalid bet"""
        response = self.client.post(
            '/api/games/dice/create/',
            data=json.dumps({
                'bet_amount': '0.00',
                'selected_number': 3
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_create_game_invalid_number(self):
        """Test game creation with invalid number"""
        response = self.client.post(
            '/api/games/dice/create/',
            data=json.dumps({
                'bet_amount': '10.00',
                'selected_number': 7
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_create_game_insufficient_balance(self):
        """Test game creation with insufficient balance"""
        self.user.profile.balance = Decimal('5.00')
        self.user.profile.save()
        
        response = self.client.post(
            '/api/games/dice/create/',
            data=json.dumps({
                'bet_amount': '10.00',
                'selected_number': 3
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_create_game_unauthenticated(self):
        """Test game creation without authentication"""
        self.client.logout()
        
        response = self.client.post(
            '/api/games/dice/create/',
            data=json.dumps({
                'bet_amount': '10.00',
                'selected_number': 3
            }),
            content_type='application/json'
        )
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_get_history(self):
        """Test getting game history"""
        # Create some games
        for i in range(5):
            DiceGameService.create_and_play_game(
                user=self.user,
                bet_amount=Decimal('10.00'),
                selected_number=(i % 6) + 1
            )
        
        response = self.client.get('/api/games/dice/history/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        self.assertIn('games', data['data'])
        self.assertIn('total', data['data'])
        
        games = data['data']['games']
        self.assertEqual(len(games), 5)
        
        # Check game structure
        game = games[0]
        self.assertIn('game_id', game)
        self.assertIn('bet_amount', game)
        self.assertIn('selected_number', game)
        self.assertIn('rolled_number', game)
        self.assertIn('multiplier', game)
        self.assertIn('won', game)
        self.assertIn('winnings', game)
        self.assertIn('created_at', game)
    
    def test_get_history_with_limit(self):
        """Test getting game history with limit"""
        # Create 10 games
        for i in range(10):
            DiceGameService.create_and_play_game(
                user=self.user,
                bet_amount=Decimal('10.00'),
                selected_number=(i % 6) + 1
            )
        
        response = self.client.get('/api/games/dice/history/?limit=3')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']['games']), 3)
    
    def test_get_history_unauthenticated(self):
        """Test getting history without authentication"""
        self.client.logout()
        
        response = self.client.get('/api/games/dice/history/')
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_get_game(self):
        """Test getting specific game"""
        game = DiceGameService.create_and_play_game(
            user=self.user,
            bet_amount=Decimal('10.00'),
            selected_number=3
        )
        
        response = self.client.get(f'/api/games/dice/{game.id}/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        
        game_data = data['data']
        self.assertEqual(game_data['game_id'], game.id)
        self.assertEqual(game_data['bet_amount'], str(game.bet_amount))
        self.assertEqual(game_data['selected_number'], game.selected_number)
        self.assertEqual(game_data['rolled_number'], game.rolled_number)
        self.assertIn('server_seed', game_data)
        self.assertIn('server_seed_hash', game_data)
        self.assertIn('client_seed', game_data)
        self.assertIn('nonce', game_data)
    
    def test_get_game_not_found(self):
        """Test getting non-existent game"""
        response = self.client.get('/api/games/dice/99999/')
        
        self.assertEqual(response.status_code, 404)
        data = response.json()
        
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_get_game_other_user(self):
        """Test getting another user's game"""
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        other_user.profile.balance = Decimal('1000.00')
        other_user.profile.save()
        
        # Create game for other user
        game = DiceGameService.create_and_play_game(
            user=other_user,
            bet_amount=Decimal('10.00'),
            selected_number=3
        )
        
        # Try to get it as current user
        response = self.client.get(f'/api/games/dice/{game.id}/')
        
        self.assertEqual(response.status_code, 404)
    
    def test_verify_game(self):
        """Test game verification"""
        game = DiceGameService.create_and_play_game(
            user=self.user,
            bet_amount=Decimal('10.00'),
            selected_number=3
        )
        
        response = self.client.post(
            '/api/games/dice/verify/',
            data=json.dumps({
                'game_id': game.id
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        self.assertEqual(data['data']['game_id'], game.id)
        self.assertTrue(data['data']['is_valid'])
        self.assertIn('message', data['data'])
    
    def test_verify_game_not_found(self):
        """Test verifying non-existent game"""
        response = self.client.post(
            '/api/games/dice/verify/',
            data=json.dumps({
                'game_id': 99999
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
        data = response.json()
        
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_balance_updates_correctly(self):
        """Test that balance updates correctly after games"""
        initial_balance = self.user.profile.balance
        bet_amount = Decimal('10.00')
        
        # Play multiple games
        games_played = 0
        total_won = Decimal('0.00')
        total_lost = Decimal('0.00')
        
        for i in range(10):
            response = self.client.post(
                '/api/games/dice/create/',
                data=json.dumps({
                    'bet_amount': str(bet_amount),
                    'selected_number': 3
                }),
                content_type='application/json'
            )
            
            data = response.json()
            games_played += 1
            
            if data['data']['won']:
                total_won += Decimal(data['data']['winnings'])
            else:
                total_lost += bet_amount
        
        # Check final balance
        self.user.profile.refresh_from_db()
        expected_balance = initial_balance + total_won - total_lost
        self.assertEqual(self.user.profile.balance, expected_balance)
