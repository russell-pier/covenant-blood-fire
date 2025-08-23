"""
Regional scale generator for mid-level terrain features.

This module generates the middle tier of the world hierarchy, creating
regional terrain features like hills, valleys, forests, and local climate variations.
"""

import time
from typing import Dict, Tuple, Optional

from ..data.world_data import WorldSectorData
from ..data.scale_types import ViewScale
from ..data.config import get_world_config
from .base_generator import HierarchicalNoiseGenerator
from .world_scale import WorldScaleGenerator


class RegionalBlockData:
    """Data for a single regional block (1024×1024 tiles)."""
    
    def __init__(self, block_x: int, block_y: int, sector_data: WorldSectorData):
        self.block_x = block_x
        self.block_y = block_y
        self.parent_sector = sector_data
        
        # Regional terrain features
        self.terrain_type = "plains"  # Default
        self.elevation_variation = 0.0  # Local elevation variation
        self.moisture_level = 0.5  # 0-1 moisture
        self.temperature_variation = 0.0  # Temperature variation from sector average
        
        # Visual representation
        self.display_char = "."
        self.display_color = (100, 150, 100)
        self.display_bg_color = (50, 75, 50)
        
        # Regional features
        self.has_river = False
        self.has_forest = False
        self.has_hills = False
        self.has_settlement = False
        
        # Generation metadata
        self.generation_time = time.time()


class RegionalMapData:
    """Complete regional map data for a world sector."""
    
    def __init__(self, sector_x: int, sector_y: int, world_seed: int):
        self.sector_x = sector_x
        self.sector_y = sector_y
        self.world_seed = world_seed
        self.regional_size_blocks = (32, 32)  # 32×32 blocks per sector
        self.blocks: Dict[Tuple[int, int], RegionalBlockData] = {}
        self.generation_complete = False
        self.generation_start_time = time.time()
        self.generation_end_time: Optional[float] = None
    
    def get_block(self, block_x: int, block_y: int) -> Optional[RegionalBlockData]:
        """Get block data for specific coordinates."""
        return self.blocks.get((block_x, block_y))
    
    def set_block(self, block_data: RegionalBlockData) -> None:
        """Set block data for specific coordinates."""
        key = (block_data.block_x, block_data.block_y)
        self.blocks[key] = block_data
    
    def is_complete(self) -> bool:
        """Check if regional generation is complete."""
        expected_blocks = self.regional_size_blocks[0] * self.regional_size_blocks[1]
        return len(self.blocks) == expected_blocks and self.generation_complete
    
    def mark_complete(self) -> None:
        """Mark regional generation as complete."""
        self.generation_complete = True
        self.generation_end_time = time.time()


class RegionalScaleGenerator:
    """Generates regional-scale terrain features."""
    
    def __init__(self, world_generator: WorldScaleGenerator, seed: Optional[int] = None):
        """
        Initialize the regional scale generator.
        
        Args:
            world_generator: World scale generator for sector data
            seed: Seed for regional generation (None to use world generator seed)
        """
        self.world_generator = world_generator
        
        if seed is None:
            seed = world_generator.seed
        
        self.seed = seed
        self.noise = HierarchicalNoiseGenerator(seed + 10000)  # Offset for regional noise
        
        # Regional configuration
        self.blocks_per_sector = 32  # 32×32 blocks per sector
        self.block_size_tiles = 1024  # Each block = 1024×1024 tiles
        
        # Generation cache
        self.regional_maps: Dict[Tuple[int, int], RegionalMapData] = {}
        
        # Regional terrain types
        self.regional_terrain_types = {
            "plains": {"char": ".", "fg": (100, 150, 100), "bg": (50, 75, 50)},
            "hills": {"char": "n", "fg": (120, 100, 80), "bg": (80, 60, 40)},
            "forest": {"char": "♠", "fg": (0, 120, 0), "bg": (0, 60, 0)},
            "marsh": {"char": "≋", "fg": (80, 120, 80), "bg": (40, 80, 40)},
            "rocky": {"char": "∩", "fg": (140, 120, 100), "bg": (100, 80, 60)},
            "fertile": {"char": "♦", "fg": (120, 180, 60), "bg": (80, 120, 40)},
            "barren": {"char": "·", "fg": (160, 140, 100), "bg": (120, 100, 70)},
            "water": {"char": "~", "fg": (60, 120, 200), "bg": (30, 80, 150)}
        }
    
    def generate_regional_map(self, sector_x: int, sector_y: int) -> RegionalMapData:
        """
        Generate complete regional map for a world sector.
        
        Args:
            sector_x: World sector X coordinate
            sector_y: World sector Y coordinate
            
        Returns:
            RegionalMapData for the specified sector
        """
        cache_key = (sector_x, sector_y)
        if cache_key in self.regional_maps:
            return self.regional_maps[cache_key]
        
        # Get world sector data
        world_map = self.world_generator.generate_complete_world_map()
        sector_data = world_map.get_sector(sector_x, sector_y)
        
        if sector_data is None:
            raise ValueError(f"No world sector data for ({sector_x}, {sector_y})")
        
        print(f"Generating regional map for sector ({sector_x}, {sector_y})...")
        
        start_time = time.time()
        regional_map = RegionalMapData(sector_x, sector_y, self.seed)
        
        # Generate all blocks in the sector
        for block_y in range(self.blocks_per_sector):
            for block_x in range(self.blocks_per_sector):
                block_data = self.generate_regional_block(
                    sector_x, sector_y, block_x, block_y, sector_data
                )
                regional_map.set_block(block_data)
        
        regional_map.mark_complete()
        self.regional_maps[cache_key] = regional_map
        
        generation_time = time.time() - start_time
        print(f"Regional map generation complete in {generation_time:.2f} seconds")
        
        return regional_map
    
    def generate_regional_block(self, sector_x: int, sector_y: int, 
                              block_x: int, block_y: int, 
                              sector_data: WorldSectorData) -> RegionalBlockData:
        """
        Generate single regional block.
        
        Args:
            sector_x: World sector X coordinate
            sector_y: World sector Y coordinate
            block_x: Block X coordinate within sector
            block_y: Block Y coordinate within sector
            sector_data: Parent world sector data
            
        Returns:
            RegionalBlockData for the specified block
        """
        # Calculate world coordinates for block center
        sector_offset_x = sector_x * self.world_generator.sector_size_tiles
        sector_offset_y = sector_y * self.world_generator.sector_size_tiles
        block_offset_x = block_x * self.block_size_tiles
        block_offset_y = block_y * self.block_size_tiles
        
        center_world_x = sector_offset_x + block_offset_x + (self.block_size_tiles // 2)
        center_world_y = sector_offset_y + block_offset_y + (self.block_size_tiles // 2)
        
        # Sample regional noise
        regional_elevation = self.noise.regional_noise(center_world_x, center_world_y)
        regional_moisture = self.noise.octave_noise(
            center_world_x, center_world_y, octaves=2, 
            base_seed=1000, frequency=0.005
        )
        regional_temperature = self.noise.octave_noise(
            center_world_x, center_world_y, octaves=2, 
            base_seed=2000, frequency=0.003
        )
        
        # Create block data
        block_data = RegionalBlockData(block_x, block_y, sector_data)
        
        # Determine regional terrain based on sector type and local variation
        terrain_type = self._determine_regional_terrain(
            sector_data, regional_elevation, regional_moisture, regional_temperature
        )
        
        # Set terrain properties
        terrain_props = self.regional_terrain_types.get(terrain_type, 
                                                       self.regional_terrain_types["plains"])
        
        block_data.terrain_type = terrain_type
        block_data.elevation_variation = regional_elevation * 100  # ±100m variation
        block_data.moisture_level = max(0, min(1, (regional_moisture + 1) / 2))  # Normalize to 0-1
        block_data.temperature_variation = regional_temperature * 5  # ±5°C variation
        
        block_data.display_char = terrain_props["char"]
        block_data.display_color = terrain_props["fg"]
        block_data.display_bg_color = terrain_props["bg"]
        
        # Determine regional features
        block_data.has_river = self._has_river(center_world_x, center_world_y, sector_data)
        block_data.has_forest = terrain_type == "forest"
        block_data.has_hills = terrain_type == "hills"
        block_data.has_settlement = self._has_settlement(center_world_x, center_world_y)
        
        return block_data
    
    def _determine_regional_terrain(self, sector_data: WorldSectorData, 
                                  elevation: float, moisture: float, 
                                  temperature: float) -> str:
        """
        Determine regional terrain type based on sector and local conditions.
        
        Args:
            sector_data: Parent world sector data
            elevation: Regional elevation variation (-1 to 1)
            moisture: Regional moisture variation (-1 to 1)
            temperature: Regional temperature variation (-1 to 1)
            
        Returns:
            Regional terrain type string
        """
        # Base terrain from world sector
        sector_terrain = sector_data.dominant_terrain
        
        # Water sectors stay water
        if "ocean" in sector_terrain:
            return "water"
        
        # Desert sectors with high moisture become oases or fertile areas
        if sector_terrain == "desert":
            if moisture > 0.3:
                return "fertile" if moisture > 0.6 else "plains"
            else:
                return "barren"
        
        # Mountain sectors
        if "mountain" in sector_terrain:
            if elevation > 0.3:
                return "rocky"
            elif moisture > 0.2:
                return "hills"
            else:
                return "barren"
        
        # Tropical sectors
        if sector_terrain == "tropical":
            if moisture > 0.0:
                return "forest"
            else:
                return "plains"
        
        # Temperate and other land
        if elevation > 0.4:
            return "hills"
        elif moisture > 0.4:
            if moisture > 0.7:
                return "marsh"
            else:
                return "forest"
        elif moisture < -0.3:
            return "barren"
        else:
            return "fertile" if moisture > 0.1 else "plains"
    
    def _has_river(self, world_x: int, world_y: int, sector_data: WorldSectorData) -> bool:
        """Determine if block has a river."""
        if not sector_data.has_major_river_system:
            return False
        
        # Use noise to create river networks
        river_noise = self.noise.octave_noise(world_x, world_y, octaves=1, 
                                            base_seed=5000, frequency=0.001)
        return abs(river_noise) < 0.1  # Thin river lines
    
    def _has_settlement(self, world_x: int, world_y: int) -> bool:
        """Determine if block has a settlement."""
        settlement_noise = self.noise.octave_noise(world_x, world_y, octaves=1, 
                                                 base_seed=6000, frequency=0.0005)
        return settlement_noise > 0.8  # Rare settlements
    
    def get_regional_block_at_world_coordinates(self, world_x: int, world_y: int) -> Optional[RegionalBlockData]:
        """
        Get regional block data for world coordinates.
        
        Args:
            world_x: World X coordinate in tiles
            world_y: World Y coordinate in tiles
            
        Returns:
            RegionalBlockData if available, None otherwise
        """
        # Calculate sector coordinates
        sector_x = world_x // self.world_generator.sector_size_tiles
        sector_y = world_y // self.world_generator.sector_size_tiles
        
        # Calculate block coordinates within sector
        sector_offset_x = world_x % self.world_generator.sector_size_tiles
        sector_offset_y = world_y % self.world_generator.sector_size_tiles
        block_x = sector_offset_x // self.block_size_tiles
        block_y = sector_offset_y // self.block_size_tiles
        
        # Get regional map
        regional_map = self.regional_maps.get((sector_x, sector_y))
        if regional_map:
            return regional_map.get_block(block_x, block_y)
        
        return None
    
    def clear_cache(self) -> None:
        """Clear cached regional data to free memory."""
        self.regional_maps.clear()
        self.noise.clear_cache()
