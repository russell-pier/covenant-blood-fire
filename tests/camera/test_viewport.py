"""
Tests for the camera and viewport system.
"""

import pytest
import tcod

from src.empires.camera.viewport import (
    CameraConfig,
    Camera,
    Viewport,
    create_default_camera,
    create_viewport_system
)


class TestCameraConfig:
    """Test the CameraConfig dataclass."""
    
    def test_default_values(self):
        """Test that CameraConfig has expected default values."""
        config = CameraConfig()
        
        assert config.crosshair_x == 40
        assert config.crosshair_y == 25
        assert config.movement_speed == 1
        assert config.smooth_scrolling is False
    
    def test_custom_values(self):
        """Test that CameraConfig accepts custom values."""
        config = CameraConfig(
            crosshair_x=50,
            crosshair_y=30,
            movement_speed=2,
            smooth_scrolling=True
        )
        
        assert config.crosshair_x == 50
        assert config.crosshair_y == 30
        assert config.movement_speed == 2
        assert config.smooth_scrolling is True


class TestCamera:
    """Test the Camera class."""
    
    def test_initialization_default_config(self):
        """Test camera initialization with default config."""
        camera = Camera()
        
        assert camera.world_x == 0
        assert camera.world_y == 0
        assert camera.screen_width == 80
        assert camera.screen_height == 50
        assert camera.config.crosshair_x == 40
        assert camera.config.crosshair_y == 25
    
    def test_initialization_custom_config(self):
        """Test camera initialization with custom config."""
        config = CameraConfig(crosshair_x=30, crosshair_y=20)
        camera = Camera(config)
        
        assert camera.config.crosshair_x == 30
        assert camera.config.crosshair_y == 20
    
    def test_move(self):
        """Test camera movement."""
        camera = Camera()
        
        # Initial position
        assert camera.get_position() == (0, 0)
        
        # Move right and down
        camera.move(5, 3)
        assert camera.get_position() == (5, 3)
        
        # Move left and up
        camera.move(-2, -1)
        assert camera.get_position() == (3, 2)
    
    def test_move_with_speed(self):
        """Test camera movement with different speeds."""
        config = CameraConfig(movement_speed=3)
        camera = Camera(config)
        
        camera.move(2, 1)
        assert camera.get_position() == (6, 3)  # 2*3, 1*3
    
    def test_set_position(self):
        """Test setting camera position directly."""
        camera = Camera()
        
        camera.set_position(100, -50)
        assert camera.get_position() == (100, -50)
        
        camera.set_position(0, 0)
        assert camera.get_position() == (0, 0)
    
    def test_screen_to_world(self):
        """Test converting screen coordinates to world coordinates."""
        camera = Camera()
        camera.set_position(10, 20)
        
        # Crosshair position should map to camera position
        world_x, world_y = camera.screen_to_world(40, 25)
        assert world_x == 10
        assert world_y == 20
        
        # Top-left corner
        world_x, world_y = camera.screen_to_world(0, 0)
        assert world_x == 10 - 40  # camera_x - crosshair_x
        assert world_y == 20 - 25  # camera_y - crosshair_y
        
        # Bottom-right corner
        world_x, world_y = camera.screen_to_world(79, 49)
        assert world_x == 10 + (79 - 40)
        assert world_y == 20 + (49 - 25)
    
    def test_world_to_screen(self):
        """Test converting world coordinates to screen coordinates."""
        camera = Camera()
        camera.set_position(10, 20)
        
        # Camera position should map to crosshair position
        screen_x, screen_y = camera.world_to_screen(10, 20)
        assert screen_x == 40
        assert screen_y == 25
        
        # Test other positions
        screen_x, screen_y = camera.world_to_screen(15, 25)
        assert screen_x == 45
        assert screen_y == 30
        
        screen_x, screen_y = camera.world_to_screen(5, 15)
        assert screen_x == 35
        assert screen_y == 20
    
    def test_is_position_visible(self):
        """Test checking if world positions are visible."""
        camera = Camera()
        camera.set_position(40, 25)  # Center camera at crosshair world position
        
        # Crosshair position should be visible
        assert camera.is_position_visible(40, 25) is True
        
        # Corners should be visible
        min_x, min_y, max_x, max_y = camera.get_visible_world_bounds()
        assert camera.is_position_visible(min_x, min_y) is True
        assert camera.is_position_visible(max_x, max_y) is True
        
        # Far away positions should not be visible
        assert camera.is_position_visible(1000, 1000) is False
        assert camera.is_position_visible(-1000, -1000) is False
    
    def test_get_visible_world_bounds(self):
        """Test getting visible world bounds."""
        camera = Camera()
        camera.set_position(0, 0)
        
        min_x, min_y, max_x, max_y = camera.get_visible_world_bounds()
        
        # Check that bounds make sense
        assert min_x < max_x
        assert min_y < max_y
        
        # Check that crosshair position is within bounds
        assert min_x <= 0 <= max_x
        assert min_y <= 0 <= max_y
        
        # Check specific values based on screen size and crosshair position
        expected_min_x = 0 - 40  # camera_x - crosshair_x
        expected_min_y = 0 - 25  # camera_y - crosshair_y
        expected_max_x = 0 + (80 - 1 - 40)  # camera_x + (screen_width - 1 - crosshair_x)
        expected_max_y = 0 + (50 - 1 - 25)  # camera_y + (screen_height - 1 - crosshair_y)
        
        assert min_x == expected_min_x
        assert min_y == expected_min_y
        assert max_x == expected_max_x
        assert max_y == expected_max_y


class TestViewport:
    """Test the Viewport class."""
    
    def test_initialization(self):
        """Test viewport initialization."""
        camera = Camera()
        viewport = Viewport(camera)
        
        assert viewport.camera is camera
    
    def test_render_crosshair(self):
        """Test rendering the crosshair."""
        camera = Camera()
        viewport = Viewport(camera)
        console = tcod.console.Console(80, 50)

        # Render crosshair without world generator (should use defaults)
        viewport.render_crosshair(console)

        # Check that crosshair was rendered at correct position
        crosshair_x = camera.config.crosshair_x
        crosshair_y = camera.config.crosshair_y

        # Get the character at crosshair position
        char_info = console.tiles[crosshair_y, crosshair_x]

        # Check that it has the golden background color
        assert char_info['bg'][0] == 255  # Red component
        assert char_info['bg'][1] == 215  # Green component
        assert char_info['bg'][2] == 0    # Blue component

    def test_render_crosshair_with_world_generator(self):
        """Test rendering the crosshair with world generator to show terrain character."""
        from empires.world.generator import create_environmental_world_generator

        camera = Camera()
        viewport = Viewport(camera)
        console = tcod.console.Console(80, 50)
        world_generator = create_environmental_world_generator(seed=12345)

        # Render crosshair with world generator
        viewport.render_crosshair(console, world_generator)

        # Check that crosshair was rendered at correct position
        crosshair_x = camera.config.crosshair_x
        crosshair_y = camera.config.crosshair_y

        # Get the character at crosshair position
        char_info = console.tiles[crosshair_y, crosshair_x]

        # Check that it has the golden background color
        assert char_info['bg'][0] == 255  # Red component
        assert char_info['bg'][1] == 215  # Green component
        assert char_info['bg'][2] == 0    # Blue component

        # Check that it has black foreground (cursor text color)
        assert char_info['fg'][0] == 0    # Red component
        assert char_info['fg'][1] == 0    # Green component
        assert char_info['fg'][2] == 0    # Blue component

        # The character should be whatever terrain is at position (0, 0)
        # We can't predict exactly what it will be, but it should be a valid character
        cursor_char = chr(char_info['ch'])
        assert len(cursor_char) == 1  # Should be a single character
    
    def test_render_ui(self):
        """Test rendering UI information."""
        camera = Camera()
        camera.set_position(100, -50)
        viewport = Viewport(camera)
        console = tcod.console.Console(80, 50)
        
        # Render UI
        viewport.render_ui(console)
        
        # Check that UI was rendered (we can't easily check exact text,
        # but we can verify that something was written to the console)
        # The UI should write to positions starting at (2, 2)
        char_info = console.tiles[2, 2]
        assert char_info['ch'] != 0  # Should have some character


class TestFactoryFunctions:
    """Test the factory functions."""
    
    def test_create_default_camera(self):
        """Test creating a default camera."""
        camera = create_default_camera()
        
        assert isinstance(camera, Camera)
        assert camera.world_x == 0
        assert camera.world_y == 0
        assert camera.config.crosshair_x == 40
        assert camera.config.crosshair_y == 25
    
    def test_create_viewport_system(self):
        """Test creating a complete viewport system."""
        camera, viewport = create_viewport_system()
        
        assert isinstance(camera, Camera)
        assert isinstance(viewport, Viewport)
        assert viewport.camera is camera


class TestCoordinateConversions:
    """Test coordinate conversion consistency."""
    
    def test_round_trip_conversion(self):
        """Test that screen->world->screen conversion is consistent."""
        camera = Camera()
        camera.set_position(50, 75)
        
        # Test various screen positions
        test_positions = [(0, 0), (40, 25), (79, 49), (20, 10)]
        
        for original_screen_x, original_screen_y in test_positions:
            # Convert to world and back
            world_x, world_y = camera.screen_to_world(original_screen_x, original_screen_y)
            screen_x, screen_y = camera.world_to_screen(world_x, world_y)
            
            assert screen_x == original_screen_x
            assert screen_y == original_screen_y
    
    def test_world_round_trip_conversion(self):
        """Test that world->screen->world conversion is consistent."""
        camera = Camera()
        camera.set_position(25, 30)
        
        # Test various world positions that should be visible
        test_positions = [(25, 30), (0, 0), (50, 60), (10, 15)]
        
        for original_world_x, original_world_y in test_positions:
            # Convert to screen and back
            screen_x, screen_y = camera.world_to_screen(original_world_x, original_world_y)
            
            # Only test if position is visible
            if (0 <= screen_x < 80 and 0 <= screen_y < 50):
                world_x, world_y = camera.screen_to_world(screen_x, screen_y)
                
                assert world_x == original_world_x
                assert world_y == original_world_y


if __name__ == "__main__":
    pytest.main([__file__])
