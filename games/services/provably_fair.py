"""
Provably Fair Service for cryptographically secure game outcomes.

This service implements provably fair algorithms that allow players to verify
that game outcomes were not manipulated. Uses HMAC-SHA256 for deterministic
random number generation.

Algorithm Overview:
1. Server generates server_seed (kept secret until game ends)
2. Client provides client_seed (or auto-generated)
3. Server provides hash of server_seed for verification
4. Game outcome is generated using HMAC(server_seed, client_seed + nonce)
5. After game, server reveals server_seed for verification

This ensures:
- Server cannot change outcome after client_seed is set
- Client can verify outcome was fair after game ends
- Outcome is deterministic and reproducible
"""
import hashlib
import hmac
import secrets
from typing import List, Tuple


class ProvablyFairService:
    """
    Service for provably fair game outcome generation.
    All methods are static and cryptographically secure.
    """
    
    # Constants
    SEED_LENGTH = 32  # bytes for server seed
    GRID_SIZE = 5  # 5x5 grid for Mines
    TOTAL_CELLS = GRID_SIZE * GRID_SIZE  # 25 cells
    
    @staticmethod
    def generate_server_seed() -> str:
        """
        Generate cryptographically secure server seed.
        
        Uses secrets module for cryptographic randomness.
        Server seed should be kept secret until game ends.
        
        Returns:
            Hex string of 32 random bytes (64 characters)
            
        Example:
            >>> seed = ProvablyFairService.generate_server_seed()
            >>> len(seed)
            64
        """
        return secrets.token_hex(ProvablyFairService.SEED_LENGTH)
    
    @staticmethod
    def generate_client_seed() -> str:
        """
        Generate client seed.
        
        Can be auto-generated or provided by client.
        Client seed is public and known before game starts.
        
        Returns:
            Hex string of 16 random bytes (32 characters)
            
        Example:
            >>> seed = ProvablyFairService.generate_client_seed()
            >>> len(seed)
            32
        """
        return secrets.token_hex(16)
    
    @staticmethod
    def hash_seed(seed: str) -> str:
        """
        Create SHA256 hash of seed for verification.
        
        Server provides hash of server_seed before game starts.
        This allows client to verify server didn't change seed after game.
        
        Args:
            seed: Seed string to hash
            
        Returns:
            SHA256 hex digest (64 characters)
            
        Example:
            >>> seed = "abc123"
            >>> hash_val = ProvablyFairService.hash_seed(seed)
            >>> len(hash_val)
            64
        """
        return hashlib.sha256(seed.encode()).hexdigest()
    
    @staticmethod
    def generate_mine_positions(
        server_seed: str,
        client_seed: str,
        nonce: int,
        mine_count: int
    ) -> List[Tuple[int, int]]:
        """
        Generate mine positions using provably fair algorithm.
        
        Algorithm:
        1. Create HMAC-SHA256 hash using server_seed as key
        2. Message is client_seed + str(nonce)
        3. Use hash bytes to shuffle cell positions (Fisher-Yates)
        4. Select first mine_count positions
        
        This is deterministic: same inputs always produce same output.
        
        Args:
            server_seed: Secret server seed (hex string)
            client_seed: Public client seed (hex string)
            nonce: Game round number (increments for each game)
            mine_count: Number of mines to place (3-20)
            
        Returns:
            List of (row, col) tuples for mine positions
            
        Raises:
            ValueError: If mine_count is invalid
            
        Example:
            >>> positions = ProvablyFairService.generate_mine_positions(
            ...     "abc123", "def456", 0, 5
            ... )
            >>> len(positions)
            5
            >>> all(0 <= r < 5 and 0 <= c < 5 for r, c in positions)
            True
        """
        # Validate mine count
        if mine_count < 3 or mine_count > 20:
            raise ValueError(f"Mine count must be between 3 and 20, got {mine_count}")
        
        if mine_count > ProvablyFairService.TOTAL_CELLS:
            raise ValueError(
                f"Mine count ({mine_count}) cannot exceed total cells "
                f"({ProvablyFairService.TOTAL_CELLS})"
            )
        
        # Create message for HMAC
        message = f"{client_seed}{nonce}".encode()
        
        # Generate HMAC-SHA256
        hmac_hash = hmac.new(
            server_seed.encode(),
            message,
            hashlib.sha256
        ).digest()
        
        # Create list of all cell positions
        cells = [
            (row, col)
            for row in range(ProvablyFairService.GRID_SIZE)
            for col in range(ProvablyFairService.GRID_SIZE)
        ]
        
        # Fisher-Yates shuffle using HMAC bytes
        # We need to generate more random bytes if hash is not enough
        random_bytes = hmac_hash
        byte_index = 0
        
        for i in range(len(cells) - 1, 0, -1):
            # Get random index using bytes from hash
            # If we run out of bytes, generate more using previous hash
            if byte_index >= len(random_bytes):
                random_bytes = hashlib.sha256(random_bytes).digest()
                byte_index = 0
            
            # Use 2 bytes to get random number (0-65535)
            rand_val = int.from_bytes(
                random_bytes[byte_index:byte_index + 2],
                byteorder='big'
            )
            byte_index += 2
            
            # Map to range [0, i]
            j = rand_val % (i + 1)
            
            # Swap
            cells[i], cells[j] = cells[j], cells[i]
        
        # Return first mine_count positions
        return cells[:mine_count]
    
    @staticmethod
    def verify_mine_positions(
        server_seed: str,
        client_seed: str,
        nonce: int,
        mine_count: int,
        claimed_positions: List[Tuple[int, int]]
    ) -> bool:
        """
        Verify that mine positions match the seeds.
        
        Regenerates positions using provided seeds and compares with claimed positions.
        Used by client to verify game was fair after server reveals server_seed.
        
        Args:
            server_seed: Server seed (revealed after game)
            client_seed: Client seed (known before game)
            nonce: Game round number
            mine_count: Number of mines
            claimed_positions: Positions claimed by server
            
        Returns:
            True if positions match, False otherwise
            
        Example:
            >>> positions = ProvablyFairService.generate_mine_positions(
            ...     "abc123", "def456", 0, 5
            ... )
            >>> ProvablyFairService.verify_mine_positions(
            ...     "abc123", "def456", 0, 5, positions
            ... )
            True
        """
        try:
            # Regenerate positions
            actual_positions = ProvablyFairService.generate_mine_positions(
                server_seed,
                client_seed,
                nonce,
                mine_count
            )
            
            # Compare sets (order doesn't matter)
            return set(actual_positions) == set(claimed_positions)
            
        except Exception:
            return False
    
    @staticmethod
    def verify_server_seed_hash(server_seed: str, server_seed_hash: str) -> bool:
        """
        Verify that server_seed matches the hash provided before game.
        
        Args:
            server_seed: Server seed revealed after game
            server_seed_hash: Hash provided before game started
            
        Returns:
            True if hash matches, False otherwise
            
        Example:
            >>> seed = "abc123"
            >>> hash_val = ProvablyFairService.hash_seed(seed)
            >>> ProvablyFairService.verify_server_seed_hash(seed, hash_val)
            True
        """
        return ProvablyFairService.hash_seed(server_seed) == server_seed_hash
    
    @staticmethod
    def get_game_info(
        server_seed_hash: str,
        client_seed: str,
        nonce: int,
        mine_count: int
    ) -> dict:
        """
        Get game information for display to player before game starts.
        
        Args:
            server_seed_hash: Hash of server seed
            client_seed: Client seed
            nonce: Game round number
            mine_count: Number of mines
            
        Returns:
            Dictionary with game information
            
        Example:
            >>> info = ProvablyFairService.get_game_info(
            ...     "abc123hash", "def456", 0, 5
            ... )
            >>> 'server_seed_hash' in info
            True
        """
        return {
            'server_seed_hash': server_seed_hash,
            'client_seed': client_seed,
            'nonce': nonce,
            'mine_count': mine_count,
            'grid_size': ProvablyFairService.GRID_SIZE,
            'total_cells': ProvablyFairService.TOTAL_CELLS
        }
    
    @staticmethod
    def get_verification_info(
        server_seed: str,
        client_seed: str,
        nonce: int,
        mine_count: int,
        mine_positions: List[Tuple[int, int]]
    ) -> dict:
        """
        Get verification information for player after game ends.
        
        Args:
            server_seed: Server seed (now revealed)
            client_seed: Client seed
            nonce: Game round number
            mine_count: Number of mines
            mine_positions: Actual mine positions
            
        Returns:
            Dictionary with verification information
            
        Example:
            >>> positions = [(0, 0), (1, 1), (2, 2)]
            >>> info = ProvablyFairService.get_verification_info(
            ...     "abc123", "def456", 0, 3, positions
            ... )
            >>> 'server_seed' in info
            True
        """
        server_seed_hash = ProvablyFairService.hash_seed(server_seed)
        
        # Verify positions
        is_valid = ProvablyFairService.verify_mine_positions(
            server_seed,
            client_seed,
            nonce,
            mine_count,
            mine_positions
        )
        
        return {
            'server_seed': server_seed,
            'server_seed_hash': server_seed_hash,
            'client_seed': client_seed,
            'nonce': nonce,
            'mine_count': mine_count,
            'mine_positions': mine_positions,
            'is_valid': is_valid,
            'verification_url': f'/verify?server_seed={server_seed}&client_seed={client_seed}&nonce={nonce}'
        }
    
    @staticmethod
    def generate_dice_roll(
        server_seed: str,
        client_seed: str,
        nonce: int
    ) -> int:
        """
        Generate dice roll (1-6) using provably fair algorithm.
        
        Algorithm:
        1. Create HMAC-SHA256 hash using server_seed as key
        2. Message is client_seed + str(nonce)
        3. Use first 4 bytes of hash to generate number
        4. Map to range [1, 6]
        
        Args:
            server_seed: Secret server seed (hex string)
            client_seed: Public client seed (hex string)
            nonce: Game round number
            
        Returns:
            Dice roll result (1-6)
            
        Example:
            >>> roll = ProvablyFairService.generate_dice_roll(
            ...     "abc123", "def456", 0
            ... )
            >>> 1 <= roll <= 6
            True
        """
        # Create message for HMAC
        message = f"{client_seed}{nonce}".encode()
        
        # Generate HMAC-SHA256
        hmac_hash = hmac.new(
            server_seed.encode(),
            message,
            hashlib.sha256
        ).digest()
        
        # Use first 4 bytes to get random number
        rand_val = int.from_bytes(hmac_hash[:4], byteorder='big')
        
        # Map to range [1, 6]
        return (rand_val % 6) + 1
