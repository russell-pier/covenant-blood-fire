"""
Resource balance configuration for gameplay tuning.

This module provides easy-to-adjust parameters for balancing the resource
generation system for optimal gameplay experience.
"""

from typing import Dict
from .layered import WorldLayer
from .resource_types import ResourceType


# Global resource generation settings
GLOBAL_RESOURCE_SETTINGS = {
    'enable_resources': True,
    'resource_density_multiplier': 1.0,  # Global multiplier for all resource generation
    'cluster_size_multiplier': 1.0,      # Global multiplier for cluster sizes
    'rarity_boost': 0.0,                 # Boost to rarity calculations (0.0 = normal, 0.1 = 10% boost)
}


# Layer-specific balance settings
LAYER_BALANCE = {
    WorldLayer.SURFACE: {
        'spawn_rate_multiplier': 1.0,     # How often surface resources spawn
        'cluster_size_multiplier': 1.0,   # Size of surface resource clusters
        'density_multiplier': 1.0,        # Density within clusters
        'renewable_rate': 1.0,            # How fast renewable resources regrow
        'description': 'Sustainable early-game resources'
    },
    WorldLayer.UNDERGROUND: {
        'spawn_rate_multiplier': 0.8,     # Underground resources are rarer
        'cluster_size_multiplier': 0.7,   # Smaller but denser clusters
        'density_multiplier': 1.3,        # Higher density to compensate
        'value_multiplier': 2.0,          # Underground resources worth more
        'description': 'Valuable finite resources requiring cave access'
    },
    WorldLayer.MOUNTAINS: {
        'spawn_rate_multiplier': 0.6,     # Mountain resources are rarest
        'cluster_size_multiplier': 0.9,   # Medium-sized clusters
        'density_multiplier': 1.2,        # High density
        'value_multiplier': 3.0,          # Premium value
        'quality_bonus': 1.5,             # Quality multiplier for mountain resources
        'description': 'Premium quality resources with dangerous access'
    }
}


# Resource type specific balance
RESOURCE_TYPE_BALANCE = {
    # Surface resources - renewable and sustainable
    ResourceType.WOOD: {
        'spawn_rate': 1.2,        # Wood is common
        'cluster_size': 1.5,      # Large forest clusters
        'regrow_time': 100,       # Time to regrow (game ticks)
        'strategic_value': 'low'
    },
    ResourceType.FOOD_SURFACE: {
        'spawn_rate': 1.1,
        'cluster_size': 1.2,
        'regrow_time': 80,
        'strategic_value': 'low'
    },
    ResourceType.STONE_SURFACE: {
        'spawn_rate': 0.9,
        'cluster_size': 1.0,
        'regrow_time': None,      # Stone doesn't regrow
        'strategic_value': 'medium'
    },
    ResourceType.WATER: {
        'spawn_rate': 0.8,
        'cluster_size': 1.3,
        'regrow_time': 50,        # Fish populations recover
        'strategic_value': 'medium'
    },
    
    # Underground resources - finite but valuable
    ResourceType.GOLD: {
        'spawn_rate': 0.3,        # Very rare
        'cluster_size': 0.7,      # Small rich veins
        'base_value': 10,
        'strategic_value': 'high'
    },
    ResourceType.IRON: {
        'spawn_rate': 0.5,
        'cluster_size': 0.8,
        'base_value': 6,
        'strategic_value': 'high'
    },
    ResourceType.COAL: {
        'spawn_rate': 0.6,
        'cluster_size': 0.9,
        'base_value': 4,
        'strategic_value': 'medium'
    },
    ResourceType.GEMS: {
        'spawn_rate': 0.2,        # Rare
        'cluster_size': 0.6,
        'base_value': 15,
        'strategic_value': 'high'
    },
    ResourceType.CRYSTAL: {
        'spawn_rate': 0.1,        # Very rare
        'cluster_size': 0.5,
        'base_value': 25,
        'strategic_value': 'critical'
    },
    ResourceType.UNDERGROUND_WATER: {
        'spawn_rate': 0.4,
        'cluster_size': 1.0,
        'regrow_time': 200,       # Slow aquifer recharge
        'strategic_value': 'medium'
    },
    
    # Mountain resources - premium quality
    ResourceType.STONE_MOUNTAIN: {
        'spawn_rate': 0.4,
        'cluster_size': 1.8,      # Massive quarries
        'base_value': 8,
        'quality_multiplier': 2.0,
        'strategic_value': 'high'
    },
    ResourceType.METAL_MOUNTAIN: {
        'spawn_rate': 0.3,
        'cluster_size': 1.0,
        'base_value': 12,
        'quality_multiplier': 1.8,
        'strategic_value': 'high'
    },
    ResourceType.RARE_GEMS: {
        'spawn_rate': 0.15,       # Very rare
        'cluster_size': 0.8,
        'base_value': 30,
        'quality_multiplier': 2.5,
        'strategic_value': 'critical'
    },
    ResourceType.ICE: {
        'spawn_rate': 0.5,
        'cluster_size': 1.2,
        'regrow_time': 300,       # Slow glacial formation
        'strategic_value': 'medium'
    }
}


# Rarity distribution settings
RARITY_BALANCE = {
    'common': {
        'probability': 0.7,       # 70% of resources are common
        'yield_multiplier': 1.0,
        'value_multiplier': 1.0
    },
    'rare': {
        'probability': 0.25,      # 25% of resources are rare
        'yield_multiplier': 1.5,
        'value_multiplier': 2.0
    },
    'epic': {
        'probability': 0.05,      # 5% of resources are epic
        'yield_multiplier': 2.5,
        'value_multiplier': 4.0
    }
}


# Economic progression settings
ECONOMIC_PROGRESSION = {
    'early_game': {
        'focus': 'surface_resources',
        'key_resources': [ResourceType.WOOD, ResourceType.FOOD_SURFACE],
        'description': 'Survival and basic settlement building'
    },
    'mid_game': {
        'focus': 'underground_resources',
        'key_resources': [ResourceType.IRON, ResourceType.COAL, ResourceType.GOLD],
        'description': 'Military expansion and technological advancement'
    },
    'late_game': {
        'focus': 'mountain_resources',
        'key_resources': [ResourceType.STONE_MOUNTAIN, ResourceType.RARE_GEMS, ResourceType.CRYSTAL],
        'description': 'Massive construction and advanced civilization'
    }
}


def get_balanced_spawn_rate(resource_type: ResourceType, layer: WorldLayer) -> float:
    """Get the balanced spawn rate for a resource type on a specific layer."""
    global_multiplier = GLOBAL_RESOURCE_SETTINGS['resource_density_multiplier']
    layer_multiplier = LAYER_BALANCE.get(layer, {}).get('spawn_rate_multiplier', 1.0)
    resource_rate = RESOURCE_TYPE_BALANCE.get(resource_type, {}).get('spawn_rate', 1.0)
    
    return global_multiplier * layer_multiplier * resource_rate


def get_balanced_cluster_size(resource_type: ResourceType, layer: WorldLayer) -> float:
    """Get the balanced cluster size for a resource type on a specific layer."""
    global_multiplier = GLOBAL_RESOURCE_SETTINGS['cluster_size_multiplier']
    layer_multiplier = LAYER_BALANCE.get(layer, {}).get('cluster_size_multiplier', 1.0)
    resource_size = RESOURCE_TYPE_BALANCE.get(resource_type, {}).get('cluster_size', 1.0)
    
    return global_multiplier * layer_multiplier * resource_size


def get_balanced_value(resource_type: ResourceType, layer: WorldLayer, rarity: str) -> int:
    """Get the balanced economic value for a resource."""
    base_value = RESOURCE_TYPE_BALANCE.get(resource_type, {}).get('base_value', 1)
    layer_multiplier = LAYER_BALANCE.get(layer, {}).get('value_multiplier', 1.0)
    rarity_multiplier = RARITY_BALANCE.get(rarity, {}).get('value_multiplier', 1.0)
    quality_multiplier = RESOURCE_TYPE_BALANCE.get(resource_type, {}).get('quality_multiplier', 1.0)
    
    return int(base_value * layer_multiplier * rarity_multiplier * quality_multiplier)


def get_strategic_importance(resource_type: ResourceType) -> str:
    """Get the strategic importance level of a resource type."""
    return RESOURCE_TYPE_BALANCE.get(resource_type, {}).get('strategic_value', 'low')


def apply_balance_to_generator(generator):
    """Apply balance settings to a resource generator instance."""
    # Apply global settings
    if not GLOBAL_RESOURCE_SETTINGS['enable_resources']:
        return
    
    # Apply layer-specific balance
    for layer, balance in LAYER_BALANCE.items():
        if layer in generator.layer_config:
            config = generator.layer_config[layer]
            
            # Adjust thresholds based on spawn rate multipliers
            spawn_multiplier = balance.get('spawn_rate_multiplier', 1.0)
            config['threshold'] *= (2.0 - spawn_multiplier)  # Lower threshold = more spawns
            
            # Adjust cluster sizes
            size_multiplier = balance.get('cluster_size_multiplier', 1.0)
            config['radius_base'] *= size_multiplier
            config['radius_scale'] *= size_multiplier
            
            # Adjust density
            density_multiplier = balance.get('density_multiplier', 1.0)
            config['density_base'] *= density_multiplier
            config['density_scale'] *= density_multiplier


# Preset balance configurations for different gameplay styles
BALANCE_PRESETS = {
    'default': {
        'description': 'Balanced gameplay with strategic resource management',
        'settings': GLOBAL_RESOURCE_SETTINGS.copy()
    },
    'abundant': {
        'description': 'More resources for casual gameplay',
        'settings': {
            **GLOBAL_RESOURCE_SETTINGS,
            'resource_density_multiplier': 1.5,
            'cluster_size_multiplier': 1.3
        }
    },
    'scarce': {
        'description': 'Fewer resources for challenging gameplay',
        'settings': {
            **GLOBAL_RESOURCE_SETTINGS,
            'resource_density_multiplier': 0.7,
            'cluster_size_multiplier': 0.8
        }
    },
    'hardcore': {
        'description': 'Very limited resources for expert players',
        'settings': {
            **GLOBAL_RESOURCE_SETTINGS,
            'resource_density_multiplier': 0.5,
            'cluster_size_multiplier': 0.6,
            'rarity_boost': -0.1  # Fewer rare resources
        }
    }
}
