"""
Tests for the noise generation module.
"""

import pytest

from src.covenant.world.noise import (
    NoiseConfig,
    NoiseGenerator,
    create_default_noise_generator,
    create_terrain_noise_generator
)


class TestNoiseConfig:
    """Test the NoiseConfig dataclass."""
    
    def test_default_values(self):
        """Test that NoiseConfig has expected default values."""
        config = NoiseConfig()
        
        assert config.octaves == 4
        assert config.frequency == 0.05
        assert config.amplitude == 1.0
        assert config.persistence == 0.5
        assert config.lacunarity == 2.0
        assert config.seed == 12345
    
    def test_custom_values(self):
        """Test that NoiseConfig accepts custom values."""
        config = NoiseConfig(
            octaves=6,
            frequency=0.1,
            amplitude=2.0,
            persistence=0.7,
            lacunarity=1.5,
            seed=54321
        )
        
        assert config.octaves == 6
        assert config.frequency == 0.1
        assert config.amplitude == 2.0
        assert config.persistence == 0.7
        assert config.lacunarity == 1.5
        assert config.seed == 54321


class TestNoiseGenerator:
    """Test the NoiseGenerator class."""
    
    def test_initialization(self):
        """Test that NoiseGenerator initializes correctly."""
        config = NoiseConfig()
        generator = NoiseGenerator(config)
        
        assert generator.config == config
        assert len(generator._permutation) == 512  # Doubled for overflow prevention
        assert len(generator._gradients) == 8
    
    def test_deterministic_generation(self):
        """Test that noise generation is deterministic with same seed."""
        config1 = NoiseConfig(seed=12345)
        config2 = NoiseConfig(seed=12345)
        
        generator1 = NoiseGenerator(config1)
        generator2 = NoiseGenerator(config2)
        
        # Same coordinates should produce same values
        value1 = generator1.generate(10.5, 20.3)
        value2 = generator2.generate(10.5, 20.3)
        
        assert value1 == value2
    
    def test_different_seeds_produce_different_values(self):
        """Test that different seeds produce different noise values."""
        config1 = NoiseConfig(seed=12345)
        config2 = NoiseConfig(seed=54321)
        
        generator1 = NoiseGenerator(config1)
        generator2 = NoiseGenerator(config2)
        
        value1 = generator1.generate(10.5, 20.3)
        value2 = generator2.generate(10.5, 20.3)
        
        assert value1 != value2
    
    def test_noise_value_range(self):
        """Test that noise values are within expected range."""
        config = NoiseConfig()
        generator = NoiseGenerator(config)
        
        # Test multiple coordinates
        for x in range(-10, 11):
            for y in range(-10, 11):
                value = generator.generate(x, y)
                assert -1.0 <= value <= 1.0
    
    def test_fade_function(self):
        """Test the fade function behavior."""
        config = NoiseConfig()
        generator = NoiseGenerator(config)
        
        # Test boundary values
        assert generator._fade(0.0) == 0.0
        assert generator._fade(1.0) == 1.0
        
        # Test that fade is smooth (derivative is 0 at boundaries)
        assert abs(generator._fade(0.1) - 0.0) < 0.1
        assert abs(generator._fade(0.9) - 1.0) < 0.1
    
    def test_lerp_function(self):
        """Test the linear interpolation function."""
        config = NoiseConfig()
        generator = NoiseGenerator(config)
        
        # Test boundary values
        assert generator._lerp(10, 20, 0.0) == 10
        assert generator._lerp(10, 20, 1.0) == 20
        
        # Test midpoint
        assert generator._lerp(10, 20, 0.5) == 15
    
    def test_chunk_generation(self):
        """Test chunk-based noise generation."""
        config = NoiseConfig()
        generator = NoiseGenerator(config)
        
        chunk_size = 16
        chunk_data = generator.generate_chunk(0, 0, chunk_size)
        
        # Check dimensions
        assert len(chunk_data) == chunk_size
        assert len(chunk_data[0]) == chunk_size
        
        # Check all values are in range
        for row in chunk_data:
            for value in row:
                assert -1.0 <= value <= 1.0
    
    def test_chunk_consistency(self):
        """Test that chunk generation is consistent with individual generation."""
        config = NoiseConfig()
        generator = NoiseGenerator(config)
        
        chunk_size = 4
        chunk_x, chunk_y = 1, 1
        chunk_data = generator.generate_chunk(chunk_x, chunk_y, chunk_size)
        
        # Compare with individual generation
        for y in range(chunk_size):
            for x in range(chunk_size):
                world_x = chunk_x * chunk_size + x
                world_y = chunk_y * chunk_size + y
                
                individual_value = generator.generate(world_x, world_y)
                chunk_value = chunk_data[y][x]
                
                assert abs(individual_value - chunk_value) < 1e-10


class TestNoiseFactoryFunctions:
    """Test the factory functions for creating noise generators."""
    
    def test_create_default_noise_generator(self):
        """Test the default noise generator factory."""
        generator = create_default_noise_generator()
        
        assert isinstance(generator, NoiseGenerator)
        assert generator.config.octaves == 4
        assert generator.config.frequency == 0.05
    
    def test_create_terrain_noise_generator_default_seed(self):
        """Test terrain noise generator with default seed."""
        generator = create_terrain_noise_generator()
        
        assert isinstance(generator, NoiseGenerator)
        assert generator.config.octaves == 6
        assert generator.config.frequency == 0.03
        assert generator.config.seed == 12345
    
    def test_create_terrain_noise_generator_custom_seed(self):
        """Test terrain noise generator with custom seed."""
        custom_seed = 99999
        generator = create_terrain_noise_generator(custom_seed)
        
        assert generator.config.seed == custom_seed
    
    def test_terrain_generator_reproducibility(self):
        """Test that terrain generators with same seed produce same results."""
        seed = 42
        generator1 = create_terrain_noise_generator(seed)
        generator2 = create_terrain_noise_generator(seed)
        
        value1 = generator1.generate(5.5, 7.3)
        value2 = generator2.generate(5.5, 7.3)
        
        assert value1 == value2


if __name__ == "__main__":
    pytest.main([__file__])
