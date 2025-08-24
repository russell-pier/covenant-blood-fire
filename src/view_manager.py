"""
View manager for the three-tier world generation system.

This module provides the ViewManager class that coordinates rendering
across different scales and manages the integration between cameras,
renderers, and UI components.
"""

import tcod
from typing import Optional, Dict

try:
    from .world_types import ViewScale
    from .world_data import WorldMapData
    from .camera import MultiScaleCameraSystem
    from .ui.ui_manager import UIManager
    from .renderers.world_renderer import WorldRenderer
    from .renderers.regional_renderer import RegionalRenderer
    from .renderers.local_renderer import LocalRenderer
except ImportError:
    from world_types import ViewScale
    from world_data import WorldMapData
    from camera import MultiScaleCameraSystem
    from ui.ui_manager import UIManager
    from renderers.world_renderer import WorldRenderer
    from renderers.regional_renderer import RegionalRenderer
    from renderers.local_renderer import LocalRenderer


class ViewManager:
    """
    Manager for coordinating all rendering and view systems.
    
    Handles:
    - Scale-specific renderer selection
    - Camera and renderer coordination
    - UI integration
    - Render area management
    - View switching logic
    
    Attributes:
        camera_system: Multi-scale camera system
        ui_manager: UI component manager
        world_data: World map data
        world_renderer: World-scale renderer
        regional_renderer: Regional-scale renderer (placeholder)
        local_renderer: Local-scale renderer (placeholder)
        current_scale: Currently active viewing scale
    """
    
    def __init__(
        self,
        console_width: int,
        console_height: int,
        world_data: Optional[WorldMapData] = None
    ) -> None:
        """
        Initialize the view manager.
        
        Args:
            console_width: Total console width
            console_height: Total console height
            world_data: World map data to display
        """
        self.console_width = console_width
        self.console_height = console_height
        self.world_data = world_data
        
        # Initialize camera system
        self.camera_system = MultiScaleCameraSystem()
        
        # Initialize UI manager
        self.ui_manager = UIManager(
            console_width, 
            console_height,
            self.camera_system,
            world_data
        )
        
        # Initialize renderers
        self.world_renderer = WorldRenderer(world_data, self.camera_system)
        self.regional_renderer = RegionalRenderer(self.camera_system)
        self.local_renderer = LocalRenderer(self.camera_system)
        
        # Set render areas for all renderers
        main_area = self.ui_manager.get_main_content_area()
        self.world_renderer.set_render_area(main_area)
        self.regional_renderer.set_render_area(main_area)
        self.local_renderer.set_render_area(main_area)
        
        self.current_scale = ViewScale.WORLD
    
    def set_world_data(self, world_data: WorldMapData) -> None:
        """
        Set the world data for all components.
        
        Args:
            world_data: World map data to use
        """
        self.world_data = world_data
        self.ui_manager.set_world_data(world_data)
        self.world_renderer.set_world_data(world_data)
    
    def switch_to_scale(self, new_scale: ViewScale) -> bool:
        """
        Switch to a different viewing scale.
        
        Args:
            new_scale: Target viewing scale
            
        Returns:
            True if switch was successful
        """
        if self.camera_system.switch_to_scale(new_scale):
            self.current_scale = new_scale
            return True
        return False
    
    def move_camera(self, dx: int, dy: int) -> bool:
        """
        Move the current camera.
        
        Args:
            dx: Horizontal movement
            dy: Vertical movement
            
        Returns:
            True if movement was successful
        """
        return self.camera_system.move_current_camera(dx, dy)
    
    def get_current_renderer(self):
        """Get the renderer for the current scale."""
        if self.current_scale == ViewScale.WORLD:
            return self.world_renderer
        elif self.current_scale == ViewScale.REGIONAL:
            return self.regional_renderer
        else:  # LOCAL
            return self.local_renderer
    
    def update(self) -> None:
        """Update all view components."""
        # Update UI with current state
        self.ui_manager.update()
    
    def render(self, console: tcod.console.Console) -> None:
        """
        Render the complete view to the console.
        
        Args:
            console: Console to render to
        """
        # Clear the main content area
        self.ui_manager.clear_main_content(console)
        
        # Render the current scale's content
        current_renderer = self.get_current_renderer()
        current_renderer.render(console)
        
        # Render UI components on top
        self.ui_manager.render(console)
    
    def handle_resize(self, new_width: int, new_height: int) -> None:
        """
        Handle console resize.
        
        Args:
            new_width: New console width
            new_height: New console height
        """
        self.console_width = new_width
        self.console_height = new_height
        
        # Update UI manager
        self.ui_manager.handle_resize(new_width, new_height)
        
        # Update renderer areas
        main_area = self.ui_manager.get_main_content_area()
        self.world_renderer.set_render_area(main_area)
        self.regional_renderer.set_render_area(main_area)
        self.local_renderer.set_render_area(main_area)
    
    def handle_mouse_click(self, x: int, y: int) -> bool:
        """
        Handle mouse click events.
        
        Args:
            x: Mouse X position
            y: Mouse Y position
            
        Returns:
            True if click was handled
        """
        # Check if click is in main content area
        main_area = self.ui_manager.get_main_content_area()
        
        if (main_area['x'] <= x < main_area['x'] + main_area['width'] and
            main_area['y'] <= y < main_area['y'] + main_area['height']):
            
            # Handle scale-specific clicks
            if self.current_scale == ViewScale.WORLD:
                return self.handle_world_click(x, y)
            elif self.current_scale == ViewScale.REGIONAL:
                return self.handle_regional_click(x, y)
            else:  # LOCAL
                return self.handle_local_click(x, y)
        
        return False
    
    def handle_world_click(self, x: int, y: int) -> bool:
        """
        Handle mouse click in world view.
        
        Args:
            x: Mouse X position
            y: Mouse Y position
            
        Returns:
            True if click was handled
        """
        # Get sector at click position
        sector_coord = self.world_renderer.get_sector_at_screen_position(x, y)
        
        if sector_coord:
            # Move camera to clicked sector
            return self.camera_system.world_camera.move_to(
                self.camera_system.world_camera.position.__class__(
                    sector_coord.x, sector_coord.y
                )
            )
        
        return False
    
    def handle_regional_click(self, x: int, y: int) -> bool:
        """Handle mouse click in regional view (placeholder)."""
        # Future implementation for regional view clicks
        return False
    
    def handle_local_click(self, x: int, y: int) -> bool:
        """Handle mouse click in local view (placeholder)."""
        # Future implementation for local view clicks
        return False
    
    def get_status_info(self) -> Dict[str, str]:
        """
        Get comprehensive status information.
        
        Returns:
            Dictionary with status information
        """
        camera_info = self.camera_system.get_current_position_info()
        abs_x, abs_y = self.camera_system.get_absolute_coordinates()
        
        return {
            'scale': camera_info['scale'],
            'position': f"({abs_x:.0f}, {abs_y:.0f})",
            'description': camera_info['description'],
            'ui_status': self.ui_manager.get_status_summary(),
            'console_size': f"{self.console_width}x{self.console_height}"
        }
    
    def toggle_ui_component(self, component_name: str) -> bool:
        """
        Toggle visibility of a UI component.
        
        Args:
            component_name: Name of component to toggle
            
        Returns:
            New visibility state
        """
        return self.ui_manager.toggle_component_visibility(component_name)


if __name__ == "__main__":
    # Basic testing
    print("Testing view manager...")
    
    # Create view manager
    view_manager = ViewManager(128, 96)
    print("✓ View manager created")
    
    # Test scale switching
    if view_manager.switch_to_scale(ViewScale.REGIONAL):
        print("✓ Scale switching works")
    
    # Test camera movement
    if view_manager.move_camera(1, 0):
        print("✓ Camera movement works")
    
    # Test status info
    status = view_manager.get_status_info()
    print(f"✓ Status info: {status['scale']} at {status['position']}")
    
    # Test with world data
    from world_generator import WorldScaleGenerator
    generator = WorldScaleGenerator(12345)
    world_data = generator.generate_complete_world_map()
    view_manager.set_world_data(world_data)
    print("✓ World data integration works")
    
    print("View manager ready!")
