# Regional Scale Generator - Complete Implementation
# Drills down from world biomes to create detailed 32×32 regional terrain

import random
import math
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Dict, Set, Optional
import heapq

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

class LandmarkType(Enum):
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
    """Detailed regional tile data"""
    # Coordinates
    x: int
    y: int
    
    # Terrain
    parent_biome: 'BiomeType'  # From world scale
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

class RegionalGenerator:
    """Generates detailed 32×32 regional maps from world-scale biome data"""
    
    def __init__(self, seed: int):
        self.seed = seed
        self.noise = HierarchicalNoise(seed + 1000)  # Offset from world generator
        
        # Regional parameters
        self.region_size = 32
        self.max_lakes = 6
        self.max_minor_rivers = 8
        self.landmark_density = 0.03  # 3% chance per tile
        self.resource_cluster_density = 0.05  # 5% chance per tile
        
        # Scale factors for regional features
        self.terrain_detail_scale = 0.15    # Terrain variation within biomes
        self.elevation_detail_scale = 0.2   # Fine elevation details
        self.water_scale = 0.1              # Small water bodies
        self.landmark_scale = 0.08          # Landmark placement
        
    def generate_regional_map(self, world_tile_data: 'WorldTile', 
                             neighboring_world_tiles: Dict[str, 'WorldTile']) -> List[List[RegionalTile]]:
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
        
        # Phase 7: Calculate derived properties
        print("  7. Calculating derived properties...")
        self._calculate_derived_properties(regional_map, world_tile_data)
        
        # Phase 8: Generate visual representation
        print("  8. Generating visual representation...")
        self._generate_regional_display(regional_map, world_tile_data)
        
        print("  Regional generation complete!")
        return regional_map
    
    def _initialize_regional_map(self, world_tile: 'WorldTile') -> List[List[RegionalTile]]:
        """Initialize 32×32 regional map with basic data"""
        regional_map = []
        
        for y in range(self.region_size):
            row = []
            for x in range(self.region_size):
                tile = RegionalTile(
                    x=x, y=y,
                    parent_biome=world_tile.biome,
                    terrain_subtype=TerrainSubtype.PLAINS,  # Will be determined later
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
                    fg_color=(100, 100, 100),
                    bg_color=(50, 50, 50)
                )
                row.append(tile)
            regional_map.append(row)
        
        return regional_map
    
    def _generate_terrain_subtypes(self, regional_map: List[List[RegionalTile]], 
                                  world_tile: 'WorldTile',
                                  neighbors: Dict[str, 'WorldTile']):
        """Generate terrain subtypes within the parent biome"""
        
        # Define subtype distributions for each biome
        subtype_distributions = {
            BiomeType.GRASSLAND: {
                TerrainSubtype.PLAINS: 0.4,
                TerrainSubtype.ROLLING_HILLS: 0.3,
                TerrainSubtype.MEADOWS: 0.2,
                TerrainSubtype.SHRUBLAND: 0.1
            },
            BiomeType.TEMPERATE_FOREST: {
                TerrainSubtype.DENSE_FOREST: 0.4,
                TerrainSubtype.LIGHT_WOODLAND: 0.3,
                TerrainSubtype.FOREST_CLEARING: 0.2,
                TerrainSubtype.OLD_GROWTH: 0.1
            },
            BiomeType.TROPICAL_FOREST: {
                TerrainSubtype.DENSE_FOREST: 0.6,
                TerrainSubtype.LIGHT_WOODLAND: 0.2,
                TerrainSubtype.FOREST_CLEARING: 0.15,
                TerrainSubtype.OLD_GROWTH: 0.05
            },
            BiomeType.DESERT: {
                TerrainSubtype.SAND_DUNES: 0.4,
                TerrainSubtype.ROCKY_DESERT: 0.4,
                TerrainSubtype.BADLANDS: 0.15,
                TerrainSubtype.OASIS: 0.05
            },
            BiomeType.HIGH_MOUNTAINS: {
                TerrainSubtype.STEEP_SLOPES: 0.4,
                TerrainSubtype.CLIFFS: 0.3,
                TerrainSubtype.MOUNTAIN_VALLEY: 0.2,
                TerrainSubtype.ALPINE_MEADOW: 0.1
            },
            BiomeType.TUNDRA: {
                TerrainSubtype.PERMAFROST: 0.5,
                TerrainSubtype.TUNDRA_HILLS: 0.3,
                TerrainSubtype.ICE_FIELDS: 0.2
            }
        }
        
        # Get distribution for this biome (default to plains if not defined)
        distribution = subtype_distributions.get(world_tile.biome, {
            TerrainSubtype.PLAINS: 1.0
        })
        
        # Generate terrain patches using noise
        for y in range(self.region_size):
            for x in range(self.region_size):
                tile = regional_map[y][x]
                
                # Use noise to determine subtype with clustering
                terrain_noise = self.noise.octave_noise(
                    x * self.terrain_detail_scale,
                    y * self.terrain_detail_scale,
                    octaves=3,
                    persistence=0.6
                )
                
                # Neighbor influence for clustering
                neighbor_influence = self._calculate_neighbor_subtype_influence(regional_map, x, y)
                
                # Combine noise with distribution probabilities
                final_noise = (terrain_noise + 1) / 2  # Normalize to 0-1
                final_noise = (final_noise + neighbor_influence) / 2
                
                # Select subtype based on weighted distribution
                tile.terrain_subtype = self._select_subtype_from_distribution(distribution, final_noise)
                
                # Handle biome edge effects
                edge_distance = min(x, y, self.region_size - 1 - x, self.region_size - 1 - y)
                if edge_distance < 3:  # Near edge
                    tile.biome_edge = True
                    # Consider neighbor biome influence
                    tile.terrain_subtype = self._apply_neighbor_biome_influence(
                        tile.terrain_subtype, neighbors, x, y, edge_distance
                    )
    
    def _calculate_neighbor_subtype_influence(self, regional_map: List[List[RegionalTile]], 
                                           x: int, y: int) -> float:
        """Calculate influence of already-assigned neighboring subtypes"""
        if x == 0 and y == 0:
            return 0.0  # No neighbors to influence
        
        subtype_weights = {}
        total_weight = 0
        
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.region_size and 0 <= ny < self.region_size:
                    if nx < x or (nx == x and ny < y):  # Only check already processed tiles
                        neighbor_subtype = regional_map[ny][nx].terrain_subtype
                        weight = 1.0 / max(1, abs(dx) + abs(dy))  # Closer neighbors have more influence
                        subtype_weights[neighbor_subtype] = subtype_weights.get(neighbor_subtype, 0) + weight
                        total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        # Return influence toward most common neighbor subtype
        most_common_subtype = max(subtype_weights.keys(), key=lambda k: subtype_weights[k])
        return subtype_weights[most_common_subtype] / total_weight * 0.3  # 30% influence
    
    def _select_subtype_from_distribution(self, distribution: Dict[TerrainSubtype, float], 
                                        noise_value: float) -> TerrainSubtype:
        """Select terrain subtype based on weighted distribution and noise"""
        cumulative = 0.0
        
        # Adjust noise to favor different subtypes
        adjusted_noise = (noise_value + random.uniform(-0.1, 0.1)) % 1.0
        
        for subtype, probability in distribution.items():
            cumulative += probability
            if adjusted_noise <= cumulative:
                return subtype
        
        # Fallback
        return list(distribution.keys())[0]
    
    def _apply_neighbor_biome_influence(self, current_subtype: TerrainSubtype, 
                                      neighbors: Dict[str, 'WorldTile'],
                                      x: int, y: int, edge_distance: int) -> TerrainSubtype:
        """Apply neighboring world biome influence at region edges"""
        
        # Determine which edge we're near
        edge_type = None
        if x < 3:
            edge_type = "west"
        elif x >= self.region_size - 3:
            edge_type = "east"
        elif y < 3:
            edge_type = "north"
        elif y >= self.region_size - 3:
            edge_type = "south"
        
        if edge_type and edge_type in neighbors:
            neighbor_biome = neighbors[edge_type].biome
            influence_strength = (3 - edge_distance) / 3  # Stronger influence closer to edge
            
            # Apply transition effects
            if influence_strength > 0.5:
                return self._create_transition_subtype(current_subtype, neighbor_biome)
        
        return current_subtype
    
    def _create_transition_subtype(self, base_subtype: TerrainSubtype, 
                                 neighbor_biome: 'BiomeType') -> TerrainSubtype:
        """Create transition terrain between biomes"""
        
        # Simple transition rules
        if neighbor_biome == BiomeType.WATER:
            return TerrainSubtype.MARSH  # Land near water becomes marshy
        elif neighbor_biome == BiomeType.DESERT:
            return TerrainSubtype.SHRUBLAND  # Near desert becomes shrubland
        elif neighbor_biome == BiomeType.HIGH_MOUNTAINS:
            return TerrainSubtype.ROLLING_HILLS  # Near mountains becomes hilly
        
        return base_subtype  # No transition needed
    
    def _generate_micro_elevation(self, regional_map: List[List[RegionalTile]], 
                                world_tile: 'WorldTile'):
        """Add fine elevation detail within the region"""
        
        base_elevation = world_tile.final_elevation
        
        for y in range(self.region_size):
            for x in range(self.region_size):
                tile = regional_map[y][x]
                
                # Fine elevation noise
                elevation_noise = self.noise.octave_noise(
                    x * self.elevation_detail_scale,
                    y * self.elevation_detail_scale,
                    octaves=4,
                    persistence=0.4
                )
                
                # Scale elevation variation based on terrain subtype
                elevation_variation = self._get_elevation_variation_for_subtype(tile.terrain_subtype)
                micro_elevation = elevation_noise * elevation_variation
                
                # Smooth transitions between different subtypes
                micro_elevation = self._smooth_elevation_transitions(regional_map, x, y, micro_elevation)
                
                tile.micro_elevation = base_elevation + micro_elevation
    
    def _get_elevation_variation_for_subtype(self, subtype: TerrainSubtype) -> float:
        """Get appropriate elevation variation range for terrain subtype"""
        variations = {
            TerrainSubtype.PLAINS: 20,
            TerrainSubtype.ROLLING_HILLS: 100,
            TerrainSubtype.STEEP_SLOPES: 300,
            TerrainSubtype.CLIFFS: 200,
            TerrainSubtype.MOUNTAIN_VALLEY: 50,
            TerrainSubtype.DENSE_FOREST: 40,
            TerrainSubtype.SAND_DUNES: 80,
            TerrainSubtype.ROCKY_DESERT: 120,
            TerrainSubtype.MARSH: 10,
            TerrainSubtype.PERMAFROST: 30
        }
        return variations.get(subtype, 50)
    
    def _smooth_elevation_transitions(self, regional_map: List[List[RegionalTile]], 
                                    x: int, y: int, elevation: float) -> float:
        """Smooth elevation transitions between different terrain types"""
        if x == 0 or y == 0:
            return elevation
        
        # Average with processed neighbors for smoothing
        neighbor_elevations = []
        for dy in [-1, 0]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                if dx > 0 and dy == 0:  # Don't check unprocessed tiles
                    continue
                
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.region_size and 0 <= ny < self.region_size:
                    neighbor_elevations.append(regional_map[ny][nx].micro_elevation)
        
        if neighbor_elevations:
            avg_neighbor = sum(neighbor_elevations) / len(neighbor_elevations)
            # Blend with neighbors for smoothing
            return elevation * 0.7 + (avg_neighbor * 0.3)
        
        return elevation
    
    def _generate_minor_water_systems(self, regional_map: List[List[RegionalTile]], 
                                    world_tile: 'WorldTile'):
        """Generate lakes and minor rivers within the region"""
        
        # Generate lakes first
        lakes = self._generate_lakes(regional_map, world_tile)
        
        # Generate minor rivers
        rivers = self._generate_minor_rivers(regional_map, world_tile, lakes)
        
        # Apply water features to tiles
        self._apply_water_features_to_tiles(regional_map, lakes, rivers)
    
    def _generate_lakes(self, regional_map: List[List[RegionalTile]], 
                       world_tile: 'WorldTile') -> List[LakeSystem]:
        """Generate lake systems within the region"""
        lakes = []
        
        # Determine number of lakes based on biome and precipitation
        lake_probability = 0.3 * world_tile.precipitation
        
        if world_tile.biome in [BiomeType.WETLAND, BiomeType.TUNDRA]:
            lake_probability *= 2.0
        elif world_tile.biome in [BiomeType.DESERT, BiomeType.HIGH_MOUNTAINS]:
            lake_probability *= 0.3
        
        num_lakes = 0
        for _ in range(self.max_lakes):
            if random.random() < lake_probability:
                num_lakes += 1
        
        # Place lakes in suitable locations
        for lake_id in range(num_lakes):
            attempts = 0
            while attempts < 30:  # Try to find good lake placement
                center_x = random.uniform(3, self.region_size - 3)
                center_y = random.uniform(3, self.region_size - 3)
                
                # Check if location is suitable (lower elevation, good terrain)
                tile_x, tile_y = int(center_x), int(center_y)
                if self._is_good_lake_location(regional_map, tile_x, tile_y):
                    size = random.uniform(1.5, 4.0)
                    depth = random.uniform(5, 50)
                    
                    # Seasonal lakes in dry areas
                    is_seasonal = (world_tile.precipitation < 0.4 and 
                                 world_tile.biome != BiomeType.WETLAND)
                    
                    lake = LakeSystem(
                        id=lake_id,
                        center_x=center_x,
                        center_y=center_y,
                        size=size,
                        depth=depth,
                        is_seasonal=is_seasonal,
                        connects_to_river=False  # Will be determined later
                    )
                    lakes.append(lake)
                    break
                
                attempts += 1
        
        return lakes
    
    def _is_good_lake_location(self, regional_map: List[List[RegionalTile]], x: int, y: int) -> bool:
        """Check if location is suitable for a lake"""
        if not (0 <= x < self.region_size and 0 <= y < self.region_size):
            return False
        
        tile = regional_map[y][x]
        
        # Check terrain suitability
        good_for_lakes = [
            TerrainSubtype.PLAINS, TerrainSubtype.MEADOWS, 
            TerrainSubtype.MOUNTAIN_VALLEY, TerrainSubtype.FOREST_CLEARING
        ]
        
        if tile.terrain_subtype not in good_for_lakes:
            return False
        
        # Check if area is relatively low elevation (will be calculated later)
        # For now, use a simple check
        return True
    
    def _generate_minor_rivers(self, regional_map: List[List[RegionalTile]], 
                             world_tile: 'WorldTile', 
                             lakes: List[LakeSystem]) -> List[RiverSegment]:
        """Generate minor river systems"""
        rivers = []
        
        # Determine number of minor rivers
        river_probability = 0.4 * world_tile.precipitation
        if world_tile.has_major_river:
            river_probability *= 0.5  # Fewer minor rivers if major river present
        
        num_rivers = 0
        for _ in range(self.max_minor_rivers):
            if random.random() < river_probability:
                num_rivers += 1
        
        # Generate rivers from various sources
        for river_id in range(num_rivers):
            source_type = self._determine_river_source_type(world_tile, lakes)
            
            if source_type == "spring":
                river = self._generate_spring_river(regional_map, river_id)
            elif source_type == "lake":
                river = self._generate_lake_outlet_river(regional_map, lakes, river_id)
            elif source_type == "mountain":
                river = self._generate_mountain_river(regional_map, river_id)
            else:  # world_river tributary
                river = self._generate_tributary_river(regional_map, world_tile, river_id)
            
            if river:
                rivers.append(river)
        
        return rivers
    
    def _determine_river_source_type(self, world_tile: 'WorldTile', lakes: List[LakeSystem]) -> str:
        """Determine what type of river source to generate"""
        if world_tile.biome == BiomeType.HIGH_MOUNTAINS:
            return "mountain" if random.random() < 0.6 else "spring"
        elif len(lakes) > 0 and random.random() < 0.4:
            return "lake"
        elif world_tile.has_major_river and random.random() < 0.5:
            return "world_river"
        else:
            return "spring"
    
    def _generate_spring_river(self, regional_map: List[List[RegionalTile]], river_id: int) -> Optional[RiverSegment]:
        """Generate a river starting from a natural spring"""
        
        # Find high elevation area for spring
        best_elevation = -float('inf')
        best_location = None
        
        for _ in range(20):  # Try multiple locations
            x = random.randint(2, self.region_size - 3)
            y = random.randint(2, self.region_size - 3)
            
            elevation = regional_map[y][x].micro_elevation
            if elevation > best_elevation:
                best_elevation = elevation
                best_location = (x, y)
        
        if not best_location:
            return None
        
        # Trace river downhill
        path = self._trace_river_path(regional_map, best_location[0], best_location[1])
        
        if len(path) < 3:  # River too short
            return None
        
        return RiverSegment(
            id=river_id,
            path=path,
            size=1,  # Small stream
            source_type="spring",
            connects_to_world_river=False
        )
    
    def _generate_lake_outlet_river(self, regional_map: List[List[RegionalTile]], 
                                   lakes: List[LakeSystem], river_id: int) -> Optional[RiverSegment]:
        """Generate river flowing out of a lake"""
        if not lakes:
            return None
        
        lake = random.choice(lakes)
        
        # Find outlet point on lake perimeter
        outlet_x = int(lake.center_x + random.uniform(-lake.size, lake.size))
        outlet_y = int(lake.center_y + random.uniform(-lake.size, lake.size))
        
        outlet_x = max(0, min(self.region_size - 1, outlet_x))
        outlet_y = max(0, min(self.region_size - 1, outlet_y))
        
        # Trace river from outlet
        path = self._trace_river_path(regional_map, outlet_x, outlet_y)
        
        if len(path) < 2:
            return None
        
        lake.connects_to_river = True
        
        return RiverSegment(
            id=river_id,
            path=path,
            size=2,  # Medium creek
            source_type="lake",
            connects_to_world_river=False
        )
    
    def _generate_mountain_river(self, regional_map: List[List[RegionalTile]], river_id: int) -> Optional[RiverSegment]:
        """Generate river from mountain snowmelt/rainfall"""
        
        # Find highest mountain area
        highest_elevation = -float('inf')
        mountain_peak = None
        
        for y in range(self.region_size):
            for x in range(self.region_size):
                tile = regional_map[y][x]
                if tile.terrain_subtype in [TerrainSubtype.STEEP_SLOPES, TerrainSubtype.CLIFFS]:
                    if tile.micro_elevation > highest_elevation:
                        highest_elevation = tile.micro_elevation
                        mountain_peak = (x, y)
        
        if not mountain_peak:
            return None
        
        # Trace river downhill from peak
        path = self._trace_river_path(regional_map, mountain_peak[0], mountain_peak[1])
        
        if len(path) < 4:  # Mountain rivers should be longer
            return None
        
        return RiverSegment(
            id=river_id,
            path=path,
            size=random.choice([1, 2]),  # Stream or creek
            source_type="mountain",
            connects_to_world_river=False
        )
    
    def _generate_tributary_river(self, regional_map: List[List[RegionalTile]], 
                                world_tile: 'WorldTile', river_id: int) -> Optional[RiverSegment]:
        """Generate tributary connecting to world-scale major river"""
        if not world_tile.has_major_river:
            return None
        
        # Major river assumed to flow through region edge or center
        # For simplicity, assume it flows west-to-east through center
        main_river_y = self.region_size // 2
        
        # Generate tributary starting from random high point
        source_x = random.randint(5, self.region_size - 5)
        source_y = random.randint(5, main_river_y - 3) if random.random() < 0.5 else random.randint(main_river_y + 3, self.region_size - 5)
        
        # Trace path toward main river
        path = self._trace_river_toward_target(regional_map, source_x, source_y, 
                                             self.region_size // 2, main_river_y)
        
        if len(path) < 3:
            return None
        
        return RiverSegment(
            id=river_id,
            path=path,
            size=random.choice([2, 3]),  # Creek or river
            source_type="world_river",
            connects_to_world_river=True
        )
    
    def _trace_river_path(self, regional_map: List[List[RegionalTile]], 
                         start_x: int, start_y: int) -> List[Tuple[int, int]]:
        """Trace river path following steepest descent"""
        path = [(start_x, start_y)]
        current_x, current_y = start_x, start_y
        visited = set()
        
        while len(path) < 20:  # Maximum river length
            if (current_x, current_y) in visited:
                break
            
            visited.add((current_x, current_y))
            
            # Find steepest descent
            best_slope = 0
            best_next = None
            
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    
                    nx, ny = current_x + dx, current_y + dy
                    if 0 <= nx < self.region_size and 0 <= ny < self.region_size:
                        current_elev = regional_map[current_y][current_x].micro_elevation
                        neighbor_elev = regional_map[ny][nx].micro_elevation
                        
                        slope = current_elev - neighbor_elev
                        if slope > best_slope:
                            best_slope = slope
                            best_next = (nx, ny)
            
            if not best_next or best_slope <= 0:
                break
            
            current_x, current_y = best_next
            path.append((current_x, current_y))
        
        return path
    
    def _trace_river_toward_target(self, regional_map: List[List[RegionalTile]], 
                                  start_x: int, start_y: int, 
                                  target_x: int, target_y: int) -> List[Tuple[int, int]]:
        """Trace river path toward specific target (e.g., main river)"""
        path = [(start_x, start_y)]
        current_x, current_y = start_x, start_y
        
        while len(path) < 15:  # Maximum path length
            # Balance between steepest descent and moving toward target
            best_score = -float('inf')
            best_next = None
            
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    
                    nx, ny = current_x + dx, current_y + dy
                    if 0 <= nx < self.region_size and 0 <= ny < self.region_size:
                        
                        # Elevation component (prefer downhill)
                        current_elev = regional_map[current_y][current_x].micro_elevation
                        neighbor_elev = regional_map[ny][nx].micro_elevation
                        elevation_score = current_elev - neighbor_elev
                        
                        # Target direction component
                        current_target_dist = math.sqrt((current_x - target_x)**2 + (current_y - target_y)**2)
                        new_target_dist = math.sqrt((nx - target_x)**2 + (ny - target_y)**2)
                        target_score = (current_target_dist - new_target_dist) * 20  # Weight toward target
                        
                        total_score = elevation_score + target_score
                        
                        if total_score > best_score:
                            best_score = total_score
                            best_next = (nx, ny)
            
            if not best_next:
                break
            
            current_x, current_y = best_next
            path.append((current_x, current_y))
            
            # Stop if we've reached the target area
            if abs(current_x - target_x) <= 1 and abs(current_y - target_y) <= 1:
                break
        
        return path
    
    def _apply_water_features_to_tiles(self, regional_map: List[List[RegionalTile]], 
                                     lakes: List[LakeSystem], 
                                     rivers: List[RiverSegment]):
        """Apply water features to regional tiles"""
        
        # Apply lakes
        for lake in lakes:
            lake_radius_squared = lake.size * lake.size
            for y in range(self.region_size):
                for x in range(self.region_size):
                    dx = x - lake.center_x
                    dy = y - lake.center_y
                    distance_squared = dx*dx + dy*dy
                    
                    if distance_squared <= lake_radius_squared:
                        tile = regional_map[y][x]
                        tile.is_lake = True
                        tile.lake_id = lake.id
                        # Lower elevation for lake
                        tile.micro_elevation -= 5
        
        # Apply rivers
        for river in rivers:
            for i, (x, y) in enumerate(river.path):
                if 0 <= x < self.region_size and 0 <= y < self.region_size:
                    tile = regional_map[y][x]
                    tile.has_minor_river = True
                    tile.river_size = river.size
                    
                    # Set flow direction to next segment
                    if i < len(river.path) - 1:
                        next_x, next_y = river.path[i + 1]
                        tile.water_flow_direction = (next_x - x, next_y - y)
                    
                    # Lower elevation slightly for river channel
                    tile.micro_elevation -= 2
    
    def _place_landmark_features(self, regional_map: List[List[RegionalTile]], 
                               world_tile: 'WorldTile'):
        """Place distinctive landmark features throughout the region"""
        
        # Determine appropriate landmarks for this biome
        biome_landmarks = self._get_biome_appropriate_landmarks(world_tile.biome)
        
        # Place landmarks with appropriate density
        for y in range(self.region_size):
            for x in range(self.region_size):
                if random.random() < self.landmark_density:
                    tile = regional_map[y][x]
                    
                    # Choose landmark based on terrain and biome
                    possible_landmarks = self._filter_landmarks_by_terrain(
                        biome_landmarks, tile.terrain_subtype, tile
                    )
                    
                    if possible_landmarks:
                        landmark = random.choice(possible_landmarks)
                        
                        # Ensure landmark spacing (don't cluster too much)
                        if self._check_landmark_spacing(regional_map, x, y, min_distance=3):
                            tile.landmark = landmark
                            # Apply landmark effects
                            self._apply_landmark_effects(tile, landmark)
    
    def _get_biome_appropriate_landmarks(self, biome: 'BiomeType') -> List[LandmarkType]:
        """Get landmarks appropriate for this biome"""
        biome_landmarks = {
            BiomeType.GRASSLAND: [
                LandmarkType.STANDING_STONES, LandmarkType.NATURAL_SPRING,
                LandmarkType.UNUSUAL_ROCK_FORMATION, LandmarkType.CRATER
            ],
            BiomeType.TEMPERATE_FOREST: [
                LandmarkType.ANCIENT_GROVE, LandmarkType.NATURAL_SPRING,
                LandmarkType.CAVE_ENTRANCE, LandmarkType.DEEP_POOL
            ],
            BiomeType.HIGH_MOUNTAINS: [
                LandmarkType.MOUNTAIN_PASS, LandmarkType.SCENIC_OVERLOOK,
                LandmarkType.NATURAL_BRIDGE, LandmarkType.CAVE_ENTRANCE,
                LandmarkType.HIDDEN_VALLEY, LandmarkType.WATERFALL
            ],
            BiomeType.DESERT: [
                LandmarkType.NATURAL_ARCH, LandmarkType.UNUSUAL_ROCK_FORMATION,
                LandmarkType.OASIS, LandmarkType.SALT_FLAT, LandmarkType.CRATER
            ],
            BiomeType.WETLAND: [
                LandmarkType.DEEP_POOL, LandmarkType.NATURAL_SPRING,
                LandmarkType.MINERAL_SPRING
            ],
            BiomeType.TUNDRA: [
                LandmarkType.STANDING_STONES, LandmarkType.CRATER,
                LandmarkType.ICE_FIELDS
            ],
            BiomeType.TAIGA: [
                LandmarkType.ANCIENT_GROVE, LandmarkType.CAVE_ENTRANCE,
                LandmarkType.NATURAL_SPRING
            ]
        }
        
        return biome_landmarks.get(biome, [LandmarkType.UNUSUAL_ROCK_FORMATION])
    
    def _filter_landmarks_by_terrain(self, possible_landmarks: List[LandmarkType], 
                                   terrain_subtype: TerrainSubtype, 
                                   tile: RegionalTile) -> List[LandmarkType]:
        """Filter landmarks that are appropriate for specific terrain"""
        
        terrain_compatibility = {
            LandmarkType.CAVE_ENTRANCE: [
                TerrainSubtype.CLIFFS, TerrainSubtype.STEEP_SLOPES, 
                TerrainSubtype.ROCKY_DESERT, TerrainSubtype.ROLLING_HILLS
            ],
            LandmarkType.MOUNTAIN_PASS: [
                TerrainSubtype.STEEP_SLOPES, TerrainSubtype.MOUNTAIN_VALLEY
            ],
            LandmarkType.WATERFALL: [
                TerrainSubtype.CLIFFS, TerrainSubtype.STEEP_SLOPES
            ],
            LandmarkType.NATURAL_SPRING: [
                TerrainSubtype.ROLLING_HILLS, TerrainSubtype.MOUNTAIN_VALLEY,
                TerrainSubtype.FOREST_CLEARING, TerrainSubtype.MEADOWS
            ],
            LandmarkType.ANCIENT_GROVE: [
                TerrainSubtype.OLD_GROWTH, TerrainSubtype.DENSE_FOREST,
                TerrainSubtype.FOREST_CLEARING
            ],
            LandmarkType.STANDING_STONES: [
                TerrainSubtype.PLAINS, TerrainSubtype.MEADOWS, 
                TerrainSubtype.ROLLING_HILLS
            ],
            LandmarkType.NATURAL_ARCH: [
                TerrainSubtype.ROCKY_DESERT, TerrainSubtype.BADLANDS,
                TerrainSubtype.CLIFFS
            ],
            LandmarkType.SALT_FLAT: [
                TerrainSubtype.ROCKY_DESERT, TerrainSubtype.BADLANDS
            ]
        }
        
        filtered = []
        for landmark in possible_landmarks:
            compatible_terrains = terrain_compatibility.get(landmark, [terrain_subtype])
            if terrain_subtype in compatible_terrains:
                filtered.append(landmark)
        
        return filtered
    
    def _check_landmark_spacing(self, regional_map: List[List[RegionalTile]], 
                              x: int, y: int, min_distance: int = 3) -> bool:
        """Ensure landmarks aren't too close together"""
        for dy in range(-min_distance, min_distance + 1):
            for dx in range(-min_distance, min_distance + 1):
                if dx == 0 and dy == 0:
                    continue
                
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.region_size and 0 <= ny < self.region_size:
                    if regional_map[ny][nx].landmark is not None:
                        return False
        return True
    
    def _apply_landmark_effects(self, tile: RegionalTile, landmark: LandmarkType):
        """Apply effects of landmarks on tile properties"""
        
        landmark_effects = {
            LandmarkType.CAVE_ENTRANCE: {
                'accessibility': -0.2,  # Harder to access
                'fertility': 0.0
            },
            LandmarkType.NATURAL_SPRING: {
                'accessibility': 0.1,
                'fertility': 0.3  # Springs improve fertility
            },
            LandmarkType.ANCIENT_GROVE: {
                'accessibility': -0.1,
                'fertility': 0.2
            },
            LandmarkType.MOUNTAIN_PASS: {
                'accessibility': 0.4,  # Easier mountain travel
                'fertility': 0.0
            },
            LandmarkType.WATERFALL: {
                'accessibility': -0.3,
                'fertility': 0.1
            },
            LandmarkType.MINERAL_SPRING: {
                'accessibility': 0.0,
                'fertility': 0.1
            },
            LandmarkType.SALT_FLAT: {
                'accessibility': 0.2,  # Flat and easy to traverse
                'fertility': -0.4  # Poor for agriculture
            }
        }
        
        effects = landmark_effects.get(landmark, {})
        tile.accessibility += effects.get('accessibility', 0.0)
        tile.fertility += effects.get('fertility', 0.0)
        
        # Clamp values
        tile.accessibility = max(0.0, min(1.0, tile.accessibility))
        tile.fertility = max(0.0, min(1.0, tile.fertility))
    
    def _assign_resource_concentrations(self, regional_map: List[List[RegionalTile]], 
                                      world_tile: 'WorldTile'):
        """Assign resource concentration areas throughout the region"""
        
        # Determine appropriate resource types for this biome
        biome_resources = self._get_biome_resource_types(world_tile.biome)
        
        # Use clustered placement for realistic resource distribution
        clusters_placed = 0
        max_clusters = 8
        
        while clusters_placed < max_clusters:
            if random.random() < self.resource_cluster_density:
                # Pick random center point
                center_x = random.randint(2, self.region_size - 3)
                center_y = random.randint(2, self.region_size - 3)
                
                # Choose resource type appropriate for terrain
                tile = regional_map[center_y][center_x]
                suitable_resources = self._filter_resources_by_terrain(
                    biome_resources, tile.terrain_subtype
                )
                
                if suitable_resources:
                    resource_type = random.choice(suitable_resources)
                    cluster_size = random.uniform(1.5, 4.0)
                    
                    # Place resource cluster
                    self._place_resource_cluster(regional_map, center_x, center_y, 
                                               resource_type, cluster_size)
                    clusters_placed += 1
            
            # Avoid infinite loop
            if clusters_placed >= max_clusters:
                break
    
    def _get_biome_resource_types(self, biome: 'BiomeType') -> List[ResourceConcentration]:
        """Get resource types appropriate for this biome"""
        biome_resources = {
            BiomeType.GRASSLAND: [
                ResourceConcentration.FERTILE_SOIL, ResourceConcentration.HUNTING_GROUNDS,
                ResourceConcentration.HERB_PATCH, ResourceConcentration.CLAY_DEPOSITS
            ],
            BiomeType.TEMPERATE_FOREST: [
                ResourceConcentration.WOOD_GROVE, ResourceConcentration.HUNTING_GROUNDS,
                ResourceConcentration.HERB_PATCH, ResourceConcentration.FERTILE_SOIL
            ],
            BiomeType.TROPICAL_FOREST: [
                ResourceConcentration.WOOD_GROVE, ResourceConcentration.HUNTING_GROUNDS,
                ResourceConcentration.HERB_PATCH
            ],
            BiomeType.HIGH_MOUNTAINS: [
                ResourceConcentration.STONE_QUARRY, ResourceConcentration.METAL_DEPOSIT,
                ResourceConcentration.HERB_PATCH
            ],
            BiomeType.DESERT: [
                ResourceConcentration.STONE_QUARRY, ResourceConcentration.METAL_DEPOSIT,
                ResourceConcentration.CLAY_DEPOSITS
            ],
            BiomeType.WETLAND: [
                ResourceConcentration.FERTILE_SOIL, ResourceConcentration.FISHING_SPOT,
                ResourceConcentration.CLAY_DEPOSITS, ResourceConcentration.HERB_PATCH
            ],
            BiomeType.TUNDRA: [
                ResourceConcentration.HUNTING_GROUNDS, ResourceConcentration.STONE_QUARRY
            ],
            BiomeType.TAIGA: [
                ResourceConcentration.WOOD_GROVE, ResourceConcentration.HUNTING_GROUNDS
            ]
        }
        
        return biome_resources.get(biome, [ResourceConcentration.STONE_QUARRY])
    
    def _filter_resources_by_terrain(self, possible_resources: List[ResourceConcentration], 
                                   terrain_subtype: TerrainSubtype) -> List[ResourceConcentration]:
        """Filter resources that can appear on specific terrain"""
        
        terrain_resource_compatibility = {
            ResourceConcentration.WOOD_GROVE: [
                TerrainSubtype.DENSE_FOREST, TerrainSubtype.OLD_GROWTH,
                TerrainSubtype.LIGHT_WOODLAND
            ],
            ResourceConcentration.STONE_QUARRY: [
                TerrainSubtype.CLIFFS, TerrainSubtype.ROCKY_DESERT,
                TerrainSubtype.STEEP_SLOPES, TerrainSubtype.ROLLING_HILLS
            ],
            ResourceConcentration.METAL_DEPOSIT: [
                TerrainSubtype.CLIFFS, TerrainSubtype.STEEP_SLOPES,
                TerrainSubtype.ROCKY_DESERT, TerrainSubtype.ROLLING_HILLS
            ],
            ResourceConcentration.FERTILE_SOIL: [
                TerrainSubtype.PLAINS, TerrainSubtype.MEADOWS,
                TerrainSubtype.FLOODPLAIN, TerrainSubtype.MOUNTAIN_VALLEY
            ],
            ResourceConcentration.HUNTING_GROUNDS: [
                TerrainSubtype.LIGHT_WOODLAND, TerrainSubtype.MEADOWS,
                TerrainSubtype.PLAINS, TerrainSubtype.SHRUBLAND
            ],
            ResourceConcentration.FISHING_SPOT: [
                TerrainSubtype.DEEP_WATER, TerrainSubtype.CALM_POOLS
            ],
            ResourceConcentration.HERB_PATCH: [
                TerrainSubtype.MEADOWS, TerrainSubtype.FOREST_CLEARING,
                TerrainSubtype.ALPINE_MEADOW, TerrainSubtype.SHRUBLAND
            ],
            ResourceConcentration.CLAY_DEPOSITS: [
                TerrainSubtype.MARSH, TerrainSubtype.FLOODPLAIN,
                TerrainSubtype.PLAINS
            ]
        }
        
        filtered = []
        for resource in possible_resources:
            compatible_terrains = terrain_resource_compatibility.get(resource, [terrain_subtype])
            if terrain_subtype in compatible_terrains:
                filtered.append(resource)
        
        return filtered
    
    def _place_resource_cluster(self, regional_map: List[List[RegionalTile]], 
                              center_x: int, center_y: int, 
                              resource_type: ResourceConcentration, 
                              cluster_size: float):
        """Place a cluster of resource concentration"""
        
        cluster_radius_squared = cluster_size * cluster_size
        
        for y in range(self.region_size):
            for x in range(self.region_size):
                dx = x - center_x
                dy = y - center_y
                distance_squared = dx*dx + dy*dy
                
                if distance_squared <= cluster_radius_squared:
                    distance = math.sqrt(distance_squared)
                    
                    # Probability decreases with distance from center
                    probability = max(0, 1.0 - (distance / cluster_size))
                    
                    if random.random() < probability:
                        tile = regional_map[y][x]
                        if tile.resource_concentration is None:  # Don't override existing
                            tile.resource_concentration = resource_type
    
    def _mark_terrain_boundaries(self, regional_map: List[List[RegionalTile]]):
        """Mark boundaries between different terrain types"""
        
        for y in range(self.region_size):
            for x in range(self.region_size):
                tile = regional_map[y][x]
                current_subtype = tile.terrain_subtype
                
                # Check if adjacent to different terrain type
                is_boundary = False
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.region_size and 0 <= ny < self.region_size:
                            neighbor_subtype = regional_map[ny][nx].terrain_subtype
                            if neighbor_subtype != current_subtype:
                                is_boundary = True
                                break
                    if is_boundary:
                        break
                
                tile.terrain_boundary = is_boundary
    
    def _calculate_derived_properties(self, regional_map: List[List[RegionalTile]], 
                                    world_tile: 'WorldTile'):
        """Calculate fertility, accessibility, and other derived properties"""
        
        for y in range(self.region_size):
            for x in range(self.region_size):
                tile = regional_map[y][x]
                
                # Base fertility from terrain subtype
                base_fertility = self._get_base_fertility(tile.terrain_subtype)
                
                # Modify fertility based on world climate
                climate_fertility_mod = world_tile.precipitation * 0.3
                
                # Water proximity bonus
                water_proximity_bonus = 0.0
                if tile.has_minor_river:
                    water_proximity_bonus = 0.2
                elif tile.is_lake:
                    water_proximity_bonus = 0.1
                else:
                    # Check for nearby water
                    for dy in [-2, -1, 0, 1, 2]:
                        for dx in [-2, -1, 0, 1, 2]:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < self.region_size and 0 <= ny < self.region_size:
                                neighbor = regional_map[ny][nx]
                                if neighbor.has_minor_river or neighbor.is_lake:
                                    distance = max(1, abs(dx) + abs(dy))
                                    water_proximity_bonus += 0.05 / distance
                
                # Final fertility calculation
                tile.fertility = base_fertility + climate_fertility_mod + water_proximity_bonus
                tile.fertility = max(0.0, min(1.0, tile.fertility))
                
                # Base accessibility from terrain
                base_accessibility = self._get_base_accessibility(tile.terrain_subtype)
                
                # River crossings affect accessibility
                if tile.has_minor_river and tile.river_size >= 2:
                    base_accessibility -= 0.2  # Rivers impede movement
                
                # Elevation affects accessibility
                elevation_penalty = abs(tile.micro_elevation) / 1000 * 0.1
                
                tile.accessibility = base_accessibility - elevation_penalty
                tile.accessibility = max(0.0, min(1.0, tile.accessibility))
    
    def _get_base_fertility(self, terrain_subtype: TerrainSubtype) -> float:
        """Get base fertility value for terrain subtype"""
        fertility_values = {
            TerrainSubtype.PLAINS: 0.8,
            TerrainSubtype.MEADOWS: 0.9,
            TerrainSubtype.FLOODPLAIN: 0.95,
            TerrainSubtype.MOUNTAIN_VALLEY: 0.7,
            TerrainSubtype.FOREST_CLEARING: 0.6,
            TerrainSubtype.LIGHT_WOODLAND: 0.4,
            TerrainSubtype.ROLLING_HILLS: 0.6,
            TerrainSubtype.SHRUBLAND: 0.3,
            TerrainSubtype.MARSH: 0.5,
            TerrainSubtype.SWAMP: 0.3,
            TerrainSubtype.SAND_DUNES: 0.1,
            TerrainSubtype.ROCKY_DESERT: 0.05,
            TerrainSubtype.BADLANDS: 0.1,
            TerrainSubtype.STEEP_SLOPES: 0.2,
            TerrainSubtype.CLIFFS: 0.0,
            TerrainSubtype.PERMAFROST: 0.1,
            TerrainSubtype.ICE_FIELDS: 0.0
        }
        return fertility_values.get(terrain_subtype, 0.3)
    
    def _get_base_accessibility(self, terrain_subtype: TerrainSubtype) -> float:
        """Get base accessibility value for terrain subtype"""
        accessibility_values = {
            TerrainSubtype.PLAINS: 0.9,
            TerrainSubtype.MEADOWS: 0.8,
            TerrainSubtype.ROLLING_HILLS: 0.6,
            TerrainSubtype.LIGHT_WOODLAND: 0.7,
            TerrainSubtype.DENSE_FOREST: 0.3,
            TerrainSubtype.FOREST_CLEARING: 0.8,
            TerrainSubtype.SAND_DUNES: 0.4,
            TerrainSubtype.ROCKY_DESERT: 0.5,
            TerrainSubtype.BADLANDS: 0.3,
            TerrainSubtype.STEEP_SLOPES: 0.2,
            TerrainSubtype.CLIFFS: 0.1,
            TerrainSubtype.MOUNTAIN_VALLEY: 0.7,
            TerrainSubtype.ALPINE_MEADOW: 0.6,
            TerrainSubtype.MARSH: 0.3,
            TerrainSubtype.SWAMP: 0.2,
            TerrainSubtype.FLOODPLAIN: 0.8,
            TerrainSubtype.PERMAFROST: 0.5
        }
        return accessibility_values.get(terrain_subtype, 0.5)
    
    def _generate_regional_display(self, regional_map: List[List[RegionalTile]], 
                                 world_tile: 'WorldTile'):
        """Generate display characters and colors for regional tiles"""
        
        # Display configurations for terrain subtypes
        subtype_display = {
            # Grassland subtypes
            TerrainSubtype.PLAINS: (".", (80, 150, 80), (40, 100, 40)),
            TerrainSubtype.ROLLING_HILLS: ("∩", (70, 140, 70), (35, 90, 35)),
            TerrainSubtype.MEADOWS: ("\"", (90, 170, 90), (50, 110, 50)),
            TerrainSubtype.SHRUBLAND: ("≡", (100, 120, 60), (60, 80, 30)),
            
            # Forest subtypes
            TerrainSubtype.DENSE_FOREST: ("♠", (0, 100, 0), (0, 60, 0)),
            TerrainSubtype.LIGHT_WOODLAND: ("♣", (20, 120, 20), (10, 70, 10)),
            TerrainSubtype.FOREST_CLEARING: ("∘", (60, 140, 60), (30, 90, 30)),
            TerrainSubtype.OLD_GROWTH: ("♠", (0, 80, 0), (0, 40, 0)),
            
            # Desert subtypes
            TerrainSubtype.SAND_DUNES: ("∼", (238, 203, 173), (218, 165, 32)),
            TerrainSubtype.ROCKY_DESERT: ("◦", (205, 133, 63), (160, 82, 45)),
            TerrainSubtype.BADLANDS: ("≋", (139, 69, 19), (101, 67, 33)),
            TerrainSubtype.OASIS: ("◯", (0, 150, 0), (0, 100, 50)),
            
            # Mountain subtypes
            TerrainSubtype.STEEP_SLOPES: ("/", (120, 100, 80), (80, 60, 40)),
            TerrainSubtype.GENTLE_SLOPES: ("^", (140, 120, 100), (100, 80, 60)),
            TerrainSubtype.MOUNTAIN_VALLEY: ("∪", (100, 140, 100), (60, 90, 60)),
            TerrainSubtype.ALPINE_MEADOW: ("\"", (120, 180, 120), (80, 130, 80)),
            TerrainSubtype.CLIFFS: ("▓", (100, 80, 60), (60, 40, 20)),
            
            # Water subtypes
            TerrainSubtype.DEEP_WATER: ("≈", (50, 100, 200), (0, 50, 150)),
            TerrainSubtype.SHALLOW_WATER: ("∼", (100, 150, 255), (50, 100, 200)),
            TerrainSubtype.RAPIDS: ("≋", (150, 200, 255), (75, 125, 200)),
            TerrainSubtype.CALM_POOLS: ("○", (80, 130, 220), (40, 80, 170)),
            
            # Wetland subtypes
            TerrainSubtype.MARSH: ("≈", (60, 140, 120), (30, 100, 80)),
            TerrainSubtype.SWAMP: ("≋", (40, 120, 100), (20, 80, 60)),
            TerrainSubtype.BOG: ("∼", (80, 100, 60), (40, 60, 30)),
            TerrainSubtype.FLOODPLAIN: ("\"", (100, 160, 100), (60, 120, 60)),
            
            # Tundra subtypes
            TerrainSubtype.PERMAFROST: ("·", (180, 180, 200), (120, 120, 140)),
            TerrainSubtype.TUNDRA_HILLS: ("∩", (160, 160, 180), (100, 100, 120)),
            TerrainSubtype.ICE_FIELDS: ("*", (240, 240, 255), (200, 200, 220))
        }
        
        # Landmark display characters
        landmark_display = {
            LandmarkType.CAVE_ENTRANCE: ("○", (150, 150, 150), (0, 0, 0)),
            LandmarkType.MOUNTAIN_PASS: ("⌂", (200, 180, 160), (120, 100, 80)),
            LandmarkType.WATERFALL: ("║", (200, 230, 255), (100, 150, 200)),
            LandmarkType.NATURAL_SPRING: ("◉", (100, 200, 255), (50, 150, 200)),
            LandmarkType.ANCIENT_GROVE: ("♠", (0, 150, 0), (0, 80, 0)),
            LandmarkType.STANDING_STONES: ("∩", (150, 150, 150), (100, 100, 100)),
            LandmarkType.NATURAL_ARCH: ("∩", (200, 150, 100), (150, 100, 50)),
            LandmarkType.CRATER: ("○", (139, 69, 19), (101, 67, 33)),
            LandmarkType.SALT_FLAT: ("·", (255, 255, 255), (220, 220, 220)),
            LandmarkType.SCENIC_OVERLOOK: ("▲", (200, 180, 160), (120, 100, 80)),
            LandmarkType.HIDDEN_VALLEY: ("∪", (80, 150, 80), (40, 100, 40))
        }
        
        # Resource concentration indicators (subtle modifications)
        resource_fg_mods = {
            ResourceConcentration.WOOD_GROVE: (0, 20, 0),
            ResourceConcentration.STONE_QUARRY: (20, 20, 20),
            ResourceConcentration.METAL_DEPOSIT: (30, 30, 30),
            ResourceConcentration.FERTILE_SOIL: (20, 40, 20),
            ResourceConcentration.HUNTING_GROUNDS: (15, 15, 0),
            ResourceConcentration.FISHING_SPOT: (0, 20, 40),
            ResourceConcentration.HERB_PATCH: (10, 30, 10),
            ResourceConcentration.CLAY_DEPOSITS: (25, 15, 5)
        }
        
        # Apply display data to all tiles
        for y in range(self.region_size):
            for x in range(self.region_size):
                tile = regional_map[y][x]
                
                # Start with terrain subtype display
                char, fg, bg = subtype_display.get(tile.terrain_subtype, ("?", (255, 255, 255), (0, 0, 0)))
                
                # Override with landmark if present
                if tile.landmark:
                    landmark_char, landmark_fg, landmark_bg = landmark_display.get(
                        tile.landmark, (char, fg, bg)
                    )
                    char, fg, bg = landmark_char, landmark_fg, landmark_bg
                
                # Modify colors for resource concentrations
                if tile.resource_concentration:
                    fg_mod = resource_fg_mods.get(tile.resource_concentration, (0, 0, 0))
                    fg = tuple(max(0, min(255, c + mod)) for c, mod in zip(fg, fg_mod))
                
                # Modify for water features
                if tile.has_minor_river:
                    if tile.river_size == 1:  # Stream
                        char = "∙"
                        fg = (150, 200, 255)
                    elif tile.river_size == 2:  # Creek
                        char = "∼"
                        fg = (100, 150, 255)
                    else:  # River
                        char = "≈"
                        fg = (50, 100, 255)
                
                if tile.is_lake:
                    char = "○"
                    fg = (80, 130, 220)
                    bg = (40, 80, 170)
                
                # Add environmental variation
                variation = random.randint(-10, 10)
                fg = tuple(max(0, min(255, c + variation)) for c in fg)
                bg = tuple(max(0, min(255, c + variation//2)) for c in bg)
                
                # Special markings for boundaries
                if tile.terrain_boundary:
                    # Slightly brighten boundaries for visibility
                    fg = tuple(min(255, c + 15) for c in fg)
                
                tile.char = char
                tile.fg_color = fg
                tile.bg_color = bg
    
    def get_regional_stats(self, regional_map: List[List[RegionalTile]]) -> Dict:
        """Get statistics about the generated regional map"""
        total_tiles = self.region_size * self.region_size
        
        # Count terrain subtypes
        subtype_counts = {}
        landmark_count = 0
        resource_count = 0
        water_tiles = 0
        boundary_tiles = 0
        
        for row in regional_map:
            for tile in row:
                # Terrain subtypes
                subtype = tile.terrain_subtype
                subtype_counts[subtype] = subtype_counts.get(subtype, 0) + 1
                
                # Features
                if tile.landmark:
                    landmark_count += 1
                if tile.resource_concentration:
                    resource_count += 1
                if tile.has_minor_river or tile.is_lake:
                    water_tiles += 1
                if tile.terrain_boundary:
                    boundary_tiles += 1
        
        return {
            'total_tiles': total_tiles,
            'subtype_distribution': subtype_counts,
            'landmarks': landmark_count,
            'resource_concentrations': resource_count,
            'water_features': water_tiles,
            'terrain_boundaries': boundary_tiles,
            'avg_fertility': sum(tile.fertility for row in regional_map for tile in row) / total_tiles,
            'avg_accessibility': sum(tile.accessibility for row in regional_map for tile in row) / total_tiles
        }
    
    def print_regional_stats(self, regional_map: List[List[RegionalTile]], world_tile: 'WorldTile'):
        """Print statistics about the generated regional map"""
        stats = self.get_regional_stats(regional_map)
        
        print(f"\nRegional Map Statistics for {world_tile.biome.value}:")
        print(f"Total tiles: {stats['total_tiles']}")
        print(f"Landmarks: {stats['landmarks']}")
        print(f"Resource concentrations: {stats['resource_concentrations']}")
        print(f"Water features: {stats['water_features']}")
        print(f"Terrain boundaries: {stats['terrain_boundaries']}")
        print(f"Average fertility: {stats['avg_fertility']:.2f}")
        print(f"Average accessibility: {stats['avg_accessibility']:.2f}")
        
        print(f"\nTerrain Subtype Distribution:")
        for subtype, count in sorted(stats['subtype_distribution'].items(), 
                                   key=lambda x: x[1], reverse=True):
            percentage = count / stats['total_tiles'] * 100
            print(f"  {subtype.value}: {count} ({percentage:.1f}%)")

# Reuse NoiseGenerator from world scale
class HierarchicalNoise:
    """Multi-scale noise generator"""
    
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
    
    def ridge_noise(self, x: float, y: float, octaves: int = 4) -> float:
        value = self.octave_noise(x, y, octaves)
        return 1.0 - abs(value)

# Example usage and testing
if __name__ == "__main__":
    # Create a sample world tile (normally this comes from world generator)
    from world_scale_generator import BiomeType, ClimateZone
    
    sample_world_tile = type('WorldTile', (), {
        'biome': BiomeType.TEMPERATE_FOREST,
        'climate_zone': ClimateZone.TEMPERATE,
        'final_elevation': 250.0,  # 250m elevation
        'precipitation': 0.7,
        'temperature': 0.6,
        'has_major_river': True
    })()
    
    # Sample neighboring tiles (for edge effects)
    neighbors = {
        'north': type('WorldTile', (), {'biome': BiomeType.GRASSLAND})(),
        'south': type('WorldTile', (), {'biome': BiomeType.HIGH_MOUNTAINS})(),
        'east': type('WorldTile', (), {'biome': BiomeType.WATER})(),
        'west': type('WorldTile', (), {'biome': BiomeType.TEMPERATE_FOREST})()
    }
    
    # Generate regional map
    generator = RegionalGenerator(seed=12345)
    regional_map = generator.generate_regional_map(sample_world_tile, neighbors)
    
    # Print statistics
    generator.print_regional_stats(regional_map, sample_world_tile)
    
    # Display sample of the regional map
    print(f"\nRegional Map Sample (32x32):")
    for y in range(min(20, generator.region_size)):  # Show first 20 rows
        line = ""
        for x in range(min(32, generator.region_size)):
            tile = regional_map[y][x]
            line += tile.char
        print(line)
    
    # Show some example tile details
    sample_tile = regional_map[16][16]  # Center tile
    print(f"\nSample tile at center (16,16):")
    print(f"  Parent biome: {sample_tile.parent_biome.value}")
    print(f"  Terrain subtype: {sample_tile.terrain_subtype.value}")
    print(f"  Micro elevation: {sample_tile.micro_elevation:.1f}m")
    print(f"  Fertility: {sample_tile.fertility:.2f}")
    print(f"  Accessibility: {sample_tile.accessibility:.2f}")
    print(f"  Has minor river: {sample_tile.has_minor_river}")
    print(f"  Landmark: {sample_tile.landmark.value if sample_tile.landmark else 'None'}")
    print(f"  Resource concentration: {sample_tile.resource_concentration.value if sample_tile.resource_concentration else 'None'}")
    print(f"  Terrain boundary: {sample_tile.terrain_boundary}")
    
    # Count interesting features
    landmarks = sum(1 for row in regional_map for tile in row if tile.landmark)
    resources = sum(1 for row in regional_map for tile in row if tile.resource_concentration)
    rivers = sum(1 for row in regional_map for tile in row if tile.has_minor_river)
    lakes = sum(1 for row in regional_map for tile in row if tile.is_lake)
    
    print(f"\nFeature Summary:")
    print(f"  Landmarks: {landmarks}")
    print(f"  Resource concentrations: {resources}")
    print(f"  River tiles: {rivers}")
    print(f"  Lake tiles: {lakes}")