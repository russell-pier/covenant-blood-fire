# Local Scale Generator - Complete Implementation
# Generates detailed 32×32 meter chunks from regional terrain data

import random
import math
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Dict, Set, Optional

class SubTerrain(Enum):
    # Ground surfaces
    DIRT_PATH = "dirt_path"
    GRASS_PATCH = "grass_patch"
    BARE_EARTH = "bare_earth"
    ROCKY_GROUND = "rocky_ground"
    SANDY_SOIL = "sandy_soil"
    MUDDY_GROUND = "muddy_ground"
    MOSS_COVERED = "moss_covered"
    LEAF_LITTER = "leaf_litter"
    
    # Vegetation subtypes  
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
    
    # Water subtypes
    SHALLOW_WATER = "shallow_water"
    DEEP_WATER = "deep_water"
    WATER_EDGE = "water_edge"
    MUDDY_BANK = "muddy_bank"
    REED_BEDS = "reed_beds"

class ZLevel(Enum):
    DEEP_UNDERGROUND = -2  # Deep cave systems
    UNDERGROUND = -1       # Shallow caves, cellars
    SURFACE = 0           # Ground level
    ELEVATED = 1          # Platforms, hills, trees
    HIGH = 2              # Tall trees, cliffs, towers

class ResourceType(Enum):
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
    SMALL_GAME = "small_game"    # Rabbits, birds
    LARGE_GAME = "large_game"    # Deer, elk
    PREDATORS = "predators"      # Wolves, bears
    LIVESTOCK = "livestock"      # Sheep, cattle (domesticated)
    FISH = "fish"               # Swimming in water
    INSECTS = "insects"         # Bees, etc.

class StructuralFeature(Enum):
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
    parent_regional_terrain: 'TerrainSubtype'
    sub_terrain: SubTerrain
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
    preferred_terrain: List[SubTerrain]

@dataclass
class ResourceCluster:
    """Resource concentration within the local area"""
    resource_type: ResourceType
    center_x: float
    center_y: float
    radius: float
    density: float  # 0.0-1.0
    quality: float  # 0.0-1.0 affects yield

class LocalGenerator:
    """Generates detailed 32×32 meter local maps from regional terrain data"""
    
    def __init__(self, seed: int):
        self.seed = seed
        self.noise = HierarchicalNoise(seed + 2000)  # Offset from regional generator
        
        # Local parameters
        self.chunk_size = 32  # 32×32 meters
        self.max_resource_clusters = 6
        self.max_animal_areas = 4
        self.max_structural_features = 8
        
        # Generation scales
        self.micro_terrain_scale = 0.8    # Sub-terrain variation (1 tile = 1 meter)
        self.elevation_detail_scale = 1.2  # Centimeter-level elevation
        self.resource_scale = 0.4         # Resource distribution
        self.structure_scale = 0.3        # Structural feature placement
        
    def generate_local_chunk(self, regional_tile: 'RegionalTile', 
                           neighboring_regional_tiles: Dict[str, 'RegionalTile'],
                           world_context: Dict) -> List[List[LocalTile]]:
        """Generate detailed 32×32 meter chunk from regional tile data"""
        
        print(f"Generating local chunk for {regional_tile.terrain_subtype.value}...")
        
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
        
        # Phase 4: Place structural features (cave entrances, etc.)
        print("  4. Placing structural features...")
        self._place_structural_features(local_map, regional_tile)
        
        # Phase 5: Place harvestable resources
        print("  5. Placing harvestable resources...")
        self._place_harvestable_resources(local_map, regional_tile, world_context)
        
        # Phase 6: Define animal spawn areas
        print("  6. Defining animal spawn areas...")
        self._define_animal_spawn_areas(local_map, regional_tile)
        
        # Phase 7: Calculate movement and gameplay properties
        print("  7. Calculating movement properties...")
        self._calculate_movement_properties(local_map, regional_tile)
        
        # Phase 8: Generate visual representation
        print("  8. Generating visual representation...")
        self._generate_local_display(local_map, regional_tile)
        
        print("  Local chunk generation complete!")
        return local_map
    
    def _initialize_local_map(self, regional_tile: 'RegionalTile') -> List[List[LocalTile]]:
        """Initialize 32×32 local map with basic data"""
        local_map = []
        
        for y in range(self.chunk_size):
            row = []
            for x in range(self.chunk_size):
                tile = LocalTile(
                    x=x, y=y,
                    parent_regional_terrain=regional_tile.terrain_subtype,
                    sub_terrain=SubTerrain.GRASS_PATCH,  # Will be determined
                    precise_elevation=regional_tile.micro_elevation,  # Base elevation
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
                    fg_color=(100, 100, 100),
                    bg_color=(50, 50, 50)
                )
                row.append(tile)
            local_map.append(row)
        
        return local_map
    
    def _generate_sub_terrain(self, local_map: List[List[LocalTile]], 
                            regional_tile: 'RegionalTile',
                            neighbors: Dict[str, 'RegionalTile']):
        """Generate detailed sub-terrain within regional terrain type"""
        
        # Define sub-terrain distributions for each regional terrain
        subterrain_distributions = {
            TerrainSubtype.PLAINS: {
                SubTerrain.SHORT_GRASS: 0.6,
                SubTerrain.GRASS_PATCH: 0.25,
                SubTerrain.BARE_EARTH: 0.1,
                SubTerrain.WILDFLOWERS: 0.05
            },
            TerrainSubtype.ROLLING_HILLS: {
                SubTerrain.TALL_GRASS: 0.4,
                SubTerrain.SHORT_GRASS: 0.3,
                SubTerrain.ROCKY_GROUND: 0.2,
                SubTerrain.LOOSE_STONES: 0.1
            },
            TerrainSubtype.DENSE_FOREST: {
                SubTerrain.MATURE_TREES: 0.4,
                SubTerrain.LEAF_LITTER: 0.3,
                SubTerrain.YOUNG_TREES: 0.15,
                SubTerrain.MOSS_COVERED: 0.1,
                SubTerrain.FALLEN_LOG: 0.05
            },
            TerrainSubtype.LIGHT_WOODLAND: {
                SubTerrain.YOUNG_TREES: 0.3,
                SubTerrain.GRASS_PATCH: 0.25,
                SubTerrain.LEAF_LITTER: 0.2,
                SubTerrain.BERRY_BUSHES: 0.15,
                SubTerrain.WILDFLOWERS: 0.1
            },
            TerrainSubtype.FOREST_CLEARING: {
                SubTerrain.TALL_GRASS: 0.4,
                SubTerrain.WILDFLOWERS: 0.3,
                SubTerrain.GRASS_PATCH: 0.2,
                SubTerrain.YOUNG_TREES: 0.1
            },
            TerrainSubtype.SAND_DUNES: {
                SubTerrain.SANDY_SOIL: 0.8,
                SubTerrain.BARE_EARTH: 0.15,
                SubTerrain.PEBBLES: 0.05
            },
            TerrainSubtype.ROCKY_DESERT: {
                SubTerrain.ROCKY_GROUND: 0.5,
                SubTerrain.LOOSE_STONES: 0.3,
                SubTerrain.SANDY_SOIL: 0.15,
                SubTerrain.SMALL_BOULDER: 0.05
            },
            TerrainSubtype.STEEP_SLOPES: {
                SubTerrain.ROCKY_GROUND: 0.4,
                SubTerrain.LOOSE_STONES: 0.3,
                SubTerrain.SMALL_BOULDER: 0.2,
                SubTerrain.BARE_EARTH: 0.1
            },
            TerrainSubtype.CLIFFS: {
                SubTerrain.ROCK_OUTCROP: 0.6,
                SubTerrain.ROCKY_GROUND: 0.3,
                SubTerrain.LOOSE_STONES: 0.1
            },
            TerrainSubtype.MARSH: {
                SubTerrain.MUDDY_GROUND: 0.4,
                SubTerrain.REED_BEDS: 0.3,
                SubTerrain.SHALLOW_WATER: 0.2,
                SubTerrain.MOSS_COVERED: 0.1
            },
            TerrainSubtype.MOUNTAIN_VALLEY: {
                SubTerrain.GRASS_PATCH: 0.4,
                SubTerrain.WILDFLOWERS: 0.25,
                SubTerrain.BERRY_BUSHES: 0.2,
                SubTerrain.SMALL_BOULDER: 0.15
            }
        }
        
        # Get distribution for this terrain (with fallback)
        distribution = subterrain_distributions.get(
            regional_tile.terrain_subtype, 
            {SubTerrain.GRASS_PATCH: 1.0}
        )
        
        # Generate sub-terrain using clustered noise
        for y in range(self.chunk_size):
            for x in range(self.chunk_size):
                tile = local_map[y][x]
                
                # Multiple noise layers for realistic clustering
                primary_noise = self.noise.octave_noise(
                    x * self.micro_terrain_scale,
                    y * self.micro_terrain_scale,
                    octaves=3,
                    persistence=0.6
                )
                
                detail_noise = self.noise.octave_noise(
                    x * self.micro_terrain_scale * 2,
                    y * self.micro_terrain_scale * 2,
                    octaves=2,
                    persistence=0.4
                )
                
                # Combine noises for varied terrain selection
                combined_noise = (primary_noise * 0.7 + detail_noise * 0.3 + 1) / 2
                
                # Apply neighbor clustering
                neighbor_influence = self._calculate_neighbor_subterrain_influence(local_map, x, y)
                final_noise = (combined_noise + neighbor_influence) / 2
                
                # Select sub-terrain from distribution
                tile.sub_terrain = self._select_subterrain_from_distribution(distribution, final_noise)
                
                # Apply edge effects from neighboring regional tiles
                if self._is_near_chunk_edge(x, y):
                    tile.sub_terrain = self._apply_neighbor_regional_influence(
                        tile.sub_terrain, neighbors, x, y
                    )
    
    def _calculate_neighbor_subterrain_influence(self, local_map: List[List[LocalTile]], 
                                               x: int, y: int) -> float:
        """Calculate clustering influence from already-processed neighbors"""
        if x == 0 and y == 0:
            return 0.0
        
        subterrain_weights = {}
        total_weight = 0.0
        
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.chunk_size and 0 <= ny < self.chunk_size:
                    # Only check already processed tiles
                    if ny < y or (ny == y and nx < x):
                        neighbor_subterrain = local_map[ny][nx].sub_terrain
                        weight = 1.0 / max(1, abs(dx) + abs(dy))
                        subterrain_weights[neighbor_subterrain] = subterrain_weights.get(neighbor_subterrain, 0) + weight
                        total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        # Return influence toward most common neighbor
        most_common = max(subterrain_weights.keys(), key=lambda k: subterrain_weights[k])
        return subterrain_weights[most_common] / total_weight * 0.4  # 40% clustering influence
    
    def _is_near_chunk_edge(self, x: int, y: int, edge_distance: int = 2) -> bool:
        """Check if tile is near chunk edge"""
        return (x < edge_distance or x >= self.chunk_size - edge_distance or
                y < edge_distance or y >= self.chunk_size - edge_distance)
    
    def _apply_neighbor_regional_influence(self, current_subterrain: SubTerrain,
                                         neighbors: Dict[str, 'RegionalTile'],
                                         x: int, y: int) -> SubTerrain:
        """Apply neighboring regional tile influence at chunk edges"""
        
        # Determine which edge and apply influence
        if x < 2 and 'west' in neighbors:
            return self._create_transition_subterrain(current_subterrain, neighbors['west'])
        elif x >= self.chunk_size - 2 and 'east' in neighbors:
            return self._create_transition_subterrain(current_subterrain, neighbors['east'])
        elif y < 2 and 'north' in neighbors:
            return self._create_transition_subterrain(current_subterrain, neighbors['north'])
        elif y >= self.chunk_size - 2 and 'south' in neighbors:
            return self._create_transition_subterrain(current_subterrain, neighbors['south'])
        
        return current_subterrain
    
    def _create_transition_subterrain(self, base_subterrain: SubTerrain, 
                                    neighbor_regional: 'RegionalTile') -> SubTerrain:
        """Create transition sub-terrain between regional terrain types"""
        
        neighbor_terrain = neighbor_regional.terrain_subtype
        
        # Simple transition rules
        transitions = {
            (TerrainSubtype.FOREST_CLEARING, TerrainSubtype.DENSE_FOREST): SubTerrain.YOUNG_TREES,
            (TerrainSubtype.PLAINS, TerrainSubtype.MARSH): SubTerrain.MUDDY_GROUND,
            (TerrainSubtype.GRASSLAND, TerrainSubtype.ROCKY_DESERT): SubTerrain.SANDY_SOIL,
            (TerrainSubtype.ROLLING_HILLS, TerrainSubtype.STEEP_SLOPES): SubTerrain.ROCKY_GROUND
        }
        
        # Look up transition (order doesn't matter)
        current_terrain = getattr(base_subterrain, 'parent_terrain', None)
        for (terrain1, terrain2), transition_subterrain in transitions.items():
            if ((current_terrain == terrain1 and neighbor_terrain == terrain2) or
                (current_terrain == terrain2 and neighbor_terrain == terrain1)):
                return transition_subterrain
        
        return base_subterrain
    
    def _select_subterrain_from_distribution(self, distribution: Dict[SubTerrain, float], 
                                           noise_value: float) -> SubTerrain:
        """Select sub-terrain from weighted distribution"""
        cumulative = 0.0
        adjusted_noise = (noise_value + random.uniform(-0.05, 0.05)) % 1.0
        
        for subterrain, probability in distribution.items():
            cumulative += probability
            if adjusted_noise <= cumulative:
                return subterrain
        
        return list(distribution.keys())[0]
    
    def _generate_precise_elevation(self, local_map: List[List[LocalTile]], 
                                  regional_tile: 'RegionalTile'):
        """Add centimeter-level elevation detail"""
        
        base_elevation = regional_tile.micro_elevation
        
        for y in range(self.chunk_size):
            for x in range(self.chunk_size):
                tile = local_map[y][x]
                
                # Fine elevation noise (centimeter scale)
                elevation_noise = self.noise.octave_noise(
                    x * self.elevation_detail_scale,
                    y * self.elevation_detail_scale,
                    octaves=4,
                    persistence=0.3
                )
                
                # Elevation variation based on sub-terrain
                elevation_variation = self._get_elevation_variation_for_subterrain(tile.sub_terrain)
                precise_elevation = base_elevation + (elevation_noise * elevation_variation)
                
                # Smooth with neighbors for realistic terrain
                precise_elevation = self._smooth_precise_elevation(local_map, x, y, precise_elevation)
                
                tile.precise_elevation = precise_elevation
    
    def _get_elevation_variation_for_subterrain(self, sub_terrain: SubTerrain) -> float:
        """Get elevation variation range for sub-terrain type"""
        variations = {
            SubTerrain.DIRT_PATH: 0.1,      # Very flat
            SubTerrain.SHORT_GRASS: 0.2,
            SubTerrain.TALL_GRASS: 0.3,
            SubTerrain.SMALL_BOULDER: 1.5,  # Raised features
            SubTerrain.LARGE_BOULDER: 3.0,
            SubTerrain.ROCK_OUTCROP: 2.5,
            SubTerrain.FALLEN_LOG: 0.8,
            SubTerrain.MATURE_TREES: 0.5,   # Tree bases create small elevation changes
            SubTerrain.MUDDY_GROUND: 0.1,   # Flat and wet
            SubTerrain.SANDY_SOIL: 0.4,     # Can have small dunes
            SubTerrain.LOOSE_STONES: 0.6,
            SubTerrain.MOSS_COVERED: 0.2
        }
        return variations.get(sub_terrain, 0.5)
    
    def _smooth_precise_elevation(self, local_map: List[List[LocalTile]], 
                                x: int, y: int, elevation: float) -> float:
        """Smooth elevation with processed neighbors"""
        if x == 0 and y == 0:
            return elevation
        
        neighbor_elevations = []
        for dy in [-1, 0]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                if dx > 0 and dy == 0:  # Skip unprocessed tiles
                    continue
                
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.chunk_size and 0 <= ny < self.chunk_size:
                    neighbor_elevations.append(local_map[ny][nx].precise_elevation)
        
        if neighbor_elevations:
            avg_neighbor = sum(neighbor_elevations) / len(neighbor_elevations)
            return elevation * 0.6 + avg_neighbor * 0.4  # Blend for smoothness
        
        return elevation
    
    def _define_z_level_structure(self, local_map: List[List[LocalTile]], 
                                regional_tile: 'RegionalTile'):
        """Define which Z-levels exist and how to access them"""
        
        # Determine available Z-levels based on regional features
        available_levels = {ZLevel.SURFACE}  # Always have surface
        
        # Underground levels
        if regional_tile.landmark in [LandmarkType.CAVE_ENTRANCE, LandmarkType.CAVERN_COMPLEX]:
            available_levels.add(ZLevel.UNDERGROUND)
            if regional_tile.landmark == LandmarkType.CAVERN_COMPLEX:
                available_levels.add(ZLevel.DEEP_UNDERGROUND)
        
        # Elevated levels
        if regional_tile.terrain_subtype in [TerrainSubtype.CLIFFS, TerrainSubtype.STEEP_SLOPES]:
            available_levels.add(ZLevel.ELEVATED)
            if regional_tile.terrain_subtype == TerrainSubtype.CLIFFS:
                available_levels.add(ZLevel.HIGH)
        elif regional_tile.terrain_subtype in [TerrainSubtype.DENSE_FOREST, TerrainSubtype.OLD_GROWTH]:
            available_levels.add(ZLevel.ELEVATED)  # Tree canopy level
        
        # Assign Z-levels to tiles based on sub-terrain and elevation
        for y in range(self.chunk_size):
            for x in range(self.chunk_size):
                tile = local_map[y][x]
                
                # Default to surface
                tile.z_level = ZLevel.SURFACE
                
                # Elevated features
                if tile.sub_terrain in [SubTerrain.MATURE_TREES, SubTerrain.LARGE_BOULDER, SubTerrain.ROCK_OUTCROP]:
                    if ZLevel.ELEVATED in available_levels:
                        # Some elevated features can be climbed
                        tile.can_access_upper_level = True
                        
                        # Create elevated structure
                        if random.random() < 0.3:  # 30% of elevated features have accessible upper level
                            tile.z_level = ZLevel.ELEVATED
                
                # Underground access
                if (tile.sub_terrain in [SubTerrain.ROCK_OUTCROP, SubTerrain.LARGE_BOULDER] and
                    ZLevel.UNDERGROUND in available_levels):
                    if random.random() < 0.1:  # 10% chance for cave entrance
                        tile.can_access_lower_level = True
    
    def _place_structural_features(self, local_map: List[List[LocalTile]], 
                                 regional_tile: 'RegionalTile'):
        """Place structural features that affect movement and access"""
        
        # Determine appropriate structural features for this regional terrain
        appropriate_features = self._get_appropriate_structural_features(regional_tile)
        
        features_placed = 0
        max_features = 8
        
        # Place features with appropriate spacing
        for attempt in range(50):  # Try multiple placements
            if features_placed >= max_features:
                break
            
            x = random.randint(1, self.chunk_size - 2)
            y = random.randint(1, self.chunk_size - 2)
            
            tile = local_map[y][x]
            
            # Check if location is suitable and not too close to other features
            if (tile.structural_feature is None and
                self._is_suitable_for_structure(tile) and
                self._check_structure_spacing(local_map, x, y, min_distance=4)):
                
                # Choose appropriate feature
                suitable_features = self._filter_features_by_subterrain(appropriate_features, tile.sub_terrain)
                if suitable_features:
                    feature = random.choice(suitable_features)
                    tile.structural_feature = feature
                    
                    # Apply structural effects
                    self._apply_structural_effects(tile, feature)
                    features_placed += 1
    
    def _get_appropriate_structural_features(self, regional_tile: 'RegionalTile') -> List[StructuralFeature]:
        """Get structural features appropriate for regional terrain"""
        
        terrain_features = {
            TerrainSubtype.CLIFFS: [
                StructuralFeature.CAVE_MOUTH, StructuralFeature.MOUNTAIN_LEDGE,
                StructuralFeature.CLIFF_FACE, StructuralFeature.NATURAL_RAMP
            ],
            TerrainSubtype.STEEP_SLOPES: [
                StructuralFeature.CAVE_MOUTH, StructuralFeature.MOUNTAIN_LEDGE,
                StructuralFeature.NATURAL_RAMP, StructuralFeature.ROCK_PILE
            ],
            TerrainSubtype.DENSE_FOREST: [
                StructuralFeature.TREE_TRUNK, StructuralFeature.FALLEN_TREE_BRIDGE,
                StructuralFeature.ROCK_PILE
            ],
            TerrainSubtype.LIGHT_WOODLAND: [
                StructuralFeature.TREE_TRUNK, StructuralFeature.FALLEN_TREE_BRIDGE
            ],
            TerrainSubtype.ROLLING_HILLS: [
                StructuralFeature.ROCK_PILE, StructuralFeature.NATURAL_RAMP
            ],
            TerrainSubtype.MARSH: [
                StructuralFeature.FALLEN_TREE_BRIDGE, StructuralFeature.WATER_FORD
            ],
            TerrainSubtype.MOUNTAIN_VALLEY: [
                StructuralFeature.CAVE_MOUTH, StructuralFeature.ROCK_PILE,
                StructuralFeature.NATURAL_RAMP
            ]
        }
        
        # Add universal features based on regional landmarks
        universal_features = []
        if regional_tile.landmark == LandmarkType.CAVE_ENTRANCE:
            universal_features.extend([StructuralFeature.CAVE_MOUTH] * 3)  # More likely
        if regional_tile.landmark == LandmarkType.MOUNTAIN_PASS:
            universal_features.extend([StructuralFeature.NATURAL_RAMP] * 2)
        
        terrain_specific = terrain_features.get(regional_tile.terrain_subtype, [])
        return terrain_specific + universal_features
    
    def _filter_features_by_subterrain(self, features: List[StructuralFeature], 
                                     sub_terrain: SubTerrain) -> List[StructuralFeature]:
        """Filter features appropriate for specific sub-terrain"""
        
        subterrain_compatibility = {
            StructuralFeature.CAVE_MOUTH: [
                SubTerrain.ROCK_OUTCROP, SubTerrain.LARGE_BOULDER, SubTerrain.ROCKY_GROUND
            ],
            StructuralFeature.TREE_TRUNK: [
                SubTerrain.MATURE_TREES, SubTerrain.YOUNG_TREES
            ],
            StructuralFeature.FALLEN_TREE_BRIDGE: [
                SubTerrain.FALLEN_LOG, SubTerrain.LEAF_LITTER, SubTerrain.MOSS_COVERED
            ],
            StructuralFeature.ROCK_PILE: [
                SubTerrain.ROCKY_GROUND, SubTerrain.LOOSE_STONES, SubTerrain.SMALL_BOULDER
            ],
            StructuralFeature.WATER_FORD: [
                SubTerrain.SHALLOW_WATER, SubTerrain.WATER_EDGE
            ],
            StructuralFeature.NATURAL_RAMP: [
                SubTerrain.ROCKY_GROUND, SubTerrain.BARE_EARTH, SubTerrain.GRASS_PATCH
            ]
        }
        
        filtered = []
        for feature in features:
            compatible_subterrains = subterrain_compatibility.get(feature, [sub_terrain])
            if sub_terrain in compatible_subterrains:
                filtered.append(feature)
        
        return filtered
    
    def _is_suitable_for_structure(self, tile: LocalTile) -> bool:
        """Check if tile is suitable for structural features"""
        # Don't place structures on water or very soft terrain
        unsuitable = [
            SubTerrain.DEEP_WATER, SubTerrain.SHALLOW_WATER,
            SubTerrain.MUDDY_GROUND
        ]
        return tile.sub_terrain not in unsuitable
    
    def _check_structure_spacing(self, local_map: List[List[LocalTile]], 
                               x: int, y: int, min_distance: int = 4) -> bool:
        """Ensure structural features aren't too close together"""
        for dy in range(-min_distance, min_distance + 1):
            for dx in range(-min_distance, min_distance + 1):
                if dx == 0 and dy == 0:
                    continue
                
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.chunk_size and 0 <= ny < self.chunk_size:
                    if local_map[ny][nx].structural_feature is not None:
                        return False
        return True
    
    def _apply_structural_effects(self, tile: LocalTile, feature: StructuralFeature):
        """Apply effects of structural features"""
        
        feature_effects = {
            StructuralFeature.CAVE_MOUTH: {
                'can_access_lower_level': True,
                'blocks_movement': False,
                'blocks_line_of_sight': False,
                'movement_cost': 1.2,
                'concealment': 0.8
            },
            StructuralFeature.MOUNTAIN_LEDGE: {
                'can_access_upper_level': True,
                'blocks_movement': False,
                'blocks_line_of_sight': False,
                'movement_cost': 1.5,
                'concealment': 0.3
            },
            StructuralFeature.CLIFF_FACE: {
                'blocks_movement': True,
                'blocks_line_of_sight': True,
                'movement_cost': 10.0,  # Effectively impassable
                'concealment': 0.1
            },
            StructuralFeature.TREE_TRUNK: {
                'can_access_upper_level': True,
                'blocks_movement': True,
                'blocks_line_of_sight': True,
                'movement_cost': 10.0,
                'concealment': 0.9
            },
            StructuralFeature.FALLEN_TREE_BRIDGE: {
                'blocks_movement': False,
                'blocks_line_of_sight': False,
                'movement_cost': 1.3,
                'concealment': 0.5
            },
            StructuralFeature.WATER_FORD: {
                'blocks_movement': False,
                'blocks_line_of_sight': False,
                'movement_cost': 1.5,
                'concealment': 0.0
            },
            StructuralFeature.ROCK_PILE: {
                'can_access_upper_level': True,
                'blocks_movement': True,
                'blocks_line_of_sight': False,
                'movement_cost': 2.0,
                'concealment': 0.4
            }
        }
        
        effects = feature_effects.get(feature, {})
        
        tile.can_access_lower_level = effects.get('can_access_lower_level', False)
        tile.can_access_upper_level = effects.get('can_access_upper_level', False)
        tile.blocks_movement = effects.get('blocks_movement', False)
        tile.blocks_line_of_sight = effects.get('blocks_line_of_sight', False)
        tile.movement_cost = effects.get('movement_cost', 1.0)
        tile.concealment = effects.get('concealment', 0.0)
    
    def _place_harvestable_resources(self, local_map: List[List[LocalTile]], 
                                   regional_tile: 'RegionalTile',
                                   world_context: Dict):
        """Place specific harvestable resources throughout the chunk"""
        
        # Get appropriate resources for this terrain
        terrain_resources = self._get_terrain_appropriate_resources(regional_tile)
        
        # Generate resource clusters
        resource_clusters = self._generate_resource_clusters(regional_tile, terrain_resources)
        
        # Apply clusters to tiles
        for cluster in resource_clusters:
            self._apply_resource_cluster(local_map, cluster)
        
        # Add scattered individual resources
        self._add_scattered_resources(local_map, regional_tile, terrain_resources)
    
    def _get_terrain_appropriate_resources(self, regional_tile: 'RegionalTile') -> List[ResourceType]:
        """Get resources appropriate for this regional terrain"""
        
        terrain_resources = {
            TerrainSubtype.DENSE_FOREST: [
                ResourceType.LOGS, ResourceType.BRANCHES, ResourceType.BARK,
                ResourceType.MUSHROOMS, ResourceType.HERBS, ResourceType.NUTS,
                ResourceType.HONEY, ResourceType.GAME_TRAIL
            ],
            TerrainSubtype.LIGHT_WOODLAND: [
                ResourceType.BRANCHES, ResourceType.BERRIES, ResourceType.HERBS,
                ResourceType.NUTS, ResourceType.GAME_TRAIL
            ],
            TerrainSubtype.MEADOWS: [
                ResourceType.HERBS, ResourceType.WILDFLOWERS, ResourceType.BERRIES,
                ResourceType.HONEY, ResourceType.GAME_TRAIL
            ],
            TerrainSubtype.ROCKY_DESERT: [
                ResourceType.FLINT, ResourceType.STONES, ResourceType.GEMS,
                ResourceType.COPPER_ORE, ResourceType.SALT
            ],
            TerrainSubtype.STEEP_SLOPES: [
                ResourceType.STONES, ResourceType.IRON_ORE, ResourceType.COPPER_ORE,
                ResourceType.FLINT
            ],
            TerrainSubtype.MARSH: [
                ResourceType.REEDS, ResourceType.CLAY, ResourceType.HERBS,
                ResourceType.FISH, ResourceType.FRESH_WATER
            ],
            TerrainSubtype.MOUNTAIN_VALLEY: [
                ResourceType.FRESH_WATER, ResourceType.HERBS, ResourceType.BERRIES,
                ResourceType.STONES, ResourceType.GAME_TRAIL
            ],
            TerrainSubtype.PLAINS: [
                ResourceType.HERBS, ResourceType.CLAY, ResourceType.STONES,
                ResourceType.GAME_TRAIL
            ]
        }
        
        base_resources = terrain_resources.get(regional_tile.terrain_subtype, [ResourceType.STONES])
        
        # Add resources from regional resource concentration
        if regional_tile.resource_concentration:
            concentration_resources = self._get_concentration_specific_resources(
                regional_tile.resource_concentration
            )
            base_resources.extend(concentration_resources)
        
        return base_resources
    
    def _get_concentration_specific_resources(self, concentration: 'ResourceConcentration') -> List[ResourceType]:
        """Get specific resources for regional resource concentrations"""
        
        concentration_resources = {
            ResourceConcentration.WOOD_GROVE: [ResourceType.LOGS, ResourceType.BRANCHES, ResourceType.BARK],
            ResourceConcentration.STONE_QUARRY: [ResourceType.STONES, ResourceType.FLINT],
            ResourceConcentration.METAL_DEPOSIT: [ResourceType.IRON_ORE, ResourceType.COPPER_ORE],
            ResourceConcentration.FERTILE_SOIL: [ResourceType.HERBS, ResourceType.BERRIES],
            ResourceConcentration.HUNTING_GROUNDS: [ResourceType.GAME_TRAIL],
            ResourceConcentration.FISHING_SPOT: [ResourceType.FISH],
            ResourceConcentration.HERB_PATCH: [ResourceType.HERBS, ResourceType.BERRIES],
            ResourceConcentration.CLAY_DEPOSITS: [ResourceType.CLAY]
        }
        
        return concentration_resources.get(concentration, [])
    
    def _generate_resource_clusters(self, regional_tile: 'RegionalTile', 
                                  available_resources: List[ResourceType]) -> List[ResourceCluster]:
        """Generate clusters of resources within the chunk"""
        clusters = []
        
        # Determine number of clusters based on regional resource concentration
        base_clusters = 2
        if regional_tile.resource_concentration:
            base_clusters += 2  # More clusters if regional concentration exists
        
        num_clusters = min(self.max_resource_clusters, base_clusters + random.randint(0, 2))
        
        for cluster_id in range(num_clusters):
            # Choose resource type
            resource_type = random.choice(available_resources)
            
            # Place cluster center
            center_x = random.uniform(3, self.chunk_size - 3)
            center_y = random.uniform(3, self.chunk_size - 3)
            
            # Cluster properties
            radius = random.uniform(2.0, 6.0)
            density = random.uniform(0.3, 0.8)
            quality = random.uniform(0.4, 1.0)
            
            cluster = ResourceCluster(
                resource_type=resource_type,
                center_x=center_x,
                center_y=center_y,
                radius=radius,
                density=density,
                quality=quality
            )
            clusters.append(cluster)
        
        return clusters
    
    def _apply_resource_cluster(self, local_map: List[List[LocalTile]], cluster: ResourceCluster):
        """Apply resource cluster to local tiles"""
        
        cluster_radius_squared = cluster.radius * cluster.radius
        
        for y in range(self.chunk_size):
            for x in range(self.chunk_size):
                dx = x - cluster.center_x
                dy = y - cluster.center_y
                distance_squared = dx*dx + dy*dy
                
                if distance_squared <= cluster_radius_squared:
                    distance = math.sqrt(distance_squared)
                    
                    # Probability decreases with distance from center
                    spawn_probability = cluster.density * max(0, 1.0 - (distance / cluster.radius))
                    
                    if random.random() < spawn_probability:
                        tile = local_map[y][x]
                        
                        # Check if sub-terrain is compatible with resource
                        if self._is_subterrain_compatible_with_resource(tile.sub_terrain, cluster.resource_type):
                            if tile.harvestable_resource is None:  # Don't override existing
                                tile.harvestable_resource = cluster.resource_type
                                
                                # Quantity based on cluster quality and distance
                                distance_factor = max(0.3, 1.0 - (distance / cluster.radius))
                                base_quantity = int(cluster.quality * distance_factor * 5) + 1
                                tile.resource_quantity = max(1, min(5, base_quantity))
                                
                                # Respawn time based on resource type
                                tile.resource_respawn_time = self._get_resource_respawn_time(cluster.resource_type)
    
    def _is_subterrain_compatible_with_resource(self, sub_terrain: SubTerrain, 
                                              resource: ResourceType) -> bool:
        """Check if sub-terrain can support this resource type"""
        
        compatibility = {
            ResourceType.BERRIES: [SubTerrain.BERRY_BUSHES, SubTerrain.THORNY_BUSHES, SubTerrain.WILDFLOWERS],
            ResourceType.NUTS: [SubTerrain.MATURE_TREES, SubTerrain.YOUNG_TREES],
            ResourceType.HERBS: [SubTerrain.WILDFLOWERS, SubTerrain.GRASS_PATCH, SubTerrain.MOSS_COVERED],
            ResourceType.MUSHROOMS: [SubTerrain.FALLEN_LOG, SubTerrain.LEAF_LITTER, SubTerrain.MOSS_COVERED],
            ResourceType.HONEY: [SubTerrain.WILDFLOWERS, SubTerrain.MATURE_TREES],
            ResourceType.LOGS: [SubTerrain.MATURE_TREES, SubTerrain.FALLEN_LOG],
            ResourceType.BRANCHES: [SubTerrain.YOUNG_TREES, SubTerrain.MATURE_TREES, SubTerrain.FALLEN_LOG],
            ResourceType.BARK: [SubTerrain.MATURE_TREES, SubTerrain.YOUNG_TREES],
            ResourceType.STONES: [SubTerrain.ROCKY_GROUND, SubTerrain.LOOSE_STONES, SubTerrain.PEBBLES],
            ResourceType.FLINT: [SubTerrain.ROCKY_GROUND, SubTerrain.LOOSE_STONES],
            ResourceType.CLAY: [SubTerrain.MUDDY_GROUND, SubTerrain.WATER_EDGE],
            ResourceType.REEDS: [SubTerrain.REED_BEDS, SubTerrain.WATER_EDGE],
            ResourceType.IRON_ORE: [SubTerrain.ROCK_OUTCROP, SubTerrain.ROCKY_GROUND],
            ResourceType.COPPER_ORE: [SubTerrain.ROCK_OUTCROP, SubTerrain.LARGE_BOULDER],
            ResourceType.GEMS: [SubTerrain.ROCK_OUTCROP, SubTerrain.ROCKY_GROUND],
            ResourceType.COAL: [SubTerrain.ROCK_OUTCROP, SubTerrain.ROCKY_GROUND],
            ResourceType.FISH: [SubTerrain.DEEP_WATER, SubTerrain.CALM_POOLS],
            ResourceType.FRESH_WATER: [SubTerrain.SHALLOW_WATER, SubTerrain.DEEP_WATER],
            ResourceType.GAME_TRAIL: [SubTerrain.DIRT_PATH, SubTerrain.GRASS_PATCH, SubTerrain.SHORT_GRASS]
        }
        
        compatible_subterrains = compatibility.get(resource, [])
        return sub_terrain in compatible_subterrains
    
    def _get_resource_respawn_time(self, resource: ResourceType) -> float:
        """Get respawn time in days for resource type"""
        
        respawn_times = {
            # Fast renewable (biological)
            ResourceType.BERRIES: 30.0,     # Monthly in season
            ResourceType.HERBS: 15.0,       # Biweekly
            ResourceType.MUSHROOMS: 7.0,    # Weekly after rain
            ResourceType.FISH: 3.0,         # Fish repopulate quickly
            ResourceType.HONEY: 60.0,       # Seasonal
            
            # Medium renewable (regrowth)
            ResourceType.BRANCHES: 90.0,    # Quarterly
            ResourceType.BARK: 365.0,       # Annual
            ResourceType.REEDS: 45.0,       # Monthly-ish
            
            # Slow renewable (geological)
            ResourceType.CLAY: 0.0,         # Finite until rain refills
            ResourceType.STONES: 0.0,       # Finite
            ResourceType.FLINT: 0.0,        # Finite
            
            # Non-renewable (mining)
            ResourceType.IRON_ORE: 0.0,     # Finite
            ResourceType.COPPER_ORE: 0.0,   # Finite
            ResourceType.GEMS: 0.0,         # Finite
            ResourceType.COAL: 0.0,         # Finite
            
            # Always renewable
            ResourceType.FRESH_WATER: 1.0,  # Daily
            ResourceType.GAME_TRAIL: 7.0    # Animals return weekly
        }
        
        return respawn_times.get(resource, 0.0)
    
    def _add_scattered_resources(self, local_map: List[List[LocalTile]], 
                               regional_tile: 'RegionalTile',
                               available_resources: List[ResourceType]):
        """Add scattered individual resources outside of clusters"""
        
        scatter_density = 0.05  # 5% of tiles get scattered resources
        
        for y in range(self.chunk_size):
            for x in range(self.chunk_size):
                tile = local_map[y][x]
                
                if (tile.harvestable_resource is None and  # No existing resource
                    random.random() < scatter_density):
                    
                    # Choose appropriate resource for this sub-terrain
                    compatible_resources = [r for r in available_resources 
                                          if self._is_subterrain_compatible_with_resource(tile.sub_terrain, r)]
                    
                    if compatible_resources:
                        resource = random.choice(compatible_resources)
                        tile.harvestable_resource = resource
                        tile.resource_quantity = random.randint(1, 3)  # Lower quantities for scattered
                        tile.resource_respawn_time = self._get_resource_respawn_time(resource)
    
    def _define_animal_spawn_areas(self, local_map: List[List[LocalTile]], 
                                 regional_tile: 'RegionalTile'):
        """Define areas where different animals spawn"""
        
        # Determine appropriate animal types for this terrain
        terrain_animals = self._get_terrain_appropriate_animals(regional_tile)
        
        # Create spawn areas
        spawn_areas = []
        for animal_type in terrain_animals:
            if random.random() < 0.6:  # 60% chance for each animal type
                # Place spawn area
                center_x = random.uniform(5, self.chunk_size - 5)
                center_y = random.uniform(5, self.chunk_size - 5)
                radius = random.uniform(3.0, 8.0)
                capacity = self._get_animal_capacity(animal_type)
                preferred_terrain = self._get_animal_preferred_subterrain(animal_type)
                
                spawn_area = AnimalSpawnArea(
                    spawn_type=animal_type,
                    center_x=center_x,
                    center_y=center_y,
                    radius=radius,
                    population_capacity=capacity,
                    preferred_terrain=preferred_terrain
                )
                spawn_areas.append(spawn_area)
        
        # Apply spawn areas to tiles
        for spawn_area in spawn_areas:
            self._apply_spawn_area(local_map, spawn_area)
    
    def _get_terrain_appropriate_animals(self, regional_tile: 'RegionalTile') -> List[AnimalSpawnType]:
        """Get animal types appropriate for this regional terrain"""
        
        terrain_animals = {
            TerrainSubtype.DENSE_FOREST: [
                AnimalSpawnType.SMALL_GAME, AnimalSpawnType.LARGE_GAME, 
                AnimalSpawnType.PREDATORS, AnimalSpawnType.INSECTS
            ],
            TerrainSubtype.LIGHT_WOODLAND: [
                AnimalSpawnType.SMALL_GAME, AnimalSpawnType.LARGE_GAME, AnimalSpawnType.INSECTS
            ],
            TerrainSubtype.MEADOWS: [
                AnimalSpawnType.SMALL_GAME, AnimalSpawnType.LARGE_GAME, 
                AnimalSpawnType.LIVESTOCK, AnimalSpawnType.INSECTS
            ],
            TerrainSubtype.PLAINS: [
                AnimalSpawnType.LARGE_GAME, AnimalSpawnType.LIVESTOCK, AnimalSpawnType.SMALL_GAME
            ],
            TerrainSubtype.ROLLING_HILLS: [
                AnimalSpawnType.LIVESTOCK, AnimalSpawnType.SMALL_GAME, AnimalSpawnType.LARGE_GAME
            ],
            TerrainSubtype.ROCKY_DESERT: [
                AnimalSpawnType.SMALL_GAME, AnimalSpawnType.PREDATORS
            ],
            TerrainSubtype.MARSH: [
                AnimalSpawnType.FISH, AnimalSpawnType.SMALL_GAME, AnimalSpawnType.INSECTS
            ],
            TerrainSubtype.MOUNTAIN_VALLEY: [
                AnimalSpawnType.LARGE_GAME, AnimalSpawnType.SMALL_GAME, AnimalSpawnType.PREDATORS
            ]
        }
        
        return terrain_animals.get(regional_tile.terrain_subtype, [AnimalSpawnType.SMALL_GAME])
    
    def _get_animal_capacity(self, animal_type: AnimalSpawnType) -> int:
        """Get population capacity for animal type"""
        capacities = {
            AnimalSpawnType.SMALL_GAME: random.randint(8, 15),
            AnimalSpawnType.LARGE_GAME: random.randint(3, 8),
            AnimalSpawnType.PREDATORS: random.randint(1, 3),
            AnimalSpawnType.LIVESTOCK: random.randint(5, 12),
            AnimalSpawnType.FISH: random.randint(10, 25),
            AnimalSpawnType.INSECTS: random.randint(20, 50)
        }
        return capacities.get(animal_type, 5)
    
    def _get_animal_preferred_subterrain(self, animal_type: AnimalSpawnType) -> List[SubTerrain]:
        """Get preferred sub-terrain for animal spawning"""
        
        preferences = {
            AnimalSpawnType.SMALL_GAME: [
                SubTerrain.TALL_GRASS, SubTerrain.BERRY_BUSHES, 
                SubTerrain.THORNY_BUSHES, SubTerrain.YOUNG_TREES
            ],
            AnimalSpawnType.LARGE_GAME: [
                SubTerrain.GRASS_PATCH, SubTerrain.WILDFLOWERS,
                SubTerrain.LIGHT_WOODLAND, SubTerrain.MEADOWS
            ],
            AnimalSpawnType.PREDATORS: [
                SubTerrain.ROCKY_GROUND, SubTerrain.DENSE_FOREST,
                SubTerrain.ROCK_OUTCROP, SubTerrain.CAVE_MOUTH
            ],
            AnimalSpawnType.LIVESTOCK: [
                SubTerrain.SHORT_GRASS, SubTerrain.GRASS_PATCH, SubTerrain.MEADOWS
            ],
            AnimalSpawnType.FISH: [
                SubTerrain.DEEP_WATER, SubTerrain.CALM_POOLS, SubTerrain.REED_BEDS
            ],
            AnimalSpawnType.INSECTS: [
                SubTerrain.WILDFLOWERS, SubTerrain.MATURE_TREES, SubTerrain.MOSS_COVERED
            ]
        }
        
        return preferences.get(animal_type, [SubTerrain.GRASS_PATCH])
    
    def _apply_spawn_area(self, local_map: List[List[LocalTile]], spawn_area: AnimalSpawnArea):
        """Apply animal spawn area to local tiles"""
        
        area_radius_squared = spawn_area.radius * spawn_area.radius
        tiles_in_area = 0
        
        # Count suitable tiles in spawn area
        for y in range(self.chunk_size):
            for x in range(self.chunk_size):
                dx = x - spawn_area.center_x
                dy = y - spawn_area.center_y
                distance_squared = dx*dx + dy*dy
                
                if distance_squared <= area_radius_squared:
                    tile = local_map[y][x]
                    if tile.sub_terrain in spawn_area.preferred_terrain:
                        tiles_in_area += 1
        
        if tiles_in_area == 0:
            return  # No suitable tiles
        
        # Distribute spawn capacity across suitable tiles
        spawn_per_tile = max(1, spawn_area.population_capacity // tiles_in_area)
        base_frequency = min(0.1, spawn_area.population_capacity / (tiles_in_area * 10))
        
        # Apply to tiles
        for y in range(self.chunk_size):
            for x in range(self.chunk_size):
                dx = x - spawn_area.center_x
                dy = y - spawn_area.center_y
                distance_squared = dx*dx + dy*dy
                
                if distance_squared <= area_radius_squared:
                    tile = local_map[y][x]
                    if tile.sub_terrain in spawn_area.preferred_terrain:
                        distance = math.sqrt(distance_squared)
                        distance_factor = max(0.3, 1.0 - (distance / spawn_area.radius))
                        
                        tile.animal_spawn_point = spawn_area.spawn_type
                        tile.max_animals = max(1, int(spawn_per_tile * distance_factor))
                        tile.spawn_frequency = base_frequency * distance_factor
    
    def _calculate_movement_properties(self, local_map: List[List[LocalTile]], 
                                     regional_tile: 'RegionalTile'):
        """Calculate movement costs, concealment, and other gameplay properties"""
        
        for y in range(self.chunk_size):
            for x in range(self.chunk_size):
                tile = local_map[y][x]
                
                # Base movement cost from sub-terrain
                base_movement_cost = self._get_base_movement_cost(tile.sub_terrain)
                
                # Elevation affects movement
                elevation_penalty = 0.0
                if y > 0:  # Check elevation change from south
                    elevation_diff = abs(tile.precise_elevation - local_map[y-1][x].precise_elevation)
                    elevation_penalty += min(1.0, elevation_diff / 2.0)  # 1 unit penalty per 2m elevation change
                
                if x > 0:  # Check elevation change from west
                    elevation_diff = abs(tile.precise_elevation - local_map[y][x-1].precise_elevation)
                    elevation_penalty += min(1.0, elevation_diff / 2.0)
                
                elevation_penalty /= 2  # Average the penalties
                
                # Resource effects on movement
                resource_penalty = 0.0
                if tile.harvestable_resource in [ResourceType.LOGS, ResourceType.STONES]:
                    resource_penalty = 0.3  # Heavy items slow movement
                
                # Final movement cost
                tile.movement_cost = base_movement_cost + elevation_penalty + resource_penalty
                tile.movement_cost = max(0.5, min(5.0, tile.movement_cost))
                
                # Concealment from sub-terrain
                tile.concealment = self._get_base_concealment(tile.sub_terrain)
                
                # Structural features already set concealment, don't override
                if tile.structural_feature is None:
                    # Apply resource concealment bonus
                    if tile.harvestable_resource in [ResourceType.BERRIES, ResourceType.HERBS]:
                        tile.concealment += 0.1
                
                tile.concealment = max(0.0, min(1.0, tile.concealment))
    
    def _get_base_movement_cost(self, sub_terrain: SubTerrain) -> float:
        """Get base movement cost for sub-terrain"""
        
        movement_costs = {
            SubTerrain.DIRT_PATH: 0.5,      # Easy travel
            SubTerrain.SHORT_GRASS: 0.8,
            SubTerrain.GRASS_PATCH: 0.9,
            SubTerrain.BARE_EARTH: 1.0,
            SubTerrain.TALL_GRASS: 1.2,
            SubTerrain.WILDFLOWERS: 1.1,
            SubTerrain.BERRY_BUSHES: 1.5,   # Must push through
            SubTerrain.THORNY_BUSHES: 2.0,  # Difficult
            SubTerrain.YOUNG_TREES: 1.8,
            SubTerrain.MATURE_TREES: 3.0,   # Cannot pass through trunk
            SubTerrain.FALLEN_LOG: 2.0,     # Must climb over
            SubTerrain.ROCKY_GROUND: 1.2,
            SubTerrain.LOOSE_STONES: 1.4,
            SubTerrain.SMALL_BOULDER: 2.5,
            SubTerrain.LARGE_BOULDER: 5.0,  # Must go around
            SubTerrain.ROCK_OUTCROP: 5.0,
            SubTerrain.MUDDY_GROUND: 1.8,   # Slow in mud
            SubTerrain.SANDY_SOIL: 1.1,
            SubTerrain.MOSS_COVERED: 1.0,
            SubTerrain.LEAF_LITTER: 1.1,
            SubTerrain.PEBBLES: 1.0,
            SubTerrain.SHALLOW_WATER: 1.5,
            SubTerrain.DEEP_WATER: 10.0,    # Must swim or go around
            SubTerrain.WATER_EDGE: 1.3,
            SubTerrain.MUDDY_BANK: 1.6,
            SubTerrain.REED_BEDS: 1.7
        }
        
        return movement_costs.get(sub_terrain, 1.0)
    
    def _get_base_concealment(self, sub_terrain: SubTerrain) -> float:
        """Get base concealment value for sub-terrain"""
        
        concealment_values = {
            SubTerrain.DIRT_PATH: 0.0,      # Very visible
            SubTerrain.SHORT_GRASS: 0.1,
            SubTerrain.GRASS_PATCH: 0.2,
            SubTerrain.TALL_GRASS: 0.5,     # Good hiding
            SubTerrain.WILDFLOWERS: 0.3,
            SubTerrain.BERRY_BUSHES: 0.6,
            SubTerrain.THORNY_BUSHES: 0.7,
            SubTerrain.YOUNG_TREES: 0.4,
            SubTerrain.MATURE_TREES: 0.8,   # Excellent hiding
            SubTerrain.FALLEN_LOG: 0.5,
            SubTerrain.ROCKY_GROUND: 0.2,
            SubTerrain.LOOSE_STONES: 0.1,
            SubTerrain.SMALL_BOULDER: 0.4,
            SubTerrain.LARGE_BOULDER: 0.6,
            SubTerrain.ROCK_OUTCROP: 0.5,
            SubTerrain.BARE_EARTH: 0.0,
            SubTerrain.MUDDY_GROUND: 0.1,
            SubTerrain.SANDY_SOIL: 0.0,
            SubTerrain.MOSS_COVERED: 0.3,
            SubTerrain.LEAF_LITTER: 0.2,
            SubTerrain.PEBBLES: 0.0,
            SubTerrain.SHALLOW_WATER: 0.0,  # Visible in water
            SubTerrain.DEEP_WATER: 0.0,
            SubTerrain.WATER_EDGE: 0.1,
            SubTerrain.MUDDY_BANK: 0.2,
            SubTerrain.REED_BEDS: 0.8       # Excellent hiding in reeds
        }
        
        return concealment_values.get(sub_terrain, 0.2)
    
    def _generate_local_display(self, local_map: List[List[LocalTile]], 
                              regional_tile: 'RegionalTile'):
        """Generate display characters and colors for local tiles"""
        
        # Display configurations for sub-terrain
        subterrain_display = {
            # Ground surfaces
            SubTerrain.DIRT_PATH: (".", (139, 69, 19), (101, 67, 33)),
            SubTerrain.GRASS_PATCH: (".", (50, 150, 50), (20, 100, 20)),
            SubTerrain.BARE_EARTH: (".", (160, 82, 45), (120, 60, 30)),
            SubTerrain.ROCKY_GROUND: ("∘", (128, 128, 128), (80, 80, 80)),
            SubTerrain.SANDY_SOIL: ("·", (238, 203, 173), (218, 165, 32)),
            SubTerrain.MUDDY_GROUND: ("∼", (101, 67, 33), (80, 50, 25)),
            SubTerrain.MOSS_COVERED: ("·", (0, 128, 0), (0, 80, 0)),
            SubTerrain.LEAF_LITTER: (",", (139, 90, 43), (101, 67, 33)),
            
            # Vegetation
            SubTerrain.TALL_GRASS: ("|", (34, 139, 34), (20, 100, 20)),
            SubTerrain.SHORT_GRASS: ("'", (50, 150, 50), (25, 125, 25)),
            SubTerrain.WILDFLOWERS: ("*", (255, 192, 203), (50, 150, 50)),
            SubTerrain.THORNY_BUSHES: ("≡", (128, 128, 0), (80, 80, 0)),
            SubTerrain.BERRY_BUSHES: ("♣", (0, 100, 0), (0, 60, 0)),
            SubTerrain.YOUNG_TREES: ("♪", (0, 120, 0), (0, 70, 0)),
            SubTerrain.MATURE_TREES: ("♠", (0, 80, 0), (0, 40, 0)),
            SubTerrain.FALLEN_LOG: ("―", (139, 69, 19), (101, 67, 33)),
            
            # Rock formations
            SubTerrain.SMALL_BOULDER: ("○", (169, 169, 169), (128, 128, 128)),
            SubTerrain.LARGE_BOULDER: ("●", (128, 128, 128), (80, 80, 80)),
            SubTerrain.ROCK_OUTCROP: ("▲", (169, 169, 169), (100, 100, 100)),
            SubTerrain.LOOSE_STONES: ("∘", (160, 160, 160), (120, 120, 120)),
            SubTerrain.PEBBLES: ("·", (192, 192, 192), (160, 160, 160)),
            
            # Water
            SubTerrain.SHALLOW_WATER: ("∼", (173, 216, 230), (100, 150, 200)),
            SubTerrain.DEEP_WATER: ("≈", (70, 130, 180), (30, 80, 150)),
            SubTerrain.WATER_EDGE: ("∽", (150, 200, 255), (75, 125, 200)),
            SubTerrain.MUDDY_BANK: ("≋", (139, 90, 43), (80, 50, 25)),
            SubTerrain.REED_BEDS: ("|", (107, 142, 35), (60, 100, 20))
        }
        
        # Structural feature display (overrides sub-terrain)
        structure_display = {
            StructuralFeature.CAVE_MOUTH: ("○", (200, 200, 200), (0, 0, 0)),
            StructuralFeature.MOUNTAIN_LEDGE: ("═", (180, 160, 140), (120, 100, 80)),
            StructuralFeature.CLIFF_FACE: ("█", (128, 128, 128), (80, 80, 80)),
            StructuralFeature.NATURAL_RAMP: ("╱", (160, 140, 120), (100, 80, 60)),
            StructuralFeature.TREE_TRUNK: ("♠", (101, 67, 33), (80, 50, 25)),
            StructuralFeature.ROCK_PILE: ("▲", (169, 169, 169), (128, 128, 128)),
            StructuralFeature.WATER_FORD: ("≈", (200, 230, 255), (100, 150, 200)),
            StructuralFeature.FALLEN_TREE_BRIDGE: ("═", (139, 69, 19), (101, 67, 33)),
            StructuralFeature.NATURAL_BRIDGE: ("═", (169, 169, 169), (128, 128, 128)),
            StructuralFeature.SCENIC_OVERLOOK: ("▲", (200, 180, 160), (150, 130, 110))
        }
        
        # Resource display modifications (subtle color changes)
        resource_display_mods = {
            ResourceType.BERRIES: ("•", (128, 0, 128)),      # Purple berries
            ResourceType.NUTS: ("○", (139, 69, 19)),         # Brown nuts
            ResourceType.HERBS: ("♪", (50, 205, 50)),        # Bright green herbs
            ResourceType.MUSHROOMS: ("♀", (160, 82, 45)),    # Brown mushrooms
            ResourceType.HONEY: ("◉", (255, 215, 0)),        # Golden honey
            ResourceType.LOGS: ("▬", (139, 69, 19)),         # Brown logs
            ResourceType.BRANCHES: ("┼", (101, 67, 33)),     # Branch pattern
            ResourceType.BARK: ("▒", (139, 69, 19)),         # Textured bark
            ResourceType.STONES: ("◦", (169, 169, 169)),     # Gray stones
            ResourceType.FLINT: ("◊", (64, 64, 64)),         # Dark gray flint
            ResourceType.CLAY: ("≡", (205, 133, 63)),        # Clay brown
            ResourceType.REEDS: ("┃", (107, 142, 35)),       # Tall reeds
            ResourceType.IRON_ORE: ("▪", (128, 128, 128)),   # Metallic gray
            ResourceType.COPPER_ORE: ("▪", (184, 115, 51)),  # Copper color
            ResourceType.GEMS: ("◊", (255, 20, 147)),        # Bright gem
            ResourceType.COAL: ("■", (36, 36, 36)),          # Black coal
            ResourceType.FISH: ("◦", (70, 130, 180)),        # Blue fish
            ResourceType.FRESH_WATER: ("○", (173, 216, 230)), # Clear water
            ResourceType.GAME_TRAIL: ("∴", (139, 90, 43))    # Trail markers
        }
        
        # Animal spawn indicators (very subtle)
        animal_spawn_mods = {
            AnimalSpawnType.SMALL_GAME: (5, 5, 0),     # Slight yellow tint
            AnimalSpawnType.LARGE_GAME: (0, 5, 0),     # Slight green tint
            AnimalSpawnType.PREDATORS: (5, 0, 0),      # Slight red tint
            AnimalSpawnType.LIVESTOCK: (0, 0, 5),      # Slight blue tint
            AnimalSpawnType.FISH: (0, 3, 8),          # Blue tint
            AnimalSpawnType.INSECTS: (3, 3, 0)        # Yellow tint
        }
        
        # Apply display data to all tiles
        for y in range(self.chunk_size):
            for x in range(self.chunk_size):
                tile = local_map[y][x]
                
                # Start with sub-terrain display
                char, fg, bg = subterrain_display.get(
                    tile.sub_terrain, 
                    ("?", (255, 255, 255), (0, 0, 0))
                )
                
                # Override with structural feature if present
                if tile.structural_feature:
                    structure_char, structure_fg, structure_bg = structure_display.get(
                        tile.structural_feature, 
                        (char, fg, bg)
                    )
                    char, fg, bg = structure_char, structure_fg, structure_bg
                
                # Modify for harvestable resources
                if tile.harvestable_resource:
                    resource_char, resource_fg = resource_display_mods.get(
                        tile.harvestable_resource, 
                        (char, fg)
                    )
                    char = resource_char
                    fg = resource_fg
                
                # Apply animal spawn color modifications (very subtle)
                if tile.animal_spawn_point:
                    r_mod, g_mod, b_mod = animal_spawn_mods.get(tile.animal_spawn_point, (0, 0, 0))
                    fg = tuple(min(255, c + mod) for c, mod in zip(fg, (r_mod, g_mod, b_mod)))
                
                # Add environmental variation
                variation = random.randint(-8, 8)
                fg = tuple(max(0, min(255, c + variation)) for c in fg)
                bg = tuple(max(0, min(255, c + variation//2)) for c in bg)
                
                # Z-level indicators (subtle background modifications)
                if tile.z_level == ZLevel.ELEVATED:
                    bg = tuple(min(255, c + 10) for c in bg)  # Slightly brighter
                elif tile.z_level == ZLevel.HIGH:
                    bg = tuple(min(255, c + 20) for c in bg)  # More brightness
                elif tile.z_level == ZLevel.UNDERGROUND:
                    bg = tuple(max(0, c - 15) for c in bg)    # Slightly darker
                elif tile.z_level == ZLevel.DEEP_UNDERGROUND:
                    bg = tuple(max(0, c - 30) for c in bg)    # Much darker
                
                # Access indicators (very subtle)
                if tile.can_access_upper_level:
                    fg = tuple(min(255, c + 5) for c in fg)   # Slightly brighter
                if tile.can_access_lower_level:
                    bg = tuple(max(0, c - 5) for c in bg)     # Slightly darker background
                
                tile.char = char
                tile.fg_color = fg
                tile.bg_color = bg
    
    def get_local_stats(self, local_map: List[List[LocalTile]]) -> Dict:
        """Get statistics about the generated local map"""
        total_tiles = self.chunk_size * self.chunk_size
        
        # Count different features
        subterrain_counts = {}
        resource_counts = {}
        animal_spawn_counts = {}
        structure_counts = {}
        z_level_counts = {}
        
        movement_costs = []
        concealment_values = []
        elevation_values = []
        
        access_upper = 0
        access_lower = 0
        blocks_movement = 0
        
        for row in local_map:
            for tile in row:
                # Sub-terrain distribution
                subterrain = tile.sub_terrain
                subterrain_counts[subterrain] = subterrain_counts.get(subterrain, 0) + 1
                
                # Resource distribution
                if tile.harvestable_resource:
                    resource = tile.harvestable_resource
                    resource_counts[resource] = resource_counts.get(resource, 0) + 1
                
                # Animal spawns
                if tile.animal_spawn_point:
                    animal = tile.animal_spawn_point
                    animal_spawn_counts[animal] = animal_spawn_counts.get(animal, 0) + 1
                
                # Structures
                if tile.structural_feature:
                    structure = tile.structural_feature
                    structure_counts[structure] = structure_counts.get(structure, 0) + 1
                
                # Z-levels
                z_level = tile.z_level
                z_level_counts[z_level] = z_level_counts.get(z_level, 0) + 1
                
                # Movement and gameplay stats
                movement_costs.append(tile.movement_cost)
                concealment_values.append(tile.concealment)
                elevation_values.append(tile.precise_elevation)
                
                if tile.can_access_upper_level:
                    access_upper += 1
                if tile.can_access_lower_level:
                    access_lower += 1
                if tile.blocks_movement:
                    blocks_movement += 1
        
        return {
            'total_tiles': total_tiles,
            'subterrain_distribution': subterrain_counts,
            'resource_distribution': resource_counts,
            'animal_spawn_distribution': animal_spawn_counts,
            'structure_distribution': structure_counts,
            'z_level_distribution': z_level_counts,
            'avg_movement_cost': sum(movement_costs) / len(movement_costs),
            'avg_concealment': sum(concealment_values) / len(concealment_values),
            'elevation_range': (min(elevation_values), max(elevation_values)),
            'upper_level_access_points': access_upper,
            'lower_level_access_points': access_lower,
            'blocked_tiles': blocks_movement,
            'passable_tiles': total_tiles - blocks_movement
        }
    
    def print_local_stats(self, local_map: List[List[LocalTile]], regional_tile: 'RegionalTile'):
        """Print statistics about the generated local map"""
        stats = self.get_local_stats(local_map)
        
        print(f"\nLocal Chunk Statistics for {regional_tile.terrain_subtype.value}:")
        print(f"Total tiles: {stats['total_tiles']} (32×32 meters)")
        print(f"Passable tiles: {stats['passable_tiles']} ({stats['passable_tiles']/stats['total_tiles']*100:.1f}%)")
        print(f"Blocked tiles: {stats['blocked_tiles']} ({stats['blocked_tiles']/stats['total_tiles']*100:.1f}%)")
        print(f"Upper level access points: {stats['upper_level_access_points']}")
        print(f"Lower level access points: {stats['lower_level_access_points']}")
        
        print(f"\nGameplay Properties:")
        print(f"Average movement cost: {stats['avg_movement_cost']:.2f}")
        print(f"Average concealment: {stats['avg_concealment']:.2f}")
        print(f"Elevation range: {stats['elevation_range'][0]:.1f}m to {stats['elevation_range'][1]:.1f}m")
        
        print(f"\nSub-terrain Distribution:")
        for subterrain, count in sorted(stats['subterrain_distribution'].items(), 
                                      key=lambda x: x[1], reverse=True)[:10]:  # Top 10
            percentage = count / stats['total_tiles'] * 100
            print(f"  {subterrain.value}: {count} ({percentage:.1f}%)")
        
        if stats['resource_distribution']:
            print(f"\nHarvestable Resources:")
            for resource, count in sorted(stats['resource_distribution'].items(), 
                                        key=lambda x: x[1], reverse=True):
                print(f"  {resource.value}: {count} tiles")
        
        if stats['animal_spawn_distribution']:
            print(f"\nAnimal Spawn Areas:")
            for animal, count in sorted(stats['animal_spawn_distribution'].items(), 
                                      key=lambda x: x[1], reverse=True):
                print(f"  {animal.value}: {count} spawn tiles")
        
        if stats['structure_distribution']:
            print(f"\nStructural Features:")
            for structure, count in sorted(stats['structure_distribution'].items(), 
                                         key=lambda x: x[1], reverse=True):
                print(f"  {structure.value}: {count}")
        
        print(f"\nZ-level Distribution:")
        for z_level, count in sorted(stats['z_level_distribution'].items(), 
                                   key=lambda x: x[0].value):
            percentage = count / stats['total_tiles'] * 100
            print(f"  {z_level.value}: {count} ({percentage:.1f}%)")

# Reuse noise generator
class HierarchicalNoise:
    """Multi-scale noise generator for local features"""
    
    def __init__(self, seed: int):
        random.seed(seed)
        self.seed = seed
        self.perm = list(range(256))
        random.shuffle(self.perm)
        self.perm = self.perm + self.perm
    
    def noise2d(self, x: float, y: float) -> float:
        return math.sin(x * 12.9898 + y * 78.233 + self.seed) * 0.5
    
    def octave_noise(self, x: float, y: float, octaves: int = 4, 
                     persistence: float = 0.5, lacunarity: float = 2.0) -> float:
        value = 0.0
        amplitude = 1.0
        frequency = 1.0
        max_value = 0.0
        
        for _ in range(octaves):
            value += self.noise2d(x * frequency, y * frequency) * amplitude
            max_value += amplitude
            amplitude *= persistence
            frequency *= lacunarity
        
        return value / max_value

# Example usage and testing
if __name__ == "__main__":
    # Import required enums (normally these come from regional generator)
    from regional_scale_generator import TerrainSubtype, LandmarkType, ResourceConcentration
    
    # Create a sample regional tile (normally this comes from regional generator)
    sample_regional_tile = type('RegionalTile', (), {
        'terrain_subtype': TerrainSubtype.DENSE_FOREST,
        'micro_elevation': 125.0,  # 125m base elevation
        'landmark': LandmarkType.CAVE_ENTRANCE,
        'resource_concentration': ResourceConcentration.WOOD_GROVE,
        'has_minor_river': True,
        'fertility': 0.7,
        'accessibility': 0.6
    })()
    
    # Sample neighboring regional tiles
    neighbors = {
        'north': type('RegionalTile', (), {'terrain_subtype': TerrainSubtype.FOREST_CLEARING})(),
        'south': type('RegionalTile', (), {'terrain_subtype': TerrainSubtype.STEEP_SLOPES})(),
        'east': type('RegionalTile', (), {'terrain_subtype': TerrainSubtype.MARSH})(),
        'west': type('RegionalTile', (), {'terrain_subtype': TerrainSubtype.DENSE_FOREST})()
    }
    
    # World context (climate, season, etc.)
    world_context = {
        'climate_zone': 'temperate',
        'season': 'summer',
        'precipitation': 0.7,
        'temperature': 0.6
    }
    
    # Generate local chunk
    generator = LocalGenerator(seed=12345)
    local_map = generator.generate_local_chunk(sample_regional_tile, neighbors, world_context)
    
    # Print statistics
    generator.print_local_stats(local_map, sample_regional_tile)
    
    # Display sample of the local map
    print(f"\nLocal Map Sample (32×32 meters):")
    for y in range(min(24, generator.chunk_size)):  # Show first 24 rows
        line = ""
        for x in range(min(32, generator.chunk_size)):
            tile = local_map[y][x]
            line += tile.char
        print(line)
    
    # Show detailed examples of interesting tiles
    print(f"\nDetailed Tile Examples:")
    
    # Find a few interesting tiles
    interesting_tiles = []
    for row in local_map:
        for tile in row:
            if (tile.harvestable_resource or tile.structural_feature or 
                tile.animal_spawn_point or tile.z_level != ZLevel.SURFACE):
                interesting_tiles.append(tile)
                if len(interesting_tiles) >= 5:  # Limit to 5 examples
                    break
        if len(interesting_tiles) >= 5:
            break
    
    for i, tile in enumerate(interesting_tiles):
        print(f"\nTile {i+1} at ({tile.x}, {tile.y}):")
        print(f"  Sub-terrain: {tile.sub_terrain.value}")
        print(f"  Z-level: {tile.z_level.value}")
        print(f"  Elevation: {tile.precise_elevation:.2f}m")
        print(f"  Movement cost: {tile.movement_cost:.1f}x")
        print(f"  Concealment: {tile.concealment:.1f}")
        
        if tile.harvestable_resource:
            print(f"  Resource: {tile.harvestable_resource.value} (qty: {tile.resource_quantity})")
            if tile.resource_respawn_time > 0:
                print(f"  Respawns in: {tile.resource_respawn_time} days")
            else:
                print(f"  Finite resource")
        
        if tile.structural_feature:
            print(f"  Structure: {tile.structural_feature.value}")
            if tile.can_access_upper_level:
                print(f"  Provides access to upper level")
            if tile.can_access_lower_level:
                print(f"  Provides access to lower level")
            if tile.blocks_movement:
                print(f"  Blocks movement")
        
        if tile.animal_spawn_point:
            print(f"  Animal spawn: {tile.animal_spawn_point.value}")
            print(f"  Max animals: {tile.max_animals}")
            print(f"  Spawn frequency: {tile.spawn_frequency:.3f}/day")
    
    # Summary of gameplay features
    total_resources = sum(1 for row in local_map for tile in row if tile.harvestable_resource)
    total_structures = sum(1 for row in local_map for tile in row if tile.structural_feature)
    total_animal_spawns = sum(1 for row in local_map for tile in row if tile.animal_spawn_point)
    cave_entrances = sum(1 for row in local_map for tile in row 
                        if tile.structural_feature == StructuralFeature.CAVE_MOUTH)
    upper_access = sum(1 for row in local_map for tile in row if tile.can_access_upper_level)
    lower_access = sum(1 for row in local_map for tile in row if tile.can_access_lower_level)
    
    print(f"\nGameplay Feature Summary:")
    print(f"  Harvestable resource tiles: {total_resources}")
    print(f"  Structural features: {total_structures}")
    print(f"  Animal spawn areas: {total_animal_spawns}")
    print(f"  Cave entrances: {cave_entrances}")
    print(f"  Upper level access points: {upper_access}")
    print(f"  Lower level access points: {lower_access}")
    
    print(f"\nLocal chunk generation demonstrates:")
    print(f"  • Meter-level precision (1 tile = 1 square meter)")
    print(f"  • Sub-terrain variety within regional terrain type") 
    print(f"  • Specific harvestable resources with quantities and respawn times")
    print(f"  • 3D structure with multiple Z-levels and access points")
    print(f"  • Animal spawn areas with population limits and frequencies")
    print(f"  • Structural features affecting movement and line-of-sight")
    print(f"  • Realistic movement costs and concealment values")
    print(f"  • Seamless integration with regional and world-scale data")