"""
World generation module that coordinates terrain generation using noise.

This module provides the main WorldGenerator class that manages the
generation of infinite worlds using Perlin noise and chunk management.
"""

from typing import Optional, Set, List, Tuple, Dict

from .chunks import Chunk, ChunkCoordinate, ChunkManager
from .environmental import EnvironmentalGenerator, EnvironmentalData, create_default_environmental_generator
from .layered import LayeredTerrainData, WorldLayer
from .layered_generator import LayeredWorldGenerator, create_layered_world_generator
from .camera_3d import CameraSystem, create_default_camera_3d
from .noise import NoiseGenerator, create_terrain_noise_generator
from .organic import OrganicWorldGenerator, OrganicTerrainData, create_organic_world_generator
from .terrain import (
    TerrainMapper, TerrainType, EnvironmentalTerrainMapper, TerrainProperties,
    create_default_terrain_mapper, create_environmental_terrain_mapper
)
from .animals import AnimalManager, AnimalType


class WorldGenerator:
    """
    Main world generation coordinator that manages infinite procedural world generation.
    
    This class combines noise generation, terrain mapping, and chunk management
    to provide seamless infinite world generation with efficient memory usage.
    """
    
    def __init__(
        self,
        chunk_size: int = 32,
        cache_size: int = 64,
        load_radius: int = 3,
        unload_radius: int = 5,
        seed: Optional[int] = None,
        use_environmental_system: bool = True,
        use_organic_system: bool = True,
        use_layered_system: bool = True,
        enable_animals: bool = True
    ):
        """
        Initialize the world generator.

        Args:
            chunk_size: Size of each chunk in tiles
            cache_size: Maximum number of chunks to keep in memory
            load_radius: Radius around camera to load chunks
            unload_radius: Radius beyond which to unload chunks
            seed: Seed for noise generation (None for random)
            use_environmental_system: Whether to use the environmental system
            use_organic_system: Whether to use the new organic system
            use_layered_system: Whether to use the 3D layered world system
            enable_animals: Whether to enable the animal system
        """
        self.chunk_size = chunk_size
        self.load_radius = load_radius
        self.unload_radius = unload_radius
        self.use_environmental_system = use_environmental_system
        self.use_organic_system = use_organic_system
        self.use_layered_system = use_layered_system
        self.enable_animals = enable_animals

        # Initialize subsystems
        self.chunk_manager = ChunkManager(chunk_size, cache_size)

        if use_organic_system:
            from .organic import OrganicWorldGenerator
            self.organic_generator = OrganicWorldGenerator(seed)
            self.terrain_mapper = create_environmental_terrain_mapper()
            # Keep other generators for backward compatibility
            self.environmental_generator = create_default_environmental_generator(seed)
            self.noise_generator = create_terrain_noise_generator(seed)
        elif use_environmental_system:
            self.environmental_generator = create_default_environmental_generator(seed)
            self.terrain_mapper = create_environmental_terrain_mapper()
            # Keep old noise generator for backward compatibility
            self.noise_generator = create_terrain_noise_generator(seed)
        else:
            self.noise_generator = create_terrain_noise_generator(seed)
            self.terrain_mapper = create_default_terrain_mapper()

        # Initialize layered system if enabled
        if self.use_layered_system:
            self.layered_generator = create_layered_world_generator(seed)
            self.camera_3d = create_default_camera_3d()
        else:
            self.layered_generator = None
            self.camera_3d = None

        # Initialize animal system if enabled
        if self.enable_animals:
            self.animal_manager = AnimalManager()
        else:
            self.animal_manager = None

        # Track current camera position for chunk management
        self._current_camera_chunk: Optional[ChunkCoordinate] = None
        self._loaded_chunks: Set[ChunkCoordinate] = set()

        # Track spawned animal herds to avoid duplicates
        self._spawned_herds: Set[ChunkCoordinate] = set()
    
    def update_camera_position(self, world_x: int, world_y: int) -> None:
        """
        Update the camera position and manage chunk loading/unloading.

        Args:
            world_x: Camera world X coordinate
            world_y: Camera world Y coordinate
        """
        camera_chunk = self.chunk_manager.world_to_chunk_coordinate(world_x, world_y)

        # Only update if camera moved to a different chunk
        if camera_chunk != self._current_camera_chunk:
            self._current_camera_chunk = camera_chunk
            self._update_chunks_around_camera()

        # Update 3D camera position if layered system is enabled
        if self.camera_3d:
            self.camera_3d.set_position(world_x, world_y)
    
    def get_terrain_at(self, world_x: int, world_y: int) -> TerrainType:
        """
        Get the terrain type at a specific world coordinate.

        Args:
            world_x: World X coordinate
            world_y: World Y coordinate

        Returns:
            TerrainType at the specified coordinate
        """
        chunk_coord = self.chunk_manager.world_to_chunk_coordinate(world_x, world_y)
        chunk = self.chunk_manager.get_chunk(chunk_coord)

        if chunk is None:
            # Generate chunk if it doesn't exist
            chunk = self._generate_chunk(chunk_coord)
            self.chunk_manager.add_chunk(chunk)

        local_x, local_y = chunk.world_to_local(world_x, world_y)

        # Double-check bounds before accessing terrain data
        if not (0 <= local_x < self.chunk_size and 0 <= local_y < self.chunk_size):
            # This shouldn't happen, but let's generate directly as fallback
            if self.use_environmental_system:
                env_data = self.environmental_generator.generate_environmental_data(world_x, world_y)
                return self.terrain_mapper.environmental_to_terrain(env_data)
            else:
                noise_value = self.noise_generator.generate(world_x, world_y)
                return self.terrain_mapper.noise_to_terrain(noise_value)

        return chunk.get_terrain_at(local_x, local_y)

    def get_layered_terrain_at(self, world_x: int, world_y: int) -> Optional[LayeredTerrainData]:
        """
        Get the layered terrain data at a specific world coordinate.

        Args:
            world_x: World X coordinate
            world_y: World Y coordinate

        Returns:
            LayeredTerrainData at the specified coordinate, or None if layered system is disabled
        """
        if not self.use_layered_system or not self.layered_generator:
            return None

        chunk_coord = self.chunk_manager.world_to_chunk_coordinate(world_x, world_y)
        chunk = self.chunk_manager.get_chunk(chunk_coord)

        if chunk is None:
            # Generate chunk if it doesn't exist
            chunk = self._generate_chunk(chunk_coord)
            self.chunk_manager.add_chunk(chunk)

        local_x, local_y = chunk.world_to_local(world_x, world_y)
        return chunk.get_layered_data_at(local_x, local_y)

    def get_rendered_terrain_at(self, world_x: int, world_y: int) -> TerrainType:
        """
        Get the terrain type for rendering based on current 3D camera layer.

        Args:
            world_x: World X coordinate
            world_y: World Y coordinate

        Returns:
            TerrainType for rendering based on current layer
        """
        if self.use_layered_system and self.camera_3d:
            layered_data = self.get_layered_terrain_at(world_x, world_y)
            if layered_data:
                rendered_terrain = self.camera_3d.get_render_data(layered_data)
                return rendered_terrain.terrain_type

        # Fallback to regular terrain generation
        return self.get_terrain_at(world_x, world_y)

    def change_layer(self, new_layer: WorldLayer) -> bool:
        """
        Attempt to change the current 3D layer.

        Args:
            new_layer: The layer to transition to

        Returns:
            True if layer change was successful, False otherwise
        """
        if not self.use_layered_system or not self.camera_3d:
            return False

        # Allow free layer switching - no terrain restrictions
        return self.camera_3d.change_layer(new_layer)

    def get_current_layer(self) -> Optional[WorldLayer]:
        """
        Get the current 3D layer.

        Returns:
            Current WorldLayer, or None if layered system is disabled
        """
        if self.camera_3d:
            return self.camera_3d.get_current_layer()
        return None

    def get_organic_terrain_properties_at(self, world_x: int, world_y: int) -> Optional[TerrainProperties]:
        """
        Get organic terrain properties at a specific world coordinate.

        Args:
            world_x: World X coordinate
            world_y: World Y coordinate

        Returns:
            TerrainProperties with organic character and colors, or None if not using organic system
        """
        if not self.use_organic_system:
            return None

        chunk_coord = self.chunk_manager.world_to_chunk_coordinate(world_x, world_y)
        chunk = self.chunk_manager.get_chunk(chunk_coord)

        if chunk is None:
            # Generate chunk if it doesn't exist
            chunk = self._generate_chunk(chunk_coord)
            self.chunk_manager.add_chunk(chunk)

        local_x, local_y = chunk.world_to_local(world_x, world_y)

        # Check if chunk has organic data
        if hasattr(chunk, 'organic_data') and chunk.organic_data:
            try:
                organic_data = chunk.organic_data[local_y][local_x]
                return TerrainProperties(
                    terrain_type=organic_data.terrain_type,
                    character=organic_data.character,
                    foreground_color=organic_data.foreground_color,
                    background_color=organic_data.background_color,
                    movement_cost=1.0,  # Default movement cost
                    passable=True,      # Default passable
                    description=f"Organic {organic_data.terrain_type.value}"
                )
            except (IndexError, AttributeError):
                pass

        return None

    def get_environmental_data_at(self, world_x: int, world_y: int) -> Optional[EnvironmentalData]:
        """
        Get the environmental data at a specific world coordinate.

        Args:
            world_x: World X coordinate
            world_y: World Y coordinate

        Returns:
            EnvironmentalData at the specified coordinate, or None if not using environmental system
        """
        if not self.use_environmental_system:
            return None

        chunk_coord = self.chunk_manager.world_to_chunk_coordinate(world_x, world_y)
        chunk = self.chunk_manager.get_chunk(chunk_coord)

        if chunk is None:
            # Generate chunk if it doesn't exist
            chunk = self._generate_chunk(chunk_coord)
            self.chunk_manager.add_chunk(chunk)

        local_x, local_y = chunk.world_to_local(world_x, world_y)

        # Double-check bounds before accessing environmental data
        if not (0 <= local_x < self.chunk_size and 0 <= local_y < self.chunk_size):
            # Generate directly as fallback
            return self.environmental_generator.generate_environmental_data(world_x, world_y)

        try:
            return chunk.get_environmental_data_at(local_x, local_y)
        except RuntimeError:
            # Environmental data not set, generate directly
            return self.environmental_generator.generate_environmental_data(world_x, world_y)

    def get_chunk_terrain_data(self, chunk_coord: ChunkCoordinate) -> Optional[Chunk]:
        """
        Get a chunk's terrain data, generating it if necessary.
        
        Args:
            chunk_coord: The chunk coordinate to retrieve
            
        Returns:
            Chunk object with terrain data, or None if generation fails
        """
        chunk = self.chunk_manager.get_chunk(chunk_coord)
        
        if chunk is None:
            chunk = self._generate_chunk(chunk_coord)
            self.chunk_manager.add_chunk(chunk)
        
        return chunk
    
    def is_chunk_loaded(self, chunk_coord: ChunkCoordinate) -> bool:
        """
        Check if a chunk is currently loaded in memory.
        
        Args:
            chunk_coord: The chunk coordinate to check
            
        Returns:
            True if the chunk is loaded, False otherwise
        """
        return self.chunk_manager.get_chunk(chunk_coord) is not None
    
    def get_world_info(self) -> dict:
        """
        Get information about the current world state.

        Returns:
            Dictionary with world generation statistics
        """
        cache_info = self.chunk_manager.get_cache_info()

        return {
            'chunk_size': self.chunk_size,
            'load_radius': self.load_radius,
            'unload_radius': self.unload_radius,
            'current_camera_chunk': self._current_camera_chunk,
            'loaded_chunks_count': len(self._loaded_chunks),
            'cache_info': cache_info,
            'noise_seed': self.noise_generator.config.seed
        }

    def get_performance_stats(self) -> dict:
        """
        Get performance-related statistics.

        Returns:
            Dictionary with performance metrics
        """
        cache_info = self.chunk_manager.get_cache_info()

        return {
            'chunks_loaded': len(self._loaded_chunks),
            'cache_usage_percent': cache_info['cache_usage'] * 100,
            'cache_size': cache_info['cache_size'],
            'current_chunk': str(self._current_camera_chunk) if self._current_camera_chunk else None
        }
    
    def _generate_chunk(self, chunk_coord: ChunkCoordinate) -> Chunk:
        """
        Generate terrain data for a chunk using organic, environmental, or noise system.

        Args:
            chunk_coord: The chunk coordinate to generate

        Returns:
            Generated Chunk object with terrain data
        """
        chunk = Chunk(chunk_coord, self.chunk_size)

        if self.use_organic_system:
            # Generate organic terrain data for the chunk
            organic_chunk_data = self.organic_generator.generate_chunk_data(
                chunk_coord.x, chunk_coord.y, self.chunk_size
            )

            # Convert organic data to terrain types and store organic data
            terrain_data = []
            organic_data = []
            for y in range(self.chunk_size):
                terrain_row = []
                organic_row = []
                for x in range(self.chunk_size):
                    organic_terrain = organic_chunk_data[(x, y)]
                    terrain_row.append(organic_terrain.terrain_type)
                    organic_row.append(organic_terrain)
                terrain_data.append(terrain_row)
                organic_data.append(organic_row)

            # Store all data types
            chunk.set_terrain_data(terrain_data)
            chunk.set_organic_data(organic_data)

        elif self.use_environmental_system:
            # Generate environmental data for the chunk
            environmental_data = self.environmental_generator.generate_chunk_environmental_data(
                chunk_coord.x, chunk_coord.y, self.chunk_size
            )

            # Convert environmental data to terrain types
            terrain_data = []
            for y in range(self.chunk_size):
                row = []
                for x in range(self.chunk_size):
                    env_data = environmental_data[y][x]
                    terrain_type = self.terrain_mapper.environmental_to_terrain(env_data)
                    row.append(terrain_type)
                terrain_data.append(row)

            # Store both environmental and terrain data
            chunk.set_environmental_data(environmental_data)
            chunk.set_terrain_data(terrain_data)
        else:
            # Use legacy noise-based generation
            noise_data = self.noise_generator.generate_chunk(
                chunk_coord.x, chunk_coord.y, self.chunk_size
            )

            # Convert noise data to terrain types
            terrain_data = []
            for y in range(self.chunk_size):
                row = []
                for x in range(self.chunk_size):
                    noise_value = noise_data[y][x]
                    terrain_type = self.terrain_mapper.noise_to_terrain(noise_value)
                    row.append(terrain_type)
                terrain_data.append(row)

            chunk.set_terrain_data(terrain_data)

        # Generate layered terrain data if layered system is enabled
        if self.use_layered_system and self.layered_generator:
            layered_chunk_data = self.layered_generator.generate_layered_chunk(
                chunk_coord.x, chunk_coord.y, self.chunk_size
            )

            # Convert to 2D list format for chunk storage
            layered_data = []
            for y in range(self.chunk_size):
                row = []
                for x in range(self.chunk_size):
                    layered_terrain = layered_chunk_data[(x, y)]
                    row.append(layered_terrain)
                layered_data.append(row)

            chunk.set_layered_data(layered_data)

        # Spawn animals if enabled and this chunk hasn't been processed yet
        if self.enable_animals and self.animal_manager and chunk_coord not in self._spawned_herds:
            self._spawn_animals_in_chunk(chunk_coord, chunk)
            self._spawned_herds.add(chunk_coord)

        return chunk

    def _spawn_animals_in_chunk(self, chunk_coord: ChunkCoordinate, chunk: Chunk) -> None:
        """
        Spawn animals in appropriate terrain within a chunk.

        Args:
            chunk_coord: The chunk coordinate
            chunk: The generated chunk with terrain data
        """
        import random

        # Always spawn sheep in the 0,0 chunk for testing
        is_origin_chunk = chunk_coord.x == 0 and chunk_coord.y == 0

        # Only spawn animals occasionally to avoid overcrowding (except origin chunk)
        if not is_origin_chunk and random.random() > 0.3:  # 30% chance per chunk
            return

        # Find suitable spawn locations in the chunk
        suitable_locations = []

        # Check terrain data based on which system is being used
        if self.use_organic_system and chunk.organic_data:
            for y in range(self.chunk_size):
                for x in range(self.chunk_size):
                    organic_terrain = chunk.organic_data[y][x]
                    if self._is_suitable_for_animals(organic_terrain.terrain_type):
                        world_x = chunk_coord.x * self.chunk_size + x
                        world_y = chunk_coord.y * self.chunk_size + y
                        suitable_locations.append((world_x, world_y))

        elif chunk.terrain_data:
            for y in range(self.chunk_size):
                for x in range(self.chunk_size):
                    terrain_type = chunk.terrain_data[y][x]
                    if self._is_suitable_for_animals(terrain_type):
                        world_x = chunk_coord.x * self.chunk_size + x
                        world_y = chunk_coord.y * self.chunk_size + y
                        suitable_locations.append((world_x, world_y))

        # Spawn animals if we found suitable locations
        if suitable_locations and len(suitable_locations) >= 8:  # Need space for a herd
            # Choose a random location for the herd center
            center_x, center_y = random.choice(suitable_locations)

            # For origin chunk, spawn both sheep and cows. Otherwise random choice
            if is_origin_chunk:
                # Spawn both types in origin chunk for visibility
                # First spawn sheep
                sheep_center_x, sheep_center_y = random.choice(suitable_locations)
                sheep_herd_id = f"sheep_origin_chunk"
                self.animal_manager.spawn_herd(
                    animal_type=AnimalType.SHEEP,
                    center_x=sheep_center_x,
                    center_y=sheep_center_y,
                    herd_id=sheep_herd_id,
                    size=4
                )

                # Then spawn cows nearby
                cow_locations = [loc for loc in suitable_locations if
                               abs(loc[0] - sheep_center_x) > 8 or abs(loc[1] - sheep_center_y) > 8]
                if cow_locations:
                    cow_center_x, cow_center_y = random.choice(cow_locations)
                    cow_herd_id = f"cow_origin_chunk"
                    self.animal_manager.spawn_herd(
                        animal_type=AnimalType.COW,
                        center_x=cow_center_x,
                        center_y=cow_center_y,
                        herd_id=cow_herd_id,
                        size=4
                    )
                return  # Skip the normal spawning logic for origin chunk
            else:
                # Increase cow probability (50/50 instead of 70/30)
                animal_type = AnimalType.SHEEP if random.random() < 0.5 else AnimalType.COW
                herd_size = random.randint(4, 8)  # Variable herd sizes

            # Generate unique herd ID
            herd_id = f"{animal_type.value}_chunk_{chunk_coord.x}_{chunk_coord.y}"

            # Spawn the herd
            self.animal_manager.spawn_herd(
                animal_type=animal_type,
                center_x=center_x,
                center_y=center_y,
                herd_id=herd_id,
                size=herd_size
            )
        elif is_origin_chunk:
            # Force spawn sheep in origin chunk even if terrain isn't ideal
            # Find any non-water location
            fallback_locations = []
            if self.use_organic_system and chunk.organic_data:
                for y in range(self.chunk_size):
                    for x in range(self.chunk_size):
                        organic_terrain = chunk.organic_data[y][x]
                        if organic_terrain.terrain_type.value not in ['water', 'cave_wall']:
                            world_x = chunk_coord.x * self.chunk_size + x
                            world_y = chunk_coord.y * self.chunk_size + y
                            fallback_locations.append((world_x, world_y))

            if fallback_locations:
                center_x, center_y = random.choice(fallback_locations)
                herd_id = f"sheep_origin_chunk"
                self.animal_manager.spawn_herd(
                    animal_type=AnimalType.SHEEP,
                    center_x=center_x,
                    center_y=center_y,
                    herd_id=herd_id,
                    size=6
                )

    def _is_suitable_for_animals(self, terrain_type: TerrainType) -> bool:
        """
        Check if a terrain type is suitable for animal spawning.

        Args:
            terrain_type: The terrain type to check

        Returns:
            True if animals can spawn on this terrain
        """
        # Animals prefer grasslands, avoid water and cliffs
        suitable_terrains = {
            TerrainType.GRASS,
            TerrainType.LIGHT_GRASS,
            TerrainType.DARK_GRASS,
            TerrainType.FERTILE
        }

        return terrain_type in suitable_terrains

    def _update_chunks_around_camera(self) -> None:
        """Update chunk loading/unloading based on camera position."""
        if self._current_camera_chunk is None:
            return
        
        # Get chunks that should be loaded
        chunks_to_load = self.chunk_manager.get_chunks_in_radius(
            self._current_camera_chunk, self.load_radius
        )
        
        # Get chunks that should be unloaded
        chunks_to_unload = set()
        for chunk_coord in self._loaded_chunks:
            distance = max(
                abs(chunk_coord.x - self._current_camera_chunk.x),
                abs(chunk_coord.y - self._current_camera_chunk.y)
            )
            if distance > self.unload_radius:
                chunks_to_unload.add(chunk_coord)
        
        # Load new chunks
        for chunk_coord in chunks_to_load:
            if not self.is_chunk_loaded(chunk_coord):
                chunk = self._generate_chunk(chunk_coord)
                self.chunk_manager.add_chunk(chunk)
                self._loaded_chunks.add(chunk_coord)
        
        # Unload distant chunks
        for chunk_coord in chunks_to_unload:
            self.chunk_manager.remove_chunk(chunk_coord)
            self._loaded_chunks.discard(chunk_coord)
    
    def preload_chunks_around(self, world_x: int, world_y: int, radius: Optional[int] = None) -> None:
        """
        Preload chunks around a specific world position.
        
        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            radius: Radius to preload (defaults to load_radius)
        """
        if radius is None:
            radius = self.load_radius
        
        center_chunk = self.chunk_manager.world_to_chunk_coordinate(world_x, world_y)
        chunks_to_load = self.chunk_manager.get_chunks_in_radius(center_chunk, radius)
        
        for chunk_coord in chunks_to_load:
            if not self.is_chunk_loaded(chunk_coord):
                chunk = self._generate_chunk(chunk_coord)
                self.chunk_manager.add_chunk(chunk)
                self._loaded_chunks.add(chunk_coord)

    def update_animals(self) -> None:
        """Update all animals in the world."""
        if not self.animal_manager:
            return

        # Get terrain data for animal collision detection
        terrain_data = {}

        # Collect terrain data from loaded chunks
        for chunk_coord in self._loaded_chunks:
            chunk = self.chunk_manager.get_chunk(chunk_coord)
            if chunk:
                if self.use_organic_system and chunk.organic_data:
                    for y in range(self.chunk_size):
                        for x in range(self.chunk_size):
                            world_x = chunk_coord.x * self.chunk_size + x
                            world_y = chunk_coord.y * self.chunk_size + y
                            terrain_data[(world_x, world_y)] = chunk.organic_data[y][x]
                elif chunk.terrain_data:
                    for y in range(self.chunk_size):
                        for x in range(self.chunk_size):
                            world_x = chunk_coord.x * self.chunk_size + x
                            world_y = chunk_coord.y * self.chunk_size + y
                            # Create a simple terrain object for compatibility
                            class SimpleTerrain:
                                def __init__(self, terrain_type):
                                    self.terrain_type = terrain_type
                            terrain_data[(world_x, world_y)] = SimpleTerrain(chunk.terrain_data[y][x])

        # Update animals with terrain data and camera position for culling
        if self._current_camera_chunk:
            camera_x = self._current_camera_chunk.x * self.chunk_size
            camera_y = self._current_camera_chunk.y * self.chunk_size
        else:
            camera_x, camera_y = 0, 0
        self.animal_manager.update_animals(terrain_data, camera_x, camera_y)

    def get_animal_positions(self) -> List[Tuple[int, int, str, Tuple[int, int, int]]]:
        """
        Get positions and render data for all animals.

        Returns:
            List of tuples (x, y, character, color) for rendering animals
        """
        if not self.animal_manager:
            return []

        return self.animal_manager.get_all_animal_positions()

    def get_animals_at_position(self, x: int, y: int):
        """
        Get any animals at a specific world position.

        Args:
            x: World X coordinate
            y: World Y coordinate

        Returns:
            List of animals at the specified position
        """
        if not self.animal_manager:
            return []

        return self.animal_manager.get_animals_at_position(x, y)

    def update_animals_continuous(self) -> None:
        """
        Update animals continuously (called every frame).
        This should be called from the main game loop, not just on camera movement.
        """
        if not self.animal_manager:
            return

        # Get terrain data for animal collision detection
        terrain_data = {}

        # Collect terrain data from loaded chunks
        for chunk_coord in self._loaded_chunks:
            chunk = self.chunk_manager.get_chunk(chunk_coord)
            if chunk:
                if self.use_organic_system and chunk.organic_data:
                    for y in range(self.chunk_size):
                        for x in range(self.chunk_size):
                            world_x = chunk_coord.x * self.chunk_size + x
                            world_y = chunk_coord.y * self.chunk_size + y
                            terrain_data[(world_x, world_y)] = chunk.organic_data[y][x]
                elif chunk.terrain_data:
                    for y in range(self.chunk_size):
                        for x in range(self.chunk_size):
                            world_x = chunk_coord.x * self.chunk_size + x
                            world_y = chunk_coord.y * self.chunk_size + y
                            # Create a simple terrain object for compatibility
                            class SimpleTerrain:
                                def __init__(self, terrain_type):
                                    self.terrain_type = terrain_type
                            terrain_data[(world_x, world_y)] = SimpleTerrain(chunk.terrain_data[y][x])

        # Get camera position for culling
        if self._current_camera_chunk:
            camera_x = self._current_camera_chunk.x * self.chunk_size
            camera_y = self._current_camera_chunk.y * self.chunk_size
        else:
            camera_x, camera_y = 0, 0

        # Update animals with terrain data and camera position for culling
        self.animal_manager.update_animals(terrain_data, camera_x, camera_y)

    def get_animal_performance_stats(self) -> Dict[str, int]:
        """
        Get animal system performance statistics.

        Returns:
            Dictionary with animal performance metrics
        """
        if not self.animal_manager:
            return {}

        return self.animal_manager.get_performance_stats()


def create_default_world_generator(seed: Optional[int] = None) -> WorldGenerator:
    """
    Create a world generator with default settings using organic system.

    Args:
        seed: Optional seed for reproducible world generation

    Returns:
        WorldGenerator instance with default configuration and organic system
    """
    return WorldGenerator(seed=seed, use_organic_system=True)


def create_legacy_world_generator(seed: Optional[int] = None) -> WorldGenerator:
    """
    Create a world generator with legacy noise-based system.

    Args:
        seed: Optional seed for reproducible world generation

    Returns:
        WorldGenerator instance with legacy noise-based configuration
    """
    return WorldGenerator(seed=seed, use_environmental_system=False)


def create_environmental_world_generator(seed: Optional[int] = None) -> WorldGenerator:
    """
    Create a world generator explicitly using the environmental system.

    Args:
        seed: Optional seed for reproducible world generation

    Returns:
        WorldGenerator instance with environmental system enabled
    """
    return WorldGenerator(seed=seed, use_environmental_system=True, use_organic_system=False)


def create_organic_world_generator(seed: Optional[int] = None) -> WorldGenerator:
    """
    Create a world generator explicitly using the organic system.

    Args:
        seed: Optional seed for reproducible world generation

    Returns:
        WorldGenerator instance with organic system enabled
    """
    return WorldGenerator(seed=seed, use_organic_system=True)
