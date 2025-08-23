"""
Configuration classes for environmental layer generation.

This module provides configuration dataclasses for the three environmental
layers (elevation, moisture, temperature) used in world generation.
"""

from dataclasses import dataclass
from typing import Tuple

# Import config system
try:
    from ..config import get_config_manager
except ImportError:
    # Fallback if config system not available
    get_config_manager = None


@dataclass
class EnvironmentalConfig:
    """Configuration for environmental layer generation."""
    
    # Elevation settings - much smaller frequency for gradual 1m² changes
    elevation_octaves: int = 6
    elevation_frequency: float = 0.0001  # Very gradual elevation changes
    elevation_persistence: float = 0.65
    elevation_lacunarity: float = 2.0
    
    # Moisture settings - gradual changes for realistic weather patterns
    moisture_octaves: int = 3
    moisture_frequency: float = 0.001  # Gradual moisture changes
    moisture_persistence: float = 0.5
    moisture_lacunarity: float = 2.0
    moisture_water_influence_radius: float = 10.0

    # Temperature settings - gradual changes for realistic climate
    temperature_octaves: int = 2
    temperature_frequency: float = 0.0005  # Very gradual temperature changes
    temperature_persistence: float = 0.4
    temperature_lacunarity: float = 2.0
    temperature_latitude_influence: float = 0.3
    
    # Visual variation settings
    color_variation_strength: float = 0.1
    brightness_variation_range: Tuple[float, float] = (0.8, 1.2)
    
    # World settings
    world_equator_y: float = 0.0  # Y coordinate of the equator
    world_scale: float = 1000.0   # Scale factor for latitude calculations
    
    # Seed offsets for different layers (to ensure independence)
    elevation_seed_offset: int = 0
    moisture_seed_offset: int = 1000
    temperature_seed_offset: int = 2000
    variation_seed_offset: int = 3000

    @classmethod
    def from_config(cls) -> 'EnvironmentalConfig':
        """Create EnvironmentalConfig from TOML config files."""
        if get_config_manager:
            config_manager = get_config_manager()
            noise_config = config_manager.get_noise_config()

            if noise_config:
                # Override defaults with config values
                return cls(
                    elevation_octaves=noise_config.get('elevation_octaves', 6),
                    elevation_frequency=noise_config.get('elevation_frequency', 0.025),
                    moisture_octaves=noise_config.get('moisture_octaves', 3),
                    moisture_frequency=noise_config.get('moisture_frequency', 0.05),
                    temperature_octaves=noise_config.get('temperature_octaves', 2),
                    temperature_frequency=noise_config.get('temperature_frequency', 0.04),
                    temperature_latitude_influence=noise_config.get('temperature_latitude_influence', 0.3),
                    # Keep other defaults for now
                )

        # Return default instance if config not available
        return cls()


def create_default_environmental_config() -> EnvironmentalConfig:
    """
    Create an environmental configuration with default values.
    
    Returns:
        EnvironmentalConfig instance with default settings
    """
    return EnvironmentalConfig()


def create_detailed_environmental_config() -> EnvironmentalConfig:
    """
    Create an environmental configuration with more detailed generation.
    
    Returns:
        EnvironmentalConfig instance with higher detail settings
    """
    return EnvironmentalConfig(
        elevation_octaves=8,
        elevation_frequency=0.02,
        elevation_persistence=0.7,
        
        moisture_octaves=4,
        moisture_frequency=0.04,
        moisture_persistence=0.6,
        
        temperature_octaves=3,
        temperature_frequency=0.03,
        temperature_persistence=0.5,
        
        color_variation_strength=0.15
    )


def create_fast_environmental_config() -> EnvironmentalConfig:
    """
    Create an environmental configuration optimized for performance.
    
    Returns:
        EnvironmentalConfig instance with faster generation settings
    """
    return EnvironmentalConfig(
        elevation_octaves=4,
        elevation_frequency=0.03,
        elevation_persistence=0.6,
        
        moisture_octaves=2,
        moisture_frequency=0.06,
        moisture_persistence=0.4,
        
        temperature_octaves=1,
        temperature_frequency=0.05,
        temperature_persistence=0.3,
        
        color_variation_strength=0.05
    )
