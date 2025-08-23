"""
Configuration constants for resource generation system.

This module contains all the configuration parameters, compatibility rules,
and tuning constants for the resource generation system.
"""

from typing import Dict, List, Set
from .layered import WorldLayer
from .resource_types import ResourceType
from .terrain import TerrainType


# Terrain compatibility rules by layer and resource type
TERRAIN_COMPATIBILITY = {
    WorldLayer.SURFACE: {
        ResourceType.WOOD: [
            TerrainType.GRASS,
            TerrainType.LIGHT_GRASS,
            TerrainType.DARK_GRASS,
            TerrainType.FOREST
        ],
        ResourceType.FOOD_SURFACE: [
            TerrainType.FERTILE,
            TerrainType.GRASS,
            TerrainType.LIGHT_GRASS,
            TerrainType.DARK_GRASS,
            TerrainType.FOREST
        ],
        ResourceType.STONE_SURFACE: [
            TerrainType.HILLS,
            TerrainType.GRASS,
            TerrainType.LIGHT_GRASS,
            TerrainType.MOUNTAINS
        ],
        ResourceType.WATER: [
            TerrainType.SHALLOW_WATER,
            TerrainType.SWAMP,
            TerrainType.DEEP_WATER
        ]
    },
    WorldLayer.UNDERGROUND: {
        ResourceType.GOLD: [
            TerrainType.CAVES,
            TerrainType.CAVE_FLOOR
        ],
        ResourceType.IRON: [
            TerrainType.CAVES,
            TerrainType.CAVE_FLOOR
        ],
        ResourceType.COAL: [
            TerrainType.CAVES,
            TerrainType.CAVE_FLOOR
        ],
        ResourceType.GEMS: [
            TerrainType.CAVES,
            TerrainType.CAVE_FLOOR
        ],
        ResourceType.CRYSTAL: [
            TerrainType.CAVES,
            TerrainType.CAVE_FLOOR
        ],
        ResourceType.UNDERGROUND_WATER: [
            TerrainType.CAVES,
            TerrainType.CAVE_FLOOR,
            TerrainType.UNDERGROUND_WATER
        ]
    },
    WorldLayer.MOUNTAINS: {
        ResourceType.STONE_MOUNTAIN: [
            TerrainType.MOUNTAINS,
            TerrainType.MOUNTAIN_PEAK,
            TerrainType.MOUNTAIN_SLOPE
        ],
        ResourceType.METAL_MOUNTAIN: [
            TerrainType.MOUNTAINS,
            TerrainType.MOUNTAIN_PEAK,
            TerrainType.MOUNTAIN_SLOPE
        ],
        ResourceType.RARE_GEMS: [
            TerrainType.MOUNTAINS,
            TerrainType.MOUNTAIN_PEAK
        ],
        ResourceType.ICE: [
            TerrainType.MOUNTAINS,
            TerrainType.MOUNTAIN_PEAK,
            TerrainType.SNOW
        ]
    }
}


# Layer-specific generation parameters
LAYER_GENERATION_CONFIG = {
    WorldLayer.SURFACE: {
        'sample_step': 6,        # More frequent surface resources
        'noise_offset': 0,
        'threshold': 0.3,        # Easier to find surface resources
        'radius_base': 10,       # Large clusters (forests, fields)
        'radius_scale': 15,
        'density_base': 0.15,    # Moderate density
        'density_scale': 0.25,
        'description': 'Renewable resources with easy access'
    },
    WorldLayer.UNDERGROUND: {
        'sample_step': 10,       # Sparser underground resources
        'noise_offset': 1000,
        'threshold': 0.5,        # Underground resources are rarer
        'radius_base': 6,        # Smaller, dense clusters (rich veins)
        'radius_scale': 8,
        'density_base': 0.25,    # High density
        'density_scale': 0.35,
        'description': 'Finite but valuable resources requiring cave access'
    },
    WorldLayer.MOUNTAINS: {
        'sample_step': 8,        # Medium mountain resources
        'noise_offset': 2000,
        'threshold': 0.4,        # Mountain resources moderately rare
        'radius_base': 8,        # Medium size clusters (quarries, peaks)
        'radius_scale': 10,
        'density_base': 0.2,     # High density
        'density_scale': 0.3,
        'description': 'High-quality resources with dangerous access'
    }
}


# Resource type distribution by layer and noise thresholds
RESOURCE_TYPE_DISTRIBUTION = {
    WorldLayer.SURFACE: {
        # Rich surface areas (noise > 0.7)
        'rich': {
            0.3: ResourceType.WOOD,           # Dense forests
            0.0: ResourceType.FOOD_SURFACE,   # Fertile valleys
            -1.0: ResourceType.STONE_SURFACE  # Surface quarries
        },
        # Common surface areas (noise <= 0.7)
        'common': {
            0.0: ResourceType.WOOD,
            -1.0: ResourceType.FOOD_SURFACE
        }
    },
    WorldLayer.UNDERGROUND: {
        # Very rich underground (noise > 0.8)
        'very_rich': {
            0.5: ResourceType.CRYSTAL,        # Rare magical crystals
            0.0: ResourceType.GOLD,           # Gold veins
            -1.0: ResourceType.GEMS           # Gem deposits
        },
        # Rich underground (0.6 < noise <= 0.8)
        'rich': {
            0.3: ResourceType.GOLD,
            0.0: ResourceType.IRON,
            -1.0: ResourceType.COAL
        },
        # Common underground (noise <= 0.6)
        'common': {
            0.5: ResourceType.IRON,
            0.0: ResourceType.COAL,
            -1.0: ResourceType.UNDERGROUND_WATER
        }
    },
    WorldLayer.MOUNTAINS: {
        # Rich mountain areas (noise > 0.7)
        'rich': {
            0.5: ResourceType.RARE_GEMS,      # Mountain gem veins
            0.0: ResourceType.METAL_MOUNTAIN, # Surface metal deposits
            -1.0: ResourceType.STONE_MOUNTAIN # Massive quarries
        },
        # Common mountain areas (noise <= 0.7)
        'common': {
            0.3: ResourceType.STONE_MOUNTAIN,
            0.0: ResourceType.ICE,            # High altitude ice
            -1.0: ResourceType.METAL_MOUNTAIN
        }
    }
}


# Noise generation configuration
NOISE_CONFIG = {
    'cluster': {
        'octaves': 3,
        'frequency': 0.003,      # How spread out cluster centers are
        'persistence': 0.6
    },
    'density': {
        'octaves': 2,
        'frequency': 0.02,       # Variation within clusters
        'persistence': 0.5
    },
    'rarity': {
        'octaves': 2,
        'frequency': 0.05,       # Fine-grained rarity variation
        'persistence': 0.4
    }
}


# Rarity thresholds
RARITY_THRESHOLDS = {
    'epic': 0.8,
    'rare': 0.6,
    'common': 0.0
}


# Spawn probability configuration
SPAWN_CONFIG = {
    'base_threshold': 0.3,       # Minimum probability to spawn resource
    'noise_variation': 0.2,      # How much noise affects spawn probability
    'distance_factor_weight': 1.0 # How much distance from cluster center matters
}


# Performance optimization settings
PERFORMANCE_CONFIG = {
    'max_cluster_radius': 25,    # Maximum cluster radius to prevent performance issues
    'min_cluster_radius': 3,     # Minimum cluster radius for meaningful clusters
    'chunk_search_radius_multiplier': 0.5,  # How far beyond chunk to search for clusters
    'terrain_sample_step': 2,    # Step size when sampling terrain for compatibility
    'max_sample_radius': 5       # Maximum radius to sample around cluster center
}


def get_terrain_compatibility(layer: WorldLayer, resource_type: ResourceType) -> List[TerrainType]:
    """Get compatible terrain types for a resource on a specific layer."""
    return TERRAIN_COMPATIBILITY.get(layer, {}).get(resource_type, [])


def get_layer_config(layer: WorldLayer) -> Dict:
    """Get generation configuration for a specific layer."""
    return LAYER_GENERATION_CONFIG.get(layer, {})


def get_resource_distribution(layer: WorldLayer) -> Dict:
    """Get resource type distribution rules for a specific layer."""
    return RESOURCE_TYPE_DISTRIBUTION.get(layer, {})


def is_terrain_compatible(layer: WorldLayer, resource_type: ResourceType, terrain_type: TerrainType) -> bool:
    """Check if a terrain type is compatible with a resource type on a specific layer."""
    compatible_terrains = get_terrain_compatibility(layer, resource_type)
    return terrain_type in compatible_terrains


def get_rarity_from_score(score: float) -> str:
    """Convert a rarity score to a rarity string."""
    if score > RARITY_THRESHOLDS['epic']:
        return 'epic'
    elif score > RARITY_THRESHOLDS['rare']:
        return 'rare'
    else:
        return 'common'


def should_spawn_resource(probability: float) -> bool:
    """Determine if a resource should spawn based on probability."""
    return probability > SPAWN_CONFIG['base_threshold']
