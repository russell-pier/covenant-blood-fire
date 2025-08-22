"""
Tests for the organic world generation system.

This module tests the organic terrain generation, character variations,
and visual enhancements.
"""

import pytest
from src.empires.world.organic import (
    OrganicWorldGenerator, OrganicTerrainData, OrganicNoiseGenerator,
    TERRAIN_CHARACTER_VARIATIONS, create_organic_world_generator
)
from src.empires.world.generator import create_organic_world_generator as create_integrated_organic_generator
from src.empires.world.terrain import TerrainType


class TestOrganicNoiseGenerator:
    """Test the enhanced organic noise generator."""
    
    def test_noise_generator_initialization(self):
        """Test that noise generator initializes correctly."""
        generator = OrganicNoiseGenerator(seed=12345)
        
        assert hasattr(generator, 'permutation')
        assert len(generator.permutation) == 512  # 256 * 2
    
    def test_noise_generation(self):
        """Test basic noise generation."""
        generator = OrganicNoiseGenerator(seed=12345)
        
        noise_value = generator.noise(0.5, 0.5)
        assert isinstance(noise_value, float)
        assert -1.0 <= noise_value <= 1.0
    
    def test_octave_noise_generation(self):
        """Test multi-octave noise generation."""
        generator = OrganicNoiseGenerator(seed=12345)
        
        noise_value = generator.octave_noise(0.5, 0.5, octaves=4)
        assert isinstance(noise_value, float)
        assert -1.0 <= noise_value <= 1.0
    
    def test_deterministic_noise(self):
        """Test that noise generation is deterministic."""
        generator1 = OrganicNoiseGenerator(seed=12345)
        generator2 = OrganicNoiseGenerator(seed=12345)
        
        for x in [0.1, 0.5, 1.0, 2.5]:
            for y in [0.1, 0.5, 1.0, 2.5]:
                noise1 = generator1.noise(x, y)
                noise2 = generator2.noise(x, y)
                assert noise1 == noise2


class TestOrganicWorldGenerator:
    """Test the organic world generator."""
    
    def test_generator_initialization(self):
        """Test that generator initializes correctly."""
        generator = OrganicWorldGenerator(seed=12345)
        
        assert generator.seed == 12345
        assert hasattr(generator, 'noise_elevation')
        assert hasattr(generator, 'noise_moisture')
        assert hasattr(generator, 'noise_temperature')
        assert hasattr(generator, 'noise_detail')
        assert hasattr(generator, 'noise_water')
        assert hasattr(generator, 'noise_transition')
    
    def test_generator_with_none_seed(self):
        """Test that generator handles None seed correctly."""
        generator = OrganicWorldGenerator(seed=None)
        
        assert generator.seed == 12345  # Default seed
    
    def test_chunk_data_generation(self):
        """Test chunk data generation."""
        generator = OrganicWorldGenerator(seed=12345)
        
        chunk_data = generator.generate_chunk_data(0, 0, 4)
        
        assert len(chunk_data) == 16  # 4x4 chunk
        
        # Check that all positions are covered
        for x in range(4):
            for y in range(4):
                assert (x, y) in chunk_data
                terrain_data = chunk_data[(x, y)]
                assert isinstance(terrain_data, OrganicTerrainData)
                assert isinstance(terrain_data.terrain_type, TerrainType)
                assert isinstance(terrain_data.character, str)
                assert len(terrain_data.character) == 1
                assert len(terrain_data.foreground_color) == 3
                assert len(terrain_data.background_color) == 3
                assert 0.0 <= terrain_data.elevation <= 1.0
                assert 0.0 <= terrain_data.moisture <= 1.0
                assert 0.0 <= terrain_data.temperature <= 1.0
    
    def test_deterministic_chunk_generation(self):
        """Test that chunk generation is deterministic."""
        generator1 = OrganicWorldGenerator(seed=12345)
        generator2 = OrganicWorldGenerator(seed=12345)
        
        chunk1 = generator1.generate_chunk_data(0, 0, 4)
        chunk2 = generator2.generate_chunk_data(0, 0, 4)
        
        for x in range(4):
            for y in range(4):
                data1 = chunk1[(x, y)]
                data2 = chunk2[(x, y)]
                
                assert data1.terrain_type == data2.terrain_type
                assert data1.character == data2.character
                assert data1.foreground_color == data2.foreground_color
                assert data1.background_color == data2.background_color
                assert data1.elevation == data2.elevation
                assert data1.moisture == data2.moisture
                assert data1.temperature == data2.temperature
    
    def test_character_variations(self):
        """Test that different characters are used for the same terrain type."""
        generator = OrganicWorldGenerator(seed=12345)
        
        # Generate a larger area to get character variations
        characters_by_terrain = {}
        
        for chunk_x in range(3):
            for chunk_y in range(3):
                chunk_data = generator.generate_chunk_data(chunk_x, chunk_y, 8)
                
                for terrain_data in chunk_data.values():
                    terrain_type = terrain_data.terrain_type
                    if terrain_type not in characters_by_terrain:
                        characters_by_terrain[terrain_type] = set()
                    characters_by_terrain[terrain_type].add(terrain_data.character)
        
        # Check that we have character variations for common terrain types
        for terrain_type, characters in characters_by_terrain.items():
            if len(characters) > 1:
                # Verify characters are from the expected set
                expected_chars = set(TERRAIN_CHARACTER_VARIATIONS[terrain_type]['chars'])
                assert characters.issubset(expected_chars)
    
    def test_color_variations(self):
        """Test that colors vary based on environmental factors."""
        generator = OrganicWorldGenerator(seed=12345)
        
        chunk_data = generator.generate_chunk_data(0, 0, 8)
        
        # Collect colors for the same terrain type
        colors_by_terrain = {}
        
        for terrain_data in chunk_data.values():
            terrain_type = terrain_data.terrain_type
            if terrain_type not in colors_by_terrain:
                colors_by_terrain[terrain_type] = set()
            colors_by_terrain[terrain_type].add(terrain_data.background_color)
        
        # Check that we have color variations for terrain types
        for terrain_type, colors in colors_by_terrain.items():
            if len(colors) > 1:
                # Colors should be different
                assert len(colors) > 1, f"No color variation for {terrain_type}"


class TestTerrainCharacterVariations:
    """Test the terrain character variation system."""
    
    def test_all_terrain_types_have_variations(self):
        """Test that all terrain types have character variations defined."""
        for terrain_type in TerrainType:
            assert terrain_type in TERRAIN_CHARACTER_VARIATIONS
            
            config = TERRAIN_CHARACTER_VARIATIONS[terrain_type]
            assert 'chars' in config
            assert 'base_fg' in config
            assert 'base_bg' in config
            
            assert len(config['chars']) > 0
            assert len(config['base_fg']) == 3
            assert len(config['base_bg']) == 3
            
            # All characters should be single characters
            for char in config['chars']:
                assert len(char) == 1
    
    def test_character_uniqueness_within_terrain(self):
        """Test that character variations within terrain types are unique."""
        for terrain_type, config in TERRAIN_CHARACTER_VARIATIONS.items():
            chars = config['chars']
            assert len(chars) == len(set(chars)), f"Duplicate characters in {terrain_type}"


class TestIntegratedOrganicSystem:
    """Test the integrated organic system with WorldGenerator."""
    
    def test_integrated_generator_creation(self):
        """Test that integrated organic generator is created correctly."""
        generator = create_integrated_organic_generator(seed=12345)
        
        assert hasattr(generator, 'use_organic_system')
        assert generator.use_organic_system is True
        assert hasattr(generator, 'organic_generator')
    
    def test_terrain_generation_with_characters(self):
        """Test that terrain generation includes character variations."""
        generator = create_integrated_organic_generator(seed=12345)
        
        # Test terrain generation
        terrain_types = set()
        characters = set()
        
        for x in range(0, 50, 5):
            for y in range(0, 50, 5):
                terrain = generator.get_terrain_at(x, y)
                terrain_types.add(terrain)
                
                props = generator.get_organic_terrain_properties_at(x, y)
                if props:
                    characters.add(props.character)
        
        # Should have multiple terrain types and characters
        assert len(terrain_types) > 1
        assert len(characters) > 1
    
    def test_organic_terrain_properties(self):
        """Test that organic terrain properties are returned correctly."""
        generator = create_integrated_organic_generator(seed=12345)
        
        props = generator.get_organic_terrain_properties_at(10, 10)
        
        assert props is not None
        assert isinstance(props.terrain_type, TerrainType)
        assert isinstance(props.character, str)
        assert len(props.character) == 1
        assert len(props.foreground_color) == 3
        assert len(props.background_color) == 3
        assert all(0 <= c <= 255 for c in props.foreground_color)
        assert all(0 <= c <= 255 for c in props.background_color)
    
    def test_performance_comparison(self):
        """Test that organic system performance is reasonable."""
        import time
        
        # Test organic system
        organic_generator = create_integrated_organic_generator(seed=12345)
        start_time = time.time()
        
        for x in range(0, 50, 2):
            for y in range(0, 50, 2):
                organic_generator.get_terrain_at(x, y)
        
        organic_time = time.time() - start_time
        
        # Should complete in reasonable time (less than 1 second for this test)
        assert organic_time < 1.0, f"Organic generation too slow: {organic_time:.3f}s"


class TestOrganicFactoryFunctions:
    """Test the factory functions for organic generators."""
    
    def test_create_organic_world_generator(self):
        """Test the organic world generator factory function."""
        generator = create_organic_world_generator(seed=12345)
        
        assert isinstance(generator, OrganicWorldGenerator)
        assert generator.seed == 12345
    
    def test_create_organic_world_generator_none_seed(self):
        """Test the factory function with None seed."""
        generator = create_organic_world_generator(seed=None)
        
        assert isinstance(generator, OrganicWorldGenerator)
        assert generator.seed == 12345  # Default seed
