import time
import tcod
import tcod.event
import os
import shutil

# NEW: Multi-scale world generation imports
from .world.generators.world_scale import WorldScaleGenerator
from .world.camera.multi_scale_camera import MultiScaleCameraSystem
from .world.camera.viewport_renderer import MultiScaleViewportRenderer
from .world.data.scale_types import ViewScale
from .world.data.config import get_world_config, create_world_config_file

# Legacy imports for Local scale integration (Phase 5)
from .camera.viewport import create_viewport_system
from .world.generator import create_default_world_generator
from .commands import CommandRegistry, CommandPalette, register_layer_commands
from .ui import create_instructions_panel, create_status_bar
from .ui.zoomed_map import ZoomedMapRenderer


class Game:
    """Main game class that handles the multi-scale game loop and state."""

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

        # Initialize configuration system
        self.config = get_world_config()

        # Create config file if in development mode
        if self.config.is_development_mode():
            create_world_config_file()

        # NEW: Multi-scale world generation system
        world_seed = self.config.get_world_seed()
        print(f"Initializing world with seed: {world_seed}")

        self.world_scale_generator = WorldScaleGenerator(seed=world_seed)
        self.multi_scale_camera = MultiScaleCameraSystem(seed=world_seed)
        self.multi_scale_renderer = MultiScaleViewportRenderer(
            self.world_scale_generator,
            self.multi_scale_camera
        )

        # Legacy systems for Local scale integration (Phase 5)
        self.world_generator = create_default_world_generator(seed=world_seed)
        self.legacy_camera, self.legacy_viewport = create_viewport_system()

        # UI components (preserved from existing design)
        self.instructions_panel = create_instructions_panel()
        self.status_bar = create_status_bar()

        # Command system (preserved for Local scale)
        self.command_registry = CommandRegistry()
        self.command_palette = CommandPalette(self.command_registry)
        register_layer_commands(self.command_registry, self.world_generator, self.instructions_panel, self.status_bar)

        # Legacy zoomed map renderer (for Local scale integration)
        self.map_renderer = ZoomedMapRenderer(self.world_generator, self.console.width, self.console.height)

        # Update multi-scale renderer with current console size
        self.multi_scale_renderer.update_console_size(self.screen_width, self.screen_height)

        # Preload initial chunks around spawn point (for Local scale)
        self.world_generator.preload_chunks_around(0, 0)

        # Performance monitoring
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.fps = 60.0

        # Resize handling
        self.last_resize_time = 0
        self.resize_debounce_delay = 0.1  # 100ms debounce
        self.stable_size = (self.screen_width, self.screen_height)

        # Multi-scale system state
        self.show_world_info = False
        self.last_scale_switch_time = time.time()

        print(f"Game initialized with {self.screen_width}×{self.screen_height} console")
        print(f"Starting in {self.multi_scale_camera.get_current_scale().value} scale")

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

            # Update multi-scale renderer with new dimensions
            self.multi_scale_renderer.update_console_size(new_width, new_height)

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

        # Scale switching (always available)
        if key == tcod.event.KeySym.N1:
            self.multi_scale_camera.change_scale(ViewScale.WORLD)
            self.last_scale_switch_time = time.time()
            return
        elif key == tcod.event.KeySym.N2:
            self.multi_scale_camera.change_scale(ViewScale.REGIONAL)
            self.last_scale_switch_time = time.time()
            return
        elif key == tcod.event.KeySym.N3:
            old_scale = self.multi_scale_camera.get_current_scale()
            self.multi_scale_camera.change_scale(ViewScale.LOCAL)
            # Sync legacy camera when switching to local scale
            if old_scale != ViewScale.LOCAL:
                self._sync_legacy_to_multi_scale_camera()
            self.last_scale_switch_time = time.time()
            return

        current_scale = self.multi_scale_camera.get_current_scale()

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
            if current_scale == ViewScale.LOCAL:
                # Use existing camera system for detailed view
                self.legacy_camera.move(dx, dy)
                # Update world generator with new camera position
                world_x, world_y = self.legacy_camera.get_position()
                self.world_generator.update_camera_position(world_x, world_y)

                # Sync multi-scale camera to match legacy camera position
                self._sync_multi_scale_to_legacy_camera()
            else:
                # Use multi-scale camera for world/regional
                self.multi_scale_camera.move_camera(dx, dy)
            return

        # Drill down functionality
        if key == tcod.event.KeySym.RETURN or key == tcod.event.KeySym.KP_ENTER:
            if current_scale == ViewScale.WORLD:
                self.multi_scale_camera.change_scale(ViewScale.REGIONAL)
            elif current_scale == ViewScale.REGIONAL:
                self.multi_scale_camera.change_scale(ViewScale.LOCAL)
            return

        # Info toggle for world/regional scales
        if key == tcod.event.KeySym.I:
            if current_scale in [ViewScale.WORLD, ViewScale.REGIONAL]:
                self.show_world_info = not self.show_world_info
                return

        # Legacy controls (only in LOCAL scale)
        if current_scale == ViewScale.LOCAL:
            # Layer switching hotkeys
            hotkey_char = None
            if key == tcod.event.KeySym.Z:
                hotkey_char = 'z'
            elif key == tcod.event.KeySym.X:
                hotkey_char = 'x'
            elif key == tcod.event.KeySym.C:
                hotkey_char = 'c'
            elif key == tcod.event.KeySym.M:
                # Toggle map mode
                self.map_renderer.toggle_map_mode()
                mode_name = "Overview" if self.map_renderer.is_overview_mode() else "Detailed"
                print(f"Switched to {mode_name} mode")
                return

            if hotkey_char:
                hotkey_handled = self.command_registry.execute_hotkey(hotkey_char)
                if hotkey_handled:
                    return

        # Quit key (ESC or Q)
        if key == tcod.event.KeySym.ESCAPE or key == tcod.event.KeySym.Q:
            self.running = False

    def _sync_multi_scale_to_legacy_camera(self) -> None:
        """Sync multi-scale camera position to match legacy camera."""
        world_x, world_y = self.legacy_camera.get_position()

        # Update local scale position in multi-scale camera
        local_x = world_x // 32  # Convert to chunk coordinates
        local_y = world_y // 32

        # Set multi-scale camera position for local scale
        old_scale = self.multi_scale_camera.get_current_scale()
        self.multi_scale_camera.change_scale(ViewScale.LOCAL)
        self.multi_scale_camera.set_camera_position(local_x, local_y)
        self.multi_scale_camera.change_scale(old_scale)

    def _sync_legacy_to_multi_scale_camera(self) -> None:
        """Sync legacy camera position to match multi-scale camera."""
        if self.multi_scale_camera.get_current_scale() == ViewScale.LOCAL:
            world_x, world_y = self.multi_scale_camera.get_current_world_coordinates()
            self.legacy_camera.set_position(world_x, world_y)

            # Update world generator
            self.world_generator.update_camera_position(world_x, world_y)

    def render(self) -> None:
        """Render the game using the multi-scale system."""
        # Clear the console
        self.console.clear(fg=(255, 255, 255), bg=(0, 0, 0))

        current_scale = self.multi_scale_camera.get_current_scale()

        if current_scale == ViewScale.LOCAL:
            # Use existing detailed rendering system for Local scale
            self._render_detailed_local_view()
        else:
            # Use new multi-scale rendering for World/Regional scales
            self.multi_scale_renderer.render_current_scale(self.console)

        # Always render UI elements
        self._render_ui_elements()

        # Render command palette (if open)
        self.command_palette.render(self.console)

        # Update FPS counter
        self._update_fps()

    def _render_detailed_local_view(self) -> None:
        """Render detailed local view using existing systems."""
        # Sync multi-scale camera position with legacy camera
        multi_scale_world_x, multi_scale_world_y = self.multi_scale_camera.get_current_world_coordinates()

        # Convert to local chunk coordinates and update legacy camera
        local_chunk_x = multi_scale_world_x // 32  # 32 tiles per chunk
        local_chunk_y = multi_scale_world_y // 32

        # Set legacy camera to show the area around the multi-scale position
        self.legacy_camera.set_position(multi_scale_world_x, multi_scale_world_y)

        # Update map renderer
        camera_x, camera_y = self.legacy_camera.get_position()
        self.map_renderer.set_camera_position(camera_x, camera_y)

        # Update animals continuously (every frame)
        self.world_generator.update_animals_continuous()

        # Store original camera settings for full screen rendering
        original_width = self.legacy_camera.screen_width
        original_height = self.legacy_camera.screen_height
        original_crosshair_x = self.legacy_camera.config.crosshair_x
        original_crosshair_y = self.legacy_camera.config.crosshair_y

        # Set camera to full screen dimensions
        self.legacy_camera.screen_width = self.console.width
        self.legacy_camera.screen_height = self.console.height
        self.legacy_camera.config.crosshair_x = self.console.width // 2
        self.legacy_camera.config.crosshair_y = self.console.height // 2

        # Render world and crosshair
        self.legacy_viewport.render_world(self.console, self.world_generator)
        self.legacy_viewport.render_crosshair(self.console, self.world_generator)

        # Restore original camera settings
        self.legacy_camera.screen_width = original_width
        self.legacy_camera.screen_height = original_height
        self.legacy_camera.config.crosshair_x = original_crosshair_x
        self.legacy_camera.config.crosshair_y = original_crosshair_y

    def _render_ui_elements(self) -> None:
        """Render UI elements appropriate for current scale."""
        current_scale = self.multi_scale_camera.get_current_scale()

        if current_scale == ViewScale.LOCAL:
            # Full UI for detailed view
            camera_x, camera_y = self.legacy_camera.get_position()
            cursor_world_pos = (camera_x, camera_y)
            self.status_bar.render(self.console, self.world_generator, cursor_world_pos)
            self.instructions_panel.render(self.console)
        else:
            # Simplified UI for world/regional views
            self._render_scale_navigation_ui()

    def _render_scale_navigation_ui(self) -> None:
        """Render UI for world/regional scales."""
        current_scale = self.multi_scale_camera.get_current_scale()
        camera_x, camera_y = self.multi_scale_camera.get_camera_position()
        world_x, world_y = self.multi_scale_camera.get_current_world_coordinates()

        # Top status bar with scale info
        status_text = f"Scale: {current_scale.value.title()} | Pos: {camera_x},{camera_y} | World: {world_x},{world_y}"
        if len(status_text) < self.console.width - 4:
            self.console.print(2, 2, status_text, fg=(255, 255, 255), bg=(60, 60, 60))

        # Show world info if requested
        if self.show_world_info:
            self._render_world_info()

        # Bottom instructions
        instructions = "1=World  2=Regional  3=Local  |  WASD=Move  Enter=Drill  I=Info  ESC=Quit"
        if len(instructions) < self.console.width - 4:
            self.console.print(2, self.console.height - 3, instructions, fg=(200, 200, 200), bg=(60, 60, 60))

    def _render_world_info(self) -> None:
        """Render world generation information."""
        world_info = self.world_scale_generator.get_world_info()

        if world_info["status"] == "complete":
            info_lines = [
                f"World Seed: {world_info['seed']}",
                f"Size: {world_info['world_size'][0]}×{world_info['world_size'][1]} sectors",
                f"Avg Elevation: {world_info['average_elevation']:.1f}m",
                f"Mountain Ranges: {world_info['major_mountain_ranges']}",
                f"River Systems: {world_info['major_river_systems']}",
                f"Generation Time: {world_info['generation_time']:.2f}s"
            ]

            # Render info box
            start_y = 5
            for i, line in enumerate(info_lines):
                if start_y + i < self.console.height - 5:
                    self.console.print(2, start_y + i, line, fg=(200, 200, 200), bg=(40, 40, 40))

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
