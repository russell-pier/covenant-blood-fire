import time
import tcod
import tcod.event
import os
import shutil

# NEW: Multi-scale world generation imports
from .world.generators.world_generator import WorldScaleGenerator
from .world.generators.regional_generator import RegionalScaleGenerator
from .world.generators.local_generator import LocalScaleGenerator
from .world.camera.multi_scale_camera import MultiScaleCameraSystem
from .world.data.scale_types import ViewScale
from .world.data.tilemap import get_tile

# Remove legacy imports - using new system only


class Game:
    """Main game class that handles the multi-scale game loop and state."""

    def __init__(self):
        # Get terminal size for responsive design
        self.screen_width, self.screen_height = self._get_terminal_size()

        # Minimum dimensions to ensure UI works properly
        # World view needs 128×96, so set larger minimums
        self.min_width = 130  # 128 + 2 for margins
        self.min_height = 100  # 96 + 4 for UI

        # Ensure minimum dimensions
        self.screen_width = max(self.screen_width, self.min_width)
        self.screen_height = max(self.screen_height, self.min_height)

        # Initialize the console with detected size
        self.console = tcod.console.Console(self.screen_width, self.screen_height)

        # Game state
        self.running = True

        # NEW: Multi-scale world generation system
        world_seed = 1712738967  # Fixed seed for testing
        print(f"Initializing world with seed: {world_seed}")

        # Initialize all three scale generators
        self.world_generator = WorldScaleGenerator(seed=world_seed)
        self.regional_generator = RegionalScaleGenerator(seed=world_seed)
        self.local_generator = LocalScaleGenerator(seed=world_seed)

        # Initialize camera system
        self.camera = MultiScaleCameraSystem(
            console_width=self.screen_width,
            console_height=self.screen_height,
            seed=world_seed
        )

        # Generate the world
        print("Generating world...")
        self.world_map = self.world_generator.generate_complete_world()
        print("World generation complete!")

        # Current context for regional/local generation
        self.current_world_sector = (64, 48)  # Center of world
        self.current_regional_block = (16, 16)  # Center of regional area
        self.current_regional_map = None
        self.current_local_map = None

        # Render distance (in tiles) - how far to generate around current position
        self.world_render_distance = max(self.camera.viewport_width, self.camera.viewport_height)
        self.regional_render_distance = max(self.camera.viewport_width, self.camera.viewport_height) * 2
        self.local_render_distance = max(self.camera.viewport_width, self.camera.viewport_height) * 2

        # Z-level for local map navigation
        self.current_z_level = 0  # 0 = surface, +1 = elevated, -1 = underground

        # Unified cursor system settings
        self.show_cursor = True
        self.cursor_char = "+"
        self.cursor_color = (255, 255, 0)  # Yellow
        self.cursor_bg_color = (100, 100, 0)  # Dark yellow background

        # Cursor positioning system
        self.cursor_screen_x = self.camera.viewport_width // 2  # Center of screen
        self.cursor_screen_y = self.camera.viewport_height // 2
        self.cursor_offset_x = 0  # Offset from center when at map edges
        self.cursor_offset_y = 0

        # Initialize all cameras at center of their respective maps
        self._initialize_centered_cameras()

        # Performance monitoring
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.fps = 60.0

        # Resize handling
        self.last_resize_time = 0
        self.resize_debounce_delay = 0.1  # 100ms debounce
        self.stable_size = (self.screen_width, self.screen_height)

        print(f"Game initialized with {self.screen_width}×{self.screen_height} console")
        print(f"Starting in {self.camera.get_current_scale().value} scale")

    def _initialize_centered_cameras(self):
        """Initialize all cameras at the center of their respective maps."""
        # World scale - center of 128x96 world
        world_camera = self.camera.camera_positions[ViewScale.WORLD]
        world_camera.x = world_camera.target_x = 64.0
        world_camera.y = world_camera.target_y = 48.0

        # Regional scale - center of 32x32 regional area
        regional_camera = self.camera.camera_positions[ViewScale.REGIONAL]
        regional_camera.x = regional_camera.target_x = 16.0
        regional_camera.y = regional_camera.target_y = 16.0

        # Local scale - center of 32x32 local area
        local_camera = self.camera.camera_positions[ViewScale.LOCAL]
        local_camera.x = local_camera.target_x = 16.0
        local_camera.y = local_camera.target_y = 16.0

        # Set current world sector to center
        self.current_world_sector = (64, 48)
        self.current_regional_block = (16, 16)

    def _update_camera_dimensions(self):
        """Update camera dimensions to match current screen size."""
        # Update the camera system with new console dimensions
        self.camera.console_width = self.screen_width
        self.camera.console_height = self.screen_height
        self.camera.viewport_width = self.screen_width - (2 * self.camera.ui_side_margin)
        self.camera.viewport_height = self.screen_height - self.camera.ui_top_height - self.camera.ui_bottom_height

    def _get_terminal_size(self):
        """Get the current terminal size, with fallback to default."""
        try:
            # Try to get terminal size
            size = shutil.get_terminal_size()
            return size.columns, size.lines
        except (OSError, AttributeError):
            # Fallback to default size if terminal size detection fails
            return 80, 50

    def _check_and_handle_resize(self):
        """Check if terminal has been resized and update accordingly."""
        new_width, new_height = self._get_terminal_size()

        # Ensure minimum dimensions
        new_width = max(new_width, self.min_width)
        new_height = max(new_height, self.min_height)

        if new_width != self.screen_width or new_height != self.screen_height:
            # Terminal has been resized
            self.screen_width = new_width
            self.screen_height = new_height

            # Update camera with new dimensions
            self.camera.console_width = new_width
            self.camera.console_height = new_height

            # Create new console with updated dimensions
            self.console = tcod.console.Console(self.screen_width, self.screen_height)

            # Update camera dimensions
            self._update_camera_dimensions()

            return True
        return False

    def _handle_window_resize(self, event, context):
        """Handle window resize events by expanding the character grid."""
        try:
            # Get the new pixel dimensions from the event
            if hasattr(event, 'width') and hasattr(event, 'height'):
                pixel_width = event.width
                pixel_height = event.height

                # Get actual font dimensions from the context
                font_width, font_height = context.recommended_console_size(pixel_width, pixel_height)

                # Ensure minimum dimensions
                new_columns = max(self.min_width, font_width)
                new_rows = max(self.min_height, font_height)

                # Only resize if dimensions actually changed
                if new_columns != self.screen_width or new_rows != self.screen_height:
                    print(f"Window resized: {pixel_width}x{pixel_height} pixels -> {new_columns}x{new_rows} characters")

                    self.screen_width = new_columns
                    self.screen_height = new_rows

                    # Create new console with expanded grid
                    old_console = self.console
                    self.console = tcod.console.Console(self.screen_width, self.screen_height)

                    # Update camera dimensions to match new grid size
                    self._update_camera_dimensions()

                    return True
        except Exception as e:
            print(f"Error handling window resize: {e}")
        return False

    def handle_events(self) -> None:
        """Handle all input events."""
        # Note: Event handling is now done in the main loop for better resize handling
        pass

    def handle_keydown(self, event: tcod.event.KeyDown) -> None:
        """Handle keyboard input for multi-scale system."""
        key = event.sym

        # Scale switching with z,x,c keys
        if key == tcod.event.KeySym.Z:
            self._transition_to_world_scale()
            return
        elif key == tcod.event.KeySym.X:
            self._transition_to_regional_scale()
            return
        elif key == tcod.event.KeySym.C:
            self._transition_to_local_scale()
            return

        # Z-level switching with < and > keys (only in local scale)
        current_scale = self.camera.get_current_scale()
        if current_scale == ViewScale.LOCAL:
            if key == tcod.event.KeySym.COMMA and (event.mod & tcod.event.Modifier.LSHIFT):  # < key
                self.current_z_level = max(-1, self.current_z_level - 1)
                print(f"Z-level: {self.current_z_level} ({'Underground' if self.current_z_level < 0 else 'Surface' if self.current_z_level == 0 else 'Elevated'})")
                return
            elif key == tcod.event.KeySym.PERIOD and (event.mod & tcod.event.Modifier.LSHIFT):  # > key
                self.current_z_level = min(1, self.current_z_level + 1)
                print(f"Z-level: {self.current_z_level} ({'Underground' if self.current_z_level < 0 else 'Surface' if self.current_z_level == 0 else 'Elevated'})")
                return

        # Movement keys (WASD and arrow keys)
        dx, dy = 0, 0
        if key in [tcod.event.KeySym.W, tcod.event.KeySym.UP]:
            dy = -1
        elif key in [tcod.event.KeySym.S, tcod.event.KeySym.DOWN]:
            dy = 1
        elif key in [tcod.event.KeySym.A, tcod.event.KeySym.LEFT]:
            dx = -1
        elif key in [tcod.event.KeySym.D, tcod.event.KeySym.RIGHT]:
            dx = 1

        if dx != 0 or dy != 0:
            self._handle_movement(dx, dy)
            return

        # Toggle cursor
        if key == tcod.event.KeySym.TAB:
            self.show_cursor = not self.show_cursor
            return

        # Quit
        if key == tcod.event.KeySym.ESCAPE or key == tcod.event.KeySym.Q:
            raise SystemExit()

    def _update_context_for_scale_change(self):
        """Update context when changing scales to ensure proper map generation."""
        current_scale = self.camera.get_current_scale()

        if current_scale == ViewScale.REGIONAL:
            # Generate regional map for current world sector if needed
            if self.current_regional_map is None:
                world_tile = self.world_map[self.current_world_sector[1]][self.current_world_sector[0]]

                # Get neighboring world tiles (simplified - empty dict for now)
                neighboring_tiles = {}  # TODO: Add actual neighboring tile lookup

                self.current_regional_map = self.regional_generator.generate_regional_map(
                    world_tile, neighboring_tiles
                )
                print(f"Generated regional map for world sector {self.current_world_sector}")

        elif current_scale == ViewScale.LOCAL:
            # Generate local map for current regional block if needed
            if self.current_local_map is None and self.current_regional_map is not None:
                regional_tile = self.current_regional_map[self.current_regional_block[1]][self.current_regional_block[0]]
                self.current_local_map = self.local_generator.generate_local_chunk(regional_tile, {})
                print(f"Generated local map for regional block {self.current_regional_block}")

    def _transition_to_world_scale(self):
        """Transition to world scale."""
        self.camera.transition_to_scale(ViewScale.WORLD)
        # World scale doesn't need coordinate updates - it's the base level

    def _transition_to_regional_scale(self):
        """Transition to regional scale, updating coordinates based on current cursor position."""
        current_scale = self.camera.get_current_scale()

        if current_scale == ViewScale.WORLD:
            # Drilling down from world to regional - use camera position as cursor
            camera = self.camera.camera_positions[ViewScale.WORLD]
            self.current_world_sector = (int(camera.x), int(camera.y))

            # Center regional camera and reset cursor offsets
            self.camera.transition_to_scale(ViewScale.REGIONAL)
            regional_camera = self.camera.camera_positions[ViewScale.REGIONAL]
            regional_camera.target_x = 16.0  # Center of 32x32 regional map
            regional_camera.target_y = 16.0
            self.cursor_offset_x = 0
            self.cursor_offset_y = 0

        elif current_scale == ViewScale.LOCAL:
            # Zooming out from local to regional
            self.camera.transition_to_scale(ViewScale.REGIONAL)
            self.cursor_offset_x = 0
            self.cursor_offset_y = 0

        # Clear regional map to force regeneration with new coordinates
        self.current_regional_map = None
        self._update_context_for_scale_change()

    def _transition_to_local_scale(self):
        """Transition to local scale, updating coordinates based on current cursor position."""
        current_scale = self.camera.get_current_scale()

        if current_scale == ViewScale.REGIONAL:
            # Drilling down from regional to local - use current cursor regional coordinates
            cursor_regional_x, cursor_regional_y = self._get_cursor_regional_coordinates()
            self.current_regional_block = (int(cursor_regional_x), int(cursor_regional_y))

            # Center local camera and reset cursor offsets
            self.camera.transition_to_scale(ViewScale.LOCAL)
            local_camera = self.camera.camera_positions[ViewScale.LOCAL]
            local_camera.target_x = 16.0  # Center of 32x32 local map
            local_camera.target_y = 16.0
            self.cursor_offset_x = 0
            self.cursor_offset_y = 0

        elif current_scale == ViewScale.WORLD:
            # Direct drill from world to local (go through regional first)
            self._transition_to_regional_scale()
            self._transition_to_local_scale()
            return

        # Clear local map to force regeneration with new coordinates
        self.current_local_map = None
        self._update_context_for_scale_change()

    def _handle_movement(self, dx: int, dy: int):
        """Handle movement with cursor fixed in center except at map boundaries."""
        current_scale = self.camera.get_current_scale()

        if current_scale == ViewScale.WORLD:
            self._handle_world_movement(dx, dy)
        else:
            # Regional and Local use the old system for now
            self.camera.move_camera(dx, dy)

    def _handle_world_movement(self, dx: int, dy: int):
        """Handle world map movement with fixed center cursor except at edges."""
        camera = self.camera.camera_positions[ViewScale.WORLD]
        viewport = self.camera.get_viewport_info()

        # World map bounds
        world_width, world_height = 128, 96

        # Calculate viewport size
        visible_width = min(viewport.viewport_width, world_width)
        visible_height = min(viewport.viewport_height, world_height)
        half_width = visible_width // 2
        half_height = visible_height // 2

        # Calculate new camera position
        new_x = camera.x + dx
        new_y = camera.y + dy

        # Clamp camera to world bounds, keeping cursor centered when possible
        # Left edge: cursor can be at center if camera is at least half_width from left
        min_camera_x = half_width
        max_camera_x = world_width - half_width - 1

        min_camera_y = half_height
        max_camera_y = world_height - half_height - 1

        # If viewport is larger than world, center the world
        if visible_width >= world_width:
            camera.target_x = world_width // 2
        else:
            camera.target_x = max(min_camera_x, min(max_camera_x, new_x))

        if visible_height >= world_height:
            camera.target_y = world_height // 2
        else:
            camera.target_y = max(min_camera_y, min(max_camera_y, new_y))

        # Ensure camera position is within world bounds
        camera.target_x = max(0, min(world_width - 1, camera.target_x))
        camera.target_y = max(0, min(world_height - 1, camera.target_y))

    def _auto_return_cursor_to_center(self):
        """Auto-return cursor to center when camera can move away from edges."""
        current_scale = self.camera.get_current_scale()
        camera = self.camera.get_current_camera_position()

        # Get map bounds
        if current_scale == ViewScale.WORLD:
            map_width, map_height = len(self.world_map[0]), len(self.world_map)
        elif current_scale == ViewScale.REGIONAL:
            if self.current_regional_map:
                map_width, map_height = len(self.current_regional_map[0]), len(self.current_regional_map)
            else:
                return
        else:  # LOCAL
            if self.current_local_map:
                map_width, map_height = len(self.current_local_map[0]), len(self.current_local_map)
            else:
                return

        viewport = self.camera.get_viewport_info()
        half_width = viewport.viewport_width // 2
        half_height = viewport.viewport_height // 2

        # Check if cursor can return to center horizontally
        if self.cursor_offset_x != 0:
            # Calculate if camera can move to accommodate cursor return
            desired_camera_x = camera.target_x - self.cursor_offset_x
            if (desired_camera_x - half_width >= 0 and desired_camera_x + half_width < map_width):
                camera.target_x = desired_camera_x
                self.cursor_offset_x = 0

        # Check if cursor can return to center vertically
        if self.cursor_offset_y != 0:
            # Calculate if camera can move to accommodate cursor return
            desired_camera_y = camera.target_y - self.cursor_offset_y
            if (desired_camera_y - half_height >= 0 and desired_camera_y + half_height < map_height):
                camera.target_y = desired_camera_y
                self.cursor_offset_y = 0

    def _get_cursor_world_coordinates(self):
        """Get current cursor position in world coordinates."""
        camera = self.camera.camera_positions[ViewScale.WORLD]
        viewport = self.camera.get_viewport_info()

        # Calculate cursor position in world coordinates
        cursor_x = camera.x + self.cursor_offset_x
        cursor_y = camera.y + self.cursor_offset_y

        return cursor_x, cursor_y

    def _get_cursor_regional_coordinates(self):
        """Get current cursor position in regional coordinates."""
        camera = self.camera.camera_positions[ViewScale.REGIONAL]
        viewport = self.camera.get_viewport_info()

        # Calculate cursor position in regional coordinates
        cursor_x = camera.x + self.cursor_offset_x
        cursor_y = camera.y + self.cursor_offset_y

        return cursor_x, cursor_y

    def _get_cursor_local_coordinates(self):
        """Get current cursor position in local coordinates."""
        camera = self.camera.camera_positions[ViewScale.LOCAL]
        viewport = self.camera.get_viewport_info()

        # Calculate cursor position in local coordinates
        cursor_x = camera.x + self.cursor_offset_x
        cursor_y = camera.y + self.cursor_offset_y

        return cursor_x, cursor_y





    def render(self) -> None:
        """Render the game using the multi-scale system."""
        # Clear the console
        self.console.clear(fg=(255, 255, 255), bg=(0, 0, 0))

        # Update camera system
        dt = 1.0 / 60.0  # Assume 60 FPS for smooth transitions
        self.camera.update(dt)

        current_scale = self.camera.get_current_scale()

        # Render based on current scale
        if current_scale == ViewScale.WORLD:
            self._render_world_scale()
        elif current_scale == ViewScale.REGIONAL:
            self._render_regional_scale()
        elif current_scale == ViewScale.LOCAL:
            self._render_local_scale()

        # Render UI
        self._render_ui()

        # Update FPS counter
        self._update_fps()

    def _render_world_scale(self):
        """Render world scale as 128x96 grid with fixed center cursor."""
        viewport = self.camera.get_viewport_info()

        # World map is 128x96 - render what fits in viewport
        world_width, world_height = 128, 96

        # Calculate how much of the world map we can show
        visible_width = min(viewport.viewport_width, world_width)
        visible_height = min(viewport.viewport_height, world_height)

        # Calculate camera position (what part of world to show)
        camera = self.camera.camera_positions[ViewScale.WORLD]

        # Calculate world area to display
        start_x = max(0, int(camera.x - visible_width // 2))
        start_y = max(0, int(camera.y - visible_height // 2))
        end_x = min(world_width, start_x + visible_width)
        end_y = min(world_height, start_y + visible_height)

        # Adjust start if we hit the right/bottom edge
        if end_x == world_width:
            start_x = max(0, world_width - visible_width)
        if end_y == world_height:
            start_y = max(0, world_height - visible_height)

        # Calculate cursor position on screen
        cursor_world_x = int(camera.x)
        cursor_world_y = int(camera.y)

        # Cursor screen position (normally center, but can move at edges)
        cursor_screen_x = viewport.viewport_start_x + (cursor_world_x - start_x)
        cursor_screen_y = viewport.viewport_start_y + (cursor_world_y - start_y)

        # Render world tiles
        for world_y in range(start_y, end_y):
            for world_x in range(start_x, end_x):
                if 0 <= world_y < len(self.world_map) and 0 <= world_x < len(self.world_map[0]):
                    tile = self.world_map[world_y][world_x]
                    screen_x = viewport.viewport_start_x + (world_x - start_x)
                    screen_y = viewport.viewport_start_y + (world_y - start_y)

                    if (0 <= screen_x < self.console.width and
                        0 <= screen_y < self.console.height):

                        # Highlight cursor tile
                        if (world_x == cursor_world_x and world_y == cursor_world_y and self.show_cursor):
                            self.console.print(screen_x, screen_y, tile.char,
                                             fg=self.cursor_color, bg=self.cursor_bg_color)
                        else:
                            self.console.print(screen_x, screen_y, tile.char,
                                             fg=tile.fg_color, bg=tile.bg_color)

    def _render_regional_scale(self):
        """Render regional scale view."""
        # Ensure regional map is generated
        self._update_context_for_scale_change()

        if self.current_regional_map is None:
            self.console.print(10, 10, "Generating regional map...", fg=(255, 255, 255))
            return

        viewport = self.camera.get_viewport_info()
        camera_x, camera_y = int(viewport.camera_x), int(viewport.camera_y)

        # Calculate viewport bounds
        start_x = max(0, camera_x - viewport.viewport_width // 2)
        start_y = max(0, camera_y - viewport.viewport_height // 2)
        end_x = min(len(self.current_regional_map[0]), start_x + viewport.viewport_width)
        end_y = min(len(self.current_regional_map), start_y + viewport.viewport_height)

        # Render regional tiles
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                if 0 <= y < len(self.current_regional_map) and 0 <= x < len(self.current_regional_map[0]):
                    tile = self.current_regional_map[y][x]
                    screen_x = viewport.viewport_start_x + (x - start_x)
                    screen_y = viewport.viewport_start_y + (y - start_y)

                    if (0 <= screen_x < self.console.width and
                        0 <= screen_y < self.console.height):

                        # Highlight cursor tile using unified cursor system
                        cursor_screen_x = viewport.viewport_start_x + viewport.viewport_width // 2 + self.cursor_offset_x
                        cursor_screen_y = viewport.viewport_start_y + viewport.viewport_height // 2 + self.cursor_offset_y

                        if screen_x == cursor_screen_x and screen_y == cursor_screen_y and self.show_cursor:
                            self.console.print(screen_x, screen_y, tile.char,
                                             fg=self.cursor_color, bg=self.cursor_bg_color)
                        else:
                            self.console.print(screen_x, screen_y, tile.char,
                                             fg=tile.fg_color, bg=tile.bg_color)

    def _render_local_scale(self):
        """Render local scale view."""
        # Ensure local map is generated
        self._update_context_for_scale_change()

        if self.current_local_map is None:
            self.console.print(10, 10, "Generating local map...", fg=(255, 255, 255))
            return

        viewport = self.camera.get_viewport_info()
        camera_x, camera_y = int(viewport.camera_x), int(viewport.camera_y)

        # Calculate viewport bounds
        start_x = max(0, camera_x - viewport.viewport_width // 2)
        start_y = max(0, camera_y - viewport.viewport_height // 2)
        end_x = min(len(self.current_local_map[0]), start_x + viewport.viewport_width)
        end_y = min(len(self.current_local_map), start_y + viewport.viewport_height)

        # Render local tiles (filter by Z-level)
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                if 0 <= y < len(self.current_local_map) and 0 <= x < len(self.current_local_map[0]):
                    tile = self.current_local_map[y][x]

                    # Filter by Z-level
                    tile_z = 0  # Default to surface
                    if hasattr(tile, 'z_level'):
                        if tile.z_level.value == 'elevated':
                            tile_z = 1
                        elif tile.z_level.value == 'underground':
                            tile_z = -1

                    # Only render tiles at current Z-level
                    if tile_z == self.current_z_level:
                        screen_x = viewport.viewport_start_x + (x - start_x)
                        screen_y = viewport.viewport_start_y + (y - start_y)

                        if (0 <= screen_x < self.console.width and
                            0 <= screen_y < self.console.height):

                            # Highlight cursor tile using unified cursor system
                            cursor_screen_x = viewport.viewport_start_x + viewport.viewport_width // 2 + self.cursor_offset_x
                            cursor_screen_y = viewport.viewport_start_y + viewport.viewport_height // 2 + self.cursor_offset_y

                            if screen_x == cursor_screen_x and screen_y == cursor_screen_y and self.show_cursor:
                                self.console.print(screen_x, screen_y, tile.char,
                                                 fg=self.cursor_color, bg=self.cursor_bg_color)
                            else:
                                self.console.print(screen_x, screen_y, tile.char,
                                                 fg=tile.fg_color, bg=tile.bg_color)



    def _render_ui(self):
        """Render UI elements."""
        current_scale = self.camera.get_current_scale()
        camera_x, camera_y = self.camera.get_camera_position()

        # Top status bar with proper coordinates
        if current_scale == ViewScale.WORLD:
            # World scale shows camera position (which is cursor position)
            camera = self.camera.camera_positions[ViewScale.WORLD]
            status_text = f"Scale: World (128x96) | Cursor: ({int(camera.x)},{int(camera.y)})"
        elif current_scale == ViewScale.REGIONAL:
            cursor_x, cursor_y = self._get_cursor_regional_coordinates()
            status_text = f"Scale: Regional | Cursor: ({cursor_x:.1f},{cursor_y:.1f})"
        else:  # LOCAL
            cursor_x, cursor_y = self._get_cursor_local_coordinates()
            z_level_name = {-1: "Underground", 0: "Surface", 1: "Elevated"}[self.current_z_level]
            status_text = f"Scale: Local | Cursor: ({cursor_x:.1f},{cursor_y:.1f}) | Z-Level: {z_level_name}"

        # Add cursor status
        if self.show_cursor:
            status_text += f" | Cursor: ON"
        else:
            status_text += f" | Cursor: OFF"

        self.console.print(1, 1, status_text, fg=(255, 255, 255), bg=(40, 40, 40))

        # Bottom instructions
        if current_scale == ViewScale.LOCAL:
            instructions = "Z=World  X=Regional  C=Local  |  WASD=Move  <>=Z-Level  TAB=Cursor  ESC=Quit"
        else:
            instructions = "Z=World  X=Regional  C=Local  |  WASD=Move  TAB=Cursor  ESC=Quit"

        self.console.print(1, self.console.height - 2, instructions, fg=(200, 200, 200), bg=(40, 40, 40))

        # Transition indicator
        if self.camera.is_transitioning():
            progress = self.camera.get_transition_progress()
            progress_text = f"Transitioning... {progress*100:.0f}%"
            self.console.print(1, 3, progress_text, fg=(255, 255, 0))

    def _update_fps(self) -> None:
        """Update FPS counter for performance monitoring."""
        self.frame_count += 1
        current_time = time.time()

        # Update FPS every second
        if current_time - self.last_fps_time >= 1.0:
            self.fps = self.frame_count / (current_time - self.last_fps_time)
            self.frame_count = 0
            self.last_fps_time = current_time

    def run(self) -> None:
        """Main game loop."""
        # Use a proportional (non-square) font for better readability
        try:
            # Load a proportional TrueType font - wider than tall for readability
            tileset = tcod.tileset.load_truetype_font("Arial.ttf", 12, 18)  # 12 wide, 18 tall = proportional
        except:
            try:
                # Fallback to another proportional font
                tileset = tcod.tileset.load_truetype_font("DejaVuSans.ttf", 12, 18)
            except:
                try:
                    # Last resort - use system default but make it proportional
                    tileset = tcod.tileset.load_truetype_font("", 12, 18)  # Empty string uses system default
                except:
                    # Final fallback - no custom font
                    tileset = None

        # Create context with proper aspect ratio (no stretching)
        context = tcod.context.new(
            columns=self.screen_width,
            rows=self.screen_height,
            title="Covenant: Blood & Fire - Multi-Scale World Explorer",
            vsync=True,
            tileset=tileset,
            # Prevent stretching - maintain square characters
            renderer=tcod.context.RENDERER_SDL2,
            # Keep aspect ratio
            resizable=True,
        )

        try:
            while self.running:
                # Check if the window has been resized with debouncing
                current_time = time.time()
                recommended_size = context.recommended_console_size()

                # Only process resize if enough time has passed and size is different
                if (recommended_size != self.stable_size and
                    current_time - self.last_resize_time > self.resize_debounce_delay):

                    new_width, new_height = recommended_size
                    if new_width > 0 and new_height > 0:
                        # Ensure minimum dimensions
                        new_width = max(new_width, self.min_width)
                        new_height = max(new_height, self.min_height)

                        # Only resize if the size actually changed significantly
                        if (abs(new_width - self.screen_width) > 1 or
                            abs(new_height - self.screen_height) > 1):

                            print(f"Console resized: {self.screen_width}x{self.screen_height} -> {new_width}x{new_height}")

                            self.screen_width = new_width
                            self.screen_height = new_height
                            self.stable_size = (new_width, new_height)
                            self.last_resize_time = current_time

                            # Create new console with new dimensions
                            self.console = tcod.console.Console(self.screen_width, self.screen_height)

                            # Update camera dimensions
                            self._update_camera_dimensions()

                # Handle events
                for event in tcod.event.get():
                    if event.type == "QUIT":
                        self.running = False
                    elif event.type == "KEYDOWN":
                        self.handle_keydown(event)

                # Render the game
                self.render()

                # Present to screen
                context.present(self.console)

                # Small delay to prevent excessive CPU usage
                time.sleep(0.016)  # ~60 FPS
        finally:
            # Cleanup map renderer background processing
            if hasattr(self, 'map_renderer'):
                self.map_renderer.cleanup()
            context.close()


def main():
    """Entry point for the game."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
