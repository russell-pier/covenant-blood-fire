"""
Terrain types and properties for the world generation system.

This module defines the different terrain types available in the game
and their visual and gameplay properties.
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .environmental import EnvironmentalData

# Import config system
try:
    from ..config import get_terrain_visual, VisualConfig
except ImportError:
    # Fallback if config system not available
    get_terrain_visual = None
    VisualConfig = None


class TerrainType(Enum):
    """Enumeration of available terrain types."""

    # Surface layer terrains (existing)
    DEEP_WATER = "deep_water"
    SHALLOW_WATER = "shallow_water"
    SAND = "sand"
    GRASS = "grass"
    LIGHT_GRASS = "light_grass"
    DARK_GRASS = "dark_grass"
    FOREST = "forest"
    HILLS = "hills"
    MOUNTAINS = "mountains"
    CAVES = "caves"
    DESERT = "desert"
    SWAMP = "swamp"
    FERTILE = "fertile"

    # Underground layer terrains
    CAVE_FLOOR = "cave_floor"
    CAVE_WALL = "cave_wall"
    UNDERGROUND_WATER = "underground_water"
    ORE_VEIN = "ore_vein"

    # Surface layer special terrains
    CAVE_ENTRANCE = "cave_entrance"
    MOUNTAIN_BASE = "mountain_base"

    # Mountain layer terrains
    MOUNTAIN_PEAK = "mountain_peak"
    MOUNTAIN_SLOPE = "mountain_slope"
    MOUNTAIN_CLIFF = "mountain_cliff"
    SNOW = "snow"


@dataclass
class TerrainProperties:
    """Properties for a terrain type including visual and gameplay attributes."""

    terrain_type: TerrainType
    character: str
    foreground_color: Tuple[int, int, int]
    background_color: Tuple[int, int, int]
    movement_cost: float
    passable: bool
    description: str

    @classmethod
    def from_config(cls, terrain_type: TerrainType, description: str = "") -> 'TerrainProperties':
        """Create TerrainProperties from config system."""
        if get_terrain_visual:
            visual_config = get_terrain_visual(terrain_type.value)
            if visual_config:
                # Use config data
                character = visual_config.characters[0] if visual_config.characters else "?"
                fg_color = visual_config.foreground_color
                bg_color = visual_config.background_color or (0, 0, 0)
                movement_cost = visual_config.movement_cost or 1.0
                passable = visual_config.passable if visual_config.passable is not None else True

                return cls(
                    terrain_type=terrain_type,
                    character=character,
                    foreground_color=fg_color,
                    background_color=bg_color,
                    movement_cost=movement_cost,
                    passable=passable,
                    description=description
                )

        # Fallback to default values if config not available
        return cls._get_default_properties(terrain_type, description)

    @classmethod
    def _get_default_properties(cls, terrain_type: TerrainType, description: str) -> 'TerrainProperties':
        """Get default properties for terrain types (fallback)."""
        defaults = {
            TerrainType.GRASS: (".", (34, 139, 34), (0, 100, 0), 1.0, True),
            TerrainType.WATER: ("~", (100, 149, 237), (25, 25, 112), float('inf'), False),
            TerrainType.FOREST: ("T", (34, 139, 34), (0, 50, 0), 1.5, True),
            TerrainType.MOUNTAINS: ("^", (105, 105, 105), (169, 169, 169), 3.0, True),
        }

        char, fg, bg, cost, passable = defaults.get(terrain_type, ("?", (255, 255, 255), (0, 0, 0), 1.0, True))

        return cls(
            terrain_type=terrain_type,
            character=char,
            foreground_color=fg,
            background_color=bg,
            movement_cost=cost,
            passable=passable,
            description=description
        )


class TerrainMapper:
    """
    Maps noise values to terrain types and provides terrain properties.
    
    This class handles the conversion from Perlin noise values to specific
    terrain types based on configurable thresholds.
    """
    
    def __init__(self):
        """Initialize the terrain mapper with default terrain properties."""
        self._terrain_properties = {
            TerrainType.DEEP_WATER: TerrainProperties(
                terrain_type=TerrainType.DEEP_WATER,
                character=" ",
                foreground_color=(0, 0, 0),
                background_color=(20, 50, 120),
                movement_cost=float('inf'),
                passable=False,
                description="Deep water - impassable"
            ),
            TerrainType.SHALLOW_WATER: TerrainProperties(
                terrain_type=TerrainType.SHALLOW_WATER,
                character=" ",
                foreground_color=(0, 0, 0),
                background_color=(40, 80, 160),
                movement_cost=2.0,
                passable=True,
                description="Shallow water - slow movement"
            ),
            TerrainType.SAND: TerrainProperties(
                terrain_type=TerrainType.SAND,
                character=" ",
                foreground_color=(0, 0, 0),
                background_color=(200, 180, 120),
                movement_cost=1.2,
                passable=True,
                description="Sandy beach - slightly slow movement"
            ),
            TerrainType.GRASS: TerrainProperties(
                terrain_type=TerrainType.GRASS,
                character=" ",
                foreground_color=(0, 0, 0),
                background_color=(50, 120, 50),
                movement_cost=1.0,
                passable=True,
                description="Grassland - normal movement"
            ),
            TerrainType.LIGHT_GRASS: TerrainProperties(
                terrain_type=TerrainType.LIGHT_GRASS,
                character=" ",
                foreground_color=(0, 0, 0),
                background_color=(60, 140, 60),
                movement_cost=1.0,
                passable=True,
                description="Light grassland - normal movement"
            ),
            TerrainType.DARK_GRASS: TerrainProperties(
                terrain_type=TerrainType.DARK_GRASS,
                character=" ",
                foreground_color=(0, 0, 0),
                background_color=(30, 80, 30),
                movement_cost=1.0,
                passable=True,
                description="Dark grassland - normal movement"
            ),
            TerrainType.FOREST: TerrainProperties(
                terrain_type=TerrainType.FOREST,
                character=" ",
                foreground_color=(0, 0, 0),
                background_color=(20, 60, 20),
                movement_cost=1.5,
                passable=True,
                description="Forest - slow movement"
            ),
            TerrainType.HILLS: TerrainProperties(
                terrain_type=TerrainType.HILLS,
                character=" ",
                foreground_color=(0, 0, 0),
                background_color=(120, 100, 80),
                movement_cost=1.3,
                passable=True,
                description="Hills - slightly slow movement"
            ),
            TerrainType.MOUNTAINS: TerrainProperties(
                terrain_type=TerrainType.MOUNTAINS,
                character=" ",
                foreground_color=(0, 0, 0),
                background_color=(80, 80, 80),
                movement_cost=float('inf'),
                passable=False,
                description="Mountains - impassable"
            ),
            TerrainType.CAVES: TerrainProperties(
                terrain_type=TerrainType.CAVES,
                character=" ",
                foreground_color=(0, 0, 0),
                background_color=(40, 30, 20),
                movement_cost=1.8,
                passable=True,
                description="Underground caves - slow movement, mining opportunities"
            ),
            TerrainType.DESERT: TerrainProperties(
                terrain_type=TerrainType.DESERT,
                character=" ",
                foreground_color=(0, 0, 0),
                background_color=(220, 180, 100),
                movement_cost=1.4,
                passable=True,
                description="Desert - hot and dry, slow movement"
            ),
            TerrainType.SWAMP: TerrainProperties(
                terrain_type=TerrainType.SWAMP,
                character=" ",
                foreground_color=(0, 0, 0),
                background_color=(60, 80, 40),
                movement_cost=2.5,
                passable=True,
                description="Swamp - very slow movement, high moisture"
            ),
            TerrainType.FERTILE: TerrainProperties(
                terrain_type=TerrainType.FERTILE,
                character=" ",
                foreground_color=(0, 0, 0),
                background_color=(80, 160, 80),
                movement_cost=0.8,
                passable=True,
                description="Fertile land - fast movement, ideal for agriculture"
            )
        }
        
        # Noise value thresholds for terrain generation
        self._terrain_thresholds = [
            (-1.0, TerrainType.DEEP_WATER),
            (-0.6, TerrainType.SHALLOW_WATER),
            (-0.3, TerrainType.SAND),
            (-0.1, TerrainType.DARK_GRASS),
            (0.1, TerrainType.GRASS),
            (0.3, TerrainType.LIGHT_GRASS),
            (0.5, TerrainType.FOREST),
            (0.7, TerrainType.HILLS),
            (1.0, TerrainType.MOUNTAINS)
        ]
    
    def noise_to_terrain(self, noise_value: float) -> TerrainType:
        """
        Convert a noise value to a terrain type.
        
        Args:
            noise_value: Noise value between -1 and 1
            
        Returns:
            TerrainType corresponding to the noise value
        """
        for threshold, terrain_type in self._terrain_thresholds:
            if noise_value <= threshold:
                return terrain_type
        
        # Fallback to mountains for values above all thresholds
        return TerrainType.MOUNTAINS
    
    def get_terrain_properties(self, terrain_type: TerrainType) -> TerrainProperties:
        """
        Get the properties for a given terrain type.
        
        Args:
            terrain_type: The terrain type to get properties for
            
        Returns:
            TerrainProperties for the given terrain type
        """
        return self._terrain_properties[terrain_type]
    
    def get_all_terrain_types(self) -> list[TerrainType]:
        """
        Get a list of all available terrain types.
        
        Returns:
            List of all TerrainType values
        """
        return list(TerrainType)
    
    def is_passable(self, terrain_type: TerrainType) -> bool:
        """
        Check if a terrain type is passable.
        
        Args:
            terrain_type: The terrain type to check
            
        Returns:
            True if the terrain is passable, False otherwise
        """
        return self._terrain_properties[terrain_type].passable
    
    def get_movement_cost(self, terrain_type: TerrainType) -> float:
        """
        Get the movement cost for a terrain type.
        
        Args:
            terrain_type: The terrain type to check
            
        Returns:
            Movement cost multiplier (1.0 = normal, >1.0 = slower, inf = impassable)
        """
        return self._terrain_properties[terrain_type].movement_cost


def create_default_terrain_mapper() -> TerrainMapper:
    """
    Create a terrain mapper with default configuration.

    Returns:
        TerrainMapper instance with default settings
    """
    return TerrainMapper()


class EnvironmentalTerrainMapper(TerrainMapper):
    """
    Enhanced terrain mapper that uses environmental layers for terrain determination.

    This class extends the basic TerrainMapper to use elevation, moisture, and
    temperature data to determine terrain types using rule-based logic.
    """

    def environmental_to_terrain(self, env_data: "EnvironmentalData") -> TerrainType:
        """
        Convert environmental data to terrain type using rule-based system.

        Args:
            env_data: EnvironmentalData containing elevation (meters), moisture, and temperature (Celsius)

        Returns:
            TerrainType determined by environmental conditions
        """
        elevation = env_data.elevation  # In meters
        moisture = env_data.moisture    # 0.0 to 1.0
        temperature = env_data.temperature  # In Celsius

        # Terrain determination logic (in priority order)
        if elevation < -50:
            return TerrainType.CAVES
        elif elevation < 0:
            return TerrainType.DEEP_WATER
        elif elevation < 50:
            return TerrainType.SHALLOW_WATER
        elif elevation < 100 and moisture > 0.75:
            return TerrainType.SWAMP
        elif temperature > 25 and moisture < 0.35:
            return TerrainType.DESERT
        elif moisture > 0.6 and 5 < temperature < 25 and 50 < elevation < 500:
            return TerrainType.FERTILE
        elif moisture > 0.6 and 0 < temperature < 30:
            return TerrainType.FOREST
        elif elevation > 630:   # Mountains start at ~630m (matches actual elevation ranges)
            return TerrainType.MOUNTAINS
        elif elevation > 580:   # Hills start at ~580m
            return TerrainType.HILLS
        else:
            # Default terrain types based on moisture and temperature
            if moisture > 0.5:
                if temperature > 15:
                    return TerrainType.LIGHT_GRASS
                else:
                    return TerrainType.DARK_GRASS
            else:
                if temperature > 10:
                    return TerrainType.SAND
                else:
                    return TerrainType.GRASS

    def get_terrain_properties_with_variation(
        self,
        terrain_type: TerrainType,
        env_data: "EnvironmentalData",
        world_x: int,
        world_y: int
    ) -> TerrainProperties:
        """
        Get terrain properties with environmental color variations.

        Args:
            terrain_type: The base terrain type
            env_data: Environmental data for color variation
            world_x: World X coordinate for micro-variation
            world_y: World Y coordinate for micro-variation

        Returns:
            TerrainProperties with environmentally-modified colors
        """
        base_props = self.get_terrain_properties(terrain_type)

        # Apply environmental color variations
        varied_bg_color = self._apply_environmental_variation(
            base_props.background_color, env_data, world_x, world_y
        )

        # Create new properties with varied colors
        return TerrainProperties(
            terrain_type=base_props.terrain_type,
            character=base_props.character,
            foreground_color=base_props.foreground_color,
            background_color=varied_bg_color,
            movement_cost=base_props.movement_cost,
            passable=base_props.passable,
            description=base_props.description
        )

    def _apply_environmental_variation(
        self,
        base_color: Tuple[int, int, int],
        env_data: "EnvironmentalData",
        world_x: int,
        world_y: int
    ) -> Tuple[int, int, int]:
        """
        Apply environmental variations to a base color.

        Args:
            base_color: Base RGB color tuple
            env_data: Environmental data for variation
            world_x: World X coordinate for micro-variation
            world_y: World Y coordinate for micro-variation

        Returns:
            Modified RGB color tuple
        """
        r, g, b = base_color

        # Elevation affects brightness (higher = brighter)
        brightness_factor = 0.8 + (env_data.elevation * 0.4)

        # Moisture affects saturation (more moisture = more saturated greens)
        moisture_factor = 0.9 + (env_data.moisture * 0.2)

        # Temperature affects warmth (higher temp = more red/yellow tint)
        temp_shift = (env_data.temperature - 0.5) * 20

        # Apply micro-variation using simple hash-based noise
        variation_seed = (world_x * 73 + world_y * 37) % 100
        micro_variation = (variation_seed / 100.0 - 0.5) * 0.1  # ±5% variation

        # Apply all variations
        r = int(r * brightness_factor * (1 + micro_variation) + temp_shift)
        g = int(g * brightness_factor * moisture_factor * (1 + micro_variation))
        b = int(b * brightness_factor * (1 + micro_variation) - temp_shift * 0.5)

        # Clamp to valid RGB range
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))

        return (r, g, b)


def create_environmental_terrain_mapper() -> EnvironmentalTerrainMapper:
    """
    Create an environmental terrain mapper with default configuration.

    Returns:
        EnvironmentalTerrainMapper instance with default settings
    """
    return EnvironmentalTerrainMapper()
