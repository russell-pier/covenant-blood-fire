"""
Tests for world scale generation system.

This module tests the world-scale generator and related data structures
to ensure deterministic and correct world generation.
"""

import pytest
import time
from src.covenant.world.generators.world_scale import WorldScaleGenerator
from src.covenant.world.generators.base_generator import HierarchicalNoiseGenerator
from src.covenant.world.data.world_data import WorldSectorData, WorldMapData
from src.covenant.world.data.scale_types import ViewScale, get_scale_config


class TestHierarchicalNoiseGenerator:
    """Test the base noise generation system."""
    
    def test_noise_deterministic(self):
        """Test that noise generation is deterministic."""
        generator1 = HierarchicalNoiseGenerator(seed=12345)
        generator2 = HierarchicalNoiseGenerator(seed=12345)
        
        # Same seed should produce same results
        for x in [0, 100, 1000]:
            for y in [0, 100, 1000]:
                assert generator1.continental_noise(x, y) == generator2.continental_noise(x, y)
                assert generator1.tectonic_noise(x, y) == generator2.tectonic_noise(x, y)
                assert generator1.climate_noise(x, y) == generator2.climate_noise(x, y)
    
    def test_noise_different_seeds(self):
        """Test that different seeds produce different results."""
        generator1 = HierarchicalNoiseGenerator(seed=12345)
        generator2 = HierarchicalNoiseGenerator(seed=54321)
        
        # Different seeds should produce different results
        different_results = False
        for x in [0, 100, 1000]:
            for y in [0, 100, 1000]:
                if generator1.continental_noise(x, y) != generator2.continental_noise(x, y):
                    different_results = True
                    break
            if different_results:
                break
        
        assert different_results, "Different seeds should produce different noise"
    
    def test_noise_range(self):
        """Test that noise values are within expected range."""
        generator = HierarchicalNoiseGenerator(seed=12345)
        
        for x in range(0, 1000, 100):
            for y in range(0, 1000, 100):
                continental = generator.continental_noise(x, y)
                tectonic = generator.tectonic_noise(x, y)
                climate = generator.climate_noise(x, y)
                
                assert -1.0 <= continental <= 1.0
                assert -1.0 <= tectonic <= 1.0
                assert -1.0 <= climate <= 1.0
    
    def test_octave_noise(self):
        """Test multi-octave noise generation."""
        generator = HierarchicalNoiseGenerator(seed=12345)
        
        # Test different octave counts
        for octaves in [1, 2, 3, 5]:
            noise_val = generator.octave_noise(100, 100, octaves=octaves)
            assert isinstance(noise_val, float)
            # Octave noise should generally stay within reasonable bounds
            assert -2.0 <= noise_val <= 2.0


class TestWorldScaleGenerator:
    """Test the world scale generator."""
    
    def test_world_generation_deterministic(self):
        """Test that world generation is deterministic."""
        generator1 = WorldScaleGenerator(seed=12345)
        generator2 = WorldScaleGenerator(seed=12345)
        
        world_map1 = generator1.generate_complete_world_map()
        world_map2 = generator2.generate_complete_world_map()
        
        assert world_map1.world_seed == world_map2.world_seed
        assert world_map1.world_size_sectors == world_map2.world_size_sectors
        assert len(world_map1.sectors) == len(world_map2.sectors)
        
        # Check that all sectors are identical
        for coord, sector1 in world_map1.sectors.items():
            sector2 = world_map2.sectors[coord]
            assert sector1.sector_x == sector2.sector_x
            assert sector1.sector_y == sector2.sector_y
            assert sector1.dominant_terrain == sector2.dominant_terrain
            assert sector1.average_elevation == sector2.average_elevation
            assert sector1.climate_zone == sector2.climate_zone
    
    def test_world_generation_complete(self):
        """Test that world generation creates all expected sectors."""
        generator = WorldScaleGenerator(seed=12345)
        world_map = generator.generate_complete_world_map()
        
        assert world_map.world_size_sectors == (8, 6)
        assert len(world_map.sectors) == 48  # 8×6
        assert world_map.generation_complete
        assert world_map.is_complete()
        
        # Check that all sectors are within bounds
        for (sector_x, sector_y) in world_map.sectors.keys():
            assert 0 <= sector_x < 8
            assert 0 <= sector_y < 6
    
    def test_sector_generation(self):
        """Test individual sector generation."""
        generator = WorldScaleGenerator(seed=12345)
        
        # Generate a few test sectors
        for sector_x in [0, 3, 7]:
            for sector_y in [0, 2, 5]:
                sector = generator.generate_world_sector(sector_x, sector_y)
                
                assert sector.sector_x == sector_x
                assert sector.sector_y == sector_y
                assert isinstance(sector.dominant_terrain, str)
                assert isinstance(sector.average_elevation, float)
                assert sector.climate_zone in ["tropical", "temperate", "polar"]
                assert isinstance(sector.display_char, str)
                assert len(sector.display_color) == 3
                assert len(sector.display_bg_color) == 3
                assert isinstance(sector.has_major_mountain_range, bool)
                assert isinstance(sector.has_major_river_system, bool)
                assert isinstance(sector.continental_plate_id, int)
    
    def test_world_coordinates_lookup(self):
        """Test looking up sectors by world coordinates."""
        generator = WorldScaleGenerator(seed=12345)
        world_map = generator.generate_complete_world_map()
        
        # Test various world coordinates
        test_coords = [
            (0, 0),           # First sector
            (8192, 8192),     # Middle of first sector
            (16384, 16384),   # Second sector
            (100000, 100000), # Later sector
        ]
        
        for world_x, world_y in test_coords:
            sector = generator.get_sector_at_world_coordinates(world_x, world_y)
            if sector:  # Only test if within world bounds
                expected_sector_x = world_x // 16384
                expected_sector_y = world_y // 16384
                assert sector.sector_x == expected_sector_x
                assert sector.sector_y == expected_sector_y
    
    def test_world_info(self):
        """Test world information gathering."""
        generator = WorldScaleGenerator(seed=12345)
        
        # Before generation
        info = generator.get_world_info()
        assert info["status"] == "not_generated"
        
        # After generation
        world_map = generator.generate_complete_world_map()
        info = generator.get_world_info()
        
        assert info["status"] == "complete"
        assert info["seed"] == 12345
        assert info["world_size"] == (16, 16)
        assert info["total_sectors"] == 256
        assert isinstance(info["average_elevation"], float)
        assert isinstance(info["terrain_distribution"], dict)
        assert isinstance(info["climate_distribution"], dict)
        assert isinstance(info["major_mountain_ranges"], int)
        assert isinstance(info["major_river_systems"], int)
        assert isinstance(info["generation_time"], float)
    
    def test_cache_clearing(self):
        """Test cache clearing functionality."""
        generator = WorldScaleGenerator(seed=12345)
        world_map = generator.generate_complete_world_map()
        
        assert generator.world_map_data is not None
        
        generator.clear_cache()
        assert generator.world_map_data is None


class TestScaleTypes:
    """Test scale type definitions and utilities."""
    
    def test_scale_configs(self):
        """Test scale configuration retrieval."""
        world_config = get_scale_config(ViewScale.WORLD)
        regional_config = get_scale_config(ViewScale.REGIONAL)
        local_config = get_scale_config(ViewScale.LOCAL)
        
        assert world_config.name == "World"
        assert world_config.pixels_per_unit == 16384
        assert world_config.map_size == (16, 16)
        
        assert regional_config.name == "Regional"
        assert regional_config.pixels_per_unit == 1024
        assert regional_config.map_size == (32, 32)
        
        assert local_config.name == "Local"
        assert local_config.pixels_per_unit == 32
        assert local_config.map_size == (32, 32)
    
    def test_coordinate_conversion(self):
        """Test coordinate conversion utilities."""
        from src.covenant.world.data.scale_types import (
            get_world_coordinates_for_scale,
            get_scale_coordinates_from_world
        )
        
        # Test world scale
        world_x, world_y = get_world_coordinates_for_scale(ViewScale.WORLD, 1, 1)
        assert world_x == 16384
        assert world_y == 16384
        
        scale_x, scale_y = get_scale_coordinates_from_world(ViewScale.WORLD, 16384, 16384)
        assert scale_x == 1
        assert scale_y == 1
        
        # Test regional scale
        world_x, world_y = get_world_coordinates_for_scale(ViewScale.REGIONAL, 2, 3)
        assert world_x == 2048
        assert world_y == 3072
        
        scale_x, scale_y = get_scale_coordinates_from_world(ViewScale.REGIONAL, 2048, 3072)
        assert scale_x == 2
        assert scale_y == 3


if __name__ == "__main__":
    pytest.main([__file__])
