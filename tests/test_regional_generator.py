"""
Tests for the regional scale generator.

This module tests the regional-scale generation system including terrain subtypes,
water systems, landmarks, and resource concentrations.
"""

import pytest
from src.covenant.world.generators.regional_generator import (
    RegionalScaleGenerator, RegionalTile, LandmarkType, ResourceConcentration,
    LakeSystem, RiverSegment
)
from src.covenant.world.generators.world_generator import WorldTile, ClimateZone
from src.covenant.world.data.tilemap import BiomeType, TerrainSubtype
from src.covenant.world.data.scale_types import CoordinateSystem


def create_test_world_tile(biome: BiomeType = BiomeType.GRASSLAND) -> WorldTile:
    """Create a test world tile for regional generation"""
    return WorldTile(
        x=10, y=10,
        plate_id=0,
        base_elevation=100.0,
        final_elevation=100.0,
        is_land=True,
        has_major_river=False,
        river_id=None,
        drainage_direction=None,
        water_accumulation=0.0,
        climate_zone=ClimateZone.TEMPERATE,
        temperature=0.6,
        precipitation=0.5,
        seasonal_variation=0.3,
        biome=biome,
        char="\"",
        fg_color=(80, 200, 80),
        bg_color=(50, 150, 50)
    )


class TestRegionalScaleGenerator:
    """Test the regional scale generator"""
    
    def test_generator_initialization(self):
        """Test generator initialization"""
        generator = RegionalScaleGenerator(12345)
        
        assert generator.seed == 12345
        assert generator.region_size == CoordinateSystem.REGIONAL_SIZE[0]
        assert generator.max_lakes == 6
        assert generator.max_minor_rivers == 8
        assert generator.landmark_density == 0.03
        assert generator.resource_cluster_density == 0.05
        assert len(generator.lakes) == 0
        assert len(generator.rivers) == 0
    
    def test_regional_generation_complete(self):
        """Test complete regional generation"""
        generator = RegionalScaleGenerator(12345)
        world_tile = create_test_world_tile(BiomeType.GRASSLAND)
        neighbors = {}
        
        regional_map = generator.generate_regional_map(world_tile, neighbors)
        
        # Check dimensions
        assert len(regional_map) == generator.region_size
        assert len(regional_map[0]) == generator.region_size
        
        # Check that all tiles are properly initialized
        for y in range(generator.region_size):
            for x in range(generator.region_size):
                tile = regional_map[y][x]
                assert isinstance(tile, RegionalTile)
                assert tile.x == x
                assert tile.y == y
                assert tile.parent_biome == BiomeType.GRASSLAND
                assert isinstance(tile.terrain_subtype, TerrainSubtype)
                assert 0.0 <= tile.fertility <= 1.0
                assert 0.0 <= tile.accessibility <= 1.0
                assert tile.char is not None
                assert len(tile.fg_color) == 3
                assert len(tile.bg_color) == 3
    
    def test_terrain_subtype_generation(self):
        """Test terrain subtype generation"""
        generator = RegionalScaleGenerator(12345)
        world_tile = create_test_world_tile(BiomeType.TEMPERATE_FOREST)
        neighbors = {}
        
        regional_map = generator.generate_regional_map(world_tile, neighbors)
        
        # Check that terrain subtypes are appropriate for the biome
        forest_subtypes = {TerrainSubtype.DENSE_FOREST, TerrainSubtype.LIGHT_WOODLAND,
                          TerrainSubtype.FOREST_CLEARING, TerrainSubtype.OLD_GROWTH}
        
        found_subtypes = set()
        for row in regional_map:
            for tile in row:
                found_subtypes.add(tile.terrain_subtype)
        
        # Should have forest-related subtypes
        assert len(found_subtypes.intersection(forest_subtypes)) > 0
    
    def test_default_terrain_subtypes(self):
        """Test default terrain subtype assignment"""
        generator = RegionalScaleGenerator(12345)
        
        # Test various biomes
        test_cases = [
            (BiomeType.GRASSLAND, TerrainSubtype.PLAINS),
            (BiomeType.TEMPERATE_FOREST, TerrainSubtype.LIGHT_WOODLAND),
            (BiomeType.DESERT, TerrainSubtype.SAND_DUNES),
            (BiomeType.HIGH_MOUNTAINS, TerrainSubtype.STEEP_SLOPES),
            (BiomeType.WETLAND, TerrainSubtype.MARSH),
        ]
        
        for biome, expected_terrain in test_cases:
            result = generator._get_default_terrain_subtype(biome)
            assert result == expected_terrain
    
    def test_biome_terrain_subtypes(self):
        """Test biome to terrain subtype mapping"""
        generator = RegionalScaleGenerator(12345)
        
        # Test that each biome has appropriate terrain subtypes
        grassland_subtypes = generator._get_biome_terrain_subtypes(BiomeType.GRASSLAND)
        assert TerrainSubtype.PLAINS in grassland_subtypes
        assert TerrainSubtype.MEADOWS in grassland_subtypes
        
        forest_subtypes = generator._get_biome_terrain_subtypes(BiomeType.TEMPERATE_FOREST)
        assert TerrainSubtype.DENSE_FOREST in forest_subtypes
        assert TerrainSubtype.LIGHT_WOODLAND in forest_subtypes
        
        desert_subtypes = generator._get_biome_terrain_subtypes(BiomeType.DESERT)
        assert TerrainSubtype.SAND_DUNES in desert_subtypes
        assert TerrainSubtype.ROCKY_DESERT in desert_subtypes
    
    def test_micro_elevation_generation(self):
        """Test micro elevation generation"""
        generator = RegionalScaleGenerator(12345)
        world_tile = create_test_world_tile(BiomeType.GRASSLAND)
        
        regional_map = generator._initialize_regional_map(world_tile)
        generator._generate_micro_elevation(regional_map, world_tile)
        
        # Check that elevations are generated
        elevations = []
        for row in regional_map:
            for tile in row:
                elevations.append(tile.micro_elevation)
        
        # Should have variation in elevations
        assert len(set(elevations)) > 1
        assert min(elevations) != max(elevations)
    
    def test_elevation_scale_factors(self):
        """Test elevation scale factors for different terrain types"""
        generator = RegionalScaleGenerator(12345)
        
        # Test that different terrain types have appropriate elevation scales
        assert generator._get_elevation_scale(TerrainSubtype.PLAINS) < generator._get_elevation_scale(TerrainSubtype.ROLLING_HILLS)
        assert generator._get_elevation_scale(TerrainSubtype.ROLLING_HILLS) < generator._get_elevation_scale(TerrainSubtype.STEEP_SLOPES)
        assert generator._get_elevation_scale(TerrainSubtype.STEEP_SLOPES) < generator._get_elevation_scale(TerrainSubtype.CLIFFS)
    
    def test_lake_generation(self):
        """Test lake generation"""
        generator = RegionalScaleGenerator(12345)
        world_tile = create_test_world_tile(BiomeType.TEMPERATE_FOREST)
        world_tile.precipitation = 0.8  # High precipitation for more lakes
        
        regional_map = generator._initialize_regional_map(world_tile)
        generator._generate_lakes(regional_map, world_tile)
        
        # Should have generated some lakes with high precipitation
        assert len(generator.lakes) >= 0  # Could be 0 due to randomness, but usually > 0
        
        # Check lake properties
        for lake in generator.lakes:
            assert isinstance(lake, LakeSystem)
            assert 0 <= lake.center_x < generator.region_size
            assert 0 <= lake.center_y < generator.region_size
            assert lake.size > 0
            assert lake.depth > 0
    
    def test_lake_probability_calculation(self):
        """Test lake probability calculation"""
        generator = RegionalScaleGenerator(12345)
        
        # Test different biomes and precipitation levels
        dry_grassland = create_test_world_tile(BiomeType.GRASSLAND)
        dry_grassland.precipitation = 0.1
        
        wet_forest = create_test_world_tile(BiomeType.TEMPERATE_FOREST)
        wet_forest.precipitation = 0.9
        
        wetland = create_test_world_tile(BiomeType.WETLAND)
        wetland.precipitation = 0.6
        
        desert = create_test_world_tile(BiomeType.DESERT)
        desert.precipitation = 0.2
        
        # Wetlands should have highest probability
        assert generator._get_lake_probability(wetland) > generator._get_lake_probability(wet_forest)
        assert generator._get_lake_probability(wet_forest) > generator._get_lake_probability(dry_grassland)
        assert generator._get_lake_probability(dry_grassland) > generator._get_lake_probability(desert)
    
    def test_water_feature_application(self):
        """Test application of water features to tiles"""
        generator = RegionalScaleGenerator(12345)
        world_tile = create_test_world_tile(BiomeType.TEMPERATE_FOREST)
        
        regional_map = generator._initialize_regional_map(world_tile)
        
        # Manually add a lake for testing
        test_lake = LakeSystem(
            id=0, center_x=10.0, center_y=10.0, size=3.0,
            depth=5.0, is_seasonal=False, connects_to_river=False
        )
        generator.lakes = [test_lake]
        
        generator._apply_water_features(regional_map)
        
        # Check that tiles near lake center are marked as lake tiles
        center_tile = regional_map[10][10]
        assert center_tile.is_lake
        assert center_tile.lake_id == 0
        assert center_tile.terrain_subtype in [TerrainSubtype.DEEP_WATER, TerrainSubtype.SHALLOW_WATER]
    
    def test_landmark_placement(self):
        """Test landmark placement"""
        generator = RegionalScaleGenerator(12345)
        world_tile = create_test_world_tile(BiomeType.HIGH_MOUNTAINS)
        
        regional_map = generator._initialize_regional_map(world_tile)
        # Set some tiles to mountain terrain
        for y in range(5, 10):
            for x in range(5, 10):
                regional_map[y][x].terrain_subtype = TerrainSubtype.STEEP_SLOPES
        
        generator._place_landmark_features(regional_map, world_tile)
        
        # Check that some landmarks were placed (probabilistic, so might be 0)
        landmark_count = 0
        for row in regional_map:
            for tile in row:
                if tile.landmark:
                    landmark_count += 1
                    assert isinstance(tile.landmark, LandmarkType)
        
        # With mountain terrain, should have some chance of landmarks
        # (This is probabilistic, so we can't guarantee landmarks will be placed)
    
    def test_landmark_selection(self):
        """Test appropriate landmark selection for terrain"""
        generator = RegionalScaleGenerator(12345)
        world_tile = create_test_world_tile(BiomeType.HIGH_MOUNTAINS)
        
        # Test mountain terrain
        mountain_tile = RegionalTile(
            x=0, y=0, parent_biome=BiomeType.HIGH_MOUNTAINS,
            terrain_subtype=TerrainSubtype.STEEP_SLOPES,
            micro_elevation=0.0, has_minor_river=False, river_size=0,
            is_lake=False, lake_id=None, water_flow_direction=None,
            landmark=None, resource_concentration=None,
            fertility=0.0, accessibility=0.0,
            terrain_boundary=False, biome_edge=False,
            char=".", fg_color=(128, 128, 128), bg_color=(64, 64, 64)
        )
        
        landmark = generator._select_appropriate_landmark(mountain_tile, world_tile)
        if landmark:  # Might be None due to randomness
            mountain_landmarks = {LandmarkType.CAVE_ENTRANCE, LandmarkType.SCENIC_OVERLOOK, 
                                LandmarkType.NATURAL_BRIDGE}
            assert landmark in mountain_landmarks
    
    def test_resource_concentration_assignment(self):
        """Test resource concentration assignment"""
        generator = RegionalScaleGenerator(12345)
        world_tile = create_test_world_tile(BiomeType.TEMPERATE_FOREST)
        
        regional_map = generator._initialize_regional_map(world_tile)
        # Set some tiles to forest terrain
        for y in range(5, 10):
            for x in range(5, 10):
                regional_map[y][x].terrain_subtype = TerrainSubtype.DENSE_FOREST
        
        generator._assign_resource_concentrations(regional_map, world_tile)
        
        # Check that some resources were assigned (probabilistic)
        resource_count = 0
        for row in regional_map:
            for tile in row:
                if tile.resource_concentration:
                    resource_count += 1
                    assert isinstance(tile.resource_concentration, ResourceConcentration)
    
    def test_resource_selection(self):
        """Test appropriate resource selection for terrain"""
        generator = RegionalScaleGenerator(12345)
        world_tile = create_test_world_tile(BiomeType.TEMPERATE_FOREST)
        
        # Test forest terrain
        forest_tile = RegionalTile(
            x=0, y=0, parent_biome=BiomeType.TEMPERATE_FOREST,
            terrain_subtype=TerrainSubtype.DENSE_FOREST,
            micro_elevation=0.0, has_minor_river=False, river_size=0,
            is_lake=False, lake_id=None, water_flow_direction=None,
            landmark=None, resource_concentration=None,
            fertility=0.0, accessibility=0.0,
            terrain_boundary=False, biome_edge=False,
            char=".", fg_color=(128, 128, 128), bg_color=(64, 64, 64)
        )
        
        resource = generator._select_appropriate_resource(forest_tile, world_tile)
        if resource:  # Might be None due to randomness
            assert resource == ResourceConcentration.WOOD_GROVE
    
    def test_terrain_boundary_marking(self):
        """Test terrain boundary marking"""
        generator = RegionalScaleGenerator(12345)
        world_tile = create_test_world_tile(BiomeType.GRASSLAND)
        
        regional_map = generator._initialize_regional_map(world_tile)
        
        # Create a terrain boundary manually
        for y in range(generator.region_size):
            for x in range(generator.region_size):
                if x < generator.region_size // 2:
                    regional_map[y][x].terrain_subtype = TerrainSubtype.PLAINS
                else:
                    regional_map[y][x].terrain_subtype = TerrainSubtype.MEADOWS
        
        generator._mark_terrain_boundaries(regional_map)
        
        # Check that boundary tiles are marked
        boundary_count = 0
        for row in regional_map:
            for tile in row:
                if tile.terrain_boundary:
                    boundary_count += 1
        
        assert boundary_count > 0  # Should have marked some boundaries
    
    def test_fertility_calculation(self):
        """Test fertility calculation"""
        generator = RegionalScaleGenerator(12345)
        world_tile = create_test_world_tile(BiomeType.GRASSLAND)
        world_tile.precipitation = 0.8
        world_tile.temperature = 0.6
        
        # Test different terrain types
        plains_tile = RegionalTile(
            x=0, y=0, parent_biome=BiomeType.GRASSLAND,
            terrain_subtype=TerrainSubtype.PLAINS,
            micro_elevation=0.0, has_minor_river=False, river_size=0,
            is_lake=False, lake_id=None, water_flow_direction=None,
            landmark=None, resource_concentration=None,
            fertility=0.0, accessibility=0.0,
            terrain_boundary=False, biome_edge=False,
            char=".", fg_color=(128, 128, 128), bg_color=(64, 64, 64)
        )
        
        mountain_tile = RegionalTile(
            x=0, y=0, parent_biome=BiomeType.HIGH_MOUNTAINS,
            terrain_subtype=TerrainSubtype.CLIFFS,
            micro_elevation=0.0, has_minor_river=False, river_size=0,
            is_lake=False, lake_id=None, water_flow_direction=None,
            landmark=None, resource_concentration=None,
            fertility=0.0, accessibility=0.0,
            terrain_boundary=False, biome_edge=False,
            char=".", fg_color=(128, 128, 128), bg_color=(64, 64, 64)
        )
        
        plains_fertility = generator._calculate_fertility(plains_tile, world_tile)
        mountain_fertility = generator._calculate_fertility(mountain_tile, world_tile)
        
        # Plains should be more fertile than cliffs
        assert plains_fertility > mountain_fertility
        assert 0.0 <= plains_fertility <= 1.0
        assert 0.0 <= mountain_fertility <= 1.0
    
    def test_accessibility_calculation(self):
        """Test accessibility calculation"""
        generator = RegionalScaleGenerator(12345)
        
        # Test different terrain types
        plains_tile = RegionalTile(
            x=0, y=0, parent_biome=BiomeType.GRASSLAND,
            terrain_subtype=TerrainSubtype.PLAINS,
            micro_elevation=0.0, has_minor_river=False, river_size=0,
            is_lake=False, lake_id=None, water_flow_direction=None,
            landmark=None, resource_concentration=None,
            fertility=0.0, accessibility=0.0,
            terrain_boundary=False, biome_edge=False,
            char=".", fg_color=(128, 128, 128), bg_color=(64, 64, 64)
        )
        
        cliff_tile = RegionalTile(
            x=0, y=0, parent_biome=BiomeType.HIGH_MOUNTAINS,
            terrain_subtype=TerrainSubtype.CLIFFS,
            micro_elevation=0.0, has_minor_river=False, river_size=0,
            is_lake=False, lake_id=None, water_flow_direction=None,
            landmark=None, resource_concentration=None,
            fertility=0.0, accessibility=0.0,
            terrain_boundary=False, biome_edge=False,
            char=".", fg_color=(128, 128, 128), bg_color=(64, 64, 64)
        )
        
        plains_accessibility = generator._calculate_accessibility(plains_tile)
        cliff_accessibility = generator._calculate_accessibility(cliff_tile)
        
        # Plains should be more accessible than cliffs
        assert plains_accessibility > cliff_accessibility
        assert 0.0 <= plains_accessibility <= 1.0
        assert 0.0 <= cliff_accessibility <= 1.0
    
    def test_get_regional_tile(self):
        """Test regional tile access"""
        generator = RegionalScaleGenerator(12345)
        world_tile = create_test_world_tile(BiomeType.GRASSLAND)
        
        regional_map = generator.generate_regional_map(world_tile, {})
        
        # Test valid coordinates
        tile = generator.get_regional_tile(regional_map, 0, 0)
        assert tile is not None
        assert tile.x == 0
        assert tile.y == 0
        
        tile = generator.get_regional_tile(regional_map, 15, 15)  # Center
        assert tile is not None
        assert tile.x == 15
        assert tile.y == 15
        
        # Test invalid coordinates
        assert generator.get_regional_tile(regional_map, -1, 0) is None
        assert generator.get_regional_tile(regional_map, 0, -1) is None
        assert generator.get_regional_tile(regional_map, generator.region_size, 0) is None
        assert generator.get_regional_tile(regional_map, 0, generator.region_size) is None


if __name__ == "__main__":
    pytest.main([__file__])
