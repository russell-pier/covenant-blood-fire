"""
Tests for the terrain module.
"""

import pytest

from src.covenant.world.terrain import (
    TerrainType,
    TerrainProperties,
    TerrainMapper,
    create_default_terrain_mapper
)


class TestTerrainType:
    """Test the TerrainType enumeration."""
    
    def test_terrain_types_exist(self):
        """Test that all expected terrain types exist."""
        expected_types = [
            "DEEP_WATER", "SHALLOW_WATER", "SAND", "GRASS",
            "LIGHT_GRASS", "DARK_GRASS", "FOREST", "HILLS", "MOUNTAINS"
        ]
        
        for terrain_name in expected_types:
            assert hasattr(TerrainType, terrain_name)
    
    def test_terrain_type_values(self):
        """Test that terrain types have expected string values."""
        assert TerrainType.DEEP_WATER.value == "deep_water"
        assert TerrainType.GRASS.value == "grass"
        assert TerrainType.MOUNTAINS.value == "mountains"


class TestTerrainProperties:
    """Test the TerrainProperties dataclass."""
    
    def test_terrain_properties_creation(self):
        """Test creating terrain properties."""
        props = TerrainProperties(
            terrain_type=TerrainType.GRASS,
            character=" ",
            foreground_color=(0, 0, 0),
            background_color=(50, 120, 50),
            movement_cost=1.0,
            passable=True,
            description="Grassland"
        )
        
        assert props.terrain_type == TerrainType.GRASS
        assert props.character == " "
        assert props.foreground_color == (0, 0, 0)
        assert props.background_color == (50, 120, 50)
        assert props.movement_cost == 1.0
        assert props.passable is True
        assert props.description == "Grassland"


class TestTerrainMapper:
    """Test the TerrainMapper class."""
    
    def test_initialization(self):
        """Test that TerrainMapper initializes correctly."""
        mapper = TerrainMapper()
        
        # Check that all terrain types have properties
        for terrain_type in TerrainType:
            props = mapper.get_terrain_properties(terrain_type)
            assert isinstance(props, TerrainProperties)
            assert props.terrain_type == terrain_type
    
    def test_noise_to_terrain_mapping(self):
        """Test noise value to terrain type mapping."""
        mapper = TerrainMapper()
        
        # Test specific noise values
        assert mapper.noise_to_terrain(-1.0) == TerrainType.DEEP_WATER
        assert mapper.noise_to_terrain(-0.8) == TerrainType.SHALLOW_WATER
        assert mapper.noise_to_terrain(-0.4) == TerrainType.SAND
        assert mapper.noise_to_terrain(0.0) == TerrainType.GRASS
        assert mapper.noise_to_terrain(0.2) == TerrainType.LIGHT_GRASS
        assert mapper.noise_to_terrain(0.6) == TerrainType.HILLS
        assert mapper.noise_to_terrain(1.0) == TerrainType.MOUNTAINS
    
    def test_noise_to_terrain_edge_cases(self):
        """Test edge cases for noise to terrain mapping."""
        mapper = TerrainMapper()
        
        # Test values at threshold boundaries
        assert mapper.noise_to_terrain(-0.6) == TerrainType.SHALLOW_WATER
        assert mapper.noise_to_terrain(-0.59) == TerrainType.SAND
        
        # Test extreme values
        assert mapper.noise_to_terrain(-999.0) == TerrainType.DEEP_WATER
        assert mapper.noise_to_terrain(999.0) == TerrainType.MOUNTAINS
    
    def test_get_terrain_properties(self):
        """Test getting terrain properties."""
        mapper = TerrainMapper()
        
        grass_props = mapper.get_terrain_properties(TerrainType.GRASS)
        assert grass_props.terrain_type == TerrainType.GRASS
        assert grass_props.passable is True
        assert grass_props.movement_cost == 1.0
        
        water_props = mapper.get_terrain_properties(TerrainType.DEEP_WATER)
        assert water_props.terrain_type == TerrainType.DEEP_WATER
        assert water_props.passable is False
        assert water_props.movement_cost == float('inf')
    
    def test_get_all_terrain_types(self):
        """Test getting all terrain types."""
        mapper = TerrainMapper()
        all_types = mapper.get_all_terrain_types()
        
        assert len(all_types) == len(TerrainType)
        for terrain_type in TerrainType:
            assert terrain_type in all_types
    
    def test_is_passable(self):
        """Test passability checking."""
        mapper = TerrainMapper()
        
        # Test passable terrains
        assert mapper.is_passable(TerrainType.GRASS) is True
        assert mapper.is_passable(TerrainType.SAND) is True
        assert mapper.is_passable(TerrainType.FOREST) is True
        
        # Test impassable terrains
        assert mapper.is_passable(TerrainType.DEEP_WATER) is False
        assert mapper.is_passable(TerrainType.MOUNTAINS) is False
    
    def test_get_movement_cost(self):
        """Test movement cost retrieval."""
        mapper = TerrainMapper()
        
        # Test normal movement cost
        assert mapper.get_movement_cost(TerrainType.GRASS) == 1.0
        
        # Test slow movement
        assert mapper.get_movement_cost(TerrainType.FOREST) > 1.0
        assert mapper.get_movement_cost(TerrainType.SHALLOW_WATER) > 1.0
        
        # Test impassable
        assert mapper.get_movement_cost(TerrainType.DEEP_WATER) == float('inf')
        assert mapper.get_movement_cost(TerrainType.MOUNTAINS) == float('inf')
    
    def test_terrain_color_consistency(self):
        """Test that terrain colors are consistent and valid."""
        mapper = TerrainMapper()
        
        for terrain_type in TerrainType:
            props = mapper.get_terrain_properties(terrain_type)
            
            # Check color format (RGB tuples)
            assert len(props.foreground_color) == 3
            assert len(props.background_color) == 3
            
            # Check color value ranges
            for color_component in props.foreground_color:
                assert 0 <= color_component <= 255
            for color_component in props.background_color:
                assert 0 <= color_component <= 255
    
    def test_terrain_character_consistency(self):
        """Test that terrain characters are consistent."""
        mapper = TerrainMapper()
        
        for terrain_type in TerrainType:
            props = mapper.get_terrain_properties(terrain_type)
            
            # All terrains should use space character for background color display
            assert props.character == " "
    
    def test_water_terrain_properties(self):
        """Test specific properties of water terrains."""
        mapper = TerrainMapper()
        
        deep_water = mapper.get_terrain_properties(TerrainType.DEEP_WATER)
        shallow_water = mapper.get_terrain_properties(TerrainType.SHALLOW_WATER)
        
        # Deep water should be impassable
        assert not deep_water.passable
        assert deep_water.movement_cost == float('inf')
        
        # Shallow water should be passable but slow
        assert shallow_water.passable
        assert shallow_water.movement_cost > 1.0
        
        # Water should have blue-ish colors
        assert deep_water.background_color[2] > deep_water.background_color[0]  # More blue than red
        assert shallow_water.background_color[2] > shallow_water.background_color[0]
    
    def test_grass_terrain_variations(self):
        """Test that grass terrain variations have appropriate properties."""
        mapper = TerrainMapper()
        
        grass_types = [TerrainType.GRASS, TerrainType.LIGHT_GRASS, TerrainType.DARK_GRASS]
        
        for grass_type in grass_types:
            props = mapper.get_terrain_properties(grass_type)
            
            # All grass should be passable with normal movement
            assert props.passable
            assert props.movement_cost == 1.0
            
            # All grass should have green-ish colors
            assert props.background_color[1] > props.background_color[0]  # More green than red
            assert props.background_color[1] > props.background_color[2]  # More green than blue


class TestTerrainFactoryFunctions:
    """Test the factory functions for creating terrain mappers."""
    
    def test_create_default_terrain_mapper(self):
        """Test the default terrain mapper factory."""
        mapper = create_default_terrain_mapper()
        
        assert isinstance(mapper, TerrainMapper)
        
        # Test that it works correctly
        terrain = mapper.noise_to_terrain(0.0)
        assert terrain == TerrainType.GRASS
        
        props = mapper.get_terrain_properties(terrain)
        assert props.terrain_type == TerrainType.GRASS


if __name__ == "__main__":
    pytest.main([__file__])
