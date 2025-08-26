"""
Tests for the coordinate system and scale types.

This module tests the coordinate conversion utilities and ensures
proper mapping between World, Regional, and Local scales.
"""

import pytest
from src.covenant.world.data.scale_types import (
    ViewScale, ScaleConfig, get_scale_config,
    WorldCoordinate, RegionalCoordinate, LocalCoordinate, AbsoluteCoordinate,
    CoordinateSystem, ScaleTransition
)


class TestScaleConfig:
    """Test scale configuration functionality"""
    
    def test_get_scale_config_world(self):
        """Test world scale configuration"""
        config = get_scale_config(ViewScale.WORLD)
        assert config.name == "World"
        assert config.map_size == (128, 96)
        assert config.tile_size_meters == 1024 * 1024
        assert config.movement_speed == 1.0
        assert config.generation_cost == "low"
        assert config.cache_priority == 1
    
    def test_get_scale_config_regional(self):
        """Test regional scale configuration"""
        config = get_scale_config(ViewScale.REGIONAL)
        assert config.name == "Regional"
        assert config.map_size == (32, 32)
        assert config.tile_size_meters == 1024
        assert config.movement_speed == 0.8
        assert config.generation_cost == "medium"
        assert config.cache_priority == 2
    
    def test_get_scale_config_local(self):
        """Test local scale configuration"""
        config = get_scale_config(ViewScale.LOCAL)
        assert config.name == "Local"
        assert config.map_size == (32, 32)
        assert config.tile_size_meters == 1
        assert config.movement_speed == 0.6
        assert config.generation_cost == "high"
        assert config.cache_priority == 3


class TestCoordinateConversions:
    """Test coordinate conversion between scales"""
    
    def test_world_to_absolute(self):
        """Test world coordinate to absolute conversion"""
        world_coord = WorldCoordinate(1, 1)
        abs_coord = CoordinateSystem.world_to_absolute(world_coord)
        
        expected_x = 1 * 32 * 32  # 1 world sector = 32 regional blocks * 32 local meters
        expected_y = 1 * 32 * 32
        
        assert abs_coord.x == expected_x
        assert abs_coord.y == expected_y
    
    def test_regional_to_absolute(self):
        """Test regional coordinate to absolute conversion"""
        regional_coord = RegionalCoordinate(1, 1, 5, 10)
        abs_coord = CoordinateSystem.regional_to_absolute(regional_coord)
        
        expected_x = (1 * 32 + 5) * 32  # World offset + regional block offset * local size
        expected_y = (1 * 32 + 10) * 32
        
        assert abs_coord.x == expected_x
        assert abs_coord.y == expected_y
    
    def test_local_to_absolute(self):
        """Test local coordinate to absolute conversion"""
        local_coord = LocalCoordinate(1, 1, 5, 10, 15, 20)
        abs_coord = CoordinateSystem.local_to_absolute(local_coord)
        
        expected_x = ((1 * 32 + 5) * 32) + 15
        expected_y = ((1 * 32 + 10) * 32) + 20
        
        assert abs_coord.x == expected_x
        assert abs_coord.y == expected_y
    
    def test_absolute_to_world(self):
        """Test absolute coordinate to world conversion"""
        abs_coord = AbsoluteCoordinate(1024, 1024)  # 1 world sector worth
        world_coord = CoordinateSystem.absolute_to_world(abs_coord)
        
        assert world_coord.sector_x == 1
        assert world_coord.sector_y == 1
    
    def test_absolute_to_regional(self):
        """Test absolute coordinate to regional conversion"""
        abs_coord = AbsoluteCoordinate(1024 + 160, 1024 + 320)  # 1 world sector + some regional blocks
        regional_coord = CoordinateSystem.absolute_to_regional(abs_coord)
        
        assert regional_coord.world_x == 1
        assert regional_coord.world_y == 1
        assert regional_coord.block_x == 5  # 160 / 32 = 5
        assert regional_coord.block_y == 10  # 320 / 32 = 10
    
    def test_absolute_to_local(self):
        """Test absolute coordinate to local conversion"""
        abs_coord = AbsoluteCoordinate(1024 + 160 + 15, 1024 + 320 + 20)
        local_coord = CoordinateSystem.absolute_to_local(abs_coord)
        
        assert local_coord.world_x == 1
        assert local_coord.world_y == 1
        assert local_coord.block_x == 5
        assert local_coord.block_y == 10
        assert local_coord.meter_x == 15
        assert local_coord.meter_y == 20
    
    def test_round_trip_conversions(self):
        """Test that coordinate conversions are reversible"""
        # Test world round trip
        original_world = WorldCoordinate(5, 3)
        abs_coord = CoordinateSystem.world_to_absolute(original_world)
        converted_world = CoordinateSystem.absolute_to_world(abs_coord)
        assert original_world == converted_world
        
        # Test regional round trip
        original_regional = RegionalCoordinate(2, 1, 15, 20)
        abs_coord = CoordinateSystem.regional_to_absolute(original_regional)
        converted_regional = CoordinateSystem.absolute_to_regional(abs_coord)
        assert original_regional == converted_regional
        
        # Test local round trip
        original_local = LocalCoordinate(1, 2, 10, 15, 25, 30)
        abs_coord = CoordinateSystem.local_to_absolute(original_local)
        converted_local = CoordinateSystem.absolute_to_local(abs_coord)
        assert original_local == converted_local


class TestCoordinateBounds:
    """Test coordinate bounds checking"""
    
    def test_get_world_bounds(self):
        """Test world bounds calculation"""
        min_coord, max_coord = CoordinateSystem.get_world_bounds()
        
        assert min_coord.x == 0
        assert min_coord.y == 0
        assert max_coord.x == (128 * 32 * 32) - 1
        assert max_coord.y == (96 * 32 * 32) - 1
    
    def test_get_regional_bounds(self):
        """Test regional bounds calculation"""
        min_coord, max_coord = CoordinateSystem.get_regional_bounds(1, 1)
        
        expected_min_x = 1 * 32 * 32
        expected_min_y = 1 * 32 * 32
        expected_max_x = expected_min_x + (32 * 32) - 1
        expected_max_y = expected_min_y + (32 * 32) - 1
        
        assert min_coord.x == expected_min_x
        assert min_coord.y == expected_min_y
        assert max_coord.x == expected_max_x
        assert max_coord.y == expected_max_y
    
    def test_get_local_bounds(self):
        """Test local bounds calculation"""
        min_coord, max_coord = CoordinateSystem.get_local_bounds(1, 1, 5, 10)
        
        expected_min_x = (1 * 32 + 5) * 32
        expected_min_y = (1 * 32 + 10) * 32
        expected_max_x = expected_min_x + 32 - 1
        expected_max_y = expected_min_y + 32 - 1
        
        assert min_coord.x == expected_min_x
        assert min_coord.y == expected_min_y
        assert max_coord.x == expected_max_x
        assert max_coord.y == expected_max_y
    
    def test_coordinate_validation(self):
        """Test coordinate validation functions"""
        # Valid coordinates
        assert CoordinateSystem.is_valid_world_coordinate(0, 0)
        assert CoordinateSystem.is_valid_world_coordinate(127, 95)
        assert CoordinateSystem.is_valid_regional_coordinate(0, 0, 0, 0)
        assert CoordinateSystem.is_valid_regional_coordinate(127, 95, 31, 31)
        assert CoordinateSystem.is_valid_local_coordinate(0, 0, 0, 0, 0, 0)
        assert CoordinateSystem.is_valid_local_coordinate(127, 95, 31, 31, 31, 31)
        
        # Invalid coordinates
        assert not CoordinateSystem.is_valid_world_coordinate(-1, 0)
        assert not CoordinateSystem.is_valid_world_coordinate(128, 0)
        assert not CoordinateSystem.is_valid_world_coordinate(0, 96)
        assert not CoordinateSystem.is_valid_regional_coordinate(0, 0, -1, 0)
        assert not CoordinateSystem.is_valid_regional_coordinate(0, 0, 32, 0)
        assert not CoordinateSystem.is_valid_local_coordinate(0, 0, 0, 0, -1, 0)
        assert not CoordinateSystem.is_valid_local_coordinate(0, 0, 0, 0, 32, 0)


class TestScaleTransition:
    """Test scale transition utilities"""
    
    def test_transition_duration(self):
        """Test transition duration calculation"""
        # Test defined transitions
        duration = ScaleTransition.get_transition_duration(ViewScale.WORLD, ViewScale.REGIONAL)
        assert duration == 0.4
        
        duration = ScaleTransition.get_transition_duration(ViewScale.REGIONAL, ViewScale.LOCAL)
        assert duration == 0.3
        
        duration = ScaleTransition.get_transition_duration(ViewScale.WORLD, ViewScale.LOCAL)
        assert duration == 0.6
        
        # Test reverse transitions
        duration = ScaleTransition.get_transition_duration(ViewScale.REGIONAL, ViewScale.WORLD)
        assert duration == 0.4
        
        # Test same scale (should use default)
        duration = ScaleTransition.get_transition_duration(ViewScale.WORLD, ViewScale.WORLD)
        assert duration == 0.3
    
    def test_equivalent_position_same_scale(self):
        """Test equivalent position calculation for same scale"""
        x, y = ScaleTransition.calculate_equivalent_position(ViewScale.WORLD, ViewScale.WORLD, 5.0, 3.0)
        assert x == 5.0
        assert y == 3.0


if __name__ == "__main__":
    pytest.main([__file__])
