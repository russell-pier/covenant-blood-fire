"""
Test suite for the rendering system.

Tests world renderer functionality, view manager integration,
and rendering coordinate calculations.
"""

import pytest
import tcod
from src.renderers.world_renderer import WorldRenderer
from src.renderers.regional_renderer import RegionalRenderer
from src.renderers.local_renderer import LocalRenderer
from src.view_manager import ViewManager
from src.world_generator import WorldScaleGenerator
from src.camera import MultiScaleCameraSystem
from src.world_types import ViewScale, WorldCoordinate


class TestWorldRenderer:
    """Test cases for the WorldRenderer class."""
    
    def test_world_renderer_initialization(self):
        """Test world renderer initialization."""
        renderer = WorldRenderer()
        assert renderer.world_data is None
        assert renderer.camera_system is None
        assert renderer.render_area is None
    
    def test_render_area_setting(self):
        """Test setting render area."""
        renderer = WorldRenderer()
        test_area = {'x': 10, 'y': 20, 'width': 100, 'height': 80}
        renderer.set_render_area(test_area)
        assert renderer.render_area == test_area
    
    def test_sector_position_calculation(self):
        """Test sector screen position calculation."""
        renderer = WorldRenderer()
        test_area = {'x': 10, 'y': 10, 'width': 200, 'height': 150}
        renderer.set_render_area(test_area)
        
        # Test corner sectors
        screen_x, screen_y = renderer.calculate_sector_screen_position(0, 0)
        assert screen_x >= test_area['x']
        assert screen_y >= test_area['y']
        
        # Test that different sectors have different positions
        screen_x1, screen_y1 = renderer.calculate_sector_screen_position(0, 0)
        screen_x2, screen_y2 = renderer.calculate_sector_screen_position(1, 0)
        assert screen_x2 > screen_x1  # Should be 16 pixels to the right
        
        screen_x3, screen_y3 = renderer.calculate_sector_screen_position(0, 1)
        assert screen_y3 > screen_y1  # Should be 16 pixels down
    
    def test_screen_to_sector_conversion(self):
        """Test converting screen coordinates back to sector coordinates."""
        renderer = WorldRenderer()
        test_area = {'x': 10, 'y': 10, 'width': 200, 'height': 150}
        renderer.set_render_area(test_area)
        
        # Test round-trip conversion
        for sector_x in range(8):
            for sector_y in range(6):
                screen_x, screen_y = renderer.calculate_sector_screen_position(sector_x, sector_y)
                # Click in center of sector
                click_x = screen_x + 8
                click_y = screen_y + 8
                
                result_coord = renderer.get_sector_at_screen_position(click_x, click_y)
                assert result_coord is not None
                assert result_coord.x == sector_x
                assert result_coord.y == sector_y
    
    def test_out_of_bounds_screen_position(self):
        """Test screen to sector conversion with out-of-bounds positions."""
        renderer = WorldRenderer()
        test_area = {'x': 10, 'y': 10, 'width': 200, 'height': 150}
        renderer.set_render_area(test_area)
        
        # Test positions outside the world area
        result = renderer.get_sector_at_screen_position(0, 0)  # Too far left/up
        assert result is None
        
        result = renderer.get_sector_at_screen_position(300, 300)  # Too far right/down
        assert result is None
    
    def test_render_with_no_data(self):
        """Test rendering when no world data is available."""
        renderer = WorldRenderer()
        test_area = {'x': 0, 'y': 0, 'width': 100, 'height': 80}
        renderer.set_render_area(test_area)
        
        # Create a test console
        console = tcod.console.Console(120, 100)
        
        # Should not crash when rendering without data
        renderer.render(console)
        # No specific assertions - just testing it doesn't crash
    
    def test_render_with_world_data(self):
        """Test rendering with actual world data."""
        # Generate test world data
        generator = WorldScaleGenerator(12345)
        world_data = generator.generate_complete_world_map()
        camera_system = MultiScaleCameraSystem()
        
        renderer = WorldRenderer(world_data, camera_system)
        test_area = {'x': 0, 'y': 0, 'width': 200, 'height': 150}
        renderer.set_render_area(test_area)
        
        # Create a test console
        console = tcod.console.Console(220, 170)
        
        # Should not crash when rendering with data
        renderer.render(console)
        # No specific assertions - just testing it doesn't crash


class TestPlaceholderRenderers:
    """Test cases for placeholder renderers."""
    
    def test_regional_renderer_initialization(self):
        """Test regional renderer initialization."""
        renderer = RegionalRenderer()
        assert renderer.camera_system is None
        assert renderer.render_area is None
    
    def test_local_renderer_initialization(self):
        """Test local renderer initialization."""
        renderer = LocalRenderer()
        assert renderer.camera_system is None
        assert renderer.render_area is None
    
    def test_placeholder_rendering(self):
        """Test that placeholder renderers don't crash."""
        camera_system = MultiScaleCameraSystem()
        test_area = {'x': 0, 'y': 0, 'width': 100, 'height': 80}
        console = tcod.console.Console(120, 100)
        
        # Test regional renderer
        regional_renderer = RegionalRenderer(camera_system)
        regional_renderer.set_render_area(test_area)
        regional_renderer.render(console)
        
        # Test local renderer
        local_renderer = LocalRenderer(camera_system)
        local_renderer.set_render_area(test_area)
        local_renderer.render(console)


class TestViewManager:
    """Test cases for the ViewManager class."""
    
    def test_view_manager_initialization(self):
        """Test view manager initialization."""
        view_manager = ViewManager(128, 96)
        assert view_manager.console_width == 128
        assert view_manager.console_height == 96
        assert view_manager.current_scale == ViewScale.WORLD
        assert view_manager.camera_system is not None
        assert view_manager.ui_manager is not None
    
    def test_scale_switching(self):
        """Test scale switching functionality."""
        view_manager = ViewManager(128, 96)
        
        # Test switching to regional
        assert view_manager.switch_to_scale(ViewScale.REGIONAL) == True
        assert view_manager.current_scale == ViewScale.REGIONAL
        
        # Test switching to local
        assert view_manager.switch_to_scale(ViewScale.LOCAL) == True
        assert view_manager.current_scale == ViewScale.LOCAL
        
        # Test switching back to world
        assert view_manager.switch_to_scale(ViewScale.WORLD) == True
        assert view_manager.current_scale == ViewScale.WORLD
    
    def test_camera_movement(self):
        """Test camera movement through view manager."""
        view_manager = ViewManager(128, 96)
        
        # Get initial position
        initial_pos = view_manager.camera_system.world_camera.position
        
        # Test movement
        assert view_manager.move_camera(1, 0) == True
        new_pos = view_manager.camera_system.world_camera.position
        assert new_pos.x == initial_pos.x + 1
        assert new_pos.y == initial_pos.y
    
    def test_renderer_selection(self):
        """Test that correct renderer is selected for each scale."""
        view_manager = ViewManager(128, 96)
        
        # World scale
        view_manager.switch_to_scale(ViewScale.WORLD)
        renderer = view_manager.get_current_renderer()
        assert isinstance(renderer, WorldRenderer)
        
        # Regional scale
        view_manager.switch_to_scale(ViewScale.REGIONAL)
        renderer = view_manager.get_current_renderer()
        assert isinstance(renderer, RegionalRenderer)
        
        # Local scale
        view_manager.switch_to_scale(ViewScale.LOCAL)
        renderer = view_manager.get_current_renderer()
        assert isinstance(renderer, LocalRenderer)
    
    def test_world_data_integration(self):
        """Test world data integration with view manager."""
        view_manager = ViewManager(128, 96)
        
        # Generate test world data
        generator = WorldScaleGenerator(12345)
        world_data = generator.generate_complete_world_map()
        
        # Set world data
        view_manager.set_world_data(world_data)
        assert view_manager.world_data == world_data
        assert view_manager.world_renderer.world_data == world_data
    
    def test_status_info(self):
        """Test status information retrieval."""
        view_manager = ViewManager(128, 96)
        
        status = view_manager.get_status_info()
        assert 'scale' in status
        assert 'position' in status
        assert 'description' in status
        assert 'ui_status' in status
        assert 'console_size' in status
        
        assert status['scale'] == 'WORLD'
        assert status['console_size'] == '128x96'
    
    def test_resize_handling(self):
        """Test console resize handling."""
        view_manager = ViewManager(128, 96)
        
        # Test resize
        view_manager.handle_resize(100, 80)
        assert view_manager.console_width == 100
        assert view_manager.console_height == 80
        
        # Check that main content area was updated
        main_area = view_manager.ui_manager.get_main_content_area()
        assert main_area['width'] > 0
        assert main_area['height'] > 0
    
    def test_mouse_click_handling(self):
        """Test mouse click event handling."""
        view_manager = ViewManager(128, 96)
        
        # Generate test world data
        generator = WorldScaleGenerator(12345)
        world_data = generator.generate_complete_world_map()
        view_manager.set_world_data(world_data)
        
        # Get main content area
        main_area = view_manager.ui_manager.get_main_content_area()
        
        # Test click in main area (should be handled)
        click_x = main_area['x'] + main_area['width'] // 2
        click_y = main_area['y'] + main_area['height'] // 2
        
        # This should not crash (actual behavior depends on implementation)
        result = view_manager.handle_mouse_click(click_x, click_y)
        assert isinstance(result, bool)
        
        # Test click outside main area (should not be handled)
        result = view_manager.handle_mouse_click(0, 0)
        assert result == False
    
    def test_rendering_integration(self):
        """Test complete rendering integration."""
        view_manager = ViewManager(128, 96)
        
        # Generate test world data
        generator = WorldScaleGenerator(12345)
        world_data = generator.generate_complete_world_map()
        view_manager.set_world_data(world_data)
        
        # Create test console
        console = tcod.console.Console(128, 96)
        
        # Test rendering for each scale
        for scale in [ViewScale.WORLD, ViewScale.REGIONAL, ViewScale.LOCAL]:
            view_manager.switch_to_scale(scale)
            view_manager.update()
            view_manager.render(console)
            # Should not crash


if __name__ == "__main__":
    # Run basic tests when called directly
    print("Running renderer tests...")
    
    # Test world renderer
    renderer = WorldRenderer()
    test_area = {'x': 10, 'y': 10, 'width': 100, 'height': 80}
    renderer.set_render_area(test_area)
    print("✓ World renderer basic functionality")
    
    # Test view manager
    view_manager = ViewManager(128, 96)
    print("✓ View manager creation")
    
    # Test with world data
    from src.world_generator import WorldScaleGenerator
    generator = WorldScaleGenerator(12345)
    world_data = generator.generate_complete_world_map()
    view_manager.set_world_data(world_data)
    print("✓ World data integration")
    
    print("Basic renderer tests completed!")
