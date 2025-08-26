"""
Scale types and coordinate system for the 3-tiered world generation system.

This module defines the core data structures and coordinate conversion utilities
for managing the hierarchical world system: World → Regional → Local scales.
"""

import math
from enum import Enum
from dataclasses import dataclass
from typing import Tuple, Dict, Optional, NamedTuple


class ViewScale(Enum):
    """The three viewing scales in the hierarchical world system"""
    WORLD = "world"        # 128×96 sectors, continental view
    REGIONAL = "regional"  # 32×32 blocks per world sector
    LOCAL = "local"       # 32×32 meters per regional block


class WorldLayer(Enum):
    """3D world layers (preserved from existing system)."""
    UNDERGROUND = 0
    SURFACE = 1
    MOUNTAINS = 2


@dataclass
class ScaleConfig:
    """Configuration parameters for each viewing scale"""
    name: str
    map_size: Tuple[int, int]  # Width×height of the map at this scale
    tile_size_meters: int      # How many meters each tile represents
    movement_speed: float      # Camera movement speed multiplier
    generation_cost: str       # Relative computational cost: "low", "medium", "high"
    cache_priority: int        # Cache priority (1=highest, 3=lowest)


class WorldCoordinate(NamedTuple):
    """World-scale coordinate (sector level)"""
    sector_x: int
    sector_y: int


class RegionalCoordinate(NamedTuple):
    """Regional-scale coordinate (block within sector)"""
    world_x: int
    world_y: int
    block_x: int
    block_y: int


class LocalCoordinate(NamedTuple):
    """Local-scale coordinate (meter within block)"""
    world_x: int
    world_y: int
    block_x: int
    block_y: int
    meter_x: int
    meter_y: int


class AbsoluteCoordinate(NamedTuple):
    """Absolute coordinate in meters from world origin"""
    x: int
    y: int


def get_scale_config(scale: ViewScale) -> ScaleConfig:
    """Get configuration for a specific scale"""
    configs = {
        ViewScale.WORLD: ScaleConfig(
            name="World",
            map_size=(128, 96),
            tile_size_meters=1024 * 1024,  # Each world sector = 1,048,576 m²
            movement_speed=1.0,
            generation_cost="low",
            cache_priority=1
        ),
        ViewScale.REGIONAL: ScaleConfig(
            name="Regional",
            map_size=(32, 32),
            tile_size_meters=1024,  # Each regional block = 1,024 m²
            movement_speed=0.8,
            generation_cost="medium",
            cache_priority=2
        ),
        ViewScale.LOCAL: ScaleConfig(
            name="Local",
            map_size=(32, 32),
            tile_size_meters=1,  # Each local tile = 1 m²
            movement_speed=0.6,
            generation_cost="high",
            cache_priority=3
        )
    }
    return configs[scale]


class CoordinateSystem:
    """Manages coordinate conversions between all scales"""

    # Scale relationships - these define the hierarchical structure
    WORLD_SIZE = (128, 96)          # World sectors
    REGIONAL_SIZE = (32, 32)        # Regional blocks per world sector
    LOCAL_SIZE = (32, 32)           # Local meters per regional block

    # Derived constants
    TOTAL_REGIONAL_SIZE = (WORLD_SIZE[0] * REGIONAL_SIZE[0], WORLD_SIZE[1] * REGIONAL_SIZE[1])
    TOTAL_LOCAL_SIZE = (TOTAL_REGIONAL_SIZE[0] * LOCAL_SIZE[0], TOTAL_REGIONAL_SIZE[1] * LOCAL_SIZE[1])

    @staticmethod
    def world_to_absolute(world_coord: WorldCoordinate) -> AbsoluteCoordinate:
        """Convert world coordinate to absolute meters"""
        abs_x = world_coord.sector_x * CoordinateSystem.REGIONAL_SIZE[0] * CoordinateSystem.LOCAL_SIZE[0]
        abs_y = world_coord.sector_y * CoordinateSystem.REGIONAL_SIZE[1] * CoordinateSystem.LOCAL_SIZE[1]
        return AbsoluteCoordinate(abs_x, abs_y)

    @staticmethod
    def regional_to_absolute(regional_coord: RegionalCoordinate) -> AbsoluteCoordinate:
        """Convert regional coordinate to absolute meters"""
        abs_x = (regional_coord.world_x * CoordinateSystem.REGIONAL_SIZE[0] +
                regional_coord.block_x) * CoordinateSystem.LOCAL_SIZE[0]
        abs_y = (regional_coord.world_y * CoordinateSystem.REGIONAL_SIZE[1] +
                regional_coord.block_y) * CoordinateSystem.LOCAL_SIZE[1]
        return AbsoluteCoordinate(abs_x, abs_y)

    @staticmethod
    def local_to_absolute(local_coord: LocalCoordinate) -> AbsoluteCoordinate:
        """Convert local coordinate to absolute meters"""
        abs_x = ((local_coord.world_x * CoordinateSystem.REGIONAL_SIZE[0] +
                 local_coord.block_x) * CoordinateSystem.LOCAL_SIZE[0] +
                 local_coord.meter_x)
        abs_y = ((local_coord.world_y * CoordinateSystem.REGIONAL_SIZE[1] +
                 local_coord.block_y) * CoordinateSystem.LOCAL_SIZE[1] +
                 local_coord.meter_y)
        return AbsoluteCoordinate(abs_x, abs_y)

    @staticmethod
    def absolute_to_world(abs_coord: AbsoluteCoordinate) -> WorldCoordinate:
        """Convert absolute coordinate to world coordinate"""
        sector_x = abs_coord.x // (CoordinateSystem.REGIONAL_SIZE[0] * CoordinateSystem.LOCAL_SIZE[0])
        sector_y = abs_coord.y // (CoordinateSystem.REGIONAL_SIZE[1] * CoordinateSystem.LOCAL_SIZE[1])
        return WorldCoordinate(sector_x, sector_y)

    @staticmethod
    def absolute_to_regional(abs_coord: AbsoluteCoordinate) -> RegionalCoordinate:
        """Convert absolute coordinate to regional coordinate"""
        # First get world coordinates
        world_coord = CoordinateSystem.absolute_to_world(abs_coord)

        # Calculate block within world sector
        world_base_x = world_coord.sector_x * CoordinateSystem.REGIONAL_SIZE[0] * CoordinateSystem.LOCAL_SIZE[0]
        world_base_y = world_coord.sector_y * CoordinateSystem.REGIONAL_SIZE[1] * CoordinateSystem.LOCAL_SIZE[1]

        relative_x = abs_coord.x - world_base_x
        relative_y = abs_coord.y - world_base_y

        block_x = relative_x // CoordinateSystem.LOCAL_SIZE[0]
        block_y = relative_y // CoordinateSystem.LOCAL_SIZE[1]

        return RegionalCoordinate(world_coord.sector_x, world_coord.sector_y, block_x, block_y)

    @staticmethod
    def absolute_to_local(abs_coord: AbsoluteCoordinate) -> LocalCoordinate:
        """Convert absolute coordinate to local coordinate"""
        # First get regional coordinates
        regional_coord = CoordinateSystem.absolute_to_regional(abs_coord)

        # Calculate meter within regional block
        block_base_x = ((regional_coord.world_x * CoordinateSystem.REGIONAL_SIZE[0] +
                        regional_coord.block_x) * CoordinateSystem.LOCAL_SIZE[0])
        block_base_y = ((regional_coord.world_y * CoordinateSystem.REGIONAL_SIZE[1] +
                        regional_coord.block_y) * CoordinateSystem.LOCAL_SIZE[1])

        meter_x = abs_coord.x - block_base_x
        meter_y = abs_coord.y - block_base_y

        return LocalCoordinate(
            regional_coord.world_x, regional_coord.world_y,
            regional_coord.block_x, regional_coord.block_y,
            meter_x, meter_y
        )

    @staticmethod
    def get_world_bounds() -> Tuple[AbsoluteCoordinate, AbsoluteCoordinate]:
        """Get absolute coordinate bounds for the entire world"""
        min_coord = AbsoluteCoordinate(0, 0)
        max_coord = AbsoluteCoordinate(
            CoordinateSystem.TOTAL_LOCAL_SIZE[0] - 1,
            CoordinateSystem.TOTAL_LOCAL_SIZE[1] - 1
        )
        return min_coord, max_coord

    @staticmethod
    def get_regional_bounds(world_x: int, world_y: int) -> Tuple[AbsoluteCoordinate, AbsoluteCoordinate]:
        """Get absolute coordinate bounds for a specific world sector"""
        min_coord = CoordinateSystem.world_to_absolute(WorldCoordinate(world_x, world_y))
        max_coord = AbsoluteCoordinate(
            min_coord.x + (CoordinateSystem.REGIONAL_SIZE[0] * CoordinateSystem.LOCAL_SIZE[0]) - 1,
            min_coord.y + (CoordinateSystem.REGIONAL_SIZE[1] * CoordinateSystem.LOCAL_SIZE[1]) - 1
        )
        return min_coord, max_coord

    @staticmethod
    def get_local_bounds(world_x: int, world_y: int, block_x: int, block_y: int) -> Tuple[AbsoluteCoordinate, AbsoluteCoordinate]:
        """Get absolute coordinate bounds for a specific regional block"""
        min_coord = CoordinateSystem.regional_to_absolute(RegionalCoordinate(world_x, world_y, block_x, block_y))
        max_coord = AbsoluteCoordinate(
            min_coord.x + CoordinateSystem.LOCAL_SIZE[0] - 1,
            min_coord.y + CoordinateSystem.LOCAL_SIZE[1] - 1
        )
        return min_coord, max_coord

    @staticmethod
    def is_valid_world_coordinate(world_x: int, world_y: int) -> bool:
        """Check if world coordinate is within valid bounds"""
        return (0 <= world_x < CoordinateSystem.WORLD_SIZE[0] and
                0 <= world_y < CoordinateSystem.WORLD_SIZE[1])

    @staticmethod
    def is_valid_regional_coordinate(world_x: int, world_y: int, block_x: int, block_y: int) -> bool:
        """Check if regional coordinate is within valid bounds"""
        return (CoordinateSystem.is_valid_world_coordinate(world_x, world_y) and
                0 <= block_x < CoordinateSystem.REGIONAL_SIZE[0] and
                0 <= block_y < CoordinateSystem.REGIONAL_SIZE[1])

    @staticmethod
    def is_valid_local_coordinate(world_x: int, world_y: int, block_x: int, block_y: int,
                                meter_x: int, meter_y: int) -> bool:
        """Check if local coordinate is within valid bounds"""
        return (CoordinateSystem.is_valid_regional_coordinate(world_x, world_y, block_x, block_y) and
                0 <= meter_x < CoordinateSystem.LOCAL_SIZE[0] and
                0 <= meter_y < CoordinateSystem.LOCAL_SIZE[1])


class ScaleTransition:
    """Utilities for smooth transitions between scales"""

    @staticmethod
    def calculate_equivalent_position(from_scale: ViewScale, to_scale: ViewScale,
                                    from_x: float, from_y: float) -> Tuple[float, float]:
        """Calculate equivalent position when transitioning between scales"""
        if from_scale == to_scale:
            return from_x, from_y

        # Convert to absolute coordinates first
        if from_scale == ViewScale.WORLD:
            abs_coord = CoordinateSystem.world_to_absolute(WorldCoordinate(int(from_x), int(from_y)))
        elif from_scale == ViewScale.REGIONAL:
            # Need world context for regional coordinates - this is simplified
            # In practice, you'd need the current world sector
            abs_coord = AbsoluteCoordinate(int(from_x), int(from_y))
        else:  # LOCAL
            abs_coord = AbsoluteCoordinate(int(from_x), int(from_y))

        # Convert to target scale
        if to_scale == ViewScale.WORLD:
            world_coord = CoordinateSystem.absolute_to_world(abs_coord)
            return float(world_coord.sector_x), float(world_coord.sector_y)
        elif to_scale == ViewScale.REGIONAL:
            regional_coord = CoordinateSystem.absolute_to_regional(abs_coord)
            return float(regional_coord.block_x), float(regional_coord.block_y)
        else:  # LOCAL
            local_coord = CoordinateSystem.absolute_to_local(abs_coord)
            return float(local_coord.meter_x), float(local_coord.meter_y)

    @staticmethod
    def get_transition_duration(from_scale: ViewScale, to_scale: ViewScale) -> float:
        """Get recommended transition duration between scales"""
        scale_distances = {
            (ViewScale.WORLD, ViewScale.REGIONAL): 0.4,
            (ViewScale.REGIONAL, ViewScale.LOCAL): 0.3,
            (ViewScale.WORLD, ViewScale.LOCAL): 0.6,
        }

        # Handle reverse transitions
        key = (from_scale, to_scale)
        reverse_key = (to_scale, from_scale)

        return scale_distances.get(key, scale_distances.get(reverse_key, 0.3))
