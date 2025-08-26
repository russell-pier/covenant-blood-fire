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

        # Z-level for local map navigation
        self.current_z_level = 0  # 0 = surface, +1 = elevated, -1 = underground

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
            self.camera.transition_to_scale(ViewScale.WORLD)
            self._update_context_for_scale_change()
            return
        elif key == tcod.event.KeySym.X:
            self.camera.transition_to_scale(ViewScale.REGIONAL)
            self._update_context_for_scale_change()
            return
        elif key == tcod.event.KeySym.C:
            self.camera.transition_to_scale(ViewScale.LOCAL)
            self._update_context_for_scale_change()
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
            self.camera.move_camera(dx, dy)
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
                self.current_regional_map = self.regional_generator.generate_regional_sector(
                    world_tile, self.current_world_sector[0], self.current_world_sector[1]
                )
                print(f"Generated regional map for world sector {self.current_world_sector}")

        elif current_scale == ViewScale.LOCAL:
            # Generate local map for current regional block if needed
            if self.current_local_map is None and self.current_regional_map is not None:
                regional_tile = self.current_regional_map[self.current_regional_block[1]][self.current_regional_block[0]]
                self.current_local_map = self.local_generator.generate_local_chunk(regional_tile, {})
                print(f"Generated local map for regional block {self.current_regional_block}")





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
        """Render world scale view."""
        viewport = self.camera.get_viewport_info()
        camera_x, camera_y = int(viewport.camera_x), int(viewport.camera_y)

        # Calculate viewport bounds
        start_x = max(0, camera_x - viewport.viewport_width // 2)
        start_y = max(0, camera_y - viewport.viewport_height // 2)
        end_x = min(len(self.world_map[0]), start_x + viewport.viewport_width)
        end_y = min(len(self.world_map), start_y + viewport.viewport_height)

        # Render world tiles
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                if 0 <= y < len(self.world_map) and 0 <= x < len(self.world_map[0]):
                    tile = self.world_map[y][x]
                    screen_x = viewport.viewport_start_x + (x - start_x)
                    screen_y = viewport.viewport_start_y + (y - start_y)

                    if (0 <= screen_x < self.console.width and
                        0 <= screen_y < self.console.height):
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
                            self.console.print(screen_x, screen_y, tile.char,
                                             fg=tile.fg_color, bg=tile.bg_color)

    def _render_ui(self):
        """Render UI elements."""
        current_scale = self.camera.get_current_scale()
        camera_x, camera_y = self.camera.get_camera_position()

        # Top status bar
        status_text = f"Scale: {current_scale.value.title()} | Pos: ({camera_x:.1f},{camera_y:.1f})"
        if current_scale == ViewScale.LOCAL:
            z_level_name = {-1: "Underground", 0: "Surface", 1: "Elevated"}[self.current_z_level]
            status_text += f" | Z-Level: {z_level_name}"

        self.console.print(1, 1, status_text, fg=(255, 255, 255), bg=(40, 40, 40))

        # Bottom instructions
        if current_scale == ViewScale.LOCAL:
            instructions = "Z=World  X=Regional  C=Local  |  WASD=Move  <>=Z-Level  ESC=Quit"
        else:
            instructions = "Z=World  X=Regional  C=Local  |  WASD=Move  ESC=Quit"

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
        # Create context that supports window resizing
        context = tcod.context.new(
            columns=self.screen_width,
            rows=self.screen_height,
            title="Covenant: Blood & Fire - Responsive Grid (Resize window to expand grid!)",
            vsync=True,
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
