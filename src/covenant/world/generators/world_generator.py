"""
World Scale Generator for the 3-tiered world generation system.

This module generates the top-level 128×96 world map with continental features,
plate tectonics, major biomes, climate zones, and river systems.
Based on examples/world_generator.py but integrated with the new architecture.
"""

import random
import math
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Dict, Set, Optional

from ..data.scale_types import ViewScale, CoordinateSystem, WorldCoordinate
from ..data.tilemap import BiomeType, get_tile


class PlateType(Enum):
    OCEANIC = "oceanic"
    CONTINENTAL = "continental"


class ClimateZone(Enum):
    POLAR = "polar"
    SUBPOLAR = "subpolar"
    TEMPERATE = "temperate"
    SUBTROPICAL = "subtropical"
    TROPICAL = "tropical"


@dataclass
class TectonicPlate:
    """Represents a tectonic plate"""
    id: int
    plate_type: PlateType
    center_x: float
    center_y: float
    velocity_x: float
    velocity_y: float
    size: float
    age: float  # Younger plates are more active


@dataclass
class WorldTile:
    """Complete data for one world tile (sector)"""
    # Coordinates
    x: int
    y: int
    
    # Geological
    plate_id: int
    base_elevation: float  # -4000m to +4000m
    final_elevation: float  # After all modifications
    is_land: bool
    
    # Hydrography
    has_major_river: bool
    river_id: Optional[int]
    drainage_direction: Optional[Tuple[int, int]]  # (dx, dy) for water flow
    water_accumulation: float  # How much water flows through here
    
    # Climate
    climate_zone: ClimateZone
    temperature: float  # 0.0 (cold) to 1.0 (hot)
    precipitation: float  # 0.0 (dry) to 1.0 (wet)
    seasonal_variation: float  # 0.0 (stable) to 1.0 (extreme seasons)
    
    # Biome
    biome: BiomeType
    
    # Display
    char: str
    fg_color: Tuple[int, int, int]
    bg_color: Tuple[int, int, int]


class HierarchicalNoise:
    """Multi-scale noise generator for world features"""
    
    def __init__(self, seed: int):
        random.seed(seed)
        self.seed = seed
        # Pre-generate permutation table for consistent noise
        self.perm = list(range(256))
        random.shuffle(self.perm)
        self.perm = self.perm + self.perm  # Duplicate for easier indexing
    
    def noise2d(self, x: float, y: float) -> float:
        """Basic 2D noise function"""
        # Simple noise - in production you'd use proper Perlin/Simplex
        return math.sin(x * 12.9898 + y * 78.233 + self.seed) * 0.5
    
    def octave_noise(self, x: float, y: float, octaves: int = 4, 
                     persistence: float = 0.5, lacunarity: float = 2.0) -> float:
        """Multi-octave noise for complex patterns"""
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
        """Ridge noise for mountain ridges"""
        value = self.octave_noise(x, y, octaves)
        return 1.0 - abs(value)


class WorldScaleGenerator:
    """Generates complete 128×96 world map with all major features"""
    
    def __init__(self, seed: int):
        self.seed = seed
        self.noise = HierarchicalNoise(seed)
        
        # World dimensions from coordinate system
        self.world_width = CoordinateSystem.WORLD_SIZE[0]  # 128
        self.world_height = CoordinateSystem.WORLD_SIZE[1]  # 96
        
        # Generation parameters
        self.num_plates = 12  # Major tectonic plates
        self.num_major_rivers = 15  # Major river systems
        
        # Scale factors for different noise layers
        self.continental_scale = 0.008  # Very large features
        self.tectonic_scale = 0.02     # Mountain ranges
        self.climate_scale = 0.015     # Climate variation
        self.local_scale = 0.05        # Fine details
        
        # Generated data
        self.plates: List[TectonicPlate] = []
        self.plate_boundaries: Set[Tuple[int, int]] = set()
        self.world_tiles: List[List[WorldTile]] = []
    
    def generate_complete_world(self) -> List[List[WorldTile]]:
        """Generate entire world map with all features"""
        print("Generating world-scale features...")
        
        # Phase 1: Tectonic Plates
        print("1. Generating tectonic plates...")
        self._generate_tectonic_plates()
        
        # Phase 2: Base elevation from plate tectonics
        print("2. Calculating base elevation...")
        self._calculate_base_elevation()
        
        # Phase 3: Apply mountain building and erosion
        print("3. Applying mountain building...")
        self._apply_mountain_building()
        
        # Phase 4: Determine land/sea boundaries
        print("4. Determining land/sea boundaries...")
        self._determine_land_sea()
        
        # Phase 5: Generate climate zones
        print("5. Generating climate zones...")
        self._generate_climate_zones()
        
        # Phase 6: River system generation
        print("6. Generating river systems...")
        self._generate_river_systems()
        
        # Phase 7: Final biome assignment
        print("7. Assigning biomes...")
        self._assign_biomes()
        
        # Phase 8: Visual representation
        print("8. Generating visual representation...")
        self._generate_display_chars()
        
        print("World generation complete!")
        return self.world_tiles
    
    def get_world_tile(self, world_x: int, world_y: int) -> Optional[WorldTile]:
        """Get world tile at specific coordinates"""
        if (0 <= world_x < self.world_width and 
            0 <= world_y < self.world_height and
            self.world_tiles):
            return self.world_tiles[world_y][world_x]
        return None
    
    def get_neighboring_world_tiles(self, world_x: int, world_y: int) -> Dict[str, WorldTile]:
        """Get neighboring world tiles for regional generation context"""
        neighbors = {}
        directions = {
            "north": (0, -1),
            "south": (0, 1),
            "east": (1, 0),
            "west": (-1, 0),
            "northeast": (1, -1),
            "northwest": (-1, -1),
            "southeast": (1, 1),
            "southwest": (-1, 1)
        }
        
        for direction, (dx, dy) in directions.items():
            nx, ny = world_x + dx, world_y + dy
            neighbor = self.get_world_tile(nx, ny)
            if neighbor:
                neighbors[direction] = neighbor
        
        return neighbors
    
    def _generate_tectonic_plates(self):
        """Create tectonic plates using Voronoi-like distribution"""
        self.plates = []
        
        # Generate plate centers with some randomness
        for i in range(self.num_plates):
            # Try to distribute plates somewhat evenly
            attempts = 0
            while attempts < 50:  # Avoid infinite loops
                center_x = random.uniform(10, self.world_width - 10)
                center_y = random.uniform(10, self.world_height - 10)
                
                # Check distance from existing plates
                too_close = False
                min_distance = 20  # Minimum distance between plate centers
                for existing_plate in self.plates:
                    dist = math.sqrt((center_x - existing_plate.center_x)**2 + 
                                   (center_y - existing_plate.center_y)**2)
                    if dist < min_distance:
                        too_close = True
                        break
                
                if not too_close:
                    break
                attempts += 1
            
            # Determine plate type (more oceanic plates)
            plate_type = PlateType.OCEANIC if random.random() < 0.7 else PlateType.CONTINENTAL
            
            # Random velocity for plate movement
            velocity_angle = random.uniform(0, 2 * math.pi)
            velocity_magnitude = random.uniform(0.5, 2.0)
            velocity_x = math.cos(velocity_angle) * velocity_magnitude
            velocity_y = math.sin(velocity_angle) * velocity_magnitude
            
            plate = TectonicPlate(
                id=i,
                plate_type=plate_type,
                center_x=center_x,
                center_y=center_y,
                velocity_x=velocity_x,
                velocity_y=velocity_y,
                size=random.uniform(0.8, 1.5),
                age=random.uniform(0.0, 1.0)
            )
            self.plates.append(plate)

        # Initialize world tiles with plate assignments
        self.world_tiles = []
        for y in range(self.world_height):
            row = []
            for x in range(self.world_width):
                # Find closest plate (Voronoi diagram)
                closest_plate_id = 0
                min_distance = float('inf')

                for plate in self.plates:
                    dist = math.sqrt((x - plate.center_x)**2 + (y - plate.center_y)**2)
                    if dist < min_distance:
                        min_distance = dist
                        closest_plate_id = plate.id

                # Create initial tile
                tile = WorldTile(
                    x=x, y=y,
                    plate_id=closest_plate_id,
                    base_elevation=0.0,
                    final_elevation=0.0,
                    is_land=False,
                    has_major_river=False,
                    river_id=None,
                    drainage_direction=None,
                    water_accumulation=0.0,
                    climate_zone=ClimateZone.TEMPERATE,
                    temperature=0.5,
                    precipitation=0.5,
                    seasonal_variation=0.3,
                    biome=BiomeType.DEEP_OCEAN,
                    char="~",
                    fg_color=(100, 150, 255),
                    bg_color=(0, 50, 150)
                )
                row.append(tile)
            self.world_tiles.append(row)

        # Identify plate boundaries
        self._identify_plate_boundaries()

    def _identify_plate_boundaries(self):
        """Find boundaries between tectonic plates"""
        self.plate_boundaries = set()

        for y in range(self.world_height):
            for x in range(self.world_width):
                current_plate = self.world_tiles[y][x].plate_id

                # Check adjacent tiles
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue

                        nx, ny = x + dx, y + dy
                        if (0 <= nx < self.world_width and
                            0 <= ny < self.world_height):

                            neighbor_plate = self.world_tiles[ny][nx].plate_id
                            if neighbor_plate != current_plate:
                                self.plate_boundaries.add((x, y))
                                break
                    if (x, y) in self.plate_boundaries:
                        break

    def _calculate_base_elevation(self):
        """Calculate base elevation using continental noise and plate types"""
        for y in range(self.world_height):
            for x in range(self.world_width):
                tile = self.world_tiles[y][x]
                plate = self.plates[tile.plate_id]

                # Continental-scale elevation noise
                continental_noise = self.noise.octave_noise(
                    x * self.continental_scale,
                    y * self.continental_scale,
                    octaves=3,
                    persistence=0.6
                )

                # Plate type influences base elevation
                if plate.plate_type == PlateType.CONTINENTAL:
                    # Continental plates: higher base elevation
                    base_elevation = (continental_noise * 1500) + 200  # -1300m to +1700m, bias toward land
                else:
                    # Oceanic plates: lower base elevation
                    base_elevation = (continental_noise * 2000) - 1000  # -3000m to +1000m, bias toward ocean

                # Distance from plate center affects elevation
                distance_to_center = math.sqrt(
                    (x - plate.center_x)**2 + (y - plate.center_y)**2
                )

                # Plates are generally higher at centers, lower at edges
                center_effect = max(0, 1.0 - (distance_to_center / 40)) * 300
                base_elevation += center_effect

                tile.base_elevation = base_elevation
                tile.final_elevation = base_elevation

    def _apply_mountain_building(self):
        """Add mountain ranges at plate boundaries and through tectonic processes"""

        # Mountain building at plate boundaries
        for boundary_x, boundary_y in self.plate_boundaries:
            tile = self.world_tiles[boundary_y][boundary_x]

            # Determine boundary type by comparing adjacent plates
            adjacent_plates = set()
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    nx, ny = boundary_x + dx, boundary_y + dy
                    if (0 <= nx < self.world_width and 0 <= ny < self.world_height):
                        adjacent_plates.add(self.world_tiles[ny][nx].plate_id)

            if len(adjacent_plates) >= 2:
                plate_list = list(adjacent_plates)
                plate1 = self.plates[plate_list[0]]
                plate2 = self.plates[plate_list[1]]

                # Continental-continental collision: high mountains
                if (plate1.plate_type == PlateType.CONTINENTAL and
                    plate2.plate_type == PlateType.CONTINENTAL):

                    mountain_height = random.uniform(1500, 4000)
                    tile.final_elevation += mountain_height

                    # Spread mountains to nearby tiles
                    self._spread_mountains(boundary_x, boundary_y, mountain_height * 0.7, radius=3)

                # Oceanic-continental: moderate mountains
                elif ((plate1.plate_type == PlateType.OCEANIC and plate2.plate_type == PlateType.CONTINENTAL) or
                      (plate1.plate_type == PlateType.CONTINENTAL and plate2.plate_type == PlateType.OCEANIC)):

                    mountain_height = random.uniform(800, 2500)
                    tile.final_elevation += mountain_height

                    # Spread mountains to nearby tiles
                    self._spread_mountains(boundary_x, boundary_y, mountain_height * 0.6, radius=2)

        # Add mountain ranges within plates using ridge noise
        for y in range(self.world_height):
            for x in range(self.world_width):
                tile = self.world_tiles[y][x]

                # Ridge noise for mountain ridges
                ridge_strength = self.noise.ridge_noise(
                    x * self.tectonic_scale,
                    y * self.tectonic_scale,
                    octaves=3
                )

                # Only create mountains where ridge noise is strong
                if ridge_strength > 0.7:
                    mountain_height = (ridge_strength - 0.7) * 2000 / 0.3  # 0 to 2000m
                    tile.final_elevation += mountain_height

    def _spread_mountains(self, center_x: int, center_y: int, base_height: float, radius: int):
        """Spread mountain elevation to nearby tiles"""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx == 0 and dy == 0:
                    continue

                nx, ny = center_x + dx, center_y + dy
                if 0 <= nx < self.world_width and 0 <= ny < self.world_height:
                    distance = math.sqrt(dx*dx + dy*dy)
                    if distance <= radius:
                        # Reduce height with distance
                        height_multiplier = max(0, 1.0 - (distance / radius))
                        additional_height = base_height * height_multiplier
                        self.world_tiles[ny][nx].final_elevation += additional_height

    def _determine_land_sea(self):
        """Determine which tiles are land vs. sea"""
        sea_level = 0.0  # Elevation threshold for sea level

        for y in range(self.world_height):
            for x in range(self.world_width):
                tile = self.world_tiles[y][x]
                tile.is_land = tile.final_elevation > sea_level

    def _generate_climate_zones(self):
        """Generate climate zones based on latitude, elevation, and continental position"""

        for y in range(self.world_height):
            for x in range(self.world_width):
                tile = self.world_tiles[y][x]

                # Latitude factor (0 = equator, 1 = pole)
                latitude_factor = abs(y - self.world_height // 2) / (self.world_height // 2)

                # Continental position (distance from ocean)
                continentality = self._calculate_continentality(x, y)

                # Base temperature from latitude
                base_temp = 1.0 - latitude_factor  # Hot at equator, cold at poles

                # Elevation cooling (temperature decreases with altitude)
                if tile.is_land and tile.final_elevation > 0:
                    elevation_cooling = min(0.4, tile.final_elevation / 5000)  # Up to 0.4 reduction
                    base_temp -= elevation_cooling

                # Continental effect (more extreme temperatures inland)
                seasonal_variation = 0.2 + (continentality * 0.5)

                # Climate noise for variation
                temp_noise = self.noise.octave_noise(
                    x * self.climate_scale,
                    y * self.climate_scale,
                    octaves=2
                ) * 0.15

                final_temp = max(0.0, min(1.0, base_temp + temp_noise))

                # Precipitation calculation
                # Generally wetter near oceans, drier inland
                base_precipitation = 0.7 - (continentality * 0.4)

                # Orographic effect: mountains create rain shadows
                orographic_effect = self._calculate_orographic_effect(x, y)

                # Latitude effect on precipitation (more rain in tropics and temperate zones)
                latitude_precip_factor = 1.0 - abs(latitude_factor - 0.4) * 2
                latitude_precip_factor = max(0.3, latitude_precip_factor)

                precip_noise = self.noise.octave_noise(
                    x * self.climate_scale * 1.3,
                    y * self.climate_scale * 1.3,
                    octaves=2
                ) * 0.2

                final_precipitation = base_precipitation + orographic_effect + precip_noise
                final_precipitation *= latitude_precip_factor
                final_precipitation = max(0.0, min(1.0, final_precipitation))

                # Assign climate zone
                if latitude_factor > 0.8:
                    climate_zone = ClimateZone.POLAR
                elif latitude_factor > 0.6:
                    climate_zone = ClimateZone.SUBPOLAR
                elif latitude_factor > 0.35:
                    climate_zone = ClimateZone.TEMPERATE
                elif latitude_factor > 0.15:
                    climate_zone = ClimateZone.SUBTROPICAL
                else:
                    climate_zone = ClimateZone.TROPICAL

                # Update tile
                tile.climate_zone = climate_zone
                tile.temperature = final_temp
                tile.precipitation = final_precipitation
                tile.seasonal_variation = seasonal_variation

    def _calculate_continentality(self, x: int, y: int) -> float:
        """Calculate how far inland a point is (0 = coast, 1 = deep inland)"""
        min_ocean_distance = float('inf')

        # Sample in a radius around the point
        sample_radius = 15
        for dy in range(-sample_radius, sample_radius + 1, 2):  # Sample every 2 tiles
            for dx in range(-sample_radius, sample_radius + 1, 2):
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.world_width and 0 <= ny < self.world_height:
                    if not self.world_tiles[ny][nx].is_land:  # Found ocean
                        distance = math.sqrt(dx*dx + dy*dy)
                        min_ocean_distance = min(min_ocean_distance, distance)

        if min_ocean_distance == float('inf'):
            return 1.0  # Very inland

        # Normalize: 0-10 tiles = coastal, 10+ = increasingly inland
        continentality = min(1.0, min_ocean_distance / 20)
        return continentality

    def _calculate_orographic_effect(self, x: int, y: int) -> float:
        """Calculate orographic (mountain) effect on precipitation"""
        if not self.world_tiles[y][x].is_land:
            return 0.0

        tile_elevation = self.world_tiles[y][x].final_elevation

        # Check elevation gradient in prevailing wind direction (assume westerly winds)
        orographic_effect = 0.0

        # Look westward for elevation changes
        for dx in range(-5, 0):  # Check 5 tiles to the west
            nx = x + dx
            if 0 <= nx < self.world_width:
                neighbor_elevation = self.world_tiles[y][nx].final_elevation
                elevation_diff = tile_elevation - neighbor_elevation

                if elevation_diff > 500:  # Significant elevation gain
                    # Windward side gets more precipitation
                    orographic_effect += 0.1
                elif elevation_diff < -300:  # Rain shadow
                    orographic_effect -= 0.15

        return max(-0.3, min(0.3, orographic_effect))

    def _generate_river_systems(self):
        """Generate major river systems using flow accumulation"""
        # Simplified river generation for now
        # In a full implementation, this would use proper flow accumulation algorithms
        river_count = 0

        for y in range(self.world_height):
            for x in range(self.world_width):
                tile = self.world_tiles[y][x]

                # Simple river placement based on elevation and precipitation
                if (tile.is_land and
                    tile.final_elevation > 500 and  # High enough for river source
                    tile.precipitation > 0.6 and   # Wet enough
                    random.random() < 0.02 and     # Random chance
                    river_count < self.num_major_rivers):

                    tile.has_major_river = True
                    tile.river_id = river_count
                    river_count += 1

    def _assign_biomes(self):
        """Assign biomes based on climate, elevation, and other factors"""

        for y in range(self.world_height):
            for x in range(self.world_width):
                tile = self.world_tiles[y][x]

                if not tile.is_land:
                    # Ocean biomes based on depth and latitude
                    if tile.final_elevation < -2000:
                        tile.biome = BiomeType.DEEP_OCEAN
                    elif tile.final_elevation < -200:
                        tile.biome = BiomeType.SHALLOW_SEA
                    else:
                        tile.biome = BiomeType.COASTAL_WATERS

                else:
                    # Land biomes
                    temp = tile.temperature
                    precip = tile.precipitation
                    elevation = tile.final_elevation

                    # High mountains override other factors
                    if elevation > 3000:
                        tile.biome = BiomeType.HIGH_MOUNTAINS
                    elif elevation > 1500:
                        if temp < 0.3:
                            tile.biome = BiomeType.HIGH_MOUNTAINS  # Cold mountain
                        elif precip > 0.6:
                            tile.biome = BiomeType.MOUNTAIN_FOREST
                        else:
                            tile.biome = BiomeType.MOUNTAIN_DESERT

                    # Rivers and wetlands
                    elif tile.has_major_river and precip > 0.5:
                        tile.biome = BiomeType.WETLAND

                    # Temperature-precipitation matrix for other biomes
                    elif temp < 0.2:  # Very cold
                        if elevation > 0:
                            tile.biome = BiomeType.POLAR_ICE
                        else:
                            tile.biome = BiomeType.TUNDRA

                    elif temp < 0.4:  # Cold
                        if precip > 0.4:
                            tile.biome = BiomeType.TAIGA
                        else:
                            tile.biome = BiomeType.TUNDRA

                    elif temp < 0.7:  # Temperate
                        if precip > 0.6:
                            tile.biome = BiomeType.TEMPERATE_FOREST
                        elif precip > 0.3:
                            tile.biome = BiomeType.GRASSLAND
                        else:
                            tile.biome = BiomeType.DESERT

                    else:  # Hot
                        if precip > 0.7:
                            tile.biome = BiomeType.TROPICAL_FOREST
                        elif precip > 0.4:
                            tile.biome = BiomeType.SAVANNA
                        else:
                            tile.biome = BiomeType.DESERT

    def _generate_display_chars(self):
        """Generate display characters and colors for each tile"""
        for y in range(self.world_height):
            for x in range(self.world_width):
                tile = self.world_tiles[y][x]

                # Get tile configuration from tilemap
                tile_config = get_tile(ViewScale.WORLD, tile.biome, use_variant=True)

                tile.char = tile_config.char
                tile.fg_color = tile_config.fg_color
                tile.bg_color = tile_config.bg_color

    def print_world_stats(self):
        """Print statistics about the generated world"""
        total_tiles = self.world_width * self.world_height
        land_tiles = sum(1 for row in self.world_tiles for tile in row if tile.is_land)
        river_tiles = sum(1 for row in self.world_tiles for tile in row if tile.has_major_river)

        print(f"\nWorld Statistics:")
        print(f"Total tiles: {total_tiles}")
        print(f"Land tiles: {land_tiles} ({land_tiles/total_tiles*100:.1f}%)")
        print(f"Ocean tiles: {total_tiles-land_tiles} ({(total_tiles-land_tiles)/total_tiles*100:.1f}%)")
        print(f"Major river tiles: {river_tiles}")
        print(f"Tectonic plates: {len(self.plates)}")

        # Biome breakdown
        biome_counts = {}
        for row in self.world_tiles:
            for tile in row:
                biome = tile.biome
                biome_counts[biome] = biome_counts.get(biome, 0) + 1

        print(f"\nBiome Distribution:")
        for biome, count in sorted(biome_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = count / total_tiles * 100
            print(f"  {biome.value}: {count} ({percentage:.1f}%)")
