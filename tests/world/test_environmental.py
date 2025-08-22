"""
Tests for the environmental layer generation system.

This module tests the environmental data structures, generators, and
terrain mapping functionality.
"""

import pytest
from src.empires.world.environmental import (
    EnvironmentalData, EnvironmentalGenerator, 
    create_default_environmental_generator
)
from src.empires.world.environmental_config import (
    EnvironmentalConfig, create_default_environmental_config
)
from src.empires.world.terrain import (
    EnvironmentalTerrainMapper, TerrainType, create_environmental_terrain_mapper
)


class TestEnvironmentalData:
    """Test the EnvironmentalData dataclass."""
    
    def test_valid_environmental_data(self):
        """Test that EnvironmentalData accepts valid values."""
        env_data = EnvironmentalData(
            elevation=0.5,
            moisture=0.3,
            temperature=0.7
        )
        
        assert env_data.elevation == 0.5
        assert env_data.moisture == 0.3
        assert env_data.temperature == 0.7
    
    def test_environmental_data_validation(self):
        """Test that EnvironmentalData validates input ranges."""
        # Test elevation out of range
        with pytest.raises(ValueError, match="elevation must be between 0.0 and 1.0"):
            EnvironmentalData(elevation=-0.1, moisture=0.5, temperature=0.5)
        
        with pytest.raises(ValueError, match="elevation must be between 0.0 and 1.0"):
            EnvironmentalData(elevation=1.1, moisture=0.5, temperature=0.5)
        
        # Test moisture out of range
        with pytest.raises(ValueError, match="moisture must be between 0.0 and 1.0"):
            EnvironmentalData(elevation=0.5, moisture=-0.1, temperature=0.5)
        
        # Test temperature out of range
        with pytest.raises(ValueError, match="temperature must be between 0.0 and 1.0"):
            EnvironmentalData(elevation=0.5, moisture=0.5, temperature=1.1)


class TestEnvironmentalConfig:
    """Test the EnvironmentalConfig dataclass."""
    
    def test_default_config(self):
        """Test that default configuration has expected values."""
        config = create_default_environmental_config()
        
        assert config.elevation_octaves == 6
        assert config.elevation_frequency == 0.025
        assert config.elevation_persistence == 0.65
        
        assert config.moisture_octaves == 3
        assert config.moisture_frequency == 0.05
        assert config.moisture_persistence == 0.5
        
        assert config.temperature_octaves == 2
        assert config.temperature_frequency == 0.04
        assert config.temperature_persistence == 0.4


class TestEnvironmentalGenerator:
    """Test the EnvironmentalGenerator class."""
    
    def test_generator_initialization(self):
        """Test that generator initializes correctly."""
        generator = create_default_environmental_generator(seed=12345)
        
        assert generator.base_seed == 12345
        assert generator.config is not None
        assert hasattr(generator, 'elevation_noise')
        assert hasattr(generator, 'moisture_noise')
        assert hasattr(generator, 'temperature_noise')
    
    def test_generate_environmental_data(self):
        """Test that environmental data generation produces valid values."""
        generator = create_default_environmental_generator(seed=12345)
        
        env_data = generator.generate_environmental_data(0, 0)
        
        assert isinstance(env_data, EnvironmentalData)
        assert 0.0 <= env_data.elevation <= 1.0
        assert 0.0 <= env_data.moisture <= 1.0
        assert 0.0 <= env_data.temperature <= 1.0
    
    def test_deterministic_generation(self):
        """Test that same seed produces same results."""
        generator1 = create_default_environmental_generator(seed=12345)
        generator2 = create_default_environmental_generator(seed=12345)
        
        env_data1 = generator1.generate_environmental_data(10, 20)
        env_data2 = generator2.generate_environmental_data(10, 20)
        
        assert env_data1.elevation == env_data2.elevation
        assert env_data1.moisture == env_data2.moisture
        assert env_data1.temperature == env_data2.temperature
    
    def test_different_seeds_produce_different_results(self):
        """Test that different seeds produce different results."""
        generator1 = create_default_environmental_generator(seed=12345)
        generator2 = create_default_environmental_generator(seed=54321)
        
        env_data1 = generator1.generate_environmental_data(10, 20)
        env_data2 = generator2.generate_environmental_data(10, 20)
        
        # At least one value should be different
        assert (env_data1.elevation != env_data2.elevation or
                env_data1.moisture != env_data2.moisture or
                env_data1.temperature != env_data2.temperature)
    
    def test_generate_chunk_environmental_data(self):
        """Test chunk-based environmental data generation."""
        generator = create_default_environmental_generator(seed=12345)
        
        chunk_data = generator.generate_chunk_environmental_data(0, 0, 4)
        
        assert len(chunk_data) == 4
        assert len(chunk_data[0]) == 4
        
        # Check that all data is valid
        for row in chunk_data:
            for env_data in row:
                assert isinstance(env_data, EnvironmentalData)
                assert 0.0 <= env_data.elevation <= 1.0
                assert 0.0 <= env_data.moisture <= 1.0
                assert 0.0 <= env_data.temperature <= 1.0


class TestEnvironmentalTerrainMapper:
    """Test the EnvironmentalTerrainMapper class."""
    
    def test_mapper_initialization(self):
        """Test that mapper initializes correctly."""
        mapper = create_environmental_terrain_mapper()
        
        assert isinstance(mapper, EnvironmentalTerrainMapper)
        assert hasattr(mapper, 'environmental_to_terrain')
        assert hasattr(mapper, 'get_terrain_properties_with_variation')
    
    def test_environmental_to_terrain_caves(self):
        """Test that low elevation produces caves."""
        mapper = create_environmental_terrain_mapper()
        
        env_data = EnvironmentalData(elevation=0.1, moisture=0.5, temperature=0.5)
        terrain = mapper.environmental_to_terrain(env_data)
        
        assert terrain == TerrainType.CAVES
    
    def test_environmental_to_terrain_water(self):
        """Test that appropriate elevation produces water."""
        mapper = create_environmental_terrain_mapper()
        
        # Deep water
        env_data = EnvironmentalData(elevation=0.24, moisture=0.5, temperature=0.5)
        terrain = mapper.environmental_to_terrain(env_data)
        assert terrain == TerrainType.DEEP_WATER
        
        # Shallow water
        env_data = EnvironmentalData(elevation=0.32, moisture=0.5, temperature=0.5)
        terrain = mapper.environmental_to_terrain(env_data)
        assert terrain == TerrainType.SHALLOW_WATER
    
    def test_environmental_to_terrain_desert(self):
        """Test that hot and dry conditions produce desert."""
        mapper = create_environmental_terrain_mapper()
        
        env_data = EnvironmentalData(elevation=0.5, moisture=0.2, temperature=0.8)
        terrain = mapper.environmental_to_terrain(env_data)
        
        assert terrain == TerrainType.DESERT
    
    def test_environmental_to_terrain_forest(self):
        """Test that moist and temperate conditions produce forest."""
        mapper = create_environmental_terrain_mapper()

        # This now produces fertile terrain due to priority order
        env_data = EnvironmentalData(elevation=0.5, moisture=0.7, temperature=0.5)
        terrain = mapper.environmental_to_terrain(env_data)
        assert terrain == TerrainType.FERTILE

        # Test conditions that should produce forest (outside fertile range)
        env_data = EnvironmentalData(elevation=0.7, moisture=0.7, temperature=0.5)
        terrain = mapper.environmental_to_terrain(env_data)
        assert terrain == TerrainType.FOREST
    
    def test_environmental_to_terrain_swamp(self):
        """Test that low elevation and high moisture produce swamp."""
        mapper = create_environmental_terrain_mapper()
        
        env_data = EnvironmentalData(elevation=0.38, moisture=0.9, temperature=0.5)
        terrain = mapper.environmental_to_terrain(env_data)
        
        assert terrain == TerrainType.SWAMP
    
    def test_get_terrain_properties_with_variation(self):
        """Test that color variation works correctly."""
        mapper = create_environmental_terrain_mapper()
        
        env_data = EnvironmentalData(elevation=0.5, moisture=0.5, temperature=0.5)
        base_props = mapper.get_terrain_properties(TerrainType.GRASS)
        varied_props = mapper.get_terrain_properties_with_variation(
            TerrainType.GRASS, env_data, 10, 20
        )
        
        # Properties should be the same except for background color
        assert varied_props.terrain_type == base_props.terrain_type
        assert varied_props.character == base_props.character
        assert varied_props.foreground_color == base_props.foreground_color
        assert varied_props.movement_cost == base_props.movement_cost
        assert varied_props.passable == base_props.passable
        assert varied_props.description == base_props.description
        
        # Background color should be different (due to environmental variation)
        # Note: This might occasionally fail due to random variation, but very unlikely
        assert varied_props.background_color != base_props.background_color


class TestEnvironmentalIntegration:
    """Test integration between environmental components."""
    
    def test_full_environmental_pipeline(self):
        """Test the complete environmental generation pipeline."""
        generator = create_default_environmental_generator(seed=12345)
        mapper = create_environmental_terrain_mapper()
        
        # Generate environmental data
        env_data = generator.generate_environmental_data(50, 50)
        
        # Convert to terrain
        terrain_type = mapper.environmental_to_terrain(env_data)
        
        # Get properties with variation
        terrain_props = mapper.get_terrain_properties_with_variation(
            terrain_type, env_data, 50, 50
        )
        
        # Verify all components work together
        assert isinstance(env_data, EnvironmentalData)
        assert isinstance(terrain_type, TerrainType)
        assert terrain_props.terrain_type == terrain_type
        assert len(terrain_props.background_color) == 3  # RGB tuple
        assert all(0 <= c <= 255 for c in terrain_props.background_color)
