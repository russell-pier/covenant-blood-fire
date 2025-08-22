import time
import tcod
import tcod.event

from .camera.viewport import create_viewport_system
from .world.generator import create_default_world_generator
from .commands import CommandRegistry, CommandPalette, register_layer_commands
from .ui import create_instructions_panel, create_status_bar


class Game:
    """Main game class that handles the game loop and state."""

    def __init__(self):
        # Console dimensions
        self.screen_width = 80
        self.screen_height = 50

        # Initialize the console
        self.console = tcod.console.Console(self.screen_width, self.screen_height)

        # Game state
        self.running = True

        # Initialize world generation system
        self.world_generator = create_default_world_generator()

        # Initialize camera and viewport system
        self.camera, self.viewport = create_viewport_system()

        # Initialize UI components
        self.instructions_panel = create_instructions_panel()
        self.status_bar = create_status_bar()

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

    def handle_events(self) -> None:
        """Handle all input events."""
        for event in tcod.event.get():
            if event.type == "QUIT":
                self.running = False
            elif event.type == "KEYDOWN":
                self.handle_keydown(event)

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

        # Direct hotkeys for layer switching
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

        if hotkey_char:
            hotkey_handled = self.command_registry.execute_hotkey(hotkey_char)
            if hotkey_handled:
                return

        # Movement keys (arrow keys and WASD) - now move camera instead of player
        if key == tcod.event.KeySym.UP or key == tcod.event.KeySym.W:
            self.camera.move(0, -1)
        elif key == tcod.event.KeySym.DOWN or key == tcod.event.KeySym.S:
            self.camera.move(0, 1)
        elif key == tcod.event.KeySym.LEFT or key == tcod.event.KeySym.A:
            self.camera.move(-1, 0)
        elif key == tcod.event.KeySym.RIGHT or key == tcod.event.KeySym.D:
            self.camera.move(1, 0)

        # Quit key (ESC or Q)
        elif key == tcod.event.KeySym.ESCAPE or key == tcod.event.KeySym.Q:
            self.running = False

        # Update world generator with new camera position
        world_x, world_y = self.camera.get_position()
        self.world_generator.update_camera_position(world_x, world_y)

    def render(self) -> None:
        """Render the game to the console."""
        # Update animals continuously (every frame)
        self.world_generator.update_animals_continuous()

        # Clear the console with a consistent background
        self.console.clear(fg=(255, 255, 255), bg=(0, 0, 0))

        # Since panels are floating on top, world should render to full screen
        # Store original camera settings
        original_width = self.camera.screen_width
        original_height = self.camera.screen_height
        original_crosshair_x = self.camera.config.crosshair_x
        original_crosshair_y = self.camera.config.crosshair_y

        # Set camera to full screen dimensions
        self.camera.screen_width = self.console.width
        self.camera.screen_height = self.console.height

        # Keep crosshair in center of full screen
        self.camera.config.crosshair_x = self.console.width // 2
        self.camera.config.crosshair_y = self.console.height // 2

        # Render world directly to the main console
        # The panels will render on top and cover any world content in their areas
        self.viewport.render_world(self.console, self.world_generator)

        # Render crosshair
        self.viewport.render_crosshair(self.console, self.world_generator)

        # Restore original camera settings
        self.camera.screen_width = original_width
        self.camera.screen_height = original_height
        self.camera.config.crosshair_x = original_crosshair_x
        self.camera.config.crosshair_y = original_crosshair_y

        # Render floating UI panels
        # Get world position for cursor (convert screen to world coordinates)
        world_x, world_y = self.camera.get_position()
        cursor_world_pos = (world_x, world_y)
        self.status_bar.render(self.console, self.world_generator, cursor_world_pos)
        self.instructions_panel.render(self.console)

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
        # Use default tcod font - it actually has good box drawing support
        # The kerning issue might be less noticeable with proper character choices
        with tcod.context.new(
            columns=self.screen_width,
            rows=self.screen_height,
            title="Covenant: Blood & Fire",
            vsync=True,
        ) as context:

            while self.running:
                # Handle events
                self.handle_events()

                # Render the game
                self.render()

                # Present to screen
                context.present(self.console)

                # Small delay to prevent excessive CPU usage
                time.sleep(0.016)  # ~60 FPS


def main():
    """Entry point for the game."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
