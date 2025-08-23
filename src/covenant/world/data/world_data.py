"""
World scale data structures for continental-level world generation.

This module defines the data structures used to represent world-scale features
like continents, oceans, mountain ranges, and climate zones.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional


@dataclass
class WorldSectorData:
    """Continental-scale data for world map display."""
    sector_x: int
    sector_y: int
    
    # Geographic features (simplified for world view)
    dominant_terrain: str  # "ocean", "continent", "mountains", "desert", etc.
    average_elevation: float  # Average elevation in meters
    climate_zone: str  # "tropical", "temperate", "polar"
    
    # Visual representation
    display_char: str
    display_color: Tuple[int, int, int]  # RGB foreground color
    display_bg_color: Tuple[int, int, int]  # RGB background color
    
    # Continental features
    has_major_mountain_range: bool
    has_major_river_system: bool
    continental_plate_id: int
    
    # Metadata
    generation_time: float = field(default_factory=time.time)  # When this was generated
    parent_seed: int = 0  # World seed used
    
    def __post_init__(self):
        """Validate data after initialization."""
        if not isinstance(self.sector_x, int) or not isinstance(self.sector_y, int):
            raise ValueError("Sector coordinates must be integers")
        if not (0 <= self.display_color[0] <= 255 and 
                0 <= self.display_color[1] <= 255 and 
                0 <= self.display_color[2] <= 255):
            raise ValueError("Display color values must be 0-255")
        if not (0 <= self.display_bg_color[0] <= 255 and 
                0 <= self.display_bg_color[1] <= 255 and 
                0 <= self.display_bg_color[2] <= 255):
            raise ValueError("Display background color values must be 0-255")


@dataclass
class WorldMapData:
    """Complete world map data."""
    world_seed: int
    world_size_sectors: Tuple[int, int]  # Default: (16, 16)
    sectors: Dict[Tuple[int, int], WorldSectorData] = field(default_factory=dict)
    generation_complete: bool = False
    generation_start_time: float = field(default_factory=time.time)
    generation_end_time: Optional[float] = None
    
    def __post_init__(self):
        """Validate world map data after initialization."""
        if self.world_size_sectors[0] <= 0 or self.world_size_sectors[1] <= 0:
            raise ValueError("World size must have positive dimensions")
        
        # Validate that all sectors are within bounds
        max_x, max_y = self.world_size_sectors
        for (sector_x, sector_y) in self.sectors.keys():
            if not (0 <= sector_x < max_x and 0 <= sector_y < max_y):
                raise ValueError(f"Sector ({sector_x}, {sector_y}) is outside world bounds")
    
    def get_sector(self, sector_x: int, sector_y: int) -> Optional[WorldSectorData]:
        """
        Get sector data for specific coordinates.
        
        Args:
            sector_x: Sector X coordinate
            sector_y: Sector Y coordinate
            
        Returns:
            WorldSectorData if exists, None otherwise
        """
        return self.sectors.get((sector_x, sector_y))
    
    def set_sector(self, sector_data: WorldSectorData) -> None:
        """
        Set sector data for specific coordinates.
        
        Args:
            sector_data: WorldSectorData to store
        """
        key = (sector_data.sector_x, sector_data.sector_y)
        self.sectors[key] = sector_data
    
    def is_complete(self) -> bool:
        """
        Check if world generation is complete.
        
        Returns:
            True if all sectors have been generated
        """
        expected_sectors = self.world_size_sectors[0] * self.world_size_sectors[1]
        return len(self.sectors) == expected_sectors and self.generation_complete
    
    def mark_complete(self) -> None:
        """Mark world generation as complete and record end time."""
        self.generation_complete = True
        self.generation_end_time = time.time()
    
    def get_generation_time(self) -> Optional[float]:
        """
        Get total generation time in seconds.
        
        Returns:
            Generation time in seconds, or None if not complete
        """
        if self.generation_end_time is None:
            return None
        return self.generation_end_time - self.generation_start_time


# Terrain type constants for world-scale features
WORLD_TERRAIN_TYPES = {
    "deep_ocean": {
        "char": "~",
        "fg": (0, 100, 200),
        "bg": (0, 50, 100),
        "elevation_range": (-2000, -500)
    },
    "shallow_ocean": {
        "char": "≈",
        "fg": (50, 150, 255),
        "bg": (25, 75, 150),
        "elevation_range": (-500, 0)
    },
    "coastal_plains": {
        "char": ".",
        "fg": (100, 180, 100),
        "bg": (50, 120, 50),
        "elevation_range": (0, 200)
    },
    "temperate_land": {
        "char": ".",
        "fg": (100, 180, 100),
        "bg": (50, 120, 50),
        "elevation_range": (200, 1000)
    },
    "tropical": {
        "char": "♠",
        "fg": (0, 150, 0),
        "bg": (0, 80, 0),
        "elevation_range": (0, 800)
    },
    "desert": {
        "char": "·",
        "fg": (218, 165, 32),
        "bg": (184, 134, 11),
        "elevation_range": (0, 1200)
    },
    "mountains": {
        "char": "^",
        "fg": (160, 140, 120),
        "bg": (100, 80, 60),
        "elevation_range": (1000, 2500)
    },
    "high_mountains": {
        "char": "▲",
        "fg": (200, 180, 160),
        "bg": (120, 100, 80),
        "elevation_range": (2500, 5000)
    },
    "tundra": {
        "char": "∘",
        "fg": (200, 200, 255),
        "bg": (150, 150, 200),
        "elevation_range": (0, 1000)
    }
}


def get_terrain_type_for_elevation(elevation: float, climate_zone: str = "temperate") -> str:
    """
    Determine terrain type based on elevation and climate.

    Args:
        elevation: Elevation in meters
        climate_zone: Climate zone ("tropical", "temperate", "polar")

    Returns:
        Terrain type string
    """
    # Ocean levels
    if elevation < -500:
        return "deep_ocean"
    elif elevation < 0:
        return "shallow_ocean"

    # Land terrain based on elevation and climate
    if elevation > 2500:
        return "high_mountains"
    elif elevation > 1000:
        return "mountains"
    elif climate_zone == "polar":
        return "tundra"
    elif climate_zone == "tropical" and elevation < 800:
        return "tropical"
    elif elevation < 200:
        return "coastal_plains"
    else:
        return "temperate_land"


# Regional terrain type constants
REGIONAL_TERRAIN_TYPES = {
    "plains": {
        "char": ".",
        "fg": (100, 150, 100),
        "bg": (50, 75, 50),
        "description": "Open grasslands and plains"
    },
    "hills": {
        "char": "n",
        "fg": (120, 100, 80),
        "bg": (80, 60, 40),
        "description": "Rolling hills and elevated terrain"
    },
    "forest": {
        "char": "♠",
        "fg": (0, 120, 0),
        "bg": (0, 60, 0),
        "description": "Dense forest coverage"
    },
    "marsh": {
        "char": "≋",
        "fg": (80, 120, 80),
        "bg": (40, 80, 40),
        "description": "Wetlands and marshes"
    },
    "rocky": {
        "char": "∩",
        "fg": (140, 120, 100),
        "bg": (100, 80, 60),
        "description": "Rocky outcrops and stone"
    },
    "fertile": {
        "char": "♦",
        "fg": (120, 180, 60),
        "bg": (80, 120, 40),
        "description": "Fertile farmland"
    },
    "barren": {
        "char": "·",
        "fg": (160, 140, 100),
        "bg": (120, 100, 70),
        "description": "Barren and dry land"
    },
    "water": {
        "char": "~",
        "fg": (60, 120, 200),
        "bg": (30, 80, 150),
        "description": "Rivers and lakes"
    }
}
