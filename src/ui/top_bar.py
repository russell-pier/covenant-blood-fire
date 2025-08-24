"""
Top bar UI component for the three-tier world generation system.

This module provides the TopBar component that displays current scale,
coordinates, terrain information, and elevation data.
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


class TopBar(UIComponent):
    """
    Top bar component displaying current location and terrain information.
    
    Shows:
    - Current viewing scale
    - Camera coordinates
    - Terrain information for current location
    - Elevation and climate data
    
    Attributes:
        camera_system: Multi-scale camera system for position info
        world_data: World map data for terrain information
        title: Title text to display
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
        Initialize the top bar component.
        
        Args:
            x: X position
            y: Y position
            width: Width of the top bar
            height: Height of the top bar (default: 3)
            camera_system: Camera system for position information
            world_data: World data for terrain information
        """
        super().__init__(x, y, width, height)
        self.camera_system = camera_system
        self.world_data = world_data
        self.title = "Three-Tier World Generation System"
        
        # Colors for different elements
        self.title_color = ColorRGB(255, 255, 255)
        self.info_color = ColorRGB(200, 200, 200)
        self.highlight_color = ColorRGB(255, 255, 100)
        self.border_color = ColorRGB(100, 100, 100)
    
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
        pos_info = self.camera_system.get_current_position_info()
        
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
                'terrain': f"{sector.dominant_terrain.name} ({scale_name} view)",
                'elevation': sector.elevation,
                'climate': sector.climate_zone.name,
                'biome': f"{sector.get_biome_description()} - {scale_name} detail",
                'has_mountains': sector.has_mountains,
                'has_rivers': sector.has_rivers
            }
        
        return {
            'terrain': 'Unknown',
            'elevation': 0.0,
            'climate': 'Unknown',
            'biome': 'No data available'
        }
    
    def render(self, console: tcod.console.Console) -> None:
        """
        Render the top bar to the console.
        
        Args:
            console: Console to render to
        """
        if not self.visible:
            return
        
        # Clear the area
        self.fill_background(console, ColorRGB(0, 0, 50))
        
        # Draw border
        self.draw_border(console, self.border_color)
        
        # Get current information
        if self.camera_system:
            pos_info = self.camera_system.get_current_position_info()
            abs_x, abs_y = self.camera_system.get_absolute_coordinates()
            terrain_info = self.get_current_terrain_info()
        else:
            pos_info = {'scale': 'UNKNOWN', 'description': 'No camera system'}
            abs_x, abs_y = 0.0, 0.0
            terrain_info = {'terrain': 'Unknown', 'elevation': 0.0, 'climate': 'Unknown'}
        
        # Line 1: Title and current scale
        title_text = f"{self.title}"
        scale_text = f"Scale: {pos_info['scale']}"
        
        self.print_text(console, 2, 1, title_text, fg=self.title_color.as_tuple())
        
        # Right-align scale info
        scale_x = self.width - len(scale_text) - 2
        self.print_text(console, scale_x, 1, scale_text, fg=self.highlight_color.as_tuple())
        
        # Line 2: Position and coordinates
        if self.camera_system:
            coord_text = f"Position: ({abs_x:.0f}, {abs_y:.0f})"
            self.print_text(console, 2, 2, coord_text, fg=self.info_color.as_tuple())
            
            # Current view description
            view_desc = pos_info.get('description', '')
            if len(view_desc) > 0:
                # Truncate if too long
                max_desc_length = self.width - len(coord_text) - 6
                if len(view_desc) > max_desc_length:
                    view_desc = view_desc[:max_desc_length - 3] + "..."
                
                desc_x = len(coord_text) + 4
                self.print_text(console, desc_x, 2, view_desc, fg=self.info_color.as_tuple())
        
        # Line 3: Terrain information
        terrain_text = f"Terrain: {terrain_info['terrain']}"
        elevation_text = f"Elevation: {terrain_info['elevation']:.2f}"
        climate_text = f"Climate: {terrain_info['climate']}"
        
        # Fit terrain info on one line
        info_parts = [terrain_text]
        
        # Add elevation if there's space
        current_length = len(terrain_text)
        if current_length + len(elevation_text) + 3 < self.width - 4:
            info_parts.append(elevation_text)
            current_length += len(elevation_text) + 3
        
        # Add climate if there's space
        if current_length + len(climate_text) + 3 < self.width - 4:
            info_parts.append(climate_text)
        
        terrain_line = " | ".join(info_parts)
        self.print_text(console, 2, 3, terrain_line, fg=self.info_color.as_tuple())
        
        # Add feature indicators if present
        if terrain_info.get('has_mountains', False) or terrain_info.get('has_rivers', False):
            features = []
            if terrain_info.get('has_mountains', False):
                features.append("⛰")
            if terrain_info.get('has_rivers', False):
                features.append("~")
            
            if features:
                feature_text = " ".join(features)
                feature_x = self.width - len(feature_text) - 2
                self.print_text(console, feature_x, 3, feature_text, fg=self.highlight_color.as_tuple())
    
    def update_title(self, new_title: str) -> None:
        """
        Update the title text.
        
        Args:
            new_title: New title to display
        """
        self.title = new_title
    
    def get_status_summary(self) -> str:
        """
        Get a text summary of current status.
        
        Returns:
            String summary of current status
        """
        if not self.camera_system:
            return "No camera system connected"
        
        pos_info = self.camera_system.get_current_position_info()
        abs_x, abs_y = self.camera_system.get_absolute_coordinates()
        terrain_info = self.get_current_terrain_info()
        
        return (f"Scale: {pos_info['scale']} | "
                f"Position: ({abs_x:.0f}, {abs_y:.0f}) | "
                f"Terrain: {terrain_info['terrain']} | "
                f"Elevation: {terrain_info['elevation']:.2f}")


if __name__ == "__main__":
    # Basic testing
    print("Testing top bar component...")
    
    # Test component creation
    top_bar = TopBar(0, 0, 80, 3)
    print(f"✓ Top bar created: {top_bar.width}x{top_bar.height}")
    
    # Test terrain info without data
    terrain_info = top_bar.get_current_terrain_info()
    print(f"✓ Terrain info (no data): {terrain_info['terrain']}")
    
    # Test status summary
    summary = top_bar.get_status_summary()
    print(f"✓ Status summary: {summary}")
    
    print("Top bar component ready!")
