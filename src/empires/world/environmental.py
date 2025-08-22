"""
Environmental layer generation system for world generation.

This module provides the core environmental system that generates three
layers (elevation, moisture, temperature) used to determine terrain types
and visual variations.
"""

import math
from dataclasses import dataclass
from typing import List, Optional

from .environmental_config import EnvironmentalConfig, create_default_environmental_config
from .noise import NoiseConfig, NoiseGenerator


@dataclass
class EnvironmentalData:
    """Container for environmental layer values at a specific location."""
    
    elevation: float    # 0.0 to 1.0 (0 = deep caves, 0.3 = sea level, 1 = highest mountains)
    moisture: float     # 0.0 to 1.0 (0 = desert dry, 1 = swamp wet)
    temperature: float  # 0.0 to 1.0 (0 = cold, 1 = hot)
    
    def __post_init__(self):
        """Validate that all values are in the expected range."""
        for field_name, value in [("elevation", self.elevation), 
                                  ("moisture", self.moisture), 
                                  ("temperature", self.temperature)]:
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be between 0.0 and 1.0, got {value}")


class EnvironmentalGenerator:
    """
    Generates environmental layer values using multiple noise generators.
    
    This class manages three separate noise generators for elevation, moisture,
    and temperature, and combines them with additional logic to create realistic
    environmental patterns.
    """
    
    def __init__(self, config: Optional[EnvironmentalConfig] = None, seed: Optional[int] = None):
        """
        Initialize the environmental generator.
        
        Args:
            config: Environmental configuration (uses default if None)
            seed: Base seed for noise generation (None for default)
        """
        self.config = config or create_default_environmental_config()
        self.base_seed = seed if seed is not None else 12345
        
        # Create noise generators for each layer
        self._setup_noise_generators()
    
    def _setup_noise_generators(self) -> None:
        """Set up the three noise generators for environmental layers."""
        # Elevation noise generator (primary terrain features)
        elevation_config = NoiseConfig(
            octaves=self.config.elevation_octaves,
            frequency=self.config.elevation_frequency,
            amplitude=1.0,
            persistence=self.config.elevation_persistence,
            lacunarity=self.config.elevation_lacunarity,
            seed=self.base_seed + self.config.elevation_seed_offset
        )
        self.elevation_noise = NoiseGenerator(elevation_config)
        
        # Moisture noise generator (climate patterns)
        moisture_config = NoiseConfig(
            octaves=self.config.moisture_octaves,
            frequency=self.config.moisture_frequency,
            amplitude=1.0,
            persistence=self.config.moisture_persistence,
            lacunarity=self.config.moisture_lacunarity,
            seed=self.base_seed + self.config.moisture_seed_offset
        )
        self.moisture_noise = NoiseGenerator(moisture_config)
        
        # Temperature noise generator (local climate variation)
        temperature_config = NoiseConfig(
            octaves=self.config.temperature_octaves,
            frequency=self.config.temperature_frequency,
            amplitude=1.0,
            persistence=self.config.temperature_persistence,
            lacunarity=self.config.temperature_lacunarity,
            seed=self.base_seed + self.config.temperature_seed_offset
        )
        self.temperature_noise = NoiseGenerator(temperature_config)
    
    def generate_environmental_data(self, x: float, y: float) -> EnvironmentalData:
        """
        Generate environmental data for a specific world coordinate.
        
        Args:
            x: World X coordinate
            y: World Y coordinate
            
        Returns:
            EnvironmentalData containing elevation, moisture, and temperature values
        """
        # Generate base elevation from noise
        elevation_raw = self.elevation_noise.generate(x, y)
        elevation = self._normalize_elevation(elevation_raw)
        
        # Generate base moisture from noise
        moisture_raw = self.moisture_noise.generate(x, y)
        moisture = self._calculate_moisture(moisture_raw, elevation, x, y)
        
        # Generate temperature with latitude influence
        temperature_raw = self.temperature_noise.generate(x, y)
        temperature = self._calculate_temperature(temperature_raw, elevation, y)
        
        return EnvironmentalData(
            elevation=elevation,
            moisture=moisture,
            temperature=temperature
        )
    
    def _normalize_elevation(self, raw_elevation: float) -> float:
        """
        Normalize raw elevation noise to 0.0-1.0 range with proper distribution.

        Args:
            raw_elevation: Raw noise value between -1 and 1

        Returns:
            Normalized elevation between 0.0 and 1.0
        """
        # Convert from [-1, 1] to [0, 1]
        normalized = (raw_elevation + 1.0) / 2.0

        # Apply a curve that creates more water and varied terrain
        # This ensures we get a good distribution of elevations including water
        # Use a power curve that creates more low elevations (water) and high elevations (mountains)
        if normalized < 0.5:
            # Lower half: create more water areas
            curved = math.pow(normalized * 2, 1.5) * 0.5
        else:
            # Upper half: create land with some high elevations
            curved = 0.5 + math.pow((normalized - 0.5) * 2, 0.7) * 0.5

        return max(0.0, min(1.0, curved))
    
    def _calculate_moisture(self, raw_moisture: float, elevation: float, x: float, y: float) -> float:
        """
        Calculate moisture considering base noise, elevation, and water proximity.
        
        Args:
            raw_moisture: Raw noise value between -1 and 1
            elevation: Elevation value between 0.0 and 1.0
            x: World X coordinate
            y: World Y coordinate
            
        Returns:
            Moisture value between 0.0 and 1.0
        """
        # Convert from [-1, 1] to [0, 1]
        base_moisture = (raw_moisture + 1.0) / 2.0
        
        # Increase moisture near water bodies (low elevation areas)
        water_influence = 0.0
        if elevation < 0.35:  # Near or below sea level
            water_distance = abs(elevation - 0.3)  # Distance from sea level
            water_influence = max(0.0, 0.4 * (1.0 - water_distance / 0.05))
        
        # Combine base moisture with water influence
        moisture = base_moisture + water_influence
        
        return max(0.0, min(1.0, moisture))
    
    def _calculate_temperature(self, raw_temperature: float, elevation: float, y: float) -> float:
        """
        Calculate temperature considering base noise, elevation cooling, and latitude.
        
        Args:
            raw_temperature: Raw noise value between -1 and 1
            elevation: Elevation value between 0.0 and 1.0
            y: World Y coordinate (for latitude calculation)
            
        Returns:
            Temperature value between 0.0 and 1.0
        """
        # Convert from [-1, 1] to [0, 1]
        base_temperature = (raw_temperature + 1.0) / 2.0
        
        # Apply latitude influence (distance from equator)
        latitude_distance = abs(y - self.config.world_equator_y) / self.config.world_scale
        latitude_cooling = self.config.temperature_latitude_influence * latitude_distance
        
        # Apply elevation cooling (higher elevations are cooler)
        elevation_cooling = 0.3 * max(0.0, elevation - 0.5)  # Cooling starts above mid-elevation
        
        # Combine all temperature factors
        temperature = base_temperature - latitude_cooling - elevation_cooling
        
        return max(0.0, min(1.0, temperature))
    
    def generate_chunk_environmental_data(self, chunk_x: int, chunk_y: int, size: int) -> List[List[EnvironmentalData]]:
        """
        Generate environmental data for an entire chunk.
        
        Args:
            chunk_x: Chunk X coordinate
            chunk_y: Chunk Y coordinate
            size: Size of the chunk (width and height)
            
        Returns:
            2D list of EnvironmentalData for the chunk
        """
        environmental_data = []
        
        # Calculate world coordinates for the chunk
        world_start_x = chunk_x * size
        world_start_y = chunk_y * size
        
        for y in range(size):
            row = []
            for x in range(size):
                world_x = world_start_x + x
                world_y = world_start_y + y
                env_data = self.generate_environmental_data(world_x, world_y)
                row.append(env_data)
            environmental_data.append(row)
        
        return environmental_data


def create_default_environmental_generator(seed: Optional[int] = None) -> EnvironmentalGenerator:
    """
    Create an environmental generator with default configuration.
    
    Args:
        seed: Optional seed for reproducible generation
        
    Returns:
        EnvironmentalGenerator instance with default settings
    """
    return EnvironmentalGenerator(seed=seed)


def create_detailed_environmental_generator(seed: Optional[int] = None) -> EnvironmentalGenerator:
    """
    Create an environmental generator with detailed configuration.
    
    Args:
        seed: Optional seed for reproducible generation
        
    Returns:
        EnvironmentalGenerator instance with detailed settings
    """
    from .environmental_config import create_detailed_environmental_config
    config = create_detailed_environmental_config()
    return EnvironmentalGenerator(config, seed)
