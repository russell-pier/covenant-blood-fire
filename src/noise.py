"""
Noise generation system for the three-tier world generation.

This module provides deterministic noise generation using Perlin-like algorithms
for creating realistic terrain patterns across multiple scales and frequencies.
"""

import math
import random
from typing import List, Tuple

try:
    from .world_types import Seed, NoiseValue, Frequency, Octaves
except ImportError:
    # For direct execution, use absolute imports
    from world_types import Seed, NoiseValue, Frequency, Octaves


class NoiseGenerator:
    """
    Base noise generator providing deterministic Perlin-like noise.
    
    This class generates smooth, continuous noise values suitable for
    terrain generation. All noise is deterministic based on the seed,
    ensuring reproducible world generation.
    
    Attributes:
        seed: Random seed for deterministic generation
        _random: Internal random number generator
    """
    
    def __init__(self, seed: Seed) -> None:
        """
        Initialize the noise generator with a specific seed.
        
        Args:
            seed: Random seed for deterministic noise generation
        """
        self.seed = seed
        self._random = random.Random(seed)
        self._permutation = self._generate_permutation()
    
    def _generate_permutation(self) -> List[int]:
        """
        Generate a permutation table for noise calculation.
        
        Returns:
            A list of 512 integers used for noise permutation
        """
        # Create base permutation of 0-255
        perm = list(range(256))
        self._random.shuffle(perm)
        
        # Duplicate to avoid overflow issues
        return perm + perm
    
    def _fade(self, t: float) -> float:
        """
        Fade function for smooth interpolation.
        
        Uses 6t^5 - 15t^4 + 10t^3 for smooth transitions.
        
        Args:
            t: Input value between 0 and 1
            
        Returns:
            Smoothed value between 0 and 1
        """
        return t * t * t * (t * (t * 6 - 15) + 10)
    
    def _lerp(self, a: float, b: float, t: float) -> float:
        """
        Linear interpolation between two values.
        
        Args:
            a: Start value
            b: End value
            t: Interpolation factor (0-1)
            
        Returns:
            Interpolated value between a and b
        """
        return a + t * (b - a)
    
    def _grad(self, hash_val: int, x: float, y: float) -> float:
        """
        Calculate gradient value for noise generation.
        
        Args:
            hash_val: Hash value for gradient selection
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Gradient contribution to noise
        """
        h = hash_val & 3
        u = x if h < 2 else y
        v = y if h < 2 else x
        return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v)
    
    def noise_2d(self, x: float, y: float) -> NoiseValue:
        """
        Generate 2D Perlin noise at given coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Noise value between -1.0 and 1.0
        """
        # Find unit square containing point
        X = int(math.floor(x)) & 255
        Y = int(math.floor(y)) & 255
        
        # Find relative position within square
        x -= math.floor(x)
        y -= math.floor(y)
        
        # Compute fade curves
        u = self._fade(x)
        v = self._fade(y)
        
        # Hash coordinates of square corners
        A = self._permutation[X] + Y
        AA = self._permutation[A]
        AB = self._permutation[A + 1]
        B = self._permutation[X + 1] + Y
        BA = self._permutation[B]
        BB = self._permutation[B + 1]
        
        # Blend results from corners
        return self._lerp(
            self._lerp(
                self._grad(self._permutation[AA], x, y),
                self._grad(self._permutation[BA], x - 1, y),
                u
            ),
            self._lerp(
                self._grad(self._permutation[AB], x, y - 1),
                self._grad(self._permutation[BB], x - 1, y - 1),
                u
            ),
            v
        )
    
    def octave_noise_2d(
        self, 
        x: float, 
        y: float, 
        octaves: Octaves = 4,
        persistence: float = 0.5,
        lacunarity: float = 2.0
    ) -> NoiseValue:
        """
        Generate multi-octave noise for more complex patterns.
        
        Combines multiple frequencies of noise for realistic terrain.
        
        Args:
            x: X coordinate
            y: Y coordinate
            octaves: Number of noise octaves to combine
            persistence: Amplitude reduction per octave
            lacunarity: Frequency increase per octave
            
        Returns:
            Combined noise value between -1.0 and 1.0
        """
        value = 0.0
        amplitude = 1.0
        frequency = 1.0
        max_value = 0.0
        
        for _ in range(octaves):
            value += self.noise_2d(x * frequency, y * frequency) * amplitude
            max_value += amplitude
            amplitude *= persistence
            frequency *= lacunarity
        
        return value / max_value
    
    def noise_range(
        self, 
        x: float, 
        y: float, 
        octaves: Octaves = 4,
        min_val: float = 0.0,
        max_val: float = 1.0
    ) -> float:
        """
        Generate noise in a specific range.
        
        Args:
            x: X coordinate
            y: Y coordinate
            octaves: Number of octaves
            min_val: Minimum output value
            max_val: Maximum output value
            
        Returns:
            Noise value in range [min_val, max_val]
        """
        noise = self.octave_noise_2d(x, y, octaves)
        # Convert from [-1, 1] to [min_val, max_val]
        return min_val + (noise + 1.0) * 0.5 * (max_val - min_val)


class HierarchicalNoiseGenerator:
    """
    Hierarchical noise generator for multi-scale terrain generation.
    
    Provides different noise frequencies for continental, regional,
    and local scale terrain features.
    """
    
    def __init__(self, seed: Seed) -> None:
        """
        Initialize hierarchical noise with base seed.
        
        Args:
            seed: Base seed for all noise generators
        """
        self.seed = seed
        # Create separate generators for each scale with derived seeds
        self.continental_gen = NoiseGenerator(seed)
        self.regional_gen = NoiseGenerator(seed + 1000)
        self.local_gen = NoiseGenerator(seed + 2000)
    
    def continental_noise(self, x: float, y: float) -> NoiseValue:
        """
        Generate continental-scale noise (0.00001 frequency).
        
        Used for major landmasses, ocean/land distribution.
        
        Args:
            x: World X coordinate
            y: World Y coordinate
            
        Returns:
            Continental noise value (-1.0 to 1.0)
        """
        frequency = 0.00001
        return self.continental_gen.octave_noise_2d(
            x * frequency, y * frequency, octaves=3
        )
    
    def regional_noise(self, x: float, y: float) -> NoiseValue:
        """
        Generate regional-scale noise (0.001 frequency).
        
        Used for mountain ranges, river systems, biome variations.
        
        Args:
            x: Regional X coordinate
            y: Regional Y coordinate
            
        Returns:
            Regional noise value (-1.0 to 1.0)
        """
        frequency = 0.001
        return self.regional_gen.octave_noise_2d(
            x * frequency, y * frequency, octaves=4
        )
    
    def local_noise(self, x: float, y: float) -> NoiseValue:
        """
        Generate local-scale noise (0.01 frequency).
        
        Used for detailed terrain variation, micro-features.
        
        Args:
            x: Local X coordinate
            y: Local Y coordinate
            
        Returns:
            Local noise value (-1.0 to 1.0)
        """
        frequency = 0.01
        return self.local_gen.octave_noise_2d(
            x * frequency, y * frequency, octaves=5
        )
    
    def combined_noise(
        self, 
        x: float, 
        y: float,
        continental_weight: float = 0.5,
        regional_weight: float = 0.3,
        local_weight: float = 0.2
    ) -> NoiseValue:
        """
        Generate combined multi-scale noise.
        
        Blends continental, regional, and local noise for complex terrain.
        
        Args:
            x: X coordinate
            y: Y coordinate
            continental_weight: Weight for continental features
            regional_weight: Weight for regional features
            local_weight: Weight for local features
            
        Returns:
            Combined noise value (-1.0 to 1.0)
        """
        continental = self.continental_noise(x, y) * continental_weight
        regional = self.regional_noise(x, y) * regional_weight
        local = self.local_noise(x, y) * local_weight
        
        total_weight = continental_weight + regional_weight + local_weight
        return (continental + regional + local) / total_weight


def test_noise_determinism(seed: Seed = 12345) -> bool:
    """
    Test that noise generation is deterministic.
    
    Args:
        seed: Test seed
        
    Returns:
        True if noise is deterministic, False otherwise
    """
    gen1 = NoiseGenerator(seed)
    gen2 = NoiseGenerator(seed)
    
    test_points = [(0.5, 0.5), (10.3, 20.7), (100.1, 200.9)]
    
    for x, y in test_points:
        val1 = gen1.noise_2d(x, y)
        val2 = gen2.noise_2d(x, y)
        if abs(val1 - val2) > 1e-10:
            return False
    
    return True


if __name__ == "__main__":
    # Basic testing
    print("Testing noise generation...")
    
    # Test determinism
    if test_noise_determinism():
        print("✓ Noise generation is deterministic")
    else:
        print("✗ Noise generation is not deterministic")
    
    # Test hierarchical noise
    hier_gen = HierarchicalNoiseGenerator(12345)
    
    print(f"Continental noise at (1000, 1000): {hier_gen.continental_noise(1000, 1000):.4f}")
    print(f"Regional noise at (100, 100): {hier_gen.regional_noise(100, 100):.4f}")
    print(f"Local noise at (10, 10): {hier_gen.local_noise(10, 10):.4f}")
    
    print("Noise generation system ready!")
