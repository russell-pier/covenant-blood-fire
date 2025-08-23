"""
World scale generator for continental-level world features.

This module generates the highest level of the world hierarchy, creating
continental features, ocean basins, major mountain ranges, and climate zones.
"""

import time
from typing import Dict, Tuple, Optional

from ..data.world_data import WorldSectorData, WorldMapData, WORLD_TERRAIN_TYPES, get_terrain_type_for_elevation
from ..data.scale_types import ViewScale
from ..data.config import get_world_config
from .base_generator import HierarchicalNoiseGenerator


class WorldScaleGenerator:
    """Generates continental-scale world features."""
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the world scale generator.
        
        Args:
            seed: Seed for world generation (None to use config)
        """
        config = get_world_config()
        
        if seed is None:
            seed = config.get_world_seed()
        
        self.seed = seed
        self.noise = HierarchicalNoiseGenerator(seed)
        
        # World configuration
        self.world_size_sectors = config.get_world_size()
        self.sector_size_tiles = 16384  # Each sector = 16,384×16,384 tiles
        
        # Generation cache
        self.world_map_data: Optional[WorldMapData] = None
        
        # Climate configuration
        self.equator_y = self.world_size_sectors[1] * self.sector_size_tiles // 2
        self.polar_threshold = 0.7  # Distance from equator for polar climate
        self.tropical_threshold = 0.3  # Distance from equator for tropical climate
    
    def generate_complete_world_map(self) -> WorldMapData:
        """
        Generate entire world map with all sectors.
        
        Returns:
            Complete WorldMapData with all sectors generated
        """
        if self.world_map_data and self.world_map_data.generation_complete:
            return self.world_map_data
        
        start_time = time.time()
        sectors = {}
        
        print(f"Generating {self.world_size_sectors[0]}×{self.world_size_sectors[1]} world map...")
        
        # Generate all sectors
        total_sectors = self.world_size_sectors[0] * self.world_size_sectors[1]
        generated = 0
        
        for sector_y in range(self.world_size_sectors[1]):
            for sector_x in range(self.world_size_sectors[0]):
                sectors[(sector_x, sector_y)] = self.generate_world_sector(
                    sector_x, sector_y
                )
                generated += 1
                
                # Progress reporting
                if generated % 32 == 0 or generated == total_sectors:
                    progress = (generated / total_sectors) * 100
                    print(f"World generation progress: {progress:.1f}% ({generated}/{total_sectors})")
        
        self.world_map_data = WorldMapData(
            world_seed=self.seed,
            world_size_sectors=self.world_size_sectors,
            sectors=sectors,
            generation_start_time=start_time
        )
        
        self.world_map_data.mark_complete()
        
        generation_time = self.world_map_data.get_generation_time()
        print(f"World generation complete in {generation_time:.2f} seconds")
        
        return self.world_map_data
    
    def generate_world_sector(self, sector_x: int, sector_y: int) -> WorldSectorData:
        """
        Generate single world sector using deterministic noise.
        
        Args:
            sector_x: Sector X coordinate
            sector_y: Sector Y coordinate
            
        Returns:
            WorldSectorData for the specified sector
        """
        # Calculate world coordinates for sector center
        center_world_x = sector_x * self.sector_size_tiles + (self.sector_size_tiles // 2)
        center_world_y = sector_y * self.sector_size_tiles + (self.sector_size_tiles // 2)
        
        # Sample continental features using multiple noise layers
        continental = self.noise.continental_noise(center_world_x, center_world_y)
        tectonic = self.noise.tectonic_noise(center_world_x, center_world_y)
        climate_var = self.noise.climate_noise(center_world_x, center_world_y)
        
        # Calculate base elevation from continental drift
        base_elevation = continental * 2000  # ±2000m base elevation
        
        # Add tectonic activity (always positive for mountain building)
        tectonic_elevation = abs(tectonic) * 1500  # 0-1500m from tectonics
        
        # Combine elevations
        total_elevation = base_elevation + tectonic_elevation
        
        # Determine climate zone based on latitude
        latitude_factor = abs(center_world_y - self.equator_y) / (self.world_size_sectors[1] * self.sector_size_tiles // 2)
        
        if latitude_factor > self.polar_threshold:
            climate_zone = "polar"
        elif latitude_factor < self.tropical_threshold:
            climate_zone = "tropical"
        else:
            climate_zone = "temperate"
        
        # Get terrain type based on elevation and climate
        terrain_type = get_terrain_type_for_elevation(total_elevation, climate_zone)
        
        # Apply climate variation for land terrain
        if total_elevation > 0 and climate_var < -0.3:
            # Dry climate variation creates deserts
            if climate_zone in ["tropical", "temperate"]:
                terrain_type = "desert"
        
        # Get display properties
        terrain_props = WORLD_TERRAIN_TYPES.get(terrain_type, WORLD_TERRAIN_TYPES["temperate_land"])
        
        # Determine major features
        has_mountains = abs(tectonic) > 0.6  # High tectonic activity
        has_rivers = (200 < total_elevation < 1500 and 
                     continental > -0.3 and 
                     climate_var > -0.2)  # Good river conditions
        
        # Continental plate ID (8 major plates in a 4x4 grid pattern)
        plate_id = ((sector_x // 4) * 4 + (sector_y // 4)) % 8
        
        return WorldSectorData(
            sector_x=sector_x,
            sector_y=sector_y,
            dominant_terrain=terrain_type,
            average_elevation=total_elevation,
            climate_zone=climate_zone,
            display_char=terrain_props["char"],
            display_color=terrain_props["fg"],
            display_bg_color=terrain_props["bg"],
            has_major_mountain_range=has_mountains,
            has_major_river_system=has_rivers,
            continental_plate_id=plate_id,
            generation_time=time.time(),
            parent_seed=self.seed
        )
    
    def get_sector_at_world_coordinates(self, world_x: int, world_y: int) -> Optional[WorldSectorData]:
        """
        Get sector data for world coordinates.
        
        Args:
            world_x: World X coordinate in tiles
            world_y: World Y coordinate in tiles
            
        Returns:
            WorldSectorData if available, None otherwise
        """
        sector_x = world_x // self.sector_size_tiles
        sector_y = world_y // self.sector_size_tiles
        
        if self.world_map_data:
            return self.world_map_data.get_sector(sector_x, sector_y)
        
        return None
    
    def clear_cache(self) -> None:
        """Clear cached world data to free memory."""
        self.world_map_data = None
        self.noise.clear_cache()
    
    def get_world_info(self) -> Dict[str, any]:
        """
        Get information about the generated world.
        
        Returns:
            Dictionary with world statistics and information
        """
        if not self.world_map_data or not self.world_map_data.is_complete():
            return {"status": "not_generated"}
        
        # Count terrain types
        terrain_counts = {}
        climate_counts = {}
        total_elevation = 0
        mountain_ranges = 0
        river_systems = 0
        
        for sector_data in self.world_map_data.sectors.values():
            # Count terrain types
            terrain = sector_data.dominant_terrain
            terrain_counts[terrain] = terrain_counts.get(terrain, 0) + 1
            
            # Count climate zones
            climate = sector_data.climate_zone
            climate_counts[climate] = climate_counts.get(climate, 0) + 1
            
            # Accumulate statistics
            total_elevation += sector_data.average_elevation
            if sector_data.has_major_mountain_range:
                mountain_ranges += 1
            if sector_data.has_major_river_system:
                river_systems += 1
        
        total_sectors = len(self.world_map_data.sectors)
        avg_elevation = total_elevation / total_sectors if total_sectors > 0 else 0
        
        return {
            "status": "complete",
            "seed": self.seed,
            "world_size": self.world_size_sectors,
            "total_sectors": total_sectors,
            "average_elevation": avg_elevation,
            "terrain_distribution": terrain_counts,
            "climate_distribution": climate_counts,
            "major_mountain_ranges": mountain_ranges,
            "major_river_systems": river_systems,
            "generation_time": self.world_map_data.get_generation_time()
        }
