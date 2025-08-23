"""
Perlin noise generation module for procedural terrain generation.

This module provides a pure Python implementation of Perlin noise
for generating smooth, natural-looking terrain patterns.
"""

import math
import random
from dataclasses import dataclass
from typing import List


@dataclass
class NoiseConfig:
    """Configuration parameters for noise generation."""
    
    octaves: int = 4
    frequency: float = 0.05
    amplitude: float = 1.0
    persistence: float = 0.5
    lacunarity: float = 2.0
    seed: int = 12345


class NoiseGenerator:
    """
    Perlin noise generator for procedural terrain generation.
    
    This implementation provides smooth, coherent noise suitable for
    terrain generation with configurable parameters for different
    terrain characteristics.
    """
    
    def __init__(self, config: NoiseConfig):
        """
        Initialize the noise generator with the given configuration.
        
        Args:
            config: NoiseConfig object with generation parameters
        """
        self.config = config
        self._setup_permutation_table()
    
    def _setup_permutation_table(self) -> None:
        """Set up the permutation table for noise generation."""
        random.seed(self.config.seed)
        
        # Create permutation table
        self._permutation = list(range(256))
        random.shuffle(self._permutation)
        
        # Duplicate the permutation table to avoid overflow
        self._permutation = self._permutation * 2
        
        # Gradient vectors for 2D noise
        self._gradients = [
            (1, 1), (-1, 1), (1, -1), (-1, -1),
            (1, 0), (-1, 0), (0, 1), (0, -1)
        ]
    
    def _fade(self, t: float) -> float:
        """
        Fade function for smooth interpolation.
        
        Args:
            t: Input value between 0 and 1
            
        Returns:
            Smoothed value using 6t^5 - 15t^4 + 10t^3
        """
        return t * t * t * (t * (t * 6 - 15) + 10)
    
    def _lerp(self, a: float, b: float, t: float) -> float:
        """
        Linear interpolation between two values.
        
        Args:
            a: First value
            b: Second value
            t: Interpolation factor (0-1)
            
        Returns:
            Interpolated value
        """
        return a + t * (b - a)
    
    def _gradient(self, hash_val: int, x: float, y: float) -> float:
        """
        Calculate gradient dot product.
        
        Args:
            hash_val: Hash value for gradient selection
            x: X coordinate offset
            y: Y coordinate offset
            
        Returns:
            Dot product of gradient and offset vector
        """
        grad = self._gradients[hash_val & 7]
        return grad[0] * x + grad[1] * y
    
    def _noise_2d(self, x: float, y: float) -> float:
        """
        Generate 2D Perlin noise at the given coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Noise value between -1 and 1
        """
        # Find unit square containing the point
        xi = int(math.floor(x)) & 255
        yi = int(math.floor(y)) & 255
        
        # Find relative position within the square
        xf = x - math.floor(x)
        yf = y - math.floor(y)
        
        # Compute fade curves
        u = self._fade(xf)
        v = self._fade(yf)
        
        # Hash coordinates of square corners
        aa = self._permutation[self._permutation[xi] + yi]
        ab = self._permutation[self._permutation[xi] + yi + 1]
        ba = self._permutation[self._permutation[xi + 1] + yi]
        bb = self._permutation[self._permutation[xi + 1] + yi + 1]
        
        # Calculate gradients at corners
        x1 = self._lerp(
            self._gradient(aa, xf, yf),
            self._gradient(ba, xf - 1, yf),
            u
        )
        x2 = self._lerp(
            self._gradient(ab, xf, yf - 1),
            self._gradient(bb, xf - 1, yf - 1),
            u
        )
        
        # Interpolate between the two values
        return self._lerp(x1, x2, v)
    
    def generate(self, x: float, y: float) -> float:
        """
        Generate multi-octave Perlin noise at the given coordinates.
        
        Args:
            x: X coordinate in world space
            y: Y coordinate in world space
            
        Returns:
            Noise value between -1 and 1
        """
        total = 0.0
        frequency = self.config.frequency
        amplitude = self.config.amplitude
        max_value = 0.0
        
        for _ in range(self.config.octaves):
            total += self._noise_2d(x * frequency, y * frequency) * amplitude
            max_value += amplitude
            
            amplitude *= self.config.persistence
            frequency *= self.config.lacunarity
        
        # Normalize to [-1, 1] range
        return total / max_value
    
    def generate_chunk(self, chunk_x: int, chunk_y: int, chunk_size: int) -> List[List[float]]:
        """
        Generate noise values for an entire chunk.
        
        Args:
            chunk_x: Chunk X coordinate
            chunk_y: Chunk Y coordinate
            chunk_size: Size of the chunk (width and height)
            
        Returns:
            2D list of noise values for the chunk
        """
        noise_data = []
        
        # Calculate world coordinates for the chunk
        world_start_x = chunk_x * chunk_size
        world_start_y = chunk_y * chunk_size
        
        for y in range(chunk_size):
            row = []
            for x in range(chunk_size):
                world_x = world_start_x + x
                world_y = world_start_y + y
                noise_value = self.generate(world_x, world_y)
                row.append(noise_value)
            noise_data.append(row)
        
        return noise_data


def create_default_noise_generator() -> NoiseGenerator:
    """
    Create a noise generator with default configuration.
    
    Returns:
        NoiseGenerator instance with default settings
    """
    config = NoiseConfig()
    return NoiseGenerator(config)


def create_terrain_noise_generator(seed: int = None) -> NoiseGenerator:
    """
    Create a noise generator optimized for terrain generation.
    
    Args:
        seed: Optional seed for reproducible generation
        
    Returns:
        NoiseGenerator instance optimized for terrain
    """
    config = NoiseConfig(
        octaves=6,
        frequency=0.03,
        amplitude=1.0,
        persistence=0.6,
        lacunarity=2.0,
        seed=seed if seed is not None else 12345
    )
    return NoiseGenerator(config)
