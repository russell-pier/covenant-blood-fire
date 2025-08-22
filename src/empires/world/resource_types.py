"""
Resource type definitions for the layered world resource generation system.

This module defines the core data structures and enums for resource generation
across the three world layers (Surface, Underground, Mountains).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple, Optional


class ResourceType(Enum):
    """Enumeration of all resource types across the three world layers."""
    
    # SURFACE LAYER resources (renewable, easy access)
    WOOD = "wood"                    # Trees, lumber - 🌲
    FOOD_SURFACE = "food_surface"    # Berries, crops, animals - 🌾
    STONE_SURFACE = "stone_surface"  # Surface rocks, small quarries - 🪨
    WATER = "water"                  # Fish, kelp - 🐟
    
    # UNDERGROUND LAYER resources (finite, valuable, requires cave access)
    GOLD = "gold"                    # Gold veins, nuggets - 💰
    IRON = "iron"                    # Iron ore deposits - ⛏️
    COAL = "coal"                    # Coal seams for fuel/smelting - 🔥
    GEMS = "gems"                    # Precious stones - 💎
    CRYSTAL = "crystal"              # Magic crystals, rare minerals - 🔮
    UNDERGROUND_WATER = "underground_water"  # Springs, underground lakes - 💧
    
    # MOUNTAIN LAYER resources (high-quality, dangerous access)
    STONE_MOUNTAIN = "stone_mountain"  # Large stone quarries - 🏔️
    METAL_MOUNTAIN = "metal_mountain"  # Surface metal deposits - ⚡
    RARE_GEMS = "rare_gems"           # Mountain gem deposits - 💎
    ICE = "ice"                       # High altitude ice/snow - ❄️


@dataclass
class ResourceCluster:
    """Defines a resource-rich area with specific characteristics."""
    center_x: int
    center_y: int
    resource_type: ResourceType
    radius: float
    density: float      # 0.0 to 1.0, how packed with resources
    intensity: float    # How valuable the resources are
    layer: 'WorldLayer'  # Which world layer this cluster belongs to


@dataclass
class ResourceNode:
    """Individual resource node on the map."""
    x: int
    y: int
    resource_type: ResourceType
    char: str
    yield_amount: int
    respawns: bool      # Whether this resource regenerates over time
    rarity: str         # 'common', 'rare', 'epic'
    fg_color: Tuple[int, int, int]  # Foreground color (RGB)
    bg_color: Optional[Tuple[int, int, int]] = None  # Background color (RGB), None to use terrain


# Resource character mappings by layer and rarity (ASCII characters for compatibility)
RESOURCE_CHARACTERS = {
    # SURFACE LAYER
    ResourceType.WOOD: {
        'common': ['T', 't', 'Y'],          # Tree symbols
        'rare': ['T', 'Y', 'I'],           # Larger tree symbols
        'epic': ['T', 'Y', 'I']            # Epic tree symbols
    },
    ResourceType.FOOD_SURFACE: {
        'common': ['*', 'o', 'O'],         # Food symbols
        'rare': ['*', 'O', '@'],          # Larger food symbols
        'epic': ['@', '*', 'O']           # Epic food symbols
    },
    ResourceType.STONE_SURFACE: {
        'common': ['^', 'A', 'n'],         # Stone symbols
        'rare': ['^', 'A', 'M'],          # Larger stone symbols
        'epic': ['^', 'A', 'M']           # Epic stone symbols
    },
    ResourceType.WATER: {
        'common': ['~', '=', '-'],         # Water life symbols
        'rare': ['~', '=', 'w'],          # Larger water symbols
        'epic': ['~', '=', 'W']           # Epic water symbols
    },

    # UNDERGROUND LAYER
    ResourceType.GOLD: {
        'common': ['$', '*', '+'],         # Gold symbols
        'rare': ['$', '*', '#'],          # Larger gold symbols
        'epic': ['$', '#', '@']           # Epic gold symbols
    },
    ResourceType.IRON: {
        'common': ['#', 'H', 'X'],         # Iron symbols
        'rare': ['#', 'H', 'X'],          # Larger iron symbols
        'epic': ['#', 'H', 'X']           # Epic iron symbols
    },
    ResourceType.COAL: {
        'common': ['C', 'c', 'o'],         # Coal symbols
        'rare': ['C', 'c', 'O'],          # Larger coal symbols
        'epic': ['C', 'O', '@']           # Epic coal symbols
    },
    ResourceType.GEMS: {
        'common': ['*', 'o', '+'],         # Gem symbols
        'rare': ['*', 'O', '#'],          # Larger gem symbols
        'epic': ['*', '@', '#']           # Epic gem symbols
    },
    ResourceType.CRYSTAL: {
        'common': ['+', '*', 'x'],         # Crystal symbols
        'rare': ['+', '*', 'X'],          # Larger crystal symbols
        'epic': ['+', '*', 'X']           # Epic crystal symbols
    },
    ResourceType.UNDERGROUND_WATER: {
        'common': ['~', '=', '-'],          # Water symbols
        'rare': ['~', '=', 'w'],           # Larger water symbols
        'epic': ['~', '=', 'W']            # Epic water symbols
    },

    # MOUNTAIN LAYER
    ResourceType.STONE_MOUNTAIN: {
        'common': ['^', 'A', 'M'],         # Mountain stone symbols
        'rare': ['^', 'A', 'M'],          # Larger mountain stone symbols
        'epic': ['^', 'A', 'M']           # Epic mountain stone symbols
    },
    ResourceType.METAL_MOUNTAIN: {
        'common': ['#', 'H', 'X'],         # Mountain metal symbols
        'rare': ['#', 'H', 'X'],          # Larger mountain metal symbols
        'epic': ['#', 'H', 'X']           # Epic mountain metal symbols
    },
    ResourceType.RARE_GEMS: {
        'common': ['*', 'o', '+'],         # Mountain gem symbols
        'rare': ['*', 'O', '#'],          # Larger mountain gem symbols
        'epic': ['*', '@', '#']           # Epic mountain gem symbols
    },
    ResourceType.ICE: {
        'common': ['*', 'o', '+'],         # Ice symbols
        'rare': ['*', 'O', 'i'],          # Larger ice symbols
        'epic': ['*', 'I', '@']           # Epic ice symbols
    }
}


# Resource colors that stand out against terrain backgrounds
RESOURCE_COLORS = {
    # SURFACE LAYER - Colors that stand out on grass/forest backgrounds
    ResourceType.WOOD: {
        'foreground': (101, 67, 33),       # Darker brown - more realistic tree color
        'background': None                  # Use terrain background
    },
    ResourceType.FOOD_SURFACE: {
        'foreground': (255, 140, 0),       # Dark orange - stands out on green
        'background': None
    },
    ResourceType.STONE_SURFACE: {
        'foreground': (169, 169, 169),     # Dark gray - stands out on grass
        'background': None
    },
    ResourceType.WATER: {
        'foreground': (0, 191, 255),       # Deep sky blue - stands out on water
        'background': None
    },

    # UNDERGROUND LAYER - Colors that stand out on dark cave backgrounds
    ResourceType.GOLD: {
        'foreground': (255, 215, 0),       # Gold - bright yellow stands out on dark
        'background': None
    },
    ResourceType.IRON: {
        'foreground': (70, 130, 180),      # Steel blue - stands out on brown caves
        'background': None
    },
    ResourceType.COAL: {
        'foreground': (105, 105, 105),     # Dim gray - lighter than cave background
        'background': None
    },
    ResourceType.GEMS: {
        'foreground': (255, 20, 147),      # Deep pink - vibrant against dark
        'background': None
    },
    ResourceType.CRYSTAL: {
        'foreground': (138, 43, 226),      # Blue violet - magical purple
        'background': None
    },
    ResourceType.UNDERGROUND_WATER: {
        'foreground': (0, 255, 255),       # Cyan - bright blue for underground water
        'background': None
    },

    # MOUNTAIN LAYER - Colors that stand out on gray mountain backgrounds
    ResourceType.STONE_MOUNTAIN: {
        'foreground': (210, 180, 140),     # Tan - warm color on gray mountains
        'background': None
    },
    ResourceType.METAL_MOUNTAIN: {
        'foreground': (192, 192, 192),     # Silver - metallic shine on mountains
        'background': None
    },
    ResourceType.RARE_GEMS: {
        'foreground': (255, 0, 255),       # Magenta - rare gem color
        'background': None
    },
    ResourceType.ICE: {
        'foreground': (240, 248, 255),     # Alice blue - ice white on gray
        'background': None
    }
}


# Resource yield amounts by rarity
RESOURCE_YIELDS = {
    'common': 1,
    'rare': 2,
    'epic': 4
}


# Resource economic values by layer and rarity
RESOURCE_VALUES = {
    # Surface resources: Low individual value, high sustainability
    ResourceType.WOOD: {'common': 1, 'rare': 2, 'epic': 4},
    ResourceType.FOOD_SURFACE: {'common': 1, 'rare': 2, 'epic': 3},
    ResourceType.STONE_SURFACE: {'common': 1, 'rare': 2, 'epic': 3},
    ResourceType.WATER: {'common': 1, 'rare': 2, 'epic': 3},
    
    # Underground resources: High individual value, finite supply
    ResourceType.GOLD: {'common': 5, 'rare': 10, 'epic': 20},
    ResourceType.IRON: {'common': 3, 'rare': 6, 'epic': 12},
    ResourceType.COAL: {'common': 2, 'rare': 4, 'epic': 8},
    ResourceType.GEMS: {'common': 8, 'rare': 16, 'epic': 32},
    ResourceType.CRYSTAL: {'common': 15, 'rare': 30, 'epic': 60},
    ResourceType.UNDERGROUND_WATER: {'common': 2, 'rare': 4, 'epic': 6},
    
    # Mountain resources: Premium value, quality bonus multipliers
    ResourceType.STONE_MOUNTAIN: {'common': 2, 'rare': 5, 'epic': 10},
    ResourceType.METAL_MOUNTAIN: {'common': 4, 'rare': 8, 'epic': 16},
    ResourceType.RARE_GEMS: {'common': 12, 'rare': 25, 'epic': 50},
    ResourceType.ICE: {'common': 3, 'rare': 6, 'epic': 12}
}


# Renewable resource types (regrow over time)
RENEWABLE_RESOURCES = {
    ResourceType.WOOD,
    ResourceType.FOOD_SURFACE,
    ResourceType.WATER,
    ResourceType.UNDERGROUND_WATER,
    ResourceType.ICE
}


def get_resource_layer(resource_type: ResourceType) -> 'WorldLayer':
    """Get the world layer for a given resource type."""
    from .layered import WorldLayer
    
    surface_resources = {
        ResourceType.WOOD, ResourceType.FOOD_SURFACE, 
        ResourceType.STONE_SURFACE, ResourceType.WATER
    }
    underground_resources = {
        ResourceType.GOLD, ResourceType.IRON, ResourceType.COAL,
        ResourceType.GEMS, ResourceType.CRYSTAL, ResourceType.UNDERGROUND_WATER
    }
    mountain_resources = {
        ResourceType.STONE_MOUNTAIN, ResourceType.METAL_MOUNTAIN,
        ResourceType.RARE_GEMS, ResourceType.ICE
    }
    
    if resource_type in surface_resources:
        return WorldLayer.SURFACE
    elif resource_type in underground_resources:
        return WorldLayer.UNDERGROUND
    elif resource_type in mountain_resources:
        return WorldLayer.MOUNTAINS
    else:
        raise ValueError(f"Unknown resource type: {resource_type}")


def is_renewable(resource_type: ResourceType) -> bool:
    """Check if a resource type is renewable."""
    return resource_type in RENEWABLE_RESOURCES


def get_resource_value(resource_type: ResourceType, rarity: str) -> int:
    """Get the economic value of a resource by type and rarity."""
    return RESOURCE_VALUES.get(resource_type, {}).get(rarity, 1)


def get_resource_colors(resource_type: ResourceType) -> Tuple[Tuple[int, int, int], Optional[Tuple[int, int, int]]]:
    """
    Get the foreground and background colors for a resource type.

    Args:
        resource_type: The resource type

    Returns:
        Tuple of (foreground_color, background_color). Background may be None to use terrain color.
    """
    color_info = RESOURCE_COLORS.get(resource_type, {})
    fg_color = color_info.get('foreground', (255, 255, 255))  # Default to white
    bg_color = color_info.get('background', None)  # Default to None (use terrain)
    return fg_color, bg_color


def get_resource_character_and_color(resource_type: ResourceType, rarity: str) -> Tuple[str, Tuple[int, int, int], Optional[Tuple[int, int, int]]]:
    """
    Get a random character and colors for a resource type and rarity.

    Args:
        resource_type: The resource type
        rarity: The rarity level ('common', 'rare', 'epic')

    Returns:
        Tuple of (character, foreground_color, background_color)
    """
    import random

    # Get character
    chars = RESOURCE_CHARACTERS.get(resource_type, {}).get(rarity, ['○'])
    char = random.choice(chars)

    # Get colors and make them brighter/bolder
    fg_color, bg_color = get_resource_colors(resource_type)

    # Make colors brighter to simulate bold effect
    bold_fg_color = _make_color_bold(fg_color)

    return char, bold_fg_color, bg_color


def _make_color_bold(color: Tuple[int, int, int]) -> Tuple[int, int, int]:
    """
    Make a color appear bolder by increasing brightness while maintaining hue.

    Args:
        color: RGB color tuple

    Returns:
        Brighter version of the color
    """
    r, g, b = color

    # Increase brightness by 20% but cap at 255
    bold_r = min(255, int(r * 1.2))
    bold_g = min(255, int(g * 1.2))
    bold_b = min(255, int(b * 1.2))

    # Ensure minimum brightness for visibility
    if bold_r + bold_g + bold_b < 150:  # If too dark
        bold_r = min(255, bold_r + 50)
        bold_g = min(255, bold_g + 50)
        bold_b = min(255, bold_b + 50)

    return (bold_r, bold_g, bold_b)
