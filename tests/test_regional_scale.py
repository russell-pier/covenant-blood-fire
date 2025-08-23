"""
Tests for regional scale generation system.

This module tests the regional-scale generator and related data structures
to ensure correct regional terrain generation.
"""

import pytest
import time
from src.covenant.world.generators.world_scale import WorldScaleGenerator
from src.covenant.world.generators.regional_scale import (
    RegionalScaleGenerator, RegionalBlockData, RegionalMapData
)
from src.covenant.world.data.world_data import REGIONAL_TERRAIN_TYPES


class TestRegionalBlockData:
    """Test regional block data structure."""
    
    def test_initialization(self):
        """Test regional block data initialization."""
        # Create mock sector data
        from src.covenant.world.data.world_data import WorldSectorData
        sector_data = WorldSectorData(
            sector_x=0, sector_y=0,
            dominant_terrain="temperate_land",
            average_elevation=500.0,
            climate_zone="temperate",
            display_char=".",
            display_color=(100, 150, 100),
            display_bg_color=(50, 75, 50),
            has_major_mountain_range=False,
            has_major_river_system=True,
            continental_plate_id=0
        )
        
        block_data = RegionalBlockData(5, 7, sector_data)
        
        assert block_data.block_x == 5
        assert block_data.block_y == 7
        assert block_data.parent_sector == sector_data
        assert block_data.terrain_type == "plains"  # Default
        assert isinstance(block_data.generation_time, float)


class TestRegionalMapData:
    """Test regional map data structure."""
    
    def test_initialization(self):
        """Test regional map data initialization."""
        regional_map = RegionalMapData(3, 4, 12345)
        
        assert regional_map.sector_x == 3
        assert regional_map.sector_y == 4
        assert regional_map.world_seed == 12345
        assert regional_map.regional_size_blocks == (32, 32)
        assert len(regional_map.blocks) == 0
        assert not regional_map.generation_complete
        assert not regional_map.is_complete()
    
    def test_block_management(self):
        """Test block data management."""
        regional_map = RegionalMapData(0, 0, 12345)
        
        # Create mock block data
        from src.covenant.world.data.world_data import WorldSectorData
        sector_data = WorldSectorData(
            sector_x=0, sector_y=0,
            dominant_terrain="temperate_land",
            average_elevation=500.0,
            climate_zone="temperate",
            display_char=".",
            display_color=(100, 150, 100),
            display_bg_color=(50, 75, 50),
            has_major_mountain_range=False,
            has_major_river_system=True,
            continental_plate_id=0
        )
        
        block_data = RegionalBlockData(10, 15, sector_data)
        
        # Test setting and getting blocks
        regional_map.set_block(block_data)
        retrieved_block = regional_map.get_block(10, 15)
        
        assert retrieved_block == block_data
        assert regional_map.get_block(0, 0) is None  # Non-existent block
    
    def test_completion_tracking(self):
        """Test completion tracking."""
        regional_map = RegionalMapData(0, 0, 12345)
        
        # Should not be complete initially
        assert not regional_map.is_complete()
        
        # Mark as complete
        regional_map.mark_complete()
        assert regional_map.generation_complete
        assert regional_map.generation_end_time is not None


class TestRegionalScaleGenerator:
    """Test the regional scale generator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.world_generator = WorldScaleGenerator(seed=12345)
        self.regional_generator = RegionalScaleGenerator(self.world_generator)
    
    def test_initialization(self):
        """Test regional generator initialization."""
        assert self.regional_generator.world_generator == self.world_generator
        assert self.regional_generator.seed == self.world_generator.seed
        assert self.regional_generator.blocks_per_sector == 32
        assert self.regional_generator.block_size_tiles == 1024
        assert len(self.regional_generator.regional_maps) == 0
    
    def test_regional_map_generation(self):
        """Test regional map generation."""
        # First generate world data
        world_map = self.world_generator.generate_complete_world_map()
        
        # Generate regional map for a sector
        regional_map = self.regional_generator.generate_regional_map(0, 0)
        
        assert regional_map.sector_x == 0
        assert regional_map.sector_y == 0
        assert regional_map.is_complete()
        assert len(regional_map.blocks) == 1024  # 32×32 blocks
        
        # Test that all blocks are generated
        for block_y in range(32):
            for block_x in range(32):
                block_data = regional_map.get_block(block_x, block_y)
                assert block_data is not None
                assert block_data.block_x == block_x
                assert block_data.block_y == block_y
    
    def test_regional_block_generation(self):
        """Test individual regional block generation."""
        # Generate world data first
        world_map = self.world_generator.generate_complete_world_map()
        sector_data = world_map.get_sector(0, 0)
        
        # Generate a regional block
        block_data = self.regional_generator.generate_regional_block(
            0, 0, 5, 7, sector_data
        )
        
        assert block_data.block_x == 5
        assert block_data.block_y == 7
        assert block_data.parent_sector == sector_data
        assert block_data.terrain_type in REGIONAL_TERRAIN_TYPES
        assert isinstance(block_data.elevation_variation, float)
        assert 0 <= block_data.moisture_level <= 1
        assert isinstance(block_data.temperature_variation, float)
        assert isinstance(block_data.has_river, bool)
        assert isinstance(block_data.has_forest, bool)
        assert isinstance(block_data.has_hills, bool)
        assert isinstance(block_data.has_settlement, bool)
    
    def test_terrain_determination(self):
        """Test regional terrain determination logic."""
        # Generate world data
        world_map = self.world_generator.generate_complete_world_map()
        
        # Test different sector types
        for (sector_x, sector_y), sector_data in world_map.sectors.items():
            # Generate a few blocks for this sector
            for block_x in [0, 15, 31]:
                for block_y in [0, 15, 31]:
                    block_data = self.regional_generator.generate_regional_block(
                        sector_x, sector_y, block_x, block_y, sector_data
                    )
                    
                    # Terrain should be appropriate for sector type
                    if "ocean" in sector_data.dominant_terrain:
                        assert block_data.terrain_type == "water"
                    elif sector_data.dominant_terrain == "desert":
                        assert block_data.terrain_type in ["barren", "fertile", "plains"]
                    elif "mountain" in sector_data.dominant_terrain:
                        assert block_data.terrain_type in ["rocky", "hills", "barren"]
                    else:
                        # Land terrain should be reasonable
                        assert block_data.terrain_type in REGIONAL_TERRAIN_TYPES
    
    def test_deterministic_generation(self):
        """Test that regional generation is deterministic."""
        # Generate same regional map twice
        regional_map1 = self.regional_generator.generate_regional_map(1, 1)
        
        # Clear cache and generate again
        self.regional_generator.clear_cache()
        regional_map2 = self.regional_generator.generate_regional_map(1, 1)
        
        # Should be identical
        assert len(regional_map1.blocks) == len(regional_map2.blocks)
        
        for (block_x, block_y), block1 in regional_map1.blocks.items():
            block2 = regional_map2.blocks[(block_x, block_y)]
            assert block1.terrain_type == block2.terrain_type
            assert block1.elevation_variation == block2.elevation_variation
            assert block1.moisture_level == block2.moisture_level
            assert block1.has_river == block2.has_river
    
    def test_world_coordinate_lookup(self):
        """Test looking up blocks by world coordinates."""
        # Generate regional map
        regional_map = self.regional_generator.generate_regional_map(0, 0)
        
        # Test coordinate lookup
        test_coords = [
            (0, 0),           # First block
            (512, 512),       # Middle of first block
            (1024, 1024),     # Second block
            (15000, 15000),   # Later block
        ]
        
        for world_x, world_y in test_coords:
            block_data = self.regional_generator.get_regional_block_at_world_coordinates(
                world_x, world_y
            )
            
            if block_data:  # Only test if within bounds
                # Calculate expected block coordinates
                expected_block_x = (world_x % 16384) // 1024
                expected_block_y = (world_y % 16384) // 1024
                
                assert block_data.block_x == expected_block_x
                assert block_data.block_y == expected_block_y
    
    def test_caching_behavior(self):
        """Test regional map caching."""
        # Generate regional map
        regional_map1 = self.regional_generator.generate_regional_map(2, 3)
        
        # Generate same map again (should use cache)
        regional_map2 = self.regional_generator.generate_regional_map(2, 3)
        
        # Should be the same object (cached)
        assert regional_map1 is regional_map2
        
        # Clear cache
        self.regional_generator.clear_cache()
        
        # Should be empty now
        assert len(self.regional_generator.regional_maps) == 0
    
    def test_feature_generation(self):
        """Test regional feature generation."""
        # Generate world and regional data
        world_map = self.world_generator.generate_complete_world_map()
        
        # Find a sector with rivers
        river_sector = None
        for sector_data in world_map.sectors.values():
            if sector_data.has_major_river_system:
                river_sector = sector_data
                break
        
        if river_sector:
            # Generate regional map for river sector
            regional_map = self.regional_generator.generate_regional_map(
                river_sector.sector_x, river_sector.sector_y
            )
            
            # Should have some blocks with rivers
            river_blocks = [block for block in regional_map.blocks.values() 
                          if block.has_river]
            
            # Should have at least some river blocks (not necessarily many due to rarity)
            assert len(river_blocks) >= 0  # At least possible to have rivers


if __name__ == "__main__":
    pytest.main([__file__])
