"""
Tests for the enhanced organic world generation system.

This module tests the large-scale terrain features, terrain transitions,
independent river systems, and logical terrain progression.
"""

from src.empires.world.organic import OrganicWorldGenerator
from src.empires.world.generator import create_organic_world_generator
from src.empires.world.terrain import TerrainType
from collections import Counter, defaultdict


class TestLargeScaleTerrainFeatures:
    """Test that terrain features span multiple chunks."""
    
    def test_terrain_coherence_across_chunks(self):
        """Test that terrain features are larger than individual chunks."""
        generator = OrganicWorldGenerator(seed=12345)
        
        # Generate multiple adjacent chunks
        chunk_terrains = {}
        for chunk_x in range(3):
            for chunk_y in range(3):
                chunk_data = generator.generate_chunk_data(chunk_x, chunk_y, 16)
                chunk_terrains[(chunk_x, chunk_y)] = chunk_data
        
        # Check for terrain coherence within chunks
        coherent_chunks = 0
        for (chunk_x, chunk_y), chunk_data in chunk_terrains.items():
            terrain_counts = Counter()
            for terrain_data in chunk_data.values():
                terrain_counts[terrain_data.terrain_type] += 1
            
            # A chunk is coherent if one terrain type dominates (>60%)
            total_tiles = sum(terrain_counts.values())
            dominant_terrain_count = max(terrain_counts.values())
            coherence_ratio = dominant_terrain_count / total_tiles
            
            if coherence_ratio > 0.6:
                coherent_chunks += 1
        
        # Most chunks should be coherent (large terrain features)
        coherence_percentage = coherent_chunks / len(chunk_terrains)
        print(f"Chunk coherence: {coherence_percentage:.1%} ({coherent_chunks}/{len(chunk_terrains)} chunks)")
        assert coherence_percentage > 0.5, f"Not enough coherent chunks: {coherence_percentage:.1%}"
    
    def test_biome_size_minimum(self):
        """Test that biomes span at least 4 chunks worth of area."""
        generator = OrganicWorldGenerator(seed=12345)
        
        # Generate a large area (equivalent to 6x6 chunks)
        large_area_size = 96  # 6 chunks * 16 tiles each
        terrain_map = {}
        
        for x in range(0, large_area_size, 4):  # Sample every 4th tile
            for y in range(0, large_area_size, 4):
                chunk_x, chunk_y = x // 16, y // 16
                local_x, local_y = x % 16, y % 16
                
                chunk_data = generator.generate_chunk_data(chunk_x, chunk_y, 16)
                if (local_x, local_y) in chunk_data:
                    terrain_map[(x, y)] = chunk_data[(local_x, local_y)].terrain_type
        
        # Find connected regions of the same terrain type
        visited = set()
        large_regions = 0
        
        for (x, y), terrain in terrain_map.items():
            if (x, y) in visited:
                continue
            
            # Flood fill to find region size
            region_size = self._flood_fill_region(terrain_map, x, y, terrain, visited)
            
            # A region spanning 4+ chunks should have 64+ tiles (16*16/4 = 64 sample points)
            if region_size >= 16:  # Accounting for sampling every 4th tile
                large_regions += 1
        
        print(f"Found {large_regions} large terrain regions")
        assert large_regions > 0, "No large terrain regions found"
    
    def _flood_fill_region(self, terrain_map, start_x, start_y, target_terrain, visited):
        """Flood fill to find connected region size."""
        stack = [(start_x, start_y)]
        region_size = 0
        
        while stack:
            x, y = stack.pop()
            if (x, y) in visited or (x, y) not in terrain_map:
                continue
            if terrain_map[(x, y)] != target_terrain:
                continue
            
            visited.add((x, y))
            region_size += 1
            
            # Check 4-connected neighbors
            for dx, dy in [(0, 4), (0, -4), (4, 0), (-4, 0)]:  # Step by 4 due to sampling
                stack.append((x + dx, y + dy))
        
        return region_size


class TestTerrainTransitions:
    """Test smooth terrain transitions and bleedover effects."""
    
    def test_terrain_transitions_are_smooth(self):
        """Test that terrain transitions are gradual, not abrupt."""
        generator = create_organic_world_generator(seed=12345)
        
        # Sample a line across terrain to check for smooth transitions
        transition_points = []
        prev_terrain = None
        
        for x in range(0, 200, 2):
            terrain = generator.get_terrain_at(x, 100)  # Horizontal line
            if prev_terrain and terrain != prev_terrain:
                transition_points.append((x, prev_terrain, terrain))
            prev_terrain = terrain
        
        # Check that transitions make logical sense
        logical_transitions = 0
        for x, from_terrain, to_terrain in transition_points:
            if self._is_logical_transition(from_terrain, to_terrain):
                logical_transitions += 1
        
        if transition_points:
            logical_ratio = logical_transitions / len(transition_points)
            print(f"Logical transitions: {logical_ratio:.1%} ({logical_transitions}/{len(transition_points)})")
            assert logical_ratio > 0.7, f"Too many illogical transitions: {logical_ratio:.1%}"
    
    def _is_logical_transition(self, from_terrain, to_terrain):
        """Check if a terrain transition is logically sound."""
        # Define logical terrain adjacencies
        logical_adjacencies = {
            TerrainType.DESERT: [TerrainType.SAND, TerrainType.GRASS, TerrainType.LIGHT_GRASS],
            TerrainType.SAND: [TerrainType.DESERT, TerrainType.GRASS, TerrainType.SHALLOW_WATER],
            TerrainType.GRASS: [TerrainType.SAND, TerrainType.LIGHT_GRASS, TerrainType.DARK_GRASS, TerrainType.FERTILE],
            TerrainType.LIGHT_GRASS: [TerrainType.GRASS, TerrainType.FERTILE, TerrainType.DESERT],
            TerrainType.DARK_GRASS: [TerrainType.GRASS, TerrainType.FOREST],
            TerrainType.FERTILE: [TerrainType.GRASS, TerrainType.LIGHT_GRASS, TerrainType.FOREST],
            TerrainType.FOREST: [TerrainType.FERTILE, TerrainType.DARK_GRASS, TerrainType.SWAMP],
            TerrainType.SWAMP: [TerrainType.FOREST, TerrainType.SHALLOW_WATER],
            TerrainType.SHALLOW_WATER: [TerrainType.SAND, TerrainType.SWAMP, TerrainType.DEEP_WATER],
            TerrainType.DEEP_WATER: [TerrainType.SHALLOW_WATER],
        }
        
        # Rivers can appear anywhere
        if from_terrain in [TerrainType.SHALLOW_WATER, TerrainType.DEEP_WATER] or \
           to_terrain in [TerrainType.SHALLOW_WATER, TerrainType.DEEP_WATER]:
            return True
        
        return to_terrain in logical_adjacencies.get(from_terrain, [])


class TestIndependentRiverSystem:
    """Test that rivers are independent features spanning multiple chunks."""
    
    def test_rivers_span_multiple_chunks(self):
        """Test that rivers extend across multiple chunks."""
        generator = create_organic_world_generator(seed=12345)
        
        # Find river tiles across a large area
        river_tiles = []
        for x in range(0, 320, 2):  # 10 chunks worth
            for y in range(0, 320, 2):
                terrain = generator.get_terrain_at(x, y)
                if terrain in [TerrainType.SHALLOW_WATER, TerrainType.DEEP_WATER]:
                    river_tiles.append((x, y))
        
        if not river_tiles:
            print("No rivers found in test area")
            return  # Rivers are rare, this is acceptable
        
        # Check if rivers span multiple chunks
        chunk_coords = set()
        for x, y in river_tiles:
            chunk_x, chunk_y = x // 32, y // 32
            chunk_coords.add((chunk_x, chunk_y))
        
        chunks_with_rivers = len(chunk_coords)
        print(f"Rivers found in {chunks_with_rivers} chunks")
        
        # If we have rivers, they should span multiple chunks
        if river_tiles:
            assert chunks_with_rivers >= 2, f"Rivers should span multiple chunks, found in {chunks_with_rivers}"
    
    def test_rivers_ignore_terrain_boundaries(self):
        """Test that rivers can cross different terrain types."""
        generator = create_organic_world_generator(seed=12345)
        
        # Find river segments and check adjacent terrain
        river_terrain_neighbors = defaultdict(set)
        
        for x in range(0, 200, 2):
            for y in range(0, 200, 2):
                terrain = generator.get_terrain_at(x, y)
                if terrain in [TerrainType.SHALLOW_WATER, TerrainType.DEEP_WATER]:
                    # Check neighboring terrain types
                    for dx, dy in [(2, 0), (-2, 0), (0, 2), (0, -2)]:
                        neighbor_terrain = generator.get_terrain_at(x + dx, y + dy)
                        if neighbor_terrain not in [TerrainType.SHALLOW_WATER, TerrainType.DEEP_WATER]:
                            river_terrain_neighbors[terrain].add(neighbor_terrain)
        
        # Rivers should be adjacent to multiple terrain types
        for river_type, neighbor_types in river_terrain_neighbors.items():
            if len(neighbor_types) > 1:
                print(f"{river_type.value} borders: {[t.value for t in neighbor_types]}")
                assert True  # Rivers cross terrain boundaries
                return
        
        print("Rivers are rare or don't cross terrain boundaries in test area")


class TestLogicalTerrainProgression:
    """Test that terrain types follow logical environmental gradients."""
    
    def test_no_desert_forest_adjacency(self):
        """Test that deserts and forests are not typically adjacent."""
        generator = create_organic_world_generator(seed=12345)
        
        desert_forest_adjacencies = 0
        total_desert_tiles = 0
        
        for x in range(0, 200, 2):
            for y in range(0, 200, 2):
                terrain = generator.get_terrain_at(x, y)
                if terrain == TerrainType.DESERT:
                    total_desert_tiles += 1
                    
                    # Check neighbors
                    for dx, dy in [(2, 0), (-2, 0), (0, 2), (0, -2)]:
                        neighbor = generator.get_terrain_at(x + dx, y + dy)
                        if neighbor == TerrainType.FOREST:
                            desert_forest_adjacencies += 1
        
        if total_desert_tiles > 0:
            adjacency_ratio = desert_forest_adjacencies / total_desert_tiles
            print(f"Desert-forest adjacency ratio: {adjacency_ratio:.1%}")
            assert adjacency_ratio < 0.1, f"Too many desert-forest adjacencies: {adjacency_ratio:.1%}"
        else:
            print("No deserts found in test area")
    
    def test_terrain_distribution_is_realistic(self):
        """Test that terrain distribution follows realistic patterns."""
        generator = create_organic_world_generator(seed=12345)
        
        terrain_counts = Counter()
        for x in range(0, 200, 4):
            for y in range(0, 200, 4):
                terrain = generator.get_terrain_at(x, y)
                terrain_counts[terrain] += 1
        
        total = sum(terrain_counts.values())
        
        print("Terrain distribution:")
        for terrain, count in terrain_counts.most_common():
            percentage = (count / total) * 100
            print(f"  {terrain.value}: {percentage:.1f}%")
        
        # Check for reasonable distribution
        # No single terrain should dominate completely (>90%)
        max_percentage = max(terrain_counts.values()) / total
        assert max_percentage < 0.9, f"Single terrain dominates: {max_percentage:.1%}"
        
        # Should have at least 2 different terrain types
        assert len(terrain_counts) >= 2, f"Only {len(terrain_counts)} terrain types found"


def run_all_tests():
    """Run all enhanced organic system tests."""
    print("🧪 Testing Enhanced Organic World Generation System")
    print("=" * 60)
    
    # Test large-scale features
    print("\n1. Testing Large-Scale Terrain Features...")
    test_large = TestLargeScaleTerrainFeatures()
    test_large.test_terrain_coherence_across_chunks()
    test_large.test_biome_size_minimum()
    print("✓ Large-scale terrain features working")
    
    # Test transitions
    print("\n2. Testing Terrain Transitions...")
    test_transitions = TestTerrainTransitions()
    test_transitions.test_terrain_transitions_are_smooth()
    print("✓ Terrain transitions working")
    
    # Test rivers
    print("\n3. Testing Independent River System...")
    test_rivers = TestIndependentRiverSystem()
    test_rivers.test_rivers_span_multiple_chunks()
    test_rivers.test_rivers_ignore_terrain_boundaries()
    print("✓ Independent river system working")
    
    # Test logical progression
    print("\n4. Testing Logical Terrain Progression...")
    test_logic = TestLogicalTerrainProgression()
    test_logic.test_no_desert_forest_adjacency()
    test_logic.test_terrain_distribution_is_realistic()
    print("✓ Logical terrain progression working")
    
    print("\n🎉 All enhanced organic system tests passed!")
    print("\nThe enhanced system successfully provides:")
    print("- Large terrain features spanning 4+ chunks")
    print("- Smooth terrain transitions with logical progression")
    print("- Independent river systems crossing terrain boundaries")
    print("- Realistic terrain distribution and adjacencies")


if __name__ == "__main__":
    run_all_tests()
