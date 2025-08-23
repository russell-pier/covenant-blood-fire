"""
Organic world generation system for natural-looking terrain.

This module provides an enhanced world generation system that creates
more organic, natural-looking terrain with character variations,
smooth biome transitions, and realistic water features.
"""

import math
import random
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple, Optional

from .terrain import TerrainType


@dataclass
class OrganicTerrainData:
    """Enhanced terrain data with organic features."""

    terrain_type: TerrainType
    character: str
    foreground_color: Tuple[int, int, int]
    background_color: Tuple[int, int, int]
    elevation: float      # In meters
    moisture: float       # 0.0 to 1.0
    temperature: float    # In Celsius


# Character variations for each terrain type to create organic appearance
TERRAIN_CHARACTER_VARIATIONS = {
    TerrainType.GRASS: {
        'chars': [".", "·", ",", "'", "`"],
        'base_fg': (50, 100, 50),
        'base_bg': (20, 60, 20)
    },
    TerrainType.LIGHT_GRASS: {
        'chars': [".", "·", ",", "'", "`"],
        'base_fg': (60, 120, 60),
        'base_bg': (30, 80, 30)
    },
    TerrainType.DARK_GRASS: {
        'chars': [".", "·", ",", "'", "`"],
        'base_fg': (40, 80, 40),
        'base_bg': (15, 50, 15)
    },
    TerrainType.FOREST: {
        'chars': ["♠", "♣", "T", "Y", "†"],
        'base_fg': (0, 80, 0),
        'base_bg': (10, 40, 10)
    },
    TerrainType.HILLS: {
        'chars': ["^", "▲", "∩", "⩙", "⌂"],
        'base_fg': (139, 69, 19),
        'base_bg': (101, 67, 33)
    },
    TerrainType.MOUNTAINS: {
        'chars': ["▲", "^", "⩙", "∩", "⌂"],
        'base_fg': (100, 100, 100),
        'base_bg': (60, 60, 60)
    },
    TerrainType.DEEP_WATER: {
        'chars': ["~", "≈", "∼", "◦", "∙"],
        'base_fg': (100, 150, 255),
        'base_bg': (0, 50, 150)
    },
    TerrainType.SHALLOW_WATER: {
        'chars': ["~", "≈", "∼", "◦", "∙"],
        'base_fg': (120, 170, 255),
        'base_bg': (20, 70, 170)
    },
    TerrainType.SAND: {
        'chars': ["·", "∘", "°", ".", "∙"],
        'base_fg': (218, 165, 32),
        'base_bg': (184, 134, 11)
    },
    TerrainType.DESERT: {
        'chars': ["·", "∘", "°", ".", "∙"],
        'base_fg': (238, 185, 52),
        'base_bg': (204, 154, 31)
    },
    TerrainType.FERTILE: {
        'chars': ['"', "≡", "'", ",", "·"],
        'base_fg': (50, 200, 50),
        'base_bg': (30, 120, 30)
    },
    TerrainType.CAVES: {
        'chars': ["▓", "░", "▒", "■", "□"],
        'base_fg': (80, 80, 80),
        'base_bg': (30, 30, 30)
    },
    TerrainType.SWAMP: {
        'chars': ["≋", "%", "~", "∼", "◦"],
        'base_fg': (60, 100, 40),
        'base_bg': (40, 60, 20)
    }
}


class OrganicNoiseGenerator:
    """Enhanced noise generator for organic terrain features."""
    
    def __init__(self, seed: int):
        """Initialize the noise generator with a seed."""
        random.seed(seed)
        self.permutation = list(range(256))
        random.shuffle(self.permutation)
        self.permutation *= 2
    
    def fade(self, t: float) -> float:
        """Fade function for smooth interpolation."""
        return t * t * t * (t * (t * 6 - 15) + 10)
    
    def lerp(self, t: float, a: float, b: float) -> float:
        """Linear interpolation."""
        return a + t * (b - a)
    
    def grad(self, hash_val: int, x: float, y: float) -> float:
        """Gradient function for noise generation."""
        h = hash_val & 15
        u = x if h < 8 else y
        v = y if h < 4 else (x if h == 12 or h == 14 else 0)
        return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v)
    
    def noise(self, x: float, y: float) -> float:
        """Generate 2D Perlin noise."""
        import math

        # Handle negative coordinates correctly
        X = int(math.floor(x)) & 255
        Y = int(math.floor(y)) & 255

        x -= math.floor(x)
        y -= math.floor(y)
        
        u = self.fade(x)
        v = self.fade(y)
        
        A = self.permutation[X] + Y
        B = self.permutation[X + 1] + Y
        
        return self.lerp(v,
            self.lerp(u, self.grad(self.permutation[A], x, y),
                        self.grad(self.permutation[B], x - 1, y)),
            self.lerp(u, self.grad(self.permutation[A + 1], x, y - 1),
                        self.grad(self.permutation[B + 1], x - 1, y - 1)))
    
    def octave_noise(self, x: float, y: float, octaves: int = 4, 
                     persistence: float = 0.5, lacunarity: float = 2.0) -> float:
        """Generate multi-octave noise for more natural patterns."""
        value = 0.0
        amplitude = 1.0
        frequency = 1.0
        max_value = 0.0
        
        for _ in range(octaves):
            value += self.noise(x * frequency, y * frequency) * amplitude
            max_value += amplitude
            amplitude *= persistence
            frequency *= lacunarity
        
        return value / max_value


class OrganicWorldGenerator:
    """Enhanced world generator for organic, natural-looking terrain."""
    
    def __init__(self, seed: Optional[int]):
        """Initialize the organic world generator."""
        self.seed = seed if seed is not None else 12345
        
        # Create multiple noise generators for different features
        self.noise_elevation = OrganicNoiseGenerator(self.seed)
        self.noise_moisture = OrganicNoiseGenerator(self.seed + 1000)
        self.noise_temperature = OrganicNoiseGenerator(self.seed + 2000)
        self.noise_detail = OrganicNoiseGenerator(self.seed + 3000)
        self.noise_water = OrganicNoiseGenerator(self.seed + 4000)
        self.noise_transition = OrganicNoiseGenerator(self.seed + 5000)
        
        # Enhanced scales for realistic 1m² coordinate system
        # Much smaller scales for gradual elevation changes (10-50cm per meter)
        self.continent_scale = 0.0001  # Very gradual continental features
        self.biome_scale = 0.0005      # Large biome features
        self.regional_scale = 0.002    # Regional variations within biomes
        self.local_scale = 0.01        # Fine texture details
        self.water_scale = 0.003       # Water body scale
        self.transition_scale = 0.005  # Biome transition smoothing
        self.river_scale = 0.0002      # River network scale
    
    def generate_chunk_data(self, chunk_x: int, chunk_y: int, chunk_size: int) -> Dict[Tuple[int, int], OrganicTerrainData]:
        """Generate organic terrain data for a chunk with large-scale features."""
        chunk_data = {}

        # Convert chunk coordinates to world coordinates
        world_offset_x = chunk_x * chunk_size
        world_offset_y = chunk_y * chunk_size

        # Generate large-scale biome map first
        biome_map = self._generate_large_scale_biome_map(world_offset_x, world_offset_y, chunk_size)

        # Generate environmental maps
        elevation_map = self._generate_elevation_map(world_offset_x, world_offset_y, chunk_size)
        moisture_map = self._generate_moisture_map(world_offset_x, world_offset_y, chunk_size)
        temperature_map = self._generate_temperature_map(world_offset_x, world_offset_y, chunk_size)

        # Apply water body modifications
        elevation_map, water_mask = self._generate_water_bodies(elevation_map, world_offset_x, world_offset_y, chunk_size)
        moisture_map = self._modify_moisture_by_water(moisture_map, water_mask, chunk_size)

        # Generate river system (independent of terrain)
        river_map = self._generate_river_system(world_offset_x, world_offset_y, chunk_size)

        # Generate terrain for each position
        for local_y in range(chunk_size):
            for local_x in range(chunk_size):
                world_x = world_offset_x + local_x
                world_y = world_offset_y + local_y

                elevation = elevation_map[local_y][local_x]
                moisture = moisture_map[local_y][local_x]
                temperature = temperature_map[local_y][local_x]
                biome_influence = biome_map[local_y][local_x]
                is_river = river_map[local_y][local_x]

                # Rivers override terrain (elevation now in meters)
                if is_river:
                    terrain_type = TerrainType.SHALLOW_WATER if elevation > 100 else TerrainType.DEEP_WATER
                else:
                    # Determine terrain type with large-scale biome influence and transitions
                    terrain_type = self._determine_terrain_with_large_scale_transitions(
                        elevation, moisture, temperature, biome_influence, world_x, world_y
                    )

                # Apply organic texture variations
                terrain_data = self._apply_organic_variations(
                    terrain_type, world_x, world_y, elevation, moisture, temperature
                )

                chunk_data[(local_x, local_y)] = terrain_data

        return chunk_data

    def _generate_large_scale_biome_map(self, world_x: int, world_y: int, size: int) -> List[List[Dict]]:
        """Generate large-scale biome influences that span multiple chunks."""
        biome_map = []

        for y in range(size):
            row = []
            for x in range(size):
                world_pos_x = (world_x + x) * self.biome_scale
                world_pos_y = (world_y + y) * self.biome_scale

                # Generate large-scale temperature and moisture patterns
                large_temp = self.noise_temperature.octave_noise(
                    world_pos_x, world_pos_y,
                    octaves=2,
                    persistence=0.6,
                    lacunarity=2.0
                )

                large_moisture = self.noise_moisture.octave_noise(
                    world_pos_x, world_pos_y,
                    octaves=2,
                    persistence=0.6,
                    lacunarity=2.0
                )

                # Normalize to 0-1 range
                large_temp = (large_temp + 1) / 2
                large_moisture = (large_moisture + 1) / 2

                # Determine primary biome based on large-scale patterns
                primary_biome = self._determine_primary_biome(large_temp, large_moisture)

                # Calculate biome transition influences
                biome_influences = self._calculate_biome_transitions(
                    world_pos_x, world_pos_y, primary_biome, large_temp, large_moisture
                )

                row.append(biome_influences)
            biome_map.append(row)

        return biome_map

    def _determine_primary_biome(self, temperature: float, moisture: float) -> TerrainType:
        """Determine the primary biome based on temperature and moisture."""
        # Logical biome progression based on climate
        if temperature > 0.8:  # Very hot
            if moisture < 0.2:
                return TerrainType.DESERT
            elif moisture < 0.5:
                return TerrainType.SAND
            else:
                return TerrainType.SWAMP  # Hot and wet
        elif temperature > 0.6:  # Hot
            if moisture < 0.3:
                return TerrainType.DESERT
            elif moisture < 0.6:
                return TerrainType.LIGHT_GRASS
            else:
                return TerrainType.FERTILE
        elif temperature > 0.4:  # Moderate
            if moisture < 0.4:
                return TerrainType.GRASS
            elif moisture < 0.7:
                return TerrainType.FERTILE
            else:
                return TerrainType.FOREST
        else:  # Cold
            if moisture < 0.5:
                return TerrainType.DARK_GRASS
            else:
                return TerrainType.FOREST

    def _calculate_biome_transitions(self, world_x: float, world_y: float,
                                   primary_biome: TerrainType, temp: float, moisture: float) -> Dict:
        """Calculate transition influences from neighboring biomes."""
        # Sample neighboring areas to determine transition influences
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                neighbor_x = world_x + dx * 0.5  # Sample nearby points
                neighbor_y = world_y + dy * 0.5

                # Get neighbor climate
                neighbor_temp = (self.noise_temperature.octave_noise(
                    neighbor_x, neighbor_y, octaves=2, persistence=0.6
                ) + 1) / 2

                neighbor_moisture = (self.noise_moisture.octave_noise(
                    neighbor_x, neighbor_y, octaves=2, persistence=0.6
                ) + 1) / 2

                neighbor_biome = self._determine_primary_biome(neighbor_temp, neighbor_moisture)
                neighbors.append(neighbor_biome)

        # Calculate transition weights
        biome_weights = {primary_biome: 0.7}  # Primary biome has strongest influence

        for neighbor in neighbors:
            if neighbor != primary_biome:
                if neighbor not in biome_weights:
                    biome_weights[neighbor] = 0.0
                biome_weights[neighbor] += 0.3 / len(neighbors)

        return {
            'primary': primary_biome,
            'weights': biome_weights,
            'temp': temp,
            'moisture': moisture
        }

    def _generate_river_system(self, world_x: int, world_y: int, size: int) -> List[List[bool]]:
        """Generate river system independent of terrain."""
        river_map = [[False for _ in range(size)] for _ in range(size)]

        for y in range(size):
            for x in range(size):
                world_pos_x = (world_x + x) * self.river_scale
                world_pos_y = (world_y + y) * self.river_scale

                # Generate river network using multiple noise layers
                river_noise1 = self.noise_water.octave_noise(
                    world_pos_x, world_pos_y,
                    octaves=1,
                    persistence=0.5,
                    lacunarity=2.0
                )

                river_noise2 = self.noise_water.octave_noise(
                    world_pos_x * 3, world_pos_y * 3,
                    octaves=1,
                    persistence=0.5,
                    lacunarity=2.0
                )

                # Create river channels with variable width
                # Rivers form where noise values create narrow channels
                river_channel1 = abs(river_noise1) < 0.05  # First channel direction
                river_channel2 = abs(river_noise2) < 0.05  # Second channel direction

                # Rivers only exist where channels intersect (much rarer)
                if river_channel1 and river_channel2:
                    # Additional rarity check - only 1% of intersections become rivers
                    rarity_noise = self.noise_detail.noise(world_pos_x * 5, world_pos_y * 5)
                    if abs(rarity_noise) < 0.1:  # Very rare
                        river_map[y][x] = True

        return river_map

    def _generate_elevation_map(self, world_x: int, world_y: int, size: int) -> List[List[float]]:
        """Generate elevation in meters using multi-octave noise."""
        elevation_map = []

        for y in range(size):
            row = []
            for x in range(size):
                world_pos_x = (world_x + x) * self.continent_scale
                world_pos_y = (world_y + y) * self.continent_scale

                elevation = self.noise_elevation.octave_noise(
                    world_pos_x, world_pos_y,
                    octaves=5,
                    persistence=0.6,
                    lacunarity=2.0
                )

                # Convert from [-1, 1] to [0, 1]
                normalized = (elevation + 1) / 2
                normalized = max(0.0, min(1.0, normalized))

                # Convert to meters with distribution favoring more mountains
                if normalized < 0.25:
                    # Lower 25%: underwater and caves (-200 to 0m)
                    curved = math.pow(normalized / 0.25, 1.5) * 0.25
                    elevation_meters = -200 + curved * 200
                elif normalized < 0.5:
                    # Next 25%: low land (0 to 600m)
                    curved = (normalized - 0.25) / 0.25
                    elevation_meters = curved * 600
                else:
                    # Upper 50%: hills and mountains (600 to 3000m) - more mountains!
                    curved = math.pow((normalized - 0.5) / 0.5, 0.6)
                    elevation_meters = 600 + curved * 2400

                elevation_meters = max(-200, min(3000, elevation_meters))
                row.append(elevation_meters)
            elevation_map.append(row)

        return elevation_map
    
    def _generate_moisture_map(self, world_x: int, world_y: int, size: int) -> List[List[float]]:
        """Generate moisture patterns."""
        moisture_map = []
        
        for y in range(size):
            row = []
            for x in range(size):
                world_pos_x = (world_x + x) * self.regional_scale
                world_pos_y = (world_y + y) * self.regional_scale
                
                moisture = self.noise_moisture.octave_noise(
                    world_pos_x, world_pos_y,
                    octaves=3,
                    persistence=0.5,
                    lacunarity=2.0
                )
                
                moisture = (moisture + 1) / 2
                row.append(max(0, min(1, moisture)))
            moisture_map.append(row)
        
        return moisture_map
    
    def _generate_temperature_map(self, world_x: int, world_y: int, size: int) -> List[List[float]]:
        """Generate temperature in Celsius with latitude influence."""
        temperature_map = []

        for y in range(size):
            row = []
            for x in range(size):
                world_pos_x = (world_x + x) * self.regional_scale
                world_pos_y = (world_y + y) * self.regional_scale

                # Base temperature from noise (-20°C to 40°C range)
                temp_noise = self.noise_temperature.octave_noise(
                    world_pos_x, world_pos_y,
                    octaves=3,
                    persistence=0.4,
                    lacunarity=2.0
                )
                base_temperature = 10 + (temp_noise * 20)  # -10°C to 30°C base

                # Latitude-based cooling (distance from equator)
                latitude_distance = abs(((world_y + y) * 0.0005) % 2.0 - 1.0)
                latitude_cooling = latitude_distance * 25  # Up to 25°C cooling

                temperature = base_temperature - latitude_cooling
                temperature = max(-20, min(40, temperature))
                row.append(temperature)
            temperature_map.append(row)

        return temperature_map

    def _generate_water_bodies(self, elevation_map: List[List[float]], world_x: int, world_y: int, size: int) -> Tuple[List[List[float]], List[List[bool]]]:
        """Create natural water bodies and lakes."""
        water_mask = [[False for _ in range(size)] for _ in range(size)]

        for y in range(size):
            for x in range(size):
                world_pos_x = (world_x + x) * self.water_scale
                world_pos_y = (world_y + y) * self.water_scale

                # Use water-specific noise for natural boundaries
                water_noise = self.noise_water.octave_noise(
                    world_pos_x, world_pos_y,
                    octaves=3,
                    persistence=0.6,
                    lacunarity=2.0
                )

                # Dynamic water threshold based on elevation and noise (now in meters)
                base_elevation = elevation_map[y][x]
                water_threshold = 20 + water_noise * 30  # 20m to 50m threshold

                if base_elevation < water_threshold:
                    elevation_map[y][x] = 0  # Sea level
                    water_mask[y][x] = True

        return elevation_map, water_mask

    def _modify_moisture_by_water(self, moisture_map: List[List[float]], water_mask: List[List[bool]], size: int) -> List[List[float]]:
        """Increase moisture near water bodies."""
        for y in range(size):
            for x in range(size):
                if water_mask[y][x]:
                    moisture_map[y][x] = 1.0
                else:
                    # Increase moisture near water
                    water_proximity = self._calculate_water_proximity(water_mask, x, y, size, radius=4)
                    moisture_map[y][x] = min(1.0, moisture_map[y][x] + water_proximity * 0.4)

        return moisture_map

    def _calculate_water_proximity(self, water_mask: List[List[bool]], x: int, y: int, size: int, radius: int = 4) -> float:
        """Calculate proximity to water bodies."""
        water_count = 0.0
        total_count = 0

        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < size and 0 <= ny < size:
                    total_count += 1
                    if water_mask[ny][nx]:
                        # Closer water has more influence
                        distance = max(1, math.sqrt(dx*dx + dy*dy))
                        water_count += 1.0 / distance

        return min(1.0, water_count / total_count) if total_count > 0 else 0.0

    def _determine_terrain_with_large_scale_transitions(self, elevation: float, moisture: float, temperature: float,
                                                       biome_influence: Dict, world_x: int, world_y: int) -> TerrainType:
        """Determine terrain type with large-scale biome influence and smooth transitions."""

        # Handle elevation-based overrides first (elevation now in meters)
        if elevation < -50:
            return TerrainType.CAVES

        if -50 <= elevation <= 50:
            if elevation < 0:
                return TerrainType.DEEP_WATER
            else:
                return TerrainType.SHALLOW_WATER

        if elevation > 630:   # Mountains start at ~630m (top 10% of elevations)
            return TerrainType.MOUNTAINS
        elif elevation > 580:  # Hills start at ~580m
            return TerrainType.HILLS

        # Use biome influence for terrain selection with transitions
        primary_biome = biome_influence['primary']
        biome_weights = biome_influence['weights']

        # Add fine-scale transition noise for organic boundaries
        transition_noise = self.noise_transition.noise(
            world_x * self.transition_scale,
            world_y * self.transition_scale
        ) * 0.15

        # Calculate weighted terrain selection based on biome influences
        terrain_candidates = []

        for biome, weight in biome_weights.items():
            # Adjust weight based on local environmental conditions
            local_suitability = self._calculate_terrain_suitability(
                biome, elevation, moisture, temperature, transition_noise
            )

            adjusted_weight = weight * local_suitability
            terrain_candidates.append((biome, adjusted_weight))

        # Select terrain based on weighted probabilities
        # Use transition noise to create organic boundaries
        noise_offset = (transition_noise + 1) / 2  # 0 to 1

        # Sort by weight and select based on noise
        terrain_candidates.sort(key=lambda x: x[1], reverse=True)

        # Primary terrain gets 70% chance, secondary gets 30%
        if len(terrain_candidates) >= 2:
            primary_terrain, primary_weight = terrain_candidates[0]
            secondary_terrain, secondary_weight = terrain_candidates[1]

            # Use noise to blend between primary and secondary
            if noise_offset < 0.7:
                return primary_terrain
            else:
                return secondary_terrain
        else:
            return terrain_candidates[0][0] if terrain_candidates else TerrainType.GRASS

    def _calculate_terrain_suitability(self, terrain_type: TerrainType, elevation: float,
                                     moisture: float, temperature: float, noise: float) -> float:
        """Calculate how suitable local conditions are for a terrain type."""
        suitability = 1.0

        # Terrain-specific suitability rules
        if terrain_type == TerrainType.DESERT:
            # Deserts prefer hot, dry conditions
            temp_suitability = max(0.1, temperature - 0.4)  # Better at high temp
            moisture_suitability = max(0.1, 0.4 - moisture)  # Better at low moisture
            suitability = temp_suitability * moisture_suitability * 2

        elif terrain_type == TerrainType.FOREST:
            # Forests prefer moderate temp, high moisture
            temp_suitability = 1.0 - abs(temperature - 0.5)  # Best at moderate temp
            moisture_suitability = max(0.1, moisture - 0.3)  # Better at high moisture
            suitability = temp_suitability * moisture_suitability * 2

        elif terrain_type == TerrainType.FERTILE:
            # Fertile land prefers good conditions
            temp_suitability = 1.0 - abs(temperature - 0.6)  # Best at warm temp
            moisture_suitability = max(0.1, moisture - 0.4)  # Better at good moisture
            elevation_suitability = 1.0 if 0.3 < elevation < 0.6 else 0.5
            suitability = temp_suitability * moisture_suitability * elevation_suitability * 2

        elif terrain_type == TerrainType.SWAMP:
            # Swamps prefer low elevation, high moisture
            elevation_suitability = max(0.1, 0.5 - elevation)  # Better at low elevation
            moisture_suitability = max(0.1, moisture - 0.6)  # Better at high moisture
            suitability = elevation_suitability * moisture_suitability * 3

        elif terrain_type in [TerrainType.LIGHT_GRASS, TerrainType.GRASS, TerrainType.DARK_GRASS]:
            # Grasslands are adaptable but have preferences
            if terrain_type == TerrainType.LIGHT_GRASS:
                suitability = max(0.3, temperature - 0.3)  # Warmer grass
            elif terrain_type == TerrainType.DARK_GRASS:
                suitability = max(0.3, 0.7 - temperature)  # Cooler grass
            else:
                suitability = 0.8  # Regular grass is adaptable

        # Add some randomness for organic variation
        suitability *= (1.0 + noise * 0.3)

        return max(0.1, min(2.0, suitability))

    def _apply_organic_variations(self, terrain_type: TerrainType, world_x: int, world_y: int,
                                  elevation: float, moisture: float, temperature: float) -> OrganicTerrainData:
        """Apply organic texture variations and environmental color shifts."""

        terrain_config = TERRAIN_CHARACTER_VARIATIONS[terrain_type]

        # Select character variant based on world position
        char_noise = self.noise_detail.noise(world_x * 0.3, world_y * 0.3)
        char_index = int((char_noise + 1) * 0.5 * len(terrain_config['chars'])) % len(terrain_config['chars'])
        selected_char = terrain_config['chars'][char_index]

        # Base colors
        base_fg = list(terrain_config['base_fg'])
        base_bg = list(terrain_config['base_bg'])

        # Environmental color variations
        color_noise = self.noise_detail.noise(world_x * self.local_scale, world_y * self.local_scale)
        color_variation = int(color_noise * 25)  # ±25 color variation

        # Elevation affects brightness
        elevation_brightness = int((elevation - 0.5) * 30)

        # Moisture affects saturation (greener when wet)
        moisture_effect = int((moisture - 0.5) * 20)

        # Apply variations
        fg_color = []
        bg_color = []

        for i, (fg_val, bg_val) in enumerate(zip(base_fg, base_bg)):
            # Combine all effects
            fg_final = fg_val + color_variation + elevation_brightness
            bg_final = bg_val + color_variation // 2 + elevation_brightness // 2

            # Green channel gets moisture boost for vegetation
            if i == 1 and terrain_type in [TerrainType.GRASS, TerrainType.LIGHT_GRASS, TerrainType.DARK_GRASS, TerrainType.FOREST, TerrainType.FERTILE]:
                fg_final += moisture_effect
                bg_final += moisture_effect // 2

            # Clamp values
            fg_color.append(max(0, min(255, fg_final)))
            bg_color.append(max(0, min(255, bg_final)))

        return OrganicTerrainData(
            terrain_type=terrain_type,
            character=selected_char,
            foreground_color=tuple(fg_color),
            background_color=tuple(bg_color),
            elevation=elevation,
            moisture=moisture,
            temperature=temperature
        )


def create_organic_world_generator(seed: Optional[int] = None) -> OrganicWorldGenerator:
    """Create an organic world generator with the specified seed."""
    if seed is None:
        seed = 12345
    return OrganicWorldGenerator(seed)
