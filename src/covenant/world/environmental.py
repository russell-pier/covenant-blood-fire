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

    elevation: float    # In meters (-200 = deep caves, 0 = sea level, 3000 = highest mountains)
    moisture: float     # 0.0 to 1.0 (0 = desert dry, 1 = swamp wet)
    temperature: float  # In Celsius (-20°C = arctic, 40°C = desert)

    def __post_init__(self):
        """Validate that all values are in the expected range."""
        if not -200 <= self.elevation <= 3000:
            raise ValueError(f"elevation must be between -200 and 3000 meters, got {self.elevation}")
        if not 0.0 <= self.moisture <= 1.0:
            raise ValueError(f"moisture must be between 0.0 and 1.0, got {self.moisture}")
        if not -20 <= self.temperature <= 40:
            raise ValueError(f"temperature must be between -20 and 40°C, got {self.temperature}")


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
        Convert raw elevation noise to meters with proper distribution.

        Args:
            raw_elevation: Raw noise value between -1 and 1

        Returns:
            Elevation in meters between -200 and 3000
        """
        # Convert from [-1, 1] to [0, 1]
        normalized = (raw_elevation + 1.0) / 2.0

        # Apply a curve that creates more water and varied terrain
        # This ensures we get a good distribution of elevations including water
        if normalized < 0.3:
            # Lower 30%: underwater and caves (-200 to 0m)
            curved = math.pow(normalized / 0.3, 1.5) * 0.3
            elevation_meters = -200 + curved * 200
        elif normalized < 0.6:
            # Middle 30%: low land (0 to 800m)
            curved = (normalized - 0.3) / 0.3
            elevation_meters = curved * 800
        else:
            # Upper 40%: hills and mountains (800 to 3000m) - expanded for more mountains
            curved = math.pow((normalized - 0.6) / 0.4, 0.7)
            elevation_meters = 800 + curved * 2200

        return max(-200, min(3000, elevation_meters))
    
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
        Calculate temperature in Celsius considering base noise, elevation cooling, and latitude.

        Args:
            raw_temperature: Raw noise value between -1 and 1
            elevation: Elevation value in meters
            y: World Y coordinate (for latitude calculation)

        Returns:
            Temperature value in Celsius between -20 and 40
        """
        # Convert from [-1, 1] to base temperature range (0°C to 30°C)
        base_temperature = 15 + (raw_temperature * 15)  # 0°C to 30°C base range

        # Apply latitude influence (distance from equator)
        latitude_distance = abs(y - self.config.world_equator_y) / self.config.world_scale
        latitude_cooling = self.config.temperature_latitude_influence * latitude_distance * 60  # Scale to Celsius

        # Apply elevation cooling (6.5°C per 1000m is realistic lapse rate)
        elevation_cooling = max(0, elevation) * 0.0065  # 6.5°C per 1000m

        # Combine all temperature factors
        temperature = base_temperature - latitude_cooling - elevation_cooling

        return max(-20, min(40, temperature))
    
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
