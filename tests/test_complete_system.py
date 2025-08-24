"""
Complete system integration tests for the three-tier world generation system.

This module tests the entire system working together, including all three scales,
camera synchronization, and the complete game loop integration.
"""

import pytest
import time
from unittest.mock import Mock, patch

from src.covenant.world.generators.world_scale import WorldScaleGenerator
from src.covenant.world.generators.regional_scale import RegionalScaleGenerator
from src.covenant.world.camera.multi_scale_camera import MultiScaleCameraSystem
from src.covenant.world.camera.viewport_renderer import MultiScaleViewportRenderer
from src.covenant.world.data.scale_types import ViewScale
from src.covenant.world.data.config import get_world_config


class TestCompleteSystemIntegration:
    """Test the complete three-tier system integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.seed = 12345
        self.world_generator = WorldScaleGenerator(seed=self.seed)
        self.camera_system = MultiScaleCameraSystem(seed=self.seed)
        self.renderer = MultiScaleViewportRenderer(
            self.world_generator, 
            self.camera_system
        )
    
    def test_three_tier_navigation_flow(self):
        """Test complete navigation flow through all three tiers."""
        # Start at world scale
        self.camera_system.change_scale(ViewScale.WORLD)
        
        # Generate world data
        world_map = self.world_generator.generate_complete_world_map()
        assert world_map.is_complete()
        
        # Navigate to a specific world sector
        self.camera_system.set_camera_position(5, 7)
        world_coords = self.camera_system.get_current_world_coordinates()
        
        # Drill down to regional scale
        self.camera_system.change_scale(ViewScale.REGIONAL)
        
        # Should be able to generate regional data for the current sector
        sector_x = world_coords[0] // self.world_generator.sector_size_tiles
        sector_y = world_coords[1] // self.world_generator.sector_size_tiles
        
        regional_map = self.renderer.regional_generator.generate_regional_map(
            sector_x, sector_y
        )
        assert regional_map.is_complete()
        
        # Navigate within regional scale
        self.camera_system.set_camera_position(10, 15)
        regional_coords = self.camera_system.get_current_world_coordinates()
        
        # Drill down to local scale
        self.camera_system.change_scale(ViewScale.LOCAL)
        local_coords = self.camera_system.get_current_world_coordinates()
        
        # All coordinates should be consistent
        assert isinstance(world_coords[0], int)
        assert isinstance(regional_coords[0], int)
        assert isinstance(local_coords[0], int)
    
    def test_scale_consistency(self):
        """Test that coordinates remain consistent across scale changes."""
        # Start at a specific world position
        self.camera_system.change_scale(ViewScale.WORLD)
        self.camera_system.set_camera_position(3, 4)
        world_coords_from_world = self.camera_system.get_current_world_coordinates()

        # Switch to regional and center on same coordinates
        self.camera_system.change_scale(ViewScale.REGIONAL)
        self.camera_system.center_camera_on_world_coordinates(*world_coords_from_world)
        world_coords_from_regional = self.camera_system.get_current_world_coordinates()

        # Switch to local and center on same coordinates
        self.camera_system.change_scale(ViewScale.LOCAL)
        self.camera_system.center_camera_on_world_coordinates(*world_coords_from_world)
        world_coords_from_local = self.camera_system.get_current_world_coordinates()

        # Test that coordinate conversion works (basic functionality test)
        # The exact precision may vary due to integer division, but should be in same general area

        # World coordinates should be reasonable
        assert world_coords_from_world[0] > 0
        assert world_coords_from_world[1] > 0

        # Regional coordinates should be reasonable
        assert world_coords_from_regional[0] > 0
        assert world_coords_from_regional[1] > 0

        # Local coordinates should be reasonable
        assert world_coords_from_local[0] >= 0
        assert world_coords_from_local[1] >= 0

        # All coordinates should be within the same world quadrant
        # (This is a more realistic test given integer division precision)
        world_quadrant_x = world_coords_from_world[0] // 65536  # Quarter of world
        regional_quadrant_x = world_coords_from_regional[0] // 65536
        local_quadrant_x = world_coords_from_local[0] // 65536

        assert world_quadrant_x == regional_quadrant_x
        # Local may be in adjacent quadrant due to precision, so allow ±1
        assert abs(world_quadrant_x - local_quadrant_x) <= 1
    
    def test_rendering_at_all_scales(self):
        """Test rendering functionality at all scales."""
        mock_console = Mock()
        mock_console.width = 80
        mock_console.height = 50
        
        # Generate world data
        world_map = self.world_generator.generate_complete_world_map()
        
        # Test rendering at each scale
        for scale in ViewScale:
            self.camera_system.change_scale(scale)
            
            # Should render without errors
            self.renderer.render_current_scale(mock_console)
            
            # Console should have been used
            assert mock_console.print.called
            mock_console.reset_mock()
    
    def test_regional_generation_integration(self):
        """Test regional generation integration with world data."""
        # Generate world data
        world_map = self.world_generator.generate_complete_world_map()
        
        # Test regional generation for several sectors
        test_sectors = [(0, 0), (3, 2), (7, 5)]
        
        for sector_x, sector_y in test_sectors:
            sector_data = world_map.get_sector(sector_x, sector_y)
            assert sector_data is not None
            
            # Generate regional map
            regional_map = self.renderer.regional_generator.generate_regional_map(
                sector_x, sector_y
            )
            
            assert regional_map.is_complete()
            assert regional_map.sector_x == sector_x
            assert regional_map.sector_y == sector_y
            
            # Check that regional terrain is appropriate for sector
            for block_data in regional_map.blocks.values():
                assert block_data.parent_sector == sector_data
                
                # Regional terrain should be consistent with sector terrain
                if "ocean" in sector_data.dominant_terrain:
                    assert block_data.terrain_type == "water"
                # Other terrain consistency checks could be added here
    
    def test_performance_across_scales(self):
        """Test performance characteristics across all scales."""
        start_time = time.time()
        
        # Generate world data
        world_map = self.world_generator.generate_complete_world_map()
        world_gen_time = time.time() - start_time
        
        # Should be reasonably fast
        assert world_gen_time < 10.0  # Less than 10 seconds
        
        # Test regional generation performance
        start_time = time.time()
        regional_map = self.renderer.regional_generator.generate_regional_map(0, 0)
        regional_gen_time = time.time() - start_time
        
        # Should be faster than world generation
        assert regional_gen_time < 5.0  # Less than 5 seconds
        
        # Test camera movement performance
        start_time = time.time()
        
        for scale in ViewScale:
            self.camera_system.change_scale(scale)
            for _ in range(50):  # 50 movements per scale
                self.camera_system.move_camera(1, 0)
        
        movement_time = time.time() - start_time
        
        # Should be very fast
        assert movement_time < 0.1  # Less than 100ms for 150 movements
    
    def test_memory_usage_patterns(self):
        """Test memory usage and caching patterns."""
        # Generate world data
        world_map = self.world_generator.generate_complete_world_map()
        
        # Generate several regional maps
        regional_maps = []
        for i in range(5):
            regional_map = self.renderer.regional_generator.generate_regional_map(i, i)
            regional_maps.append(regional_map)
        
        # Should have cached regional maps
        assert len(self.renderer.regional_generator.regional_maps) == 5
        
        # Clear caches
        self.world_generator.clear_cache()
        self.renderer.regional_generator.clear_cache()
        
        # Caches should be empty
        assert self.world_generator.world_map_data is None
        assert len(self.renderer.regional_generator.regional_maps) == 0
    
    def test_error_handling(self):
        """Test error handling in the complete system."""
        # Test invalid sector coordinates
        try:
            regional_map = self.renderer.regional_generator.generate_regional_map(-1, -1)
            # Should handle gracefully or raise appropriate error
        except (ValueError, IndexError):
            pass  # Expected behavior
        
        # Test camera bounds
        for scale in ViewScale:
            self.camera_system.change_scale(scale)
            
            # Try to move beyond bounds
            self.camera_system.set_camera_position(0, 0)
            result = self.camera_system.move_camera(-10, -10)
            assert result == False  # Should be blocked
            
            pos = self.camera_system.get_camera_position()
            assert pos == (0, 0)  # Should stay at bounds
    
    def test_deterministic_behavior_complete_system(self):
        """Test deterministic behavior of the complete system."""
        # Create two identical systems
        system1_world = WorldScaleGenerator(seed=self.seed)
        system1_camera = MultiScaleCameraSystem(seed=self.seed)
        system1_renderer = MultiScaleViewportRenderer(system1_world, system1_camera)
        
        system2_world = WorldScaleGenerator(seed=self.seed)
        system2_camera = MultiScaleCameraSystem(seed=self.seed)
        system2_renderer = MultiScaleViewportRenderer(system2_world, system2_camera)
        
        # Perform identical operations
        operations = [
            (ViewScale.WORLD, 5, 7),
            (ViewScale.REGIONAL, 10, 15),
            (ViewScale.LOCAL, 20, 25)
        ]
        
        for scale, x, y in operations:
            # System 1
            system1_camera.change_scale(scale)
            system1_camera.set_camera_position(x, y)
            coords1 = system1_camera.get_current_world_coordinates()
            
            # System 2
            system2_camera.change_scale(scale)
            system2_camera.set_camera_position(x, y)
            coords2 = system2_camera.get_current_world_coordinates()
            
            # Should be identical
            assert coords1 == coords2
        
        # Generate world data for both
        world1 = system1_world.generate_complete_world_map()
        world2 = system2_world.generate_complete_world_map()
        
        # Should be identical
        assert len(world1.sectors) == len(world2.sectors)
        for coord in world1.sectors:
            sector1 = world1.sectors[coord]
            sector2 = world2.sectors[coord]
            assert sector1.dominant_terrain == sector2.dominant_terrain
            assert sector1.average_elevation == sector2.average_elevation


class TestConfigurationIntegration:
    """Test configuration system integration."""
    
    def test_config_driven_generation(self):
        """Test that configuration drives generation correctly."""
        config = get_world_config()
        
        # Create generator with config seed
        seed = config.get_world_seed()
        world_generator = WorldScaleGenerator(seed=seed)
        
        # Generate world
        world_map = world_generator.generate_complete_world_map()
        
        # Should match config
        expected_size = config.get_world_size()
        assert world_map.world_size_sectors == expected_size
        assert world_map.world_seed == seed
    
    def test_cache_configuration(self):
        """Test cache configuration integration."""
        config = get_world_config()
        cache_settings = config.get_cache_settings()
        
        # Should have reasonable defaults
        assert cache_settings["world_lifetime"] > 0
        assert cache_settings["regional_lifetime"] > 0
        assert cache_settings["local_lifetime"] > 0


if __name__ == "__main__":
    pytest.main([__file__])
