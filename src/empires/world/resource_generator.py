"""
Clustered Resource Generator for creating realistic resource distributions.

This module provides the ClusteredResourceGenerator class that creates large
resource clusters instead of scattered individual nodes, with layer-specific
characteristics and strategic gameplay implications.
"""

import math
import random
from typing import Dict, List, Tuple, Optional

from .layered import WorldLayer, LayeredTerrainData, TerrainData
from .noise import NoiseGenerator, NoiseConfig
from .resource_types import (
    ResourceType, ResourceCluster, ResourceNode, RESOURCE_CHARACTERS,
    RESOURCE_YIELDS, get_resource_layer, is_renewable, get_resource_character_and_color
)
from .resource_config import (
    TERRAIN_COMPATIBILITY, LAYER_GENERATION_CONFIG, RESOURCE_TYPE_DISTRIBUTION,
    get_terrain_compatibility, get_layer_config, is_terrain_compatible,
    get_rarity_from_score, should_spawn_resource
)
from .terrain import TerrainType


class ClusteredResourceGenerator:
    """Generates large resource clusters instead of scattered individual nodes."""

    def __init__(self, seed: int):
        """
        Initialize the clustered resource generator.

        Args:
            seed: Seed for random generation
        """
        self.seed = seed

        # Performance optimization: cache for cluster data
        self._cluster_cache = {}
        self._cache_max_size = 100
        
        # Multiple noise generators for different aspects
        self.noise_cluster = NoiseGenerator(NoiseConfig(
            seed=seed + 6000,
            octaves=3,
            frequency=0.01,   # How spread out cluster centers are (increased for more variation)
            persistence=0.6
        ))
        self.noise_density = NoiseGenerator(NoiseConfig(
            seed=seed + 7000,
            octaves=2,
            frequency=0.05,   # Variation within clusters (increased)
            persistence=0.5
        ))
        self.noise_rarity = NoiseGenerator(NoiseConfig(
            seed=seed + 8000,
            octaves=2,
            frequency=0.1,    # Fine-grained rarity variation (increased)
            persistence=0.4
        ))
        
        # Layer-specific configuration (balanced for good gameplay)
        self.layer_config = {
            WorldLayer.SURFACE: {
                'sample_step': 5,        # Slightly less frequent sampling
                'noise_offset': 0,
                'threshold': 0.2,        # Moderately common surface resources
                'radius_base': 5,        # Smaller clusters
                'radius_scale': 8,       # Reduced scale
                'density_base': 0.25,    # Moderate density
                'density_scale': 0.3
            },
            WorldLayer.UNDERGROUND: {
                'sample_step': 7,        # Less frequent underground sampling
                'noise_offset': 1000,
                'threshold': 0.25,       # Less common underground resources
                'radius_base': 3,        # Smaller, dense clusters (rich veins)
                'radius_scale': 6,       # Reduced scale
                'density_base': 0.35,    # Good density
                'density_scale': 0.4
            },
            WorldLayer.MOUNTAINS: {
                'sample_step': 6,        # Less frequent mountain sampling
                'noise_offset': 2000,
                'threshold': 0.22,       # Less common mountain resources
                'radius_base': 4,        # Smaller clusters (quarries, peaks)
                'radius_scale': 7,       # Reduced scale
                'density_base': 0.3,     # Good density
                'density_scale': 0.35
            }
        }
    
    def generate_layered_resource_clusters(
        self,
        chunk_x: int,
        chunk_y: int,
        layered_terrain_data: Dict[Tuple[int, int], LayeredTerrainData],
        chunk_size: int = 32
    ) -> Dict[WorldLayer, List[ResourceNode]]:
        """
        Generate clustered resources for all three layers.

        Args:
            chunk_x: Chunk X coordinate
            chunk_y: Chunk Y coordinate
            layered_terrain_data: Terrain data for the chunk
            chunk_size: Size of the chunk in tiles

        Returns:
            Dictionary mapping WorldLayer to list of ResourceNodes
        """
        # Performance optimization: check cache first
        cache_key = (chunk_x, chunk_y, chunk_size)
        if cache_key in self._cluster_cache:
            return self._cluster_cache[cache_key]

        world_offset_x = chunk_x * chunk_size
        world_offset_y = chunk_y * chunk_size

        layered_resources = {
            WorldLayer.SURFACE: [],
            WorldLayer.UNDERGROUND: [],
            WorldLayer.MOUNTAINS: []
        }

        # Generate clusters for each layer separately
        for layer in WorldLayer:
            clusters = self._find_layer_specific_clusters(
                world_offset_x, world_offset_y, chunk_size, layer
            )
            valid_clusters = self._filter_clusters_by_layer_terrain(
                clusters, layered_terrain_data, world_offset_x, world_offset_y, chunk_size, layer
            )

            for cluster in valid_clusters:
                nodes = self._populate_layer_cluster(
                    cluster, layered_terrain_data, world_offset_x, world_offset_y, chunk_size, layer
                )
                layered_resources[layer].extend(nodes)

        # Cache the result (with size limit)
        if len(self._cluster_cache) >= self._cache_max_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self._cluster_cache))
            del self._cluster_cache[oldest_key]

        self._cluster_cache[cache_key] = layered_resources
        return layered_resources
    
    def _find_layer_specific_clusters(
        self, 
        world_x: int, 
        world_y: int, 
        size: int, 
        layer: WorldLayer
    ) -> List[ResourceCluster]:
        """Find clusters specific to each layer with different characteristics."""
        clusters = []
        search_radius = size // 2
        config = self.layer_config[layer]
        
        for sample_y in range(-search_radius, size + search_radius, config['sample_step']):
            for sample_x in range(-search_radius, size + search_radius, config['sample_step']):
                check_x = world_x + sample_x
                check_y = world_y + sample_y
                
                # Layer-specific noise with offset
                cluster_noise = self.noise_cluster.generate(
                    check_x + config['noise_offset'],
                    check_y + config['noise_offset']
                )
                
                if abs(cluster_noise) > config['threshold']:
                    # Layer-specific cluster properties
                    radius = config['radius_base'] + (abs(cluster_noise) * config['radius_scale'])
                    density = config['density_base'] + (abs(cluster_noise) * config['density_scale'])
                    
                    # Determine resource type for this cluster
                    resource_type = self._determine_cluster_resource_type(check_x, check_y, cluster_noise, layer)
                    
                    clusters.append(ResourceCluster(
                        center_x=check_x,
                        center_y=check_y,
                        resource_type=resource_type,
                        radius=radius,
                        density=density,
                        intensity=cluster_noise,
                        layer=layer
                    ))
        
        return clusters
    
    def _determine_cluster_resource_type(
        self, 
        x: int, 
        y: int, 
        base_noise: float, 
        layer: WorldLayer
    ) -> ResourceType:
        """Determine what type of resource cluster based on layer and noise."""
        # Use different noise frequency to determine resource type
        type_noise = self.noise_cluster.generate(x * 0.1, y * 0.1)
        
        if layer == WorldLayer.SURFACE:
            # Surface resources - life and basic materials
            if base_noise > 0.7:  # Rich surface areas
                if type_noise > 0.3:
                    return ResourceType.WOOD  # Dense forests
                elif type_noise > 0:
                    return ResourceType.FOOD_SURFACE  # Fertile valleys
                else:
                    return ResourceType.STONE_SURFACE  # Surface quarries
            else:  # Common surface resources
                if type_noise > 0:
                    return ResourceType.WOOD
                else:
                    return ResourceType.FOOD_SURFACE
                    
        elif layer == WorldLayer.UNDERGROUND:
            # Underground resources - valuable minerals and metals
            if base_noise > 0.8:  # Very rich underground areas
                if type_noise > 0.5:
                    return ResourceType.CRYSTAL  # Rare magical crystals
                elif type_noise > 0:
                    return ResourceType.GOLD  # Gold veins
                else:
                    return ResourceType.GEMS  # Gem deposits
            elif base_noise > 0.6:  # Rich underground
                if type_noise > 0.3:
                    return ResourceType.GOLD
                elif type_noise > 0:
                    return ResourceType.IRON
                else:
                    return ResourceType.COAL
            else:  # Common underground
                if type_noise > 0.5:
                    return ResourceType.IRON
                elif type_noise > 0:
                    return ResourceType.COAL
                else:
                    return ResourceType.UNDERGROUND_WATER
                    
        elif layer == WorldLayer.MOUNTAINS:
            # Mountain resources - high-quality stone and rare materials
            if base_noise > 0.7:  # Rich mountain areas
                if type_noise > 0.5:
                    return ResourceType.RARE_GEMS  # Mountain gem veins
                elif type_noise > 0:
                    return ResourceType.METAL_MOUNTAIN  # Surface metal deposits
                else:
                    return ResourceType.STONE_MOUNTAIN  # Massive quarries
            else:  # Common mountain resources
                if type_noise > 0.3:
                    return ResourceType.STONE_MOUNTAIN
                elif type_noise > 0:
                    return ResourceType.ICE  # High altitude ice
                else:
                    return ResourceType.METAL_MOUNTAIN
        
        # Fallback
        return ResourceType.WOOD

    def _filter_clusters_by_layer_terrain(
        self,
        clusters: List[ResourceCluster],
        layered_terrain_data: Dict[Tuple[int, int], LayeredTerrainData],
        world_x: int,
        world_y: int,
        chunk_size: int,
        layer: WorldLayer
    ) -> List[ResourceCluster]:
        """Only keep clusters that match appropriate terrain for the layer."""

        valid_clusters = []
        layer_compatibility = TERRAIN_COMPATIBILITY.get(layer, {})

        for cluster in clusters:
            # Check if cluster center or nearby area has suitable terrain
            suitable_terrain_found = False
            compatible_terrains = layer_compatibility.get(cluster.resource_type, [])

            if not compatible_terrains:
                # If no specific compatibility rules, allow the cluster
                valid_clusters.append(cluster)
                continue

            # Sample terrain around cluster center
            sample_radius = min(5, int(cluster.radius // 2))
            for dy in range(-sample_radius, sample_radius + 1, 2):
                for dx in range(-sample_radius, sample_radius + 1, 2):
                    sample_x = cluster.center_x + dx
                    sample_y = cluster.center_y + dy

                    # Convert to chunk-local coordinates
                    local_x = sample_x - world_x
                    local_y = sample_y - world_y

                    # Check if this position is in our chunk and has terrain data
                    if 0 <= local_x < chunk_size and 0 <= local_y < chunk_size:
                        if (local_x, local_y) in layered_terrain_data:
                            layered_terrain = layered_terrain_data[(local_x, local_y)]

                            # Get terrain for the appropriate layer
                            if layer == WorldLayer.SURFACE:
                                terrain_type = layered_terrain.surface.terrain_type
                            elif layer == WorldLayer.UNDERGROUND:
                                terrain_type = layered_terrain.underground.terrain_type
                            elif layer == WorldLayer.MOUNTAINS and layered_terrain.mountains:
                                terrain_type = layered_terrain.mountains.terrain_type
                            else:
                                continue

                            if terrain_type in compatible_terrains:
                                suitable_terrain_found = True
                                break

                if suitable_terrain_found:
                    break

            if suitable_terrain_found:
                valid_clusters.append(cluster)

        return valid_clusters

    def _populate_layer_cluster(
        self,
        cluster: ResourceCluster,
        layered_terrain_data: Dict[Tuple[int, int], LayeredTerrainData],
        world_x: int,
        world_y: int,
        chunk_size: int,
        layer: WorldLayer
    ) -> List[ResourceNode]:
        """Fill a cluster with individual resource nodes."""

        resource_nodes = []
        cluster_radius_squared = cluster.radius * cluster.radius

        # Check every position within the cluster radius
        min_x = max(0, int(cluster.center_x - cluster.radius) - world_x)
        max_x = min(chunk_size, int(cluster.center_x + cluster.radius) - world_x + 1)
        min_y = max(0, int(cluster.center_y - cluster.radius) - world_y)
        max_y = min(chunk_size, int(cluster.center_y + cluster.radius) - world_y + 1)

        for local_y in range(min_y, max_y):
            for local_x in range(min_x, max_x):
                world_pos_x = world_x + local_x
                world_pos_y = world_y + local_y

                # Check if position is within cluster radius
                dx = world_pos_x - cluster.center_x
                dy = world_pos_y - cluster.center_y
                distance_squared = dx * dx + dy * dy

                if distance_squared <= cluster_radius_squared:
                    # Check if we have terrain data for this position
                    if (local_x, local_y) not in layered_terrain_data:
                        continue

                    layered_terrain = layered_terrain_data[(local_x, local_y)]

                    # Get terrain for the appropriate layer
                    if layer == WorldLayer.SURFACE:
                        terrain_data = layered_terrain.surface
                    elif layer == WorldLayer.UNDERGROUND:
                        terrain_data = layered_terrain.underground
                    elif layer == WorldLayer.MOUNTAINS and layered_terrain.mountains:
                        terrain_data = layered_terrain.mountains
                    else:
                        continue

                    # Check terrain compatibility
                    if not self._is_terrain_suitable_for_resource(cluster.resource_type, terrain_data.terrain_type, layer):
                        continue

                    # Use density noise to determine if resource spawns here
                    density_noise = self.noise_density.generate(
                        world_pos_x,
                        world_pos_y
                    )

                    # Distance from cluster center affects spawn probability
                    distance_factor = 1.0 - (math.sqrt(distance_squared) / cluster.radius)
                    spawn_probability = cluster.density * distance_factor

                    # Apply noise variation
                    final_probability = spawn_probability + (density_noise * 0.2)

                    if final_probability > 0.1:  # Much lower threshold for spawning resource nodes

                        # Determine resource rarity based on cluster intensity and distance
                        rarity_noise = self.noise_rarity.generate(
                            world_pos_x,
                            world_pos_y
                        )

                        rarity_score = cluster.intensity * distance_factor + rarity_noise

                        if rarity_score > 0.8:
                            rarity = 'epic'
                        elif rarity_score > 0.6:
                            rarity = 'rare'
                        else:
                            rarity = 'common'

                        # Select character and colors for resource node
                        char, fg_color, bg_color = get_resource_character_and_color(cluster.resource_type, rarity)

                        resource_nodes.append(ResourceNode(
                            x=local_x,
                            y=local_y,
                            resource_type=cluster.resource_type,
                            char=char,
                            yield_amount=RESOURCE_YIELDS[rarity],
                            respawns=is_renewable(cluster.resource_type),
                            rarity=rarity,
                            fg_color=fg_color,
                            bg_color=bg_color
                        ))

        return resource_nodes

    def _is_terrain_suitable_for_resource(
        self,
        resource_type: ResourceType,
        terrain_type: TerrainType,
        layer: WorldLayer
    ) -> bool:
        """Check if terrain can support this resource type on this layer."""

        # Use the centralized terrain compatibility from config
        compatibility = TERRAIN_COMPATIBILITY.get(layer, {})

        compatible_terrains = compatibility.get(resource_type, [])
        return terrain_type in compatible_terrains




    def generate_surface_resources(
        self,
        chunk_x: int,
        chunk_y: int,
        layered_terrain_data: Dict[Tuple[int, int], LayeredTerrainData],
        chunk_size: int = 32
    ) -> List[ResourceNode]:
        """
        Generate surface layer resources with renewable characteristics.

        Surface resources include:
        - 🌲 Massive forests (renewable wood)
        - 🌾 Fertile valleys (renewable food)
        - 🪨 Surface quarries (stone)
        - 🐟 Fishing grounds (renewable water resources)
        """
        surface_clusters = self._find_layer_specific_clusters(
            chunk_x * chunk_size, chunk_y * chunk_size, chunk_size, WorldLayer.SURFACE
        )

        valid_clusters = self._filter_clusters_by_layer_terrain(
            surface_clusters, layered_terrain_data,
            chunk_x * chunk_size, chunk_y * chunk_size, chunk_size, WorldLayer.SURFACE
        )

        surface_nodes = []
        for cluster in valid_clusters:
            nodes = self._populate_layer_cluster(
                cluster, layered_terrain_data,
                chunk_x * chunk_size, chunk_y * chunk_size, chunk_size, WorldLayer.SURFACE
            )
            surface_nodes.extend(nodes)

        return surface_nodes

    def generate_underground_resources(
        self,
        chunk_x: int,
        chunk_y: int,
        layered_terrain_data: Dict[Tuple[int, int], LayeredTerrainData],
        chunk_size: int = 32
    ) -> List[ResourceNode]:
        """
        Generate underground layer resources with finite, high-value characteristics.

        Underground resources include:
        - 💰 Rich gold veins
        - ⛏️ Dense iron mines
        - 🔥 Coal seams
        - 💎 Gem caverns
        - 🔮 Crystal caves
        - 💧 Underground springs
        """
        underground_clusters = self._find_layer_specific_clusters(
            chunk_x * chunk_size, chunk_y * chunk_size, chunk_size, WorldLayer.UNDERGROUND
        )

        valid_clusters = self._filter_clusters_by_layer_terrain(
            underground_clusters, layered_terrain_data,
            chunk_x * chunk_size, chunk_y * chunk_size, chunk_size, WorldLayer.UNDERGROUND
        )

        underground_nodes = []
        for cluster in valid_clusters:
            nodes = self._populate_layer_cluster(
                cluster, layered_terrain_data,
                chunk_x * chunk_size, chunk_y * chunk_size, chunk_size, WorldLayer.UNDERGROUND
            )
            underground_nodes.extend(nodes)

        return underground_nodes

    def generate_mountain_resources(
        self,
        chunk_x: int,
        chunk_y: int,
        layered_terrain_data: Dict[Tuple[int, int], LayeredTerrainData],
        chunk_size: int = 32
    ) -> List[ResourceNode]:
        """
        Generate mountain layer resources with high-quality, dangerous access characteristics.

        Mountain resources include:
        - 🏔️ Massive quarries
        - ⚡ Surface metal deposits
        - 💎 Mountain gems
        - ❄️ Eternal ice
        """
        mountain_clusters = self._find_layer_specific_clusters(
            chunk_x * chunk_size, chunk_y * chunk_size, chunk_size, WorldLayer.MOUNTAINS
        )

        valid_clusters = self._filter_clusters_by_layer_terrain(
            mountain_clusters, layered_terrain_data,
            chunk_x * chunk_size, chunk_y * chunk_size, chunk_size, WorldLayer.MOUNTAINS
        )

        mountain_nodes = []
        for cluster in valid_clusters:
            nodes = self._populate_layer_cluster(
                cluster, layered_terrain_data,
                chunk_x * chunk_size, chunk_y * chunk_size, chunk_size, WorldLayer.MOUNTAINS
            )
            mountain_nodes.extend(nodes)

        return mountain_nodes


def create_default_resource_generator(seed: Optional[int] = None) -> ClusteredResourceGenerator:
    """
    Create a resource generator with default settings.

    Args:
        seed: Optional seed for reproducible generation

    Returns:
        ClusteredResourceGenerator instance
    """
    if seed is None:
        seed = random.randint(0, 2**31 - 1)
    return ClusteredResourceGenerator(seed)
