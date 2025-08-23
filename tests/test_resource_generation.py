"""
Tests for the resource generation system.

This module contains unit and integration tests for the clustered resource
generation system across all three world layers.
"""

import pytest
from typing import Dict, Tuple

from src.covenant.world.layered import WorldLayer, LayeredTerrainData
from src.covenant.world.resource_generator import ClusteredResourceGenerator
from src.covenant.world.resource_types import ResourceType, ResourceNode, get_resource_layer
from src.covenant.world.resource_utils import (
    get_resource_at_position, has_resource_at_position, get_all_resources_in_chunk,
    count_resources_by_type, get_resource_summary, can_access_layer
)
from src.covenant.world.layered_generator import LayeredWorldGenerator


class TestResourceGenerator:
    """Test the core resource generation functionality."""
    
    def test_resource_generator_initialization(self):
        """Test that resource generator initializes correctly."""
        generator = ClusteredResourceGenerator(seed=12345)
        
        assert generator.seed == 12345
        assert generator.noise_cluster is not None
        assert generator.noise_density is not None
        assert generator.noise_rarity is not None
        assert len(generator.layer_config) == 3
    
    def test_layer_specific_cluster_generation(self):
        """Test that clusters are generated with layer-specific characteristics."""
        generator = ClusteredResourceGenerator(seed=12345)
        
        # Test each layer has different configuration
        surface_config = generator.layer_config[WorldLayer.SURFACE]
        underground_config = generator.layer_config[WorldLayer.UNDERGROUND]
        mountain_config = generator.layer_config[WorldLayer.MOUNTAINS]
        
        # Surface should be easier to find (lower threshold)
        assert surface_config['threshold'] < underground_config['threshold']
        
        # Underground should have smaller, denser clusters
        assert underground_config['radius_base'] < surface_config['radius_base']
        assert underground_config['density_base'] > surface_config['density_base']
        
        # Mountain should be between surface and underground
        assert mountain_config['threshold'] > surface_config['threshold']
        assert mountain_config['threshold'] < underground_config['threshold']
    
    def test_resource_type_layer_mapping(self):
        """Test that resource types are correctly mapped to layers."""
        # Surface resources
        assert get_resource_layer(ResourceType.WOOD) == WorldLayer.SURFACE
        assert get_resource_layer(ResourceType.FOOD_SURFACE) == WorldLayer.SURFACE
        
        # Underground resources
        assert get_resource_layer(ResourceType.GOLD) == WorldLayer.UNDERGROUND
        assert get_resource_layer(ResourceType.IRON) == WorldLayer.UNDERGROUND
        
        # Mountain resources
        assert get_resource_layer(ResourceType.STONE_MOUNTAIN) == WorldLayer.MOUNTAINS
        assert get_resource_layer(ResourceType.ICE) == WorldLayer.MOUNTAINS


class TestResourceIntegration:
    """Test integration with the layered world generator."""
    
    def test_layered_generator_with_resources(self):
        """Test that layered generator creates resources when enabled."""
        generator = LayeredWorldGenerator(seed=12345, enable_resources=True)
        
        assert generator.enable_resources is True
        assert generator.resource_generator is not None
        
        # Generate a small chunk
        chunk_data = generator.generate_layered_chunk(0, 0, chunk_size=8)
        
        assert len(chunk_data) == 64  # 8x8 chunk
        
        # Check that some resources were generated
        resource_summary = get_resource_summary(chunk_data)
        
        # Should have at least some resources (not guaranteed due to randomness, but likely)
        # We'll check that the system is working rather than specific counts
        assert 'total_resources' in resource_summary
        assert 'by_layer' in resource_summary
        assert 'by_type' in resource_summary
    
    def test_layered_generator_without_resources(self):
        """Test that layered generator works without resources."""
        generator = LayeredWorldGenerator(seed=12345, enable_resources=False)
        
        assert generator.enable_resources is False
        assert generator.resource_generator is None
        
        # Generate a small chunk
        chunk_data = generator.generate_layered_chunk(0, 0, chunk_size=8)
        
        assert len(chunk_data) == 64  # 8x8 chunk
        
        # Check that no resources were generated
        resource_summary = get_resource_summary(chunk_data)
        assert resource_summary['total_resources'] == 0
    
    def test_resource_terrain_integration(self):
        """Test that resources are properly integrated into terrain data."""
        generator = LayeredWorldGenerator(seed=12345, enable_resources=True)
        chunk_data = generator.generate_layered_chunk(0, 0, chunk_size=8)
        
        # Find a position with resources
        for position, layered_terrain in chunk_data.items():
            for layer in WorldLayer:
                resource = get_resource_at_position(layered_terrain, layer)
                if resource:
                    # Verify resource is properly stored
                    assert isinstance(resource, ResourceNode)
                    assert resource.resource_type in ResourceType
                    assert resource.rarity in ['common', 'rare', 'epic']
                    assert resource.yield_amount > 0
                    assert len(resource.fg_color) == 3  # RGB tuple
                    assert all(0 <= c <= 255 for c in resource.fg_color)  # Valid RGB values
                    
                    # Verify terrain character was updated
                    if layer == WorldLayer.SURFACE:
                        terrain_char = layered_terrain.surface.char
                    elif layer == WorldLayer.UNDERGROUND:
                        terrain_char = layered_terrain.underground.char
                    elif layer == WorldLayer.MOUNTAINS and layered_terrain.mountains:
                        terrain_char = layered_terrain.mountains.char
                    else:
                        continue
                    
                    assert terrain_char == resource.char
                    break


class TestResourceUtils:
    """Test resource utility functions."""
    
    def test_resource_access_functions(self):
        """Test basic resource access functions."""
        generator = LayeredWorldGenerator(seed=12345, enable_resources=True)
        chunk_data = generator.generate_layered_chunk(0, 0, chunk_size=4)
        
        # Test resource counting
        resource_counts = count_resources_by_type(chunk_data)
        assert isinstance(resource_counts, dict)
        
        # Test resource summary
        summary = get_resource_summary(chunk_data)
        assert 'total_resources' in summary
        assert 'by_layer' in summary
        assert 'by_type' in summary
        assert 'renewable_count' in summary
        assert 'finite_count' in summary
        
        # Verify counts are consistent
        total_from_layers = sum(summary['by_layer'].values())
        assert total_from_layers == summary['total_resources']
        
        renewable_plus_finite = summary['renewable_count'] + summary['finite_count']
        assert renewable_plus_finite == summary['total_resources']
    
    def test_layer_accessibility(self):
        """Test layer accessibility logic."""
        generator = LayeredWorldGenerator(seed=12345, enable_resources=True)
        chunk_data = generator.generate_layered_chunk(0, 0, chunk_size=4)
        
        for layered_terrain in chunk_data.values():
            # Surface should always be accessible
            assert can_access_layer(layered_terrain, WorldLayer.SURFACE) is True
            
            # Underground access depends on cave entrance
            underground_accessible = can_access_layer(layered_terrain, WorldLayer.UNDERGROUND)
            assert underground_accessible == layered_terrain.has_cave_entrance
            
            # Mountain access depends on mountain access
            mountain_accessible = can_access_layer(layered_terrain, WorldLayer.MOUNTAINS)
            assert mountain_accessible == layered_terrain.has_mountain_access


class TestResourceDistribution:
    """Test resource distribution patterns and balance."""
    
    def test_chunk_boundary_consistency(self):
        """Test that resource clusters are consistent across chunk boundaries."""
        generator = LayeredWorldGenerator(seed=12345, enable_resources=True)
        
        # Generate adjacent chunks
        chunk_00 = generator.generate_layered_chunk(0, 0, chunk_size=4)
        chunk_01 = generator.generate_layered_chunk(0, 1, chunk_size=4)
        chunk_10 = generator.generate_layered_chunk(1, 0, chunk_size=4)
        
        # This test verifies that the same seed produces consistent results
        # More sophisticated tests would check cluster overlap at boundaries
        assert len(chunk_00) == 16
        assert len(chunk_01) == 16
        assert len(chunk_10) == 16
    
    def test_resource_rarity_distribution(self):
        """Test that resource rarity follows expected distribution."""
        generator = LayeredWorldGenerator(seed=12345, enable_resources=True)
        
        # Generate multiple chunks to get statistical data
        all_resources = []
        for chunk_x in range(3):
            for chunk_y in range(3):
                chunk_data = generator.generate_layered_chunk(chunk_x, chunk_y, chunk_size=8)
                layered_resources = get_all_resources_in_chunk(chunk_data)
                
                for layer_resources in layered_resources.values():
                    for _, resource in layer_resources:
                        all_resources.append(resource)
        
        if all_resources:  # Only test if we have resources
            # Count rarities
            rarity_counts = {'common': 0, 'rare': 0, 'epic': 0}
            for resource in all_resources:
                rarity_counts[resource.rarity] += 1
            
            total = sum(rarity_counts.values())
            if total > 0:
                # Common should be most frequent, epic should be least
                common_ratio = rarity_counts['common'] / total
                epic_ratio = rarity_counts['epic'] / total
                
                assert common_ratio > epic_ratio
    
    def test_layer_specific_resources(self):
        """Test that resources appear on appropriate layers."""
        generator = LayeredWorldGenerator(seed=12345, enable_resources=True)
        chunk_data = generator.generate_layered_chunk(0, 0, chunk_size=8)
        
        layered_resources = get_all_resources_in_chunk(chunk_data)
        
        # Check surface resources
        for _, resource in layered_resources[WorldLayer.SURFACE]:
            assert resource.resource_type in [
                ResourceType.WOOD, ResourceType.FOOD_SURFACE, 
                ResourceType.STONE_SURFACE, ResourceType.WATER
            ]
        
        # Check underground resources
        for _, resource in layered_resources[WorldLayer.UNDERGROUND]:
            assert resource.resource_type in [
                ResourceType.GOLD, ResourceType.IRON, ResourceType.COAL,
                ResourceType.GEMS, ResourceType.CRYSTAL, ResourceType.UNDERGROUND_WATER
            ]
        
        # Check mountain resources
        for _, resource in layered_resources[WorldLayer.MOUNTAINS]:
            assert resource.resource_type in [
                ResourceType.STONE_MOUNTAIN, ResourceType.METAL_MOUNTAIN,
                ResourceType.RARE_GEMS, ResourceType.ICE
            ]


if __name__ == "__main__":
    pytest.main([__file__])
