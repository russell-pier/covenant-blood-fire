"""
Input handler for the three-tier world generation system.

This module provides the InputHandler class that processes keyboard
and mouse events, translating them into appropriate actions for the
view manager and camera system.
"""

import tcod.event
from typing import Optional, Callable, Dict, Any

try:
    from .world_types import ViewScale
    from .view_manager import ViewManager
except ImportError:
    from world_types import ViewScale
    from view_manager import ViewManager


class InputHandler:
    """
    Handler for keyboard and mouse input events.
    
    Processes user input and translates it into appropriate actions:
    - Scale switching (1/2/3 keys)
    - Camera movement (WASD keys)
    - Mouse clicks for selection
    - System controls (ESC to quit)
    
    Attributes:
        view_manager: View manager to control
        quit_callback: Function to call when quit is requested
        movement_speed: Camera movement speed
        key_bindings: Dictionary mapping keys to actions
    """
    
    def __init__(
        self,
        view_manager: ViewManager,
        quit_callback: Optional[Callable[[], None]] = None
    ) -> None:
        """
        Initialize the input handler.
        
        Args:
            view_manager: View manager to control
            quit_callback: Function to call when quit is requested
        """
        self.view_manager = view_manager
        self.quit_callback = quit_callback
        self.movement_speed = 1
        
        # Key binding configuration
        self.key_bindings = {
            # Scale switching
            tcod.event.KeySym.N1: self._switch_to_world,
            tcod.event.KeySym.N2: self._switch_to_regional,
            tcod.event.KeySym.N3: self._switch_to_local,

            # Camera movement (WASD)
            tcod.event.KeySym.W: lambda: self._move_camera(0, -1),
            tcod.event.KeySym.A: lambda: self._move_camera(-1, 0),
            tcod.event.KeySym.S: lambda: self._move_camera(0, 1),
            tcod.event.KeySym.D: lambda: self._move_camera(1, 0),

            # Alternative movement (arrow keys)
            tcod.event.KeySym.UP: lambda: self._move_camera(0, -1),
            tcod.event.KeySym.LEFT: lambda: self._move_camera(-1, 0),
            tcod.event.KeySym.DOWN: lambda: self._move_camera(0, 1),
            tcod.event.KeySym.RIGHT: lambda: self._move_camera(1, 0),

            # System controls
            tcod.event.KeySym.ESCAPE: self._quit,
            tcod.event.KeySym.Q: self._quit,

            # UI toggles
            tcod.event.KeySym.H: self._toggle_help,
            tcod.event.KeySym.F1: self._toggle_help,
        }
        
        # Track key states for smooth movement
        self.pressed_keys = set()
    
    def handle_event(self, event: tcod.event.Event) -> bool:
        """
        Handle a single input event.
        
        Args:
            event: Event to handle
            
        Returns:
            True if event was handled, False otherwise
        """
        if event.type == "KEYDOWN":
            return self.handle_keydown(event)
        elif event.type == "KEYUP":
            return self.handle_keyup(event)
        elif event.type == "MOUSEBUTTONDOWN":
            return self.handle_mouse_click(event)
        elif event.type == "QUIT":
            self._quit()
            return True
        
        return False
    
    def handle_keydown(self, event: tcod.event.KeyDown) -> bool:
        """
        Handle key press events.
        
        Args:
            event: Key down event
            
        Returns:
            True if key was handled
        """
        key_sym = event.sym
        
        # Add to pressed keys for movement
        self.pressed_keys.add(key_sym)
        
        # Handle key binding
        if key_sym in self.key_bindings:
            action = self.key_bindings[key_sym]
            action()
            return True
        
        return False
    
    def handle_keyup(self, event: tcod.event.KeyUp) -> bool:
        """
        Handle key release events.
        
        Args:
            event: Key up event
            
        Returns:
            True if key was handled
        """
        key_sym = event.sym
        
        # Remove from pressed keys
        self.pressed_keys.discard(key_sym)
        
        return False
    
    def handle_mouse_click(self, event: tcod.event.MouseButtonDown) -> bool:
        """
        Handle mouse click events.
        
        Args:
            event: Mouse button down event
            
        Returns:
            True if click was handled
        """
        if event.button == tcod.event.BUTTON_LEFT:
            return self.view_manager.handle_mouse_click(event.tile.x, event.tile.y)
        
        return False
    
    def update(self) -> None:
        """
        Update handler state (for continuous movement).
        
        Called each frame to handle held keys for smooth movement.
        """
        # Handle continuous movement for held keys
        movement_keys = {
            tcod.event.KeySym.W: (0, -1),
            tcod.event.KeySym.A: (-1, 0),
            tcod.event.KeySym.S: (0, 1),
            tcod.event.KeySym.D: (1, 0),
            tcod.event.KeySym.UP: (0, -1),
            tcod.event.KeySym.LEFT: (-1, 0),
            tcod.event.KeySym.DOWN: (0, 1),
            tcod.event.KeySym.RIGHT: (1, 0),
        }
        
        # Apply movement for all currently pressed movement keys
        total_dx, total_dy = 0, 0
        for key_sym in self.pressed_keys:
            if key_sym in movement_keys:
                dx, dy = movement_keys[key_sym]
                total_dx += dx
                total_dy += dy
        
        # Apply accumulated movement
        if total_dx != 0 or total_dy != 0:
            self._move_camera(total_dx, total_dy)
    
    def _switch_to_world(self) -> None:
        """Switch to world view scale."""
        self.view_manager.switch_to_scale(ViewScale.WORLD)
    
    def _switch_to_regional(self) -> None:
        """Switch to regional view scale."""
        self.view_manager.switch_to_scale(ViewScale.REGIONAL)
    
    def _switch_to_local(self) -> None:
        """Switch to local view scale."""
        self.view_manager.switch_to_scale(ViewScale.LOCAL)
    
    def _move_camera(self, dx: int, dy: int) -> None:
        """
        Move camera by relative offset.
        
        Args:
            dx: Horizontal movement
            dy: Vertical movement
        """
        # Apply movement speed
        actual_dx = dx * self.movement_speed
        actual_dy = dy * self.movement_speed
        
        self.view_manager.move_camera(actual_dx, actual_dy)
    
    def _quit(self) -> None:
        """Handle quit request."""
        if self.quit_callback:
            self.quit_callback()
    
    def _toggle_help(self) -> None:
        """Toggle help display."""
        # Toggle bottom bar help (if implemented)
        self.view_manager.toggle_ui_component('bottom_bar')
    
    def set_movement_speed(self, speed: int) -> None:
        """
        Set camera movement speed.
        
        Args:
            speed: Movement speed multiplier
        """
        self.movement_speed = max(1, speed)
    
    def add_key_binding(self, key: tcod.event.KeySym, action: Callable[[], None]) -> None:
        """
        Add a custom key binding.
        
        Args:
            key: Key symbol to bind
            action: Function to call when key is pressed
        """
        self.key_bindings[key] = action
    
    def remove_key_binding(self, key: tcod.event.KeySym) -> None:
        """
        Remove a key binding.
        
        Args:
            key: Key symbol to unbind
        """
        self.key_bindings.pop(key, None)
    
    def get_help_text(self) -> Dict[str, str]:
        """
        Get help text for current key bindings.
        
        Returns:
            Dictionary mapping key descriptions to actions
        """
        help_text = {
            "1/2/3": "Switch between World/Regional/Local views",
            "WASD": "Move camera",
            "Arrow Keys": "Move camera (alternative)",
            "ESC/Q": "Quit application",
            "H/F1": "Toggle help",
            "Mouse Click": "Select location (World view)"
        }
        
        return help_text
    
    def get_current_bindings_info(self) -> str:
        """
        Get information about current key bindings.
        
        Returns:
            String describing current bindings
        """
        binding_count = len(self.key_bindings)
        pressed_count = len(self.pressed_keys)
        
        return f"Input: {binding_count} bindings, {pressed_count} keys pressed"


if __name__ == "__main__":
    # Basic testing
    print("Testing input handler...")
    
    # Create mock view manager for testing
    class MockViewManager:
        def __init__(self):
            self.current_scale = ViewScale.WORLD
            
        def switch_to_scale(self, scale):
            self.current_scale = scale
            return True
            
        def move_camera(self, dx, dy):
            return True
            
        def handle_mouse_click(self, x, y):
            return True
            
        def toggle_ui_component(self, component):
            return True
    
    # Test input handler creation
    mock_view_manager = MockViewManager()
    input_handler = InputHandler(mock_view_manager)
    print("✓ Input handler created")
    
    # Test key binding info
    help_text = input_handler.get_help_text()
    print(f"✓ Help text: {len(help_text)} entries")
    
    # Test binding info
    info = input_handler.get_current_bindings_info()
    print(f"✓ Binding info: {info}")
    
    # Test movement speed
    input_handler.set_movement_speed(2)
    print("✓ Movement speed setting works")
    
    print("Input handler ready!")
