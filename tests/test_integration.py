"""
Integration tests for the multi-scale world generation system.

This module tests the integration between all components of the
three-tier world generation system without requiring graphics.
"""

import pytest
import time
from unittest.mock import Mock, patch

from src.covenant.world.generators.world_scale import WorldScaleGenerator
from src.covenant.world.camera.multi_scale_camera import MultiScaleCameraSystem
from src.covenant.world.camera.viewport_renderer import MultiScaleViewportRenderer
from src.covenant.world.data.scale_types import ViewScale
from src.covenant.world.data.config import get_world_config


class TestSystemIntegration:
    """Test integration between all system components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.seed = 12345
        self.world_generator = WorldScaleGenerator(seed=self.seed)
        self.camera_system = MultiScaleCameraSystem(seed=self.seed)
        self.renderer = MultiScaleViewportRenderer(
            self.world_generator, 
            self.camera_system
        )
    
    def test_complete_world_generation_flow(self):
        """Test complete world generation and navigation flow."""
        # Start in local scale
        assert self.camera_system.get_current_scale() == ViewScale.LOCAL
        
        # Switch to world scale
        self.camera_system.change_scale(ViewScale.WORLD)
        assert self.camera_system.get_current_scale() == ViewScale.WORLD
        
        # Generate world data
        world_map = self.world_generator.generate_complete_world_map()
        assert world_map.is_complete()
        assert len(world_map.sectors) == 256  # 16x16 world
        
        # Navigate around world
        initial_pos = self.camera_system.get_camera_position()
        self.camera_system.move_camera(1, 1)
        new_pos = self.camera_system.get_camera_position()
        assert new_pos != initial_pos
        
        # Test coordinate conversion
        world_coords = self.camera_system.get_current_world_coordinates()
        assert isinstance(world_coords[0], int)
        assert isinstance(world_coords[1], int)
        
        # Switch to regional scale
        self.camera_system.change_scale(ViewScale.REGIONAL)
        assert self.camera_system.get_current_scale() == ViewScale.REGIONAL
        
        # Switch to local scale
        self.camera_system.change_scale(ViewScale.LOCAL)
        assert self.camera_system.get_current_scale() == ViewScale.LOCAL
    
    def test_renderer_integration(self):
        """Test renderer integration with world data."""
        # Generate world data
        world_map = self.world_generator.generate_complete_world_map()
        
        # Test rendering at different scales
        mock_console = Mock()
        mock_console.width = 80
        mock_console.height = 50
        
        for scale in ViewScale:
            self.camera_system.change_scale(scale)
            
            # Should not raise exceptions
            self.renderer.render_current_scale(mock_console)
            
            # Verify console was used
            assert mock_console.print.called
            mock_console.reset_mock()
    
    def test_world_info_generation(self):
        """Test world information generation."""
        # Generate world
        world_map = self.world_generator.generate_complete_world_map()
        
        # Get world info
        info = self.world_generator.get_world_info()
        
        assert info["status"] == "complete"
        assert info["seed"] == self.seed
        assert info["total_sectors"] == 256
        assert "terrain_distribution" in info
        assert "climate_distribution" in info
        assert isinstance(info["generation_time"], float)
        assert info["generation_time"] > 0
    
    def test_deterministic_behavior(self):
        """Test that the system behaves deterministically."""
        # Create two identical systems
        generator1 = WorldScaleGenerator(seed=self.seed)
        generator2 = WorldScaleGenerator(seed=self.seed)
        
        camera1 = MultiScaleCameraSystem(seed=self.seed)
        camera2 = MultiScaleCameraSystem(seed=self.seed)
        
        # Generate worlds
        world1 = generator1.generate_complete_world_map()
        world2 = generator2.generate_complete_world_map()
        
        # Should be identical
        assert world1.world_seed == world2.world_seed
        assert len(world1.sectors) == len(world2.sectors)
        
        # Test same movements
        camera1.change_scale(ViewScale.WORLD)
        camera2.change_scale(ViewScale.WORLD)
        
        camera1.move_camera(3, 5)
        camera2.move_camera(3, 5)
        
        assert camera1.get_camera_position() == camera2.get_camera_position()
        assert camera1.get_current_world_coordinates() == camera2.get_current_world_coordinates()
    
    def test_scale_transitions(self):
        """Test smooth transitions between scales."""
        # Start at world scale
        self.camera_system.change_scale(ViewScale.WORLD)
        self.camera_system.set_camera_position(5, 7)
        
        world_coords_from_world = self.camera_system.get_current_world_coordinates()
        
        # Switch to regional scale
        self.camera_system.change_scale(ViewScale.REGIONAL)
        
        # Center on the same world coordinates
        self.camera_system.center_camera_on_world_coordinates(*world_coords_from_world)
        
        # Should be in the correct region
        regional_pos = self.camera_system.get_camera_position()
        assert isinstance(regional_pos[0], int)
        assert isinstance(regional_pos[1], int)
        
        # Switch to local scale
        self.camera_system.change_scale(ViewScale.LOCAL)
        
        # Should maintain coordinate consistency
        local_world_coords = self.camera_system.get_current_world_coordinates()
        assert isinstance(local_world_coords[0], int)
        assert isinstance(local_world_coords[1], int)
    
    def test_movement_bounds(self):
        """Test movement bounds at all scales."""
        for scale in ViewScale:
            self.camera_system.change_scale(scale)
            
            # Move to corner
            self.camera_system.set_camera_position(0, 0)
            
            # Try to move beyond bounds
            result = self.camera_system.move_camera(-1, -1)
            assert result == False  # Movement should be blocked
            
            pos = self.camera_system.get_camera_position()
            assert pos == (0, 0)  # Should stay at bounds
    
    def test_performance_characteristics(self):
        """Test performance characteristics of the system."""
        start_time = time.time()
        
        # Generate complete world
        world_map = self.world_generator.generate_complete_world_map()
        
        generation_time = time.time() - start_time
        
        # Should complete in reasonable time (less than 5 seconds)
        assert generation_time < 5.0
        
        # Should have generated all sectors
        assert len(world_map.sectors) == 48  # 8×6
        
        # Test camera movement performance
        start_time = time.time()
        
        for scale in ViewScale:
            self.camera_system.change_scale(scale)
            for _ in range(100):  # 100 movements
                self.camera_system.move_camera(1, 0)
        
        movement_time = time.time() - start_time
        
        # Should be very fast (less than 0.1 seconds for 300 movements)
        assert movement_time < 0.1


class TestConfigurationSystem:
    """Test the configuration system."""
    
    def test_config_loading(self):
        """Test configuration loading."""
        config = get_world_config()
        
        # Should have default values
        seed = config.get_world_seed()
        assert isinstance(seed, int)
        
        world_size = config.get_world_size()
        assert isinstance(world_size, tuple)
        assert len(world_size) == 2
        assert world_size[0] > 0 and world_size[1] > 0
    
    def test_seed_consistency(self):
        """Test that same config produces same seeds."""
        config = get_world_config()
        
        seed1 = config.get_world_seed()
        seed2 = config.get_world_seed()
        
        # Should be consistent
        assert seed1 == seed2


if __name__ == "__main__":
    pytest.main([__file__])
