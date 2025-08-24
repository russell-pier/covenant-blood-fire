"""
Tests for multi-scale camera system.

This module tests the camera system and viewport renderer
for the three-tier world generation system.
"""

import pytest
import time
from unittest.mock import Mock, MagicMock

from src.covenant.world.camera.multi_scale_camera import MultiScaleCameraSystem
from src.covenant.world.camera.viewport_renderer import MultiScaleViewportRenderer
from src.covenant.world.data.scale_types import ViewScale
from src.covenant.world.generators.world_scale import WorldScaleGenerator


class TestMultiScaleCameraSystem:
    """Test the multi-scale camera system."""
    
    def test_initialization(self):
        """Test camera system initialization."""
        camera = MultiScaleCameraSystem(seed=12345)
        
        assert camera.get_current_scale() == ViewScale.LOCAL
        assert camera.get_camera_position() == (16, 16)  # Center of local view
        assert camera.movement_velocity == 0.0
        assert camera.scale_change_count == 0
    
    def test_scale_switching(self):
        """Test switching between scales."""
        camera = MultiScaleCameraSystem(seed=12345)
        
        # Test switching to world scale
        assert camera.change_scale(ViewScale.WORLD) == True
        assert camera.get_current_scale() == ViewScale.WORLD
        assert camera.scale_change_count == 1
        
        # Test switching to same scale (should return False)
        assert camera.change_scale(ViewScale.WORLD) == False
        assert camera.scale_change_count == 1
        
        # Test switching to regional scale
        assert camera.change_scale(ViewScale.REGIONAL) == True
        assert camera.get_current_scale() == ViewScale.REGIONAL
        assert camera.scale_change_count == 2
        
        # Test switching back to local
        assert camera.change_scale(ViewScale.LOCAL) == True
        assert camera.get_current_scale() == ViewScale.LOCAL
        assert camera.scale_change_count == 3
    
    def test_camera_movement(self):
        """Test camera movement within bounds."""
        camera = MultiScaleCameraSystem(seed=12345)
        
        # Test movement in local scale (32x32)
        camera.change_scale(ViewScale.LOCAL)
        initial_x, initial_y = camera.get_camera_position()
        
        # Move right
        assert camera.move_camera(1, 0) == True
        new_x, new_y = camera.get_camera_position()
        assert new_x == initial_x + 1
        assert new_y == initial_y
        
        # Move down
        assert camera.move_camera(0, 1) == True
        new_x, new_y = camera.get_camera_position()
        assert new_x == initial_x + 1
        assert new_y == initial_y + 1
        
        # Test movement velocity tracking
        assert camera.movement_velocity > 0
        assert camera.total_distance_moved > 0
    
    def test_movement_bounds(self):
        """Test camera movement bounds checking."""
        camera = MultiScaleCameraSystem(seed=12345)
        
        # Test world scale bounds (16x16)
        camera.change_scale(ViewScale.WORLD)
        camera.set_camera_position(0, 0)  # Top-left corner
        
        # Try to move beyond bounds
        assert camera.move_camera(-1, -1) == False  # Should be blocked
        x, y = camera.get_camera_position()
        assert x == 0 and y == 0  # Should stay at bounds
        
        # Move to bottom-right corner
        camera.set_camera_position(15, 15)
        assert camera.move_camera(1, 1) == False  # Should be blocked
        x, y = camera.get_camera_position()
        assert x == 15 and y == 15  # Should stay at bounds
    
    def test_coordinate_conversion(self):
        """Test coordinate conversion between scales and world coordinates."""
        camera = MultiScaleCameraSystem(seed=12345)
        
        # Test world scale conversion
        camera.change_scale(ViewScale.WORLD)
        camera.set_camera_position(1, 1)
        world_x, world_y = camera.get_current_world_coordinates()
        assert world_x == 16384  # 1 * 16384
        assert world_y == 16384
        
        # Test regional scale conversion
        camera.change_scale(ViewScale.REGIONAL)
        camera.set_camera_position(2, 3)
        world_x, world_y = camera.get_current_world_coordinates()
        assert world_x == 2048  # 2 * 1024
        assert world_y == 3072  # 3 * 1024
        
        # Test local scale conversion
        camera.change_scale(ViewScale.LOCAL)
        camera.set_camera_position(5, 7)
        world_x, world_y = camera.get_current_world_coordinates()
        assert world_x == 160  # 5 * 32
        assert world_y == 224  # 7 * 32
    
    def test_center_on_world_coordinates(self):
        """Test centering camera on world coordinates."""
        camera = MultiScaleCameraSystem(seed=12345)
        
        # Test centering in world scale
        camera.change_scale(ViewScale.WORLD)
        camera.center_camera_on_world_coordinates(32768, 49152)  # 2*16384, 3*16384
        x, y = camera.get_camera_position()
        assert x == 2
        assert y == 3
        
        # Test centering in regional scale
        camera.change_scale(ViewScale.REGIONAL)
        camera.center_camera_on_world_coordinates(3072, 4096)  # 3*1024, 4*1024
        x, y = camera.get_camera_position()
        assert x == 3
        assert y == 4
    
    def test_position_reset(self):
        """Test camera position reset functionality."""
        camera = MultiScaleCameraSystem(seed=12345)
        
        # Move camera away from center
        camera.change_scale(ViewScale.WORLD)
        camera.set_camera_position(0, 0)
        
        # Reset position
        camera.reset_position()
        x, y = camera.get_camera_position()
        assert x == 8  # Center of 16x16 world
        assert y == 8
        
        # Test reset all positions
        camera.change_scale(ViewScale.LOCAL)
        camera.set_camera_position(0, 0)
        camera.reset_all_positions()
        
        # Check all scales are centered
        camera.change_scale(ViewScale.WORLD)
        x, y = camera.get_camera_position()
        assert x == 4 and y == 3  # Center of 8×6 world
        
        camera.change_scale(ViewScale.REGIONAL)
        x, y = camera.get_camera_position()
        assert x == 16 and y == 16  # Center of 32x32 regional
        
        camera.change_scale(ViewScale.LOCAL)
        x, y = camera.get_camera_position()
        assert x == 16 and y == 16  # Center of 32x32 local
    
    def test_movement_stats(self):
        """Test movement statistics tracking."""
        camera = MultiScaleCameraSystem(seed=12345)
        
        # Initial stats
        stats = camera.get_movement_stats()
        assert stats["current_scale"] == "local"
        assert stats["total_distance_moved"] == 0.0
        assert stats["scale_changes"] == 0
        
        # Move camera and change scale
        camera.move_camera(5, 3)
        camera.change_scale(ViewScale.WORLD)
        
        stats = camera.get_movement_stats()
        assert stats["current_scale"] == "world"
        assert stats["total_distance_moved"] > 0
        assert stats["scale_changes"] == 1
        assert "current_position" in stats
        assert "world_coordinates" in stats


class TestMultiScaleViewportRenderer:
    """Test the multi-scale viewport renderer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.world_generator = WorldScaleGenerator(seed=12345)
        self.camera_system = MultiScaleCameraSystem(seed=12345)
        self.renderer = MultiScaleViewportRenderer(
            self.world_generator, 
            self.camera_system
        )
    
    def test_initialization(self):
        """Test renderer initialization."""
        assert self.renderer.console_width == 80
        assert self.renderer.console_height == 50
        assert self.renderer.render_start_y > 0
        assert self.renderer.render_end_y < 50
        assert self.renderer.render_height > 0
        assert self.renderer.render_width == 80
    
    def test_console_size_update(self):
        """Test console size update for responsive design."""
        self.renderer.update_console_size(100, 60)
        
        assert self.renderer.console_width == 100
        assert self.renderer.console_height == 60
        assert self.renderer.render_width == 100
        
        # Check that rendering area was recalculated
        expected_render_height = 60 - self.renderer.status_bar_height - self.renderer.instructions_height - 2 * self.renderer.ui_margin
        assert self.renderer.render_height == expected_render_height
    
    def test_render_bounds(self):
        """Test render bounds calculation."""
        bounds = self.renderer.get_render_bounds()
        start_x, start_y, end_x, end_y = bounds
        
        assert start_x == 0
        assert start_y == self.renderer.render_start_y
        assert end_x == self.renderer.render_width
        assert end_y == self.renderer.render_end_y
        assert start_y < end_y
        assert start_x < end_x
    
    def test_render_current_scale_mock(self):
        """Test rendering with mocked console."""
        # Create a mock console
        mock_console = Mock()
        mock_console.width = 80
        mock_console.height = 50
        
        # Test rendering at different scales
        scales_to_test = [ViewScale.WORLD, ViewScale.REGIONAL, ViewScale.LOCAL]
        
        for scale in scales_to_test:
            self.camera_system.change_scale(scale)
            
            # This should not raise an exception
            self.renderer.render_current_scale(mock_console)
            
            # Verify that print was called (console was used)
            assert mock_console.print.called
            mock_console.reset_mock()
    
    def test_world_view_rendering_logic(self):
        """Test world view rendering logic without actual console."""
        self.camera_system.change_scale(ViewScale.WORLD)
        self.camera_system.set_camera_position(5, 7)
        
        # Generate world data
        world_map = self.world_generator.generate_complete_world_map()
        
        # Test that we can access the data needed for rendering
        assert world_map.world_size_sectors == (16, 16)
        assert len(world_map.sectors) == 256
        
        # Test that camera position is valid
        camera_x, camera_y = self.camera_system.get_camera_position()
        assert 0 <= camera_x < 16
        assert 0 <= camera_y < 16
        
        # Test that we can get sector data for camera position
        sector_data = world_map.get_sector(camera_x, camera_y)
        assert sector_data is not None
        assert hasattr(sector_data, 'display_char')
        assert hasattr(sector_data, 'display_color')
        assert hasattr(sector_data, 'display_bg_color')


if __name__ == "__main__":
    pytest.main([__file__])
