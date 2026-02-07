"""
Test Slots API endpoints.
"""
import json
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from users.models import Profile
from games.models import SlotsGame

User = get_user_model()


class SlotsAPITest(TestCase):
    """Test Slots game API endpoints."""
    
    def setUp(self):
        """Set up test client and user."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        # Set initial balance
        self.user.profile.balance = Decimal('1000.00')
        self.user.profile.save()
        
        # Login
        self.client.login(username='testuser', password='testpass123')
    
    def test_create_slots_game_3_reels(self):
        """Test creating a 3-reel slots game."""
        response = self.client.post(
            '/api/games/slots/create/',
            data=json.dumps({
                'bet_amount': '10.00',
                'reels_count': 3
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['bet_amount'], '10.00')
        self.assertEqual(data['data']['reels_count'], 3)
        self.assertEqual(len(data['data']['reels']), 3)
        self.assertIn('multiplier', data['data'])
        self.assertIn('win_amount', data['data'])
        self.assertIn('balance', data['data'])
        
        # Check balance was deducted
        self.user.profile.refresh_from_db()
        if Decimal(data['data']['win_amount']) > 0:
            # Won: balance = 1000 - 10 + win_amount
            expected_balance = Decimal('990.00') + Decimal(data['data']['win_amount'])
        else:
            # Lost: balance = 1000 - 10
            expected_balance = Decimal('990.00')
        
        self.assertEqual(self.user.profile.balance, expected_balance)
    
    def test_create_slots_game_5_reels(self):
        """Test creating a 5-reel slots game."""
        response = self.client.post(
            '/api/games/slots/create/',
            data=json.dumps({
                'bet_amount': '10.00',
                'reels_count': 5
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['bet_amount'], '10.00')
        self.assertEqual(data['data']['reels_count'], 5)
        self.assertEqual(len(data['data']['reels']), 5)
    
    def test_create_slots_game_insufficient_balance(self):
        """Test creating game with insufficient balance."""
        self.user.profile.balance = Decimal('5.00')
        self.user.profile.save()
        
        response = self.client.post(
            '/api/games/slots/create/',
            data=json.dumps({
                'bet_amount': '10.00',
                'reels_count': 5
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
    
    def test_create_slots_game_invalid_reels_count(self):
        """Test creating game with invalid reels count."""
        response = self.client.post(
            '/api/games/slots/create/',
            data=json.dumps({
                'bet_amount': '10.00',
                'reels_count': 7
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
    
    def test_get_slots_history(self):
        """Test getting slots game history."""
        # Create a few games
        for i in range(3):
            self.client.post(
                '/api/games/slots/create/',
                data=json.dumps({
                    'bet_amount': '10.00',
                    'reels_count': 5
                }),
                content_type='application/json'
            )
        
        response = self.client.get('/api/games/slots/history/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']['games']), 3)
    
    def test_get_specific_game(self):
        """Test getting specific game details."""
        # Create a game
        create_response = self.client.post(
            '/api/games/slots/create/',
            data=json.dumps({
                'bet_amount': '10.00',
                'reels_count': 5
            }),
            content_type='application/json'
        )
        
        game_id = create_response.json()['data']['game_id']
        
        # Get game details
        response = self.client.get(f'/api/games/slots/{game_id}/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['game_id'], game_id)
        self.assertIn('server_seed', data['data'])
        self.assertIn('client_seed', data['data'])
        self.assertIn('nonce', data['data'])
    
    def test_verify_game(self):
        """Test verifying game with provably fair."""
        # Create a game
        create_response = self.client.post(
            '/api/games/slots/create/',
            data=json.dumps({
                'bet_amount': '10.00',
                'reels_count': 5
            }),
            content_type='application/json'
        )
        
        game_id = create_response.json()['data']['game_id']
        
        # Verify game
        response = self.client.post(
            '/api/games/slots/verify/',
            data=json.dumps({
                'game_id': game_id
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertTrue(data['data']['is_valid'])
    
    def test_provably_fair_determinism(self):
        """Test that same seeds produce same results."""
        # Create a game
        response = self.client.post(
            '/api/games/slots/create/',
            data=json.dumps({
                'bet_amount': '10.00',
                'reels_count': 5,
                'client_seed': 'test_seed_123'
            }),
            content_type='application/json'
        )
        
        game_id = response.json()['data']['game_id']
        game = SlotsGame.objects.get(id=game_id)
        
        # Verify game produces same results
        from games.services.slots_service import SlotsGameService
        
        reels = SlotsGameService.generate_reels(
            server_seed=game.server_seed,
            client_seed=game.client_seed,
            nonce=game.nonce,
            reels_count=game.reels_count
        )
        
        self.assertEqual(reels, game.reels)


if __name__ == '__main__':
    import django
    django.setup()
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['__main__'])
