"""
Camera and viewport system for managing world view and rendering.

This module provides camera movement and viewport management, replacing
direct player movement with a scrolling world view system.
"""

from dataclasses import dataclass
from typing import Tuple

import tcod


@dataclass
class CameraConfig:
    """Configuration for camera behavior."""
    
    crosshair_x: int = 40
    crosshair_y: int = 25
    movement_speed: int = 1
    smooth_scrolling: bool = False


class Camera:
    """
    Camera system that manages world position and movement.
    
    The camera represents the player's view into the world, with a fixed
    crosshair cursor and scrolling world underneath.
    """
    
    def __init__(self, config: CameraConfig = None):
        """
        Initialize the camera system.
        
        Args:
            config: Camera configuration (uses default if None)
        """
        self.config = config or CameraConfig()
        
        # Camera position in world coordinates
        self.world_x = 0
        self.world_y = 0
        
        # Screen dimensions (should match console size)
        self.screen_width = 80
        self.screen_height = 50
    
    def move(self, dx: int, dy: int) -> None:
        """
        Move the camera by the specified offset.
        
        Args:
            dx: Change in X position
            dy: Change in Y position
        """
        self.world_x += dx * self.config.movement_speed
        self.world_y += dy * self.config.movement_speed
    
    def set_position(self, world_x: int, world_y: int) -> None:
        """
        Set the camera to a specific world position.
        
        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
        """
        self.world_x = world_x
        self.world_y = world_y
    
    def get_position(self) -> Tuple[int, int]:
        """
        Get the current camera position in world coordinates.
        
        Returns:
            Tuple of (world_x, world_y)
        """
        return self.world_x, self.world_y
    
    def screen_to_world(self, screen_x: int, screen_y: int) -> Tuple[int, int]:
        """
        Convert screen coordinates to world coordinates.
        
        Args:
            screen_x: Screen X coordinate
            screen_y: Screen Y coordinate
            
        Returns:
            Tuple of (world_x, world_y)
        """
        # Calculate offset from crosshair position
        offset_x = screen_x - self.config.crosshair_x
        offset_y = screen_y - self.config.crosshair_y
        
        # Add to camera world position
        world_x = self.world_x + offset_x
        world_y = self.world_y + offset_y
        
        return world_x, world_y
    
    def world_to_screen(self, world_x: int, world_y: int) -> Tuple[int, int]:
        """
        Convert world coordinates to screen coordinates.
        
        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            
        Returns:
            Tuple of (screen_x, screen_y), or None if off-screen
        """
        # Calculate offset from camera position
        offset_x = world_x - self.world_x
        offset_y = world_y - self.world_y
        
        # Add to crosshair position
        screen_x = self.config.crosshair_x + offset_x
        screen_y = self.config.crosshair_y + offset_y
        
        return screen_x, screen_y
    
    def is_position_visible(self, world_x: int, world_y: int) -> bool:
        """
        Check if a world position is visible on screen.
        
        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            
        Returns:
            True if the position is visible on screen
        """
        screen_x, screen_y = self.world_to_screen(world_x, world_y)
        
        return (0 <= screen_x < self.screen_width and 
                0 <= screen_y < self.screen_height)
    
    def get_visible_world_bounds(self) -> Tuple[int, int, int, int]:
        """
        Get the world coordinate bounds of the visible area.
        
        Returns:
            Tuple of (min_x, min_y, max_x, max_y) in world coordinates
        """
        # Top-left corner of screen in world coordinates
        min_x, min_y = self.screen_to_world(0, 0)
        
        # Bottom-right corner of screen in world coordinates
        max_x, max_y = self.screen_to_world(
            self.screen_width - 1, 
            self.screen_height - 1
        )
        
        return min_x, min_y, max_x, max_y


class Viewport:
    """
    Viewport system that manages rendering of the world through the camera.
    
    This class handles the rendering of world tiles to the screen console
    based on the camera position and visible area.
    """
    
    def __init__(self, camera: Camera):
        """
        Initialize the viewport with a camera.
        
        Args:
            camera: Camera instance to use for rendering
        """
        self.camera = camera
    
    def render_world(self, console: tcod.console.Console, world_generator) -> None:
        """
        Render the visible world to the console.
        
        Args:
            console: tcod console to render to
            world_generator: WorldGenerator instance for terrain data
        """
        # Get visible world bounds
        min_x, min_y, max_x, max_y = self.camera.get_visible_world_bounds()
        
        # Render each visible world tile
        for world_y in range(min_y, max_y + 1):
            for world_x in range(min_x, max_x + 1):
                # Get screen position for this world tile
                screen_x, screen_y = self.camera.world_to_screen(world_x, world_y)
                
                # Skip if somehow off-screen
                if not (0 <= screen_x < console.width and 
                       0 <= screen_y < console.height):
                    continue
                
                # Get terrain at this world position - use layered rendering if available
                if (hasattr(world_generator, 'use_layered_system') and
                    world_generator.use_layered_system and
                    hasattr(world_generator, 'get_layered_terrain_at')):
                    # Get layered terrain data and render based on current layer
                    layered_data = world_generator.get_layered_terrain_at(world_x, world_y)
                    if layered_data and world_generator.camera_3d:
                        rendered_terrain = world_generator.camera_3d.get_render_data(layered_data)
                        # Render using the layered terrain data directly
                        console.print(
                            screen_x, screen_y,
                            rendered_terrain.char,
                            fg=rendered_terrain.fg_color,
                            bg=rendered_terrain.bg_color
                        )
                        continue

                # Fallback to regular terrain rendering
                terrain_type = world_generator.get_terrain_at(world_x, world_y)

                # Use organic terrain properties if available
                if hasattr(world_generator, 'use_organic_system') and world_generator.use_organic_system:
                    organic_props = world_generator.get_organic_terrain_properties_at(world_x, world_y)
                    if organic_props:
                        terrain_props = organic_props
                    else:
                        terrain_props = world_generator.terrain_mapper.get_terrain_properties(terrain_type)
                # Use environmental color variations if available
                elif (hasattr(world_generator, 'use_environmental_system') and
                      world_generator.use_environmental_system and
                      hasattr(world_generator.terrain_mapper, 'get_terrain_properties_with_variation')):
                    env_data = world_generator.get_environmental_data_at(world_x, world_y)
                    if env_data:
                        terrain_props = world_generator.terrain_mapper.get_terrain_properties_with_variation(
                            terrain_type, env_data, world_x, world_y
                        )
                    else:
                        terrain_props = world_generator.terrain_mapper.get_terrain_properties(terrain_type)
                else:
                    terrain_props = world_generator.terrain_mapper.get_terrain_properties(terrain_type)



                # Render the terrain tile
                console.print(
                    screen_x, screen_y,
                    terrain_props.character,
                    fg=terrain_props.foreground_color,
                    bg=terrain_props.background_color
                )

        # Render animals on top of terrain
        self.render_animals(console, world_generator)

    def render_animals(self, console: tcod.console.Console, world_generator) -> None:
        """
        Render animals on top of the terrain.

        Args:
            console: tcod console to render to
            world_generator: WorldGenerator instance for animal data
        """
        if not hasattr(world_generator, 'get_animal_positions'):
            return

        # Get all animal positions
        animal_positions = world_generator.get_animal_positions()

        # Render each animal
        for world_x, world_y, char, color in animal_positions:
            # Convert world position to screen position
            screen_x, screen_y = self.camera.world_to_screen(world_x, world_y)

            # Only render if on screen
            if (0 <= screen_x < console.width and
                0 <= screen_y < console.height):
                console.print(
                    screen_x, screen_y,
                    char,
                    fg=color
                )

    def render_crosshair(self, console: tcod.console.Console, world_generator=None) -> None:
        """
        Render the crosshair cursor at the center of the screen.

        Args:
            console: tcod console to render to
            world_generator: WorldGenerator instance to get terrain character
        """
        crosshair_x = self.camera.config.crosshair_x
        crosshair_y = self.camera.config.crosshair_y

        # Get the character that's underneath the cursor
        cursor_char = " "  # Default fallback

        if world_generator:
            try:
                # Get world position at cursor
                world_x, world_y = self.camera.get_position()

                # Get terrain type and properties at cursor position
                terrain_type = world_generator.get_terrain_at(world_x, world_y)

                # Check if we have environmental variations
                if (hasattr(world_generator, 'use_environmental_system') and
                    world_generator.use_environmental_system and
                    hasattr(world_generator, 'get_environmental_data_at')):
                    env_data = world_generator.get_environmental_data_at(world_x, world_y)
                    if env_data:
                        terrain_props = world_generator.terrain_mapper.get_terrain_properties_with_variation(
                            terrain_type, env_data, world_x, world_y
                        )
                    else:
                        terrain_props = world_generator.terrain_mapper.get_terrain_properties(terrain_type)
                else:
                    terrain_props = world_generator.terrain_mapper.get_terrain_properties(terrain_type)

                cursor_char = terrain_props.character

            except Exception:
                # If anything goes wrong, use defaults
                cursor_char = " "

        # Render the cursor with the underlying character, black foreground, and yellow background
        console.print(
            crosshair_x, crosshair_y,
            cursor_char,
            fg=(0, 0, 0),  # Black foreground
            bg=(255, 215, 0)  # Golden yellow background
        )
    
    def render_ui(self, console: tcod.console.Console, fps: float = None, world_generator=None) -> None:
        """
        Render minimal UI information on the screen.

        Args:
            console: tcod console to render to
            fps: Current FPS for display (optional)
            world_generator: WorldGenerator instance for layered system info (optional)
        """
        # Display current layer in top-left corner
        if (world_generator and
            hasattr(world_generator, 'use_layered_system') and
            world_generator.use_layered_system and
            world_generator.camera_3d):
            current_layer = world_generator.get_current_layer()
            if current_layer:
                layer_name = current_layer.name.title()
                console.print(
                    2, 1,
                    f"🏔️ {layer_name}",
                    fg=(150, 200, 255)
                )

        # Display FPS in top-right corner if provided
        if fps is not None:
            fps_color = (0, 255, 0) if fps >= 55 else (255, 255, 0) if fps >= 30 else (255, 0, 0)
            fps_text = f"⚡ {fps:.1f}"
            console.print(
                console.width - len(fps_text) - 2, 1,
                fps_text,
                fg=fps_color
            )


def create_default_camera() -> Camera:
    """
    Create a camera with default configuration.
    
    Returns:
        Camera instance with default settings
    """
    return Camera()


def create_viewport_system() -> Tuple[Camera, Viewport]:
    """
    Create a complete camera and viewport system.
    
    Returns:
        Tuple of (Camera, Viewport) instances
    """
    camera = create_default_camera()
    viewport = Viewport(camera)
    return camera, viewport
