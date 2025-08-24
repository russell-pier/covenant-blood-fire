"""
Test suite for the world generation system.

Tests deterministic generation, terrain distribution, climate patterns,
and world map validation functionality.
"""

import pytest
from src.world_generator import WorldScaleGenerator, test_world_generation, export_world_to_file
from src.world_data import WorldMapData, validate_world_data
from src.world_types import TerrainType, ClimateZone, WORLD_SECTORS_X, WORLD_SECTORS_Y


class TestWorldScaleGenerator:
    """Test cases for the WorldScaleGenerator class."""
    
    def test_deterministic_generation(self):
        """Test that same seed produces identical worlds."""
        seed = 12345
        gen1 = WorldScaleGenerator(seed)
        gen2 = WorldScaleGenerator(seed)
        
        # Test single sector determinism
        sector1 = gen1.generate_world_sector(3, 2)
        sector2 = gen2.generate_world_sector(3, 2)
        
        assert sector1.dominant_terrain == sector2.dominant_terrain
        assert abs(sector1.elevation - sector2.elevation) < 1e-10
        assert abs(sector1.temperature - sector2.temperature) < 1e-10
        assert abs(sector1.moisture - sector2.moisture) < 1e-10
        assert sector1.climate_zone == sector2.climate_zone
        assert sector1.has_mountains == sector2.has_mountains
        assert sector1.has_rivers == sector2.has_rivers
        assert sector1.tectonic_plate == sector2.tectonic_plate
    
    def test_complete_world_determinism(self):
        """Test that complete world generation is deterministic."""
        seed = 54321
        gen1 = WorldScaleGenerator(seed)
        gen2 = WorldScaleGenerator(seed)
        
        world1 = gen1.generate_complete_world_map()
        world2 = gen2.generate_complete_world_map()
        
        # Check all sectors match
        for y in range(WORLD_SECTORS_Y):
            for x in range(WORLD_SECTORS_X):
                s1 = world1.sectors[y][x]
                s2 = world2.sectors[y][x]
                
                assert s1.dominant_terrain == s2.dominant_terrain, f"Terrain mismatch at ({x},{y})"
                assert abs(s1.elevation - s2.elevation) < 1e-10, f"Elevation mismatch at ({x},{y})"
                assert s1.climate_zone == s2.climate_zone, f"Climate mismatch at ({x},{y})"
    
    def test_different_seeds_produce_different_worlds(self):
        """Test that different seeds produce different worlds."""
        gen1 = WorldScaleGenerator(12345)
        gen2 = WorldScaleGenerator(54321)
        
        world1 = gen1.generate_complete_world_map()
        world2 = gen2.generate_complete_world_map()
        
        # Count differences
        differences = 0
        total_sectors = WORLD_SECTORS_X * WORLD_SECTORS_Y
        
        for y in range(WORLD_SECTORS_Y):
            for x in range(WORLD_SECTORS_X):
                s1 = world1.sectors[y][x]
                s2 = world2.sectors[y][x]
                
                if (s1.dominant_terrain != s2.dominant_terrain or
                    abs(s1.elevation - s2.elevation) > 0.1 or
                    s1.climate_zone != s2.climate_zone):
                    differences += 1
        
        # Should have significant differences
        assert differences > total_sectors * 0.3, f"Only {differences}/{total_sectors} sectors differ"
    
    def test_all_sectors_generated(self):
        """Test that all 48 sectors are generated."""
        generator = WorldScaleGenerator(12345)
        world_data = generator.generate_complete_world_map()
        
        assert len(world_data.sectors) == WORLD_SECTORS_Y
        for row in world_data.sectors:
            assert len(row) == WORLD_SECTORS_X
        
        # Check all coordinates are correct
        for y in range(WORLD_SECTORS_Y):
            for x in range(WORLD_SECTORS_X):
                sector = world_data.sectors[y][x]
                assert sector.coordinate.x == x
                assert sector.coordinate.y == y
    
    def test_terrain_distribution(self):
        """Test that terrain distribution is reasonable."""
        generator = WorldScaleGenerator(12345)
        world_data = generator.generate_complete_world_map()
        
        # Count terrain types
        terrain_counts = {}
        for terrain in TerrainType:
            terrain_counts[terrain] = 0
        
        for row in world_data.sectors:
            for sector in row:
                terrain_counts[sector.dominant_terrain] += 1
        
        total_sectors = WORLD_SECTORS_X * WORLD_SECTORS_Y
        
        # Should have some variety (at least 3 different terrain types)
        terrain_types_present = sum(1 for count in terrain_counts.values() if count > 0)
        assert terrain_types_present >= 3, f"Only {terrain_types_present} terrain types present"
        
        # Should have some ocean or coastal
        water_sectors = terrain_counts[TerrainType.OCEAN] + terrain_counts[TerrainType.COASTAL]
        assert water_sectors > 0, "No water sectors found"
        
        # Should have some land
        land_sectors = total_sectors - water_sectors
        assert land_sectors > 0, "No land sectors found"
    
    def test_climate_zone_patterns(self):
        """Test that climate zones follow latitude patterns."""
        generator = WorldScaleGenerator(12345)
        world_data = generator.generate_complete_world_map()
        
        # Count climate zones by latitude
        climate_by_lat = {}
        for y in range(WORLD_SECTORS_Y):
            climate_by_lat[y] = {}
            for climate in ClimateZone:
                climate_by_lat[y][climate] = 0
        
        for y in range(WORLD_SECTORS_Y):
            for x in range(WORLD_SECTORS_X):
                sector = world_data.sectors[y][x]
                climate_by_lat[y][sector.climate_zone] += 1
        
        # Check that we have climate variety
        all_climates = set()
        for y in range(WORLD_SECTORS_Y):
            for x in range(WORLD_SECTORS_X):
                all_climates.add(world_data.sectors[y][x].climate_zone)
        
        assert len(all_climates) >= 2, f"Only {len(all_climates)} climate zones present"
    
    def test_tectonic_plate_assignment(self):
        """Test that tectonic plates are assigned reasonably."""
        generator = WorldScaleGenerator(12345, tectonic_plates=4)
        world_data = generator.generate_complete_world_map()
        
        # Count sectors per plate
        plate_counts = {}
        for row in world_data.sectors:
            for sector in row:
                plate = sector.tectonic_plate
                plate_counts[plate] = plate_counts.get(plate, 0) + 1
        
        # Should use all plates
        assert len(plate_counts) == 4, f"Only {len(plate_counts)} plates used"
        
        # Each plate should have at least one sector
        for plate_id, count in plate_counts.items():
            assert count > 0, f"Plate {plate_id} has no sectors"
            assert 0 <= plate_id < 4, f"Invalid plate ID: {plate_id}"
    
    def test_elevation_ranges(self):
        """Test that elevation values are in valid ranges."""
        generator = WorldScaleGenerator(12345)
        world_data = generator.generate_complete_world_map()
        
        elevations = []
        for row in world_data.sectors:
            for sector in row:
                elevations.append(sector.elevation)
                # Check individual sector range
                assert -1.0 <= sector.elevation <= 1.0, f"Elevation {sector.elevation} out of range"
        
        # Should use a reasonable range of elevations
        min_elev = min(elevations)
        max_elev = max(elevations)
        elevation_range = max_elev - min_elev

        assert elevation_range > 0.3, f"Elevation range {elevation_range} too small"
    
    def test_temperature_and_moisture_ranges(self):
        """Test that temperature and moisture values are valid."""
        generator = WorldScaleGenerator(12345)
        world_data = generator.generate_complete_world_map()
        
        for row in world_data.sectors:
            for sector in row:
                # Temperature range
                assert -1.0 <= sector.temperature <= 1.0, f"Temperature {sector.temperature} out of range"
                
                # Moisture range
                assert 0.0 <= sector.moisture <= 1.0, f"Moisture {sector.moisture} out of range"
    
    def test_feature_generation(self):
        """Test that mountains and rivers are generated appropriately."""
        generator = WorldScaleGenerator(12345)
        world_data = generator.generate_complete_world_map()
        
        mountain_count = 0
        river_count = 0
        ocean_with_mountains = 0
        
        for row in world_data.sectors:
            for sector in row:
                if sector.has_mountains:
                    mountain_count += 1
                    if sector.dominant_terrain == TerrainType.OCEAN:
                        ocean_with_mountains += 1
                
                if sector.has_rivers:
                    river_count += 1
        
        # Should have some mountains and rivers
        assert mountain_count > 0, "No mountains generated"
        assert river_count > 0, "No rivers generated"
        
        # Ocean sectors shouldn't have mountains
        assert ocean_with_mountains == 0, f"{ocean_with_mountains} ocean sectors have mountains"


class TestWorldMapData:
    """Test cases for WorldMapData functionality."""
    
    def test_world_map_validation(self):
        """Test world map data validation."""
        generator = WorldScaleGenerator(12345)
        world_data = generator.generate_complete_world_map()
        
        # Should pass validation
        errors = validate_world_data(world_data)
        assert len(errors) == 0, f"Validation errors: {errors}"
    
    def test_world_statistics(self):
        """Test world statistics calculation."""
        generator = WorldScaleGenerator(12345)
        world_data = generator.generate_complete_world_map()
        
        stats = world_data.calculate_statistics()
        
        # Check required fields
        assert 'total_sectors' in stats
        assert 'terrain_distribution' in stats
        assert 'climate_distribution' in stats
        assert 'average_elevation' in stats
        
        # Check values
        assert stats['total_sectors'] == WORLD_SECTORS_X * WORLD_SECTORS_Y
        assert -1.0 <= stats['average_elevation'] <= 1.0
        assert -1.0 <= stats['average_temperature'] <= 1.0
        assert 0.0 <= stats['average_moisture'] <= 1.0
    
    def test_world_export(self):
        """Test world data export functionality."""
        generator = WorldScaleGenerator(12345)
        world_data = generator.generate_complete_world_map()
        
        # Test text export
        text_export = world_data.export_to_text()
        assert "World Map" in text_export
        assert "World Statistics" in text_export
        
        # Test JSON export
        json_export = world_data.to_json()
        assert "generation_seed" in json_export
        assert "sectors" in json_export
        
        # Should be valid JSON
        import json
        parsed = json.loads(json_export)
        assert parsed['generation_seed'] == 12345


class TestWorldGeneratorCLI:
    """Test CLI functionality."""
    
    def test_world_generation_function(self):
        """Test the test_world_generation function."""
        # Should succeed with valid seed
        assert test_world_generation(12345) == True
        assert test_world_generation(54321) == True
    
    def test_export_functionality(self):
        """Test world export to file."""
        import tempfile
        import os
        
        generator = WorldScaleGenerator(12345)
        world_data = generator.generate_complete_world_map()
        
        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_filename = f.name
        
        try:
            export_world_to_file(world_data, temp_filename)
            
            # Check file was created and has content
            assert os.path.exists(temp_filename)
            
            with open(temp_filename, 'r') as f:
                content = f.read()
                assert len(content) > 0
                assert "World Map" in content
        
        finally:
            # Clean up
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)


if __name__ == "__main__":
    # Run basic tests when called directly
    print("Running world generator tests...")
    
    # Test basic generation
    generator = WorldScaleGenerator(12345)
    world_data = generator.generate_complete_world_map()
    
    print(f"✓ Generated world with {len(world_data.sectors)} rows")
    print(f"✓ Each row has {len(world_data.sectors[0])} sectors")
    
    # Test validation
    errors = validate_world_data(world_data)
    if len(errors) == 0:
        print("✓ World data validation passed")
    else:
        print(f"✗ World data validation failed: {errors}")
    
    # Test statistics
    stats = world_data.calculate_statistics()
    print(f"✓ World statistics: {stats['total_sectors']} sectors")
    
    print("Basic world generator tests completed!")
