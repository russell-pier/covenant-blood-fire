"""
Status bar for displaying game information at the top of the screen.

This module provides a floating status bar with rounded borders
showing current game state, terrain info, and resources.
"""

import tcod


class StatusBar:
    """A floating status bar at the top showing game information."""
    
    def __init__(self):
        """Initialize the status bar."""
        self.is_visible = True
        self.content_height = 1  # 1 line of content
        self.height = 3  # 1 content + 2 border = 3 total
    
    def toggle_visibility(self) -> None:
        """Toggle the visibility of the status bar."""
        self.is_visible = not self.is_visible
    
    def render(self, console: tcod.console.Console, world_generator=None, cursor_pos=None) -> None:
        """
        Render the status bar at the top of the console.
        
        Args:
            console: Console to render to
            world_generator: WorldGenerator for terrain info
            cursor_pos: Current cursor position (x, y)
        """
        if not self.is_visible:
            return
        
        # Calculate floating panel position (1 line margin from top)
        panel_y = 1  # 1 line margin from top
        panel_width = console.width - 4  # 2 chars margin on each side
        panel_x = 2  # Left margin
        
        # No need to clear margins - the world renders behind and panels render on top

        # Background color for the floating panel
        panel_bg = (60, 60, 60)  # Dark gray
        border_fg = (120, 120, 120)  # Light gray for border
        text_fg = (255, 255, 255)  # White text on dark background
        
        # Draw panel background
        for y in range(panel_y, panel_y + self.height):
            for x in range(panel_x, panel_x + panel_width):
                console.print(x, y, " ", bg=panel_bg)
        
        # Draw rounded border
        # Top border
        console.print(panel_x, panel_y, "╭", fg=border_fg, bg=panel_bg)  # Top-left corner
        for x in range(panel_x + 1, panel_x + panel_width - 1):
            console.print(x, panel_y, "─", fg=border_fg, bg=panel_bg)  # Top line
        console.print(panel_x + panel_width - 1, panel_y, "╮", fg=border_fg, bg=panel_bg)  # Top-right corner
        
        # Side borders
        console.print(panel_x, panel_y + 1, "│", fg=border_fg, bg=panel_bg)  # Left side
        console.print(panel_x + panel_width - 1, panel_y + 1, "│", fg=border_fg, bg=panel_bg)  # Right side
        
        # Bottom border
        console.print(panel_x, panel_y + self.height - 1, "╰", fg=border_fg, bg=panel_bg)  # Bottom-left corner
        for x in range(panel_x + 1, panel_x + panel_width - 1):
            console.print(x, panel_y + self.height - 1, "─", fg=border_fg, bg=panel_bg)  # Bottom line
        console.print(panel_x + panel_width - 1, panel_y + self.height - 1, "╯", fg=border_fg, bg=panel_bg)  # Bottom-right corner
        
        # Content area (inside the border)
        content_y = panel_y + 1
        content_x = panel_x + 2  # 2 chars inside the border for padding
        
        # Get terrain and resource info if available
        terrain_info = "Unknown Terrain"
        resource_info = ""
        if world_generator and cursor_pos:
            try:
                # Get layered terrain at cursor position for full info including resources
                layered_terrain = world_generator.get_layered_terrain_at(cursor_pos[0], cursor_pos[1])
                if layered_terrain:
                    # Get current layer
                    current_layer = None
                    if (hasattr(world_generator, 'use_layered_system') and
                        world_generator.use_layered_system and
                        world_generator.camera_3d):
                        current_layer = world_generator.get_current_layer()

                    # Get terrain data for current layer
                    terrain_data = None
                    if current_layer:
                        if current_layer.name == 'SURFACE':
                            terrain_data = layered_terrain.surface
                        elif current_layer.name == 'UNDERGROUND':
                            terrain_data = layered_terrain.underground
                        elif current_layer.name == 'MOUNTAINS' and layered_terrain.mountains:
                            terrain_data = layered_terrain.mountains
                    else:
                        # Default to surface if no layer system
                        terrain_data = layered_terrain.surface

                    if terrain_data:
                        terrain_type = terrain_data.terrain_type.name.replace('_', ' ').title()
                        terrain_info = f"🌍 {terrain_type}"

                        # Check for resource at this position
                        if hasattr(terrain_data, 'resource') and terrain_data.resource:
                            resource = terrain_data.resource
                            resource_name = resource.resource_type.value.replace('_', ' ').title()
                            rarity_emoji = {'common': '⚪', 'rare': '🔵', 'epic': '🟣'}
                            rarity_symbol = rarity_emoji.get(resource.rarity, '⚪')
                            resource_info = f" | {rarity_symbol} {resource_name} ({resource.rarity})"
                else:
                    # Fallback to basic terrain
                    terrain_type_basic = world_generator.get_terrain_at(cursor_pos[0], cursor_pos[1])
                    if terrain_type_basic:
                        terrain_name = terrain_type_basic.name.replace('_', ' ').title()
                        terrain_info = f"🌍 {terrain_name}"
            except Exception as e:
                terrain_info = "🌍 Terrain Info Unavailable"
        
        # Get current layer info
        layer_info = ""
        if (world_generator and 
            hasattr(world_generator, 'use_layered_system') and 
            world_generator.use_layered_system and 
            world_generator.camera_3d):
            current_layer = world_generator.get_current_layer()
            if current_layer:
                layer_name = current_layer.name.title()
                layer_info = f"🏔️ {layer_name}"
        
        # Status bar content - terrain and resource info on left, layer on right
        full_terrain_info = terrain_info + resource_info
        console.print(
            content_x, content_y,
            full_terrain_info,
            fg=text_fg, bg=panel_bg
        )
        
        if layer_info:
            # Right-align the layer info
            layer_text_width = len(layer_info)
            right_x = panel_x + panel_width - layer_text_width - 2  # 2 chars padding from right border
            console.print(
                right_x, content_y,
                layer_info,
                fg=(150, 200, 255), bg=panel_bg  # Light blue text for layer
            )
    
    def get_height(self) -> int:
        """
        Get the total height including margin when visible.
        
        Returns:
            Height in lines including 1 line margin, or 0 if not visible
        """
        return (self.height + 1) if self.is_visible else 0  # +1 for top margin


def create_status_bar() -> StatusBar:
    """
    Create a default status bar.
    
    Returns:
        StatusBar instance
    """
    return StatusBar()
