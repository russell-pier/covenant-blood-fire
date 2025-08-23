"""
Integration tests for the 3D layered world system with the main world generator.

This module tests the integration of the layered world system with the existing
world generation infrastructure, including chunk management and rendering.
"""

import pytest
from unittest.mock import Mock

from covenant.world.generator import WorldGenerator
from covenant.world.layered import WorldLayer, LayeredTerrainData, TerrainType
from covenant.world.chunks import ChunkCoordinate


class TestWorldGeneratorLayeredIntegration:
    """Test integration of layered system with WorldGenerator."""
    
    def test_world_generator_with_layered_system(self):
        """Test creating world generator with layered system enabled."""
        generator = WorldGenerator(
            chunk_size=4,
            cache_size=8,
            seed=12345,
            use_layered_system=True
        )
        
        assert generator.use_layered_system is True
        assert generator.layered_generator is not None
        assert generator.camera_3d is not None
    
    def test_world_generator_without_layered_system(self):
        """Test creating world generator with layered system disabled."""
        generator = WorldGenerator(
            chunk_size=4,
            cache_size=8,
            seed=12345,
            use_layered_system=False
        )
        
        assert generator.use_layered_system is False
        assert generator.layered_generator is None
        assert generator.camera_3d is None
    
    def test_get_layered_terrain_at(self):
        """Test getting layered terrain data at world coordinates."""
        generator = WorldGenerator(
            chunk_size=4,
            cache_size=8,
            seed=12345,
            use_layered_system=True
        )
        
        # Test getting layered terrain data
        layered_data = generator.get_layered_terrain_at(0, 0)
        
        assert layered_data is not None
        assert isinstance(layered_data, LayeredTerrainData)
        assert layered_data.underground is not None
        assert layered_data.surface is not None
        # Mountains can be None depending on elevation
    
    def test_get_layered_terrain_disabled(self):
        """Test getting layered terrain when system is disabled."""
        generator = WorldGenerator(
            chunk_size=4,
            cache_size=8,
            seed=12345,
            use_layered_system=False
        )
        
        layered_data = generator.get_layered_terrain_at(0, 0)
        assert layered_data is None
    
    def test_get_rendered_terrain_at(self):
        """Test getting rendered terrain based on current layer."""
        generator = WorldGenerator(
            chunk_size=4,
            cache_size=8,
            seed=12345,
            use_layered_system=True
        )
        
        # Test getting rendered terrain
        terrain_type = generator.get_rendered_terrain_at(0, 0)
        assert isinstance(terrain_type, TerrainType)
        
        # Test changing layer and getting different terrain
        generator.change_layer(WorldLayer.UNDERGROUND)
        underground_terrain = generator.get_rendered_terrain_at(0, 0)
        assert isinstance(underground_terrain, TerrainType)
    
    def test_layer_transitions(self):
        """Test layer transition functionality."""
        generator = WorldGenerator(
            chunk_size=4,
            cache_size=8,
            seed=12345,
            use_layered_system=True
        )
        
        # Start on surface
        assert generator.get_current_layer() == WorldLayer.SURFACE
        
        # Try to change layers (may or may not succeed depending on terrain)
        result = generator.change_layer(WorldLayer.UNDERGROUND)
        assert isinstance(result, bool)
        
        result = generator.change_layer(WorldLayer.MOUNTAINS)
        assert isinstance(result, bool)
        
        # Can always return to surface
        result = generator.change_layer(WorldLayer.SURFACE)
        assert result is True or generator.get_current_layer() == WorldLayer.SURFACE
    
    def test_camera_position_updates(self):
        """Test that camera position updates correctly."""
        generator = WorldGenerator(
            chunk_size=4,
            cache_size=8,
            seed=12345,
            use_layered_system=True
        )
        
        # Update camera position
        generator.update_camera_position(100, 200)
        
        # Check that 3D camera position was updated
        camera_pos = generator.camera_3d.get_position()
        assert camera_pos == (100, 200)
    
    def test_chunk_generation_with_layered_data(self):
        """Test that chunks are generated with layered data."""
        generator = WorldGenerator(
            chunk_size=4,
            cache_size=8,
            seed=12345,
            use_layered_system=True
        )
        
        # Force chunk generation by getting terrain
        terrain_type = generator.get_terrain_at(0, 0)
        assert isinstance(terrain_type, TerrainType)
        
        # Check that chunk was created with layered data
        chunk_coord = ChunkCoordinate(0, 0)
        chunk = generator.chunk_manager.get_chunk(chunk_coord)
        
        assert chunk is not None
        assert hasattr(chunk, 'layered_data')
        assert len(chunk.layered_data) > 0
        
        # Check that layered data is properly structured
        layered_terrain = chunk.get_layered_data_at(0, 0)
        assert layered_terrain is not None
        assert isinstance(layered_terrain, LayeredTerrainData)


class TestLayeredChunkManagement:
    """Test chunk management with layered terrain data."""
    
    def test_chunk_layered_data_storage(self):
        """Test storing and retrieving layered data in chunks."""
        generator = WorldGenerator(
            chunk_size=2,
            cache_size=4,
            seed=12345,
            use_layered_system=True
        )
        
        # Generate a chunk
        chunk_coord = ChunkCoordinate(0, 0)
        chunk = generator._generate_chunk(chunk_coord)
        
        # Check that layered data was set
        assert hasattr(chunk, 'layered_data')
        assert len(chunk.layered_data) == 2  # chunk_size
        assert len(chunk.layered_data[0]) == 2  # chunk_size
        
        # Check that we can retrieve layered data
        layered_terrain = chunk.get_layered_data_at(0, 0)
        assert layered_terrain is not None
        assert isinstance(layered_terrain, LayeredTerrainData)
        
        layered_terrain = chunk.get_layered_data_at(1, 1)
        assert layered_terrain is not None
        assert isinstance(layered_terrain, LayeredTerrainData)
    
    def test_chunk_layered_data_bounds_checking(self):
        """Test bounds checking for layered data access."""
        generator = WorldGenerator(
            chunk_size=2,
            cache_size=4,
            seed=12345,
            use_layered_system=True
        )
        
        chunk_coord = ChunkCoordinate(0, 0)
        chunk = generator._generate_chunk(chunk_coord)
        
        # Test valid coordinates
        assert chunk.get_layered_data_at(0, 0) is not None
        assert chunk.get_layered_data_at(1, 1) is not None
        
        # Test invalid coordinates
        assert chunk.get_layered_data_at(-1, 0) is None
        assert chunk.get_layered_data_at(0, -1) is None
        assert chunk.get_layered_data_at(2, 0) is None
        assert chunk.get_layered_data_at(0, 2) is None


class TestLayeredWorldPerformance:
    """Test performance aspects of the layered world system."""
    
    def test_chunk_generation_performance(self):
        """Test that chunk generation with layered system is reasonably fast."""
        import time
        
        generator = WorldGenerator(
            chunk_size=32,
            cache_size=16,
            seed=12345,
            use_layered_system=True
        )
        
        start_time = time.time()
        
        # Generate several chunks
        for x in range(3):
            for y in range(3):
                chunk_coord = ChunkCoordinate(x, y)
                chunk = generator._generate_chunk(chunk_coord)
                assert chunk is not None
        
        end_time = time.time()
        generation_time = end_time - start_time
        
        # Should generate 9 32x32 chunks in reasonable time (less than 5 seconds)
        assert generation_time < 5.0, f"Chunk generation took too long: {generation_time:.2f}s"
    
    def test_layered_terrain_access_performance(self):
        """Test that layered terrain access is fast."""
        import time
        
        generator = WorldGenerator(
            chunk_size=32,
            cache_size=16,
            seed=12345,
            use_layered_system=True
        )
        
        # Pre-generate a chunk
        generator.get_terrain_at(0, 0)
        
        start_time = time.time()
        
        # Access layered terrain data many times
        for i in range(1000):
            x = i % 32
            y = (i // 32) % 32
            layered_data = generator.get_layered_terrain_at(x, y)
            assert layered_data is not None
        
        end_time = time.time()
        access_time = end_time - start_time
        
        # Should access 1000 terrain tiles quickly (less than 1 second)
        assert access_time < 1.0, f"Terrain access took too long: {access_time:.2f}s"


class TestLayeredWorldConsistency:
    """Test consistency of the layered world system."""
    
    def test_terrain_consistency_across_layers(self):
        """Test that terrain is consistent across different layer views."""
        generator = WorldGenerator(
            chunk_size=4,
            cache_size=8,
            seed=12345,
            use_layered_system=True
        )
        
        # Get layered terrain data
        layered_data = generator.get_layered_terrain_at(0, 0)
        assert layered_data is not None
        
        # Test that each layer has valid terrain
        assert layered_data.underground.terrain_type in [
            TerrainType.CAVE_FLOOR, TerrainType.CAVE_WALL,
            TerrainType.UNDERGROUND_WATER, TerrainType.ORE_VEIN
        ]
        
        # Surface should have surface-appropriate terrain
        surface_terrains = [
            TerrainType.GRASS, TerrainType.LIGHT_GRASS, TerrainType.DARK_GRASS,
            TerrainType.FOREST, TerrainType.DEEP_WATER, TerrainType.SHALLOW_WATER,
            TerrainType.SAND, TerrainType.HILLS, TerrainType.MOUNTAINS
        ]
        assert layered_data.surface.terrain_type in surface_terrains
        
        # Mountains can be None or mountain terrain
        if layered_data.mountains is not None:
            mountain_terrains = [
                TerrainType.MOUNTAIN_PEAK, TerrainType.MOUNTAIN_SLOPE,
                TerrainType.MOUNTAIN_CLIFF, TerrainType.SNOW
            ]
            assert layered_data.mountains.terrain_type in mountain_terrains
    
    def test_entrance_consistency(self):
        """Test that entrance flags are consistent with terrain."""
        generator = WorldGenerator(
            chunk_size=8,
            cache_size=16,
            seed=12345,
            use_layered_system=True
        )
        
        # Check multiple positions for entrance consistency
        for x in range(8):
            for y in range(8):
                layered_data = generator.get_layered_terrain_at(x, y)
                assert layered_data is not None
                
                # If has_mountain_access is True, mountains should exist
                if layered_data.has_mountain_access:
                    assert layered_data.mountains is not None
                
                # Cave entrances should be logical (not underwater)
                if layered_data.has_cave_entrance:
                    assert layered_data.surface.terrain_type not in [
                        TerrainType.DEEP_WATER, TerrainType.SHALLOW_WATER
                    ]
