"""
Core type definitions for the three-tier world generation system.

This module defines enums, dataclasses, and type aliases used throughout
the world generation system for type safety and consistency.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import NamedTuple, Tuple


class ViewScale(Enum):
    """
    Enumeration of the three viewing scales in the world generation system.
    
    Each scale represents a different level of detail and zoom:
    - WORLD: Continental view showing 8x6 sectors
    - REGIONAL: Sector detail showing 32x32 blocks  
    - LOCAL: Block detail showing 32x32 chunks
    """
    WORLD = auto()
    REGIONAL = auto()
    LOCAL = auto()


class WorldLayer(Enum):
    """
    Enumeration of vertical world layers for 3D world representation.
    
    Represents different elevation levels that can be viewed:
    - UNDERGROUND: Below-surface features (caves, minerals)
    - SURFACE: Ground level terrain (default view)
    - MOUNTAINS: Elevated terrain and peaks
    """
    UNDERGROUND = auto()
    SURFACE = auto()
    MOUNTAINS = auto()


class TerrainType(Enum):
    """
    Enumeration of terrain types used across all scales.
    
    Each terrain type has visual and gameplay properties:
    - OCEAN: Deep water, impassable
    - COASTAL: Shallow water, coastal areas
    - PLAINS: Flat grassland, easy movement
    - FOREST: Wooded areas, moderate movement
    - HILLS: Rolling terrain, slower movement
    - MOUNTAINS: High elevation, difficult terrain
    - DESERT: Arid regions, special movement rules
    - TUNDRA: Cold regions, harsh conditions
    """
    OCEAN = auto()
    COASTAL = auto()
    PLAINS = auto()
    FOREST = auto()
    HILLS = auto()
    MOUNTAINS = auto()
    DESERT = auto()
    TUNDRA = auto()


class ClimateZone(Enum):
    """
    Enumeration of climate zones for world generation.
    
    Climate affects terrain distribution and characteristics:
    - ARCTIC: Extreme cold, tundra and ice
    - TEMPERATE: Moderate climate, varied terrain
    - TROPICAL: Warm and humid, dense vegetation
    - ARID: Hot and dry, desert conditions
    """
    ARCTIC = auto()
    TEMPERATE = auto()
    TROPICAL = auto()
    ARID = auto()


class Coordinate(NamedTuple):
    """
    Immutable coordinate pair for position tracking.
    
    Used for all position calculations across different scales.
    Provides type safety and immutability for coordinate operations.
    
    Attributes:
        x: Horizontal position
        y: Vertical position
    """
    x: int
    y: int
    
    def __add__(self, other: 'Coordinate') -> 'Coordinate':
        """Add two coordinates component-wise."""
        return Coordinate(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Coordinate') -> 'Coordinate':
        """Subtract two coordinates component-wise."""
        return Coordinate(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar: int) -> 'Coordinate':
        """Multiply coordinate by scalar."""
        return Coordinate(self.x * scalar, self.y * scalar)


class WorldCoordinate(NamedTuple):
    """
    World-scale coordinate (sector-level positioning).
    
    Represents position in the 8x6 world sector grid.
    Valid ranges: x=[0,7], y=[0,5]
    """
    x: int
    y: int


class RegionalCoordinate(NamedTuple):
    """
    Regional-scale coordinate (block-level positioning).
    
    Represents position within a 32x32 block grid inside a sector.
    Valid ranges: x=[0,31], y=[0,31]
    """
    x: int
    y: int


class LocalCoordinate(NamedTuple):
    """
    Local-scale coordinate (chunk-level positioning).
    
    Represents position within a 32x32 chunk grid inside a block.
    Valid ranges: x=[0,31], y=[0,31]
    """
    x: int
    y: int


@dataclass
class ColorRGB:
    """
    RGB color representation for rendering.
    
    Provides type-safe color handling with validation.
    All components should be in range [0, 255].
    
    Attributes:
        r: Red component (0-255)
        g: Green component (0-255)  
        b: Blue component (0-255)
    """
    r: int
    g: int
    b: int
    
    def __post_init__(self) -> None:
        """Validate color component ranges."""
        for component in [self.r, self.g, self.b]:
            if not 0 <= component <= 255:
                raise ValueError(f"Color component {component} out of range [0, 255]")
    
    def as_tuple(self) -> Tuple[int, int, int]:
        """Return color as tuple for tcod compatibility."""
        return (self.r, self.g, self.b)


@dataclass
class CameraPosition:
    """
    Camera position and state for a specific scale.
    
    Tracks camera location and viewing parameters for each scale level.
    Used by the multi-scale camera system.
    
    Attributes:
        position: Current camera position
        scale: Which scale this camera is viewing
        bounds_width: Maximum width for bounds checking
        bounds_height: Maximum height for bounds checking
    """
    position: Coordinate
    scale: ViewScale
    bounds_width: int
    bounds_height: int
    
    def is_in_bounds(self, pos: Coordinate) -> bool:
        """Check if a position is within camera bounds."""
        return (0 <= pos.x < self.bounds_width and 
                0 <= pos.y < self.bounds_height)


# Type aliases for clarity
Seed = int
NoiseValue = float
Frequency = float
Octaves = int

# Scale conversion constants - Expanded world size for proper scrolling
WORLD_SECTORS_X = 64  # Much larger world for scrolling
WORLD_SECTORS_Y = 48
REGIONAL_BLOCKS_SIZE = 32
LOCAL_CHUNKS_SIZE = 32
SECTOR_PIXEL_SIZE = 16  # 16x16 pixels per sector in world view

# Console dimensions
WORLD_VIEW_WIDTH = 128
WORLD_VIEW_HEIGHT = 96
