"""
3D Layered World System for underground, surface, and mountain layers.

This module provides the core data structures and enums for the 3D layered
world system that allows players to explore underground caves, surface terrain,
and mountain peaks in a single integrated world.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Tuple, Optional, List

from .terrain import TerrainType


class WorldLayer(Enum):
    """Enumeration of the three world layers."""
    UNDERGROUND = 0
    SURFACE = 1  
    MOUNTAINS = 2


@dataclass
class TerrainData:
    """Enhanced terrain data for layered world system."""
    terrain_type: TerrainType
    char: str
    fg_color: Tuple[int, int, int]
    bg_color: Tuple[int, int, int]
    elevation: float
    is_passable: bool = True
    is_entrance: bool = False
    resource: Optional['ResourceNode'] = None  # Resource data if present


@dataclass
class LayeredTerrainData:
    """Terrain data for all three layers at a single world position."""
    underground: TerrainData
    surface: TerrainData 
    mountains: Optional[TerrainData]  # None if no mountain layer
    
    # Layer connectivity
    has_cave_entrance: bool = False
    has_mountain_access: bool = False


# Enhanced terrain configurations for all layers
TERRAIN_CONFIGS = {
    # Underground terrains
    TerrainType.CAVE_FLOOR: {
        'chars': [".", "·", "∘"],
        'base_fg': (120, 100, 80),
        'base_bg': (40, 30, 20)
    },
    TerrainType.CAVE_WALL: {
        'chars': ["█", "▓", "▒"],
        'base_fg': (15, 15, 15),  # Much darker, almost black
        'base_bg': (5, 5, 5)      # Very dark background
    },
    TerrainType.UNDERGROUND_WATER: {
        'chars': ["~", "≈", "∼"],
        'base_fg': (50, 100, 150),
        'base_bg': (10, 30, 60)
    },
    TerrainType.ORE_VEIN: {
        'chars': ["*", "◊", "♦"],
        'base_fg': (200, 180, 100),
        'base_bg': (80, 60, 40)
    },
    
    # Surface terrains (enhanced from existing)
    TerrainType.GRASS: {
        'chars': [".", "·", ",", "'", "`"],
        'base_fg': (50, 120, 50),
        'base_bg': (20, 80, 20)
    },
    TerrainType.LIGHT_GRASS: {
        'chars': [".", "·", ",", "'", "`"],
        'base_fg': (70, 140, 70),
        'base_bg': (30, 90, 30)
    },
    TerrainType.DARK_GRASS: {
        'chars': [".", "·", ",", "'", "`"],
        'base_fg': (30, 100, 30),
        'base_bg': (10, 70, 10)
    },
    TerrainType.FOREST: {
        'chars': ["♠", "♣", "T", "Y", "†"],
        'base_fg': (0, 100, 0),
        'base_bg': (10, 60, 10)
    },
    TerrainType.DEEP_WATER: {
        'chars': ["~", "≈", "∼", "◦"],
        'base_fg': (100, 150, 255),
        'base_bg': (0, 50, 150)
    },
    TerrainType.SHALLOW_WATER: {
        'chars': ["~", "≈", "∼", "◦"],
        'base_fg': (120, 170, 255),
        'base_bg': (20, 70, 170)
    },
    TerrainType.SAND: {
        'chars': [".", "·", "∘", "°"],
        'base_fg': (200, 180, 120),
        'base_bg': (160, 140, 80)
    },
    TerrainType.DESERT: {
        'chars': [".", "·", "∘", "°"],
        'base_fg': (220, 200, 140),
        'base_bg': (180, 160, 100)
    },
    TerrainType.HILLS: {
        'chars': ["^", "∩", "⩙"],
        'base_fg': (100, 80, 60),
        'base_bg': (60, 40, 20)
    },
    TerrainType.MOUNTAINS: {
        'chars': ["▲", "⩙", "∩"],
        'base_fg': (120, 100, 80),
        'base_bg': (80, 60, 40)
    },
    
    # Special surface terrains
    TerrainType.CAVE_ENTRANCE: {
        'chars': ["○", "◯", "●"],
        'base_fg': (150, 150, 150),
        'base_bg': (0, 0, 0)
    },
    TerrainType.MOUNTAIN_BASE: {
        'chars': ["▓", "▒", "░"],
        'base_fg': (100, 80, 60),
        'base_bg': (60, 40, 20)
    },
    
    # Mountain terrains
    TerrainType.MOUNTAIN_PEAK: {
        'chars': ["▲", "⩙", "∩"],
        'base_fg': (180, 160, 140),
        'base_bg': (120, 100, 80)
    },
    TerrainType.MOUNTAIN_SLOPE: {
        'chars': ["^", "/", "\\"],
        'base_fg': (140, 120, 100),
        'base_bg': (100, 80, 60)
    },
    TerrainType.MOUNTAIN_CLIFF: {
        'chars': ["█", "▓", "▒"],
        'base_fg': (100, 80, 60),
        'base_bg': (60, 40, 20)
    },
    TerrainType.SNOW: {
        'chars': ["*", "·", "∘"],
        'base_fg': (240, 240, 255),
        'base_bg': (200, 200, 220)
    }
}


def get_terrain_config(terrain_type: TerrainType) -> Dict:
    """
    Get terrain configuration for a given terrain type.
    
    Args:
        terrain_type: The terrain type to get configuration for
        
    Returns:
        Dictionary containing terrain configuration
        
    Raises:
        KeyError: If terrain type is not configured
    """
    if terrain_type in TERRAIN_CONFIGS:
        return TERRAIN_CONFIGS[terrain_type]
    
    # Fallback to basic grass configuration for unknown types
    return TERRAIN_CONFIGS[TerrainType.GRASS]


def create_terrain_data(
    terrain_type: TerrainType, 
    world_x: int, 
    world_y: int, 
    elevation: float,
    noise_generator=None
) -> TerrainData:
    """
    Create terrain data with variations based on world position.
    
    Args:
        terrain_type: The type of terrain to create
        world_x: World X coordinate for variation
        world_y: World Y coordinate for variation
        elevation: Elevation value for the terrain
        noise_generator: Optional noise generator for variations
        
    Returns:
        TerrainData instance with appropriate variations
    """
    config = get_terrain_config(terrain_type)
    
    # Select character variant (simple hash-based selection if no noise generator)
    if noise_generator:
        char_noise = noise_generator.generate(world_x * 0.3, world_y * 0.3)
        char_index = int((char_noise + 1) * 0.5 * len(config['chars'])) % len(config['chars'])
        color_variation = int(noise_generator.generate(world_x * 0.1, world_y * 0.1) * 20)
    else:
        # Simple hash-based variation
        char_index = (world_x * 7 + world_y * 13) % len(config['chars'])
        color_variation = ((world_x * 3 + world_y * 5) % 40) - 20
    
    # Apply color variations
    fg_color = tuple(max(0, min(255, c + color_variation)) for c in config['base_fg'])
    bg_color = tuple(max(0, min(255, c + color_variation // 2)) for c in config['base_bg'])
    
    # Determine passability
    is_passable = terrain_type not in [
        TerrainType.CAVE_WALL, 
        TerrainType.DEEP_WATER, 
        TerrainType.MOUNTAIN_CLIFF
    ]
    
    # Determine if this is an entrance
    is_entrance = terrain_type in [
        TerrainType.CAVE_ENTRANCE, 
        TerrainType.MOUNTAIN_BASE
    ]
    
    return TerrainData(
        terrain_type=terrain_type,
        char=config['chars'][char_index],
        fg_color=fg_color,
        bg_color=bg_color,
        elevation=elevation,
        is_passable=is_passable,
        is_entrance=is_entrance
    )
