"""
World renderer for the three-tier world generation system.

This module provides the WorldRenderer class that renders the 8x6 world
sector grid with 16x16 pixel representation per sector, camera crosshair,
and proper color mapping for terrain types.
"""

import tcod
from typing import Optional, Tuple, Dict

try:
    from ..world_types import (
        ViewScale, Coordinate, WorldCoordinate, ColorRGB,
        WORLD_SECTORS_X, WORLD_SECTORS_Y, SECTOR_PIXEL_SIZE
    )
    from ..world_data import WorldMapData, WorldSectorData
    from ..camera import MultiScaleCameraSystem
except ImportError:
    from world_types import (
        ViewScale, Coordinate, WorldCoordinate, ColorRGB,
        WORLD_SECTORS_X, WORLD_SECTORS_Y, SECTOR_PIXEL_SIZE
    )
    from world_data import WorldMapData, WorldSectorData
    from camera import MultiScaleCameraSystem


class WorldRenderer:
    """
    Renderer for world-scale view showing 8x6 sector grid.
    
    Renders each sector as a 16x16 pixel block with terrain-appropriate
    colors and characters. Includes camera crosshair and selection
    indicators.
    
    Attributes:
        world_data: World map data to render
        camera_system: Camera system for position and selection
        render_area: Area available for rendering
        crosshair_color: Color for camera crosshair
        selection_color: Color for selection indicators
    """
    
    def __init__(
        self,
        world_data: Optional[WorldMapData] = None,
        camera_system: Optional[MultiScaleCameraSystem] = None
    ) -> None:
        """
        Initialize the world renderer.
        
        Args:
            world_data: World map data to render
            camera_system: Camera system for position tracking
        """
        self.world_data = world_data
        self.camera_system = camera_system
        self.render_area: Optional[Dict[str, int]] = None
        
        # Rendering colors
        self.crosshair_color = ColorRGB(255, 255, 0)  # Yellow crosshair
        self.selection_color = ColorRGB(255, 100, 100)  # Red selection
        self.border_color = ColorRGB(100, 100, 100)  # Gray borders
        self.background_color = ColorRGB(0, 0, 20)  # Dark blue background
    
    def set_world_data(self, world_data: WorldMapData) -> None:
        """Set the world data to render."""
        self.world_data = world_data
    
    def set_camera_system(self, camera_system: MultiScaleCameraSystem) -> None:
        """Set the camera system reference."""
        self.camera_system = camera_system
    
    def set_render_area(self, area: Dict[str, int]) -> None:
        """
        Set the rendering area.
        
        Args:
            area: Dictionary with x, y, width, height
        """
        self.render_area = area
    
    def calculate_sector_screen_position(self, sector_x: int, sector_y: int) -> Tuple[int, int]:
        """
        Calculate screen position for a world sector based on camera position.

        Args:
            sector_x: Sector X coordinate
            sector_y: Sector Y coordinate

        Returns:
            Tuple of (screen_x, screen_y) for top-left of sector
        """
        if not self.render_area or not self.camera_system:
            return (0, 0)

        # Get camera position (this is the top-left of the view)
        camera_pos = self.camera_system.world_camera.position

        # Calculate sector position relative to camera
        relative_x = sector_x - camera_pos.x
        relative_y = sector_y - camera_pos.y

        # Convert to screen coordinates
        screen_x = self.render_area['x'] + (relative_x * SECTOR_PIXEL_SIZE)
        screen_y = self.render_area['y'] + (relative_y * SECTOR_PIXEL_SIZE)

        return screen_x, screen_y
    
    def render_sector(
        self, 
        console: tcod.console.Console,
        sector: WorldSectorData,
        screen_x: int,
        screen_y: int,
        is_selected: bool = False
    ) -> None:
        """
        Render a single world sector as a 16x16 block.
        
        Args:
            console: Console to render to
            sector: Sector data to render
            screen_x: Screen X position for top-left
            screen_y: Screen Y position for top-left
            is_selected: Whether this sector is selected
        """
        # Get sector display properties
        char = sector.display_char
        color = sector.display_color
        
        # Modify color if selected
        if is_selected:
            # Brighten the color for selection
            color = ColorRGB(
                min(255, color.r + 50),
                min(255, color.g + 50), 
                min(255, color.b + 50)
            )
        
        # Fill the 16x16 sector area
        for dy in range(SECTOR_PIXEL_SIZE):
            for dx in range(SECTOR_PIXEL_SIZE):
                pixel_x = screen_x + dx
                pixel_y = screen_y + dy
                
                # Check console bounds
                if (0 <= pixel_x < console.width and 
                    0 <= pixel_y < console.height):
                    
                    # Use different characters for variety within sector
                    if dx == 0 or dy == 0 or dx == SECTOR_PIXEL_SIZE-1 or dy == SECTOR_PIXEL_SIZE-1:
                        # Border pixels - use a subtle border char
                        display_char = "·" if char != "~" else "~"
                        display_color = ColorRGB(
                            max(0, color.r - 30),
                            max(0, color.g - 30),
                            max(0, color.b - 30)
                        )
                    else:
                        # Interior pixels - use main character
                        display_char = char
                        display_color = color
                    
                    console.print(
                        pixel_x, pixel_y,
                        display_char,
                        fg=display_color.as_tuple(),
                        bg=(0, 0, 0)
                    )
    
    def render_crosshair(
        self,
        console: tcod.console.Console,
        center_x: int,
        center_y: int
    ) -> None:
        """
        Render camera crosshair at specified position.
        
        Args:
            console: Console to render to
            center_x: Center X position
            center_y: Center Y position
        """
        crosshair_size = 3
        color = self.crosshair_color.as_tuple()
        
        # Horizontal line
        for dx in range(-crosshair_size, crosshair_size + 1):
            x = center_x + dx
            if 0 <= x < console.width and 0 <= center_y < console.height:
                console.print(x, center_y, "─", fg=color)
        
        # Vertical line
        for dy in range(-crosshair_size, crosshair_size + 1):
            y = center_y + dy
            if 0 <= center_x < console.width and 0 <= y < console.height:
                console.print(center_x, y, "│", fg=color)
        
        # Center point
        if 0 <= center_x < console.width and 0 <= center_y < console.height:
            console.print(center_x, center_y, "┼", fg=color)
    
    def render(self, console: tcod.console.Console) -> None:
        """
        Render the complete world view.
        
        Args:
            console: Console to render to
        """
        if not self.world_data or not self.render_area:
            # Render placeholder if no data
            self.render_placeholder(console)
            return
        
        # Clear render area
        self.clear_render_area(console)
        
        # Get current camera position for selection
        selected_sector = None
        if self.camera_system and self.camera_system.current_scale == ViewScale.WORLD:
            camera_pos = self.camera_system.world_camera.position
            selected_sector = WorldCoordinate(camera_pos.x, camera_pos.y)
        
        # Calculate visible sector range based on camera and render area
        if self.camera_system:
            camera_pos = self.camera_system.world_camera.position

            # Calculate how many sectors fit in the render area
            sectors_per_screen_x = (self.render_area['width'] // SECTOR_PIXEL_SIZE) + 2  # +2 for partial sectors
            sectors_per_screen_y = (self.render_area['height'] // SECTOR_PIXEL_SIZE) + 2

            # Calculate visible range
            start_x = max(0, camera_pos.x)
            end_x = min(WORLD_SECTORS_X, camera_pos.x + sectors_per_screen_x)
            start_y = max(0, camera_pos.y)
            end_y = min(WORLD_SECTORS_Y, camera_pos.y + sectors_per_screen_y)

            # Render only visible sectors
            for y in range(start_y, end_y):
                for x in range(start_x, end_x):
                    if (y < len(self.world_data.sectors) and
                        x < len(self.world_data.sectors[y])):
                        sector = self.world_data.sectors[y][x]
                        screen_x, screen_y = self.calculate_sector_screen_position(x, y)

                        # Only render if on screen
                        if (screen_x >= self.render_area['x'] - SECTOR_PIXEL_SIZE and
                            screen_x < self.render_area['x'] + self.render_area['width'] and
                            screen_y >= self.render_area['y'] - SECTOR_PIXEL_SIZE and
                            screen_y < self.render_area['y'] + self.render_area['height']):

                            # Check if this sector is selected
                            is_selected = (selected_sector and
                                          selected_sector.x == x and
                                          selected_sector.y == y)

                            self.render_sector(console, sector, screen_x, screen_y, is_selected)
        
        # Render cursor crosshair if in world view
        if (self.camera_system and
            self.camera_system.current_scale == ViewScale.WORLD):
            cursor_pos = self.camera_system.world_camera.get_cursor_world_position()
            crosshair_x, crosshair_y = self.calculate_sector_screen_position(
                cursor_pos.x, cursor_pos.y
            )
            # Center crosshair in sector
            crosshair_x += SECTOR_PIXEL_SIZE // 2
            crosshair_y += SECTOR_PIXEL_SIZE // 2

            self.render_crosshair(console, crosshair_x, crosshair_y)
    
    def render_placeholder(self, console: tcod.console.Console) -> None:
        """
        Render placeholder when no world data is available.
        
        Args:
            console: Console to render to
        """
        if not self.render_area:
            return
        
        # Clear area
        self.clear_render_area(console)
        
        # Draw placeholder text
        placeholder_text = "No World Data"
        text_x = self.render_area['x'] + (self.render_area['width'] - len(placeholder_text)) // 2
        text_y = self.render_area['y'] + self.render_area['height'] // 2
        
        if (0 <= text_x < console.width and 0 <= text_y < console.height):
            console.print(text_x, text_y, placeholder_text, fg=(150, 150, 150))
    
    def clear_render_area(self, console: tcod.console.Console) -> None:
        """
        Clear the rendering area.
        
        Args:
            console: Console to clear
        """
        if not self.render_area:
            return
        
        bg_color = self.background_color.as_tuple()
        
        for y in range(self.render_area['height']):
            for x in range(self.render_area['width']):
                console_x = self.render_area['x'] + x
                console_y = self.render_area['y'] + y
                
                if (0 <= console_x < console.width and 
                    0 <= console_y < console.height):
                    console.print(console_x, console_y, " ", fg=(255, 255, 255), bg=bg_color)
    
    def get_sector_at_screen_position(self, screen_x: int, screen_y: int) -> Optional[WorldCoordinate]:
        """
        Get world sector at screen position based on camera position.

        Args:
            screen_x: Screen X coordinate
            screen_y: Screen Y coordinate

        Returns:
            World coordinate if valid, None otherwise
        """
        if not self.render_area or not self.camera_system:
            return None

        # Check if click is within render area
        if (screen_x < self.render_area['x'] or
            screen_x >= self.render_area['x'] + self.render_area['width'] or
            screen_y < self.render_area['y'] or
            screen_y >= self.render_area['y'] + self.render_area['height']):
            return None

        # Get camera position
        camera_pos = self.camera_system.world_camera.position

        # Convert screen position to relative position within render area
        relative_x = screen_x - self.render_area['x']
        relative_y = screen_y - self.render_area['y']

        # Calculate sector coordinates based on camera position
        sector_x = camera_pos.x + (relative_x // SECTOR_PIXEL_SIZE)
        sector_y = camera_pos.y + (relative_y // SECTOR_PIXEL_SIZE)

        # Validate bounds
        if (0 <= sector_x < WORLD_SECTORS_X and
            0 <= sector_y < WORLD_SECTORS_Y):
            return WorldCoordinate(sector_x, sector_y)

        return None


if __name__ == "__main__":
    # Basic testing
    print("Testing world renderer...")
    
    # Test renderer creation
    renderer = WorldRenderer()
    print("✓ World renderer created")
    
    # Test area setting
    test_area = {'x': 10, 'y': 10, 'width': 100, 'height': 80}
    renderer.set_render_area(test_area)
    print("✓ Render area set")
    
    # Test sector position calculation
    screen_x, screen_y = renderer.calculate_sector_screen_position(0, 0)
    print(f"✓ Sector (0,0) screen position: ({screen_x}, {screen_y})")
    
    screen_x, screen_y = renderer.calculate_sector_screen_position(7, 5)
    print(f"✓ Sector (7,5) screen position: ({screen_x}, {screen_y})")
    
    # Test screen to sector conversion
    sector_coord = renderer.get_sector_at_screen_position(screen_x + 8, screen_y + 8)
    if sector_coord:
        print(f"✓ Screen to sector conversion: ({sector_coord.x}, {sector_coord.y})")
    
    print("World renderer ready!")
