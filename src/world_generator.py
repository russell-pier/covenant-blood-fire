"""
World scale generator for the three-tier world generation system.

This module generates continental-scale terrain features including
ocean/land distribution, mountain ranges, climate zones, and tectonic plates.
"""

import random
from typing import Dict, List, Tuple

try:
    from .world_types import (
        TerrainType, ClimateZone, WorldCoordinate, ColorRGB, Seed,
        WORLD_SECTORS_X, WORLD_SECTORS_Y
    )
    from .world_data import WorldSectorData, WorldMapData
    from .noise import HierarchicalNoiseGenerator
except ImportError:
    from world_types import (
        TerrainType, ClimateZone, WorldCoordinate, ColorRGB, Seed,
        WORLD_SECTORS_X, WORLD_SECTORS_Y
    )
    from world_data import WorldSectorData, WorldMapData
    from noise import HierarchicalNoiseGenerator


class WorldScaleGenerator:
    """
    Generator for world-scale terrain features.
    
    Creates continental landmasses, ocean distribution, climate zones,
    and tectonic plate assignments using hierarchical noise generation.
    
    Attributes:
        seed: Master seed for world generation
        noise_gen: Hierarchical noise generator
        random: Random number generator for discrete choices
        tectonic_plates: Number of tectonic plates
    """
    
    def __init__(self, seed: Seed, tectonic_plates: int = 6) -> None:
        """
        Initialize the world scale generator.
        
        Args:
            seed: Master seed for deterministic generation
            tectonic_plates: Number of tectonic plates (affects geology)
        """
        self.seed = seed
        self.noise_gen = HierarchicalNoiseGenerator(seed)
        self.random = random.Random(seed)
        self.tectonic_plates = tectonic_plates
        
        # Generate tectonic plate centers
        self._plate_centers = self._generate_plate_centers()
    
    def _generate_plate_centers(self) -> List[Tuple[float, float]]:
        """Generate tectonic plate center points."""
        centers = []
        for _ in range(self.tectonic_plates):
            x = self.random.uniform(0, WORLD_SECTORS_X)
            y = self.random.uniform(0, WORLD_SECTORS_Y)
            centers.append((x, y))
        return centers
    
    def _get_tectonic_plate(self, x: int, y: int) -> int:
        """
        Determine which tectonic plate a sector belongs to.
        
        Args:
            x: Sector X coordinate
            y: Sector Y coordinate
            
        Returns:
            Tectonic plate ID (0 to tectonic_plates-1)
        """
        min_distance = float('inf')
        closest_plate = 0
        
        for i, (center_x, center_y) in enumerate(self._plate_centers):
            distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                closest_plate = i
        
        return closest_plate
    
    def _determine_climate_zone(self, x: int, y: int, temperature: float) -> ClimateZone:
        """
        Determine climate zone based on latitude and temperature.
        
        Args:
            x: Sector X coordinate
            y: Sector Y coordinate  
            temperature: Temperature value (-1.0 to 1.0)
            
        Returns:
            Climate zone classification
        """
        # Latitude factor (0.0 at poles, 1.0 at equator)
        latitude_factor = 1.0 - abs(y - WORLD_SECTORS_Y / 2) / (WORLD_SECTORS_Y / 2)
        
        # Combine latitude and temperature
        climate_value = (latitude_factor + temperature + 1.0) / 3.0
        
        if climate_value < 0.2:
            return ClimateZone.ARCTIC
        elif climate_value < 0.5:
            return ClimateZone.TEMPERATE
        elif climate_value < 0.8:
            return ClimateZone.TROPICAL
        else:
            return ClimateZone.ARID
    
    def _classify_terrain(
        self,
        elevation: float,
        moisture: float,
        temperature: float,
        climate: ClimateZone
    ) -> TerrainType:
        """
        Classify terrain type based on environmental factors.

        Args:
            elevation: Elevation value (-1.0 to 1.0)
            moisture: Moisture level (0.0 to 1.0)
            temperature: Temperature (-1.0 to 1.0)
            climate: Climate zone

        Returns:
            Terrain type classification
        """
        # Ocean threshold - more generous to ensure we get oceans
        if elevation < -0.1:
            return TerrainType.OCEAN

        # Coastal areas
        if elevation < 0.1:
            return TerrainType.COASTAL

        # High elevation = mountains - lower threshold
        if elevation > 0.4:
            return TerrainType.MOUNTAINS

        # Climate-based terrain for land areas
        if climate == ClimateZone.ARCTIC:
            return TerrainType.TUNDRA
        elif climate == ClimateZone.ARID:
            return TerrainType.DESERT
        else:
            # Temperate and tropical - use moisture
            if moisture > 0.6:
                return TerrainType.FOREST
            elif elevation > 0.2:
                return TerrainType.HILLS
            else:
                return TerrainType.PLAINS
    
    def _get_terrain_display(self, terrain: TerrainType, climate: ClimateZone) -> Tuple[str, ColorRGB]:
        """
        Get display character and color for terrain type.
        
        Args:
            terrain: Terrain type
            climate: Climate zone
            
        Returns:
            Tuple of (character, color)
        """
        terrain_display = {
            TerrainType.OCEAN: ('~', ColorRGB(0, 50, 150)),
            TerrainType.COASTAL: ('≈', ColorRGB(50, 100, 200)),
            TerrainType.PLAINS: ('.', ColorRGB(100, 150, 50)),
            TerrainType.FOREST: ('♠', ColorRGB(50, 100, 50)),
            TerrainType.HILLS: ('∩', ColorRGB(120, 100, 80)),
            TerrainType.MOUNTAINS: ('▲', ColorRGB(150, 150, 150)),
            TerrainType.DESERT: ('°', ColorRGB(200, 180, 100)),
            TerrainType.TUNDRA: ('*', ColorRGB(200, 200, 250))
        }
        
        char, base_color = terrain_display[terrain]
        
        # Modify color slightly based on climate
        color = ColorRGB(base_color.r, base_color.g, base_color.b)
        
        if climate == ClimateZone.ARCTIC:
            # Cooler tones
            color.b = min(255, color.b + 30)
        elif climate == ClimateZone.TROPICAL:
            # Warmer, more saturated
            color.g = min(255, color.g + 20)
        elif climate == ClimateZone.ARID:
            # More yellow/brown
            color.r = min(255, color.r + 20)
            color.g = min(255, color.g + 10)
        
        return char, color
    
    def generate_world_sector(self, x: int, y: int) -> WorldSectorData:
        """
        Generate a single world sector.
        
        Args:
            x: Sector X coordinate (0-7)
            y: Sector Y coordinate (0-5)
            
        Returns:
            Generated world sector data
        """
        # Convert to world coordinates for noise sampling
        world_x = x * 1000.0  # Scale up for continental noise
        world_y = y * 1000.0
        
        # Generate base environmental values using noise
        elevation = self.noise_gen.continental_noise(world_x, world_y)

        # Add some regional variation to elevation for more range
        elevation += self.noise_gen.regional_noise(world_x, world_y) * 0.5

        # Amplify elevation range to ensure we get full spectrum
        elevation = elevation * 1.5
        elevation = max(-1.0, min(1.0, elevation))
        
        # Temperature based on latitude and noise
        latitude_temp = 1.0 - abs(y - WORLD_SECTORS_Y / 2) / (WORLD_SECTORS_Y / 2)
        temp_noise = self.noise_gen.continental_noise(world_x + 5000, world_y + 5000)
        temperature = (latitude_temp * 0.7 + temp_noise * 0.3) * 2.0 - 1.0
        temperature = max(-1.0, min(1.0, temperature))
        
        # Moisture based on distance from ocean and noise
        moisture_noise = self.noise_gen.continental_noise(world_x + 10000, world_y + 10000)
        moisture = (moisture_noise + 1.0) * 0.5  # Convert to 0-1 range
        
        # Determine climate zone
        climate = self._determine_climate_zone(x, y, temperature)
        
        # Classify terrain
        terrain = self._classify_terrain(elevation, moisture, temperature, climate)
        
        # Determine features - use different coordinates and lower thresholds
        mountain_noise = self.noise_gen.regional_noise(world_x * 0.1 + 1500, world_y * 0.1 + 1500)
        has_mountains = mountain_noise > -0.3 and terrain != TerrainType.OCEAN and elevation > 0.05

        river_noise = self.noise_gen.regional_noise(world_x * 0.1 + 2000, world_y * 0.1 + 2000)
        has_rivers = river_noise > -0.2 and terrain not in [TerrainType.OCEAN, TerrainType.DESERT]
        
        # Get display representation
        display_char, display_color = self._get_terrain_display(terrain, climate)
        
        # Get tectonic plate
        tectonic_plate = self._get_tectonic_plate(x, y)
        
        # Generate sector-specific seed
        sector_seed = self.seed + x * 1000 + y * 100
        
        return WorldSectorData(
            coordinate=WorldCoordinate(x, y),
            dominant_terrain=terrain,
            elevation=elevation,
            has_mountains=has_mountains,
            has_rivers=has_rivers,
            climate_zone=climate,
            tectonic_plate=tectonic_plate,
            temperature=temperature,
            moisture=moisture,
            display_char=display_char,
            display_color=display_color,
            generation_seed=sector_seed
        )
    
    def generate_complete_world_map(self) -> WorldMapData:
        """
        Generate the complete 8x6 world map.
        
        Returns:
            Complete world map data with all sectors
        """
        sectors = []
        
        # Generate all sectors
        for y in range(WORLD_SECTORS_Y):
            row = []
            for x in range(WORLD_SECTORS_X):
                sector = self.generate_world_sector(x, y)
                row.append(sector)
            sectors.append(row)
        
        # Create world map data
        world_data = WorldMapData(
            sectors=sectors,
            generation_seed=self.seed,
            tectonic_plates=self.tectonic_plates,
            world_age=1.0,  # Default world age
            metadata={
                'generator_version': '1.0',
                'generation_time': 'runtime',
                'plate_centers': self._plate_centers
            }
        )
        
        return world_data


def export_world_to_file(world_data: WorldMapData, filename: str) -> None:
    """
    Export world data to text file for validation.
    
    Args:
        world_data: World map data to export
        filename: Output filename
    """
    with open(filename, 'w') as f:
        f.write(world_data.export_to_text())


def test_world_generation(seed: Seed = 12345) -> bool:
    """
    Test world generation functionality.
    
    Args:
        seed: Test seed
        
    Returns:
        True if generation successful, False otherwise
    """
    try:
        generator = WorldScaleGenerator(seed)
        world_data = generator.generate_complete_world_map()
        
        # Basic validation
        if len(world_data.sectors) != WORLD_SECTORS_Y:
            return False
        
        if len(world_data.sectors[0]) != WORLD_SECTORS_X:
            return False
        
        # Check that we have some variety
        terrains = set()
        for row in world_data.sectors:
            for sector in row:
                terrains.add(sector.dominant_terrain)
        
        return len(terrains) > 1
        
    except Exception:
        return False


if __name__ == "__main__":
    # Basic testing
    print("Testing world generation...")
    
    # Test single sector generation
    generator = WorldScaleGenerator(12345)
    sector = generator.generate_world_sector(0, 0)
    print(f"✓ Generated sector at (0,0): {sector.dominant_terrain.name}")
    print(f"  Biome: {sector.get_biome_description()}")
    
    # Test complete world generation
    if test_world_generation():
        print("✓ Complete world generation successful")
    else:
        print("✗ Complete world generation failed")
    
    # Generate and display a sample world
    world_data = generator.generate_complete_world_map()
    print(f"\nSample world (seed {generator.seed}):")
    for y in range(WORLD_SECTORS_Y):
        row = ""
        for x in range(WORLD_SECTORS_X):
            row += world_data.sectors[y][x].display_char
        print(f"  {row}")
    
    print("\nWorld generation system ready!")
