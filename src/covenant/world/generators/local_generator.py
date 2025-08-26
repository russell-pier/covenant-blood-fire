"""
Local Scale Generator for the 3-tiered world generation system.

This module generates detailed 32×32 meter local maps from regional terrain data,
creating sub-terrain detail, harvestable resources, animal spawn areas, and 3D structure.
Based on examples/local_generator.py but integrated with the new architecture.
"""

import random
import math
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Dict, Set, Optional

from ..data.scale_types import ViewScale, CoordinateSystem, LocalCoordinate
from ..data.tilemap import LocalTerrain, get_tile
from .regional_generator import RegionalTile, TerrainSubtype, HierarchicalNoise


class ZLevel(Enum):
    """3D Z-levels for local terrain"""
    DEEP_UNDERGROUND = -2  # Deep cave systems
    UNDERGROUND = -1       # Shallow caves, cellars
    SURFACE = 0           # Ground level
    ELEVATED = 1          # Platforms, hills, trees
    HIGH = 2              # Tall trees, cliffs, towers


class ResourceType(Enum):
    """Harvestable resource types"""
    # Renewable biological resources
    BERRIES = "berries"
    NUTS = "nuts"
    HERBS = "herbs"
    MUSHROOMS = "mushrooms"
    HONEY = "honey"
    GAME_TRAIL = "game_trail"  # Animal hunting spot
    FISH = "fish"
    
    # Harvestable materials
    BRANCHES = "branches"
    LOGS = "logs"
    BARK = "bark"
    REEDS = "reeds"
    CLAY = "clay"
    FLINT = "flint"
    STONES = "stones"
    
    # Mineral resources
    IRON_ORE = "iron_ore"
    COPPER_ORE = "copper_ore"
    SALT = "salt"
    GEMS = "gems"
    COAL = "coal"
    
    # Water resources
    FRESH_WATER = "fresh_water"
    MINERAL_WATER = "mineral_water"


class AnimalSpawnType(Enum):
    """Animal spawn types"""
    SMALL_GAME = "small_game"    # Rabbits, birds
    LARGE_GAME = "large_game"    # Deer, elk
    PREDATORS = "predators"      # Wolves, bears
    LIVESTOCK = "livestock"      # Sheep, cattle (domesticated)
    FISH = "fish"               # Swimming in water
    INSECTS = "insects"         # Bees, etc.


class StructuralFeature(Enum):
    """3D structural features"""
    CAVE_MOUTH = "cave_mouth"         # Entrance to underground levels
    MOUNTAIN_LEDGE = "mountain_ledge" # Access to elevated levels  
    CLIFF_FACE = "cliff_face"         # Vertical barrier
    NATURAL_RAMP = "natural_ramp"     # Gradual elevation change
    TREE_TRUNK = "tree_trunk"         # Climbable to elevated level
    ROCK_PILE = "rock_pile"           # Climbable obstacle
    WATER_FORD = "water_ford"         # River crossing point
    FALLEN_TREE_BRIDGE = "fallen_tree_bridge"  # Natural bridge


@dataclass
class LocalTile:
    """Individual 1×1 meter tile data"""
    # Coordinates
    x: int
    y: int
    
    # Terrain detail
    parent_regional_terrain: TerrainSubtype
    sub_terrain: LocalTerrain
    precise_elevation: float  # Meter-level elevation
    
    # 3D structure
    z_level: ZLevel
    structural_feature: Optional[StructuralFeature]
    blocks_movement: bool
    blocks_line_of_sight: bool
    can_access_upper_level: bool
    can_access_lower_level: bool
    
    # Resources
    harvestable_resource: Optional[ResourceType]
    resource_quantity: int  # How much resource (0-5)
    resource_respawn_time: float  # Days to respawn (0 = finite)
    
    # Animals
    animal_spawn_point: Optional[AnimalSpawnType]
    spawn_frequency: float  # 0.0-1.0 chance per day
    max_animals: int  # Maximum animals that can spawn here
    
    # Properties
    movement_cost: float  # 0.5-3.0 multiplier for movement
    concealment: float   # 0.0-1.0 how well this hides creatures
    fertility: float     # 0.0-1.0 for plant growth
    
    # Display
    char: str
    fg_color: Tuple[int, int, int]
    bg_color: Tuple[int, int, int]


@dataclass
class AnimalSpawnArea:
    """Defines an area where animals spawn"""
    spawn_type: AnimalSpawnType
    center_x: float
    center_y: float
    radius: float
    population_capacity: int
    preferred_terrain: List[LocalTerrain]


@dataclass
class ResourceCluster:
    """Resource concentration within the local area"""
    resource_type: ResourceType
    center_x: float
    center_y: float
    radius: float
    density: float  # 0.0-1.0
    quality: float  # 0.0-1.0 affects yield


class LocalScaleGenerator:
    """Generates detailed 32×32 meter local maps from regional terrain data"""
    
    def __init__(self, seed: int):
        self.seed = seed
        self.noise = HierarchicalNoise(seed + 2000)  # Offset from regional generator
        
        # Local parameters
        self.chunk_size = CoordinateSystem.LOCAL_SIZE[0]  # 32
        self.max_resource_clusters = 6
        self.max_animal_areas = 4
        self.max_structural_features = 8
        
        # Generation scales
        self.micro_terrain_scale = 0.8    # Sub-terrain variation (1 tile = 1 meter)
        self.elevation_detail_scale = 1.2  # Centimeter-level elevation
        self.resource_scale = 0.4         # Resource distribution
        self.structure_scale = 0.3        # Structural feature placement
        
        # Generated data
        self.resource_clusters: List[ResourceCluster] = []
        self.animal_areas: List[AnimalSpawnArea] = []
    
    def generate_local_chunk(self, regional_tile: RegionalTile, 
                           neighboring_regional_tiles: Dict[str, RegionalTile],
                           world_context: Dict = None) -> List[List[LocalTile]]:
        """Generate detailed 32×32 meter chunk from regional tile data"""
        
        print(f"Generating local chunk for {regional_tile.terrain_subtype.value}...")
        
        if world_context is None:
            world_context = {}
        
        # Initialize local map
        local_map = self._initialize_local_map(regional_tile)
        
        # Phase 1: Generate sub-terrain patterns
        print("  1. Generating sub-terrain...")
        self._generate_sub_terrain(local_map, regional_tile, neighboring_regional_tiles)
        
        # Phase 2: Add precise elevation detail  
        print("  2. Adding precise elevation...")
        self._generate_precise_elevation(local_map, regional_tile)
        
        # Phase 3: Define 3D structure and Z-levels
        print("  3. Defining 3D structure...")
        self._define_z_level_structure(local_map, regional_tile)
        
        # Phase 4: Place harvestable resources
        print("  4. Placing harvestable resources...")
        self._place_harvestable_resources(local_map, regional_tile)
        
        # Phase 5: Define animal spawn areas
        print("  5. Defining animal spawn areas...")
        self._define_animal_spawn_areas(local_map, regional_tile)
        
        # Phase 6: Calculate movement costs and properties
        print("  6. Calculating movement costs...")
        self._calculate_movement_costs(local_map, regional_tile)
        
        # Phase 7: Generate display representation
        print("  7. Generating display representation...")
        self._generate_display_chars(local_map)
        
        print("  Local generation complete!")
        return local_map
    
    def get_local_tile(self, local_map: List[List[LocalTile]], 
                      meter_x: int, meter_y: int) -> Optional[LocalTile]:
        """Get local tile at specific coordinates"""
        if (0 <= meter_x < self.chunk_size and 
            0 <= meter_y < self.chunk_size and
            local_map):
            return local_map[meter_y][meter_x]
        return None
    
    def _initialize_local_map(self, regional_tile: RegionalTile) -> List[List[LocalTile]]:
        """Initialize empty local map with basic data"""
        local_map = []
        
        for y in range(self.chunk_size):
            row = []
            for x in range(self.chunk_size):
                tile = LocalTile(
                    x=x, y=y,
                    parent_regional_terrain=regional_tile.terrain_subtype,
                    sub_terrain=self._get_default_sub_terrain(regional_tile.terrain_subtype),
                    precise_elevation=regional_tile.micro_elevation,
                    z_level=ZLevel.SURFACE,
                    structural_feature=None,
                    blocks_movement=False,
                    blocks_line_of_sight=False,
                    can_access_upper_level=False,
                    can_access_lower_level=False,
                    harvestable_resource=None,
                    resource_quantity=0,
                    resource_respawn_time=0.0,
                    animal_spawn_point=None,
                    spawn_frequency=0.0,
                    max_animals=0,
                    movement_cost=1.0,
                    concealment=0.0,
                    fertility=regional_tile.fertility,
                    char=".",
                    fg_color=(128, 128, 128),
                    bg_color=(64, 64, 64)
                )
                row.append(tile)
            local_map.append(row)
        
        return local_map
    
    def _get_default_sub_terrain(self, terrain_subtype: TerrainSubtype) -> LocalTerrain:
        """Get default sub-terrain for a regional terrain subtype"""
        terrain_mapping = {
            TerrainSubtype.PLAINS: LocalTerrain.GRASS_PATCH,
            TerrainSubtype.ROLLING_HILLS: LocalTerrain.SHORT_GRASS,
            TerrainSubtype.MEADOWS: LocalTerrain.TALL_GRASS,
            TerrainSubtype.SHRUBLAND: LocalTerrain.THORNY_BUSHES,
            TerrainSubtype.DENSE_FOREST: LocalTerrain.MATURE_TREES,
            TerrainSubtype.LIGHT_WOODLAND: LocalTerrain.YOUNG_TREES,
            TerrainSubtype.FOREST_CLEARING: LocalTerrain.GRASS_PATCH,
            TerrainSubtype.OLD_GROWTH: LocalTerrain.MATURE_TREES,
            TerrainSubtype.SAND_DUNES: LocalTerrain.SANDY_SOIL,
            TerrainSubtype.ROCKY_DESERT: LocalTerrain.ROCKY_GROUND,
            TerrainSubtype.BADLANDS: LocalTerrain.BARE_EARTH,
            TerrainSubtype.OASIS: LocalTerrain.GRASS_PATCH,
            TerrainSubtype.STEEP_SLOPES: LocalTerrain.ROCKY_GROUND,
            TerrainSubtype.GENTLE_SLOPES: LocalTerrain.GRASS_PATCH,
            TerrainSubtype.MOUNTAIN_VALLEY: LocalTerrain.GRASS_PATCH,
            TerrainSubtype.ALPINE_MEADOW: LocalTerrain.SHORT_GRASS,
            TerrainSubtype.CLIFFS: LocalTerrain.ROCKY_GROUND,
            TerrainSubtype.DEEP_WATER: LocalTerrain.DEEP_WATER,
            TerrainSubtype.SHALLOW_WATER: LocalTerrain.SHALLOW_WATER,
            TerrainSubtype.RAPIDS: LocalTerrain.SHALLOW_WATER,
            TerrainSubtype.CALM_POOLS: LocalTerrain.DEEP_WATER,
            TerrainSubtype.MARSH: LocalTerrain.MUDDY_GROUND,
            TerrainSubtype.SWAMP: LocalTerrain.MUDDY_GROUND,
            TerrainSubtype.BOG: LocalTerrain.MOSS_COVERED,
            TerrainSubtype.FLOODPLAIN: LocalTerrain.GRASS_PATCH,
            TerrainSubtype.PERMAFROST: LocalTerrain.BARE_EARTH,
            TerrainSubtype.TUNDRA_HILLS: LocalTerrain.SHORT_GRASS,
            TerrainSubtype.ICE_FIELDS: LocalTerrain.BARE_EARTH,
        }
        
        return terrain_mapping.get(terrain_subtype, LocalTerrain.GRASS_PATCH)

    def _get_terrain_sub_types(self, terrain_subtype: TerrainSubtype) -> List[LocalTerrain]:
        """Get possible sub-terrain types for a regional terrain subtype"""
        terrain_subtypes = {
            TerrainSubtype.PLAINS: [
                LocalTerrain.GRASS_PATCH, LocalTerrain.SHORT_GRASS,
                LocalTerrain.BARE_EARTH, LocalTerrain.DIRT_PATH
            ],
            TerrainSubtype.ROLLING_HILLS: [
                LocalTerrain.SHORT_GRASS, LocalTerrain.GRASS_PATCH,
                LocalTerrain.ROCKY_GROUND, LocalTerrain.LOOSE_STONES
            ],
            TerrainSubtype.MEADOWS: [
                LocalTerrain.TALL_GRASS, LocalTerrain.WILDFLOWERS,
                LocalTerrain.GRASS_PATCH, LocalTerrain.SHORT_GRASS
            ],
            TerrainSubtype.SHRUBLAND: [
                LocalTerrain.THORNY_BUSHES, LocalTerrain.BERRY_BUSHES,
                LocalTerrain.SHORT_GRASS, LocalTerrain.BARE_EARTH
            ],
            TerrainSubtype.DENSE_FOREST: [
                LocalTerrain.MATURE_TREES, LocalTerrain.FALLEN_LOG,
                LocalTerrain.LEAF_LITTER, LocalTerrain.MOSS_COVERED
            ],
            TerrainSubtype.LIGHT_WOODLAND: [
                LocalTerrain.YOUNG_TREES, LocalTerrain.GRASS_PATCH,
                LocalTerrain.LEAF_LITTER, LocalTerrain.WILDFLOWERS
            ],
            TerrainSubtype.FOREST_CLEARING: [
                LocalTerrain.GRASS_PATCH, LocalTerrain.TALL_GRASS,
                LocalTerrain.WILDFLOWERS, LocalTerrain.YOUNG_TREES
            ],
            TerrainSubtype.SAND_DUNES: [
                LocalTerrain.SANDY_SOIL, LocalTerrain.BARE_EARTH,
                LocalTerrain.LOOSE_STONES, LocalTerrain.PEBBLES
            ],
            TerrainSubtype.ROCKY_DESERT: [
                LocalTerrain.ROCKY_GROUND, LocalTerrain.LOOSE_STONES,
                LocalTerrain.SMALL_BOULDER, LocalTerrain.BARE_EARTH
            ],
            TerrainSubtype.STEEP_SLOPES: [
                LocalTerrain.ROCKY_GROUND, LocalTerrain.SMALL_BOULDER,
                LocalTerrain.LARGE_BOULDER, LocalTerrain.LOOSE_STONES
            ],
            TerrainSubtype.CLIFFS: [
                LocalTerrain.ROCKY_GROUND, LocalTerrain.LARGE_BOULDER,
                LocalTerrain.ROCK_OUTCROP, LocalTerrain.LOOSE_STONES
            ],
            TerrainSubtype.MARSH: [
                LocalTerrain.MUDDY_GROUND, LocalTerrain.REED_BEDS,
                LocalTerrain.SHALLOW_WATER, LocalTerrain.MOSS_COVERED
            ],
            TerrainSubtype.SWAMP: [
                LocalTerrain.MUDDY_GROUND, LocalTerrain.SHALLOW_WATER,
                LocalTerrain.MOSS_COVERED, LocalTerrain.FALLEN_LOG
            ],
        }

        return terrain_subtypes.get(terrain_subtype, [LocalTerrain.GRASS_PATCH])

    def _generate_sub_terrain(self, local_map: List[List[LocalTile]],
                             regional_tile: RegionalTile,
                             neighboring_regional_tiles: Dict[str, RegionalTile]):
        """Generate sub-terrain patterns within the local area"""
        available_subtypes = self._get_terrain_sub_types(regional_tile.terrain_subtype)

        for y in range(self.chunk_size):
            for x in range(self.chunk_size):
                tile = local_map[y][x]

                # Base terrain noise
                terrain_noise = self.noise.octave_noise(
                    x * self.micro_terrain_scale,
                    y * self.micro_terrain_scale,
                    octaves=3,
                    persistence=0.6
                )

                # Select sub-terrain based on noise
                if len(available_subtypes) == 1:
                    tile.sub_terrain = available_subtypes[0]
                else:
                    noise_index = int((terrain_noise + 1) * 0.5 * len(available_subtypes))
                    noise_index = max(0, min(len(available_subtypes) - 1, noise_index))
                    tile.sub_terrain = available_subtypes[noise_index]

                # Special cases for water features
                if regional_tile.has_minor_river:
                    self._apply_water_features(tile, x, y, regional_tile)

                # Edge effects from neighboring regional tiles
                self._apply_neighbor_influence(tile, x, y, neighboring_regional_tiles)

    def _apply_water_features(self, tile: LocalTile, x: int, y: int, regional_tile: RegionalTile):
        """Apply water features from regional rivers"""
        # Simplified water feature application
        # In a full implementation, this would trace actual river paths

        if regional_tile.river_size > 0:
            # Create water features along certain paths
            if (x + y) % 8 == 0:  # Simple pattern for demonstration
                if regional_tile.river_size == 1:  # Stream
                    tile.sub_terrain = LocalTerrain.SHALLOW_WATER
                elif regional_tile.river_size == 2:  # Creek
                    tile.sub_terrain = LocalTerrain.SHALLOW_WATER
                else:  # River
                    tile.sub_terrain = LocalTerrain.DEEP_WATER

                # Add water edges
                if random.random() < 0.3:
                    tile.sub_terrain = LocalTerrain.WATER_EDGE

    def _apply_neighbor_influence(self, tile: LocalTile, x: int, y: int,
                                 neighboring_regional_tiles: Dict[str, RegionalTile]):
        """Apply influence from neighboring regional tiles at chunk edges"""
        edge_distance = 3  # How far edge effects penetrate

        # Check if we're near an edge
        near_north = y < edge_distance
        near_south = y >= self.chunk_size - edge_distance
        near_west = x < edge_distance
        near_east = x >= self.chunk_size - edge_distance

        if not (near_north or near_south or near_west or near_east):
            return

        # Apply neighbor terrain influence
        influences = []

        if near_north and "north" in neighboring_regional_tiles:
            influences.append(neighboring_regional_tiles["north"].terrain_subtype)
        if near_south and "south" in neighboring_regional_tiles:
            influences.append(neighboring_regional_tiles["south"].terrain_subtype)
        if near_west and "west" in neighboring_regional_tiles:
            influences.append(neighboring_regional_tiles["west"].terrain_subtype)
        if near_east and "east" in neighboring_regional_tiles:
            influences.append(neighboring_regional_tiles["east"].terrain_subtype)

        # Create transition sub-terrain
        for neighbor_terrain in influences:
            if neighbor_terrain != tile.parent_regional_terrain and random.random() < 0.15:
                transition_subtypes = self._get_terrain_sub_types(neighbor_terrain)
                if transition_subtypes:
                    tile.sub_terrain = random.choice(transition_subtypes)

    def _generate_precise_elevation(self, local_map: List[List[LocalTile]],
                                   regional_tile: RegionalTile):
        """Generate precise meter-level elevation detail"""
        base_elevation = regional_tile.micro_elevation

        for y in range(self.chunk_size):
            for x in range(self.chunk_size):
                tile = local_map[y][x]

                # Fine elevation noise (centimeter level)
                elevation_noise = self.noise.octave_noise(
                    x * self.elevation_detail_scale,
                    y * self.elevation_detail_scale,
                    octaves=4,
                    persistence=0.4
                )

                # Scale elevation variation based on sub-terrain
                elevation_scale = self._get_sub_terrain_elevation_scale(tile.sub_terrain)
                precise_elevation = base_elevation + (elevation_noise * elevation_scale)

                # Add terrain-specific elevation patterns
                if tile.sub_terrain in [LocalTerrain.SMALL_BOULDER, LocalTerrain.LARGE_BOULDER]:
                    # Boulders are elevated
                    boulder_height = 0.5 if tile.sub_terrain == LocalTerrain.SMALL_BOULDER else 1.5
                    precise_elevation += boulder_height

                elif tile.sub_terrain in [LocalTerrain.SHALLOW_WATER, LocalTerrain.DEEP_WATER]:
                    # Water is lower
                    water_depth = 0.2 if tile.sub_terrain == LocalTerrain.SHALLOW_WATER else 0.8
                    precise_elevation -= water_depth

                tile.precise_elevation = precise_elevation

    def _get_sub_terrain_elevation_scale(self, sub_terrain: LocalTerrain) -> float:
        """Get elevation variation scale for sub-terrain type"""
        scales = {
            LocalTerrain.GRASS_PATCH: 0.1,
            LocalTerrain.SHORT_GRASS: 0.05,
            LocalTerrain.TALL_GRASS: 0.08,
            LocalTerrain.BARE_EARTH: 0.15,
            LocalTerrain.ROCKY_GROUND: 0.3,
            LocalTerrain.SANDY_SOIL: 0.2,
            LocalTerrain.MUDDY_GROUND: 0.05,
            LocalTerrain.MOSS_COVERED: 0.03,
            LocalTerrain.LEAF_LITTER: 0.1,
            LocalTerrain.WILDFLOWERS: 0.08,
            LocalTerrain.THORNY_BUSHES: 0.2,
            LocalTerrain.BERRY_BUSHES: 0.15,
            LocalTerrain.YOUNG_TREES: 0.3,
            LocalTerrain.MATURE_TREES: 0.4,
            LocalTerrain.FALLEN_LOG: 0.5,
            LocalTerrain.SMALL_BOULDER: 0.8,
            LocalTerrain.LARGE_BOULDER: 1.2,
            LocalTerrain.ROCK_OUTCROP: 1.5,
            LocalTerrain.LOOSE_STONES: 0.4,
            LocalTerrain.PEBBLES: 0.1,
            LocalTerrain.SHALLOW_WATER: 0.02,
            LocalTerrain.DEEP_WATER: 0.05,
            LocalTerrain.WATER_EDGE: 0.1,
            LocalTerrain.MUDDY_BANK: 0.08,
            LocalTerrain.REED_BEDS: 0.1,
        }

        return scales.get(sub_terrain, 0.1)

    def _define_z_level_structure(self, local_map: List[List[LocalTile]],
                                 regional_tile: RegionalTile):
        """Define 3D structure and Z-levels"""
        for y in range(self.chunk_size):
            for x in range(self.chunk_size):
                tile = local_map[y][x]

                # Determine Z-level based on sub-terrain and elevation
                tile.z_level = self._determine_z_level(tile)

                # Set movement and sight blocking properties
                tile.blocks_movement = self._blocks_movement(tile.sub_terrain)
                tile.blocks_line_of_sight = self._blocks_line_of_sight(tile.sub_terrain)

                # Determine level access
                tile.can_access_upper_level = self._can_access_upper_level(tile.sub_terrain)
                tile.can_access_lower_level = self._can_access_lower_level(tile.sub_terrain)

                # Add structural features
                if random.random() < 0.05:  # 5% chance
                    tile.structural_feature = self._select_structural_feature(tile, regional_tile)

    def _determine_z_level(self, tile: LocalTile) -> ZLevel:
        """Determine Z-level for a tile"""
        if tile.sub_terrain in [LocalTerrain.SHALLOW_WATER, LocalTerrain.DEEP_WATER]:
            return ZLevel.SURFACE  # Water at surface level
        elif tile.sub_terrain in [LocalTerrain.MATURE_TREES, LocalTerrain.YOUNG_TREES]:
            return ZLevel.ELEVATED  # Trees provide elevated access
        elif tile.sub_terrain in [LocalTerrain.LARGE_BOULDER, LocalTerrain.ROCK_OUTCROP]:
            return ZLevel.ELEVATED  # Large rocks are elevated
        else:
            return ZLevel.SURFACE

    def _blocks_movement(self, sub_terrain: LocalTerrain) -> bool:
        """Check if sub-terrain blocks movement"""
        blocking_terrain = {
            LocalTerrain.LARGE_BOULDER, LocalTerrain.ROCK_OUTCROP,
            LocalTerrain.DEEP_WATER, LocalTerrain.MATURE_TREES
        }
        return sub_terrain in blocking_terrain

    def _blocks_line_of_sight(self, sub_terrain: LocalTerrain) -> bool:
        """Check if sub-terrain blocks line of sight"""
        blocking_terrain = {
            LocalTerrain.LARGE_BOULDER, LocalTerrain.ROCK_OUTCROP,
            LocalTerrain.MATURE_TREES, LocalTerrain.YOUNG_TREES
        }
        return sub_terrain in blocking_terrain

    def _can_access_upper_level(self, sub_terrain: LocalTerrain) -> bool:
        """Check if sub-terrain allows access to upper levels"""
        access_terrain = {
            LocalTerrain.MATURE_TREES, LocalTerrain.YOUNG_TREES,
            LocalTerrain.LARGE_BOULDER, LocalTerrain.ROCK_OUTCROP
        }
        return sub_terrain in access_terrain

    def _can_access_lower_level(self, sub_terrain: LocalTerrain) -> bool:
        """Check if sub-terrain allows access to lower levels"""
        # For now, no lower level access (caves would be added here)
        return False

    def _select_structural_feature(self, tile: LocalTile,
                                  regional_tile: RegionalTile) -> Optional[StructuralFeature]:
        """Select appropriate structural feature for tile"""
        if tile.sub_terrain == LocalTerrain.FALLEN_LOG:
            return StructuralFeature.FALLEN_TREE_BRIDGE
        elif tile.sub_terrain in [LocalTerrain.SHALLOW_WATER, LocalTerrain.WATER_EDGE]:
            return StructuralFeature.WATER_FORD
        elif tile.sub_terrain in [LocalTerrain.LARGE_BOULDER, LocalTerrain.ROCK_OUTCROP]:
            return StructuralFeature.ROCK_PILE
        elif regional_tile.terrain_subtype in [TerrainSubtype.STEEP_SLOPES, TerrainSubtype.CLIFFS]:
            return StructuralFeature.MOUNTAIN_LEDGE

        return None

    def _place_harvestable_resources(self, local_map: List[List[LocalTile]],
                                    regional_tile: RegionalTile):
        """Place harvestable resources throughout the local area"""
        from .local_generator_methods import place_harvestable_resources
        place_harvestable_resources(self, local_map, regional_tile)

    def _define_animal_spawn_areas(self, local_map: List[List[LocalTile]],
                                  regional_tile: RegionalTile):
        """Define animal spawn areas throughout the local chunk"""
        from .local_generator_methods import define_animal_spawn_areas
        define_animal_spawn_areas(self, local_map, regional_tile)

    def _calculate_movement_costs(self, local_map: List[List[LocalTile]],
                                 regional_tile: RegionalTile):
        """Calculate movement costs and other properties for each tile"""
        from .local_generator_methods import calculate_movement_costs
        calculate_movement_costs(self, local_map, regional_tile)

    def _generate_display_chars(self, local_map: List[List[LocalTile]]):
        """Generate display characters and colors for each tile"""
        from .local_generator_methods import generate_display_chars
        generate_display_chars(self, local_map)
