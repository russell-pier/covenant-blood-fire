"""
Regional Scale Generator for the 3-tiered world generation system.

This module generates detailed 32×32 regional maps from world-scale biome data,
creating terrain subtypes, minor water systems, landmarks, and resource areas.
Based on examples/regional_generator.py but integrated with the new architecture.
"""

import random
import math
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Dict, Set, Optional

from ..data.scale_types import ViewScale, CoordinateSystem, RegionalCoordinate
from ..data.tilemap import BiomeType, TerrainSubtype, get_tile
from .world_generator import WorldTile, HierarchicalNoise


class LandmarkType(Enum):
    """Special landmark features within regions"""
    # Cave systems
    CAVE_ENTRANCE = "cave_entrance"
    CAVERN_COMPLEX = "cavern_complex"
    DEEP_CAVE = "deep_cave"
    UNDERGROUND_LAKE = "underground_lake"
    
    # Mountain features
    MOUNTAIN_PASS = "mountain_pass"
    SCENIC_OVERLOOK = "scenic_overlook"
    NATURAL_BRIDGE = "natural_bridge"
    HIDDEN_VALLEY = "hidden_valley"
    
    # Water features
    WATERFALL = "waterfall"
    NATURAL_SPRING = "natural_spring"
    DEEP_POOL = "deep_pool"
    RIVER_CROSSING = "river_crossing"
    
    # Unique terrain
    STANDING_STONES = "standing_stones"
    CRATER = "crater"
    NATURAL_ARCH = "natural_arch"
    UNUSUAL_ROCK_FORMATION = "unusual_rock_formation"
    
    # Resource landmarks
    VISIBLE_ORE_OUTCROP = "visible_ore_outcrop"
    ANCIENT_GROVE = "ancient_grove"
    MINERAL_SPRING = "mineral_spring"
    SALT_FLAT = "salt_flat"


class ResourceConcentration(Enum):
    """Resource concentration areas within regions"""
    WOOD_GROVE = "wood_grove"
    STONE_QUARRY = "stone_quarry"
    METAL_DEPOSIT = "metal_deposit"
    FERTILE_SOIL = "fertile_soil"
    HUNTING_GROUNDS = "hunting_grounds"
    FISHING_SPOT = "fishing_spot"
    HERB_PATCH = "herb_patch"
    CLAY_DEPOSITS = "clay_deposits"


@dataclass
class RegionalTile:
    """Complete data for one regional tile (block)"""
    # Coordinates
    x: int
    y: int
    
    # Terrain
    parent_biome: BiomeType  # From world scale
    terrain_subtype: TerrainSubtype
    micro_elevation: float  # Fine elevation detail within region
    
    # Water features
    has_minor_river: bool
    river_size: int  # 0=none, 1=stream, 2=creek, 3=river
    is_lake: bool
    lake_id: Optional[int]
    water_flow_direction: Optional[Tuple[int, int]]
    
    # Special features
    landmark: Optional[LandmarkType]
    resource_concentration: Optional[ResourceConcentration]
    fertility: float  # 0.0-1.0 for agricultural potential
    accessibility: float  # 0.0-1.0 for ease of movement
    
    # Boundaries and transitions
    terrain_boundary: bool  # Marks transition between terrain types
    biome_edge: bool  # Edge of parent biome influence
    
    # Display
    char: str
    fg_color: Tuple[int, int, int]
    bg_color: Tuple[int, int, int]


@dataclass
class LakeSystem:
    """Represents a lake within the region"""
    id: int
    center_x: float
    center_y: float
    size: float  # Radius
    depth: float
    is_seasonal: bool
    connects_to_river: bool


@dataclass
class RiverSegment:
    """Segment of a minor river system"""
    id: int
    path: List[Tuple[int, int]]
    size: int  # 1=stream, 2=creek, 3=river
    source_type: str  # "spring", "lake", "mountain", "world_river"
    connects_to_world_river: bool


class RegionalScaleGenerator:
    """Generates detailed 32×32 regional maps from world-scale biome data"""
    
    def __init__(self, seed: int):
        self.seed = seed
        self.noise = HierarchicalNoise(seed + 1000)  # Offset from world generator
        
        # Regional parameters
        self.region_size = CoordinateSystem.REGIONAL_SIZE[0]  # 32
        self.max_lakes = 6
        self.max_minor_rivers = 8
        self.landmark_density = 0.03  # 3% chance per tile
        self.resource_cluster_density = 0.05  # 5% chance per tile
        
        # Scale factors for regional features
        self.terrain_detail_scale = 0.15    # Terrain variation within biomes
        self.elevation_detail_scale = 0.2   # Fine elevation details
        self.water_scale = 0.1              # Small water bodies
        self.landmark_scale = 0.08          # Landmark placement
        
        # Generated data
        self.lakes: List[LakeSystem] = []
        self.rivers: List[RiverSegment] = []
    
    def generate_regional_map(self, world_tile_data: WorldTile, 
                             neighboring_world_tiles: Dict[str, WorldTile]) -> List[List[RegionalTile]]:
        """Generate 32×32 regional map from world-scale tile data"""
        
        print(f"Generating regional map for {world_tile_data.biome.value} biome...")
        
        # Initialize regional map
        regional_map = self._initialize_regional_map(world_tile_data)
        
        # Phase 1: Generate terrain subtypes within biome
        print("  1. Generating terrain subtypes...")
        self._generate_terrain_subtypes(regional_map, world_tile_data, neighboring_world_tiles)
        
        # Phase 2: Add fine elevation detail
        print("  2. Adding elevation detail...")
        self._generate_micro_elevation(regional_map, world_tile_data)
        
        # Phase 3: Generate minor water systems
        print("  3. Generating water systems...")
        self._generate_minor_water_systems(regional_map, world_tile_data)
        
        # Phase 4: Place landmark features
        print("  4. Placing landmarks...")
        self._place_landmark_features(regional_map, world_tile_data)
        
        # Phase 5: Assign resource concentrations
        print("  5. Assigning resource concentrations...")
        self._assign_resource_concentrations(regional_map, world_tile_data)
        
        # Phase 6: Mark terrain boundaries and transitions
        print("  6. Marking terrain boundaries...")
        self._mark_terrain_boundaries(regional_map)
        
        # Phase 7: Calculate accessibility and fertility
        print("  7. Calculating tile properties...")
        self._calculate_tile_properties(regional_map, world_tile_data)
        
        # Phase 8: Generate display representation
        print("  8. Generating display representation...")
        self._generate_display_chars(regional_map)
        
        print("  Regional generation complete!")
        return regional_map
    
    def get_regional_tile(self, regional_map: List[List[RegionalTile]], 
                         block_x: int, block_y: int) -> Optional[RegionalTile]:
        """Get regional tile at specific coordinates"""
        if (0 <= block_x < self.region_size and 
            0 <= block_y < self.region_size and
            regional_map):
            return regional_map[block_y][block_x]
        return None
    
    def _initialize_regional_map(self, world_tile_data: WorldTile) -> List[List[RegionalTile]]:
        """Initialize empty regional map with basic data"""
        regional_map = []
        
        for y in range(self.region_size):
            row = []
            for x in range(self.region_size):
                tile = RegionalTile(
                    x=x, y=y,
                    parent_biome=world_tile_data.biome,
                    terrain_subtype=self._get_default_terrain_subtype(world_tile_data.biome),
                    micro_elevation=0.0,
                    has_minor_river=False,
                    river_size=0,
                    is_lake=False,
                    lake_id=None,
                    water_flow_direction=None,
                    landmark=None,
                    resource_concentration=None,
                    fertility=0.5,
                    accessibility=0.5,
                    terrain_boundary=False,
                    biome_edge=False,
                    char=".",
                    fg_color=(128, 128, 128),
                    bg_color=(64, 64, 64)
                )
                row.append(tile)
            regional_map.append(row)
        
        return regional_map
    
    def _get_default_terrain_subtype(self, biome: BiomeType) -> TerrainSubtype:
        """Get default terrain subtype for a biome"""
        biome_to_terrain = {
            BiomeType.GRASSLAND: TerrainSubtype.PLAINS,
            BiomeType.TEMPERATE_FOREST: TerrainSubtype.LIGHT_WOODLAND,
            BiomeType.TROPICAL_FOREST: TerrainSubtype.DENSE_FOREST,
            BiomeType.DESERT: TerrainSubtype.SAND_DUNES,  # Will be mapped to appropriate desert type
            BiomeType.TAIGA: TerrainSubtype.DENSE_FOREST,
            BiomeType.TUNDRA: TerrainSubtype.PERMAFROST,
            BiomeType.HIGH_MOUNTAINS: TerrainSubtype.STEEP_SLOPES,
            BiomeType.MOUNTAIN_FOREST: TerrainSubtype.GENTLE_SLOPES,
            BiomeType.SAVANNA: TerrainSubtype.SHRUBLAND,
            BiomeType.WETLAND: TerrainSubtype.MARSH,
            # Ocean biomes
            BiomeType.DEEP_OCEAN: TerrainSubtype.DEEP_WATER,
            BiomeType.SHALLOW_SEA: TerrainSubtype.SHALLOW_WATER,
            BiomeType.COASTAL_WATERS: TerrainSubtype.SHALLOW_WATER,
        }
        
        return biome_to_terrain.get(biome, TerrainSubtype.PLAINS)
    
    def _get_biome_terrain_subtypes(self, biome: BiomeType) -> List[TerrainSubtype]:
        """Get possible terrain subtypes for a biome"""
        biome_subtypes = {
            BiomeType.GRASSLAND: [
                TerrainSubtype.PLAINS, TerrainSubtype.ROLLING_HILLS, 
                TerrainSubtype.MEADOWS, TerrainSubtype.SHRUBLAND
            ],
            BiomeType.TEMPERATE_FOREST: [
                TerrainSubtype.DENSE_FOREST, TerrainSubtype.LIGHT_WOODLAND,
                TerrainSubtype.FOREST_CLEARING, TerrainSubtype.OLD_GROWTH
            ],
            BiomeType.TROPICAL_FOREST: [
                TerrainSubtype.DENSE_FOREST, TerrainSubtype.OLD_GROWTH,
                TerrainSubtype.FOREST_CLEARING
            ],
            BiomeType.DESERT: [
                TerrainSubtype.SAND_DUNES, TerrainSubtype.ROCKY_DESERT,
                TerrainSubtype.BADLANDS, TerrainSubtype.OASIS
            ],
            BiomeType.HIGH_MOUNTAINS: [
                TerrainSubtype.STEEP_SLOPES, TerrainSubtype.CLIFFS,
                TerrainSubtype.ALPINE_MEADOW, TerrainSubtype.MOUNTAIN_VALLEY
            ],
            BiomeType.MOUNTAIN_FOREST: [
                TerrainSubtype.GENTLE_SLOPES, TerrainSubtype.MOUNTAIN_VALLEY,
                TerrainSubtype.DENSE_FOREST, TerrainSubtype.ALPINE_MEADOW
            ],
            BiomeType.WETLAND: [
                TerrainSubtype.MARSH, TerrainSubtype.SWAMP,
                TerrainSubtype.BOG, TerrainSubtype.FLOODPLAIN
            ],
            BiomeType.TUNDRA: [
                TerrainSubtype.PERMAFROST, TerrainSubtype.TUNDRA_HILLS,
                TerrainSubtype.ICE_FIELDS
            ]
        }
        
        return biome_subtypes.get(biome, [TerrainSubtype.PLAINS])

    def _generate_terrain_subtypes(self, regional_map: List[List[RegionalTile]],
                                  world_tile_data: WorldTile,
                                  neighboring_world_tiles: Dict[str, WorldTile]):
        """Generate terrain subtypes within the biome"""
        available_subtypes = self._get_biome_terrain_subtypes(world_tile_data.biome)

        # Create terrain zones using noise
        for y in range(self.region_size):
            for x in range(self.region_size):
                tile = regional_map[y][x]

                # Base terrain noise
                terrain_noise = self.noise.octave_noise(
                    x * self.terrain_detail_scale,
                    y * self.terrain_detail_scale,
                    octaves=3,
                    persistence=0.6
                )

                # Select terrain subtype based on noise and biome
                if len(available_subtypes) == 1:
                    tile.terrain_subtype = available_subtypes[0]
                else:
                    # Map noise to terrain types
                    noise_index = int((terrain_noise + 1) * 0.5 * len(available_subtypes))
                    noise_index = max(0, min(len(available_subtypes) - 1, noise_index))
                    tile.terrain_subtype = available_subtypes[noise_index]

                # Special cases based on world tile properties
                if world_tile_data.has_major_river and random.random() < 0.3:
                    # Near major rivers, create floodplains or water features
                    if world_tile_data.biome in [BiomeType.GRASSLAND, BiomeType.TEMPERATE_FOREST]:
                        tile.terrain_subtype = TerrainSubtype.FLOODPLAIN

                # Edge effects from neighboring biomes
                self._apply_neighbor_influence(tile, x, y, neighboring_world_tiles)

    def _apply_neighbor_influence(self, tile: RegionalTile, x: int, y: int,
                                 neighboring_world_tiles: Dict[str, WorldTile]):
        """Apply influence from neighboring world tiles at region edges"""
        edge_distance = 4  # How far edge effects penetrate

        # Check if we're near an edge
        near_north = y < edge_distance
        near_south = y >= self.region_size - edge_distance
        near_west = x < edge_distance
        near_east = x >= self.region_size - edge_distance

        if not (near_north or near_south or near_west or near_east):
            return

        # Apply neighbor biome influence
        influences = []

        if near_north and "north" in neighboring_world_tiles:
            influences.append(neighboring_world_tiles["north"].biome)
        if near_south and "south" in neighboring_world_tiles:
            influences.append(neighboring_world_tiles["south"].biome)
        if near_west and "west" in neighboring_world_tiles:
            influences.append(neighboring_world_tiles["west"].biome)
        if near_east and "east" in neighboring_world_tiles:
            influences.append(neighboring_world_tiles["east"].biome)

        # Create transition zones
        for neighbor_biome in influences:
            if neighbor_biome != tile.parent_biome and random.random() < 0.2:
                # Create transition terrain
                transition_subtypes = self._get_transition_terrain(tile.parent_biome, neighbor_biome)
                if transition_subtypes:
                    tile.terrain_subtype = random.choice(transition_subtypes)
                    tile.biome_edge = True

    def _get_transition_terrain(self, biome1: BiomeType, biome2: BiomeType) -> List[TerrainSubtype]:
        """Get terrain subtypes appropriate for transitions between biomes"""
        # Simplified transition logic
        transitions = {
            (BiomeType.GRASSLAND, BiomeType.TEMPERATE_FOREST): [TerrainSubtype.LIGHT_WOODLAND, TerrainSubtype.SHRUBLAND],
            (BiomeType.TEMPERATE_FOREST, BiomeType.GRASSLAND): [TerrainSubtype.FOREST_CLEARING, TerrainSubtype.MEADOWS],
            (BiomeType.DESERT, BiomeType.GRASSLAND): [TerrainSubtype.SHRUBLAND],
            (BiomeType.GRASSLAND, BiomeType.DESERT): [TerrainSubtype.SHRUBLAND],
            (BiomeType.MOUNTAIN_FOREST, BiomeType.HIGH_MOUNTAINS): [TerrainSubtype.ALPINE_MEADOW],
            (BiomeType.HIGH_MOUNTAINS, BiomeType.MOUNTAIN_FOREST): [TerrainSubtype.GENTLE_SLOPES],
        }

        return transitions.get((biome1, biome2), [])

    def _generate_micro_elevation(self, regional_map: List[List[RegionalTile]],
                                 world_tile_data: WorldTile):
        """Generate fine elevation detail within the region"""
        base_elevation = world_tile_data.final_elevation

        for y in range(self.region_size):
            for x in range(self.region_size):
                tile = regional_map[y][x]

                # Fine elevation noise
                elevation_noise = self.noise.octave_noise(
                    x * self.elevation_detail_scale,
                    y * self.elevation_detail_scale,
                    octaves=4,
                    persistence=0.5
                )

                # Scale elevation variation based on terrain type
                elevation_scale = self._get_elevation_scale(tile.terrain_subtype)
                micro_elevation = elevation_noise * elevation_scale

                # Add terrain-specific elevation patterns
                if tile.terrain_subtype in [TerrainSubtype.ROLLING_HILLS, TerrainSubtype.TUNDRA_HILLS]:
                    # Add hill patterns
                    hill_noise = self.noise.octave_noise(
                        x * 0.3, y * 0.3, octaves=2
                    )
                    if hill_noise > 0.3:
                        micro_elevation += hill_noise * 50

                elif tile.terrain_subtype == TerrainSubtype.CLIFFS:
                    # Sharp elevation changes for cliffs
                    cliff_noise = self.noise.ridge_noise(x * 0.4, y * 0.4)
                    micro_elevation += cliff_noise * 100

                tile.micro_elevation = micro_elevation

    def _get_elevation_scale(self, terrain_subtype: TerrainSubtype) -> float:
        """Get elevation variation scale for terrain subtype"""
        scales = {
            TerrainSubtype.PLAINS: 10.0,
            TerrainSubtype.ROLLING_HILLS: 30.0,
            TerrainSubtype.STEEP_SLOPES: 80.0,
            TerrainSubtype.CLIFFS: 150.0,
            TerrainSubtype.MOUNTAIN_VALLEY: 20.0,
            TerrainSubtype.ALPINE_MEADOW: 25.0,
            TerrainSubtype.SAND_DUNES: 15.0,
            TerrainSubtype.ROCKY_DESERT: 40.0,
            TerrainSubtype.BADLANDS: 60.0,
            TerrainSubtype.DENSE_FOREST: 20.0,
            TerrainSubtype.LIGHT_WOODLAND: 15.0,
            TerrainSubtype.MARSH: 5.0,
            TerrainSubtype.SWAMP: 8.0,
            TerrainSubtype.DEEP_WATER: 2.0,
            TerrainSubtype.SHALLOW_WATER: 3.0,
        }

        return scales.get(terrain_subtype, 15.0)

    def _generate_minor_water_systems(self, regional_map: List[List[RegionalTile]],
                                     world_tile_data: WorldTile):
        """Generate minor rivers, streams, and lakes"""
        self.lakes = []
        self.rivers = []

        # Generate lakes first
        self._generate_lakes(regional_map, world_tile_data)

        # Generate minor rivers and streams
        self._generate_minor_rivers(regional_map, world_tile_data)

        # Apply water features to tiles
        self._apply_water_features(regional_map)

    def _generate_lakes(self, regional_map: List[List[RegionalTile]],
                       world_tile_data: WorldTile):
        """Generate lake systems within the region"""
        # Determine number of lakes based on biome and precipitation
        lake_probability = self._get_lake_probability(world_tile_data)
        num_lakes = 0

        for _ in range(self.max_lakes):
            if random.random() < lake_probability:
                num_lakes += 1

        # Place lakes
        for lake_id in range(num_lakes):
            attempts = 0
            while attempts < 20:  # Try to place lake
                center_x = random.uniform(4, self.region_size - 4)
                center_y = random.uniform(4, self.region_size - 4)
                size = random.uniform(1.5, 4.0)

                # Check if location is suitable
                if self._is_suitable_lake_location(regional_map, center_x, center_y, size):
                    lake = LakeSystem(
                        id=lake_id,
                        center_x=center_x,
                        center_y=center_y,
                        size=size,
                        depth=random.uniform(2.0, 8.0),
                        is_seasonal=random.random() < 0.2,
                        connects_to_river=random.random() < 0.4
                    )
                    self.lakes.append(lake)
                    break

                attempts += 1

    def _get_lake_probability(self, world_tile_data: WorldTile) -> float:
        """Calculate probability of lakes based on world tile data"""
        base_prob = 0.1

        # Increase probability with precipitation
        precip_bonus = world_tile_data.precipitation * 0.3

        # Biome modifiers
        biome_modifiers = {
            BiomeType.WETLAND: 0.5,
            BiomeType.TEMPERATE_FOREST: 0.2,
            BiomeType.TAIGA: 0.3,
            BiomeType.TUNDRA: 0.4,
            BiomeType.HIGH_MOUNTAINS: 0.3,
            BiomeType.DESERT: 0.02,
            BiomeType.GRASSLAND: 0.1,
        }

        biome_modifier = biome_modifiers.get(world_tile_data.biome, 0.1)

        return min(0.8, base_prob + precip_bonus + biome_modifier)

    def _is_suitable_lake_location(self, regional_map: List[List[RegionalTile]],
                                  center_x: float, center_y: float, size: float) -> bool:
        """Check if location is suitable for a lake"""
        # Check for conflicts with existing lakes
        for existing_lake in self.lakes:
            distance = math.sqrt((center_x - existing_lake.center_x)**2 +
                               (center_y - existing_lake.center_y)**2)
            if distance < (size + existing_lake.size + 2):
                return False

        # Check terrain suitability
        for dy in range(-int(size), int(size) + 1):
            for dx in range(-int(size), int(size) + 1):
                x, y = int(center_x + dx), int(center_y + dy)
                if 0 <= x < self.region_size and 0 <= y < self.region_size:
                    tile = regional_map[y][x]
                    # Avoid placing lakes on steep terrain
                    if tile.terrain_subtype in [TerrainSubtype.STEEP_SLOPES, TerrainSubtype.CLIFFS]:
                        return False

        return True

    def _generate_minor_rivers(self, regional_map: List[List[RegionalTile]],
                              world_tile_data: WorldTile):
        """Generate minor river systems"""
        # Simplified river generation for now
        river_probability = world_tile_data.precipitation * 0.4

        if world_tile_data.has_major_river:
            river_probability += 0.3  # More minor rivers near major ones

        num_rivers = 0
        for _ in range(self.max_minor_rivers):
            if random.random() < river_probability:
                num_rivers += 1

        # Generate river paths
        for river_id in range(num_rivers):
            self._generate_river_path(regional_map, river_id, world_tile_data)

    def _generate_river_path(self, regional_map: List[List[RegionalTile]],
                            river_id: int, world_tile_data: WorldTile):
        """Generate a single river path"""
        # Start from high elevation or lake
        start_x, start_y = self._find_river_source(regional_map)
        if start_x is None:
            return

        path = [(start_x, start_y)]
        current_x, current_y = start_x, start_y

        # Follow elevation gradient downward
        for _ in range(20):  # Max river length
            next_x, next_y = self._find_next_river_tile(regional_map, current_x, current_y)
            if next_x is None or (next_x, next_y) in path:
                break

            path.append((next_x, next_y))
            current_x, current_y = next_x, next_y

            # Stop if we reach edge or water
            if (current_x <= 0 or current_x >= self.region_size - 1 or
                current_y <= 0 or current_y >= self.region_size - 1):
                break

        if len(path) > 3:  # Only keep rivers with reasonable length
            river = RiverSegment(
                id=river_id,
                path=path,
                size=random.randint(1, 2),  # Stream or creek
                source_type="spring",
                connects_to_world_river=world_tile_data.has_major_river and random.random() < 0.3
            )
            self.rivers.append(river)

    def _find_river_source(self, regional_map: List[List[RegionalTile]]) -> Tuple[Optional[int], Optional[int]]:
        """Find suitable river source location"""
        # Look for high elevation areas
        best_elevation = float('-inf')
        best_location = (None, None)

        for y in range(2, self.region_size - 2):
            for x in range(2, self.region_size - 2):
                tile = regional_map[y][x]
                if (tile.micro_elevation > best_elevation and
                    not tile.is_lake and
                    tile.terrain_subtype not in [TerrainSubtype.DEEP_WATER, TerrainSubtype.SHALLOW_WATER]):
                    best_elevation = tile.micro_elevation
                    best_location = (x, y)

        return best_location

    def _find_next_river_tile(self, regional_map: List[List[RegionalTile]],
                             current_x: int, current_y: int) -> Tuple[Optional[int], Optional[int]]:
        """Find next tile in river path (following elevation gradient)"""
        current_elevation = regional_map[current_y][current_x].micro_elevation
        best_elevation = current_elevation
        best_location = (None, None)

        # Check adjacent tiles
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                nx, ny = current_x + dx, current_y + dy
                if 0 <= nx < self.region_size and 0 <= ny < self.region_size:
                    neighbor_elevation = regional_map[ny][nx].micro_elevation
                    if neighbor_elevation < best_elevation:
                        best_elevation = neighbor_elevation
                        best_location = (nx, ny)

        return best_location

    def _apply_water_features(self, regional_map: List[List[RegionalTile]]):
        """Apply water features to regional tiles"""
        # Apply lakes
        for lake in self.lakes:
            for y in range(self.region_size):
                for x in range(self.region_size):
                    distance = math.sqrt((x - lake.center_x)**2 + (y - lake.center_y)**2)
                    if distance <= lake.size:
                        tile = regional_map[y][x]
                        tile.is_lake = True
                        tile.lake_id = lake.id
                        tile.terrain_subtype = TerrainSubtype.DEEP_WATER if distance < lake.size * 0.6 else TerrainSubtype.SHALLOW_WATER

        # Apply rivers
        for river in self.rivers:
            for x, y in river.path:
                if 0 <= x < self.region_size and 0 <= y < self.region_size:
                    tile = regional_map[y][x]
                    tile.has_minor_river = True
                    tile.river_size = river.size

                    # Set appropriate water terrain
                    if river.size == 1:  # Stream
                        # Keep existing terrain but mark as having water
                        pass
                    elif river.size == 2:  # Creek
                        tile.terrain_subtype = TerrainSubtype.SHALLOW_WATER
                    else:  # River
                        tile.terrain_subtype = TerrainSubtype.DEEP_WATER

    def _place_landmark_features(self, regional_map: List[List[RegionalTile]],
                                world_tile_data: WorldTile):
        """Place special landmark features"""
        for y in range(self.region_size):
            for x in range(self.region_size):
                tile = regional_map[y][x]

                if random.random() < self.landmark_density:
                    landmark = self._select_appropriate_landmark(tile, world_tile_data)
                    if landmark:
                        tile.landmark = landmark

    def _select_appropriate_landmark(self, tile: RegionalTile,
                                   world_tile_data: WorldTile) -> Optional[LandmarkType]:
        """Select appropriate landmark for tile based on terrain and biome"""
        terrain = tile.terrain_subtype
        biome = world_tile_data.biome

        # Terrain-specific landmarks
        if terrain in [TerrainSubtype.STEEP_SLOPES, TerrainSubtype.CLIFFS]:
            return random.choice([LandmarkType.CAVE_ENTRANCE, LandmarkType.SCENIC_OVERLOOK,
                                LandmarkType.NATURAL_BRIDGE])

        elif terrain in [TerrainSubtype.MOUNTAIN_VALLEY, TerrainSubtype.ALPINE_MEADOW]:
            return random.choice([LandmarkType.HIDDEN_VALLEY, LandmarkType.NATURAL_SPRING])

        elif terrain in [TerrainSubtype.DEEP_WATER, TerrainSubtype.SHALLOW_WATER]:
            return random.choice([LandmarkType.DEEP_POOL, LandmarkType.WATERFALL])

        elif terrain in [TerrainSubtype.DENSE_FOREST, TerrainSubtype.OLD_GROWTH]:
            return random.choice([LandmarkType.ANCIENT_GROVE, LandmarkType.STANDING_STONES])

        elif terrain in [TerrainSubtype.ROCKY_DESERT, TerrainSubtype.BADLANDS]:
            return random.choice([LandmarkType.NATURAL_ARCH, LandmarkType.UNUSUAL_ROCK_FORMATION])

        # Biome-specific landmarks
        if biome == BiomeType.DESERT and random.random() < 0.1:
            return LandmarkType.OASIS

        elif biome in [BiomeType.HIGH_MOUNTAINS, BiomeType.MOUNTAIN_FOREST] and random.random() < 0.15:
            return LandmarkType.MINERAL_SPRING

        return None

    def _assign_resource_concentrations(self, regional_map: List[List[RegionalTile]],
                                       world_tile_data: WorldTile):
        """Assign resource concentration areas"""
        for y in range(self.region_size):
            for x in range(self.region_size):
                tile = regional_map[y][x]

                if random.random() < self.resource_cluster_density:
                    resource = self._select_appropriate_resource(tile, world_tile_data)
                    if resource:
                        tile.resource_concentration = resource

    def _select_appropriate_resource(self, tile: RegionalTile,
                                   world_tile_data: WorldTile) -> Optional[ResourceConcentration]:
        """Select appropriate resource concentration for tile"""
        terrain = tile.terrain_subtype
        biome = world_tile_data.biome

        # Terrain-specific resources
        if terrain in [TerrainSubtype.DENSE_FOREST, TerrainSubtype.OLD_GROWTH]:
            return ResourceConcentration.WOOD_GROVE

        elif terrain in [TerrainSubtype.STEEP_SLOPES, TerrainSubtype.CLIFFS, TerrainSubtype.ROCKY_DESERT]:
            return random.choice([ResourceConcentration.STONE_QUARRY, ResourceConcentration.METAL_DEPOSIT])

        elif terrain in [TerrainSubtype.PLAINS, TerrainSubtype.MEADOWS, TerrainSubtype.FLOODPLAIN]:
            return ResourceConcentration.FERTILE_SOIL

        elif terrain in [TerrainSubtype.DEEP_WATER, TerrainSubtype.SHALLOW_WATER] and tile.is_lake:
            return ResourceConcentration.FISHING_SPOT

        elif terrain in [TerrainSubtype.MARSH, TerrainSubtype.SWAMP]:
            return random.choice([ResourceConcentration.HERB_PATCH, ResourceConcentration.CLAY_DEPOSITS])

        # Biome-specific resources
        if biome in [BiomeType.GRASSLAND, BiomeType.SAVANNA]:
            return ResourceConcentration.HUNTING_GROUNDS

        return None

    def _mark_terrain_boundaries(self, regional_map: List[List[RegionalTile]]):
        """Mark boundaries between different terrain types"""
        for y in range(self.region_size):
            for x in range(self.region_size):
                tile = regional_map[y][x]
                current_terrain = tile.terrain_subtype

                # Check adjacent tiles for terrain changes
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue

                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.region_size and 0 <= ny < self.region_size:
                            neighbor_terrain = regional_map[ny][nx].terrain_subtype
                            if neighbor_terrain != current_terrain:
                                tile.terrain_boundary = True
                                break
                    if tile.terrain_boundary:
                        break

    def _calculate_tile_properties(self, regional_map: List[List[RegionalTile]],
                                  world_tile_data: WorldTile):
        """Calculate fertility and accessibility for each tile"""
        for y in range(self.region_size):
            for x in range(self.region_size):
                tile = regional_map[y][x]

                # Calculate fertility
                tile.fertility = self._calculate_fertility(tile, world_tile_data)

                # Calculate accessibility
                tile.accessibility = self._calculate_accessibility(tile)

    def _calculate_fertility(self, tile: RegionalTile, world_tile_data: WorldTile) -> float:
        """Calculate agricultural fertility for a tile"""
        base_fertility = 0.3

        # Terrain modifiers
        terrain_fertility = {
            TerrainSubtype.PLAINS: 0.8,
            TerrainSubtype.MEADOWS: 0.9,
            TerrainSubtype.FLOODPLAIN: 1.0,
            TerrainSubtype.ROLLING_HILLS: 0.6,
            TerrainSubtype.FOREST_CLEARING: 0.7,
            TerrainSubtype.MARSH: 0.4,
            TerrainSubtype.SWAMP: 0.2,
            TerrainSubtype.SAND_DUNES: 0.1,
            TerrainSubtype.ROCKY_DESERT: 0.05,
            TerrainSubtype.STEEP_SLOPES: 0.1,
            TerrainSubtype.CLIFFS: 0.0,
        }

        fertility = terrain_fertility.get(tile.terrain_subtype, base_fertility)

        # Climate modifiers
        fertility *= world_tile_data.precipitation  # More rain = more fertile
        fertility *= (1.0 - abs(world_tile_data.temperature - 0.6))  # Moderate temps best

        # Resource bonuses
        if tile.resource_concentration == ResourceConcentration.FERTILE_SOIL:
            fertility += 0.3

        # Water proximity bonus
        if tile.has_minor_river or tile.is_lake:
            fertility += 0.2

        return max(0.0, min(1.0, fertility))

    def _calculate_accessibility(self, tile: RegionalTile) -> float:
        """Calculate ease of movement through a tile"""
        base_accessibility = 0.5

        # Terrain modifiers
        terrain_accessibility = {
            TerrainSubtype.PLAINS: 1.0,
            TerrainSubtype.ROLLING_HILLS: 0.8,
            TerrainSubtype.MEADOWS: 0.9,
            TerrainSubtype.LIGHT_WOODLAND: 0.7,
            TerrainSubtype.DENSE_FOREST: 0.4,
            TerrainSubtype.STEEP_SLOPES: 0.3,
            TerrainSubtype.CLIFFS: 0.1,
            TerrainSubtype.MARSH: 0.3,
            TerrainSubtype.SWAMP: 0.2,
            TerrainSubtype.DEEP_WATER: 0.0,
            TerrainSubtype.SHALLOW_WATER: 0.1,
            TerrainSubtype.SAND_DUNES: 0.6,
            TerrainSubtype.ROCKY_DESERT: 0.5,
        }

        accessibility = terrain_accessibility.get(tile.terrain_subtype, base_accessibility)

        # Elevation modifier
        if abs(tile.micro_elevation) > 50:
            accessibility *= 0.8  # Steep areas harder to traverse

        # River crossing penalty
        if tile.has_minor_river and tile.river_size > 1:
            accessibility *= 0.7

        return max(0.0, min(1.0, accessibility))

    def _generate_display_chars(self, regional_map: List[List[RegionalTile]]):
        """Generate display characters and colors for each tile"""
        for y in range(self.region_size):
            for x in range(self.region_size):
                tile = regional_map[y][x]

                # Get tile configuration from tilemap
                tile_config = get_tile(ViewScale.REGIONAL, tile.terrain_subtype, use_variant=True)

                tile.char = tile_config.char
                tile.fg_color = tile_config.fg_color
                tile.bg_color = tile_config.bg_color

                # Special overrides for landmarks and resources
                if tile.landmark:
                    tile.char = self._get_landmark_char(tile.landmark)
                elif tile.resource_concentration:
                    tile.char = self._get_resource_char(tile.resource_concentration)

    def _get_landmark_char(self, landmark: LandmarkType) -> str:
        """Get display character for landmark"""
        landmark_chars = {
            LandmarkType.CAVE_ENTRANCE: "◊",
            LandmarkType.SCENIC_OVERLOOK: "▲",
            LandmarkType.NATURAL_BRIDGE: "∩",
            LandmarkType.WATERFALL: "‖",
            LandmarkType.NATURAL_SPRING: "○",
            LandmarkType.STANDING_STONES: "⌘",
            LandmarkType.ANCIENT_GROVE: "♠",
            LandmarkType.NATURAL_ARCH: "∩",
            LandmarkType.MINERAL_SPRING: "◉",
        }
        return landmark_chars.get(landmark, "?")

    def _get_resource_char(self, resource: ResourceConcentration) -> str:
        """Get display character for resource concentration"""
        resource_chars = {
            ResourceConcentration.WOOD_GROVE: "♠",
            ResourceConcentration.STONE_QUARRY: "▪",
            ResourceConcentration.METAL_DEPOSIT: "●",
            ResourceConcentration.FERTILE_SOIL: "≡",
            ResourceConcentration.FISHING_SPOT: "≈",
            ResourceConcentration.HERB_PATCH: "*",
            ResourceConcentration.CLAY_DEPOSITS: "■",
        }
        return resource_chars.get(resource, "?")
