"""
Tests for the 3D layered world system.

This module tests the layered world generation, camera system, and terrain data
structures for the underground, surface, and mountain layers.
"""

import pytest
from unittest.mock import Mock

from empires.world.layered import (
    WorldLayer, LayeredTerrainData, TerrainData, TerrainType,
    create_terrain_data, get_terrain_config, TERRAIN_CONFIGS
)
from empires.world.layered_generator import LayeredWorldGenerator, create_layered_world_generator
from empires.world.camera_3d import CameraSystem, create_default_camera_3d


class TestWorldLayer:
    """Test the WorldLayer enum."""
    
    def test_layer_values(self):
        """Test that layer enum values are correct."""
        assert WorldLayer.UNDERGROUND.value == 0
        assert WorldLayer.SURFACE.value == 1
        assert WorldLayer.MOUNTAINS.value == 2


class TestTerrainData:
    """Test the TerrainData dataclass."""
    
    def test_terrain_data_creation(self):
        """Test creating terrain data."""
        terrain = TerrainData(
            terrain_type=TerrainType.CAVE_FLOOR,
            char=".",
            fg_color=(120, 100, 80),
            bg_color=(40, 30, 20),
            elevation=0.5,
            is_passable=True,
            is_entrance=False
        )
        
        assert terrain.terrain_type == TerrainType.CAVE_FLOOR
        assert terrain.char == "."
        assert terrain.fg_color == (120, 100, 80)
        assert terrain.bg_color == (40, 30, 20)
        assert terrain.elevation == 0.5
        assert terrain.is_passable is True
        assert terrain.is_entrance is False


class TestLayeredTerrainData:
    """Test the LayeredTerrainData dataclass."""
    
    def test_layered_terrain_creation(self):
        """Test creating layered terrain data."""
        underground = TerrainData(
            terrain_type=TerrainType.CAVE_FLOOR,
            char=".", fg_color=(120, 100, 80), bg_color=(40, 30, 20),
            elevation=0.3
        )
        surface = TerrainData(
            terrain_type=TerrainType.GRASS,
            char=".", fg_color=(50, 120, 50), bg_color=(20, 80, 20),
            elevation=0.5
        )
        mountains = TerrainData(
            terrain_type=TerrainType.MOUNTAIN_PEAK,
            char="▲", fg_color=(180, 160, 140), bg_color=(120, 100, 80),
            elevation=0.8
        )
        
        layered = LayeredTerrainData(
            underground=underground,
            surface=surface,
            mountains=mountains,
            has_cave_entrance=True,
            has_mountain_access=True
        )
        
        assert layered.underground == underground
        assert layered.surface == surface
        assert layered.mountains == mountains
        assert layered.has_cave_entrance is True
        assert layered.has_mountain_access is True


class TestTerrainConfigs:
    """Test terrain configuration system."""
    
    def test_get_terrain_config(self):
        """Test getting terrain configuration."""
        config = get_terrain_config(TerrainType.CAVE_FLOOR)
        
        assert 'chars' in config
        assert 'base_fg' in config
        assert 'base_bg' in config
        assert isinstance(config['chars'], list)
        assert len(config['chars']) > 0
    
    def test_all_layered_terrains_have_configs(self):
        """Test that all layered terrain types have configurations."""
        layered_terrains = [
            TerrainType.CAVE_FLOOR, TerrainType.CAVE_WALL,
            TerrainType.UNDERGROUND_WATER, TerrainType.ORE_VEIN,
            TerrainType.CAVE_ENTRANCE, TerrainType.MOUNTAIN_BASE,
            TerrainType.MOUNTAIN_PEAK, TerrainType.MOUNTAIN_SLOPE,
            TerrainType.MOUNTAIN_CLIFF, TerrainType.SNOW
        ]
        
        for terrain_type in layered_terrains:
            config = get_terrain_config(terrain_type)
            assert config is not None
            assert 'chars' in config
            assert 'base_fg' in config
            assert 'base_bg' in config
    
    def test_create_terrain_data(self):
        """Test creating terrain data with variations."""
        terrain = create_terrain_data(
            TerrainType.CAVE_FLOOR, 10, 20, 0.5
        )
        
        assert terrain.terrain_type == TerrainType.CAVE_FLOOR
        assert terrain.elevation == 0.5
        assert terrain.is_passable is True
        assert terrain.is_entrance is False
        assert len(terrain.char) == 1
        assert len(terrain.fg_color) == 3
        assert len(terrain.bg_color) == 3


class TestCameraSystem:
    """Test the 3D camera system."""
    
    def test_camera_creation(self):
        """Test creating a camera system."""
        camera = CameraSystem()
        
        assert camera.current_layer == WorldLayer.SURFACE
        assert camera.world_x == 0
        assert camera.world_y == 0
        assert camera.is_transitioning is False
    
    def test_layer_change(self):
        """Test changing layers."""
        camera = CameraSystem()
        
        # Test changing to different layer
        result = camera.change_layer(WorldLayer.UNDERGROUND)
        assert result is True
        assert camera.current_layer == WorldLayer.UNDERGROUND
        assert camera.is_transitioning is True
        
        # Test changing to same layer
        result = camera.change_layer(WorldLayer.UNDERGROUND)
        assert result is False
    
    def test_can_change_layer(self):
        """Test layer transition validation (now allows free switching)."""
        camera = CameraSystem()

        # Create mock layered terrain data
        layered_data = LayeredTerrainData(
            underground=Mock(),
            surface=Mock(),
            mountains=Mock(),
            has_cave_entrance=True,
            has_mountain_access=True
        )

        # Test that all transitions are now allowed (free layer switching)
        assert camera.can_change_layer(WorldLayer.UNDERGROUND, layered_data) is True
        assert camera.can_change_layer(WorldLayer.MOUNTAINS, layered_data) is True
        assert camera.can_change_layer(WorldLayer.SURFACE, layered_data) is True

        # Test that transitions are still allowed even without terrain entrances
        layered_data.has_cave_entrance = False
        layered_data.has_mountain_access = False
        assert camera.can_change_layer(WorldLayer.UNDERGROUND, layered_data) is True
        assert camera.can_change_layer(WorldLayer.MOUNTAINS, layered_data) is True
        assert camera.can_change_layer(WorldLayer.SURFACE, layered_data) is True

        # Test that transitions work without terrain data (optional parameter)
        assert camera.can_change_layer(WorldLayer.UNDERGROUND) is True
        assert camera.can_change_layer(WorldLayer.MOUNTAINS) is True
        assert camera.can_change_layer(WorldLayer.SURFACE) is True
    
    def test_position_management(self):
        """Test camera position management."""
        camera = CameraSystem()
        
        camera.set_position(100, 200)
        assert camera.get_position() == (100, 200)
    
    def test_create_default_camera(self):
        """Test creating default camera."""
        camera = create_default_camera_3d()
        
        assert isinstance(camera, CameraSystem)
        assert camera.current_layer == WorldLayer.SURFACE


class TestLayeredWorldGenerator:
    """Test the layered world generator."""
    
    def test_generator_creation(self):
        """Test creating a layered world generator."""
        generator = LayeredWorldGenerator(seed=12345)
        
        assert generator.seed == 12345
        assert hasattr(generator, 'noise_elevation')
        assert hasattr(generator, 'noise_caves')
        assert hasattr(generator, 'noise_mountains')
        assert hasattr(generator, 'noise_surface')
        assert hasattr(generator, 'noise_detail')
    
    def test_generate_layered_chunk(self):
        """Test generating a layered chunk."""
        generator = LayeredWorldGenerator(seed=12345)
        
        chunk_data = generator.generate_layered_chunk(0, 0, chunk_size=4)
        
        # Check that we got data for all positions
        assert len(chunk_data) == 16  # 4x4 chunk
        
        # Check that each position has layered terrain data
        for local_x in range(4):
            for local_y in range(4):
                assert (local_x, local_y) in chunk_data
                layered_terrain = chunk_data[(local_x, local_y)]
                
                assert isinstance(layered_terrain, LayeredTerrainData)
                assert isinstance(layered_terrain.underground, TerrainData)
                assert isinstance(layered_terrain.surface, TerrainData)
                # Mountains can be None
                assert layered_terrain.mountains is None or isinstance(layered_terrain.mountains, TerrainData)
                assert isinstance(layered_terrain.has_cave_entrance, bool)
                assert isinstance(layered_terrain.has_mountain_access, bool)
    
    def test_create_layered_world_generator(self):
        """Test creating layered world generator with factory function."""
        generator = create_layered_world_generator(seed=54321)
        
        assert isinstance(generator, LayeredWorldGenerator)
        assert generator.seed == 54321
        
        # Test with no seed
        generator2 = create_layered_world_generator()
        assert isinstance(generator2, LayeredWorldGenerator)
        assert generator2.seed is not None


class TestLayeredWorldIntegration:
    """Integration tests for the layered world system."""
    
    def test_camera_rendering_integration(self):
        """Test camera rendering with layered terrain data."""
        camera = CameraSystem()
        generator = LayeredWorldGenerator(seed=12345)
        
        # Generate some test data
        chunk_data = generator.generate_layered_chunk(0, 0, chunk_size=2)
        layered_terrain = chunk_data[(0, 0)]
        
        # Test rendering from different layers
        camera.change_layer(WorldLayer.SURFACE)
        surface_render = camera.get_render_data(layered_terrain)
        assert isinstance(surface_render, TerrainData)
        
        camera.change_layer(WorldLayer.UNDERGROUND)
        underground_render = camera.get_render_data(layered_terrain)
        assert isinstance(underground_render, TerrainData)
        
        camera.change_layer(WorldLayer.MOUNTAINS)
        mountain_render = camera.get_render_data(layered_terrain)
        assert isinstance(mountain_render, TerrainData)
    
    def test_deterministic_generation(self):
        """Test that generation is deterministic with same seed."""
        generator1 = LayeredWorldGenerator(seed=12345)
        generator2 = LayeredWorldGenerator(seed=12345)
        
        chunk1 = generator1.generate_layered_chunk(0, 0, chunk_size=2)
        chunk2 = generator2.generate_layered_chunk(0, 0, chunk_size=2)
        
        # Should generate identical terrain
        for pos in chunk1:
            terrain1 = chunk1[pos]
            terrain2 = chunk2[pos]
            
            assert terrain1.underground.terrain_type == terrain2.underground.terrain_type
            assert terrain1.surface.terrain_type == terrain2.surface.terrain_type
            assert terrain1.has_cave_entrance == terrain2.has_cave_entrance
            assert terrain1.has_mountain_access == terrain2.has_mountain_access
