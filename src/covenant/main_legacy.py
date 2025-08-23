import time
import tcod
import tcod.event
import os
import shutil

from .camera.viewport import create_viewport_system
from .world.generator import create_default_world_generator
from .commands import CommandRegistry, CommandPalette, register_layer_commands
from .ui import create_instructions_panel, create_status_bar
from .ui.zoomed_map import ZoomedMapRenderer


class Game:
    """Main game class that handles the game loop and state."""

    def __init__(self):
        # Get terminal size for responsive design
        self.screen_width, self.screen_height = self._get_terminal_size()

        # Minimum dimensions to ensure UI works properly
        self.min_width = 60
        self.min_height = 30

        # Ensure minimum dimensions
        self.screen_width = max(self.screen_width, self.min_width)
        self.screen_height = max(self.screen_height, self.min_height)

        # Initialize the console with detected size
        self.console = tcod.console.Console(self.screen_width, self.screen_height)

        # Game state
        self.running = True

        # Initialize world generation system
        self.world_generator = create_default_world_generator()

        # Initialize camera and viewport system with responsive dimensions
        self.camera, self.viewport = create_viewport_system()
        self._update_camera_dimensions()

        # Initialize UI components
        self.instructions_panel = create_instructions_panel()
        self.status_bar = create_status_bar()

        # Initialize zoomed map system
        self.map_renderer = ZoomedMapRenderer(self.world_generator, self.console.width, self.console.height)

        # Initialize command system
        self.command_registry = CommandRegistry()
        self.command_palette = CommandPalette(self.command_registry)

        # Register layer commands with UI panels
        register_layer_commands(self.command_registry, self.world_generator, self.instructions_panel, self.status_bar)

        # Preload initial chunks around spawn point
        self.world_generator.preload_chunks_around(0, 0)

        # Performance monitoring
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.fps = 60.0

        # Resize handling
        self.last_resize_time = 0
        self.resize_debounce_delay = 0.1  # 100ms debounce
        self.stable_size = (self.screen_width, self.screen_height)

    def _get_terminal_size(self):
        """Get the current terminal size, with fallback to default."""
        try:
            # Try to get terminal size
            size = shutil.get_terminal_size()
            return size.columns, size.lines
        except (OSError, AttributeError):
            # Fallback to default size if terminal size detection fails
            return 80, 50

    def _update_camera_dimensions(self):
        """Update camera dimensions to match current screen size."""
        self.camera.screen_width = self.screen_width
        self.camera.screen_height = self.screen_height

        # Update crosshair position to center of screen
        self.camera.config.crosshair_x = self.screen_width // 2
        self.camera.config.crosshair_y = self.screen_height // 2

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
        """Handle keyboard input."""
        # First, let command palette handle input if it's open
        if self.command_palette.handle_input(event):
            return

        key = event.sym

        # Command palette toggle (CMD+K or CTRL+K)
        if ((event.mod & tcod.event.Modifier.LCTRL or event.mod & tcod.event.Modifier.RCTRL or
             event.mod & tcod.event.Modifier.LGUI or event.mod & tcod.event.Modifier.RGUI) and
            key == tcod.event.KeySym.K):
            self.command_palette.open()
            return

        # Direct hotkeys for layer switching and map
        # Convert key symbol to character for hotkey matching
        hotkey_char = None
        if key == tcod.event.KeySym.Z:
            hotkey_char = 'z'
        elif key == tcod.event.KeySym.X:
            hotkey_char = 'x'
        elif key == tcod.event.KeySym.C:
            hotkey_char = 'c'
        elif key == tcod.event.KeySym.I:
            hotkey_char = 'i'
        elif key == tcod.event.KeySym.M:
            # Toggle map mode
            self.map_renderer.toggle_map_mode()
            mode_name = "Overview" if self.map_renderer.is_overview_mode() else "Detailed"
            print(f"Switched to {mode_name} mode")
            return  # Don't process as hotkey

        if hotkey_char:
            hotkey_handled = self.command_registry.execute_hotkey(hotkey_char)
            if hotkey_handled:
                return

        # Movement keys (arrow keys and WASD) - now move camera instead of player
        if key == tcod.event.KeySym.UP or key == tcod.event.KeySym.W:
            if self.map_renderer.is_detailed_mode():
                self.camera.move(0, -1)
            else:
                self.map_renderer.handle_movement(0, -1)
        elif key == tcod.event.KeySym.DOWN or key == tcod.event.KeySym.S:
            if self.map_renderer.is_detailed_mode():
                self.camera.move(0, 1)
            else:
                self.map_renderer.handle_movement(0, 1)
        elif key == tcod.event.KeySym.LEFT or key == tcod.event.KeySym.A:
            if self.map_renderer.is_detailed_mode():
                self.camera.move(-1, 0)
            else:
                self.map_renderer.handle_movement(-1, 0)
        elif key == tcod.event.KeySym.RIGHT or key == tcod.event.KeySym.D:
            if self.map_renderer.is_detailed_mode():
                self.camera.move(1, 0)
            else:
                self.map_renderer.handle_movement(1, 0)

        # Enter key for fast travel in overview mode
        elif key == tcod.event.KeySym.RETURN or key == tcod.event.KeySym.KP_ENTER:
            if self.map_renderer.is_overview_mode():
                self.map_renderer.fast_travel_to_cursor()
                return

        # Quit key (ESC or Q)
        elif key == tcod.event.KeySym.ESCAPE or key == tcod.event.KeySym.Q:
            self.running = False

        # Update world generator with new camera position
        world_x, world_y = self.camera.get_position()
        self.world_generator.update_camera_position(world_x, world_y)

    def render(self) -> None:
        """Render the game to the console."""
        # Clear the console
        self.console.clear(fg=(255, 255, 255), bg=(0, 0, 0))

        # Update camera position in map renderer
        camera_x, camera_y = self.camera.get_position()
        self.map_renderer.set_camera_position(camera_x, camera_y)

        # Update animals continuously (every frame)
        self.world_generator.update_animals_continuous()

        if self.map_renderer.is_detailed_mode():
            # Render detailed mode with full UI
            # Store original camera settings for full screen rendering
            original_width = self.camera.screen_width
            original_height = self.camera.screen_height
            original_crosshair_x = self.camera.config.crosshair_x
            original_crosshair_y = self.camera.config.crosshair_y

            # Set camera to full screen dimensions
            self.camera.screen_width = self.console.width
            self.camera.screen_height = self.console.height
            self.camera.config.crosshair_x = self.console.width // 2
            self.camera.config.crosshair_y = self.console.height // 2

            # Render world and crosshair
            self.viewport.render_world(self.console, self.world_generator)
            self.viewport.render_crosshair(self.console, self.world_generator)

            # Restore original camera settings
            self.camera.screen_width = original_width
            self.camera.screen_height = original_height
            self.camera.config.crosshair_x = original_crosshair_x
            self.camera.config.crosshair_y = original_crosshair_y

            # Render floating UI panels
            cursor_world_pos = (camera_x, camera_y)
            self.status_bar.render(self.console, self.world_generator, cursor_world_pos)
            self.instructions_panel.render(self.console)
        else:
            # Render overview mode
            self.map_renderer.render_current_mode(self.console)

        # Render command palette (if open)
        self.command_palette.render(self.console)

        # Update FPS counter
        self._update_fps()

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
