"""
Tests for the chunk management system.
"""

import pytest

from src.empires.world.chunks import (
    ChunkCoordinate,
    Chunk,
    ChunkManager
)
from src.empires.world.terrain import TerrainType


class TestChunkCoordinate:
    """Test the ChunkCoordinate class."""
    
    def test_creation(self):
        """Test creating chunk coordinates."""
        coord = ChunkCoordinate(5, -3)
        assert coord.x == 5
        assert coord.y == -3
    
    def test_equality(self):
        """Test chunk coordinate equality."""
        coord1 = ChunkCoordinate(1, 2)
        coord2 = ChunkCoordinate(1, 2)
        coord3 = ChunkCoordinate(2, 1)
        
        assert coord1 == coord2
        assert coord1 != coord3
        assert coord2 != coord3
    
    def test_hashable(self):
        """Test that chunk coordinates can be used as dictionary keys."""
        coord1 = ChunkCoordinate(1, 2)
        coord2 = ChunkCoordinate(1, 2)
        coord3 = ChunkCoordinate(2, 1)
        
        # Test in dictionary
        chunk_dict = {coord1: "chunk1", coord3: "chunk3"}
        assert chunk_dict[coord2] == "chunk1"  # Should find coord1's value
        
        # Test in set
        coord_set = {coord1, coord2, coord3}
        assert len(coord_set) == 2  # coord1 and coord2 should be same
    
    def test_string_representation(self):
        """Test string representation of chunk coordinates."""
        coord = ChunkCoordinate(10, -5)
        repr_str = repr(coord)
        assert "10" in repr_str
        assert "-5" in repr_str
        assert "ChunkCoordinate" in repr_str


class TestChunk:
    """Test the Chunk class."""
    
    def test_creation(self):
        """Test creating a chunk."""
        coord = ChunkCoordinate(0, 0)
        chunk = Chunk(coord, 16)
        
        assert chunk.coordinate == coord
        assert chunk.size == 16
        assert chunk.terrain_data == []
        assert chunk.is_generated is False
        assert chunk.last_accessed == 0
    
    def test_set_terrain_data(self):
        """Test setting terrain data."""
        coord = ChunkCoordinate(0, 0)
        chunk = Chunk(coord, 4)
        
        # Create 4x4 terrain data
        terrain_data = [
            [TerrainType.GRASS, TerrainType.GRASS, TerrainType.SAND, TerrainType.DEEP_WATER],
            [TerrainType.GRASS, TerrainType.FOREST, TerrainType.SAND, TerrainType.DEEP_WATER],
            [TerrainType.HILLS, TerrainType.FOREST, TerrainType.SAND, TerrainType.DEEP_WATER],
            [TerrainType.HILLS, TerrainType.MOUNTAINS, TerrainType.SAND, TerrainType.DEEP_WATER]
        ]
        
        chunk.set_terrain_data(terrain_data)
        
        assert chunk.terrain_data == terrain_data
        assert chunk.is_generated is True
    
    def test_set_terrain_data_wrong_size(self):
        """Test that setting wrong-sized terrain data raises error."""
        coord = ChunkCoordinate(0, 0)
        chunk = Chunk(coord, 4)
        
        # Wrong size data
        wrong_data = [[TerrainType.GRASS, TerrainType.GRASS]]
        
        with pytest.raises(ValueError):
            chunk.set_terrain_data(wrong_data)
    
    def test_get_terrain_at(self):
        """Test getting terrain at local coordinates."""
        coord = ChunkCoordinate(0, 0)
        chunk = Chunk(coord, 2)
        
        terrain_data = [
            [TerrainType.GRASS, TerrainType.SAND],
            [TerrainType.FOREST, TerrainType.DEEP_WATER]
        ]
        chunk.set_terrain_data(terrain_data)
        
        assert chunk.get_terrain_at(0, 0) == TerrainType.GRASS
        assert chunk.get_terrain_at(1, 0) == TerrainType.SAND
        assert chunk.get_terrain_at(0, 1) == TerrainType.FOREST
        assert chunk.get_terrain_at(1, 1) == TerrainType.DEEP_WATER
    
    def test_get_terrain_at_not_generated(self):
        """Test that getting terrain from ungenerated chunk raises error."""
        coord = ChunkCoordinate(0, 0)
        chunk = Chunk(coord, 4)
        
        with pytest.raises(RuntimeError):
            chunk.get_terrain_at(0, 0)
    
    def test_get_terrain_at_out_of_bounds(self):
        """Test that out-of-bounds coordinates raise error."""
        coord = ChunkCoordinate(0, 0)
        chunk = Chunk(coord, 2)
        
        terrain_data = [
            [TerrainType.GRASS, TerrainType.SAND],
            [TerrainType.FOREST, TerrainType.DEEP_WATER]
        ]
        chunk.set_terrain_data(terrain_data)
        
        with pytest.raises(ValueError):
            chunk.get_terrain_at(2, 0)  # Out of bounds
        
        with pytest.raises(ValueError):
            chunk.get_terrain_at(0, 2)  # Out of bounds
        
        with pytest.raises(ValueError):
            chunk.get_terrain_at(-1, 0)  # Negative coordinates
    
    def test_world_to_local(self):
        """Test converting world coordinates to local coordinates."""
        coord = ChunkCoordinate(2, -1)  # Chunk at world position (64, -32) with size 32
        chunk = Chunk(coord, 32)
        
        # Test various world coordinates
        local_x, local_y = chunk.world_to_local(64, -32)  # Top-left of chunk
        assert local_x == 0
        assert local_y == 0
        
        local_x, local_y = chunk.world_to_local(95, -1)  # Bottom-right of chunk
        assert local_x == 31
        assert local_y == 31
        
        local_x, local_y = chunk.world_to_local(80, -16)  # Middle of chunk
        assert local_x == 16
        assert local_y == 16


class TestChunkManager:
    """Test the ChunkManager class."""
    
    def test_creation(self):
        """Test creating a chunk manager."""
        manager = ChunkManager(chunk_size=16, cache_size=32)
        
        assert manager.chunk_size == 16
        assert manager.cache_size == 32
        assert len(manager._chunks) == 0
        assert len(manager._access_order) == 0
    
    def test_world_to_chunk_coordinate(self):
        """Test converting world coordinates to chunk coordinates."""
        manager = ChunkManager(chunk_size=32)
        
        # Test positive coordinates
        coord = manager.world_to_chunk_coordinate(0, 0)
        assert coord == ChunkCoordinate(0, 0)
        
        coord = manager.world_to_chunk_coordinate(31, 31)
        assert coord == ChunkCoordinate(0, 0)
        
        coord = manager.world_to_chunk_coordinate(32, 32)
        assert coord == ChunkCoordinate(1, 1)
        
        coord = manager.world_to_chunk_coordinate(63, 63)
        assert coord == ChunkCoordinate(1, 1)
        
        # Test negative coordinates
        # -1 // 32 = -1, but since -1 % 32 != 0, we subtract 1 to get -2
        coord = manager.world_to_chunk_coordinate(-1, -1)
        assert coord == ChunkCoordinate(-2, -2)

        # -32 // 32 = -1, and -32 % 32 == 0, so no adjustment needed
        coord = manager.world_to_chunk_coordinate(-32, -32)
        assert coord == ChunkCoordinate(-1, -1)

        # -33 // 32 = -2, and -33 % 32 != 0, so subtract 1 to get -3
        coord = manager.world_to_chunk_coordinate(-33, -33)
        assert coord == ChunkCoordinate(-3, -3)
    
    def test_add_and_get_chunk(self):
        """Test adding and retrieving chunks."""
        manager = ChunkManager(chunk_size=16, cache_size=4)
        
        coord = ChunkCoordinate(1, 1)
        chunk = Chunk(coord, 16)
        
        # Initially chunk should not exist
        assert manager.get_chunk(coord) is None
        
        # Add chunk
        manager.add_chunk(chunk)
        
        # Now chunk should exist
        retrieved_chunk = manager.get_chunk(coord)
        assert retrieved_chunk is chunk
        assert retrieved_chunk.coordinate == coord
    
    def test_remove_chunk(self):
        """Test removing chunks."""
        manager = ChunkManager(chunk_size=16, cache_size=4)
        
        coord = ChunkCoordinate(1, 1)
        chunk = Chunk(coord, 16)
        
        # Add chunk
        manager.add_chunk(chunk)
        assert manager.get_chunk(coord) is not None
        
        # Remove chunk
        result = manager.remove_chunk(coord)
        assert result is True
        assert manager.get_chunk(coord) is None
        
        # Try to remove non-existent chunk
        result = manager.remove_chunk(coord)
        assert result is False
    
    def test_cache_eviction(self):
        """Test that LRU cache eviction works correctly."""
        manager = ChunkManager(chunk_size=16, cache_size=2)
        
        # Add chunks up to cache limit
        coord1 = ChunkCoordinate(0, 0)
        coord2 = ChunkCoordinate(1, 0)
        chunk1 = Chunk(coord1, 16)
        chunk2 = Chunk(coord2, 16)
        
        manager.add_chunk(chunk1)
        manager.add_chunk(chunk2)
        
        # Both should be in cache
        assert manager.get_chunk(coord1) is not None
        assert manager.get_chunk(coord2) is not None
        
        # Add third chunk, should evict least recently used
        coord3 = ChunkCoordinate(2, 0)
        chunk3 = Chunk(coord3, 16)
        manager.add_chunk(chunk3)
        
        # First chunk should be evicted, others should remain
        assert manager.get_chunk(coord1) is None
        assert manager.get_chunk(coord2) is not None
        assert manager.get_chunk(coord3) is not None
    
    def test_get_chunks_in_radius(self):
        """Test getting chunks within a radius."""
        manager = ChunkManager()
        
        center = ChunkCoordinate(0, 0)
        
        # Test radius 0 (just center)
        chunks = manager.get_chunks_in_radius(center, 0)
        assert chunks == {ChunkCoordinate(0, 0)}
        
        # Test radius 1
        chunks = manager.get_chunks_in_radius(center, 1)
        expected = {
            ChunkCoordinate(-1, -1), ChunkCoordinate(0, -1), ChunkCoordinate(1, -1),
            ChunkCoordinate(-1, 0), ChunkCoordinate(0, 0), ChunkCoordinate(1, 0),
            ChunkCoordinate(-1, 1), ChunkCoordinate(0, 1), ChunkCoordinate(1, 1)
        }
        assert chunks == expected
        
        # Test radius 2
        chunks = manager.get_chunks_in_radius(center, 2)
        assert len(chunks) == 25  # 5x5 grid
        assert ChunkCoordinate(-2, -2) in chunks
        assert ChunkCoordinate(2, 2) in chunks
        assert ChunkCoordinate(0, 0) in chunks
    
    def test_get_loaded_chunks(self):
        """Test getting all loaded chunks."""
        manager = ChunkManager()
        
        # Initially no chunks loaded
        assert manager.get_loaded_chunks() == set()
        
        # Add some chunks
        coords = [ChunkCoordinate(0, 0), ChunkCoordinate(1, 1), ChunkCoordinate(-1, 0)]
        for coord in coords:
            chunk = Chunk(coord, 16)
            manager.add_chunk(chunk)
        
        loaded = manager.get_loaded_chunks()
        assert loaded == set(coords)
    
    def test_get_cache_info(self):
        """Test getting cache information."""
        manager = ChunkManager(chunk_size=16, cache_size=4)
        
        info = manager.get_cache_info()
        assert info['loaded_chunks'] == 0
        assert info['cache_size'] == 4
        assert info['cache_usage'] == 0.0
        
        # Add some chunks
        for i in range(2):
            coord = ChunkCoordinate(i, 0)
            chunk = Chunk(coord, 16)
            manager.add_chunk(chunk)
        
        info = manager.get_cache_info()
        assert info['loaded_chunks'] == 2
        assert info['cache_size'] == 4
        assert info['cache_usage'] == 0.5


if __name__ == "__main__":
    pytest.main([__file__])
