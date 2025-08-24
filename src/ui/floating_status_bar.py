"""
Floating status bar UI component for the three-tier world generation system.

This module provides a floating status bar that overlays on the world view,
matching the original design with rounded borders and dark background.
"""

import tcod
from typing import Optional, Dict, Any

try:
    from .base import UIComponent
    from ..world_types import ViewScale, ColorRGB
    from ..camera import MultiScaleCameraSystem
    from ..world_data import WorldMapData
except ImportError:
    from base import UIComponent
    from world_types import ViewScale, ColorRGB
    from camera import MultiScaleCameraSystem
    from world_data import WorldMapData


class FloatingStatusBar(UIComponent):
    """
    Floating status bar component that overlays on the world view.
    
    Shows current scale, coordinates, terrain information, and other
    status details in a floating panel with rounded borders.
    
    Attributes:
        camera_system: Multi-scale camera system for position info
        world_data: World map data for terrain information
    """
    
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int = 3,
        camera_system: Optional[MultiScaleCameraSystem] = None,
        world_data: Optional[WorldMapData] = None
    ) -> None:
        """
        Initialize the floating status bar.
        
        Args:
            x: X position
            y: Y position
            width: Width of the status bar
            height: Height of the status bar (default: 3)
            camera_system: Camera system for position information
            world_data: World data for terrain information
        """
        super().__init__(x, y, width, height)
        self.camera_system = camera_system
        self.world_data = world_data
        
        # Colors matching original design
        self.background_color = ColorRGB(40, 40, 40)  # Dark gray background
        self.border_color = ColorRGB(80, 80, 80)  # Lighter gray border
        self.text_color = ColorRGB(220, 220, 220)  # Light gray text
        self.highlight_color = ColorRGB(255, 255, 100)  # Yellow highlights
    
    def set_camera_system(self, camera_system: MultiScaleCameraSystem) -> None:
        """Set the camera system reference."""
        self.camera_system = camera_system
    
    def set_world_data(self, world_data: WorldMapData) -> None:
        """Set the world data reference."""
        self.world_data = world_data
    
    def get_current_terrain_info(self) -> Dict[str, Any]:
        """
        Get terrain information for the current camera position.
        
        Returns:
            Dictionary with terrain information
        """
        if not self.camera_system or not self.world_data:
            return {
                'terrain': 'Unknown',
                'elevation': 0.0,
                'climate': 'Unknown',
                'biome': 'No data available'
            }
        
        # Get current position info
        if self.camera_system.current_scale == ViewScale.WORLD:
            # Get sector information
            camera_pos = self.camera_system.world_camera.position
            sector = self.world_data.get_sector(camera_pos.x, camera_pos.y)
            
            if sector:
                return {
                    'terrain': sector.dominant_terrain.name,
                    'elevation': sector.elevation,
                    'climate': sector.climate_zone.name,
                    'biome': sector.get_biome_description(),
                    'has_mountains': sector.has_mountains,
                    'has_rivers': sector.has_rivers
                }
        
        # For regional and local scales, use the selected sector's data
        sector = self.world_data.get_sector(
            self.camera_system.selected_sector.x,
            self.camera_system.selected_sector.y
        )
        
        if sector:
            scale_name = self.camera_system.current_scale.name.lower()
            return {
                'terrain': f"{sector.dominant_terrain.name}",
                'elevation': sector.elevation,
                'climate': sector.climate_zone.name,
                'biome': f"{sector.get_biome_description()}",
                'scale': scale_name
            }
        
        return {
            'terrain': 'Unknown',
            'elevation': 0.0,
            'climate': 'Unknown',
            'biome': 'No data available'
        }
    
    def draw_rounded_border(self, console: tcod.console.Console) -> None:
        """
        Draw a rounded border around the status bar.
        
        Args:
            console: Console to draw on
        """
        border_color = self.border_color.as_tuple()
        
        # Top and bottom horizontal lines
        for x in range(1, self.width - 1):
            console.print(self.x + x, self.y, "─", fg=border_color)
            console.print(self.x + x, self.y + self.height - 1, "─", fg=border_color)
        
        # Left and right vertical lines
        for y in range(1, self.height - 1):
            console.print(self.x, self.y + y, "│", fg=border_color)
            console.print(self.x + self.width - 1, self.y + y, "│", fg=border_color)
        
        # Rounded corners
        console.print(self.x, self.y, "╭", fg=border_color)
        console.print(self.x + self.width - 1, self.y, "╮", fg=border_color)
        console.print(self.x, self.y + self.height - 1, "╰", fg=border_color)
        console.print(self.x + self.width - 1, self.y + self.height - 1, "╯", fg=border_color)
    
    def render(self, console: tcod.console.Console) -> None:
        """
        Render the floating status bar to the console.
        
        Args:
            console: Console to render to
        """
        if not self.visible:
            return
        
        # Fill background
        self.fill_background(console, self.background_color)
        
        # Draw rounded border
        self.draw_rounded_border(console)
        
        # Get current information
        if self.camera_system:
            pos_info = self.camera_system.get_current_position_info()
            abs_x, abs_y = self.camera_system.get_absolute_coordinates()
            terrain_info = self.get_current_terrain_info()
        else:
            pos_info = {'scale': 'UNKNOWN', 'description': 'No camera system'}
            abs_x, abs_y = 0.0, 0.0
            terrain_info = {'terrain': 'Unknown', 'elevation': 0.0, 'climate': 'Unknown'}
        
        # Line 1: Scale and position
        scale_text = f"Scale: {pos_info['scale']}"
        coord_text = f"Pos: ({abs_x:.0f}, {abs_y:.0f})"
        
        self.print_text(console, 2, 1, scale_text, fg=self.highlight_color.as_tuple())
        
        # Right-align coordinates
        coord_x = self.width - len(coord_text) - 2
        self.print_text(console, coord_x, 1, coord_text, fg=self.text_color.as_tuple())
        
        # Line 2: Terrain information (if there's space)
        if self.height > 2:
            terrain_text = f"Terrain: {terrain_info['terrain']}"
            elevation_text = f"Elev: {terrain_info['elevation']:.2f}"
            
            # Fit terrain info on one line
            max_terrain_length = self.width - len(elevation_text) - 6
            if len(terrain_text) > max_terrain_length:
                terrain_text = terrain_text[:max_terrain_length - 3] + "..."
            
            self.print_text(console, 2, 2, terrain_text, fg=self.text_color.as_tuple())
            
            # Right-align elevation
            elev_x = self.width - len(elevation_text) - 2
            self.print_text(console, elev_x, 2, elevation_text, fg=self.text_color.as_tuple())


if __name__ == "__main__":
    # Basic testing
    print("Testing floating status bar...")
    
    # Test component creation
    status_bar = FloatingStatusBar(2, 1, 80, 3)
    print(f"✓ Floating status bar created: {status_bar.width}x{status_bar.height}")
    
    # Test terrain info without data
    terrain_info = status_bar.get_current_terrain_info()
    print(f"✓ Terrain info (no data): {terrain_info['terrain']}")
    
    print("Floating status bar ready!")
