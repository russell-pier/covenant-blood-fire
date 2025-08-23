"""
World data structures and configuration.

This package contains the data structures and configuration systems
for the three-tier world generation system.
"""

from .scale_types import ViewScale, WorldLayer, ScaleConfig, get_scale_config
from .world_data import WorldSectorData, WorldMapData, WORLD_TERRAIN_TYPES
from .config import WorldConfig, get_world_config

__all__ = [
    'ViewScale',
    'WorldLayer', 
    'ScaleConfig',
    'get_scale_config',
    'WorldSectorData',
    'WorldMapData',
    'WORLD_TERRAIN_TYPES',
    'WorldConfig',
    'get_world_config'
]
