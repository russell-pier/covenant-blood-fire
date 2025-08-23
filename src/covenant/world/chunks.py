"""
Chunk management system for efficient world generation and memory usage.

This module provides a chunk-based approach to world management, allowing
for infinite world generation while maintaining reasonable memory usage.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple, Union, TYPE_CHECKING

from .terrain import TerrainType

if TYPE_CHECKING:
    from .environmental import EnvironmentalData
    from .layered import LayeredTerrainData


@dataclass
class ChunkCoordinate:
    """Represents a chunk coordinate in the world."""
    
    x: int
    y: int
    
    def __hash__(self) -> int:
        """Make ChunkCoordinate hashable for use in dictionaries."""
        return hash((self.x, self.y))
    
    def __eq__(self, other) -> bool:
        """Check equality with another ChunkCoordinate."""
        if not isinstance(other, ChunkCoordinate):
            return False
        return self.x == other.x and self.y == other.y
    
    def __repr__(self) -> str:
        """String representation of the chunk coordinate."""
        return f"ChunkCoordinate({self.x}, {self.y})"


class Chunk:
    """
    Represents a single chunk of the world containing terrain data.
    
    A chunk is a square section of the world with a fixed size,
    containing terrain information for efficient loading and rendering.
    """
    
    def __init__(self, coordinate: ChunkCoordinate, size: int):
        """
        Initialize a new chunk.

        Args:
            coordinate: The chunk's coordinate in chunk space
            size: The size of the chunk (width and height in tiles)
        """
        self.coordinate = coordinate
        self.size = size
        self.terrain_data: List[List[TerrainType]] = []
        self.environmental_data: List[List["EnvironmentalData"]] = []
        self.organic_data: List[List] = []  # Will store OrganicTerrainData
        self.layered_data: List[List["LayeredTerrainData"]] = []  # 3D layered terrain data
        self.is_generated = False
        self.last_accessed = 0  # For LRU cache management
    
    def set_terrain_data(self, terrain_data: List[List[TerrainType]]) -> None:
        """
        Set the terrain data for this chunk.
        
        Args:
            terrain_data: 2D list of TerrainType values
        """
        if len(terrain_data) != self.size or len(terrain_data[0]) != self.size:
            raise ValueError(f"Terrain data must be {self.size}x{self.size}")
        
        self.terrain_data = terrain_data
        self.is_generated = True
    
    def get_terrain_at(self, local_x: int, local_y: int) -> TerrainType:
        """
        Get the terrain type at a local coordinate within the chunk.
        
        Args:
            local_x: X coordinate within the chunk (0 to size-1)
            local_y: Y coordinate within the chunk (0 to size-1)
            
        Returns:
            TerrainType at the specified local coordinate
        """
        if not self.is_generated:
            raise RuntimeError("Chunk has not been generated yet")
        
        if not (0 <= local_x < self.size and 0 <= local_y < self.size):
            raise ValueError(f"Coordinates ({local_x}, {local_y}) out of chunk bounds")
        
        return self.terrain_data[local_y][local_x]

    def set_environmental_data(self, environmental_data: List[List["EnvironmentalData"]]) -> None:
        """
        Set the environmental data for this chunk.

        Args:
            environmental_data: 2D list of EnvironmentalData values
        """
        if len(environmental_data) != self.size or len(environmental_data[0]) != self.size:
            raise ValueError(f"Environmental data must be {self.size}x{self.size}")

        self.environmental_data = environmental_data

    def get_environmental_data_at(self, local_x: int, local_y: int) -> "EnvironmentalData":
        """
        Get the environmental data at a local coordinate within the chunk.

        Args:
            local_x: X coordinate within the chunk (0 to size-1)
            local_y: Y coordinate within the chunk (0 to size-1)

        Returns:
            EnvironmentalData at the specified local coordinate
        """
        if not self.environmental_data:
            raise RuntimeError("Chunk environmental data has not been set")

        if not (0 <= local_x < self.size and 0 <= local_y < self.size):
            raise ValueError(f"Coordinates ({local_x}, {local_y}) out of chunk bounds")

        return self.environmental_data[local_y][local_x]

    def set_organic_data(self, organic_data: List[List]) -> None:
        """
        Set the organic terrain data for this chunk.

        Args:
            organic_data: 2D list of OrganicTerrainData values
        """
        if len(organic_data) != self.size or len(organic_data[0]) != self.size:
            raise ValueError(f"Organic data must be {self.size}x{self.size}")

        self.organic_data = organic_data

    def get_organic_data_at(self, local_x: int, local_y: int):
        """
        Get the organic terrain data at a local coordinate within the chunk.

        Args:
            local_x: X coordinate within the chunk (0 to size-1)
            local_y: Y coordinate within the chunk (0 to size-1)

        Returns:
            OrganicTerrainData at the specified local coordinate
        """
        if not self.organic_data:
            raise RuntimeError("Chunk organic data has not been set")

        if not (0 <= local_x < self.size and 0 <= local_y < self.size):
            raise ValueError(f"Coordinates ({local_x}, {local_y}) out of chunk bounds")

        return self.organic_data[local_y][local_x]

    def set_layered_data(self, layered_data: List[List["LayeredTerrainData"]]) -> None:
        """
        Set the layered terrain data for this chunk.

        Args:
            layered_data: 2D list of LayeredTerrainData
        """
        if len(layered_data) != self.size or len(layered_data[0]) != self.size:
            raise ValueError(f"Layered data must be {self.size}x{self.size}")

        self.layered_data = layered_data

    def get_layered_data_at(self, local_x: int, local_y: int) -> Optional["LayeredTerrainData"]:
        """
        Get layered terrain data at local coordinates.

        Args:
            local_x: Local X coordinate within chunk
            local_y: Local Y coordinate within chunk

        Returns:
            LayeredTerrainData at the specified coordinates, or None if not available
        """
        if not self.layered_data or not (0 <= local_x < self.size and 0 <= local_y < self.size):
            return None

        return self.layered_data[local_y][local_x]

    def world_to_local(self, world_x: int, world_y: int) -> Tuple[int, int]:
        """
        Convert world coordinates to local chunk coordinates.

        Args:
            world_x: World X coordinate
            world_y: World Y coordinate

        Returns:
            Tuple of (local_x, local_y) coordinates
        """
        chunk_world_x = self.coordinate.x * self.size
        chunk_world_y = self.coordinate.y * self.size

        local_x = world_x - chunk_world_x
        local_y = world_y - chunk_world_y

        # Ensure coordinates are within bounds
        local_x = max(0, min(self.size - 1, local_x))
        local_y = max(0, min(self.size - 1, local_y))

        return local_x, local_y


class ChunkManager:
    """
    Manages chunk loading, unloading, and caching for efficient world management.
    
    This class implements an LRU cache for chunks and handles the loading
    and unloading of chunks based on camera position.
    """
    
    def __init__(self, chunk_size: int = 32, cache_size: int = 64):
        """
        Initialize the chunk manager.
        
        Args:
            chunk_size: Size of each chunk in tiles
            cache_size: Maximum number of chunks to keep in memory
        """
        self.chunk_size = chunk_size
        self.cache_size = cache_size
        self._chunks: Dict[ChunkCoordinate, Chunk] = {}
        self._access_order: List[ChunkCoordinate] = []
        self._access_counter = 0
    
    def world_to_chunk_coordinate(self, world_x: int, world_y: int) -> ChunkCoordinate:
        """
        Convert world coordinates to chunk coordinates.
        
        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            
        Returns:
            ChunkCoordinate containing the world position
        """
        # Use floor division to handle negative coordinates correctly
        import math
        chunk_x = math.floor(world_x / self.chunk_size)
        chunk_y = math.floor(world_y / self.chunk_size)
        
        return ChunkCoordinate(chunk_x, chunk_y)
    
    def get_chunk(self, coordinate: ChunkCoordinate) -> Optional[Chunk]:
        """
        Get a chunk by its coordinate, if it exists in the cache.
        
        Args:
            coordinate: The chunk coordinate to retrieve
            
        Returns:
            Chunk if it exists in cache, None otherwise
        """
        if coordinate in self._chunks:
            self._update_access(coordinate)
            return self._chunks[coordinate]
        return None
    
    def add_chunk(self, chunk: Chunk) -> None:
        """
        Add a chunk to the cache, potentially evicting old chunks.
        
        Args:
            chunk: The chunk to add to the cache
        """
        coordinate = chunk.coordinate
        
        # If chunk already exists, update it
        if coordinate in self._chunks:
            self._chunks[coordinate] = chunk
            self._update_access(coordinate)
            return
        
        # If cache is full, evict least recently used chunk
        if len(self._chunks) >= self.cache_size:
            self._evict_lru_chunk()
        
        # Add the new chunk
        self._chunks[coordinate] = chunk
        self._access_order.append(coordinate)
        chunk.last_accessed = self._access_counter
        self._access_counter += 1
    
    def remove_chunk(self, coordinate: ChunkCoordinate) -> bool:
        """
        Remove a chunk from the cache.
        
        Args:
            coordinate: The chunk coordinate to remove
            
        Returns:
            True if chunk was removed, False if it wasn't in cache
        """
        if coordinate in self._chunks:
            del self._chunks[coordinate]
            if coordinate in self._access_order:
                self._access_order.remove(coordinate)
            return True
        return False
    
    def get_chunks_in_radius(self, center: ChunkCoordinate, radius: int) -> Set[ChunkCoordinate]:
        """
        Get all chunk coordinates within a given radius of a center point.
        
        Args:
            center: Center chunk coordinate
            radius: Radius in chunks
            
        Returns:
            Set of ChunkCoordinate objects within the radius
        """
        chunks = set()
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                chunk_coord = ChunkCoordinate(center.x + dx, center.y + dy)
                chunks.add(chunk_coord)
        return chunks
    
    def get_loaded_chunks(self) -> Set[ChunkCoordinate]:
        """
        Get all currently loaded chunk coordinates.
        
        Returns:
            Set of all loaded ChunkCoordinate objects
        """
        return set(self._chunks.keys())
    
    def get_cache_info(self) -> Dict[str, Union[int, float]]:
        """
        Get information about the current cache state.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            'loaded_chunks': len(self._chunks),
            'cache_size': self.cache_size,
            'cache_usage': len(self._chunks) / self.cache_size
        }
    
    def _update_access(self, coordinate: ChunkCoordinate) -> None:
        """Update the access time for a chunk."""
        if coordinate in self._chunks:
            self._chunks[coordinate].last_accessed = self._access_counter
            self._access_counter += 1
            
            # Move to end of access order
            if coordinate in self._access_order:
                self._access_order.remove(coordinate)
            self._access_order.append(coordinate)
    
    def _evict_lru_chunk(self) -> None:
        """Evict the least recently used chunk from the cache."""
        if not self._access_order:
            return
        
        # Find the least recently used chunk
        lru_coordinate = self._access_order[0]
        lru_time = self._chunks[lru_coordinate].last_accessed
        
        for coordinate in self._access_order:
            if self._chunks[coordinate].last_accessed < lru_time:
                lru_coordinate = coordinate
                lru_time = self._chunks[coordinate].last_accessed
        
        # Remove the LRU chunk
        self.remove_chunk(lru_coordinate)
