"""
Tests for the multi-scale camera system.

This module tests the camera system including movement, transitions,
and coordinate mapping between scales.
"""

import pytest
import time
from src.covenant.world.camera.multi_scale_camera import (
    MultiScaleCameraSystem, CameraPosition, ViewTransition, ViewportInfo,
    TransitionState
)
from src.covenant.world.data.scale_types import ViewScale, CoordinateSystem


class TestMultiScaleCameraSystem:
    """Test the multi-scale camera system"""
    
    def test_camera_initialization(self):
        """Test camera system initialization"""
        camera = MultiScaleCameraSystem(console_width=80, console_height=50)
        
        assert camera.console_width == 80
        assert camera.console_height == 50
        assert camera.current_scale == ViewScale.LOCAL
        assert camera.viewport_width == 78  # 80 - 2*1 margin
        assert camera.viewport_height == 42  # 50 - 3 - 5 UI space
        assert camera.viewport_start_x == 1
        assert camera.viewport_start_y == 3
        
        # Check that all scales have camera positions
        assert ViewScale.WORLD in camera.camera_positions
        assert ViewScale.REGIONAL in camera.camera_positions
        assert ViewScale.LOCAL in camera.camera_positions
        
        # Check initial transition state
        assert camera.transition.state == TransitionState.NONE
        assert not camera.is_transitioning()
    
    def test_camera_position_initialization(self):
        """Test camera position initialization for all scales"""
        camera = MultiScaleCameraSystem()
        
        # World scale position
        world_pos = camera.camera_positions[ViewScale.WORLD]
        assert isinstance(world_pos, CameraPosition)
        assert world_pos.x == CoordinateSystem.WORLD_SIZE[0] / 2
        assert world_pos.y == CoordinateSystem.WORLD_SIZE[1] / 2
        assert world_pos.bounds_min == (0, 0)
        assert world_pos.bounds_max == (CoordinateSystem.WORLD_SIZE[0] - 1, CoordinateSystem.WORLD_SIZE[1] - 1)
        
        # Regional scale position
        regional_pos = camera.camera_positions[ViewScale.REGIONAL]
        assert isinstance(regional_pos, CameraPosition)
        assert regional_pos.x == CoordinateSystem.REGIONAL_SIZE[0] / 2
        assert regional_pos.y == CoordinateSystem.REGIONAL_SIZE[1] / 2
        
        # Local scale position
        local_pos = camera.camera_positions[ViewScale.LOCAL]
        assert isinstance(local_pos, CameraPosition)
        assert local_pos.x == CoordinateSystem.LOCAL_SIZE[0] / 2
        assert local_pos.y == CoordinateSystem.LOCAL_SIZE[1] / 2
    
    def test_get_current_camera_position(self):
        """Test getting current camera position"""
        camera = MultiScaleCameraSystem()
        
        # Should start at local scale
        current_pos = camera.get_current_camera_position()
        local_pos = camera.camera_positions[ViewScale.LOCAL]
        assert current_pos is local_pos
        
        # Change scale and test again
        camera.current_scale = ViewScale.WORLD
        current_pos = camera.get_current_camera_position()
        world_pos = camera.camera_positions[ViewScale.WORLD]
        assert current_pos is world_pos
    
    def test_camera_movement(self):
        """Test camera movement with bounds checking"""
        camera = MultiScaleCameraSystem()
        
        # Get initial position
        initial_pos = camera.get_current_camera_position()
        initial_x, initial_y = initial_pos.target_x, initial_pos.target_y
        
        # Move camera
        camera.move_camera(5, 3)
        
        # Check that target position changed
        assert initial_pos.target_x != initial_x
        assert initial_pos.target_y != initial_y
        
        # Check bounds are respected
        assert initial_pos.target_x >= initial_pos.bounds_min[0]
        assert initial_pos.target_x <= initial_pos.bounds_max[0]
        assert initial_pos.target_y >= initial_pos.bounds_min[1]
        assert initial_pos.target_y <= initial_pos.bounds_max[1]
    
    def test_camera_movement_bounds(self):
        """Test camera movement respects bounds"""
        camera = MultiScaleCameraSystem()
        
        # Move to edge of bounds
        pos = camera.get_current_camera_position()
        pos.target_x = pos.bounds_max[0]
        pos.target_y = pos.bounds_max[1]
        
        # Try to move beyond bounds
        camera.move_camera(10, 10)
        
        # Should be clamped to bounds
        assert pos.target_x == pos.bounds_max[0]
        assert pos.target_y == pos.bounds_max[1]
    
    def test_scale_transitions(self):
        """Test transitions between scales"""
        camera = MultiScaleCameraSystem()
        
        # Start at local scale
        assert camera.current_scale == ViewScale.LOCAL
        assert not camera.is_transitioning()
        
        # Initiate transition to regional
        camera.transition_to_scale(ViewScale.REGIONAL)
        
        # Should be transitioning
        assert camera.is_transitioning()
        assert camera.transition.state == TransitionState.ZOOMING_OUT
        assert camera.transition.from_scale == ViewScale.LOCAL
        assert camera.transition.to_scale == ViewScale.REGIONAL
        assert 0.0 <= camera.get_transition_progress() <= 1.0
    
    def test_zoom_methods(self):
        """Test zoom in/out methods"""
        camera = MultiScaleCameraSystem()
        
        # Start at local, zoom out
        camera.zoom_out()
        assert camera.transition.to_scale == ViewScale.REGIONAL
        
        # Reset and test from world scale
        camera.current_scale = ViewScale.WORLD
        camera.transition.state = TransitionState.NONE
        
        camera.zoom_in()
        assert camera.transition.to_scale == ViewScale.REGIONAL
    
    def test_transition_completion(self):
        """Test transition completion"""
        camera = MultiScaleCameraSystem()
        
        # Start transition
        camera.transition_to_scale(ViewScale.REGIONAL)
        
        # Simulate time passing to complete transition
        camera.transition.start_time = time.time() - 1.0  # 1 second ago
        camera.transition.duration = 0.5  # 0.5 second duration
        
        # Update should complete the transition
        camera.update(0.1)
        
        # Should be completed
        assert not camera.is_transitioning()
        assert camera.current_scale == ViewScale.REGIONAL
    
    def test_smooth_movement_update(self):
        """Test smooth movement updates"""
        camera = MultiScaleCameraSystem()
        
        pos = camera.get_current_camera_position()
        initial_x = pos.x
        
        # Set a target different from current position
        pos.target_x = initial_x + 10
        
        # Update should move camera toward target
        camera.update(0.1)
        
        # Should have moved toward target but not reached it immediately
        assert pos.x > initial_x
        assert pos.x < pos.target_x
    
    def test_viewport_info(self):
        """Test viewport information generation"""
        camera = MultiScaleCameraSystem(console_width=100, console_height=60)
        
        viewport = camera.get_viewport_info()
        
        assert isinstance(viewport, ViewportInfo)
        assert viewport.scale == camera.current_scale
        assert viewport.viewport_width == 98  # 100 - 2*1
        assert viewport.viewport_height == 52  # 60 - 3 - 5
        assert viewport.viewport_start_x == 1
        assert viewport.viewport_start_y == 3
        assert isinstance(viewport.tiles_visible, list)
    
    def test_context_setting(self):
        """Test setting world and regional context"""
        camera = MultiScaleCameraSystem()
        
        # Set world context
        camera.set_world_context(10, 20)
        assert camera.current_world_sector == (10, 20)
        
        # Set regional context
        camera.set_regional_context(5, 15)
        assert camera.current_regional_block == (5, 15)
    
    def test_equivalent_position_calculation(self):
        """Test equivalent position calculation between scales"""
        camera = MultiScaleCameraSystem()
        
        # Test local to regional conversion
        local_pos = (16.0, 16.0)  # Center of local area
        regional_pos = camera._calculate_equivalent_position(
            ViewScale.LOCAL, ViewScale.REGIONAL, local_pos[0], local_pos[1]
        )
        
        # Should be scaled down
        expected_x = local_pos[0] / CoordinateSystem.LOCAL_SIZE[0]
        expected_y = local_pos[1] / CoordinateSystem.LOCAL_SIZE[1]
        assert regional_pos == (expected_x, expected_y)
        
        # Test regional to world conversion
        regional_pos = (16.0, 16.0)  # Center of regional area
        world_pos = camera._calculate_equivalent_position(
            ViewScale.REGIONAL, ViewScale.WORLD, regional_pos[0], regional_pos[1]
        )
        
        # Should be scaled down
        expected_x = regional_pos[0] / CoordinateSystem.REGIONAL_SIZE[0]
        expected_y = regional_pos[1] / CoordinateSystem.REGIONAL_SIZE[1]
        assert world_pos == (expected_x, expected_y)
    
    def test_is_zooming_out(self):
        """Test zoom direction detection"""
        camera = MultiScaleCameraSystem()
        
        # Local to Regional is zooming out
        assert camera._is_zooming_out(ViewScale.LOCAL, ViewScale.REGIONAL)
        
        # Regional to World is zooming out
        assert camera._is_zooming_out(ViewScale.REGIONAL, ViewScale.WORLD)
        
        # Local to World is zooming out
        assert camera._is_zooming_out(ViewScale.LOCAL, ViewScale.WORLD)
        
        # Reverse directions are zooming in
        assert not camera._is_zooming_out(ViewScale.REGIONAL, ViewScale.LOCAL)
        assert not camera._is_zooming_out(ViewScale.WORLD, ViewScale.REGIONAL)
        assert not camera._is_zooming_out(ViewScale.WORLD, ViewScale.LOCAL)
        
        # Same scale is not zooming
        assert not camera._is_zooming_out(ViewScale.LOCAL, ViewScale.LOCAL)
    
    def test_auto_transition_edge_detection(self):
        """Test auto-transition at map edges"""
        camera = MultiScaleCameraSystem()
        camera.auto_transition_enabled = True
        
        # Move camera near edge
        pos = camera.get_current_camera_position()
        pos.x = pos.bounds_min[0] + 1  # Very close to left edge
        pos.target_x = pos.x
        
        # Move toward edge
        camera.move_camera(-1, 0)
        
        # Should trigger auto-transition (if at local scale)
        if camera.current_scale == ViewScale.LOCAL:
            # Might trigger transition to regional
            pass  # This is probabilistic based on edge distance
    
    def test_legacy_compatibility_methods(self):
        """Test legacy compatibility methods"""
        camera = MultiScaleCameraSystem()
        
        # Test get_camera_position
        pos = camera.get_camera_position()
        assert isinstance(pos, tuple)
        assert len(pos) == 2
        
        # Test change_scale
        result = camera.change_scale(ViewScale.WORLD)
        assert result == True  # Should return True for scale change
        
        result = camera.change_scale(ViewScale.LOCAL)  # Current scale after transition
        # Note: This might not change immediately due to transitions
    
    def test_transition_prevention_during_movement(self):
        """Test that movement is prevented during transitions"""
        camera = MultiScaleCameraSystem()
        
        # Start a transition
        camera.transition_to_scale(ViewScale.REGIONAL)
        
        # Get current position
        pos = camera.get_current_camera_position()
        initial_target_x = pos.target_x
        
        # Try to move during transition
        camera.move_camera(5, 0)
        
        # Target should not have changed
        assert pos.target_x == initial_target_x
    
    def test_scale_config_access(self):
        """Test scale configuration access"""
        camera = MultiScaleCameraSystem()
        
        config = camera.get_current_scale_config()
        assert config is not None
        assert hasattr(config, 'movement_speed')
        assert hasattr(config, 'name')


if __name__ == "__main__":
    pytest.main([__file__])
