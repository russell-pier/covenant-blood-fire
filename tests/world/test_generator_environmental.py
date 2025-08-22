"""
Tests for the WorldGenerator with environmental system integration.

This module tests the integration between the WorldGenerator and the
environmental layer system.
"""

import pytest
from src.empires.world.generator import (
    WorldGenerator, create_default_world_generator, 
    create_legacy_world_generator, create_environmental_world_generator
)
from src.empires.world.terrain import TerrainType
from src.empires.world.environmental import EnvironmentalData
from src.empires.world.chunks import ChunkCoordinate


class TestWorldGeneratorEnvironmental:
    """Test WorldGenerator with environmental system."""
    
    def test_environmental_world_generator_creation(self):
        """Test that environmental world generator is created correctly."""
        generator = create_environmental_world_generator(seed=12345)
        
        assert generator.use_environmental_system is True
        assert hasattr(generator, 'environmental_generator')
        assert hasattr(generator, 'terrain_mapper')
        assert hasattr(generator.terrain_mapper, 'environmental_to_terrain')
    
    def test_legacy_world_generator_creation(self):
        """Test that legacy world generator still works."""
        generator = create_legacy_world_generator(seed=12345)
        
        assert generator.use_environmental_system is False
        assert hasattr(generator, 'noise_generator')
        assert hasattr(generator, 'terrain_mapper')
        assert not hasattr(generator.terrain_mapper, 'environmental_to_terrain')
    
    def test_default_world_generator_uses_environmental(self):
        """Test that default world generator uses environmental system."""
        generator = create_default_world_generator(seed=12345)
        
        assert generator.use_environmental_system is True
        assert hasattr(generator, 'environmental_generator')
    
    def test_environmental_terrain_generation(self):
        """Test that environmental system generates terrain correctly."""
        generator = create_environmental_world_generator(seed=12345)
        
        # Generate terrain at various locations
        terrain_types = set()
        for x in range(0, 100, 10):
            for y in range(0, 100, 10):
                terrain = generator.get_terrain_at(x, y)
                terrain_types.add(terrain)
        
        # Should have multiple terrain types
        assert len(terrain_types) > 1
        
        # Should include some of the new terrain types
        all_terrain_types = {t for t in TerrainType}
        assert terrain_types.issubset(all_terrain_types)
    
    def test_environmental_data_retrieval(self):
        """Test that environmental data can be retrieved."""
        generator = create_environmental_world_generator(seed=12345)
        
        env_data = generator.get_environmental_data_at(50, 50)
        
        assert env_data is not None
        assert isinstance(env_data, EnvironmentalData)
        assert 0.0 <= env_data.elevation <= 1.0
        assert 0.0 <= env_data.moisture <= 1.0
        assert 0.0 <= env_data.temperature <= 1.0
    
    def test_legacy_environmental_data_returns_none(self):
        """Test that legacy generator returns None for environmental data."""
        generator = create_legacy_world_generator(seed=12345)
        
        env_data = generator.get_environmental_data_at(50, 50)
        
        assert env_data is None
    
    def test_chunk_generation_with_environmental_data(self):
        """Test that chunks are generated with environmental data."""
        generator = create_environmental_world_generator(seed=12345)
        
        chunk_coord = ChunkCoordinate(0, 0)
        chunk = generator.get_chunk_terrain_data(chunk_coord)
        
        assert chunk is not None
        assert chunk.is_generated
        assert len(chunk.terrain_data) == generator.chunk_size
        assert len(chunk.environmental_data) == generator.chunk_size
        
        # Check that environmental data is properly set
        env_data = chunk.get_environmental_data_at(0, 0)
        assert isinstance(env_data, EnvironmentalData)
    
    def test_deterministic_generation_environmental(self):
        """Test that environmental generation is deterministic."""
        generator1 = create_environmental_world_generator(seed=12345)
        generator2 = create_environmental_world_generator(seed=12345)
        
        # Test terrain generation
        for x in range(0, 20, 5):
            for y in range(0, 20, 5):
                terrain1 = generator1.get_terrain_at(x, y)
                terrain2 = generator2.get_terrain_at(x, y)
                assert terrain1 == terrain2
        
        # Test environmental data generation
        for x in range(0, 20, 5):
            for y in range(0, 20, 5):
                env1 = generator1.get_environmental_data_at(x, y)
                env2 = generator2.get_environmental_data_at(x, y)
                assert env1.elevation == env2.elevation
                assert env1.moisture == env2.moisture
                assert env1.temperature == env2.temperature
    
    def test_different_seeds_produce_different_worlds(self):
        """Test that different seeds produce different worlds."""
        generator1 = create_environmental_world_generator(seed=12345)
        generator2 = create_environmental_world_generator(seed=54321)
        
        # Check that at least some terrain is different
        differences = 0
        for x in range(0, 50, 10):
            for y in range(0, 50, 10):
                terrain1 = generator1.get_terrain_at(x, y)
                terrain2 = generator2.get_terrain_at(x, y)
                if terrain1 != terrain2:
                    differences += 1
        
        # Should have some differences
        assert differences > 0
    
    def test_terrain_type_distribution(self):
        """Test that environmental system produces reasonable terrain distribution."""
        generator = create_environmental_world_generator(seed=12345)
        
        terrain_counts = {}
        total_samples = 0
        
        # Sample a larger area
        for x in range(0, 200, 5):
            for y in range(0, 200, 5):
                terrain = generator.get_terrain_at(x, y)
                terrain_counts[terrain] = terrain_counts.get(terrain, 0) + 1
                total_samples += 1
        
        # Should have multiple terrain types
        assert len(terrain_counts) >= 3
        
        # No single terrain type should dominate completely (> 80%)
        for terrain, count in terrain_counts.items():
            percentage = count / total_samples
            assert percentage < 0.8, f"{terrain} dominates with {percentage:.2%}"
    
    def test_water_terrain_characteristics(self):
        """Test that water terrain appears in appropriate environmental conditions."""
        generator = create_environmental_world_generator(seed=12345)
        
        water_locations = []
        
        # Find water locations
        for x in range(0, 100, 2):
            for y in range(0, 100, 2):
                terrain = generator.get_terrain_at(x, y)
                if terrain in [TerrainType.DEEP_WATER, TerrainType.SHALLOW_WATER]:
                    env_data = generator.get_environmental_data_at(x, y)
                    water_locations.append((x, y, terrain, env_data))
        
        # Should have some water
        assert len(water_locations) > 0
        
        # Water should generally have low elevation
        for x, y, terrain, env_data in water_locations:
            assert env_data.elevation < 0.4, f"Water at ({x}, {y}) has high elevation: {env_data.elevation}"
    
    def test_mountain_terrain_characteristics(self):
        """Test that mountain terrain appears in appropriate environmental conditions."""
        generator = create_environmental_world_generator(seed=12345)
        
        mountain_locations = []
        
        # Find mountain locations
        for x in range(0, 100, 2):
            for y in range(0, 100, 2):
                terrain = generator.get_terrain_at(x, y)
                if terrain == TerrainType.MOUNTAINS:
                    env_data = generator.get_environmental_data_at(x, y)
                    mountain_locations.append((x, y, terrain, env_data))
        
        # If we have mountains, they should have high elevation and low temperature
        for x, y, terrain, env_data in mountain_locations:
            assert env_data.elevation > 0.6, f"Mountain at ({x}, {y}) has low elevation: {env_data.elevation}"
            assert env_data.temperature < 0.5, f"Mountain at ({x}, {y}) has high temperature: {env_data.temperature}"
    
    def test_desert_terrain_characteristics(self):
        """Test that desert terrain appears in appropriate environmental conditions."""
        generator = create_environmental_world_generator(seed=12345)
        
        desert_locations = []
        
        # Find desert locations
        for x in range(0, 100, 2):
            for y in range(0, 100, 2):
                terrain = generator.get_terrain_at(x, y)
                if terrain == TerrainType.DESERT:
                    env_data = generator.get_environmental_data_at(x, y)
                    desert_locations.append((x, y, terrain, env_data))
        
        # If we have deserts, they should have high temperature and low moisture
        for x, y, terrain, env_data in desert_locations:
            assert env_data.temperature > 0.6, f"Desert at ({x}, {y}) has low temperature: {env_data.temperature}"
            assert env_data.moisture < 0.4, f"Desert at ({x}, {y}) has high moisture: {env_data.moisture}"


class TestBackwardCompatibility:
    """Test backward compatibility between environmental and legacy systems."""
    
    def test_legacy_system_still_works(self):
        """Test that legacy noise-based system still functions."""
        generator = create_legacy_world_generator(seed=12345)
        
        # Should be able to generate terrain
        terrain = generator.get_terrain_at(50, 50)
        assert isinstance(terrain, TerrainType)
        
        # Should be able to generate chunks
        chunk_coord = ChunkCoordinate(0, 0)
        chunk = generator.get_chunk_terrain_data(chunk_coord)
        assert chunk is not None
        assert chunk.is_generated
        
        # Environmental data should not be available
        env_data = generator.get_environmental_data_at(50, 50)
        assert env_data is None
    
    def test_performance_comparison(self):
        """Test that environmental system performance is reasonable."""
        import time
        
        # Test legacy system performance
        legacy_generator = create_legacy_world_generator(seed=12345)
        start_time = time.time()
        for x in range(0, 50, 2):
            for y in range(0, 50, 2):
                legacy_generator.get_terrain_at(x, y)
        legacy_time = time.time() - start_time
        
        # Test environmental system performance
        env_generator = create_environmental_world_generator(seed=12345)
        start_time = time.time()
        for x in range(0, 50, 2):
            for y in range(0, 50, 2):
                env_generator.get_terrain_at(x, y)
        env_time = time.time() - start_time
        
        # Environmental system should not be more than 5x slower
        # (This is a generous limit for the additional computation)
        assert env_time < legacy_time * 5, f"Environmental system too slow: {env_time:.3f}s vs {legacy_time:.3f}s"
