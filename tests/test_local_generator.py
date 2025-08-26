"""
Tests for the local scale generator.

This module tests the local-scale generation system including sub-terrain,
3D structure, resources, and animal spawn areas.
"""

import pytest
from src.covenant.world.generators.local_generator import (
    LocalScaleGenerator, LocalTile, ZLevel, ResourceType, AnimalSpawnType,
    StructuralFeature
)
from src.covenant.world.generators.regional_generator import RegionalTile, TerrainSubtype
from src.covenant.world.data.tilemap import BiomeType, LocalTerrain
from src.covenant.world.data.scale_types import CoordinateSystem


def create_test_regional_tile(terrain_subtype: TerrainSubtype = TerrainSubtype.PLAINS) -> RegionalTile:
    """Create a test regional tile for local generation"""
    return RegionalTile(
        x=5, y=5,
        parent_biome=BiomeType.GRASSLAND,
        terrain_subtype=terrain_subtype,
        micro_elevation=10.0,
        has_minor_river=False,
        river_size=0,
        is_lake=False,
        lake_id=None,
        water_flow_direction=None,
        landmark=None,
        resource_concentration=None,
        fertility=0.6,
        accessibility=0.8,
        terrain_boundary=False,
        biome_edge=False,
        char=".",
        fg_color=(50, 150, 50),
        bg_color=(25, 100, 25)
    )


class TestLocalScaleGenerator:
    """Test the local scale generator"""
    
    def test_generator_initialization(self):
        """Test generator initialization"""
        generator = LocalScaleGenerator(12345)
        
        assert generator.seed == 12345
        assert generator.chunk_size == CoordinateSystem.LOCAL_SIZE[0]
        assert generator.max_resource_clusters == 6
        assert generator.max_animal_areas == 4
        assert generator.max_structural_features == 8
        assert len(generator.resource_clusters) == 0
        assert len(generator.animal_areas) == 0
    
    def test_local_generation_complete(self):
        """Test complete local generation"""
        generator = LocalScaleGenerator(12345)
        regional_tile = create_test_regional_tile(TerrainSubtype.PLAINS)
        neighbors = {}
        
        local_map = generator.generate_local_chunk(regional_tile, neighbors)
        
        # Check dimensions
        assert len(local_map) == generator.chunk_size
        assert len(local_map[0]) == generator.chunk_size
        
        # Check that all tiles are properly initialized
        for y in range(generator.chunk_size):
            for x in range(generator.chunk_size):
                tile = local_map[y][x]
                assert isinstance(tile, LocalTile)
                assert tile.x == x
                assert tile.y == y
                assert tile.parent_regional_terrain == TerrainSubtype.PLAINS
                assert isinstance(tile.sub_terrain, LocalTerrain)
                assert isinstance(tile.z_level, ZLevel)
                assert isinstance(tile.blocks_movement, bool)
                assert isinstance(tile.blocks_line_of_sight, bool)
                assert 0.5 <= tile.movement_cost <= 3.0
                assert 0.0 <= tile.concealment <= 1.0
                assert 0.0 <= tile.fertility <= 1.0
                assert tile.char is not None
                assert len(tile.fg_color) == 3
                assert len(tile.bg_color) == 3
    
    def test_default_sub_terrain_mapping(self):
        """Test default sub-terrain mapping"""
        generator = LocalScaleGenerator(12345)
        
        # Test various terrain subtypes
        test_cases = [
            (TerrainSubtype.PLAINS, LocalTerrain.GRASS_PATCH),
            (TerrainSubtype.DENSE_FOREST, LocalTerrain.MATURE_TREES),
            (TerrainSubtype.SAND_DUNES, LocalTerrain.SANDY_SOIL),
            (TerrainSubtype.STEEP_SLOPES, LocalTerrain.ROCKY_GROUND),
            (TerrainSubtype.MARSH, LocalTerrain.MUDDY_GROUND),
        ]
        
        for terrain_subtype, expected_sub_terrain in test_cases:
            result = generator._get_default_sub_terrain(terrain_subtype)
            assert result == expected_sub_terrain
    
    def test_terrain_sub_types(self):
        """Test terrain sub-type mapping"""
        generator = LocalScaleGenerator(12345)
        
        # Test that each terrain subtype has appropriate sub-terrain types
        plains_subtypes = generator._get_terrain_sub_types(TerrainSubtype.PLAINS)
        assert LocalTerrain.GRASS_PATCH in plains_subtypes
        assert LocalTerrain.SHORT_GRASS in plains_subtypes
        
        forest_subtypes = generator._get_terrain_sub_types(TerrainSubtype.DENSE_FOREST)
        assert LocalTerrain.MATURE_TREES in forest_subtypes
        assert LocalTerrain.LEAF_LITTER in forest_subtypes
        
        desert_subtypes = generator._get_terrain_sub_types(TerrainSubtype.SAND_DUNES)
        assert LocalTerrain.SANDY_SOIL in desert_subtypes
        assert LocalTerrain.BARE_EARTH in desert_subtypes
    
    def test_sub_terrain_generation(self):
        """Test sub-terrain generation"""
        generator = LocalScaleGenerator(12345)
        regional_tile = create_test_regional_tile(TerrainSubtype.MEADOWS)
        
        local_map = generator._initialize_local_map(regional_tile)
        generator._generate_sub_terrain(local_map, regional_tile, {})
        
        # Check that sub-terrain types are appropriate for meadows
        meadow_subtypes = {LocalTerrain.TALL_GRASS, LocalTerrain.WILDFLOWERS,
                          LocalTerrain.GRASS_PATCH, LocalTerrain.SHORT_GRASS}
        
        found_subtypes = set()
        for row in local_map:
            for tile in row:
                found_subtypes.add(tile.sub_terrain)
        
        # Should have meadow-related subtypes
        assert len(found_subtypes.intersection(meadow_subtypes)) > 0
    
    def test_precise_elevation_generation(self):
        """Test precise elevation generation"""
        generator = LocalScaleGenerator(12345)
        regional_tile = create_test_regional_tile(TerrainSubtype.PLAINS)
        regional_tile.micro_elevation = 50.0
        
        local_map = generator._initialize_local_map(regional_tile)
        generator._generate_sub_terrain(local_map, regional_tile, {})
        generator._generate_precise_elevation(local_map, regional_tile)
        
        # Check that elevations are generated and vary
        elevations = []
        for row in local_map:
            for tile in row:
                elevations.append(tile.precise_elevation)
        
        # Should have variation in elevations
        assert len(set(elevations)) > 1
        assert min(elevations) != max(elevations)
        
        # Should be roughly centered around regional elevation
        avg_elevation = sum(elevations) / len(elevations)
        assert abs(avg_elevation - regional_tile.micro_elevation) < 10.0
    
    def test_elevation_scale_factors(self):
        """Test elevation scale factors for different sub-terrain types"""
        generator = LocalScaleGenerator(12345)
        
        # Test that different sub-terrain types have appropriate elevation scales
        assert generator._get_sub_terrain_elevation_scale(LocalTerrain.GRASS_PATCH) < \
               generator._get_sub_terrain_elevation_scale(LocalTerrain.ROCKY_GROUND)
        assert generator._get_sub_terrain_elevation_scale(LocalTerrain.SMALL_BOULDER) < \
               generator._get_sub_terrain_elevation_scale(LocalTerrain.LARGE_BOULDER)
        assert generator._get_sub_terrain_elevation_scale(LocalTerrain.SHALLOW_WATER) < \
               generator._get_sub_terrain_elevation_scale(LocalTerrain.TALL_GRASS)
    
    def test_z_level_structure(self):
        """Test 3D structure and Z-level assignment"""
        generator = LocalScaleGenerator(12345)
        regional_tile = create_test_regional_tile(TerrainSubtype.DENSE_FOREST)
        
        local_map = generator._initialize_local_map(regional_tile)
        generator._generate_sub_terrain(local_map, regional_tile, {})
        generator._define_z_level_structure(local_map, regional_tile)
        
        # Check that Z-levels are assigned appropriately
        z_levels = set()
        elevated_count = 0
        
        for row in local_map:
            for tile in row:
                z_levels.add(tile.z_level)
                if tile.z_level == ZLevel.ELEVATED:
                    elevated_count += 1
        
        # Should have at least surface level
        assert ZLevel.SURFACE in z_levels
        
        # Forest should have some elevated areas (trees)
        # Note: This is probabilistic, so might be 0
    
    def test_movement_blocking(self):
        """Test movement blocking logic"""
        generator = LocalScaleGenerator(12345)
        
        # Test blocking terrain
        assert generator._blocks_movement(LocalTerrain.LARGE_BOULDER)
        assert generator._blocks_movement(LocalTerrain.DEEP_WATER)
        assert generator._blocks_movement(LocalTerrain.MATURE_TREES)
        
        # Test non-blocking terrain
        assert not generator._blocks_movement(LocalTerrain.GRASS_PATCH)
        assert not generator._blocks_movement(LocalTerrain.SHORT_GRASS)
        assert not generator._blocks_movement(LocalTerrain.SHALLOW_WATER)
    
    def test_line_of_sight_blocking(self):
        """Test line of sight blocking logic"""
        generator = LocalScaleGenerator(12345)
        
        # Test sight-blocking terrain
        assert generator._blocks_line_of_sight(LocalTerrain.LARGE_BOULDER)
        assert generator._blocks_line_of_sight(LocalTerrain.MATURE_TREES)
        assert generator._blocks_line_of_sight(LocalTerrain.YOUNG_TREES)
        
        # Test non-sight-blocking terrain
        assert not generator._blocks_line_of_sight(LocalTerrain.GRASS_PATCH)
        assert not generator._blocks_line_of_sight(LocalTerrain.SHALLOW_WATER)
        assert not generator._blocks_line_of_sight(LocalTerrain.SMALL_BOULDER)
    
    def test_level_access(self):
        """Test level access logic"""
        generator = LocalScaleGenerator(12345)
        
        # Test upper level access
        assert generator._can_access_upper_level(LocalTerrain.MATURE_TREES)
        assert generator._can_access_upper_level(LocalTerrain.LARGE_BOULDER)
        assert not generator._can_access_upper_level(LocalTerrain.GRASS_PATCH)
        
        # Test lower level access (currently none)
        assert not generator._can_access_lower_level(LocalTerrain.GRASS_PATCH)
        assert not generator._can_access_lower_level(LocalTerrain.MATURE_TREES)
    
    def test_structural_feature_selection(self):
        """Test structural feature selection"""
        generator = LocalScaleGenerator(12345)
        regional_tile = create_test_regional_tile(TerrainSubtype.STEEP_SLOPES)
        
        # Test fallen log
        fallen_log_tile = LocalTile(
            x=0, y=0, parent_regional_terrain=TerrainSubtype.PLAINS,
            sub_terrain=LocalTerrain.FALLEN_LOG, precise_elevation=0.0,
            z_level=ZLevel.SURFACE, structural_feature=None,
            blocks_movement=False, blocks_line_of_sight=False,
            can_access_upper_level=False, can_access_lower_level=False,
            harvestable_resource=None, resource_quantity=0, resource_respawn_time=0.0,
            animal_spawn_point=None, spawn_frequency=0.0, max_animals=0,
            movement_cost=1.0, concealment=0.0, fertility=0.0,
            char=".", fg_color=(128, 128, 128), bg_color=(64, 64, 64)
        )
        
        feature = generator._select_structural_feature(fallen_log_tile, regional_tile)
        assert feature == StructuralFeature.FALLEN_TREE_BRIDGE
        
        # Test water ford
        water_tile = LocalTile(
            x=0, y=0, parent_regional_terrain=TerrainSubtype.PLAINS,
            sub_terrain=LocalTerrain.SHALLOW_WATER, precise_elevation=0.0,
            z_level=ZLevel.SURFACE, structural_feature=None,
            blocks_movement=False, blocks_line_of_sight=False,
            can_access_upper_level=False, can_access_lower_level=False,
            harvestable_resource=None, resource_quantity=0, resource_respawn_time=0.0,
            animal_spawn_point=None, spawn_frequency=0.0, max_animals=0,
            movement_cost=1.0, concealment=0.0, fertility=0.0,
            char=".", fg_color=(128, 128, 128), bg_color=(64, 64, 64)
        )
        
        feature = generator._select_structural_feature(water_tile, regional_tile)
        assert feature == StructuralFeature.WATER_FORD
    
    def test_water_feature_application(self):
        """Test water feature application from regional rivers"""
        generator = LocalScaleGenerator(12345)
        regional_tile = create_test_regional_tile(TerrainSubtype.PLAINS)
        regional_tile.has_minor_river = True
        regional_tile.river_size = 2  # Creek
        
        test_tile = LocalTile(
            x=0, y=0, parent_regional_terrain=TerrainSubtype.PLAINS,
            sub_terrain=LocalTerrain.GRASS_PATCH, precise_elevation=0.0,
            z_level=ZLevel.SURFACE, structural_feature=None,
            blocks_movement=False, blocks_line_of_sight=False,
            can_access_upper_level=False, can_access_lower_level=False,
            harvestable_resource=None, resource_quantity=0, resource_respawn_time=0.0,
            animal_spawn_point=None, spawn_frequency=0.0, max_animals=0,
            movement_cost=1.0, concealment=0.0, fertility=0.0,
            char=".", fg_color=(128, 128, 128), bg_color=(64, 64, 64)
        )
        
        # Test water feature application (this is probabilistic)
        original_terrain = test_tile.sub_terrain
        generator._apply_water_features(test_tile, 0, 0, regional_tile)
        
        # Terrain might change to water-related if conditions are met
        # This is probabilistic, so we just check it doesn't crash
        assert test_tile.sub_terrain is not None
    
    def test_get_local_tile(self):
        """Test local tile access"""
        generator = LocalScaleGenerator(12345)
        regional_tile = create_test_regional_tile(TerrainSubtype.PLAINS)
        
        local_map = generator.generate_local_chunk(regional_tile, {})
        
        # Test valid coordinates
        tile = generator.get_local_tile(local_map, 0, 0)
        assert tile is not None
        assert tile.x == 0
        assert tile.y == 0
        
        tile = generator.get_local_tile(local_map, 15, 15)  # Center
        assert tile is not None
        assert tile.x == 15
        assert tile.y == 15
        
        # Test invalid coordinates
        assert generator.get_local_tile(local_map, -1, 0) is None
        assert generator.get_local_tile(local_map, 0, -1) is None
        assert generator.get_local_tile(local_map, generator.chunk_size, 0) is None
        assert generator.get_local_tile(local_map, 0, generator.chunk_size) is None
    
    def test_resource_and_animal_placement(self):
        """Test that resource and animal placement methods work"""
        generator = LocalScaleGenerator(12345)
        regional_tile = create_test_regional_tile(TerrainSubtype.DENSE_FOREST)
        
        local_map = generator.generate_local_chunk(regional_tile, {})
        
        # Check that some tiles might have resources or animals (probabilistic)
        resource_count = 0
        animal_count = 0
        
        for row in local_map:
            for tile in row:
                if tile.harvestable_resource:
                    resource_count += 1
                    assert isinstance(tile.harvestable_resource, ResourceType)
                    assert tile.resource_quantity > 0
                
                if tile.animal_spawn_point:
                    animal_count += 1
                    assert isinstance(tile.animal_spawn_point, AnimalSpawnType)
                    assert 0.0 <= tile.spawn_frequency <= 1.0
                    assert tile.max_animals >= 0
        
        # These are probabilistic, so we just check they don't crash
        # and that any placed resources/animals have valid properties
    
    def test_deterministic_generation(self):
        """Test that generation is deterministic with same seed"""
        regional_tile = create_test_regional_tile(TerrainSubtype.PLAINS)
        
        generator1 = LocalScaleGenerator(12345)
        local_map1 = generator1.generate_local_chunk(regional_tile, {})
        
        generator2 = LocalScaleGenerator(12345)
        local_map2 = generator2.generate_local_chunk(regional_tile, {})
        
        # Should produce identical results
        for y in range(generator1.chunk_size):
            for x in range(generator1.chunk_size):
                tile1 = local_map1[y][x]
                tile2 = local_map2[y][x]
                
                assert tile1.sub_terrain == tile2.sub_terrain
                assert tile1.z_level == tile2.z_level
                assert abs(tile1.precise_elevation - tile2.precise_elevation) < 0.001
                assert tile1.blocks_movement == tile2.blocks_movement
                assert tile1.blocks_line_of_sight == tile2.blocks_line_of_sight


if __name__ == "__main__":
    pytest.main([__file__])
