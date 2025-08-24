"""
UI Manager for the three-tier world generation system.

This module provides the UIManager class that coordinates all UI components
and handles console area allocation, rendering order, and component updates.
"""

import tcod
from typing import Optional, Dict, Any

try:
    from .base import UIComponent, calculate_layout_areas
    from .floating_status_bar import FloatingStatusBar
    from .floating_instructions_panel import FloatingInstructionsPanel
    from ..world_types import ViewScale, ColorRGB
    from ..camera import MultiScaleCameraSystem
    from ..world_data import WorldMapData
except ImportError:
    from base import UIComponent, calculate_layout_areas
    from floating_status_bar import FloatingStatusBar
    from floating_instructions_panel import FloatingInstructionsPanel
    from world_types import ViewScale, ColorRGB
    from camera import MultiScaleCameraSystem
    from world_data import WorldMapData


class UIManager:
    """
    Manager for floating UI components in the world generation system.

    Handles:
    - Floating component creation and positioning
    - Rendering coordination over full-screen world view
    - Component updates and responsiveness
    - Minimal overlay UI design

    Attributes:
        console_width: Total console width
        console_height: Total console height
        status_bar: Floating status information bar
        instructions_panel: Floating instructions panel
        main_content_area: Full-screen area for world content
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
        
        # Create floating UI components
        self._create_components()

        # Component rendering order (back to front)
        self.render_order = [
            self.status_bar,
            self.instructions_panel
        ]
        
        # Main content area for game rendering
        self.main_content_area = self.layout['main_content']
    
    def _create_components(self) -> None:
        """Create floating UI components with proper positioning."""
        # Floating status bar
        status_area = self.layout['status_bar']
        self.status_bar = FloatingStatusBar(
            x=status_area['x'],
            y=status_area['y'],
            width=status_area['width'],
            height=status_area['height'],
            camera_system=self.camera_system,
            world_data=self.world_data
        )

        # Floating instructions panel
        instructions_area = self.layout['instructions_panel']
        self.instructions_panel = FloatingInstructionsPanel(
            x=instructions_area['x'],
            y=instructions_area['y'],
            width=instructions_area['width'],
            height=instructions_area['height']
        )
    
    def set_camera_system(self, camera_system: MultiScaleCameraSystem) -> None:
        """
        Set the camera system reference.

        Args:
            camera_system: Camera system to use
        """
        self.camera_system = camera_system
        self.status_bar.set_camera_system(camera_system)

    def set_world_data(self, world_data: WorldMapData) -> None:
        """
        Set the world data reference.

        Args:
            world_data: World data to use
        """
        self.world_data = world_data
        self.status_bar.set_world_data(world_data)
    
    def update(self) -> None:
        """Update all UI components with current state."""
        if self.camera_system:
            # Update instructions panel with current scale
            self.instructions_panel.set_current_scale(self.camera_system.current_scale)
    
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
        
        # Update floating component positions and sizes
        status_area = self.layout['status_bar']
        self.status_bar.set_position(status_area['x'], status_area['y'])
        self.status_bar.set_size(status_area['width'], status_area['height'])

        instructions_area = self.layout['instructions_panel']
        self.instructions_panel.set_position(instructions_area['x'], instructions_area['y'])
        self.instructions_panel.set_size(instructions_area['width'], instructions_area['height'])
        
        # Update main content area
        self.main_content_area = self.layout['main_content']
    
    def toggle_component_visibility(self, component_name: str) -> bool:
        """
        Toggle visibility of a UI component.

        Args:
            component_name: Name of component ('status_bar', 'instructions_panel')

        Returns:
            New visibility state
        """
        component_map = {
            'status_bar': self.status_bar,
            'instructions_panel': self.instructions_panel
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

        return (f"UI: {visible_components}/2 floating components, "
                f"full screen: {main_area['width']}x{main_area['height']}")


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
