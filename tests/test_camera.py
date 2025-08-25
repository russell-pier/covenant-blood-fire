"""
Test suite for the camera system.

Tests camera movement, bounds checking, scale switching,
coordinate conversions, and multi-scale camera functionality.
"""

import pytest
from src.camera import Camera, MultiScaleCameraSystem
from src.world_types import ViewScale, Coordinate, WorldCoordinate, RegionalCoordinate


class TestCamera:
    """Test cases for the basic Camera class."""
    
    def test_camera_initialization(self):
        """Test camera initialization with default and custom parameters."""
        # Default initialization
        camera = Camera()
        assert camera.position == Coordinate(0, 0)
        assert camera.bounds_width == 100
        assert camera.bounds_height == 100
        
        # Custom initialization
        camera = Camera(
            initial_position=Coordinate(5, 10),
            bounds_width=50,
            bounds_height=75
        )
        assert camera.position == Coordinate(5, 10)
        assert camera.bounds_width == 50
        assert camera.bounds_height == 75
    
    def test_camera_movement(self):
        """Test camera movement with relative offsets."""
        camera = Camera(bounds_width=20, bounds_height=20)
        
        # Valid movement
        assert camera.move(5, 3) == True
        assert camera.position == Coordinate(5, 3)
        
        # Another valid movement
        assert camera.move(-2, 4) == True
        assert camera.position == Coordinate(3, 7)
        
        # Movement to edge
        assert camera.move(16, 12) == True
        assert camera.position == Coordinate(19, 19)
    
    def test_camera_bounds_checking(self):
        """Test camera movement bounds checking."""
        camera = Camera(bounds_width=10, bounds_height=10)
        
        # Move to edge
        camera.move_to(Coordinate(9, 9))
        assert camera.position == Coordinate(9, 9)
        
        # Try to move beyond bounds
        assert camera.move(1, 0) == False  # Would go to x=10
        assert camera.move(0, 1) == False  # Would go to y=10
        assert camera.move(-20, 0) == False  # Would go to x=-11
        
        # Position should remain unchanged
        assert camera.position == Coordinate(9, 9)
    
    def test_move_to_absolute(self):
        """Test absolute position movement."""
        camera = Camera(bounds_width=15, bounds_height=15)
        
        # Valid absolute movement
        assert camera.move_to(Coordinate(7, 12)) == True
        assert camera.position == Coordinate(7, 12)
        
        # Invalid absolute movement
        assert camera.move_to(Coordinate(20, 5)) == False
        assert camera.move_to(Coordinate(5, 20)) == False
        assert camera.move_to(Coordinate(-1, 5)) == False
        
        # Position should remain unchanged
        assert camera.position == Coordinate(7, 12)
    
    def test_position_validation(self):
        """Test position validation method."""
        camera = Camera(bounds_width=8, bounds_height=6)
        
        # Valid positions
        assert camera.is_position_valid(Coordinate(0, 0)) == True
        assert camera.is_position_valid(Coordinate(7, 5)) == True
        assert camera.is_position_valid(Coordinate(4, 3)) == True
        
        # Invalid positions
        assert camera.is_position_valid(Coordinate(8, 0)) == False
        assert camera.is_position_valid(Coordinate(0, 6)) == False
        assert camera.is_position_valid(Coordinate(-1, 0)) == False
        assert camera.is_position_valid(Coordinate(0, -1)) == False
    
    def test_view_bounds(self):
        """Test view bounds calculation."""
        camera = Camera(
            initial_position=Coordinate(10, 10),
            bounds_width=50,
            bounds_height=50,
            view_width=20,
            view_height=16
        )
        
        top_left, bottom_right = camera.get_view_bounds()
        
        # Should be centered around camera position
        expected_top_left = Coordinate(0, 2)  # max(0, 10-10), max(0, 10-8)
        expected_bottom_right = Coordinate(20, 18)  # min(49, 10+10), min(49, 10+8)
        
        assert top_left == expected_top_left
        assert bottom_right == expected_bottom_right
    
    def test_coordinate_conversion(self):
        """Test world to screen and screen to world coordinate conversion."""
        camera = Camera(
            initial_position=Coordinate(10, 10),
            view_width=20,
            view_height=20
        )
        
        # Test world to screen conversion
        screen_pos = camera.world_to_screen(Coordinate(15, 12))
        assert screen_pos == Coordinate(15, 12)  # 15-10+10, 12-10+10
        
        # Test screen to world conversion
        world_pos = camera.screen_to_world(Coordinate(15, 12))
        assert world_pos == Coordinate(15, 12)  # 15-10+10, 12-10+10
        
        # Test position outside view
        outside_pos = camera.world_to_screen(Coordinate(50, 50))
        assert outside_pos is None
    
    def test_center_on_target(self):
        """Test centering camera on target position."""
        camera = Camera(bounds_width=20, bounds_height=20)
        
        # Valid target
        assert camera.center_on(Coordinate(8, 12)) == True
        assert camera.position == Coordinate(8, 12)
        
        # Invalid target
        assert camera.center_on(Coordinate(25, 5)) == False
        assert camera.position == Coordinate(8, 12)  # Unchanged


class TestMultiScaleCameraSystem:
    """Test cases for the MultiScaleCameraSystem class."""
    
    def test_multi_camera_initialization(self):
        """Test multi-scale camera system initialization."""
        multi_cam = MultiScaleCameraSystem()
        
        # Check initial state
        assert multi_cam.current_scale == ViewScale.WORLD
        assert multi_cam.selected_sector.x == 32  # WORLD_SECTORS_X // 2 (64//2)
        assert multi_cam.selected_sector.y == 24  # WORLD_SECTORS_Y // 2 (48//2)
        
        # Check cameras are initialized (cursor cameras start with cursor at center)
        world_cursor = multi_cam.world_camera.get_cursor_world_position()
        assert world_cursor.x == 32  # WORLD_SECTORS_X // 2
        assert world_cursor.y == 24  # WORLD_SECTORS_Y // 2

        regional_cursor = multi_cam.regional_camera.get_cursor_world_position()
        assert regional_cursor.x == 16  # REGIONAL_BLOCKS_SIZE // 2
        assert regional_cursor.y == 16  # REGIONAL_BLOCKS_SIZE // 2

        local_cursor = multi_cam.local_camera.get_cursor_world_position()
        assert local_cursor.x == 16  # LOCAL_CHUNKS_SIZE // 2
        assert local_cursor.y == 16  # LOCAL_CHUNKS_SIZE // 2
    
    def test_current_camera_selection(self):
        """Test getting current camera based on scale."""
        multi_cam = MultiScaleCameraSystem()
        
        # World scale
        assert multi_cam.get_current_camera() == multi_cam.world_camera
        
        # Regional scale
        multi_cam.current_scale = ViewScale.REGIONAL
        assert multi_cam.get_current_camera() == multi_cam.regional_camera
        
        # Local scale
        multi_cam.current_scale = ViewScale.LOCAL
        assert multi_cam.get_current_camera() == multi_cam.local_camera
    
    def test_scale_switching(self):
        """Test switching between different scales."""
        multi_cam = MultiScaleCameraSystem()
        
        # Switch to regional
        assert multi_cam.switch_to_scale(ViewScale.REGIONAL) == True
        assert multi_cam.current_scale == ViewScale.REGIONAL
        
        # Switch to local
        assert multi_cam.switch_to_scale(ViewScale.LOCAL) == True
        assert multi_cam.current_scale == ViewScale.LOCAL
        
        # Switch back to world
        assert multi_cam.switch_to_scale(ViewScale.WORLD) == True
        assert multi_cam.current_scale == ViewScale.WORLD
        
        # Switch to same scale (should succeed)
        assert multi_cam.switch_to_scale(ViewScale.WORLD) == True
        assert multi_cam.current_scale == ViewScale.WORLD
    
    def test_scale_switching_preserves_positions(self):
        """Test that scale switching preserves relative positions."""
        multi_cam = MultiScaleCameraSystem()
        
        # Move world camera
        multi_cam.world_camera.move_to(Coordinate(2, 1))
        
        # Switch to regional - should update selected sector
        multi_cam.switch_to_scale(ViewScale.REGIONAL)
        assert multi_cam.selected_sector == WorldCoordinate(2, 1)
        
        # Move regional camera
        multi_cam.regional_camera.move_to(Coordinate(10, 15))
        
        # Switch to local - should update selected block
        multi_cam.switch_to_scale(ViewScale.LOCAL)
        assert multi_cam.selected_block == RegionalCoordinate(10, 15)
    
    def test_current_camera_movement(self):
        """Test moving the current scale's camera."""
        multi_cam = MultiScaleCameraSystem()
        
        # Move world camera (now moves cursor, not camera directly)
        initial_cursor = multi_cam.world_camera.get_cursor_world_position()
        assert multi_cam.move_current_camera(2, -1) == True
        new_cursor = multi_cam.world_camera.get_cursor_world_position()
        assert new_cursor == Coordinate(initial_cursor.x + 2, initial_cursor.y - 1)
        
        # Switch to regional and move (now moves cursor)
        multi_cam.switch_to_scale(ViewScale.REGIONAL)
        initial_cursor = multi_cam.regional_camera.get_cursor_world_position()
        assert multi_cam.move_current_camera(3, 4) == True  # Use positive values to avoid bounds issues
        new_cursor = multi_cam.regional_camera.get_cursor_world_position()
        assert new_cursor == Coordinate(initial_cursor.x + 3, initial_cursor.y + 4)
    
    def test_position_info(self):
        """Test getting current position information."""
        multi_cam = MultiScaleCameraSystem()
        
        # World scale info
        info = multi_cam.get_current_position_info()
        assert info['scale'] == 'WORLD'
        assert 'World View' in info['description']
        assert info['camera_position'] == multi_cam.world_camera.position
        
        # Regional scale info
        multi_cam.switch_to_scale(ViewScale.REGIONAL)
        info = multi_cam.get_current_position_info()
        assert info['scale'] == 'REGIONAL'
        assert 'Regional View' in info['description']
        
        # Local scale info
        multi_cam.switch_to_scale(ViewScale.LOCAL)
        info = multi_cam.get_current_position_info()
        assert info['scale'] == 'LOCAL'
        assert 'Local View' in info['description']
    
    def test_absolute_coordinates(self):
        """Test absolute coordinate calculation."""
        multi_cam = MultiScaleCameraSystem()
        
        # World scale - should return camera position directly
        abs_x, abs_y = multi_cam.get_absolute_coordinates()
        assert abs_x == float(multi_cam.world_camera.position.x)
        assert abs_y == float(multi_cam.world_camera.position.y)
        
        # Regional scale - should include sector offset
        multi_cam.switch_to_scale(ViewScale.REGIONAL)
        multi_cam.selected_sector = WorldCoordinate(2, 1)
        multi_cam.regional_camera.move_to(Coordinate(5, 8))
        
        abs_x, abs_y = multi_cam.get_absolute_coordinates()
        expected_x = 2 * 32 + 5  # sector * REGIONAL_BLOCKS_SIZE + block
        expected_y = 1 * 32 + 8
        assert abs_x == expected_x
        assert abs_y == expected_y
        
        # Local scale - should include sector and block offsets
        multi_cam.switch_to_scale(ViewScale.LOCAL)
        multi_cam.selected_block = RegionalCoordinate(3, 7)
        multi_cam.local_camera.move_to(Coordinate(12, 20))
        
        abs_x, abs_y = multi_cam.get_absolute_coordinates()
        expected_x = 2 * 32 * 32 + 3 * 32 + 12  # sector * regional * local + block * local + chunk
        expected_y = 1 * 32 * 32 + 7 * 32 + 20
        assert abs_x == expected_x
        assert abs_y == expected_y


class TestCameraIntegration:
    """Integration tests for camera system."""
    
    def test_camera_bounds_match_world_size(self):
        """Test that camera bounds match expected world dimensions."""
        multi_cam = MultiScaleCameraSystem()
        
        # World camera bounds should match world sectors
        assert multi_cam.world_camera.bounds_width == 64  # WORLD_SECTORS_X
        assert multi_cam.world_camera.bounds_height == 48  # WORLD_SECTORS_Y
        
        # Regional camera bounds should match regional blocks
        assert multi_cam.regional_camera.bounds_width == 32  # REGIONAL_BLOCKS_SIZE
        assert multi_cam.regional_camera.bounds_height == 32
        
        # Local camera bounds should match local chunks
        assert multi_cam.local_camera.bounds_width == 32  # LOCAL_CHUNKS_SIZE
        assert multi_cam.local_camera.bounds_height == 32
    
    def test_full_navigation_workflow(self):
        """Test complete navigation workflow across scales."""
        multi_cam = MultiScaleCameraSystem()
        
        # Start at world scale, move to a sector
        assert multi_cam.move_current_camera(1, -1) == True
        world_pos = multi_cam.world_camera.position
        
        # Switch to regional scale
        multi_cam.switch_to_scale(ViewScale.REGIONAL)
        assert multi_cam.selected_sector == WorldCoordinate(world_pos.x, world_pos.y)
        
        # Move within the sector
        assert multi_cam.move_current_camera(5, 3) == True
        regional_pos = multi_cam.regional_camera.position
        
        # Switch to local scale
        multi_cam.switch_to_scale(ViewScale.LOCAL)
        assert multi_cam.selected_block == RegionalCoordinate(regional_pos.x, regional_pos.y)
        
        # Move within the block
        assert multi_cam.move_current_camera(-2, 4) == True
        
        # Verify absolute coordinates make sense
        abs_x, abs_y = multi_cam.get_absolute_coordinates()
        assert abs_x >= 0
        assert abs_y >= 0


if __name__ == "__main__":
    # Run basic tests when called directly
    print("Running camera system tests...")
    
    # Test basic camera
    camera = Camera(bounds_width=10, bounds_height=10)
    if camera.move(3, 4):
        print("✓ Basic camera movement works")
    else:
        print("✗ Basic camera movement failed")
    
    # Test bounds
    if not camera.move(20, 20):
        print("✓ Camera bounds checking works")
    else:
        print("✗ Camera bounds checking failed")
    
    # Test multi-scale system
    multi_cam = MultiScaleCameraSystem()
    if multi_cam.switch_to_scale(ViewScale.REGIONAL):
        print("✓ Scale switching works")
    else:
        print("✗ Scale switching failed")
    
    print("Basic camera tests completed!")
