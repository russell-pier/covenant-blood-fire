"""
Layered World Generator for creating 3D multi-layer worlds.

This module provides the LayeredWorldGenerator class that creates underground,
surface, and mountain layers simultaneously with proper connectivity between layers.
"""

import random
from typing import Dict, Tuple, Optional, List

from .layered import (
    WorldLayer, LayeredTerrainData, TerrainData, TerrainType,
    create_terrain_data, get_terrain_config
)
from .noise import NoiseGenerator, NoiseConfig
from .resource_generator import ClusteredResourceGenerator


class LayeredWorldGenerator:
    """World generator that creates all three layers simultaneously."""
    
    def __init__(self, seed: int, enable_resources: bool = True):
        """
        Initialize the layered world generator.

        Args:
            seed: Seed for random generation
            enable_resources: Whether to generate resources
        """
        self.seed = seed
        self.enable_resources = enable_resources

        # Different noise generators for each layer
        self.noise_elevation = NoiseGenerator(NoiseConfig(
            seed=seed,
            octaves=5,
            frequency=0.001,
            persistence=0.6
        ))
        self.noise_caves = NoiseGenerator(NoiseConfig(
            seed=seed + 1000,
            octaves=3,
            frequency=0.12
        ))
        self.noise_mountains = NoiseGenerator(NoiseConfig(
            seed=seed + 2000,
            octaves=4,
            frequency=0.006
        ))
        self.noise_surface = NoiseGenerator(NoiseConfig(
            seed=seed + 3000,
            octaves=4,
            frequency=0.008
        ))
        self.noise_detail = NoiseGenerator(NoiseConfig(
            seed=seed + 4000,
            octaves=2,
            frequency=0.05
        ))

        # Resource generator
        if enable_resources:
            self.resource_generator = ClusteredResourceGenerator(seed + 5000)
        else:
            self.resource_generator = None

        # Layer-specific scales
        self.cave_scale = 0.08      # Cave systems (reduced for larger caves)
        self.mountain_scale = 0.006  # Mountain ranges
        self.surface_scale = 0.008   # Surface features
    
    def generate_layered_chunk(
        self, 
        chunk_x: int, 
        chunk_y: int, 
        chunk_size: int = 32
    ) -> Dict[Tuple[int, int], LayeredTerrainData]:
        """
        Generate all three layers for a chunk.
        
        Args:
            chunk_x: Chunk X coordinate
            chunk_y: Chunk Y coordinate
            chunk_size: Size of the chunk in tiles
            
        Returns:
            Dictionary mapping local coordinates to LayeredTerrainData
        """
        chunk_data = {}
        world_offset_x = chunk_x * chunk_size
        world_offset_y = chunk_y * chunk_size
        
        # Generate base elevation map
        elevation_map = self._generate_base_elevation(world_offset_x, world_offset_y, chunk_size)
        
        for local_y in range(chunk_size):
            for local_x in range(chunk_size):
                world_x = world_offset_x + local_x
                world_y = world_offset_y + local_y
                base_elevation = elevation_map[local_y][local_x]
                
                # Generate all three layers
                underground = self._generate_underground_terrain(world_x, world_y, base_elevation)
                surface = self._generate_surface_terrain(world_x, world_y, base_elevation) 
                mountains = self._generate_mountain_terrain(world_x, world_y, base_elevation)
                
                # Determine layer connectivity
                has_cave_entrance = self._determine_cave_entrance(world_x, world_y, base_elevation)
                has_mountain_access = mountains is not None
                
                layered_terrain = LayeredTerrainData(
                    underground=underground,
                    surface=surface,
                    mountains=mountains,
                    has_cave_entrance=has_cave_entrance,
                    has_mountain_access=has_mountain_access
                )
                
                chunk_data[(local_x, local_y)] = layered_terrain

        # Generate resources if enabled
        if self.enable_resources and self.resource_generator:
            layered_resources = self.resource_generator.generate_layered_resource_clusters(
                chunk_x, chunk_y, chunk_data, chunk_size
            )

            # Apply resources to terrain data
            self._apply_resources_to_terrain(chunk_data, layered_resources)

        return chunk_data

    def _apply_resources_to_terrain(
        self,
        chunk_data: Dict[Tuple[int, int], LayeredTerrainData],
        layered_resources: Dict[WorldLayer, List]
    ) -> None:
        """
        Apply resource nodes to terrain data by updating display characters.

        Args:
            chunk_data: Terrain data for the chunk
            layered_resources: Resource nodes organized by layer
        """
        for layer, resource_nodes in layered_resources.items():
            for resource_node in resource_nodes:
                local_pos = (resource_node.x, resource_node.y)

                if local_pos in chunk_data:
                    layered_terrain = chunk_data[local_pos]

                    # Update the appropriate layer's terrain character, colors, and resource data
                    if layer == WorldLayer.SURFACE:
                        layered_terrain.surface.char = resource_node.char
                        layered_terrain.surface.fg_color = resource_node.fg_color
                        if resource_node.bg_color is not None:
                            layered_terrain.surface.bg_color = resource_node.bg_color
                        layered_terrain.surface.resource = resource_node

                    elif layer == WorldLayer.UNDERGROUND:
                        layered_terrain.underground.char = resource_node.char
                        layered_terrain.underground.fg_color = resource_node.fg_color
                        if resource_node.bg_color is not None:
                            layered_terrain.underground.bg_color = resource_node.bg_color
                        layered_terrain.underground.resource = resource_node

                    elif layer == WorldLayer.MOUNTAINS and layered_terrain.mountains:
                        layered_terrain.mountains.char = resource_node.char
                        layered_terrain.mountains.fg_color = resource_node.fg_color
                        if resource_node.bg_color is not None:
                            layered_terrain.mountains.bg_color = resource_node.bg_color
                        layered_terrain.mountains.resource = resource_node
    
    def _generate_base_elevation(self, world_x: int, world_y: int, size: int) -> List[List[float]]:
        """
        Generate base elevation map for all layers.
        
        Args:
            world_x: World X offset
            world_y: World Y offset
            size: Size of the elevation map
            
        Returns:
            2D list of elevation values between 0 and 1
        """
        elevation_map = []
        
        for y in range(size):
            row = []
            for x in range(size):
                world_pos_x = world_x + x
                world_pos_y = world_y + y
                
                elevation = self.noise_elevation.generate(world_pos_x, world_pos_y)
                elevation = (elevation + 1) / 2  # Normalize to 0-1
                row.append(max(0, min(1, elevation)))
            elevation_map.append(row)
        
        return elevation_map
    
    def _generate_underground_terrain(self, world_x: int, world_y: int, base_elevation: float) -> TerrainData:
        """
        Generate underground cave system with larger, more connected caves.

        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            base_elevation: Base elevation value

        Returns:
            TerrainData for underground layer
        """
        # Primary cave noise for main cave systems
        cave_noise = self.noise_caves.generate(world_x, world_y)

        # Secondary noise for cave connectivity and variation
        connectivity_noise = self.noise_detail.generate(world_x * 0.05, world_y * 0.05)

        # Lower threshold for larger caves, adjusted by elevation
        base_threshold = 0.1 + (base_elevation * 0.2)  # Reduced from 0.2 + 0.3

        # Add connectivity bonus to create larger connected systems
        connectivity_bonus = connectivity_noise * 0.15
        effective_threshold = base_threshold - connectivity_bonus

        if abs(cave_noise) > effective_threshold:
            # Open cave space - larger areas will be caves now
            if cave_noise > 0.7:  # Slightly higher threshold for rare ore veins
                terrain_type = TerrainType.ORE_VEIN
            elif cave_noise < -0.6:  # Underground water in deeper areas
                terrain_type = TerrainType.UNDERGROUND_WATER
            else:
                terrain_type = TerrainType.CAVE_FLOOR
        else:
            # Solid rock - will be much darker
            terrain_type = TerrainType.CAVE_WALL

        return create_terrain_data(terrain_type, world_x, world_y, base_elevation, self.noise_detail)
    
    def _generate_surface_terrain(self, world_x: int, world_y: int, base_elevation: float) -> TerrainData:
        """
        Generate surface layer terrain.
        
        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            base_elevation: Base elevation value
            
        Returns:
            TerrainData for surface layer
        """
        # Use base elevation to determine surface type
        surface_noise = self.noise_surface.generate(world_x, world_y)
        
        if base_elevation < 0.2:
            terrain_type = TerrainType.DEEP_WATER
        elif base_elevation < 0.3:
            terrain_type = TerrainType.SHALLOW_WATER
        elif base_elevation < 0.35:
            terrain_type = TerrainType.SAND
        elif base_elevation > 0.8:
            terrain_type = TerrainType.MOUNTAINS
        elif base_elevation > 0.7:
            terrain_type = TerrainType.HILLS
        else:
            # Use surface noise for variety in mid-elevation areas
            if surface_noise > 0.3:
                terrain_type = TerrainType.FOREST
            elif surface_noise > 0.1:
                terrain_type = TerrainType.LIGHT_GRASS
            elif surface_noise < -0.1:
                terrain_type = TerrainType.DARK_GRASS
            else:
                terrain_type = TerrainType.GRASS
        
        return create_terrain_data(terrain_type, world_x, world_y, base_elevation, self.noise_detail)
    
    def _generate_mountain_terrain(self, world_x: int, world_y: int, base_elevation: float) -> Optional[TerrainData]:
        """
        Generate mountain layer (only exists above certain elevation).
        
        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            base_elevation: Base elevation value
            
        Returns:
            TerrainData for mountain layer, or None if no mountain
        """
        if base_elevation < 0.7:
            return None  # No mountain layer
        
        mountain_noise = self.noise_mountains.generate(world_x, world_y)
        
        # Higher elevations get more dramatic mountain features
        mountain_intensity = (base_elevation - 0.7) / 0.3
        
        if mountain_noise > 0.3 * mountain_intensity:
            if base_elevation > 0.9:
                terrain_type = TerrainType.SNOW
            else:
                terrain_type = TerrainType.MOUNTAIN_PEAK
        elif mountain_noise < -0.3 * mountain_intensity:
            terrain_type = TerrainType.MOUNTAIN_CLIFF
        else:
            terrain_type = TerrainType.MOUNTAIN_SLOPE
        
        return create_terrain_data(terrain_type, world_x, world_y, base_elevation, self.noise_detail)
    
    def _determine_cave_entrance(self, world_x: int, world_y: int, base_elevation: float) -> bool:
        """
        Determine if this surface location has a cave entrance.
        
        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            base_elevation: Base elevation value
            
        Returns:
            True if there's a cave entrance, False otherwise
        """
        if base_elevation < 0.3:  # No caves under water
            return False
        
        # Check if there's a cave below and surface access
        cave_noise = abs(self.noise_caves.generate(world_x, world_y))
        cave_threshold = 0.2 + (base_elevation * 0.3)
        entrance_chance = self.noise_detail.generate(world_x * 2, world_y * 2)
        
        return (cave_noise > cave_threshold and entrance_chance > 0.4)


def create_layered_world_generator(seed: int = None, enable_resources: bool = True) -> LayeredWorldGenerator:
    """
    Create a layered world generator with the specified seed.

    Args:
        seed: Seed for random generation (None for random seed)
        enable_resources: Whether to enable resource generation

    Returns:
        LayeredWorldGenerator instance
    """
    if seed is None:
        seed = random.randint(0, 2**31 - 1)

    return LayeredWorldGenerator(seed, enable_resources)
