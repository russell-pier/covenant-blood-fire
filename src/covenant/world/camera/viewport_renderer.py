"""
Scale-aware viewport renderer for multi-scale world system.

This module handles rendering the world at different scales with
consistent UI layout and visual feedback.
"""

import tcod
from typing import Tuple, Optional

from ..generators.world_scale import WorldScaleGenerator
from ..generators.regional_scale import RegionalScaleGenerator
from .multi_scale_camera import MultiScaleCameraSystem
from ..data.scale_types import ViewScale


class MultiScaleViewportRenderer:
    """Renders world at different scales with consistent UI."""
    
    def __init__(self, world_generator: WorldScaleGenerator,
                 camera_system: MultiScaleCameraSystem):
        """
        Initialize the multi-scale viewport renderer.

        Args:
            world_generator: World scale generator for world data
            camera_system: Multi-scale camera system
        """
        self.world_generator = world_generator
        self.camera_system = camera_system

        # Initialize regional generator
        self.regional_generator = RegionalScaleGenerator(world_generator)
        
        # Console dimensions (maintain existing layout)
        self.console_width = 80
        self.console_height = 50
        
        # UI space reservations (keep existing floating bar layout)
        self.status_bar_height = 3
        self.instructions_height = 5
        self.ui_margin = 1
        
        # Available rendering area
        self.render_start_y = self.status_bar_height + self.ui_margin
        self.render_end_y = self.console_height - self.instructions_height - self.ui_margin
        self.render_height = self.render_end_y - self.render_start_y
        self.render_width = self.console_width
        
        # Rendering state
        self.last_rendered_scale = None
        self.last_camera_position = None
    
    def update_console_size(self, width: int, height: int) -> None:
        """
        Update console dimensions for responsive design.
        
        Args:
            width: New console width
            height: New console height
        """
        self.console_width = width
        self.console_height = height
        
        # Recalculate rendering area
        self.render_start_y = self.status_bar_height + self.ui_margin
        self.render_end_y = self.console_height - self.instructions_height - self.ui_margin
        self.render_height = self.render_end_y - self.render_start_y
        self.render_width = self.console_width
    
    def render_current_scale(self, console: tcod.console.Console) -> None:
        """
        Render world at current camera scale.
        
        Args:
            console: tcod console to render to
        """
        current_scale = self.camera_system.get_current_scale()
        camera_x, camera_y = self.camera_system.get_camera_position()
        
        # Clear the rendering area first
        self._clear_render_area(console)
        
        if current_scale == ViewScale.WORLD:
            self._render_world_view(console, camera_x, camera_y)
        elif current_scale == ViewScale.REGIONAL:
            self._render_regional_view(console, camera_x, camera_y)
        else:  # LOCAL
            self._render_local_view(console, camera_x, camera_y)
        
        # Always render scale indicator and UI
        self._render_scale_ui(console)
        
        # Update rendering state
        self.last_rendered_scale = current_scale
        self.last_camera_position = (camera_x, camera_y)
    
    def _clear_render_area(self, console: tcod.console.Console) -> None:
        """Clear the main rendering area."""
        for y in range(self.render_start_y, self.render_end_y):
            for x in range(self.render_width):
                if 0 <= x < console.width and 0 <= y < console.height:
                    console.print(x, y, " ", fg=(0, 0, 0), bg=(0, 0, 0))
    
    def _render_world_view(self, console: tcod.console.Console,
                          camera_x: int, camera_y: int) -> None:
        """
        Render 16×16 world sector view with 2x2 scaling for better visibility.

        Args:
            console: tcod console to render to
            camera_x: Camera X position in world scale
            camera_y: Camera Y position in world scale
        """
        world_map = self.world_generator.generate_complete_world_map()

        # Scale factor for better visibility (2x2 = 4 characters per sector)
        scale_factor = 2
        scaled_width = world_map.world_size_sectors[0] * scale_factor
        scaled_height = world_map.world_size_sectors[1] * scale_factor

        # Calculate rendering offset to center the scaled world map
        start_x = (self.render_width - scaled_width) // 2
        start_y = self.render_start_y + (self.render_height - scaled_height) // 2

        # Render world sectors with scaling
        for (sector_x, sector_y), sector_data in world_map.sectors.items():
            # Calculate scaled position
            base_x = start_x + (sector_x * scale_factor)
            base_y = start_y + (sector_y * scale_factor)

            # Determine colors
            if sector_x == camera_x and sector_y == camera_y:
                # Bright highlight for camera position
                bg_color = (120, 120, 0)  # Yellow background
                fg_color = (255, 255, 255)  # White foreground
                char = "⊕"  # Special cursor character
            else:
                bg_color = sector_data.display_bg_color
                fg_color = sector_data.display_color
                char = sector_data.display_char

            # Render 2x2 block for each sector
            for dy in range(scale_factor):
                for dx in range(scale_factor):
                    render_x = base_x + dx
                    render_y = base_y + dy

                    if (0 <= render_x < console.width and
                        0 <= render_y < console.height):

                        # Use different characters for visual variety in the 2x2 block
                        if sector_x == camera_x and sector_y == camera_y:
                            # Cursor gets special treatment
                            if dx == 0 and dy == 0:
                                display_char = "⊕"
                            elif dx == 1 and dy == 0:
                                display_char = "⊖"
                            elif dx == 0 and dy == 1:
                                display_char = "⊗"
                            else:
                                display_char = "⊙"
                        else:
                            # Normal terrain uses same character for consistency
                            display_char = char

                        console.print(
                            render_x, render_y,
                            display_char,
                            fg=fg_color,
                            bg=bg_color
                        )
    
    def _render_regional_view(self, console: tcod.console.Console,
                             camera_x: int, camera_y: int) -> None:
        """
        Render 32×32 regional block view.

        Args:
            console: tcod console to render to
            camera_x: Camera X position in regional scale
            camera_y: Camera Y position in regional scale
        """
        # Get current world coordinates to determine which sector to show
        world_x, world_y = self.camera_system.get_current_world_coordinates()
        sector_x = world_x // self.world_generator.sector_size_tiles
        sector_y = world_y // self.world_generator.sector_size_tiles

        # Generate regional map for current sector
        try:
            regional_map = self.regional_generator.generate_regional_map(sector_x, sector_y)
        except Exception as e:
            # Fallback to placeholder if generation fails
            self._render_placeholder_grid(console, "REGIONAL VIEW", f"Error: {str(e)}",
                                        32, 32, camera_x, camera_y)
            return

        # Calculate rendering area - use more space for regional view
        max_display_size = min(self.render_width - 4, self.render_height - 8, 32)

        start_x = (self.render_width - max_display_size) // 2
        start_y = self.render_start_y + 4

        # Render regional blocks
        for y in range(max_display_size):
            for x in range(max_display_size):
                if x < 32 and y < 32:  # Within regional map bounds
                    block_data = regional_map.get_block(x, y)

                    render_x = start_x + x
                    render_y = start_y + y

                    if (0 <= render_x < console.width and
                        0 <= render_y < console.height):

                        if block_data:
                            # Highlight camera position with bright cursor
                            if x == camera_x and y == camera_y:
                                char = "⊕"
                                fg = (255, 255, 0)
                                bg = (120, 120, 0)
                            else:
                                char = block_data.display_char
                                fg = block_data.display_color
                                bg = block_data.display_bg_color
                        else:
                            # Missing block data
                            char = "?"
                            fg = (255, 0, 0)
                            bg = (100, 0, 0)

                        console.print(render_x, render_y, char, fg=fg, bg=bg)

        # Render title and position info
        title = f"REGIONAL VIEW - Sector ({sector_x},{sector_y})"
        title_x = (self.render_width - len(title)) // 2
        if 0 <= title_x < console.width:
            console.print(title_x, self.render_start_y + 1, title, fg=(255, 255, 255))

        # Show current regional position
        pos_info = f"Regional Position: ({camera_x},{camera_y})"
        pos_x = (self.render_width - len(pos_info)) // 2
        if 0 <= pos_x < console.width:
            console.print(pos_x, self.render_start_y + 2, pos_info, fg=(200, 200, 200))
    
    def _render_local_view(self, console: tcod.console.Console,
                          camera_x: int, camera_y: int) -> None:
        """
        Render 32×32 local chunk view.
        
        Args:
            console: tcod console to render to
            camera_x: Camera X position in local scale
            camera_y: Camera Y position in local scale
        """
        # TODO: Integrate with existing detailed rendering system in Phase 5
        # For now, show placeholder with grid
        self._render_placeholder_grid(console, "LOCAL VIEW", "32×32 Chunks", 
                                    32, 32, camera_x, camera_y)
    
    def _render_placeholder_grid(self, console: tcod.console.Console, 
                               title: str, subtitle: str, grid_width: int, 
                               grid_height: int, camera_x: int, camera_y: int) -> None:
        """
        Render placeholder content with grid for unimplemented views.
        
        Args:
            console: tcod console to render to
            title: Title text to display
            subtitle: Subtitle text to display
            grid_width: Width of the grid to show
            grid_height: Height of the grid to show
            camera_x: Camera X position
            camera_y: Camera Y position
        """
        # Calculate grid rendering area
        available_width = min(self.render_width - 4, grid_width)
        available_height = min(self.render_height - 6, grid_height)
        
        grid_start_x = (self.render_width - available_width) // 2
        grid_start_y = self.render_start_y + 3
        
        # Render grid
        for y in range(available_height):
            for x in range(available_width):
                render_x = grid_start_x + x
                render_y = grid_start_y + y
                
                if (0 <= render_x < console.width and 
                    0 <= render_y < console.height):
                    
                    # Highlight camera position
                    if x == camera_x and y == camera_y:
                        char = "⊕"
                        fg = (255, 255, 0)
                        bg = (60, 60, 0)
                    else:
                        char = "·"
                        fg = (100, 100, 100)
                        bg = (20, 20, 20)
                    
                    console.print(render_x, render_y, char, fg=fg, bg=bg)
        
        # Render title and subtitle
        center_x = self.render_width // 2
        title_y = self.render_start_y + 1
        
        # Title
        title_x = center_x - len(title) // 2
        if 0 <= title_x < console.width and 0 <= title_y < console.height:
            console.print(title_x, title_y, title, fg=(255, 255, 255))
        
        # Subtitle
        subtitle_x = center_x - len(subtitle) // 2
        subtitle_y = title_y + 1
        if 0 <= subtitle_x < console.width and 0 <= subtitle_y < console.height:
            console.print(subtitle_x, subtitle_y, subtitle, fg=(150, 150, 150))
    
    def _render_scale_ui(self, console: tcod.console.Console) -> None:
        """
        Render scale indicator and controls.
        
        Args:
            console: tcod console to render to
        """
        current_scale = self.camera_system.get_current_scale()
        camera_x, camera_y = self.camera_system.get_camera_position()
        world_x, world_y = self.camera_system.get_current_world_coordinates()
        
        # Scale indicator (top-right of rendering area)
        scale_text = f"Scale: {current_scale.value.title()}"
        position_text = f"Pos: {camera_x},{camera_y}"
        world_pos_text = f"World: {world_x},{world_y}"
        
        info_x = max(0, console.width - 30)
        
        if info_x < console.width:
            console.print(info_x, self.render_start_y, 
                         scale_text, fg=(255, 255, 0))
            console.print(info_x, self.render_start_y + 1, 
                         position_text, fg=(200, 200, 200))
            console.print(info_x, self.render_start_y + 2, 
                         world_pos_text, fg=(150, 150, 150))
        
        # Controls reminder (bottom of rendering area)
        controls_y = self.render_end_y - 1
        controls_text = "1=World 2=Region 3=Local | WASD=Move | Enter=Drill"
        controls_x = max(0, (console.width - len(controls_text)) // 2)
        
        if 0 <= controls_y < console.height and controls_x < console.width:
            console.print(controls_x, controls_y, controls_text, fg=(120, 120, 120))
    
    def get_render_bounds(self) -> Tuple[int, int, int, int]:
        """
        Get the current rendering bounds.
        
        Returns:
            Tuple of (start_x, start_y, end_x, end_y)
        """
        return 0, self.render_start_y, self.render_width, self.render_end_y
