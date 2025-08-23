"""
Performance benchmarks for the environmental layer system.

This module provides benchmarks to ensure the environmental system
meets performance requirements compared to the legacy system.
"""

import time
import pytest
from src.covenant.world.generator import (
    create_environmental_world_generator, 
    create_legacy_world_generator
)
from src.covenant.world.chunks import ChunkCoordinate


class TestPerformanceBenchmarks:
    """Performance benchmarks for environmental vs legacy systems."""
    
    def test_terrain_generation_performance(self):
        """Benchmark terrain generation performance."""
        # Test parameters
        test_size = 100
        iterations = 3
        
        # Legacy system benchmark
        legacy_times = []
        for _ in range(iterations):
            generator = create_legacy_world_generator(seed=12345)
            start_time = time.time()
            
            for x in range(0, test_size, 2):
                for y in range(0, test_size, 2):
                    generator.get_terrain_at(x, y)
            
            legacy_times.append(time.time() - start_time)
        
        legacy_avg = sum(legacy_times) / len(legacy_times)
        
        # Environmental system benchmark
        env_times = []
        for _ in range(iterations):
            generator = create_environmental_world_generator(seed=12345)
            start_time = time.time()
            
            for x in range(0, test_size, 2):
                for y in range(0, test_size, 2):
                    generator.get_terrain_at(x, y)
            
            env_times.append(time.time() - start_time)
        
        env_avg = sum(env_times) / len(env_times)
        
        # Performance requirements
        slowdown_ratio = env_avg / legacy_avg
        
        print(f"\nTerrain Generation Performance:")
        print(f"Legacy system: {legacy_avg:.4f}s average")
        print(f"Environmental system: {env_avg:.4f}s average")
        print(f"Slowdown ratio: {slowdown_ratio:.2f}x")
        
        # Should not be more than 4x slower (generous limit)
        assert slowdown_ratio < 4.0, f"Environmental system too slow: {slowdown_ratio:.2f}x"
    
    def test_chunk_generation_performance(self):
        """Benchmark chunk generation performance."""
        iterations = 5
        
        # Legacy system benchmark
        legacy_times = []
        for _ in range(iterations):
            generator = create_legacy_world_generator(seed=12345)
            start_time = time.time()
            
            # Generate several chunks
            for chunk_x in range(0, 3):
                for chunk_y in range(0, 3):
                    chunk_coord = ChunkCoordinate(chunk_x, chunk_y)
                    generator.get_chunk_terrain_data(chunk_coord)
            
            legacy_times.append(time.time() - start_time)
        
        legacy_avg = sum(legacy_times) / len(legacy_times)
        
        # Environmental system benchmark
        env_times = []
        for _ in range(iterations):
            generator = create_environmental_world_generator(seed=12345)
            start_time = time.time()
            
            # Generate several chunks
            for chunk_x in range(0, 3):
                for chunk_y in range(0, 3):
                    chunk_coord = ChunkCoordinate(chunk_x, chunk_y)
                    generator.get_chunk_terrain_data(chunk_coord)
            
            env_times.append(time.time() - start_time)
        
        env_avg = sum(env_times) / len(env_times)
        
        # Performance requirements
        slowdown_ratio = env_avg / legacy_avg
        
        print(f"\nChunk Generation Performance:")
        print(f"Legacy system: {legacy_avg:.4f}s average")
        print(f"Environmental system: {env_avg:.4f}s average")
        print(f"Slowdown ratio: {slowdown_ratio:.2f}x")
        
        # Should not be more than 4x slower
        assert slowdown_ratio < 4.0, f"Environmental chunk generation too slow: {slowdown_ratio:.2f}x"
    
    def test_memory_usage_estimation(self):
        """Estimate memory usage of environmental data."""
        generator = create_environmental_world_generator(seed=12345)
        
        # Generate a chunk and estimate memory usage
        chunk_coord = ChunkCoordinate(0, 0)
        chunk = generator.get_chunk_terrain_data(chunk_coord)
        
        # Estimate memory usage
        chunk_size = generator.chunk_size
        tiles_per_chunk = chunk_size * chunk_size
        
        # Environmental data: 3 floats per tile (elevation, moisture, temperature)
        # Each float is typically 8 bytes in Python
        env_data_bytes = tiles_per_chunk * 3 * 8
        
        # Terrain data: 1 enum per tile (typically 4-8 bytes)
        terrain_data_bytes = tiles_per_chunk * 8  # Conservative estimate
        
        total_bytes_per_chunk = env_data_bytes + terrain_data_bytes
        
        print(f"\nMemory Usage Estimation:")
        print(f"Chunk size: {chunk_size}x{chunk_size} = {tiles_per_chunk} tiles")
        print(f"Environmental data: {env_data_bytes} bytes")
        print(f"Terrain data: {terrain_data_bytes} bytes")
        print(f"Total per chunk: {total_bytes_per_chunk} bytes ({total_bytes_per_chunk/1024:.1f} KB)")
        
        # With 64 chunk cache
        cache_size = 64
        total_cache_bytes = total_bytes_per_chunk * cache_size
        print(f"Total cache memory: {total_cache_bytes} bytes ({total_cache_bytes/1024/1024:.1f} MB)")
        
        # Should be reasonable (less than 10MB for cache)
        assert total_cache_bytes < 10 * 1024 * 1024, f"Memory usage too high: {total_cache_bytes/1024/1024:.1f} MB"
    
    def test_deterministic_performance(self):
        """Test that deterministic generation doesn't impact performance significantly."""
        iterations = 3
        
        # Test same seed multiple times
        same_seed_times = []
        for _ in range(iterations):
            generator = create_environmental_world_generator(seed=12345)
            start_time = time.time()
            
            for x in range(0, 50, 2):
                for y in range(0, 50, 2):
                    generator.get_terrain_at(x, y)
            
            same_seed_times.append(time.time() - start_time)
        
        # Test different seeds
        different_seed_times = []
        for i in range(iterations):
            generator = create_environmental_world_generator(seed=12345 + i)
            start_time = time.time()
            
            for x in range(0, 50, 2):
                for y in range(0, 50, 2):
                    generator.get_terrain_at(x, y)
            
            different_seed_times.append(time.time() - start_time)
        
        same_seed_avg = sum(same_seed_times) / len(same_seed_times)
        different_seed_avg = sum(different_seed_times) / len(different_seed_times)
        
        print(f"\nDeterministic Performance:")
        print(f"Same seed: {same_seed_avg:.4f}s average")
        print(f"Different seeds: {different_seed_avg:.4f}s average")
        
        # Performance should be similar regardless of seed
        ratio = max(same_seed_avg, different_seed_avg) / min(same_seed_avg, different_seed_avg)
        assert ratio < 1.5, f"Seed variation affects performance too much: {ratio:.2f}x"
    
    def test_large_area_generation(self):
        """Test performance with large area generation."""
        generator = create_environmental_world_generator(seed=12345)
        
        # Generate a large area
        start_time = time.time()
        terrain_count = 0
        
        for x in range(0, 500, 5):  # 100x100 grid with step 5
            for y in range(0, 500, 5):
                generator.get_terrain_at(x, y)
                terrain_count += 1
        
        generation_time = time.time() - start_time
        tiles_per_second = terrain_count / generation_time
        
        print(f"\nLarge Area Generation:")
        print(f"Generated {terrain_count} tiles in {generation_time:.4f}s")
        print(f"Performance: {tiles_per_second:.0f} tiles/second")
        
        # Should generate at least 1000 tiles per second
        assert tiles_per_second > 1000, f"Large area generation too slow: {tiles_per_second:.0f} tiles/s"
    
    def test_environmental_data_access_performance(self):
        """Test performance of environmental data access."""
        generator = create_environmental_world_generator(seed=12345)
        
        # Pre-generate some chunks
        for chunk_x in range(0, 2):
            for chunk_y in range(0, 2):
                chunk_coord = ChunkCoordinate(chunk_x, chunk_y)
                generator.get_chunk_terrain_data(chunk_coord)
        
        # Test environmental data access
        start_time = time.time()
        access_count = 0
        
        for x in range(0, 64, 2):  # 2 chunks worth
            for y in range(0, 64, 2):
                env_data = generator.get_environmental_data_at(x, y)
                if env_data:
                    access_count += 1
        
        access_time = time.time() - start_time
        accesses_per_second = access_count / access_time
        
        print(f"\nEnvironmental Data Access:")
        print(f"Accessed {access_count} environmental data points in {access_time:.4f}s")
        print(f"Performance: {accesses_per_second:.0f} accesses/second")
        
        # Should be very fast for cached data
        assert accesses_per_second > 10000, f"Environmental data access too slow: {accesses_per_second:.0f} accesses/s"


@pytest.mark.slow
class TestExtensivePerformance:
    """More extensive performance tests (marked as slow)."""
    
    def test_sustained_generation_performance(self):
        """Test performance over sustained generation."""
        generator = create_environmental_world_generator(seed=12345)
        
        # Generate terrain over a large area to test sustained performance
        chunk_times = []
        
        for chunk_x in range(0, 10):
            for chunk_y in range(0, 10):
                start_time = time.time()
                chunk_coord = ChunkCoordinate(chunk_x, chunk_y)
                generator.get_chunk_terrain_data(chunk_coord)
                chunk_times.append(time.time() - start_time)
        
        # Check that performance doesn't degrade significantly
        first_half = chunk_times[:len(chunk_times)//2]
        second_half = chunk_times[len(chunk_times)//2:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        print(f"\nSustained Generation Performance:")
        print(f"First half average: {first_avg:.4f}s")
        print(f"Second half average: {second_avg:.4f}s")
        
        # Performance shouldn't degrade by more than 50%
        degradation = second_avg / first_avg
        assert degradation < 1.5, f"Performance degraded too much: {degradation:.2f}x"
