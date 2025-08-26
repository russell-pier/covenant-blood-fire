# Complete Hierarchical Tile Mapping Configuration
# Defines visual representation for all terrain types across all three scales

from enum import Enum
from dataclasses import dataclass
from typing import Tuple, Dict, List, Optional
import random

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
        
        self.tiles['world'] = {
            
            # === OCEAN BIOMES ===
            'deep_ocean': TileConfig(
                "~", ColorPalette.LIGHT_BLUE, ColorPalette.DEEP_BLUE,
                description="Deep ocean waters"
            ),
            'shallow_sea': TileConfig(
                "≈", ColorPalette.SKY_BLUE, ColorPalette.OCEAN_BLUE,
                description="Shallow coastal seas"
            ),
            'coastal_waters': TileConfig(
                "∼", ColorPalette.PALE_BLUE, ColorPalette.WATER_BLUE,
                description="Near-shore waters"
            ),
            
            # === LAND BIOMES ===
            'polar_ice': TileConfig(
                "*", ColorPalette.SNOW_WHITE, ColorPalette.ICE_BLUE,
                description="Polar ice caps"
            ),
            'tundra': TileConfig(
                "∘", ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.7), 
                ColorPalette.shade(ColorPalette.LIGHT_GRAY, 0.8),
                description="Arctic tundra"
            ),
            'taiga': TileConfig(
                "♠", ColorPalette.FOREST_GREEN, ColorPalette.DARK_GREEN,
                description="Northern coniferous forests"
            ),
            'temperate_forest': TileConfig(
                "♣", ColorPalette.MEDIUM_GREEN, ColorPalette.FOREST_GREEN,
                description="Temperate deciduous forests"
            ),
            'grassland': TileConfig(
                "\"", ColorPalette.BRIGHT_GREEN, ColorPalette.MEDIUM_GREEN,
                description="Temperate grasslands"
            ),
            'desert': TileConfig(
                "·", ColorPalette.DESERT_TAN, ColorPalette.DESERT_BROWN,
                description="Hot desert regions"
            ),
            'tropical_forest': TileConfig(
                "♠", ColorPalette.LIME_GREEN, ColorPalette.CACTUS_GREEN,
                description="Tropical rainforests"
            ),
            'savanna': TileConfig(
                "'", ColorPalette.shade(ColorPalette.BRIGHT_GREEN, 0.8), 
                ColorPalette.shade(ColorPalette.TAN, 1.1),
                description="Tropical grasslands with scattered trees"
            ),
            'wetland': TileConfig(
                "≋", ColorPalette.tint(ColorPalette.MEDIUM_GREEN, ColorPalette.WATER_BLUE),
                ColorPalette.tint(ColorPalette.DARK_GREEN, ColorPalette.DEEP_BLUE),
                description="Marshes and wetlands"
            ),
            
            # === MOUNTAIN BIOMES ===
            'high_mountains': TileConfig(
                "▲", ColorPalette.LIGHT_GRAY, ColorPalette.MOUNTAIN_GRAY,
                description="High mountain peaks"
            ),
            'mountain_forest': TileConfig(
                "^", ColorPalette.FOREST_GREEN, ColorPalette.MOUNTAIN_BROWN,
                description="Forested mountain slopes"
            ),
            'mountain_desert': TileConfig(
                "^", ColorPalette.TAN, ColorPalette.DESERT_BROWN,
                description="Arid mountain regions"
            )
        }
        
        # ========================================
        # REGIONAL SCALE TILES (32x32 regional map)
        # ========================================
        
        self.tiles['regional'] = {
            
            # === GRASSLAND SUBTYPES ===
            'plains': TileConfig(
                ".", ColorPalette.MEDIUM_GREEN, ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.6),
                variants=[
                    TileConfig("·", ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 1.1), ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.6)),
                    TileConfig(",", ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.9), ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.6)),
                ],
                description="Open plains with short grass"
            ),
            'rolling_hills': TileConfig(
                "∩", ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.8), ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.5),
                variants=[
                    TileConfig("⩙", ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.9), ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.5)),
                    TileConfig("∪", ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.7), ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.5)),
                ],
                description="Gently rolling grassy hills"
            ),
            'meadows': TileConfig(
                "\"", ColorPalette.BRIGHT_GREEN, ColorPalette.MEDIUM_GREEN,
                variants=[
                    TileConfig("'", ColorPalette.shade(ColorPalette.BRIGHT_GREEN, 1.1), ColorPalette.MEDIUM_GREEN),
                    TileConfig("'", ColorPalette.shade(ColorPalette.BRIGHT_GREEN, 0.9), ColorPalette.MEDIUM_GREEN),
                ],
                description="Lush meadows with tall grass"
            ),
            'shrubland': TileConfig(
                "≡", ColorPalette.tint(ColorPalette.MEDIUM_GREEN, ColorPalette.MEDIUM_BROWN, 0.3),
                ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.7),
                variants=[
                    TileConfig("⌐", ColorPalette.tint(ColorPalette.MEDIUM_GREEN, ColorPalette.MEDIUM_BROWN, 0.2), ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.7)),
                    TileConfig("¬", ColorPalette.tint(ColorPalette.MEDIUM_GREEN, ColorPalette.MEDIUM_BROWN, 0.4), ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.7)),
                ],
                description="Shrubland with scattered bushes"
            ),
            
            # === FOREST SUBTYPES ===
            'dense_forest': TileConfig(
                "♠", ColorPalette.DARK_GREEN, ColorPalette.shade(ColorPalette.DARK_GREEN, 0.6),
                variants=[
                    TileConfig("♣", ColorPalette.shade(ColorPalette.DARK_GREEN, 1.1), ColorPalette.shade(ColorPalette.DARK_GREEN, 0.6)),
                    TileConfig("♧", ColorPalette.shade(ColorPalette.DARK_GREEN, 0.9), ColorPalette.shade(ColorPalette.DARK_GREEN, 0.6)),
                ],
                description="Dense forest canopy"
            ),
            'light_woodland': TileConfig(
                "♣", ColorPalette.FOREST_GREEN, ColorPalette.shade(ColorPalette.FOREST_GREEN, 0.6),
                variants=[
                    TileConfig("♪", ColorPalette.shade(ColorPalette.FOREST_GREEN, 1.1), ColorPalette.shade(ColorPalette.FOREST_GREEN, 0.6)),
                    TileConfig("♫", ColorPalette.shade(ColorPalette.FOREST_GREEN, 0.9), ColorPalette.shade(ColorPalette.FOREST_GREEN, 0.6)),
                ],
                description="Light woodland with clearings"
            ),
            'forest_clearing': TileConfig(
                "∘", ColorPalette.BRIGHT_GREEN, ColorPalette.MEDIUM_GREEN,
                variants=[
                    TileConfig("○", ColorPalette.shade(ColorPalette.BRIGHT_GREEN, 1.1), ColorPalette.MEDIUM_GREEN),
                    TileConfig("◦", ColorPalette.shade(ColorPalette.BRIGHT_GREEN, 0.9), ColorPalette.MEDIUM_GREEN),
                ],
                description="Forest clearings and glades"
            ),
            'old_growth': TileConfig(
                "♠", ColorPalette.shade(ColorPalette.DARK_GREEN, 0.8), ColorPalette.shade(ColorPalette.DARK_GREEN, 0.5),
                variants=[
                    TileConfig("♠", ColorPalette.shade(ColorPalette.DARK_GREEN, 0.7), ColorPalette.shade(ColorPalette.DARK_GREEN, 0.5)),
                    TileConfig("♠", ColorPalette.shade(ColorPalette.DARK_GREEN, 0.9), ColorPalette.shade(ColorPalette.DARK_GREEN, 0.5)),
                ],
                description="Ancient old-growth forest"
            ),
            
            # === DESERT SUBTYPES ===
            'sand_dunes': TileConfig(
                "∼", ColorPalette.SAND, ColorPalette.DESERT_TAN,
                variants=[
                    TileConfig("≈", ColorPalette.shade(ColorPalette.SAND, 1.1), ColorPalette.DESERT_TAN),
                    TileConfig("~", ColorPalette.shade(ColorPalette.SAND, 0.9), ColorPalette.DESERT_TAN),
                ],
                description="Rolling sand dunes"
            ),
            'rocky_desert': TileConfig(
                "◦", ColorPalette.TAN, ColorPalette.DESERT_BROWN,
                variants=[
                    TileConfig("∘", ColorPalette.shade(ColorPalette.TAN, 1.1), ColorPalette.DESERT_BROWN),
                    TileConfig("·", ColorPalette.shade(ColorPalette.TAN, 0.9), ColorPalette.DESERT_BROWN),
                ],
                description="Rocky desert terrain"
            ),
            'badlands': TileConfig(
                "≋", ColorPalette.MEDIUM_BROWN, ColorPalette.DESERT_BROWN,
                variants=[
                    TileConfig("≈", ColorPalette.shade(ColorPalette.MEDIUM_BROWN, 1.1), ColorPalette.DESERT_BROWN),
                    TileConfig("∼", ColorPalette.shade(ColorPalette.MEDIUM_BROWN, 0.9), ColorPalette.DESERT_BROWN),
                ],
                description="Eroded badlands"
            ),
            'oasis': TileConfig(
                "◯", ColorPalette.LIME_GREEN, ColorPalette.tint(ColorPalette.DESERT_TAN, ColorPalette.MEDIUM_GREEN, 0.3),
                description="Desert oasis"
            ),
            
            # === MOUNTAIN SUBTYPES ===
            'steep_slopes': TileConfig(
                "/", ColorPalette.MOUNTAIN_GRAY, ColorPalette.shade(ColorPalette.MOUNTAIN_GRAY, 0.7),
                variants=[
                    TileConfig("\\", ColorPalette.MOUNTAIN_GRAY, ColorPalette.shade(ColorPalette.MOUNTAIN_GRAY, 0.7)),
                    TileConfig("|", ColorPalette.MOUNTAIN_GRAY, ColorPalette.shade(ColorPalette.MOUNTAIN_GRAY, 0.7)),
                ],
                description="Steep mountain slopes"
            ),
            'gentle_slopes': TileConfig(
                "^", ColorPalette.shade(ColorPalette.MOUNTAIN_GRAY, 1.2), ColorPalette.MOUNTAIN_GRAY,
                variants=[
                    TileConfig("∩", ColorPalette.shade(ColorPalette.MOUNTAIN_GRAY, 1.1), ColorPalette.MOUNTAIN_GRAY),
                    TileConfig("⌂", ColorPalette.shade(ColorPalette.MOUNTAIN_GRAY, 1.3), ColorPalette.MOUNTAIN_GRAY),
                ],
                description="Gentle mountain slopes"
            ),
            'mountain_valley': TileConfig(
                "∪", ColorPalette.MEDIUM_GREEN, ColorPalette.MOUNTAIN_BROWN,
                description="Mountain valley"
            ),
            'alpine_meadow': TileConfig(
                "\"", ColorPalette.shade(ColorPalette.BRIGHT_GREEN, 0.9), 
                ColorPalette.tint(ColorPalette.MEDIUM_GREEN, ColorPalette.MOUNTAIN_GRAY, 0.2),
                description="High altitude meadows"
            ),
            'cliffs': TileConfig(
                "▓", ColorPalette.MEDIUM_GRAY, ColorPalette.DARK_GRAY,
                variants=[
                    TileConfig("█", ColorPalette.MEDIUM_GRAY, ColorPalette.DARK_GRAY),
                    TileConfig("▒", ColorPalette.MEDIUM_GRAY, ColorPalette.DARK_GRAY),
                ],
                description="Sheer cliff faces"
            ),
            
            # === WATER SUBTYPES ===
            'deep_water': TileConfig(
                "≈", ColorPalette.WATER_BLUE, ColorPalette.DEEP_BLUE,
                variants=[
                    TileConfig("~", ColorPalette.shade(ColorPalette.WATER_BLUE, 1.1), ColorPalette.DEEP_BLUE),
                    TileConfig("∼", ColorPalette.shade(ColorPalette.WATER_BLUE, 0.9), ColorPalette.DEEP_BLUE),
                ],
                description="Deep water bodies"
            ),
            'shallow_water': TileConfig(
                "∼", ColorPalette.LIGHT_BLUE, ColorPalette.WATER_BLUE,
                variants=[
                    TileConfig("≈", ColorPalette.shade(ColorPalette.LIGHT_BLUE, 1.1), ColorPalette.WATER_BLUE),
                    TileConfig("~", ColorPalette.shade(ColorPalette.LIGHT_BLUE, 0.9), ColorPalette.WATER_BLUE),
                ],
                description="Shallow water"
            ),
            'rapids': TileConfig(
                "≋", ColorPalette.SKY_BLUE, ColorPalette.LIGHT_BLUE,
                variants=[
                    TileConfig("≈", ColorPalette.shade(ColorPalette.SKY_BLUE, 1.1), ColorPalette.LIGHT_BLUE),
                    TileConfig("∼", ColorPalette.shade(ColorPalette.SKY_BLUE, 0.9), ColorPalette.LIGHT_BLUE),
                ],
                description="Fast-flowing rapids"
            ),
            'calm_pools': TileConfig(
                "○", ColorPalette.tint(ColorPalette.LIGHT_BLUE, ColorPalette.MEDIUM_GREEN, 0.1), ColorPalette.WATER_BLUE,
                description="Calm water pools"
            ),
            
            # === WETLAND SUBTYPES ===
            'marsh': TileConfig(
                "≈", ColorPalette.tint(ColorPalette.MEDIUM_GREEN, ColorPalette.WATER_BLUE, 0.3),
                ColorPalette.tint(ColorPalette.DARK_GREEN, ColorPalette.DEEP_BLUE, 0.3),
                variants=[
                    TileConfig("∼", ColorPalette.tint(ColorPalette.MEDIUM_GREEN, ColorPalette.WATER_BLUE, 0.2), ColorPalette.tint(ColorPalette.DARK_GREEN, ColorPalette.DEEP_BLUE, 0.3)),
                    TileConfig("≋", ColorPalette.tint(ColorPalette.MEDIUM_GREEN, ColorPalette.WATER_BLUE, 0.4), ColorPalette.tint(ColorPalette.DARK_GREEN, ColorPalette.DEEP_BLUE, 0.3)),
                ],
                description="Marshy wetlands"
            ),
            'swamp': TileConfig(
                "≋", ColorPalette.tint(ColorPalette.FOREST_GREEN, ColorPalette.MEDIUM_BROWN, 0.2),
                ColorPalette.tint(ColorPalette.DARK_GREEN, ColorPalette.DARK_BROWN, 0.2),
                description="Dense swampland"
            ),
            'bog': TileConfig(
                "∼", ColorPalette.tint(ColorPalette.MEDIUM_GREEN, ColorPalette.MEDIUM_BROWN, 0.3),
                ColorPalette.tint(ColorPalette.DARK_GREEN, ColorPalette.DARK_BROWN, 0.3),
                description="Acidic bog areas"
            ),
            'floodplain': TileConfig(
                "\"", ColorPalette.shade(ColorPalette.BRIGHT_GREEN, 0.9),
                ColorPalette.tint(ColorPalette.MEDIUM_GREEN, ColorPalette.MEDIUM_BROWN, 0.1),
                description="Fertile floodplains"
            ),
            
            # === TUNDRA SUBTYPES ===
            'permafrost': TileConfig(
                "·", ColorPalette.shade(ColorPalette.LIGHT_GRAY, 1.1), ColorPalette.shade(ColorPalette.MEDIUM_GRAY, 0.8),
                variants=[
                    TileConfig("∘", ColorPalette.LIGHT_GRAY, ColorPalette.shade(ColorPalette.MEDIUM_GRAY, 0.8)),
                    TileConfig("°", ColorPalette.shade(ColorPalette.LIGHT_GRAY, 0.9), ColorPalette.shade(ColorPalette.MEDIUM_GRAY, 0.8)),
                ],
                description="Frozen ground"
            ),
            'tundra_hills': TileConfig(
                "∩", ColorPalette.shade(ColorPalette.MEDIUM_GRAY, 1.1), ColorPalette.LIGHT_GRAY,
                description="Rolling tundra hills"
            ),
            'ice_fields': TileConfig(
                "*", ColorPalette.SNOW_WHITE, ColorPalette.ICE_BLUE,
                variants=[
                    TileConfig("❄", ColorPalette.SNOW_WHITE, ColorPalette.ICE_BLUE),
                    TileConfig("✦", ColorPalette.SNOW_WHITE, ColorPalette.ICE_BLUE),
                ],
                description="Fields of ice and snow"
            )
        }
        
        # ========================================
        # LOCAL SCALE TILES (32x32 meter map)
        # ========================================
        
        self.tiles['local'] = {
            
            # === GROUND SURFACES ===
            'dirt_path': TileConfig(
                ".", ColorPalette.MEDIUM_BROWN, ColorPalette.DARK_BROWN,
                variants=[
                    TileConfig("·", ColorPalette.shade(ColorPalette.MEDIUM_BROWN, 1.1), ColorPalette.DARK_BROWN),
                    TileConfig("∘", ColorPalette.shade(ColorPalette.MEDIUM_BROWN, 0.9), ColorPalette.DARK_BROWN),
                ],
                description="Worn dirt path"
            ),
            'grass_patch': TileConfig(
                ".", ColorPalette.MEDIUM_GREEN, ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.6),
                variants=[
                    TileConfig("·", ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 1.1), ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.6)),
                    TileConfig(",", ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.9), ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.6)),
                    TileConfig("'", ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 1.05), ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.6)),
                    TileConfig("`", ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.95), ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.6)),
                ],
                description="Patches of grass"
            ),
            'bare_earth': TileConfig(
                ".", ColorPalette.LIGHT_BROWN, ColorPalette.MEDIUM_BROWN,
                variants=[
                    TileConfig("·", ColorPalette.shade(ColorPalette.LIGHT_BROWN, 1.1), ColorPalette.MEDIUM_BROWN),
                    TileConfig("∘", ColorPalette.shade(ColorPalette.LIGHT_BROWN, 0.9), ColorPalette.MEDIUM_BROWN),
                ],
                description="Bare earth and soil"
            ),
            'rocky_ground': TileConfig(
                "∘", ColorPalette.MEDIUM_GRAY, ColorPalette.shade(ColorPalette.MEDIUM_GRAY, 0.7),
                variants=[
                    TileConfig("·", ColorPalette.shade(ColorPalette.MEDIUM_GRAY, 1.1), ColorPalette.shade(ColorPalette.MEDIUM_GRAY, 0.7)),
                    TileConfig("°", ColorPalette.shade(ColorPalette.MEDIUM_GRAY, 0.9), ColorPalette.shade(ColorPalette.MEDIUM_GRAY, 0.7)),
                ],
                description="Rocky ground surface"
            ),
            'sandy_soil': TileConfig(
                "·", ColorPalette.SAND, ColorPalette.DESERT_TAN,
                variants=[
                    TileConfig("∘", ColorPalette.shade(ColorPalette.SAND, 1.1), ColorPalette.DESERT_TAN),
                    TileConfig("°", ColorPalette.shade(ColorPalette.SAND, 0.9), ColorPalette.DESERT_TAN),
                ],
                description="Sandy soil"
            ),
            'muddy_ground': TileConfig(
                "∼", ColorPalette.DARK_BROWN, ColorPalette.shade(ColorPalette.DARK_BROWN, 0.8),
                variants=[
                    TileConfig("≈", ColorPalette.shade(ColorPalette.DARK_BROWN, 1.1), ColorPalette.shade(ColorPalette.DARK_BROWN, 0.8)),
                    TileConfig("~", ColorPalette.shade(ColorPalette.DARK_BROWN, 0.9), ColorPalette.shade(ColorPalette.DARK_BROWN, 0.8)),
                ],
                description="Muddy, wet ground"
            ),
            'moss_covered': TileConfig(
                "·", ColorPalette.shade(ColorPalette.FOREST_GREEN, 0.8), ColorPalette.shade(ColorPalette.DARK_GREEN, 0.8),
                variants=[
                    TileConfig("∘", ColorPalette.shade(ColorPalette.FOREST_GREEN, 0.9), ColorPalette.shade(ColorPalette.DARK_GREEN, 0.8)),
                    TileConfig("°", ColorPalette.shade(ColorPalette.FOREST_GREEN, 0.7), ColorPalette.shade(ColorPalette.DARK_GREEN, 0.8)),
                ],
                description="Moss-covered ground"
            ),
            'leaf_litter': TileConfig(
                ",", ColorPalette.MEDIUM_BROWN, ColorPalette.DARK_BROWN,
                variants=[
                    TileConfig("'", ColorPalette.shade(ColorPalette.MEDIUM_BROWN, 1.1), ColorPalette.DARK_BROWN),
                    TileConfig("`", ColorPalette.shade(ColorPalette.MEDIUM_BROWN, 0.9), ColorPalette.DARK_BROWN),
                ],
                description="Fallen leaves and organic matter"
            ),
            
            # === VEGETATION SUBTYPES ===
            'tall_grass': TileConfig(
                "|", ColorPalette.BRIGHT_GREEN, ColorPalette.MEDIUM_GREEN,
                variants=[
                    TileConfig("┃", ColorPalette.shade(ColorPalette.BRIGHT_GREEN, 1.1), ColorPalette.MEDIUM_GREEN),
                    TileConfig("∣", ColorPalette.shade(ColorPalette.BRIGHT_GREEN, 0.9), ColorPalette.MEDIUM_GREEN),
                    TileConfig("│", ColorPalette.shade(ColorPalette.BRIGHT_GREEN, 1.05), ColorPalette.MEDIUM_GREEN),
                ],
                description="Tall grass stalks"
            ),
            'short_grass': TileConfig(
                "'", ColorPalette.MEDIUM_GREEN, ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.7),
                variants=[
                    TileConfig("`", ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 1.1), ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.7)),
                    TileConfig(",", ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.9), ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.7)),
                    TileConfig(".", ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 1.05), ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.7)),
                ],
                description="Short grass coverage"
            ),
            'wildflowers': TileConfig(
                "*", ColorPalette.FLOWER_PINK, ColorPalette.MEDIUM_GREEN,
                variants=[
                    TileConfig("❀", ColorPalette.FLOWER_YELLOW, ColorPalette.MEDIUM_GREEN),
                    TileConfig("✿", ColorPalette.FLOWER_PINK, ColorPalette.MEDIUM_GREEN),
                    TileConfig("❁", ColorPalette.shade(ColorPalette.FLOWER_PINK, 0.8), ColorPalette.MEDIUM_GREEN),
                    TileConfig("✾", ColorPalette.FLOWER_YELLOW, ColorPalette.MEDIUM_GREEN),
                ],
                description="Wild flowering plants"
            ),
            'thorny_bushes': TileConfig(
                "≡", ColorPalette.tint(ColorPalette.FOREST_GREEN, ColorPalette.MEDIUM_BROWN, 0.3),
                ColorPalette.shade(ColorPalette.FOREST_GREEN, 0.6),
                variants=[
                    TileConfig("⌐", ColorPalette.tint(ColorPalette.FOREST_GREEN, ColorPalette.MEDIUM_BROWN, 0.2), ColorPalette.shade(ColorPalette.FOREST_GREEN, 0.6)),
                    TileConfig("¬", ColorPalette.tint(ColorPalette.FOREST_GREEN, ColorPalette.MEDIUM_BROWN, 0.4), ColorPalette.shade(ColorPalette.FOREST_GREEN, 0.6)),
                ],
                description="Thorny shrubs and bushes"
            ),
            'berry_bushes': TileConfig(
                "♣", ColorPalette.FOREST_GREEN, ColorPalette.DARK_GREEN,
                variants=[
                    TileConfig("♧", ColorPalette.shade(ColorPalette.FOREST_GREEN, 1.1), ColorPalette.DARK_GREEN),
                    TileConfig("♠", ColorPalette.shade(ColorPalette.FOREST_GREEN, 0.9), ColorPalette.DARK_GREEN),
                ],
                description="Berry-bearing bushes"
            ),
            'young_trees': TileConfig(
                "♪", ColorPalette.FOREST_GREEN, ColorPalette.shade(ColorPalette.FOREST_GREEN, 0.6),
                variants=[
                    TileConfig("♫", ColorPalette.shade(ColorPalette.FOREST_GREEN, 1.1), ColorPalette.shade(ColorPalette.FOREST_GREEN, 0.6)),
                    TileConfig("♬", ColorPalette.shade(ColorPalette.FOREST_GREEN, 0.9), ColorPalette.shade(ColorPalette.FOREST_GREEN, 0.6)),
                ],
                description="Young saplings and small trees"
            ),
            'mature_trees': TileConfig(
                "♠", ColorPalette.DARK_GREEN, ColorPalette.shade(ColorPalette.DARK_GREEN, 0.6),
                variants=[
                    TileConfig("♣", ColorPalette.shade(ColorPalette.DARK_GREEN, 1.1), ColorPalette.shade(ColorPalette.DARK_GREEN, 0.6)),
                    TileConfig("♧", ColorPalette.shade(ColorPalette.DARK_GREEN, 0.9), ColorPalette.shade(ColorPalette.DARK_GREEN, 0.6)),
                    TileConfig("♤", ColorPalette.shade(ColorPalette.DARK_GREEN, 1.05), ColorPalette.shade(ColorPalette.DARK_GREEN, 0.6)),
                ],
                description="Large mature trees"
            ),
            'fallen_log': TileConfig(
                "―", ColorPalette.MEDIUM_BROWN, ColorPalette.DARK_BROWN,
                variants=[
                    TileConfig("━", ColorPalette.shade(ColorPalette.MEDIUM_BROWN, 1.1), ColorPalette.DARK_BROWN),
                    TileConfig("─", ColorPalette.shade(ColorPalette.MEDIUM_BROWN, 0.9), ColorPalette.DARK_BROWN),
                ],
                description="Fallen tree logs"
            ),
            
            # === ROCK FORMATIONS ===
            'small_boulder': TileConfig(
                "○", ColorPalette.LIGHT_GRAY, ColorPalette.MEDIUM_GRAY,
                variants=[
                    TileConfig("◯", ColorPalette.shade(ColorPalette.LIGHT_GRAY, 1.1), ColorPalette.MEDIUM_GRAY),
                    TileConfig("◦", ColorPalette.shade(ColorPalette.LIGHT_GRAY, 0.9), ColorPalette.MEDIUM_GRAY),
                ],
                description="Small boulders and rocks"
            ),
            'large_boulder': TileConfig(
                "●", ColorPalette.MEDIUM_GRAY, ColorPalette.DARK_GRAY,
                variants=[
                    TileConfig("⬤", ColorPalette.shade(ColorPalette.MEDIUM_GRAY, 1.1), ColorPalette.DARK_GRAY),
                    TileConfig("◉", ColorPalette.shade(ColorPalette.MEDIUM_GRAY, 0.9), ColorPalette.DARK_GRAY),
                ],
                description="Large boulders and rock formations"
            ),
            'rock_outcrop': TileConfig(
                "▲", ColorPalette.LIGHT_GRAY, ColorPalette.MEDIUM_GRAY,
                variants=[
                    TileConfig("▼", ColorPalette.shade(ColorPalette.LIGHT_GRAY, 1.1), ColorPalette.MEDIUM_GRAY),
                    TileConfig("◄", ColorPalette.shade(ColorPalette.LIGHT_GRAY, 0.9), ColorPalette.MEDIUM_GRAY),
                    TileConfig("►", ColorPalette.shade(ColorPalette.LIGHT_GRAY, 1.05), ColorPalette.MEDIUM_GRAY),
                ],
                description="Rocky outcrops and formations"
            ),
            'loose_stones': TileConfig(
                "∘", ColorPalette.STONE_GRAY, ColorPalette.shade(ColorPalette.STONE_GRAY, 0.7),
                variants=[
                    TileConfig("·", ColorPalette.shade(ColorPalette.STONE_GRAY, 1.1), ColorPalette.shade(ColorPalette.STONE_GRAY, 0.7)),
                    TileConfig("°", ColorPalette.shade(ColorPalette.STONE_GRAY, 0.9), ColorPalette.shade(ColorPalette.STONE_GRAY, 0.7)),
                ],
                description="Scattered loose stones"
            ),
            'pebbles': TileConfig(
                "·", ColorPalette.LIGHT_GRAY, ColorPalette.shade(ColorPalette.LIGHT_GRAY, 0.8),
                variants=[
                    TileConfig("∘", ColorPalette.shade(ColorPalette.LIGHT_GRAY, 1.1), ColorPalette.shade(ColorPalette.LIGHT_GRAY, 0.8)),
                    TileConfig("°", ColorPalette.shade(ColorPalette.LIGHT_GRAY, 0.9), ColorPalette.shade(ColorPalette.LIGHT_GRAY, 0.8)),
                ],
                description="Small pebbles and gravel"
            ),
            
            # === WATER SUBTYPES ===
            'shallow_water': TileConfig(
                "∼", ColorPalette.SKY_BLUE, ColorPalette.WATER_BLUE,
                variants=[
                    TileConfig("≈", ColorPalette.shade(ColorPalette.SKY_BLUE, 1.1), ColorPalette.WATER_BLUE),
                    TileConfig("~", ColorPalette.shade(ColorPalette.SKY_BLUE, 0.9), ColorPalette.WATER_BLUE),
                ],
                description="Shallow water areas"
            ),
            'deep_water': TileConfig(
                "≈", ColorPalette.WATER_BLUE, ColorPalette.DEEP_BLUE,
                variants=[
                    TileConfig("~", ColorPalette.shade(ColorPalette.WATER_BLUE, 1.1), ColorPalette.DEEP_BLUE),
                    TileConfig("∼", ColorPalette.shade(ColorPalette.WATER_BLUE, 0.9), ColorPalette.DEEP_BLUE),
                ],
                description="Deep water bodies"
            ),
            'water_edge': TileConfig(
                "∽", ColorPalette.PALE_BLUE, ColorPalette.tint(ColorPalette.WATER_BLUE, ColorPalette.MEDIUM_BROWN, 0.2),
                variants=[
                    TileConfig("≋", ColorPalette.shade(ColorPalette.PALE_BLUE, 1.1), ColorPalette.tint(ColorPalette.WATER_BLUE, ColorPalette.MEDIUM_BROWN, 0.2)),
                    TileConfig("∼", ColorPalette.shade(ColorPalette.PALE_BLUE, 0.9), ColorPalette.tint(ColorPalette.WATER_BLUE, ColorPalette.MEDIUM_BROWN, 0.2)),
                ],
                description="Water's edge and shoreline"
            ),
            'muddy_bank': TileConfig(
                "≋", ColorPalette.MEDIUM_BROWN, ColorPalette.DARK_BROWN,
                variants=[
                    TileConfig("∼", ColorPalette.shade(ColorPalette.MEDIUM_BROWN, 1.1), ColorPalette.DARK_BROWN),
                    TileConfig("≈", ColorPalette.shade(ColorPalette.MEDIUM_BROWN, 0.9), ColorPalette.DARK_BROWN),
                ],
                description="Muddy banks and wetland edges"
            ),
            'reed_beds': TileConfig(
                "|", ColorPalette.CACTUS_GREEN, ColorPalette.tint(ColorPalette.WATER_BLUE, ColorPalette.DARK_GREEN, 0.3),
                variants=[
                    TileConfig("┃", ColorPalette.shade(ColorPalette.CACTUS_GREEN, 1.1), ColorPalette.tint(ColorPalette.WATER_BLUE, ColorPalette.DARK_GREEN, 0.3)),
                    TileConfig("│", ColorPalette.shade(ColorPalette.CACTUS_GREEN, 0.9), ColorPalette.tint(ColorPalette.WATER_BLUE, ColorPalette.DARK_GREEN, 0.3)),
                ],
                description="Reed beds and marsh grasses"
            )
        }
        
        # ========================================
        # SPECIAL FEATURE TILES (All Scales)
        # ========================================
        
        self.tiles['features'] = {
            
            # === STRUCTURAL FEATURES ===
            'cave_mouth': TileConfig(
                "○", ColorPalette.LIGHT_GRAY, ColorPalette.BLACK,
                description="Cave entrance"
            ),
            'mountain_ledge': TileConfig(
                "═", ColorPalette.shade(ColorPalette.MOUNTAIN_GRAY, 1.2), ColorPalette.MOUNTAIN_GRAY,
                description="Mountain ledge or platform"
            ),
            'cliff_face': TileConfig(
                "█", ColorPalette.MEDIUM_GRAY, ColorPalette.DARK_GRAY,
                description="Vertical cliff face"
            ),
            'natural_ramp': TileConfig(
                "╱", ColorPalette.MOUNTAIN_BROWN, ColorPalette.shade(ColorPalette.MOUNTAIN_BROWN, 0.7),
                variants=[
                    TileConfig("╲", ColorPalette.MOUNTAIN_BROWN, ColorPalette.shade(ColorPalette.MOUNTAIN_BROWN, 0.7)),
                ],
                description="Natural slope or ramp"
            ),
            'tree_trunk': TileConfig(
                "♠", ColorPalette.DARK_BROWN, ColorPalette.shade(ColorPalette.DARK_BROWN, 0.8),
                description="Large tree trunk (climbable)"
            ),
            'rock_pile': TileConfig(
                "▲", ColorPalette.LIGHT_GRAY, ColorPalette.MEDIUM_GRAY,
                variants=[
                    TileConfig("⩙", ColorPalette.shade(ColorPalette.LIGHT_GRAY, 1.1), ColorPalette.MEDIUM_GRAY),
                    TileConfig("∩", ColorPalette.shade(ColorPalette.LIGHT_GRAY, 0.9), ColorPalette.MEDIUM_GRAY),
                ],
                description="Pile of climbable rocks"
            ),
            'water_ford': TileConfig(
                "≈", ColorPalette.PALE_BLUE, ColorPalette.LIGHT_BLUE,
                description="Shallow river crossing"
            ),
            'fallen_tree_bridge': TileConfig(
                "═", ColorPalette.MEDIUM_BROWN, ColorPalette.DARK_BROWN,
                description="Fallen tree forming natural bridge"
            ),
            'natural_bridge': TileConfig(
                "═", ColorPalette.STONE_GRAY, ColorPalette.MEDIUM_GRAY,
                description="Natural stone bridge"
            ),
            
            # === LANDMARKS ===
            'waterfall': TileConfig(
                "║", ColorPalette.PALE_BLUE, ColorPalette.WATER_BLUE,
                variants=[
                    TileConfig("┃", ColorPalette.SKY_BLUE, ColorPalette.WATER_BLUE),
                    TileConfig("│", ColorPalette.PALE_BLUE, ColorPalette.WATER_BLUE),
                ],
                description="Cascading waterfall"
            ),
            'natural_spring': TileConfig(
                "◉", ColorPalette.SKY_BLUE, ColorPalette.LIGHT_BLUE,
                description="Natural freshwater spring"
            ),
            'ancient_grove': TileConfig(
                "♠", ColorPalette.shade(ColorPalette.DARK_GREEN, 0.8), ColorPalette.shade(ColorPalette.DARK_GREEN, 0.5),
                description="Sacred grove of ancient trees"
            ),
            'standing_stones': TileConfig(
                "∩", ColorPalette.STONE_GRAY, ColorPalette.MEDIUM_GRAY,
                variants=[
                    TileConfig("⩙", ColorPalette.shade(ColorPalette.STONE_GRAY, 1.1), ColorPalette.MEDIUM_GRAY),
                    TileConfig("▲", ColorPalette.shade(ColorPalette.STONE_GRAY, 0.9), ColorPalette.MEDIUM_GRAY),
                ],
                description="Ancient standing stones"
            ),
            'natural_arch': TileConfig(
                "∩", ColorPalette.TAN, ColorPalette.DESERT_BROWN,
                description="Natural stone archway"
            ),
            'crater': TileConfig(
                "○", ColorPalette.MEDIUM_BROWN, ColorPalette.DARK_BROWN,
                description="Impact crater or caldera"
            ),
            'salt_flat': TileConfig(
                "·", ColorPalette.SNOW_WHITE, (220, 220, 220),
                variants=[
                    TileConfig("∘", ColorPalette.SNOW_WHITE, (220, 220, 220)),
                    TileConfig("°", ColorPalette.SNOW_WHITE, (220, 220, 220)),
                ],
                description="Crystalline salt flats"
            ),
            'scenic_overlook': TileConfig(
                "▲", ColorPalette.shade(ColorPalette.MOUNTAIN_GRAY, 1.3), ColorPalette.MOUNTAIN_GRAY,
                description="Scenic mountain overlook"
            ),
            'hidden_valley': TileConfig(
                "∪", ColorPalette.BRIGHT_GREEN, ColorPalette.MOUNTAIN_BROWN,
                description="Hidden mountain valley"
            )
        }
        
        # ========================================
        # RESOURCE TILES (Local Scale)
        # ========================================
        
        self.tiles['resources'] = {
            
            # === RENEWABLE BIOLOGICAL ===
            'berries': TileConfig(
                "•", ColorPalette.BERRY_RED, ColorPalette.FOREST_GREEN,
                variants=[
                    TileConfig("●", (128, 0, 128), ColorPalette.FOREST_GREEN),  # Purple berries
                    TileConfig("◦", ColorPalette.BERRY_RED, ColorPalette.FOREST_GREEN),
                ],
                description="Edible berries"
            ),
            'nuts': TileConfig(
                "○", ColorPalette.MEDIUM_BROWN, ColorPalette.DARK_GREEN,
                variants=[
                    TileConfig("◯", ColorPalette.shade(ColorPalette.MEDIUM_BROWN, 1.1), ColorPalette.DARK_GREEN),
                    TileConfig("◦", ColorPalette.shade(ColorPalette.MEDIUM_BROWN, 0.9), ColorPalette.DARK_GREEN),
                ],
                description="Edible nuts from trees"
            ),
            'herbs': TileConfig(
                "♪", ColorPalette.LIME_GREEN, ColorPalette.MEDIUM_GREEN,
                variants=[
                    TileConfig("♫", ColorPalette.shade(ColorPalette.LIME_GREEN, 1.1), ColorPalette.MEDIUM_GREEN),
                    TileConfig("♬", ColorPalette.shade(ColorPalette.LIME_GREEN, 0.9), ColorPalette.MEDIUM_GREEN),
                ],
                description="Medicinal and culinary herbs"
            ),
            'mushrooms': TileConfig(
                "♀", ColorPalette.MUSHROOM_BROWN, ColorPalette.DARK_GREEN,
                variants=[
                    TileConfig("⚘", (200, 200, 200), ColorPalette.DARK_GREEN),  # White mushrooms
                    TileConfig("♂", ColorPalette.BERRY_RED, ColorPalette.DARK_GREEN),  # Red mushrooms
                ],
                description="Edible mushrooms and fungi"
            ),
            'honey': TileConfig(
                "◉", ColorPalette.GOLD, ColorPalette.MEDIUM_GREEN,
                description="Bee hives and honey"
            ),
            'fish': TileConfig(
                "◦", ColorPalette.SILVER, ColorPalette.WATER_BLUE,
                variants=[
                    TileConfig("○", ColorPalette.shade(ColorPalette.SILVER, 0.8), ColorPalette.WATER_BLUE),
                    TileConfig("∘", ColorPalette.shade(ColorPalette.SILVER, 1.2), ColorPalette.WATER_BLUE),
                ],
                description="Fish in water bodies"
            ),
            
            # === HARVESTABLE MATERIALS ===
            'branches': TileConfig(
                "┼", ColorPalette.LIGHT_BROWN, ColorPalette.DARK_BROWN,
                variants=[
                    TileConfig("├", ColorPalette.shade(ColorPalette.LIGHT_BROWN, 1.1), ColorPalette.DARK_BROWN),
                    TileConfig("┤", ColorPalette.shade(ColorPalette.LIGHT_BROWN, 0.9), ColorPalette.DARK_BROWN),
                    TileConfig("┬", ColorPalette.shade(ColorPalette.LIGHT_BROWN, 1.05), ColorPalette.DARK_BROWN),
                ],
                description="Harvestable branches and twigs"
            ),
            'logs': TileConfig(
                "▬", ColorPalette.MEDIUM_BROWN, ColorPalette.DARK_BROWN,
                variants=[
                    TileConfig("━", ColorPalette.shade(ColorPalette.MEDIUM_BROWN, 1.1), ColorPalette.DARK_BROWN),
                    TileConfig("─", ColorPalette.shade(ColorPalette.MEDIUM_BROWN, 0.9), ColorPalette.DARK_BROWN),
                ],
                description="Fallen logs suitable for lumber"
            ),
            'bark': TileConfig(
                "▒", ColorPalette.DARK_BROWN, ColorPalette.shade(ColorPalette.DARK_BROWN, 0.8),
                variants=[
                    TileConfig("▓", ColorPalette.shade(ColorPalette.DARK_BROWN, 1.1), ColorPalette.shade(ColorPalette.DARK_BROWN, 0.8)),
                    TileConfig("░", ColorPalette.shade(ColorPalette.DARK_BROWN, 0.9), ColorPalette.shade(ColorPalette.DARK_BROWN, 0.8)),
                ],
                description="Tree bark for crafting"
            ),
            'reeds': TileConfig(
                "┃", ColorPalette.CACTUS_GREEN, ColorPalette.tint(ColorPalette.WATER_BLUE, ColorPalette.FOREST_GREEN, 0.3),
                variants=[
                    TileConfig("│", ColorPalette.shade(ColorPalette.CACTUS_GREEN, 1.1), ColorPalette.tint(ColorPalette.WATER_BLUE, ColorPalette.FOREST_GREEN, 0.3)),
                    TileConfig("║", ColorPalette.shade(ColorPalette.CACTUS_GREEN, 0.9), ColorPalette.tint(ColorPalette.WATER_BLUE, ColorPalette.FOREST_GREEN, 0.3)),
                ],
                description="Marsh reeds for weaving"
            ),
            'clay': TileConfig(
                "≡", ColorPalette.TAN, ColorPalette.MEDIUM_BROWN,
                variants=[
                    TileConfig("⌐", ColorPalette.shade(ColorPalette.TAN, 1.1), ColorPalette.MEDIUM_BROWN),
                    TileConfig("¬", ColorPalette.shade(ColorPalette.TAN, 0.9), ColorPalette.MEDIUM_BROWN),
                ],
                description="Clay deposits for pottery"
            ),
            'flint': TileConfig(
                "◊", ColorPalette.DARK_GRAY, ColorPalette.MEDIUM_GRAY,
                variants=[
                    TileConfig("⬟", ColorPalette.shade(ColorPalette.DARK_GRAY, 1.1), ColorPalette.MEDIUM_GRAY),
                    TileConfig("◇", ColorPalette.shade(ColorPalette.DARK_GRAY, 0.9), ColorPalette.MEDIUM_GRAY),
                ],
                description="Flint for tools and fire"
            ),
            'stones': TileConfig(
                "◦", ColorPalette.STONE_GRAY, ColorPalette.MEDIUM_GRAY,
                variants=[
                    TileConfig("○", ColorPalette.shade(ColorPalette.STONE_GRAY, 1.1), ColorPalette.MEDIUM_GRAY),
                    TileConfig("∘", ColorPalette.shade(ColorPalette.STONE_GRAY, 0.9), ColorPalette.MEDIUM_GRAY),
                ],
                description="Building stones"
            ),
            
            # === MINERAL RESOURCES ===
            'iron_ore': TileConfig(
                "▪", ColorPalette.IRON, ColorPalette.DARK_GRAY,
                variants=[
                    TileConfig("■", ColorPalette.shade(ColorPalette.IRON, 1.1), ColorPalette.DARK_GRAY),
                    TileConfig("▫", ColorPalette.shade(ColorPalette.IRON, 0.9), ColorPalette.DARK_GRAY),
                ],
                description="Iron ore deposits"
            ),
            'copper_ore': TileConfig(
                "▪", ColorPalette.COPPER, ColorPalette.MEDIUM_BROWN,
                variants=[
                    TileConfig("■", ColorPalette.shade(ColorPalette.COPPER, 1.1), ColorPalette.MEDIUM_BROWN),
                    TileConfig("▫", ColorPalette.shade(ColorPalette.COPPER, 0.9), ColorPalette.MEDIUM_BROWN),
                ],
                description="Copper ore deposits"
            ),
            'salt': TileConfig(
                "◊", ColorPalette.SNOW_WHITE, (220, 220, 220),
                variants=[
                    TileConfig("⬟", ColorPalette.SNOW_WHITE, (200, 200, 200)),
                    TileConfig("◇", ColorPalette.SNOW_WHITE, (240, 240, 240)),
                ],
                description="Salt deposits"
            ),
            'gems': TileConfig(
                "◊", (255, 20, 147), ColorPalette.DARK_GRAY,  # Deep pink
                variants=[
                    TileConfig("♦", (138, 43, 226), ColorPalette.DARK_GRAY),  # Blue violet
                    TileConfig("⬟", (50, 205, 50), ColorPalette.DARK_GRAY),   # Lime green
                    TileConfig("◇", (255, 165, 0), ColorPalette.DARK_GRAY),   # Orange
                ],
                description="Precious gemstones"
            ),
            'coal': TileConfig(
                "■", ColorPalette.CHARCOAL, ColorPalette.BLACK,
                variants=[
                    TileConfig("▪", ColorPalette.shade(ColorPalette.CHARCOAL, 1.2), ColorPalette.BLACK),
                    TileConfig("▫", ColorPalette.shade(ColorPalette.CHARCOAL, 0.8), ColorPalette.BLACK),
                ],
                description="Coal for fuel and smelting"
            ),
            
            # === WATER RESOURCES ===
            'fresh_water': TileConfig(
                "○", ColorPalette.SKY_BLUE, ColorPalette.LIGHT_BLUE,
                description="Source of fresh drinking water"
            ),
            'mineral_water': TileConfig(
                "◉", ColorPalette.tint(ColorPalette.SKY_BLUE, ColorPalette.GOLD, 0.1), ColorPalette.LIGHT_BLUE,
                description="Mineral-rich spring water"
            ),
            
            # === SPECIAL RESOURCES ===
            'game_trail': TileConfig(
                "∴", ColorPalette.MEDIUM_BROWN, ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.8),
                variants=[
                    TileConfig(":", ColorPalette.MEDIUM_BROWN, ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.8)),
                    TileConfig("∵", ColorPalette.MEDIUM_BROWN, ColorPalette.shade(ColorPalette.MEDIUM_GREEN, 0.8)),
                ],
                description="Animal trails for hunting"
            )
        }
        
        # ========================================
        # ANIMAL SPAWN INDICATORS (Subtle)
        # ========================================
        
        self.tiles['animals'] = {
            'small_game_area': TileConfig(
                "·", ColorPalette.tint(ColorPalette.MEDIUM_GREEN, (255, 255, 0), 0.05),  # Slight yellow tint
                ColorPalette.tint(ColorPalette.DARK_GREEN, (255, 255, 0), 0.05),
                description="Area where small game spawns"
            ),
            'large_game_area': TileConfig(
                "·", ColorPalette.tint(ColorPalette.MEDIUM_GREEN, (0, 255, 0), 0.05),  # Slight green tint
                ColorPalette.tint(ColorPalette.DARK_GREEN, (0, 255, 0), 0.05),
                description="Area where large game spawns"
            ),
            'predator_area': TileConfig(
                "·", ColorPalette.tint(ColorPalette.MEDIUM_GREEN, (255, 0, 0), 0.05),  # Slight red tint
                ColorPalette.tint(ColorPalette.DARK_GREEN, (255, 0, 0), 0.05),
                description="Area where predators spawn"
            ),
            'livestock_area': TileConfig(
                "·", ColorPalette.tint(ColorPalette.MEDIUM_GREEN, (0, 0, 255), 0.05),  # Slight blue tint
                ColorPalette.tint(ColorPalette.DARK_GREEN, (0, 0, 255), 0.05),
                description="Suitable area for livestock"
            ),
            'fish_area': TileConfig(
                "∼", ColorPalette.tint(ColorPalette.WATER_BLUE, (0, 255, 255), 0.1),  # Cyan tint
                ColorPalette.tint(ColorPalette.DEEP_BLUE, (0, 255, 255), 0.1),
                description="Area where fish spawn"
            ),
            'insect_area': TileConfig(
                "·", ColorPalette.tint(ColorPalette.MEDIUM_GREEN, (255, 255, 0), 0.03),  # Very slight yellow
                ColorPalette.tint(ColorPalette.DARK_GREEN, (255, 255, 0), 0.03),
                description="Area with high insect activity"
            )
        }
    
    def get_tile(self, scale: str, tile_type: str, use_variant: bool = True) -> TileConfig:
        """Get tile configuration, optionally using a random variant"""
        if scale not in self.tiles or tile_type not in self.tiles[scale]:
            # Return fallback tile
            return TileConfig("?", ColorPalette.SNOW_WHITE, ColorPalette.BLACK, 
                            description=f"Unknown tile: {scale}.{tile_type}")
        
        base_tile = self.tiles[scale][tile_type]
        
        # Use variant if available and requested
        if use_variant and base_tile.variants and random.random() < 0.3:  # 30% chance for variant
            return random.choice(base_tile.variants)
        
        return base_tile
    
    def get_tile_with_environmental_variation(self, scale: str, tile_type: str