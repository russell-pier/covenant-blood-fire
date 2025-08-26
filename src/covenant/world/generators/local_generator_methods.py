"""
Additional methods for the Local Scale Generator.

This module contains the remaining methods for resource placement, animal spawns,
movement costs, and display generation for the local generator.
"""

import random
from typing import List, Dict

from ..data.tilemap import LocalTerrain, get_tile
from ..data.scale_types import ViewScale
from .regional_generator import RegionalTile, TerrainSubtype

# Import enums that we need
try:
    from .local_generator import ResourceType, AnimalSpawnType, StructuralFeature, ResourceCluster, AnimalSpawnArea
except ImportError:
    # Define placeholder enums for when local_generator isn't fully loaded yet
    from enum import Enum

    class ResourceType(Enum):
        BERRIES = "berries"
        NUTS = "nuts"
        HERBS = "herbs"
        MUSHROOMS = "mushrooms"
        HONEY = "honey"
        GAME_TRAIL = "game_trail"
        FISH = "fish"
        BRANCHES = "branches"
        LOGS = "logs"
        BARK = "bark"
        REEDS = "reeds"
        CLAY = "clay"
        FLINT = "flint"
        STONES = "stones"
        IRON_ORE = "iron_ore"
        COPPER_ORE = "copper_ore"
        SALT = "salt"
        GEMS = "gems"
        COAL = "coal"
        FRESH_WATER = "fresh_water"
        MINERAL_WATER = "mineral_water"

    class AnimalSpawnType(Enum):
        SMALL_GAME = "small_game"
        LARGE_GAME = "large_game"
        PREDATORS = "predators"
        LIVESTOCK = "livestock"
        FISH = "fish"
        INSECTS = "insects"

    class StructuralFeature(Enum):
        CAVE_MOUTH = "cave_mouth"
        MOUNTAIN_LEDGE = "mountain_ledge"
        CLIFF_FACE = "cliff_face"
        NATURAL_RAMP = "natural_ramp"
        TREE_TRUNK = "tree_trunk"
        ROCK_PILE = "rock_pile"
        WATER_FORD = "water_ford"
        FALLEN_TREE_BRIDGE = "fallen_tree_bridge"

    # Simple dataclass replacements
    class ResourceCluster:
        def __init__(self, resource_type, center_x, center_y, radius, density, quality):
            self.resource_type = resource_type
            self.center_x = center_x
            self.center_y = center_y
            self.radius = radius
            self.density = density
            self.quality = quality

    class AnimalSpawnArea:
        def __init__(self, spawn_type, center_x, center_y, radius, population_capacity, preferred_terrain):
            self.spawn_type = spawn_type
            self.center_x = center_x
            self.center_y = center_y
            self.radius = radius
            self.population_capacity = population_capacity
            self.preferred_terrain = preferred_terrain

# Use string annotations to avoid circular imports
from typing import Any


def place_harvestable_resources(generator, local_map: List[List[Any]],
                               regional_tile: RegionalTile):
    """Place harvestable resources throughout the local area"""
    generator.resource_clusters = []
    
    # Generate resource clusters first
    _generate_resource_clusters(generator, regional_tile)
    
    # Apply resource clusters to tiles
    for y in range(generator.chunk_size):
        for x in range(generator.chunk_size):
            tile = local_map[y][x]
            
            # Check if tile is in a resource cluster
            for cluster in generator.resource_clusters:
                distance = ((x - cluster.center_x)**2 + (y - cluster.center_y)**2)**0.5
                if distance <= cluster.radius:
                    if random.random() < cluster.density:
                        tile.harvestable_resource = cluster.resource_type
                        tile.resource_quantity = int(cluster.quality * 5) + 1
                        tile.resource_respawn_time = _get_resource_respawn_time(cluster.resource_type)
            
            # Individual resource placement based on terrain
            if not tile.harvestable_resource and random.random() < 0.1:
                resource = _select_terrain_resource(tile.sub_terrain, regional_tile)
                if resource:
                    tile.harvestable_resource = resource
                    tile.resource_quantity = random.randint(1, 3)
                    tile.resource_respawn_time = _get_resource_respawn_time(resource)


def _generate_resource_clusters(generator, regional_tile: RegionalTile):
    """Generate resource clusters based on regional tile properties"""
    cluster_probability = 0.3
    
    # Increase probability based on regional resource concentration
    if regional_tile.resource_concentration:
        cluster_probability += 0.4
    
    num_clusters = 0
    for _ in range(generator.max_resource_clusters):
        if random.random() < cluster_probability:
            num_clusters += 1
    
    # Place clusters
    for cluster_id in range(num_clusters):
        attempts = 0
        while attempts < 15:
            center_x = random.uniform(2, generator.chunk_size - 2)
            center_y = random.uniform(2, generator.chunk_size - 2)
            radius = random.uniform(1.5, 4.0)
            
            # Check for conflicts with existing clusters
            conflict = False
            for existing_cluster in generator.resource_clusters:
                distance = ((center_x - existing_cluster.center_x)**2 + 
                           (center_y - existing_cluster.center_y)**2)**0.5
                if distance < (radius + existing_cluster.radius + 1):
                    conflict = True
                    break
            
            if not conflict:
                resource_type = _select_cluster_resource_type(regional_tile)
                if resource_type:
                    cluster = ResourceCluster(
                        resource_type=resource_type,
                        center_x=center_x,
                        center_y=center_y,
                        radius=radius,
                        density=random.uniform(0.3, 0.8),
                        quality=random.uniform(0.4, 1.0)
                    )
                    generator.resource_clusters.append(cluster)
                break
            
            attempts += 1


def _select_cluster_resource_type(regional_tile: RegionalTile) -> ResourceType:
    """Select appropriate resource type for cluster based on regional context"""
    terrain = regional_tile.terrain_subtype
    
    # Terrain-specific resource clusters
    if terrain in [TerrainSubtype.DENSE_FOREST, TerrainSubtype.OLD_GROWTH]:
        return random.choice([ResourceType.LOGS, ResourceType.BRANCHES, ResourceType.NUTS])
    elif terrain in [TerrainSubtype.LIGHT_WOODLAND, TerrainSubtype.FOREST_CLEARING]:
        return random.choice([ResourceType.BRANCHES, ResourceType.BERRIES, ResourceType.HERBS])
    elif terrain in [TerrainSubtype.MEADOWS, TerrainSubtype.PLAINS]:
        return random.choice([ResourceType.HERBS, ResourceType.BERRIES])
    elif terrain in [TerrainSubtype.ROCKY_DESERT, TerrainSubtype.STEEP_SLOPES]:
        return random.choice([ResourceType.STONES, ResourceType.FLINT, ResourceType.IRON_ORE])
    elif terrain in [TerrainSubtype.MARSH, TerrainSubtype.SWAMP]:
        return random.choice([ResourceType.REEDS, ResourceType.CLAY, ResourceType.HERBS])
    elif terrain in [TerrainSubtype.SHALLOW_WATER, TerrainSubtype.DEEP_WATER]:
        return ResourceType.FISH
    
    return ResourceType.HERBS  # Default


def _select_terrain_resource(sub_terrain: LocalTerrain, regional_tile: RegionalTile) -> ResourceType:
    """Select individual resource based on sub-terrain"""
    terrain_resources = {
        LocalTerrain.BERRY_BUSHES: ResourceType.BERRIES,
        LocalTerrain.WILDFLOWERS: ResourceType.HERBS,
        LocalTerrain.FALLEN_LOG: ResourceType.BRANCHES,
        LocalTerrain.MATURE_TREES: ResourceType.LOGS,
        LocalTerrain.YOUNG_TREES: ResourceType.BRANCHES,
        LocalTerrain.LOOSE_STONES: ResourceType.STONES,
        LocalTerrain.PEBBLES: ResourceType.FLINT,
        LocalTerrain.REED_BEDS: ResourceType.REEDS,
        LocalTerrain.MUDDY_GROUND: ResourceType.CLAY,
        LocalTerrain.SHALLOW_WATER: ResourceType.FISH,
        LocalTerrain.DEEP_WATER: ResourceType.FISH,
    }
    
    return terrain_resources.get(sub_terrain)


def _get_resource_respawn_time(resource_type: ResourceType) -> float:
    """Get respawn time in days for resource type"""
    respawn_times = {
        # Renewable resources
        ResourceType.BERRIES: 7.0,
        ResourceType.HERBS: 14.0,
        ResourceType.MUSHROOMS: 3.0,
        ResourceType.FISH: 1.0,
        ResourceType.BRANCHES: 30.0,
        ResourceType.REEDS: 21.0,
        
        # Finite resources
        ResourceType.LOGS: 0.0,  # Don't respawn
        ResourceType.STONES: 0.0,
        ResourceType.FLINT: 0.0,
        ResourceType.CLAY: 0.0,
        ResourceType.IRON_ORE: 0.0,
        ResourceType.COPPER_ORE: 0.0,
        ResourceType.COAL: 0.0,
        ResourceType.GEMS: 0.0,
        ResourceType.SALT: 0.0,
    }
    
    return respawn_times.get(resource_type, 0.0)


def define_animal_spawn_areas(generator, local_map: List[List[Any]],
                             regional_tile: RegionalTile):
    """Define animal spawn areas throughout the local chunk"""
    generator.animal_areas = []
    
    # Generate animal spawn areas
    _generate_animal_areas(generator, regional_tile)
    
    # Apply spawn areas to tiles
    for y in range(generator.chunk_size):
        for x in range(generator.chunk_size):
            tile = local_map[y][x]
            
            # Check if tile is in an animal spawn area
            for area in generator.animal_areas:
                distance = ((x - area.center_x)**2 + (y - area.center_y)**2)**0.5
                if distance <= area.radius:
                    if tile.sub_terrain in area.preferred_terrain:
                        tile.animal_spawn_point = area.spawn_type
                        tile.spawn_frequency = random.uniform(0.1, 0.3)
                        tile.max_animals = random.randint(1, 3)


def _generate_animal_areas(generator, regional_tile: RegionalTile):
    """Generate animal spawn areas based on regional context"""
    area_probability = 0.4
    
    # Increase probability for certain biomes
    if regional_tile.parent_biome.value in ['temperate_forest', 'grassland', 'wetland']:
        area_probability += 0.3
    
    num_areas = 0
    for _ in range(generator.max_animal_areas):
        if random.random() < area_probability:
            num_areas += 1
    
    # Place animal areas
    for area_id in range(num_areas):
        attempts = 0
        while attempts < 10:
            center_x = random.uniform(3, generator.chunk_size - 3)
            center_y = random.uniform(3, generator.chunk_size - 3)
            radius = random.uniform(2.0, 6.0)
            
            # Check for conflicts
            conflict = False
            for existing_area in generator.animal_areas:
                distance = ((center_x - existing_area.center_x)**2 + 
                           (center_y - existing_area.center_y)**2)**0.5
                if distance < (radius + existing_area.radius + 2):
                    conflict = True
                    break
            
            if not conflict:
                spawn_type, preferred_terrain = _select_animal_spawn_type(regional_tile)
                if spawn_type:
                    area = AnimalSpawnArea(
                        spawn_type=spawn_type,
                        center_x=center_x,
                        center_y=center_y,
                        radius=radius,
                        population_capacity=random.randint(3, 8),
                        preferred_terrain=preferred_terrain
                    )
                    generator.animal_areas.append(area)
                break
            
            attempts += 1


def _select_animal_spawn_type(regional_tile: RegionalTile) -> tuple:
    """Select animal spawn type and preferred terrain"""
    terrain = regional_tile.terrain_subtype
    
    if terrain in [TerrainSubtype.DENSE_FOREST, TerrainSubtype.LIGHT_WOODLAND]:
        return AnimalSpawnType.SMALL_GAME, [LocalTerrain.YOUNG_TREES, LocalTerrain.MATURE_TREES, LocalTerrain.LEAF_LITTER]
    elif terrain in [TerrainSubtype.PLAINS, TerrainSubtype.MEADOWS]:
        return AnimalSpawnType.LARGE_GAME, [LocalTerrain.GRASS_PATCH, LocalTerrain.TALL_GRASS]
    elif terrain in [TerrainSubtype.SHALLOW_WATER, TerrainSubtype.DEEP_WATER]:
        return AnimalSpawnType.FISH, [LocalTerrain.SHALLOW_WATER, LocalTerrain.DEEP_WATER]
    elif terrain in [TerrainSubtype.MARSH, TerrainSubtype.SWAMP]:
        return AnimalSpawnType.SMALL_GAME, [LocalTerrain.REED_BEDS, LocalTerrain.MUDDY_GROUND]
    elif terrain == TerrainSubtype.SHRUBLAND:
        return AnimalSpawnType.SMALL_GAME, [LocalTerrain.THORNY_BUSHES, LocalTerrain.BERRY_BUSHES]
    
    return AnimalSpawnType.SMALL_GAME, [LocalTerrain.GRASS_PATCH]


def calculate_movement_costs(generator, local_map: List[List[Any]],
                           regional_tile: RegionalTile):
    """Calculate movement costs and other properties for each tile"""
    for y in range(generator.chunk_size):
        for x in range(generator.chunk_size):
            tile = local_map[y][x]
            
            # Calculate movement cost
            tile.movement_cost = _calculate_movement_cost(tile)
            
            # Calculate concealment
            tile.concealment = _calculate_concealment(tile)


def _calculate_movement_cost(tile: Any) -> float:
    """Calculate movement cost for a tile"""
    base_costs = {
        LocalTerrain.GRASS_PATCH: 1.0,
        LocalTerrain.SHORT_GRASS: 1.0,
        LocalTerrain.TALL_GRASS: 1.2,
        LocalTerrain.BARE_EARTH: 1.1,
        LocalTerrain.DIRT_PATH: 0.8,
        LocalTerrain.ROCKY_GROUND: 1.5,
        LocalTerrain.SANDY_SOIL: 1.3,
        LocalTerrain.MUDDY_GROUND: 2.0,
        LocalTerrain.MOSS_COVERED: 1.1,
        LocalTerrain.LEAF_LITTER: 1.2,
        LocalTerrain.WILDFLOWERS: 1.1,
        LocalTerrain.THORNY_BUSHES: 2.5,
        LocalTerrain.BERRY_BUSHES: 1.8,
        LocalTerrain.YOUNG_TREES: 2.0,
        LocalTerrain.MATURE_TREES: 3.0,  # Blocked
        LocalTerrain.FALLEN_LOG: 2.2,
        LocalTerrain.SMALL_BOULDER: 1.8,
        LocalTerrain.LARGE_BOULDER: 3.0,  # Blocked
        LocalTerrain.ROCK_OUTCROP: 3.0,  # Blocked
        LocalTerrain.LOOSE_STONES: 1.6,
        LocalTerrain.PEBBLES: 1.2,
        LocalTerrain.SHALLOW_WATER: 2.5,
        LocalTerrain.DEEP_WATER: 3.0,  # Blocked
        LocalTerrain.WATER_EDGE: 1.4,
        LocalTerrain.MUDDY_BANK: 1.8,
        LocalTerrain.REED_BEDS: 2.0,
    }
    
    cost = base_costs.get(tile.sub_terrain, 1.0)
    
    # Elevation modifier
    if abs(tile.precise_elevation) > 1.0:
        cost *= 1.2  # Steep areas are harder to traverse
    
    return min(3.0, cost)


def _calculate_concealment(tile: Any) -> float:
    """Calculate concealment value for a tile"""
    concealment_values = {
        LocalTerrain.GRASS_PATCH: 0.1,
        LocalTerrain.SHORT_GRASS: 0.05,
        LocalTerrain.TALL_GRASS: 0.4,
        LocalTerrain.BARE_EARTH: 0.0,
        LocalTerrain.ROCKY_GROUND: 0.2,
        LocalTerrain.MUDDY_GROUND: 0.1,
        LocalTerrain.MOSS_COVERED: 0.3,
        LocalTerrain.LEAF_LITTER: 0.3,
        LocalTerrain.WILDFLOWERS: 0.2,
        LocalTerrain.THORNY_BUSHES: 0.7,
        LocalTerrain.BERRY_BUSHES: 0.6,
        LocalTerrain.YOUNG_TREES: 0.8,
        LocalTerrain.MATURE_TREES: 0.9,
        LocalTerrain.FALLEN_LOG: 0.5,
        LocalTerrain.SMALL_BOULDER: 0.4,
        LocalTerrain.LARGE_BOULDER: 0.6,
        LocalTerrain.ROCK_OUTCROP: 0.7,
        LocalTerrain.LOOSE_STONES: 0.2,
        LocalTerrain.REED_BEDS: 0.8,
    }
    
    return concealment_values.get(tile.sub_terrain, 0.0)


def generate_display_chars(generator, local_map: List[List[Any]]):
    """Generate display characters and colors for each tile"""
    for y in range(generator.chunk_size):
        for x in range(generator.chunk_size):
            tile = local_map[y][x]
            
            # Get tile configuration from tilemap
            tile_config = get_tile(ViewScale.LOCAL, tile.sub_terrain, use_variant=True)
            
            tile.char = tile_config.char
            tile.fg_color = tile_config.fg_color
            tile.bg_color = tile_config.bg_color
            
            # Override for resources
            if tile.harvestable_resource:
                tile.char = _get_resource_char(tile.harvestable_resource)
            
            # Override for structural features
            if tile.structural_feature:
                tile.char = _get_structural_feature_char(tile.structural_feature)


def _get_resource_char(resource: ResourceType) -> str:
    """Get display character for resource"""
    resource_chars = {
        ResourceType.BERRIES: "*",
        ResourceType.NUTS: "°",
        ResourceType.HERBS: "\"",
        ResourceType.MUSHROOMS: "♠",
        ResourceType.BRANCHES: "/",
        ResourceType.LOGS: "=",
        ResourceType.STONES: "○",
        ResourceType.FLINT: "◦",
        ResourceType.CLAY: "■",
        ResourceType.REEDS: "|",
        ResourceType.FISH: "≈",
        ResourceType.IRON_ORE: "●",
        ResourceType.COPPER_ORE: "◉",
    }
    return resource_chars.get(resource, "?")


def _get_structural_feature_char(feature: StructuralFeature) -> str:
    """Get display character for structural feature"""
    feature_chars = {
        StructuralFeature.FALLEN_TREE_BRIDGE: "=",
        StructuralFeature.WATER_FORD: "≈",
        StructuralFeature.ROCK_PILE: "▲",
        StructuralFeature.MOUNTAIN_LEDGE: "^",
        StructuralFeature.NATURAL_RAMP: "/",
    }
    return feature_chars.get(feature, "?")
