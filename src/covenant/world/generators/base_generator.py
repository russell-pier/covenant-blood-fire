"""
Base noise generation system for hierarchical world generation.

This module provides the core noise generation functions that work consistently
across all scales of the world generation system.
"""

import math
import hashlib
from typing import Tuple, List


class HierarchicalNoiseGenerator:
    """Noise system that works consistently across all scales."""
    
    def __init__(self, seed: int):
        """
        Initialize the noise generator with a seed.
        
        Args:
            seed: Base seed for all noise generation
        """
        self.seed = seed
        
        # Different noise layers for different world features
        self.continental_noise_seed = seed
        self.tectonic_noise_seed = seed + 1000
        self.climate_noise_seed = seed + 2000
        self.regional_noise_seed = seed + 3000
        self.local_noise_seed = seed + 4000
        
        # Precompute hash-based random values for better performance
        self._hash_cache = {}
    
    def continental_noise(self, world_x: float, world_y: float) -> float:
        """
        Very low frequency noise for continental shapes.
        
        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            
        Returns:
            Noise value between -1.0 and 1.0
        """
        return self._noise(
            world_x * 0.00001 + self.continental_noise_seed,
            world_y * 0.00001
        )
    
    def tectonic_noise(self, world_x: float, world_y: float) -> float:
        """
        Low frequency noise for mountain ranges and tectonic features.
        
        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            
        Returns:
            Noise value between -1.0 and 1.0
        """
        return self._noise(
            world_x * 0.0001 + self.tectonic_noise_seed,
            world_y * 0.0001
        )
    
    def climate_noise(self, world_x: float, world_y: float) -> float:
        """
        Medium frequency noise for climate variation.
        
        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            
        Returns:
            Noise value between -1.0 and 1.0
        """
        return self._noise(
            world_x * 0.001 + self.climate_noise_seed,
            world_y * 0.001
        )
    
    def regional_noise(self, world_x: float, world_y: float) -> float:
        """
        Higher frequency noise for regional terrain features.
        
        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            
        Returns:
            Noise value between -1.0 and 1.0
        """
        return self._noise(
            world_x * 0.01 + self.regional_noise_seed,
            world_y * 0.01
        )
    
    def local_noise(self, world_x: float, world_y: float) -> float:
        """
        High frequency noise for local terrain details.
        
        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            
        Returns:
            Noise value between -1.0 and 1.0
        """
        return self._noise(
            world_x * 0.1 + self.local_noise_seed,
            world_y * 0.1
        )
    
    def _noise(self, x: float, y: float) -> float:
        """
        Core noise function using improved hash-based approach.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Noise value between -1.0 and 1.0
        """
        # Use integer coordinates for hashing
        ix = int(x)
        iy = int(y)
        
        # Get fractional parts
        fx = x - ix
        fy = y - iy
        
        # Get corner values
        a = self._hash_noise(ix, iy)
        b = self._hash_noise(ix + 1, iy)
        c = self._hash_noise(ix, iy + 1)
        d = self._hash_noise(ix + 1, iy + 1)
        
        # Smooth interpolation
        u = self._smooth_step(fx)
        v = self._smooth_step(fy)
        
        # Bilinear interpolation
        x1 = self._lerp(a, b, u)
        x2 = self._lerp(c, d, u)
        return self._lerp(x1, x2, v)
    
    def _hash_noise(self, x: int, y: int) -> float:
        """
        Generate hash-based noise for integer coordinates.
        
        Args:
            x: Integer X coordinate
            y: Integer Y coordinate
            
        Returns:
            Noise value between -1.0 and 1.0
        """
        # Create cache key
        key = (x, y)
        if key in self._hash_cache:
            return self._hash_cache[key]
        
        # Generate hash
        hash_input = f"{x},{y},{self.seed}".encode('utf-8')
        hash_value = hashlib.md5(hash_input).hexdigest()
        
        # Convert to float between -1 and 1
        int_value = int(hash_value[:8], 16)
        float_value = (int_value / 0xFFFFFFFF) * 2.0 - 1.0
        
        # Cache the result
        self._hash_cache[key] = float_value
        return float_value
    
    def _smooth_step(self, t: float) -> float:
        """
        Smooth step function for interpolation.
        
        Args:
            t: Input value between 0 and 1
            
        Returns:
            Smoothed value between 0 and 1
        """
        return t * t * (3.0 - 2.0 * t)
    
    def _lerp(self, a: float, b: float, t: float) -> float:
        """
        Linear interpolation between two values.
        
        Args:
            a: Start value
            b: End value
            t: Interpolation factor (0-1)
            
        Returns:
            Interpolated value
        """
        return a + t * (b - a)
    
    def octave_noise(self, x: float, y: float, octaves: int = 3, 
                     base_seed: int = 0, frequency: float = 1.0, 
                     amplitude: float = 1.0) -> float:
        """
        Multi-octave noise for complex patterns.
        
        Args:
            x: X coordinate
            y: Y coordinate
            octaves: Number of octaves to combine
            base_seed: Additional seed offset
            frequency: Base frequency multiplier
            amplitude: Base amplitude multiplier
            
        Returns:
            Combined noise value
        """
        value = 0.0
        current_amplitude = amplitude
        current_frequency = frequency
        max_value = 0.0
        
        for i in range(octaves):
            noise_val = self._noise(
                x * current_frequency + base_seed + i * 1000, 
                y * current_frequency
            )
            value += noise_val * current_amplitude
            max_value += current_amplitude
            current_amplitude *= 0.5
            current_frequency *= 2.0
        
        # Normalize to maintain -1 to 1 range
        if max_value > 0:
            value /= max_value
        
        return value
    
    def ridged_noise(self, x: float, y: float, octaves: int = 3) -> float:
        """
        Ridged noise for mountain-like features.
        
        Args:
            x: X coordinate
            y: Y coordinate
            octaves: Number of octaves
            
        Returns:
            Ridged noise value between 0 and 1
        """
        value = 0.0
        amplitude = 1.0
        frequency = 1.0
        
        for i in range(octaves):
            noise_val = abs(self._noise(x * frequency, y * frequency))
            noise_val = 1.0 - noise_val  # Invert for ridges
            value += noise_val * amplitude
            amplitude *= 0.5
            frequency *= 2.0
        
        return max(0.0, min(1.0, value))
    
    def clear_cache(self) -> None:
        """Clear the noise cache to free memory."""
        self._hash_cache.clear()
