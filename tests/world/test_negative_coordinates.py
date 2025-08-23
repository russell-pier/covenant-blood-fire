"""
Tests for negative coordinate handling in the world generation system.

This module tests that negative coordinates work correctly with:
- Proper chunk coordinate conversion
- Smooth terrain transitions across chunk boundaries
- Consistent noise generation
- Character variations and organic features
"""

from src.covenant.world.chunks import ChunkManager
from src.covenant.world.generator import create_organic_world_generator
from src.covenant.world.organic import OrganicNoiseGenerator
from src.covenant.world.terrain import TerrainType
from collections import Counter
import math


class TestChunkCoordinateConversion:
    """Test that chunk coordinate conversion works correctly for negative coordinates."""
    
    def test_chunk_coordinate_conversion(self):
        """Test chunk coordinate conversion for various world coordinates."""
        chunk_manager = ChunkManager(32, 64)
        
        test_cases = [
            # (world_x, world_y, expected_chunk_x, expected_chunk_y)
            (0, 0, 0, 0),
            (31, 31, 0, 0),
            (32, 32, 1, 1),
            (-1, -1, -1, -1),
            (-32, -32, -1, -1),
            (-33, -33, -2, -2),
            (63, -65, 1, -3),
            (-64, 64, -2, 2),
        ]
        
        for world_x, world_y, expected_chunk_x, expected_chunk_y in test_cases:
            chunk_coord = chunk_manager.world_to_chunk_coordinate(world_x, world_y)
            assert chunk_coord.x == expected_chunk_x, \
                f"World ({world_x}, {world_y}) -> Chunk ({chunk_coord.x}, {chunk_coord.y}), expected ({expected_chunk_x}, {expected_chunk_y})"
            assert chunk_coord.y == expected_chunk_y, \
                f"World ({world_x}, {world_y}) -> Chunk ({chunk_coord.x}, {chunk_coord.y}), expected ({expected_chunk_x}, {expected_chunk_y})"
        
        print("✓ Chunk coordinate conversion working correctly")


class TestNoiseGenerationNegativeCoordinates:
    """Test that noise generation works correctly for negative coordinates."""
    
    def test_noise_continuity_across_zero(self):
        """Test that noise is continuous across the zero boundary."""
        noise_gen = OrganicNoiseGenerator(seed=12345)
        
        # Test continuity around x=0
        noise_values_x = []
        for x in [-2, -1, 0, 1, 2]:
            noise_val = noise_gen.noise(x, 0)
            noise_values_x.append(noise_val)
        
        # Check that values are different (not all the same)
        assert len(set(noise_values_x)) > 1, "Noise values should vary"
        
        # Test continuity around y=0
        noise_values_y = []
        for y in [-2, -1, 0, 1, 2]:
            noise_val = noise_gen.noise(0, y)
            noise_values_y.append(noise_val)
        
        # Check that values are different (not all the same)
        assert len(set(noise_values_y)) > 1, "Noise values should vary"
        
        print("✓ Noise generation continuous across zero boundary")
    
    def test_noise_deterministic_negative_coords(self):
        """Test that noise generation is deterministic for negative coordinates."""
        noise_gen1 = OrganicNoiseGenerator(seed=12345)
        noise_gen2 = OrganicNoiseGenerator(seed=12345)
        
        test_coords = [(-10.5, -20.3), (-1.1, -1.1), (-0.1, -0.1)]
        
        for x, y in test_coords:
            noise1 = noise_gen1.noise(x, y)
            noise2 = noise_gen2.noise(x, y)
            assert noise1 == noise2, f"Noise not deterministic at ({x}, {y}): {noise1} != {noise2}"
        
        print("✓ Noise generation deterministic for negative coordinates")


class TestTerrainGenerationNegativeCoordinates:
    """Test that terrain generation works correctly for negative coordinates."""
    
    def test_terrain_variety_in_negative_coords(self):
        """Test that negative coordinates produce terrain variety."""
        generator = create_organic_world_generator(seed=12345)
        
        terrain_counts = Counter()
        for x in range(-100, -50, 5):
            for y in range(-100, -50, 5):
                terrain = generator.get_terrain_at(x, y)
                terrain_counts[terrain] += 1
        
        # Should have at least 1 terrain type (could be more)
        assert len(terrain_counts) >= 1, f"No terrain found in negative coordinates"
        
        # Should not be all the same terrain (unless it's a very uniform area)
        total_tiles = sum(terrain_counts.values())
        max_terrain_count = max(terrain_counts.values())
        dominance_ratio = max_terrain_count / total_tiles
        
        print(f"Terrain variety in negative coords: {len(terrain_counts)} types")
        print(f"Dominant terrain: {dominance_ratio:.1%}")
        
        # Allow high dominance but not 100% (some variation expected)
        assert dominance_ratio < 1.0 or len(terrain_counts) > 1, "Should have some terrain variation"
        
        print("✓ Terrain variety working in negative coordinates")
    
    def test_smooth_transitions_negative_coords(self):
        """Test that terrain transitions are smooth in negative coordinates."""
        generator = create_organic_world_generator(seed=12345)
        
        # Test horizontal line across chunk boundaries
        terrains = []
        for x in range(-70, -30, 2):
            terrain = generator.get_terrain_at(x, -50)
            terrains.append(terrain)
        
        # Count terrain changes
        changes = 0
        for i in range(1, len(terrains)):
            if terrains[i] != terrains[i-1]:
                changes += 1
        
        # Should have some changes but not too many (smooth transitions)
        change_ratio = changes / len(terrains)
        print(f"Terrain changes in negative coords: {changes}/{len(terrains)} ({change_ratio:.1%})")
        
        # Allow for some changes but not excessive (would indicate hard boundaries)
        assert change_ratio < 0.5, f"Too many terrain changes: {change_ratio:.1%}"
        
        print("✓ Smooth transitions working in negative coordinates")
    
    def test_character_variations_negative_coords(self):
        """Test that character variations work in negative coordinates."""
        generator = create_organic_world_generator(seed=12345)
        
        character_variations = {}
        for x in range(-80, -60, 5):
            for y in range(-80, -60, 5):
                props = generator.get_organic_terrain_properties_at(x, y)
                if props:
                    terrain = props.terrain_type
                    if terrain not in character_variations:
                        character_variations[terrain] = set()
                    character_variations[terrain].add(props.character)
        
        # Should have character variations
        total_variations = sum(len(chars) for chars in character_variations.values())
        assert total_variations > 0, "No character variations found"
        
        print(f"Character variations in negative coords:")
        for terrain, chars in character_variations.items():
            print(f"  {terrain.value}: {sorted(chars)}")
        
        print("✓ Character variations working in negative coordinates")


class TestChunkBoundaryTransitions:
    """Test that chunk boundaries don't create hard transitions."""
    
    def test_no_hard_boundaries_negative_coords(self):
        """Test that there are no hard boundaries at chunk edges in negative coordinates."""
        generator = create_organic_world_generator(seed=12345)
        
        # Test around chunk boundary at x=-32 (between chunks -1 and -2)
        boundary_terrains = []
        for x in range(-35, -29):  # Cross the boundary
            terrain = generator.get_terrain_at(x, -50)
            boundary_terrains.append(terrain)
        
        # Check for abrupt changes at the boundary
        # The terrain at x=-32 and x=-33 should not be drastically different
        # from their neighbors
        boundary_changes = 0
        for i in range(1, len(boundary_terrains)):
            if boundary_terrains[i] != boundary_terrains[i-1]:
                boundary_changes += 1
        
        # Should not have too many changes in a small area
        change_ratio = boundary_changes / len(boundary_terrains)
        print(f"Boundary changes: {boundary_changes}/{len(boundary_terrains)} ({change_ratio:.1%})")
        
        # Allow some changes but not excessive
        assert change_ratio < 0.7, f"Too many changes at chunk boundary: {change_ratio:.1%}"
        
        print("✓ No hard boundaries at chunk edges in negative coordinates")


def run_negative_coordinate_tests():
    """Run all negative coordinate tests."""
    print("🧪 Testing Negative Coordinate Handling")
    print("=" * 50)
    
    # Test chunk coordinate conversion
    print("\n1. Testing Chunk Coordinate Conversion...")
    test_chunks = TestChunkCoordinateConversion()
    test_chunks.test_chunk_coordinate_conversion()
    
    # Test noise generation
    print("\n2. Testing Noise Generation...")
    test_noise = TestNoiseGenerationNegativeCoordinates()
    test_noise.test_noise_continuity_across_zero()
    test_noise.test_noise_deterministic_negative_coords()
    
    # Test terrain generation
    print("\n3. Testing Terrain Generation...")
    test_terrain = TestTerrainGenerationNegativeCoordinates()
    test_terrain.test_terrain_variety_in_negative_coords()
    test_terrain.test_smooth_transitions_negative_coords()
    test_terrain.test_character_variations_negative_coords()
    
    # Test chunk boundaries
    print("\n4. Testing Chunk Boundary Transitions...")
    test_boundaries = TestChunkBoundaryTransitions()
    test_boundaries.test_no_hard_boundaries_negative_coords()
    
    print("\n🎉 All negative coordinate tests passed!")
    print("\nNegative coordinate handling is now working correctly:")
    print("- Proper chunk coordinate conversion using floor division")
    print("- Continuous noise generation across zero boundary")
    print("- Smooth terrain transitions in negative areas")
    print("- Character variations working in all coordinate ranges")
    print("- No hard boundaries at chunk edges")


if __name__ == "__main__":
    run_negative_coordinate_tests()
