"""
UI Manager for the three-tier world generation system.

This module provides the UIManager class that coordinates all UI components
and handles console area allocation, rendering order, and component updates.
"""

import tcod
from typing import Optional, Dict, Any

try:
    from .base import UIComponent, calculate_layout_areas
    from .top_bar import TopBar
    from .bottom_bar import BottomBar
    from .left_sidebar import LeftSidebar
    from .right_sidebar import RightSidebar
    from ..world_types import ViewScale, ColorRGB
    from ..camera import MultiScaleCameraSystem
    from ..world_data import WorldMapData
except ImportError:
    from base import UIComponent, calculate_layout_areas
    from top_bar import TopBar
    from bottom_bar import BottomBar
    from left_sidebar import LeftSidebar
    from right_sidebar import RightSidebar
    from world_types import ViewScale, ColorRGB
    from camera import MultiScaleCameraSystem
    from world_data import WorldMapData


class UIManager:
    """
    Manager for all UI components in the world generation system.
    
    Handles:
    - Component creation and layout
    - Rendering coordination
    - Event distribution
    - Console area management
    - Component updates
    
    Attributes:
        console_width: Total console width
        console_height: Total console height
        top_bar: Top information bar
        bottom_bar: Bottom control bar
        left_sidebar: Left sidebar (placeholder)
        right_sidebar: Right sidebar (placeholder)
        main_content_area: Area available for main content
        camera_system: Camera system reference
        world_data: World data reference
    """
    
    def __init__(
        self,
        console_width: int,
        console_height: int,
        camera_system: Optional[MultiScaleCameraSystem] = None,
        world_data: Optional[WorldMapData] = None
    ) -> None:
        """
        Initialize the UI manager.
        
        Args:
            console_width: Total console width
            console_height: Total console height
            camera_system: Camera system for position information
            world_data: World data for terrain information
        """
        self.console_width = console_width
        self.console_height = console_height
        self.camera_system = camera_system
        self.world_data = world_data
        
        # Calculate layout areas
        self.layout = calculate_layout_areas(console_width, console_height)
        
        # Create UI components
        self._create_components()
        
        # Component rendering order (back to front)
        self.render_order = [
            self.left_sidebar,
            self.right_sidebar,
            self.top_bar,
            self.bottom_bar
        ]
        
        # Main content area for game rendering
        self.main_content_area = self.layout['main_content']
    
    def _create_components(self) -> None:
        """Create all UI components with proper positioning."""
        # Top bar
        top_area = self.layout['top_bar']
        self.top_bar = TopBar(
            x=top_area['x'],
            y=top_area['y'],
            width=top_area['width'],
            height=top_area['height'],
            camera_system=self.camera_system,
            world_data=self.world_data
        )
        
        # Bottom bar
        bottom_area = self.layout['bottom_bar']
        self.bottom_bar = BottomBar(
            x=bottom_area['x'],
            y=bottom_area['y'],
            width=bottom_area['width'],
            height=bottom_area['height']
        )
        
        # Left sidebar
        left_area = self.layout['left_sidebar']
        self.left_sidebar = LeftSidebar(
            x=left_area['x'],
            y=left_area['y'],
            width=left_area['width'],
            height=left_area['height']
        )
        
        # Right sidebar
        right_area = self.layout['right_sidebar']
        self.right_sidebar = RightSidebar(
            x=right_area['x'],
            y=right_area['y'],
            width=right_area['width'],
            height=right_area['height']
        )
    
    def set_camera_system(self, camera_system: MultiScaleCameraSystem) -> None:
        """
        Set the camera system reference.
        
        Args:
            camera_system: Camera system to use
        """
        self.camera_system = camera_system
        self.top_bar.set_camera_system(camera_system)
    
    def set_world_data(self, world_data: WorldMapData) -> None:
        """
        Set the world data reference.
        
        Args:
            world_data: World data to use
        """
        self.world_data = world_data
        self.top_bar.set_world_data(world_data)
    
    def update(self) -> None:
        """Update all UI components with current state."""
        if self.camera_system:
            # Update bottom bar with current scale
            self.bottom_bar.set_current_scale(self.camera_system.current_scale)
    
    def render(self, console: tcod.console.Console) -> None:
        """
        Render all UI components to the console.
        
        Args:
            console: Console to render to
        """
        # Render components in order
        for component in self.render_order:
            if component.visible:
                component.render(console)
    
    def clear_main_content(self, console: tcod.console.Console) -> None:
        """
        Clear the main content area.
        
        Args:
            console: Console to clear
        """
        area = self.main_content_area
        for y in range(area['height']):
            for x in range(area['width']):
                console_x = area['x'] + x
                console_y = area['y'] + y
                if (0 <= console_x < console.width and 
                    0 <= console_y < console.height):
                    console.print(console_x, console_y, " ", fg=(255, 255, 255), bg=(0, 0, 0))
    
    def get_main_content_area(self) -> Dict[str, int]:
        """
        Get the main content area dimensions.
        
        Returns:
            Dictionary with x, y, width, height of main content area
        """
        return self.main_content_area.copy()
    
    def handle_resize(self, new_width: int, new_height: int) -> None:
        """
        Handle console resize by recalculating layout.
        
        Args:
            new_width: New console width
            new_height: New console height
        """
        self.console_width = new_width
        self.console_height = new_height
        
        # Recalculate layout
        self.layout = calculate_layout_areas(new_width, new_height)
        
        # Update component positions and sizes
        top_area = self.layout['top_bar']
        self.top_bar.set_position(top_area['x'], top_area['y'])
        self.top_bar.set_size(top_area['width'], top_area['height'])
        
        bottom_area = self.layout['bottom_bar']
        self.bottom_bar.set_position(bottom_area['x'], bottom_area['y'])
        self.bottom_bar.set_size(bottom_area['width'], bottom_area['height'])
        
        left_area = self.layout['left_sidebar']
        self.left_sidebar.set_position(left_area['x'], left_area['y'])
        self.left_sidebar.set_size(left_area['width'], left_area['height'])
        
        right_area = self.layout['right_sidebar']
        self.right_sidebar.set_position(right_area['x'], right_area['y'])
        self.right_sidebar.set_size(right_area['width'], right_area['height'])
        
        # Update main content area
        self.main_content_area = self.layout['main_content']
    
    def toggle_component_visibility(self, component_name: str) -> bool:
        """
        Toggle visibility of a UI component.
        
        Args:
            component_name: Name of component ('top_bar', 'bottom_bar', etc.)
            
        Returns:
            New visibility state
        """
        component_map = {
            'top_bar': self.top_bar,
            'bottom_bar': self.bottom_bar,
            'left_sidebar': self.left_sidebar,
            'right_sidebar': self.right_sidebar
        }
        
        if component_name in component_map:
            component = component_map[component_name]
            component.visible = not component.visible
            return component.visible
        
        return False
    
    def get_component_at_position(self, x: int, y: int) -> Optional[UIComponent]:
        """
        Get the UI component at a specific position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            UI component at position, or None
        """
        # Check components in reverse render order (front to back)
        for component in reversed(self.render_order):
            if component.visible and component.contains_point(x, y):
                return component
        
        return None
    
    def get_status_summary(self) -> str:
        """
        Get a summary of current UI status.
        
        Returns:
            String summary of UI state
        """
        visible_components = sum(1 for comp in self.render_order if comp.visible)
        main_area = self.main_content_area
        
        return (f"UI: {visible_components}/4 components visible, "
                f"main area: {main_area['width']}x{main_area['height']}")


if __name__ == "__main__":
    # Basic testing
    print("Testing UI manager...")
    
    # Test UI manager creation
    ui_manager = UIManager(128, 96)
    print(f"✓ UI manager created for {ui_manager.console_width}x{ui_manager.console_height}")
    
    # Test main content area
    main_area = ui_manager.get_main_content_area()
    print(f"✓ Main content area: {main_area['width']}x{main_area['height']} at ({main_area['x']}, {main_area['y']})")
    
    # Test component visibility
    original_visibility = ui_manager.top_bar.visible
    new_visibility = ui_manager.toggle_component_visibility('top_bar')
    print(f"✓ Top bar visibility toggled: {original_visibility} -> {new_visibility}")
    
    # Test status summary
    status = ui_manager.get_status_summary()
    print(f"✓ Status summary: {status}")
    
    # Test resize
    ui_manager.handle_resize(100, 80)
    new_main_area = ui_manager.get_main_content_area()
    print(f"✓ After resize: main area {new_main_area['width']}x{new_main_area['height']}")
    
    print("UI manager ready!")
