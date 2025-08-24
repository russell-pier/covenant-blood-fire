"""
Scale type definitions for the three-tier world generation system.

This module defines the core types and configurations for the hierarchical
world generation system with three viewing scales: World, Regional, and Local.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Tuple


class ViewScale(Enum):
    """Three viewing scales for hierarchical world generation."""
    WORLD = "world"      # 1 pixel = 1 sector (16,384×16,384 tiles)
    REGIONAL = "regional" # 1 pixel = 1 block (1,024×1,024 tiles)  
    LOCAL = "local"      # 1 pixel = 1 chunk (32×32 tiles)


class WorldLayer(Enum):
    """3D world layers (preserved from existing system)."""
    UNDERGROUND = 0
    SURFACE = 1  
    MOUNTAINS = 2


@dataclass
class ScaleConfig:
    """Configuration for each viewing scale."""
    name: str
    pixels_per_unit: int     # How many tiles per pixel
    map_size: Tuple[int, int]  # Width×height in units
    cache_lifetime: float    # Seconds to cache data
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.pixels_per_unit <= 0:
            raise ValueError("pixels_per_unit must be positive")
        if self.map_size[0] <= 0 or self.map_size[1] <= 0:
            raise ValueError("map_size dimensions must be positive")
        if self.cache_lifetime < 0:
            raise ValueError("cache_lifetime must be non-negative")


# Default scale configurations
DEFAULT_SCALE_CONFIGS = {
    ViewScale.WORLD: ScaleConfig("World", 16384, (8, 6), 300.0),
    ViewScale.REGIONAL: ScaleConfig("Regional", 1024, (32, 32), 60.0),
    ViewScale.LOCAL: ScaleConfig("Local", 32, (32, 32), 10.0)
}


def get_scale_config(scale: ViewScale) -> ScaleConfig:
    """
    Get the configuration for a specific scale.
    
    Args:
        scale: The viewing scale to get configuration for
        
    Returns:
        ScaleConfig instance for the specified scale
    """
    return DEFAULT_SCALE_CONFIGS[scale]


def get_world_coordinates_for_scale(scale: ViewScale, x: int, y: int) -> Tuple[int, int]:
    """
    Convert scale-specific coordinates to world tile coordinates.
    
    Args:
        scale: The viewing scale
        x: X coordinate in scale units
        y: Y coordinate in scale units
        
    Returns:
        Tuple of (world_x, world_y) in tile coordinates
    """
    config = get_scale_config(scale)
    world_x = x * config.pixels_per_unit
    world_y = y * config.pixels_per_unit
    return world_x, world_y


def get_scale_coordinates_from_world(scale: ViewScale, world_x: int, world_y: int) -> Tuple[int, int]:
    """
    Convert world tile coordinates to scale-specific coordinates.
    
    Args:
        scale: The viewing scale
        world_x: World X coordinate in tiles
        world_y: World Y coordinate in tiles
        
    Returns:
        Tuple of (scale_x, scale_y) in scale units
    """
    config = get_scale_config(scale)
    scale_x = world_x // config.pixels_per_unit
    scale_y = world_y // config.pixels_per_unit
    return scale_x, scale_y
