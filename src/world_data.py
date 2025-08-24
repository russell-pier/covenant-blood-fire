"""
World data structures for the three-tier world generation system.

This module defines the data structures used to represent world sectors,
regional blocks, and their associated metadata for the hierarchical
world generation system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import json

try:
    from .world_types import (
        TerrainType, ClimateZone, WorldCoordinate, 
        ColorRGB, Seed, WORLD_SECTORS_X, WORLD_SECTORS_Y
    )
except ImportError:
    from world_types import (
        TerrainType, ClimateZone, WorldCoordinate, 
        ColorRGB, Seed, WORLD_SECTORS_X, WORLD_SECTORS_Y
    )


@dataclass
class WorldSectorData:
    """
    Data structure representing a single world sector.
    
    Each sector represents a 16,384×16,384 tile area in the world
    and contains continental-scale terrain information.
    
    Attributes:
        coordinate: Position in the 8x6 world grid
        dominant_terrain: Primary terrain type for this sector
        elevation: Average elevation (-1.0 to 1.0, sea level = 0)
        has_mountains: Whether this sector contains mountain ranges
        has_rivers: Whether this sector contains major rivers
        climate_zone: Climate classification for this sector
        tectonic_plate: Tectonic plate ID for geological consistency
        temperature: Average temperature (-1.0 to 1.0)
        moisture: Average moisture level (0.0 to 1.0)
        display_char: Character used for world view display
        display_color: Color used for world view display
        generation_seed: Seed used for generating this sector
    """
    coordinate: WorldCoordinate
    dominant_terrain: TerrainType
    elevation: float
    has_mountains: bool
    has_rivers: bool
    climate_zone: ClimateZone
    tectonic_plate: int
    temperature: float
    moisture: float
    display_char: str
    display_color: ColorRGB
    generation_seed: Seed
    
    def __post_init__(self) -> None:
        """Validate sector data after initialization."""
        # Validate elevation range
        if not -1.0 <= self.elevation <= 1.0:
            raise ValueError(f"Elevation {self.elevation} out of range [-1.0, 1.0]")
        
        # Validate temperature range
        if not -1.0 <= self.temperature <= 1.0:
            raise ValueError(f"Temperature {self.temperature} out of range [-1.0, 1.0]")
        
        # Validate moisture range
        if not 0.0 <= self.moisture <= 1.0:
            raise ValueError(f"Moisture {self.moisture} out of range [0.0, 1.0]")
        
        # Validate coordinate bounds
        if not (0 <= self.coordinate.x < WORLD_SECTORS_X):
            raise ValueError(f"X coordinate {self.coordinate.x} out of bounds")
        if not (0 <= self.coordinate.y < WORLD_SECTORS_Y):
            raise ValueError(f"Y coordinate {self.coordinate.y} out of bounds")
    
    def is_ocean(self) -> bool:
        """Check if this sector is primarily ocean."""
        return self.dominant_terrain == TerrainType.OCEAN
    
    def is_coastal(self) -> bool:
        """Check if this sector is coastal."""
        return self.dominant_terrain == TerrainType.COASTAL
    
    def is_land(self) -> bool:
        """Check if this sector is primarily land."""
        return not (self.is_ocean() or self.is_coastal())
    
    def get_biome_description(self) -> str:
        """Get a human-readable description of this sector's biome."""
        climate_desc = {
            ClimateZone.ARCTIC: "frigid",
            ClimateZone.TEMPERATE: "temperate", 
            ClimateZone.TROPICAL: "tropical",
            ClimateZone.ARID: "arid"
        }
        
        terrain_desc = {
            TerrainType.OCEAN: "deep ocean",
            TerrainType.COASTAL: "coastal waters",
            TerrainType.PLAINS: "grasslands",
            TerrainType.FOREST: "forests",
            TerrainType.HILLS: "rolling hills",
            TerrainType.MOUNTAINS: "mountain ranges",
            TerrainType.DESERT: "desert",
            TerrainType.TUNDRA: "tundra"
        }
        
        climate = climate_desc.get(self.climate_zone, "unknown")
        terrain = terrain_desc.get(self.dominant_terrain, "unknown")
        
        features = []
        if self.has_mountains:
            features.append("mountainous")
        if self.has_rivers:
            features.append("river systems")
        
        feature_str = f" with {', '.join(features)}" if features else ""
        
        return f"{climate} {terrain}{feature_str}"
    
    def to_dict(self) -> Dict:
        """Convert sector data to dictionary for serialization."""
        return {
            'coordinate': {'x': self.coordinate.x, 'y': self.coordinate.y},
            'dominant_terrain': self.dominant_terrain.name,
            'elevation': self.elevation,
            'has_mountains': self.has_mountains,
            'has_rivers': self.has_rivers,
            'climate_zone': self.climate_zone.name,
            'tectonic_plate': self.tectonic_plate,
            'temperature': self.temperature,
            'moisture': self.moisture,
            'display_char': self.display_char,
            'display_color': {'r': self.display_color.r, 'g': self.display_color.g, 'b': self.display_color.b},
            'generation_seed': self.generation_seed,
            'biome_description': self.get_biome_description()
        }


@dataclass
class WorldMapData:
    """
    Container for complete world map data.
    
    Manages the 8x6 grid of world sectors and provides
    access methods and validation.
    
    Attributes:
        sectors: 2D array of WorldSectorData [y][x]
        generation_seed: Master seed used for world generation
        tectonic_plates: Number of tectonic plates in the world
        world_age: Geological age factor affecting terrain
        metadata: Additional world generation metadata
    """
    sectors: List[List[WorldSectorData]]
    generation_seed: Seed
    tectonic_plates: int
    world_age: float
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate world map data after initialization."""
        # Validate grid dimensions
        if len(self.sectors) != WORLD_SECTORS_Y:
            raise ValueError(f"Expected {WORLD_SECTORS_Y} rows, got {len(self.sectors)}")
        
        for y, row in enumerate(self.sectors):
            if len(row) != WORLD_SECTORS_X:
                raise ValueError(f"Row {y} has {len(row)} sectors, expected {WORLD_SECTORS_X}")
        
        # Validate all sector coordinates match their position
        for y in range(WORLD_SECTORS_Y):
            for x in range(WORLD_SECTORS_X):
                sector = self.sectors[y][x]
                if sector.coordinate.x != x or sector.coordinate.y != y:
                    raise ValueError(f"Sector at [{y}][{x}] has wrong coordinate {sector.coordinate}")
    
    def get_sector(self, x: int, y: int) -> Optional[WorldSectorData]:
        """
        Get sector at given coordinates.
        
        Args:
            x: X coordinate (0-7)
            y: Y coordinate (0-5)
            
        Returns:
            WorldSectorData if coordinates valid, None otherwise
        """
        if 0 <= x < WORLD_SECTORS_X and 0 <= y < WORLD_SECTORS_Y:
            return self.sectors[y][x]
        return None
    
    def get_sector_by_coord(self, coord: WorldCoordinate) -> Optional[WorldSectorData]:
        """Get sector by WorldCoordinate."""
        return self.get_sector(coord.x, coord.y)
    
    def get_neighbors(self, x: int, y: int) -> List[WorldSectorData]:
        """
        Get all neighboring sectors (including diagonals).
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            List of neighboring sectors
        """
        neighbors = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                neighbor = self.get_sector(x + dx, y + dy)
                if neighbor:
                    neighbors.append(neighbor)
        return neighbors
    
    def get_ocean_sectors(self) -> List[WorldSectorData]:
        """Get all ocean sectors."""
        return [sector for row in self.sectors for sector in row if sector.is_ocean()]
    
    def get_land_sectors(self) -> List[WorldSectorData]:
        """Get all land sectors."""
        return [sector for row in self.sectors for sector in row if sector.is_land()]
    
    def get_coastal_sectors(self) -> List[WorldSectorData]:
        """Get all coastal sectors."""
        return [sector for row in self.sectors for sector in row if sector.is_coastal()]
    
    def calculate_statistics(self) -> Dict:
        """Calculate world statistics."""
        all_sectors = [sector for row in self.sectors for sector in row]
        total_sectors = len(all_sectors)
        
        # Terrain distribution
        terrain_counts = {}
        for terrain in TerrainType:
            terrain_counts[terrain.name] = sum(1 for s in all_sectors if s.dominant_terrain == terrain)
        
        # Climate distribution
        climate_counts = {}
        for climate in ClimateZone:
            climate_counts[climate.name] = sum(1 for s in all_sectors if s.climate_zone == climate)
        
        # Feature counts
        mountain_count = sum(1 for s in all_sectors if s.has_mountains)
        river_count = sum(1 for s in all_sectors if s.has_rivers)
        
        # Average values
        avg_elevation = sum(s.elevation for s in all_sectors) / total_sectors
        avg_temperature = sum(s.temperature for s in all_sectors) / total_sectors
        avg_moisture = sum(s.moisture for s in all_sectors) / total_sectors
        
        return {
            'total_sectors': total_sectors,
            'terrain_distribution': terrain_counts,
            'climate_distribution': climate_counts,
            'sectors_with_mountains': mountain_count,
            'sectors_with_rivers': river_count,
            'average_elevation': avg_elevation,
            'average_temperature': avg_temperature,
            'average_moisture': avg_moisture,
            'tectonic_plates': self.tectonic_plates,
            'world_age': self.world_age
        }
    
    def export_to_text(self) -> str:
        """Export world map to text format for validation."""
        lines = []
        lines.append(f"World Map (Seed: {self.generation_seed})")
        lines.append("=" * 50)
        
        # Grid representation
        for y in range(WORLD_SECTORS_Y):
            row_chars = ""
            for x in range(WORLD_SECTORS_X):
                sector = self.sectors[y][x]
                row_chars += sector.display_char
            lines.append(f"Row {y}: {row_chars}")
        
        lines.append("")
        
        # Statistics
        stats = self.calculate_statistics()
        lines.append("World Statistics:")
        for key, value in stats.items():
            if isinstance(value, dict):
                lines.append(f"  {key}:")
                for subkey, subvalue in value.items():
                    lines.append(f"    {subkey}: {subvalue}")
            else:
                lines.append(f"  {key}: {value}")
        
        return "\n".join(lines)
    
    def to_json(self) -> str:
        """Export world map to JSON format."""
        data = {
            'generation_seed': self.generation_seed,
            'tectonic_plates': self.tectonic_plates,
            'world_age': self.world_age,
            'metadata': self.metadata,
            'sectors': [[sector.to_dict() for sector in row] for row in self.sectors],
            'statistics': self.calculate_statistics()
        }
        return json.dumps(data, indent=2)


def validate_world_data(world_data: WorldMapData) -> List[str]:
    """
    Validate world data consistency and return any issues found.
    
    Args:
        world_data: World map data to validate
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    try:
        # Basic structure validation happens in __post_init__
        pass
    except ValueError as e:
        errors.append(f"Structure validation failed: {e}")
        return errors
    
    # Check for reasonable terrain distribution
    stats = world_data.calculate_statistics()
    terrain_dist = stats['terrain_distribution']
    
    # Should have some ocean
    if terrain_dist.get('OCEAN', 0) == 0:
        errors.append("No ocean sectors found")
    
    # Should have some land
    land_count = sum(terrain_dist.get(t, 0) for t in ['PLAINS', 'FOREST', 'HILLS', 'MOUNTAINS', 'DESERT', 'TUNDRA'])
    if land_count == 0:
        errors.append("No land sectors found")
    
    # Check climate zone distribution
    climate_dist = stats['climate_distribution']
    if len([c for c in climate_dist.values() if c > 0]) < 2:
        errors.append("Too few climate zones represented")
    
    return errors


if __name__ == "__main__":
    # Basic testing
    print("Testing world data structures...")
    
    # Test sector creation
    try:
        sector = WorldSectorData(
            coordinate=WorldCoordinate(0, 0),
            dominant_terrain=TerrainType.PLAINS,
            elevation=0.2,
            has_mountains=False,
            has_rivers=True,
            climate_zone=ClimateZone.TEMPERATE,
            tectonic_plate=1,
            temperature=0.1,
            moisture=0.6,
            display_char='.',
            display_color=ColorRGB(100, 150, 100),
            generation_seed=12345
        )
        print("✓ WorldSectorData creation successful")
        print(f"  Biome: {sector.get_biome_description()}")
    except Exception as e:
        print(f"✗ WorldSectorData creation failed: {e}")
    
    print("World data structures ready!")
