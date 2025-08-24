"""
Test suite for the noise generation system.

Tests deterministic behavior, frequency separation, value ranges,
and hierarchical noise generation functionality.
"""

import pytest
import math
from src.noise import NoiseGenerator, HierarchicalNoiseGenerator


class TestNoiseGenerator:
    """Test cases for the base NoiseGenerator class."""
    
    def test_deterministic_behavior(self):
        """Test that same seed produces identical output."""
        seed = 12345
        gen1 = NoiseGenerator(seed)
        gen2 = NoiseGenerator(seed)
        
        test_points = [
            (0.0, 0.0),
            (1.5, 2.3),
            (10.7, 20.1),
            (100.5, 200.9),
            (-5.2, -10.8)
        ]
        
        for x, y in test_points:
            val1 = gen1.noise_2d(x, y)
            val2 = gen2.noise_2d(x, y)
            assert abs(val1 - val2) < 1e-10, f"Non-deterministic at ({x}, {y})"
    
    def test_different_seeds_produce_different_output(self):
        """Test that different seeds produce different noise."""
        gen1 = NoiseGenerator(12345)
        gen2 = NoiseGenerator(54321)
        
        # Test multiple points to ensure difference
        differences = 0
        test_points = [(i * 0.1, j * 0.1) for i in range(10) for j in range(10)]
        
        for x, y in test_points:
            val1 = gen1.noise_2d(x, y)
            val2 = gen2.noise_2d(x, y)
            if abs(val1 - val2) > 1e-6:
                differences += 1
        
        # Should have many differences
        assert differences > len(test_points) * 0.8, "Seeds too similar"
    
    def test_noise_value_range(self):
        """Test that noise values are in expected range [-1, 1]."""
        gen = NoiseGenerator(12345)
        
        # Test many points to check range
        for i in range(100):
            for j in range(100):
                x, y = i * 0.1, j * 0.1
                value = gen.noise_2d(x, y)
                assert -1.0 <= value <= 1.0, f"Value {value} out of range at ({x}, {y})"
    
    def test_octave_noise_range(self):
        """Test that octave noise values are in expected range."""
        gen = NoiseGenerator(12345)
        
        for octaves in [1, 2, 4, 8]:
            for i in range(50):
                x, y = i * 0.2, i * 0.3
                value = gen.octave_noise_2d(x, y, octaves=octaves)
                assert -1.0 <= value <= 1.0, f"Octave noise {value} out of range"
    
    def test_noise_range_function(self):
        """Test the noise_range function for custom ranges."""
        gen = NoiseGenerator(12345)
        
        test_ranges = [
            (0.0, 1.0),
            (-5.0, 5.0),
            (10.0, 20.0),
            (-100.0, -50.0)
        ]
        
        for min_val, max_val in test_ranges:
            for i in range(20):
                x, y = i * 0.5, i * 0.7
                value = gen.noise_range(x, y, min_val=min_val, max_val=max_val)
                assert min_val <= value <= max_val, f"Range noise {value} not in [{min_val}, {max_val}]"
    
    def test_smoothness(self):
        """Test that noise is smooth (no sudden jumps)."""
        gen = NoiseGenerator(12345)
        
        # Test smoothness by checking nearby points
        step = 0.01
        max_difference = 0.0
        
        for i in range(100):
            x, y = i * 0.1, i * 0.1
            val1 = gen.noise_2d(x, y)
            val2 = gen.noise_2d(x + step, y)
            val3 = gen.noise_2d(x, y + step)
            
            diff1 = abs(val2 - val1)
            diff2 = abs(val3 - val1)
            max_difference = max(max_difference, diff1, diff2)
        
        # Noise should be smooth - no huge jumps for small steps
        assert max_difference < 0.1, f"Noise not smooth, max difference: {max_difference}"


class TestHierarchicalNoiseGenerator:
    """Test cases for the HierarchicalNoiseGenerator class."""
    
    def test_deterministic_hierarchical(self):
        """Test that hierarchical noise is deterministic."""
        seed = 12345
        gen1 = HierarchicalNoiseGenerator(seed)
        gen2 = HierarchicalNoiseGenerator(seed)
        
        test_points = [(10.0, 20.0), (100.5, 200.3), (1000.1, 2000.7)]
        
        for x, y in test_points:
            # Test all three scales
            cont1 = gen1.continental_noise(x, y)
            cont2 = gen2.continental_noise(x, y)
            assert abs(cont1 - cont2) < 1e-10, "Continental noise not deterministic"
            
            reg1 = gen1.regional_noise(x, y)
            reg2 = gen2.regional_noise(x, y)
            assert abs(reg1 - reg2) < 1e-10, "Regional noise not deterministic"
            
            local1 = gen1.local_noise(x, y)
            local2 = gen2.local_noise(x, y)
            assert abs(local1 - local2) < 1e-10, "Local noise not deterministic"
    
    def test_frequency_separation(self):
        """Test that different scales have different frequency characteristics."""
        gen = HierarchicalNoiseGenerator(12345)
        
        # Test points close together
        x1, y1 = 100.0, 100.0
        x2, y2 = 100.1, 100.1  # Very close points
        
        cont1 = gen.continental_noise(x1, y1)
        cont2 = gen.continental_noise(x2, y2)
        
        reg1 = gen.regional_noise(x1, y1)
        reg2 = gen.regional_noise(x2, y2)
        
        local1 = gen.local_noise(x1, y1)
        local2 = gen.local_noise(x2, y2)
        
        cont_diff = abs(cont2 - cont1)
        reg_diff = abs(reg2 - reg1)
        local_diff = abs(local2 - local1)
        
        # Continental should change least, local should change most
        assert cont_diff <= reg_diff, "Continental noise changing too fast"
        assert reg_diff <= local_diff, "Regional noise changing faster than local"
    
    def test_combined_noise_weights(self):
        """Test that combined noise respects weight parameters."""
        gen = HierarchicalNoiseGenerator(12345)
        
        x, y = 50.0, 75.0
        
        # Test with only continental weight
        combined1 = gen.combined_noise(x, y, 1.0, 0.0, 0.0)
        continental = gen.continental_noise(x, y)
        assert abs(combined1 - continental) < 1e-10, "Combined noise ignoring weights"
        
        # Test with only regional weight
        combined2 = gen.combined_noise(x, y, 0.0, 1.0, 0.0)
        regional = gen.regional_noise(x, y)
        assert abs(combined2 - regional) < 1e-10, "Combined noise ignoring weights"
        
        # Test with only local weight
        combined3 = gen.combined_noise(x, y, 0.0, 0.0, 1.0)
        local = gen.local_noise(x, y)
        assert abs(combined3 - local) < 1e-10, "Combined noise ignoring weights"
    
    def test_all_scales_in_range(self):
        """Test that all noise scales produce values in [-1, 1]."""
        gen = HierarchicalNoiseGenerator(12345)
        
        test_points = [
            (0.0, 0.0),
            (50.5, 100.3),
            (1000.7, 2000.1),
            (-500.2, -1000.8)
        ]
        
        for x, y in test_points:
            cont = gen.continental_noise(x, y)
            reg = gen.regional_noise(x, y)
            local = gen.local_noise(x, y)
            combined = gen.combined_noise(x, y)
            
            assert -1.0 <= cont <= 1.0, f"Continental noise {cont} out of range"
            assert -1.0 <= reg <= 1.0, f"Regional noise {reg} out of range"
            assert -1.0 <= local <= 1.0, f"Local noise {local} out of range"
            assert -1.0 <= combined <= 1.0, f"Combined noise {combined} out of range"


class TestNoiseDistribution:
    """Test noise distribution properties."""
    
    def test_noise_distribution(self):
        """Test that noise has reasonable distribution properties."""
        gen = NoiseGenerator(12345)
        
        values = []
        for i in range(1000):
            x = i * 0.1
            y = i * 0.13  # Use different step to avoid patterns
            values.append(gen.noise_2d(x, y))
        
        # Calculate basic statistics
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        
        # Mean should be close to 0
        assert abs(mean) < 0.1, f"Noise mean {mean} too far from 0"
        
        # Should have reasonable variance (not all the same value)
        assert variance > 0.01, f"Noise variance {variance} too low"
        
        # Should use most of the range
        min_val = min(values)
        max_val = max(values)
        range_used = max_val - min_val
        assert range_used > 1.0, f"Noise range {range_used} too small"


def test_noise_cli_interface():
    """Test the CLI interface functionality."""
    from src.noise import test_noise_determinism
    
    # Test the determinism function
    assert test_noise_determinism(12345) == True, "Determinism test failed"
    assert test_noise_determinism(54321) == True, "Determinism test failed with different seed"


if __name__ == "__main__":
    # Run basic tests when called directly
    print("Running noise generation tests...")
    
    # Test determinism
    gen1 = NoiseGenerator(12345)
    gen2 = NoiseGenerator(12345)
    
    test_point = (10.5, 20.3)
    val1 = gen1.noise_2d(*test_point)
    val2 = gen2.noise_2d(*test_point)
    
    if abs(val1 - val2) < 1e-10:
        print("✓ Basic determinism test passed")
    else:
        print("✗ Basic determinism test failed")
    
    # Test hierarchical noise
    hier_gen = HierarchicalNoiseGenerator(12345)
    cont = hier_gen.continental_noise(1000, 1000)
    reg = hier_gen.regional_noise(100, 100)
    local = hier_gen.local_noise(10, 10)
    
    print(f"Continental: {cont:.4f}, Regional: {reg:.4f}, Local: {local:.4f}")
    
    if all(-1.0 <= val <= 1.0 for val in [cont, reg, local]):
        print("✓ All noise values in valid range")
    else:
        print("✗ Some noise values out of range")
    
    print("Basic noise tests completed!")
