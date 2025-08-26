"""
Tests for the world scale generator.

This module tests the world-scale generation system including plate tectonics,
elevation, climate, and biome assignment.
"""

import pytest
from src.covenant.world.generators.world_generator import (
    WorldScaleGenerator, WorldTile, TectonicPlate, PlateType, ClimateZone,
    HierarchicalNoise
)
from src.covenant.world.data.tilemap import BiomeType
from src.covenant.world.data.scale_types import CoordinateSystem


class TestHierarchicalNoise:
    """Test the noise generation system"""
    
    def test_noise_initialization(self):
        """Test noise generator initialization"""
        noise = HierarchicalNoise(12345)
        assert noise.seed == 12345
        assert len(noise.perm) == 512  # Doubled permutation table
    
    def test_noise2d_consistency(self):
        """Test that noise2d produces consistent results"""
        noise = HierarchicalNoise(12345)
        
        # Same input should produce same output
        result1 = noise.noise2d(1.0, 2.0)
        result2 = noise.noise2d(1.0, 2.0)
        assert result1 == result2
        
        # Different inputs should produce different outputs (with high probability)
        result3 = noise.noise2d(1.1, 2.0)
        assert result1 != result3
    
    def test_octave_noise_range(self):
        """Test that octave noise produces values in expected range"""
        noise = HierarchicalNoise(12345)
        
        # Test multiple points
        for x in range(0, 10):
            for y in range(0, 10):
                value = noise.octave_noise(x * 0.1, y * 0.1)
                assert -1.0 <= value <= 1.0  # Should be normalized
    
    def test_ridge_noise(self):
        """Test ridge noise generation"""
        noise = HierarchicalNoise(12345)
        
        value = noise.ridge_noise(1.0, 2.0)
        assert 0.0 <= value <= 1.0  # Ridge noise should be positive


class TestWorldScaleGenerator:
    """Test the world scale generator"""
    
    def test_generator_initialization(self):
        """Test generator initialization"""
        generator = WorldScaleGenerator(12345)
        
        assert generator.seed == 12345
        assert generator.world_width == CoordinateSystem.WORLD_SIZE[0]
        assert generator.world_height == CoordinateSystem.WORLD_SIZE[1]
        assert generator.num_plates == 12
        assert generator.num_major_rivers == 15
        assert len(generator.plates) == 0  # Not generated yet
        assert len(generator.world_tiles) == 0  # Not generated yet
    
    def test_world_generation_complete(self):
        """Test complete world generation"""
        generator = WorldScaleGenerator(12345)
        world_tiles = generator.generate_complete_world()
        
        # Check dimensions
        assert len(world_tiles) == generator.world_height
        assert len(world_tiles[0]) == generator.world_width
        
        # Check that all tiles are properly initialized
        for y in range(generator.world_height):
            for x in range(generator.world_width):
                tile = world_tiles[y][x]
                assert isinstance(tile, WorldTile)
                assert tile.x == x
                assert tile.y == y
                assert isinstance(tile.biome, BiomeType)
                assert isinstance(tile.climate_zone, ClimateZone)
                assert 0.0 <= tile.temperature <= 1.0
                assert 0.0 <= tile.precipitation <= 1.0
                assert tile.char is not None
                assert len(tile.fg_color) == 3
                assert len(tile.bg_color) == 3
    
    def test_tectonic_plates_generation(self):
        """Test tectonic plate generation"""
        generator = WorldScaleGenerator(12345)
        generator._generate_tectonic_plates()
        
        # Should have generated the expected number of plates
        assert len(generator.plates) == generator.num_plates
        
        # Check plate properties
        for plate in generator.plates:
            assert isinstance(plate, TectonicPlate)
            assert isinstance(plate.plate_type, PlateType)
            assert 0 <= plate.center_x < generator.world_width
            assert 0 <= plate.center_y < generator.world_height
            assert 0.0 <= plate.age <= 1.0
        
        # Check that world tiles are assigned to plates
        assert len(generator.world_tiles) == generator.world_height
        for row in generator.world_tiles:
            assert len(row) == generator.world_width
            for tile in row:
                assert 0 <= tile.plate_id < generator.num_plates
        
        # Check that plate boundaries are identified
        assert len(generator.plate_boundaries) > 0
    
    def test_elevation_calculation(self):
        """Test elevation calculation"""
        generator = WorldScaleGenerator(12345)
        generator._generate_tectonic_plates()
        generator._calculate_base_elevation()
        
        # Check that elevations are calculated
        for row in generator.world_tiles:
            for tile in row:
                assert tile.base_elevation is not None
                assert tile.final_elevation is not None
                assert tile.base_elevation == tile.final_elevation  # Before mountain building
    
    def test_mountain_building(self):
        """Test mountain building process"""
        generator = WorldScaleGenerator(12345)
        generator._generate_tectonic_plates()
        generator._calculate_base_elevation()
        
        # Store original elevations
        original_elevations = {}
        for y in range(generator.world_height):
            for x in range(generator.world_width):
                original_elevations[(x, y)] = generator.world_tiles[y][x].final_elevation
        
        generator._apply_mountain_building()
        
        # Check that some elevations have increased (mountains built)
        elevation_increases = 0
        for y in range(generator.world_height):
            for x in range(generator.world_width):
                new_elevation = generator.world_tiles[y][x].final_elevation
                if new_elevation > original_elevations[(x, y)]:
                    elevation_increases += 1
        
        assert elevation_increases > 0  # Some mountains should have been built
    
    def test_land_sea_determination(self):
        """Test land/sea boundary determination"""
        generator = WorldScaleGenerator(12345)
        generator._generate_tectonic_plates()
        generator._calculate_base_elevation()
        generator._apply_mountain_building()
        generator._determine_land_sea()
        
        # Check that land/sea is determined
        land_count = 0
        sea_count = 0
        
        for row in generator.world_tiles:
            for tile in row:
                assert isinstance(tile.is_land, bool)
                if tile.is_land:
                    land_count += 1
                else:
                    sea_count += 1
        
        # Should have both land and sea
        assert land_count > 0
        assert sea_count > 0
    
    def test_climate_generation(self):
        """Test climate zone generation"""
        generator = WorldScaleGenerator(12345)
        generator._generate_tectonic_plates()
        generator._calculate_base_elevation()
        generator._apply_mountain_building()
        generator._determine_land_sea()
        generator._generate_climate_zones()
        
        # Check that climate data is generated
        climate_zones = set()
        for row in generator.world_tiles:
            for tile in row:
                assert isinstance(tile.climate_zone, ClimateZone)
                assert 0.0 <= tile.temperature <= 1.0
                assert 0.0 <= tile.precipitation <= 1.0
                assert 0.0 <= tile.seasonal_variation <= 1.0
                climate_zones.add(tile.climate_zone)
        
        # Should have multiple climate zones
        assert len(climate_zones) > 1
    
    def test_biome_assignment(self):
        """Test biome assignment"""
        generator = WorldScaleGenerator(12345)
        world_tiles = generator.generate_complete_world()
        
        # Check that biomes are assigned
        biomes = set()
        for row in world_tiles:
            for tile in row:
                assert isinstance(tile.biome, BiomeType)
                biomes.add(tile.biome)
        
        # Should have multiple biomes
        assert len(biomes) > 1
        
        # Should have both land and ocean biomes
        ocean_biomes = {BiomeType.DEEP_OCEAN, BiomeType.SHALLOW_SEA, BiomeType.COASTAL_WATERS}
        land_biomes = set(BiomeType) - ocean_biomes
        
        has_ocean = any(biome in ocean_biomes for biome in biomes)
        has_land = any(biome in land_biomes for biome in biomes)
        
        assert has_ocean
        assert has_land
    
    def test_display_generation(self):
        """Test display character generation"""
        generator = WorldScaleGenerator(12345)
        world_tiles = generator.generate_complete_world()
        
        # Check that display properties are set
        for row in world_tiles:
            for tile in row:
                assert tile.char is not None
                assert len(tile.char) > 0
                assert len(tile.fg_color) == 3
                assert len(tile.bg_color) == 3
                
                # Colors should be valid RGB values
                for color_component in tile.fg_color + tile.bg_color:
                    assert 0 <= color_component <= 255
    
    def test_get_world_tile(self):
        """Test world tile access"""
        generator = WorldScaleGenerator(12345)
        generator.generate_complete_world()
        
        # Test valid coordinates
        tile = generator.get_world_tile(0, 0)
        assert tile is not None
        assert tile.x == 0
        assert tile.y == 0
        
        tile = generator.get_world_tile(64, 48)  # Center
        assert tile is not None
        assert tile.x == 64
        assert tile.y == 48
        
        # Test invalid coordinates
        assert generator.get_world_tile(-1, 0) is None
        assert generator.get_world_tile(0, -1) is None
        assert generator.get_world_tile(generator.world_width, 0) is None
        assert generator.get_world_tile(0, generator.world_height) is None
    
    def test_get_neighboring_tiles(self):
        """Test neighboring tile access"""
        generator = WorldScaleGenerator(12345)
        generator.generate_complete_world()
        
        # Test center tile (should have all neighbors)
        neighbors = generator.get_neighboring_world_tiles(64, 48)
        expected_directions = {"north", "south", "east", "west", "northeast", "northwest", "southeast", "southwest"}
        assert set(neighbors.keys()) == expected_directions
        
        # Test corner tile (should have fewer neighbors)
        neighbors = generator.get_neighboring_world_tiles(0, 0)
        assert len(neighbors) < 8  # Corner has fewer neighbors
        
        # Test edge tile
        neighbors = generator.get_neighboring_world_tiles(0, 48)
        assert len(neighbors) < 8  # Edge has fewer neighbors
    
    def test_deterministic_generation(self):
        """Test that generation is deterministic with same seed"""
        generator1 = WorldScaleGenerator(12345)
        world1 = generator1.generate_complete_world()
        
        generator2 = WorldScaleGenerator(12345)
        world2 = generator2.generate_complete_world()
        
        # Should produce identical results
        for y in range(generator1.world_height):
            for x in range(generator1.world_width):
                tile1 = world1[y][x]
                tile2 = world2[y][x]
                
                assert tile1.biome == tile2.biome
                assert tile1.is_land == tile2.is_land
                assert tile1.climate_zone == tile2.climate_zone
                assert abs(tile1.temperature - tile2.temperature) < 0.001
                assert abs(tile1.precipitation - tile2.precipitation) < 0.001
    
    def test_different_seeds_produce_different_worlds(self):
        """Test that different seeds produce different worlds"""
        generator1 = WorldScaleGenerator(12345)
        world1 = generator1.generate_complete_world()
        
        generator2 = WorldScaleGenerator(54321)
        world2 = generator2.generate_complete_world()
        
        # Should produce different results
        differences = 0
        for y in range(generator1.world_height):
            for x in range(generator1.world_width):
                tile1 = world1[y][x]
                tile2 = world2[y][x]
                
                if (tile1.biome != tile2.biome or 
                    tile1.is_land != tile2.is_land or
                    abs(tile1.temperature - tile2.temperature) > 0.1):
                    differences += 1
        
        # Should have significant differences
        total_tiles = generator1.world_width * generator1.world_height
        assert differences > total_tiles * 0.1  # At least 10% different


if __name__ == "__main__":
    pytest.main([__file__])
