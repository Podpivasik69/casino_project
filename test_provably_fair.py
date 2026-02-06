"""
Test script for Provably Fair Service.
Tests cryptographic security, determinism, and verification.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'casino.settings')
django.setup()

from games.services.provably_fair import ProvablyFairService


def print_section(title):
    """Print section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_seed_generation():
    """Test seed generation"""
    print_section("1. Testing Seed Generation")
    
    # Test 1: Server seed generation
    print("\n🔐 Test 1: Server Seed Generation")
    server_seed = ProvablyFairService.generate_server_seed()
    
    print(f"  Server seed: {server_seed}")
    print(f"  Length: {len(server_seed)} characters")
    
    assert len(server_seed) == 64, "Server seed should be 64 hex characters"
    assert all(c in '0123456789abcdef' for c in server_seed), "Should be hex string"
    print("  ✓ Server seed generated correctly")
    
    # Test 2: Client seed generation
    print("\n🔐 Test 2: Client Seed Generation")
    client_seed = ProvablyFairService.generate_client_seed()
    
    print(f"  Client seed: {client_seed}")
    print(f"  Length: {len(client_seed)} characters")
    
    assert len(client_seed) == 32, "Client seed should be 32 hex characters"
    assert all(c in '0123456789abcdef' for c in client_seed), "Should be hex string"
    print("  ✓ Client seed generated correctly")
    
    # Test 3: Seeds are unique
    print("\n🔐 Test 3: Seed Uniqueness")
    seeds = [ProvablyFairService.generate_server_seed() for _ in range(10)]
    
    assert len(set(seeds)) == 10, "All seeds should be unique"
    print(f"  ✓ Generated 10 unique seeds")


def test_seed_hashing():
    """Test seed hashing"""
    print_section("2. Testing Seed Hashing")
    
    # Test 1: Hash generation
    print("\n🔒 Test 1: Hash Generation")
    seed = "test_seed_123"
    hash_val = ProvablyFairService.hash_seed(seed)
    
    print(f"  Seed: {seed}")
    print(f"  Hash: {hash_val}")
    print(f"  Length: {len(hash_val)} characters")
    
    assert len(hash_val) == 64, "SHA256 hash should be 64 hex characters"
    print("  ✓ Hash generated correctly")
    
    # Test 2: Hash is deterministic
    print("\n🔒 Test 2: Hash Determinism")
    hash_val2 = ProvablyFairService.hash_seed(seed)
    
    assert hash_val == hash_val2, "Same seed should produce same hash"
    print("  ✓ Hash is deterministic")
    
    # Test 3: Different seeds produce different hashes
    print("\n🔒 Test 3: Hash Uniqueness")
    seed2 = "test_seed_456"
    hash_val3 = ProvablyFairService.hash_seed(seed2)
    
    assert hash_val != hash_val3, "Different seeds should produce different hashes"
    print("  ✓ Different seeds produce different hashes")
    
    # Test 4: Verify server seed hash
    print("\n🔒 Test 4: Server Seed Hash Verification")
    server_seed = ProvablyFairService.generate_server_seed()
    server_seed_hash = ProvablyFairService.hash_seed(server_seed)
    
    is_valid = ProvablyFairService.verify_server_seed_hash(server_seed, server_seed_hash)
    assert is_valid, "Server seed should match its hash"
    print("  ✓ Server seed hash verification works")
    
    # Test with wrong seed
    wrong_seed = ProvablyFairService.generate_server_seed()
    is_valid = ProvablyFairService.verify_server_seed_hash(wrong_seed, server_seed_hash)
    assert not is_valid, "Wrong seed should not match hash"
    print("  ✓ Wrong seed correctly rejected")


def test_mine_position_generation():
    """Test mine position generation"""
    print_section("3. Testing Mine Position Generation")
    
    # Test 1: Basic generation
    print("\n💣 Test 1: Basic Mine Generation")
    server_seed = "abc123"
    client_seed = "def456"
    nonce = 0
    mine_count = 5
    
    positions = ProvablyFairService.generate_mine_positions(
        server_seed, client_seed, nonce, mine_count
    )
    
    print(f"  Server seed: {server_seed}")
    print(f"  Client seed: {client_seed}")
    print(f"  Nonce: {nonce}")
    print(f"  Mine count: {mine_count}")
    print(f"  Positions: {positions}")
    
    assert len(positions) == mine_count, f"Should generate {mine_count} positions"
    assert len(set(positions)) == mine_count, "All positions should be unique"
    
    # Check all positions are valid (0-4 for 5x5 grid)
    for row, col in positions:
        assert 0 <= row < 5, f"Row {row} out of bounds"
        assert 0 <= col < 5, f"Col {col} out of bounds"
    
    print("  ✓ Generated valid mine positions")
    
    # Test 2: Determinism
    print("\n💣 Test 2: Determinism")
    positions2 = ProvablyFairService.generate_mine_positions(
        server_seed, client_seed, nonce, mine_count
    )
    
    assert positions == positions2, "Same inputs should produce same positions"
    print("  ✓ Mine generation is deterministic")
    
    # Test 3: Different seeds produce different positions
    print("\n💣 Test 3: Seed Sensitivity")
    positions3 = ProvablyFairService.generate_mine_positions(
        "different_seed", client_seed, nonce, mine_count
    )
    
    assert positions != positions3, "Different server seed should change positions"
    print("  ✓ Different seeds produce different positions")
    
    # Test 4: Different nonce produces different positions
    print("\n💣 Test 4: Nonce Sensitivity")
    positions4 = ProvablyFairService.generate_mine_positions(
        server_seed, client_seed, 1, mine_count
    )
    
    assert positions != positions4, "Different nonce should change positions"
    print("  ✓ Different nonce produces different positions")
    
    # Test 5: Different mine counts
    print("\n💣 Test 5: Various Mine Counts")
    for count in [3, 5, 10, 15, 20]:
        positions = ProvablyFairService.generate_mine_positions(
            server_seed, client_seed, nonce, count
        )
        assert len(positions) == count
        assert len(set(positions)) == count
        print(f"  ✓ Generated {count} unique mines")
    
    # Test 6: Invalid mine counts
    print("\n💣 Test 6: Invalid Mine Counts")
    try:
        ProvablyFairService.generate_mine_positions(
            server_seed, client_seed, nonce, 2
        )
        print("  ✗ Should have raised ValueError for mine_count=2")
    except ValueError as e:
        print(f"  ✓ Correctly rejected mine_count=2: {e}")
    
    try:
        ProvablyFairService.generate_mine_positions(
            server_seed, client_seed, nonce, 21
        )
        print("  ✗ Should have raised ValueError for mine_count=21")
    except ValueError as e:
        print(f"  ✓ Correctly rejected mine_count=21: {e}")


def test_position_verification():
    """Test mine position verification"""
    print_section("4. Testing Position Verification")
    
    # Test 1: Valid verification
    print("\n✅ Test 1: Valid Verification")
    server_seed = "test_server_seed"
    client_seed = "test_client_seed"
    nonce = 0
    mine_count = 5
    
    positions = ProvablyFairService.generate_mine_positions(
        server_seed, client_seed, nonce, mine_count
    )
    
    is_valid = ProvablyFairService.verify_mine_positions(
        server_seed, client_seed, nonce, mine_count, positions
    )
    
    assert is_valid, "Verification should pass for correct positions"
    print("  ✓ Valid positions verified successfully")
    
    # Test 2: Invalid verification (wrong positions)
    print("\n❌ Test 2: Invalid Verification (Wrong Positions)")
    wrong_positions = [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)]
    
    is_valid = ProvablyFairService.verify_mine_positions(
        server_seed, client_seed, nonce, mine_count, wrong_positions
    )
    
    assert not is_valid, "Verification should fail for wrong positions"
    print("  ✓ Wrong positions correctly rejected")
    
    # Test 3: Invalid verification (wrong server seed)
    print("\n❌ Test 3: Invalid Verification (Wrong Server Seed)")
    is_valid = ProvablyFairService.verify_mine_positions(
        "wrong_server_seed", client_seed, nonce, mine_count, positions
    )
    
    assert not is_valid, "Verification should fail for wrong server seed"
    print("  ✓ Wrong server seed correctly rejected")
    
    # Test 4: Invalid verification (wrong client seed)
    print("\n❌ Test 4: Invalid Verification (Wrong Client Seed)")
    is_valid = ProvablyFairService.verify_mine_positions(
        server_seed, "wrong_client_seed", nonce, mine_count, positions
    )
    
    assert not is_valid, "Verification should fail for wrong client seed"
    print("  ✓ Wrong client seed correctly rejected")
    
    # Test 5: Invalid verification (wrong nonce)
    print("\n❌ Test 5: Invalid Verification (Wrong Nonce)")
    is_valid = ProvablyFairService.verify_mine_positions(
        server_seed, client_seed, 999, mine_count, positions
    )
    
    assert not is_valid, "Verification should fail for wrong nonce"
    print("  ✓ Wrong nonce correctly rejected")


def test_game_info():
    """Test game info generation"""
    print_section("5. Testing Game Info")
    
    # Test 1: Get game info
    print("\n📊 Test 1: Get Game Info")
    server_seed = ProvablyFairService.generate_server_seed()
    server_seed_hash = ProvablyFairService.hash_seed(server_seed)
    client_seed = ProvablyFairService.generate_client_seed()
    nonce = 0
    mine_count = 5
    
    info = ProvablyFairService.get_game_info(
        server_seed_hash, client_seed, nonce, mine_count
    )
    
    print(f"  Server seed hash: {info['server_seed_hash'][:32]}...")
    print(f"  Client seed: {info['client_seed']}")
    print(f"  Nonce: {info['nonce']}")
    print(f"  Mine count: {info['mine_count']}")
    print(f"  Grid size: {info['grid_size']}")
    print(f"  Total cells: {info['total_cells']}")
    
    assert info['server_seed_hash'] == server_seed_hash
    assert info['client_seed'] == client_seed
    assert info['nonce'] == nonce
    assert info['mine_count'] == mine_count
    print("  ✓ Game info generated correctly")


def test_verification_info():
    """Test verification info generation"""
    print_section("6. Testing Verification Info")
    
    # Test 1: Get verification info
    print("\n🔍 Test 1: Get Verification Info")
    server_seed = "test_server_seed"
    client_seed = "test_client_seed"
    nonce = 0
    mine_count = 5
    
    positions = ProvablyFairService.generate_mine_positions(
        server_seed, client_seed, nonce, mine_count
    )
    
    info = ProvablyFairService.get_verification_info(
        server_seed, client_seed, nonce, mine_count, positions
    )
    
    print(f"  Server seed: {info['server_seed']}")
    print(f"  Server seed hash: {info['server_seed_hash'][:32]}...")
    print(f"  Client seed: {info['client_seed']}")
    print(f"  Nonce: {info['nonce']}")
    print(f"  Mine count: {info['mine_count']}")
    print(f"  Mine positions: {info['mine_positions']}")
    print(f"  Is valid: {info['is_valid']}")
    print(f"  Verification URL: {info['verification_url'][:50]}...")
    
    assert info['server_seed'] == server_seed
    assert info['client_seed'] == client_seed
    assert info['is_valid'] == True
    print("  ✓ Verification info generated correctly")


def test_complete_workflow():
    """Test complete provably fair workflow"""
    print_section("7. Testing Complete Workflow")
    
    print("\n🎮 Complete Provably Fair Workflow:")
    
    # Step 1: Server generates seeds
    print("\n  Step 1: Server generates server seed")
    server_seed = ProvablyFairService.generate_server_seed()
    server_seed_hash = ProvablyFairService.hash_seed(server_seed)
    print(f"    Server seed (secret): {server_seed[:16]}...")
    print(f"    Server seed hash (public): {server_seed_hash[:32]}...")
    
    # Step 2: Client provides seed
    print("\n  Step 2: Client provides client seed")
    client_seed = ProvablyFairService.generate_client_seed()
    print(f"    Client seed (public): {client_seed}")
    
    # Step 3: Show game info to player
    print("\n  Step 3: Show game info to player (before game)")
    nonce = 0
    mine_count = 5
    game_info = ProvablyFairService.get_game_info(
        server_seed_hash, client_seed, nonce, mine_count
    )
    print(f"    Player can see:")
    print(f"      - Server seed hash: {game_info['server_seed_hash'][:32]}...")
    print(f"      - Client seed: {game_info['client_seed']}")
    print(f"      - Nonce: {game_info['nonce']}")
    print(f"      - Mine count: {game_info['mine_count']}")
    
    # Step 4: Generate mine positions (server-side, secret)
    print("\n  Step 4: Server generates mine positions (secret)")
    positions = ProvablyFairService.generate_mine_positions(
        server_seed, client_seed, nonce, mine_count
    )
    print(f"    Mine positions: {positions}")
    
    # Step 5: Game is played...
    print("\n  Step 5: Game is played...")
    print(f"    (Player clicks cells, avoids mines, etc.)")
    
    # Step 6: Game ends, reveal server seed
    print("\n  Step 6: Game ends, server reveals server seed")
    verification_info = ProvablyFairService.get_verification_info(
        server_seed, client_seed, nonce, mine_count, positions
    )
    print(f"    Server seed revealed: {verification_info['server_seed'][:16]}...")
    
    # Step 7: Player verifies
    print("\n  Step 7: Player verifies game was fair")
    
    # Verify server seed hash
    hash_valid = ProvablyFairService.verify_server_seed_hash(
        server_seed, server_seed_hash
    )
    print(f"    ✓ Server seed hash matches: {hash_valid}")
    
    # Verify positions
    positions_valid = ProvablyFairService.verify_mine_positions(
        server_seed, client_seed, nonce, mine_count, positions
    )
    print(f"    ✓ Mine positions are correct: {positions_valid}")
    
    print(f"\n    ✓ Game was provably fair!")
    
    assert hash_valid and positions_valid
    print("\n  ✓ Complete workflow executed successfully")


def test_distribution():
    """Test mine position distribution"""
    print_section("8. Testing Position Distribution")
    
    print("\n📊 Testing distribution of mine positions:")
    
    server_seed = "test_seed"
    client_seed = "client_seed"
    mine_count = 5
    
    # Generate positions for different nonces
    all_positions = []
    for nonce in range(100):
        positions = ProvablyFairService.generate_mine_positions(
            server_seed, client_seed, nonce, mine_count
        )
        all_positions.extend(positions)
    
    # Count frequency of each cell
    cell_counts = {}
    for row, col in all_positions:
        cell = (row, col)
        cell_counts[cell] = cell_counts.get(cell, 0) + 1
    
    # Calculate statistics
    total_positions = len(all_positions)
    expected_per_cell = total_positions / 25  # 25 cells in 5x5 grid
    
    print(f"  Total positions generated: {total_positions}")
    print(f"  Expected per cell: {expected_per_cell:.1f}")
    
    # Show distribution
    print(f"\n  Cell frequency distribution:")
    min_count = min(cell_counts.values())
    max_count = max(cell_counts.values())
    avg_count = sum(cell_counts.values()) / len(cell_counts)
    
    print(f"    Min: {min_count}")
    print(f"    Max: {max_count}")
    print(f"    Avg: {avg_count:.1f}")
    print(f"    Expected: {expected_per_cell:.1f}")
    
    # Check that all cells are used (no cell has 0 count)
    assert len(cell_counts) == 25, "All 25 cells should be used"
    assert min_count > 0, "All cells should have at least one mine"
    
    # Check distribution is not extremely skewed (max should be < 2x expected)
    # With 100 samples and random distribution, some variance is normal
    max_allowed = expected_per_cell * 2
    assert max_count < max_allowed, f"Max count {max_count} exceeds {max_allowed}"
    
    print(f"  ✓ Distribution is reasonable (all cells used, no extreme outliers)")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  Provably Fair Service Test Suite")
    print("=" * 60)
    
    try:
        test_seed_generation()
        test_seed_hashing()
        test_mine_position_generation()
        test_position_verification()
        test_game_info()
        test_verification_info()
        test_complete_workflow()
        test_distribution()
        
        print("\n" + "=" * 60)
        print("  ✓ All Tests Completed Successfully!")
        print("=" * 60 + "\n")
        
    except AssertionError as e:
        print(f"\n\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n\n✗ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
