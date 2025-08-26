"""
Centralized tile mapping system for the 3-tiered world generation.

This module provides a unified tile configuration system that maps terrain types
to visual representations across all three scales: World, Regional, and Local.
Based on examples/tilemap.py but integrated with the new architecture.
"""

import random
from enum import Enum
from dataclasses import dataclass
from typing import Tuple, Dict, List, Optional

from .scale_types import ViewScale


@dataclass
class TileConfig:
    """Configuration for a single tile type"""
    char: str
    fg_color: Tuple[int, int, int]  # RGB text color
    bg_color: Tuple[int, int, int]  # RGB background color
    variants: Optional[List['TileConfig']] = None  # Alternative versions
    description: str = ""


class ColorPalette:
    """Centralized color palette for consistent theming"""
    
    # === BASE COLORS ===
    # Greens (vegetation)
    DARK_GREEN = (0, 80, 0)
    FOREST_GREEN = (0, 100, 0) 
    MEDIUM_GREEN = (50, 150, 50)
    BRIGHT_GREEN = (80, 200, 80)
    LIME_GREEN = (120, 255, 120)
    PALE_GREEN = (150, 255, 150)
    
    # Browns (earth, wood)
    DARK_BROWN = (101, 67, 33)
    MEDIUM_BROWN = (139, 69, 19)
    LIGHT_BROWN = (160, 82, 45)
    TAN = (210, 180, 140)
    SAND = (238, 203, 173)
    
    # Grays (stone, metal)
    DARK_GRAY = (64, 64, 64)
    MEDIUM_GRAY = (128, 128, 128)
    LIGHT_GRAY = (192, 192, 192)
    STONE_GRAY = (169, 169, 169)
    CHARCOAL = (54, 54, 54)
    
    # Blues (water)
    DEEP_BLUE = (0, 50, 150)
    OCEAN_BLUE = (25, 75, 150)
    WATER_BLUE = (50, 100, 200)
    LIGHT_BLUE = (100, 150, 255)
    SKY_BLUE = (173, 216, 230)
    PALE_BLUE = (200, 230, 255)
    
    # Desert colors
    DESERT_SAND = (238, 203, 173)
    DESERT_TAN = (218, 165, 32)
    DESERT_BROWN = (184, 134, 11)
    CACTUS_GREEN = (107, 142, 35)
    
    # Mountain colors  
    MOUNTAIN_GRAY = (120, 100, 80)
    MOUNTAIN_BROWN = (139, 90, 43)
    SNOW_WHITE = (240, 240, 255)
    ICE_BLUE = (200, 230, 255)
    
    # Special colors
    GOLD = (255, 215, 0)
    COPPER = (184, 115, 51)
    IRON = (128, 128, 128)
    SILVER = (192, 192, 192)
    
    # Organic colors
    FLOWER_PINK = (255, 192, 203)
    FLOWER_YELLOW = (255, 255, 0)
    BERRY_RED = (220, 20, 60)
    MUSHROOM_BROWN = (160, 82, 45)
    
    # Darkness levels
    BLACK = (0, 0, 0)
    VERY_DARK = (20, 20, 20)
    DARK = (40, 40, 40)
    DIM = (60, 60, 60)
    
    @staticmethod
    def shade(color: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
        """Shade a color darker (factor < 1) or lighter (factor > 1)"""
        return tuple(max(0, min(255, int(c * factor))) for c in color)
    
    @staticmethod
    def tint(base_color: Tuple[int, int, int], tint_color: Tuple[int, int, int], 
             strength: float = 0.1) -> Tuple[int, int, int]:
        """Apply a color tint to a base color"""
        return tuple(
            max(0, min(255, int(base * (1 - strength) + tint * strength)))
            for base, tint in zip(base_color, tint_color)
        )
    
    @staticmethod
    def random_variation(color: Tuple[int, int, int], variance: int = 15) -> Tuple[int, int, int]:
        """Add random variation to a color"""
        return tuple(
            max(0, min(255, c + random.randint(-variance, variance)))
            for c in color
        )


# Biome types for world scale
class BiomeType(Enum):
    # Ocean biomes
    DEEP_OCEAN = "deep_ocean"
    SHALLOW_SEA = "shallow_sea"
    COASTAL_WATERS = "coastal_waters"
    
    # Land biomes
    POLAR_ICE = "polar_ice"
    TUNDRA = "tundra"
    TAIGA = "taiga"
    TEMPERATE_FOREST = "temperate_forest"
    GRASSLAND = "grassland"
    DESERT = "desert"
    TROPICAL_FOREST = "tropical_forest"
    SAVANNA = "savanna"
    WETLAND = "wetland"
    
    # Mountain biomes
    HIGH_MOUNTAINS = "high_mountains"
    MOUNTAIN_FOREST = "mountain_forest"
    MOUNTAIN_DESERT = "mountain_desert"


# Regional terrain subtypes
class TerrainSubtype(Enum):
    # GRASSLAND subtypes
    PLAINS = "plains"
    ROLLING_HILLS = "rolling_hills"
    MEADOWS = "meadows"
    SHRUBLAND = "shrubland"
    
    # FOREST subtypes
    DENSE_FOREST = "dense_forest"
    LIGHT_WOODLAND = "light_woodland"
    FOREST_CLEARING = "forest_clearing"
    OLD_GROWTH = "old_growth"
    
    # DESERT subtypes
    SAND_DUNES = "sand_dunes"
    ROCKY_DESERT = "rocky_desert"
    BADLANDS = "badlands"
    OASIS = "oasis"
    
    # MOUNTAIN subtypes
    STEEP_SLOPES = "steep_slopes"
    GENTLE_SLOPES = "gentle_slopes"
    MOUNTAIN_VALLEY = "mountain_valley"
    ALPINE_MEADOW = "alpine_meadow"
    CLIFFS = "cliffs"
    
    # WATER subtypes
    DEEP_WATER = "deep_water"
    SHALLOW_WATER = "shallow_water"
    RAPIDS = "rapids"
    CALM_POOLS = "calm_pools"
    
    # WETLAND subtypes
    MARSH = "marsh"
    SWAMP = "swamp"
    BOG = "bog"
    FLOODPLAIN = "floodplain"
    
    # TUNDRA subtypes
    PERMAFROST = "permafrost"
    TUNDRA_HILLS = "tundra_hills"
    ICE_FIELDS = "ice_fields"


# Local terrain types
class LocalTerrain(Enum):
    # Ground surfaces
    DIRT_PATH = "dirt_path"
    GRASS_PATCH = "grass_patch"
    BARE_EARTH = "bare_earth"
    ROCKY_GROUND = "rocky_ground"
    SANDY_SOIL = "sandy_soil"
    MUDDY_GROUND = "muddy_ground"
    MOSS_COVERED = "moss_covered"
    LEAF_LITTER = "leaf_litter"
    
    # Vegetation
    TALL_GRASS = "tall_grass"
    SHORT_GRASS = "short_grass"
    WILDFLOWERS = "wildflowers"
    THORNY_BUSHES = "thorny_bushes"
    BERRY_BUSHES = "berry_bushes"
    YOUNG_TREES = "young_trees"
    MATURE_TREES = "mature_trees"
    FALLEN_LOG = "fallen_log"
    
    # Rock formations
    SMALL_BOULDER = "small_boulder"
    LARGE_BOULDER = "large_boulder"
    ROCK_OUTCROP = "rock_outcrop"
    LOOSE_STONES = "loose_stones"
    PEBBLES = "pebbles"
    
    # Water features
    SHALLOW_WATER = "shallow_water"
    DEEP_WATER = "deep_water"
    WATER_EDGE = "water_edge"
    MUDDY_BANK = "muddy_bank"
    REED_BEDS = "reed_beds"


class TileLibrary:
    """Complete library of all tile configurations organized hierarchically"""
    
    def __init__(self):
        self.tiles = {}
        self._initialize_tile_library()
    
    def _initialize_tile_library(self):
        """Initialize complete tile library"""
        
        # ========================================
        # WORLD SCALE TILES (128x96 world map)
        # ========================================
        
        self.tiles[ViewScale.WORLD] = {
            # Ocean biomes
            BiomeType.DEEP_OCEAN: TileConfig(
                "~", ColorPalette.LIGHT_BLUE, ColorPalette.DEEP_BLUE,
                description="Deep ocean waters"
            ),
            BiomeType.SHALLOW_SEA: TileConfig(
                "≈", ColorPalette.SKY_BLUE, ColorPalette.OCEAN_BLUE,
                description="Shallow coastal seas"
            ),
            BiomeType.COASTAL_WATERS: TileConfig(
                "∼", ColorPalette.PALE_BLUE, ColorPalette.WATER_BLUE,
                description="Near-shore waters"
            ),
            
            # Land biomes
            BiomeType.POLAR_ICE: TileConfig(
                "*", ColorPalette.SNOW_WHITE, ColorPalette.ICE_BLUE,
                description="Polar ice caps"
            ),
            BiomeType.TUNDRA: TileConfig(
                "∘", ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.7), 
                ColorPalette.shade(ColorPalette.LIGHT_GRAY, 0.8),
                description="Arctic tundra"
            ),
            BiomeType.TAIGA: TileConfig(
                "♠", ColorPalette.FOREST_GREEN, ColorPalette.DARK_GREEN,
                description="Northern coniferous forests"
            ),
            BiomeType.TEMPERATE_FOREST: TileConfig(
                "♣", ColorPalette.MEDIUM_GREEN, ColorPalette.FOREST_GREEN,
                description="Temperate deciduous forests"
            ),
            BiomeType.GRASSLAND: TileConfig(
                "\"", ColorPalette.BRIGHT_GREEN, ColorPalette.MEDIUM_GREEN,
                description="Temperate grasslands"
            ),
            BiomeType.DESERT: TileConfig(
                "·", ColorPalette.DESERT_TAN, ColorPalette.DESERT_BROWN,
                description="Hot desert regions"
            ),
            BiomeType.TROPICAL_FOREST: TileConfig(
                "♠", ColorPalette.LIME_GREEN, ColorPalette.CACTUS_GREEN,
                description="Tropical rainforests"
            ),
            BiomeType.SAVANNA: TileConfig(
                "'", ColorPalette.shade(ColorPalette.BRIGHT_GREEN, 0.8), 
                ColorPalette.shade(ColorPalette.TAN, 1.1),
                description="Tropical grasslands with scattered trees"
            ),
            BiomeType.WETLAND: TileConfig(
                "≋", ColorPalette.tint(ColorPalette.MEDIUM_GREEN, ColorPalette.WATER_BLUE),
                ColorPalette.tint(ColorPalette.DARK_GREEN, ColorPalette.DEEP_BLUE),
                description="Marshes and wetlands"
            ),
            
            # Mountain biomes
            BiomeType.HIGH_MOUNTAINS: TileConfig(
                "▲", ColorPalette.LIGHT_GRAY, ColorPalette.MOUNTAIN_GRAY,
                description="High mountain peaks"
            ),
            BiomeType.MOUNTAIN_FOREST: TileConfig(
                "^", ColorPalette.FOREST_GREEN, ColorPalette.MOUNTAIN_BROWN,
                description="Forested mountain slopes"
            ),
            BiomeType.MOUNTAIN_DESERT: TileConfig(
                "^", ColorPalette.TAN, ColorPalette.DESERT_BROWN,
                description="Arid mountain regions"
            )
        }

        # ========================================
        # REGIONAL SCALE TILES (32x32 regional map)
        # ========================================

        self.tiles[ViewScale.REGIONAL] = {
            # GRASSLAND subtypes
            TerrainSubtype.PLAINS: TileConfig(
                ".", ColorPalette.MEDIUM_GREEN, ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.6),
                variants=[
                    TileConfig("·", ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 1.1), ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.6)),
                    TileConfig(",", ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.9), ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.6)),
                ],
                description="Open plains with short grass"
            ),
            TerrainSubtype.ROLLING_HILLS: TileConfig(
                "∩", ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.8), ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.5),
                variants=[
                    TileConfig("⩙", ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.9), ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.5)),
                    TileConfig("∪", ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.7), ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.5)),
                ],
                description="Gently rolling grassy hills"
            ),
            TerrainSubtype.MEADOWS: TileConfig(
                "\"", ColorPalette.BRIGHT_GREEN, ColorPalette.MEDIUM_GREEN,
                variants=[
                    TileConfig("'", ColorPalette.shade(ColorPalette.BRIGHT_GREEN, 1.1), ColorPalette.MEDIUM_GREEN),
                    TileConfig("'", ColorPalette.shade(ColorPalette.BRIGHT_GREEN, 0.9), ColorPalette.MEDIUM_GREEN),
                ],
                description="Lush meadows with tall grass"
            ),
            TerrainSubtype.SHRUBLAND: TileConfig(
                "≡", ColorPalette.tint(ColorPalette.MEDIUM_GREEN, ColorPalette.MEDIUM_BROWN, 0.3),
                ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.7),
                variants=[
                    TileConfig("⌐", ColorPalette.tint(ColorPalette.MEDIUM_GREEN, ColorPalette.MEDIUM_BROWN, 0.2), ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.7)),
                    TileConfig("¬", ColorPalette.tint(ColorPalette.MEDIUM_GREEN, ColorPalette.MEDIUM_BROWN, 0.4), ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.7)),
                ],
                description="Shrubland with scattered bushes"
            ),

            # FOREST subtypes
            TerrainSubtype.DENSE_FOREST: TileConfig(
                "♠", ColorPalette.DARK_GREEN, ColorPalette.shade(ColorPalette.DARK_GREEN, 0.6),
                variants=[
                    TileConfig("♣", ColorPalette.shade(ColorPalette.DARK_GREEN, 1.1), ColorPalette.shade(ColorPalette.DARK_GREEN, 0.6)),
                    TileConfig("♧", ColorPalette.shade(ColorPalette.DARK_GREEN, 0.9), ColorPalette.shade(ColorPalette.DARK_GREEN, 0.6)),
                ],
                description="Dense forest canopy"
            ),
            TerrainSubtype.LIGHT_WOODLAND: TileConfig(
                "♣", ColorPalette.FOREST_GREEN, ColorPalette.shade(ColorPalette.FOREST_GREEN, 0.6),
                variants=[
                    TileConfig("♪", ColorPalette.shade(ColorPalette.FOREST_GREEN, 1.1), ColorPalette.shade(ColorPalette.FOREST_GREEN, 0.6)),
                    TileConfig("♫", ColorPalette.shade(ColorPalette.FOREST_GREEN, 0.9), ColorPalette.shade(ColorPalette.FOREST_GREEN, 0.6)),
                ],
                description="Light woodland with clearings"
            ),
            TerrainSubtype.FOREST_CLEARING: TileConfig(
                "∘", ColorPalette.BRIGHT_GREEN, ColorPalette.MEDIUM_GREEN,
                variants=[
                    TileConfig("○", ColorPalette.shade(ColorPalette.BRIGHT_GREEN, 1.1), ColorPalette.MEDIUM_GREEN),
                    TileConfig("◦", ColorPalette.shade(ColorPalette.BRIGHT_GREEN, 0.9), ColorPalette.MEDIUM_GREEN),
                ],
                description="Forest clearings and glades"
            ),
            TerrainSubtype.OLD_GROWTH: TileConfig(
                "♠", ColorPalette.shade(ColorPalette.DARK_GREEN, 0.8), ColorPalette.shade(ColorPalette.DARK_GREEN, 0.5),
                variants=[
                    TileConfig("♠", ColorPalette.shade(ColorPalette.DARK_GREEN, 0.7), ColorPalette.shade(ColorPalette.DARK_GREEN, 0.5)),
                    TileConfig("♠", ColorPalette.shade(ColorPalette.DARK_GREEN, 0.9), ColorPalette.shade(ColorPalette.DARK_GREEN, 0.5)),
                ],
                description="Ancient old-growth forest"
            ),

            # DESERT subtypes
            TerrainSubtype.SAND_DUNES: TileConfig(
                "∼", ColorPalette.SAND, ColorPalette.DESERT_TAN,
                variants=[
                    TileConfig("≈", ColorPalette.shade(ColorPalette.SAND, 1.1), ColorPalette.DESERT_TAN),
                    TileConfig("~", ColorPalette.shade(ColorPalette.SAND, 0.9), ColorPalette.DESERT_TAN),
                ],
                description="Rolling sand dunes"
            ),
            TerrainSubtype.ROCKY_DESERT: TileConfig(
                "◦", ColorPalette.TAN, ColorPalette.DESERT_BROWN,
                variants=[
                    TileConfig("∘", ColorPalette.shade(ColorPalette.TAN, 1.1), ColorPalette.DESERT_BROWN),
                    TileConfig("·", ColorPalette.shade(ColorPalette.TAN, 0.9), ColorPalette.DESERT_BROWN),
                ],
                description="Rocky desert terrain"
            ),
            TerrainSubtype.BADLANDS: TileConfig(
                "≋", ColorPalette.MEDIUM_BROWN, ColorPalette.DESERT_BROWN,
                variants=[
                    TileConfig("≈", ColorPalette.shade(ColorPalette.MEDIUM_BROWN, 1.1), ColorPalette.DESERT_BROWN),
                    TileConfig("∼", ColorPalette.shade(ColorPalette.MEDIUM_BROWN, 0.9), ColorPalette.DESERT_BROWN),
                ],
                description="Eroded badlands"
            ),
            TerrainSubtype.OASIS: TileConfig(
                "◯", ColorPalette.LIME_GREEN, ColorPalette.tint(ColorPalette.DESERT_TAN, ColorPalette.MEDIUM_GREEN, 0.3),
                description="Desert oasis"
            )
        }

        # ========================================
        # LOCAL SCALE TILES (32x32 meter map)
        # ========================================

        self.tiles[ViewScale.LOCAL] = {
            # Ground surfaces
            LocalTerrain.DIRT_PATH: TileConfig(
                ".", ColorPalette.MEDIUM_BROWN, ColorPalette.DARK_BROWN,
                variants=[
                    TileConfig("·", ColorPalette.shade(ColorPalette.MEDIUM_BROWN, 1.1), ColorPalette.DARK_BROWN),
                    TileConfig("∘", ColorPalette.shade(ColorPalette.MEDIUM_BROWN, 0.9), ColorPalette.DARK_BROWN),
                ],
                description="Worn dirt path"
            ),
            LocalTerrain.GRASS_PATCH: TileConfig(
                ".", ColorPalette.MEDIUM_GREEN, ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.6),
                variants=[
                    TileConfig("·", ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 1.1), ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.6)),
                    TileConfig(",", ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.9), ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.6)),
                    TileConfig("'", ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 1.05), ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.6)),
                    TileConfig("`", ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.95), ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.6)),
                ],
                description="Patches of grass"
            ),
            LocalTerrain.BARE_EARTH: TileConfig(
                ".", ColorPalette.LIGHT_BROWN, ColorPalette.MEDIUM_BROWN,
                variants=[
                    TileConfig("·", ColorPalette.shade(ColorPalette.LIGHT_BROWN, 1.1), ColorPalette.MEDIUM_BROWN),
                    TileConfig("∘", ColorPalette.shade(ColorPalette.LIGHT_BROWN, 0.9), ColorPalette.MEDIUM_BROWN),
                ],
                description="Bare earth and soil"
            ),
            LocalTerrain.ROCKY_GROUND: TileConfig(
                "∘", ColorPalette.MEDIUM_GRAY, ColorPalette.shade(ColorPalette.MEDIUM_GRAY, 0.7),
                variants=[
                    TileConfig("·", ColorPalette.shade(ColorPalette.MEDIUM_GRAY, 1.1), ColorPalette.shade(ColorPalette.MEDIUM_GRAY, 0.7)),
                    TileConfig("°", ColorPalette.shade(ColorPalette.MEDIUM_GRAY, 0.9), ColorPalette.shade(ColorPalette.MEDIUM_GRAY, 0.7)),
                ],
                description="Rocky ground surface"
            ),

            # Vegetation
            LocalTerrain.TALL_GRASS: TileConfig(
                "|", ColorPalette.BRIGHT_GREEN, ColorPalette.MEDIUM_GREEN,
                variants=[
                    TileConfig("┃", ColorPalette.shade(ColorPalette.BRIGHT_GREEN, 1.1), ColorPalette.MEDIUM_GREEN),
                    TileConfig("∣", ColorPalette.shade(ColorPalette.BRIGHT_GREEN, 0.9), ColorPalette.MEDIUM_GREEN),
                    TileConfig("│", ColorPalette.shade(ColorPalette.BRIGHT_GREEN, 1.05), ColorPalette.MEDIUM_GREEN),
                ],
                description="Tall grass stalks"
            ),
            LocalTerrain.SHORT_GRASS: TileConfig(
                "'", ColorPalette.MEDIUM_GREEN, ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.7),
                variants=[
                    TileConfig("`", ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 1.1), ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.7)),
                    TileConfig(",", ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.9), ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.7)),
                    TileConfig(".", ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 1.05), ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.7)),
                ],
                description="Short grass coverage"
            ),
            LocalTerrain.WILDFLOWERS: TileConfig(
                "*", ColorPalette.FLOWER_PINK, ColorPalette.MEDIUM_GREEN,
                variants=[
                    TileConfig("❀", ColorPalette.FLOWER_YELLOW, ColorPalette.MEDIUM_GREEN),
                    TileConfig("✿", ColorPalette.FLOWER_PINK, ColorPalette.MEDIUM_GREEN),
                    TileConfig("❁", ColorPalette.shade(ColorPalette.FLOWER_PINK, 0.8), ColorPalette.MEDIUM_GREEN),
                    TileConfig("✾", ColorPalette.FLOWER_YELLOW, ColorPalette.MEDIUM_GREEN),
                ],
                description="Wild flowering plants"
            ),
            LocalTerrain.MATURE_TREES: TileConfig(
                "♠", ColorPalette.DARK_GREEN, ColorPalette.shade(ColorPalette.DARK_GREEN, 0.6),
                variants=[
                    TileConfig("♣", ColorPalette.shade(ColorPalette.DARK_GREEN, 1.1), ColorPalette.shade(ColorPalette.DARK_GREEN, 0.6)),
                    TileConfig("♧", ColorPalette.shade(ColorPalette.DARK_GREEN, 0.9), ColorPalette.shade(ColorPalette.DARK_GREEN, 0.6)),
                    TileConfig("♤", ColorPalette.shade(ColorPalette.DARK_GREEN, 1.05), ColorPalette.shade(ColorPalette.DARK_GREEN, 0.6)),
                ],
                description="Large mature trees"
            ),

            # Rock formations
            LocalTerrain.SMALL_BOULDER: TileConfig(
                "○", ColorPalette.LIGHT_GRAY, ColorPalette.MEDIUM_GRAY,
                variants=[
                    TileConfig("◯", ColorPalette.shade(ColorPalette.LIGHT_GRAY, 1.1), ColorPalette.MEDIUM_GRAY),
                    TileConfig("◦", ColorPalette.shade(ColorPalette.LIGHT_GRAY, 0.9), ColorPalette.MEDIUM_GRAY),
                ],
                description="Small boulders and rocks"
            ),
            LocalTerrain.LARGE_BOULDER: TileConfig(
                "●", ColorPalette.MEDIUM_GRAY, ColorPalette.DARK_GRAY,
                variants=[
                    TileConfig("⬤", ColorPalette.shade(ColorPalette.MEDIUM_GRAY, 1.1), ColorPalette.DARK_GRAY),
                    TileConfig("◉", ColorPalette.shade(ColorPalette.MEDIUM_GRAY, 0.9), ColorPalette.DARK_GRAY),
                ],
                description="Large boulders and rock formations"
            ),

            # Water features
            LocalTerrain.SHALLOW_WATER: TileConfig(
                "∼", ColorPalette.SKY_BLUE, ColorPalette.WATER_BLUE,
                variants=[
                    TileConfig("≈", ColorPalette.shade(ColorPalette.SKY_BLUE, 1.1), ColorPalette.WATER_BLUE),
                    TileConfig("~", ColorPalette.shade(ColorPalette.SKY_BLUE, 0.9), ColorPalette.WATER_BLUE),
                ],
                description="Shallow water areas"
            ),
            LocalTerrain.DEEP_WATER: TileConfig(
                "≈", ColorPalette.WATER_BLUE, ColorPalette.DEEP_BLUE,
                variants=[
                    TileConfig("~", ColorPalette.shade(ColorPalette.WATER_BLUE, 1.1), ColorPalette.DEEP_BLUE),
                    TileConfig("∼", ColorPalette.shade(ColorPalette.WATER_BLUE, 0.9), ColorPalette.DEEP_BLUE),
                ],
                description="Deep water bodies"
            )
        }

    def get_tile(self, scale: ViewScale, tile_type, use_variant: bool = True) -> TileConfig:
        """Get tile configuration, optionally using a random variant"""
        if scale not in self.tiles or tile_type not in self.tiles[scale]:
            # Return fallback tile
            return TileConfig("?", ColorPalette.SNOW_WHITE, ColorPalette.BLACK,
                            description=f"Unknown tile: {scale.value}.{tile_type}")

        base_tile = self.tiles[scale][tile_type]

        if use_variant and base_tile.variants and random.random() < 0.3:  # 30% chance for variant
            return random.choice(base_tile.variants)

        return base_tile

    def get_tile_with_variation(self, scale: ViewScale, tile_type,
                              color_variance: int = 10) -> TileConfig:
        """Get tile with random color variation"""
        base_tile = self.get_tile(scale, tile_type, use_variant=True)

        # Apply color variation
        varied_fg = ColorPalette.random_variation(base_tile.fg_color, color_variance)
        varied_bg = ColorPalette.random_variation(base_tile.bg_color, color_variance)

        return TileConfig(
            base_tile.char,
            varied_fg,
            varied_bg,
            base_tile.variants,
            base_tile.description
        )

    def get_available_tiles(self, scale: ViewScale) -> List:
        """Get list of available tile types for a scale"""
        return list(self.tiles.get(scale, {}).keys())

    def has_tile(self, scale: ViewScale, tile_type) -> bool:
        """Check if a tile type exists for a scale"""
        return scale in self.tiles and tile_type in self.tiles[scale]


# Global tile library instance
TILE_LIBRARY = TileLibrary()


def get_tile(scale: ViewScale, tile_type, use_variant: bool = True) -> TileConfig:
    """Convenience function to get a tile from the global library"""
    return TILE_LIBRARY.get_tile(scale, tile_type, use_variant)


def get_tile_with_variation(scale: ViewScale, tile_type, color_variance: int = 10) -> TileConfig:
    """Convenience function to get a tile with color variation"""
    return TILE_LIBRARY.get_tile_with_variation(scale, tile_type, color_variance)
