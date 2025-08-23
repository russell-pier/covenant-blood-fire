"""
Core command system with command palette and hotkey support.

This module provides the foundation for a command-driven interface with
a searchable command palette and direct hotkey execution.
"""

from dataclasses import dataclass
from typing import Dict, List, Callable, Optional, Any
import tcod


@dataclass
class Command:
    """Represents a single command that can be executed."""
    
    id: str
    name: str
    description: str
    hotkey: Optional[str] = None
    category: str = "General"
    action: Optional[Callable[[], Any]] = None
    enabled: bool = True


class CommandRegistry:
    """Registry for managing all available commands."""
    
    def __init__(self):
        """Initialize the command registry."""
        self._commands: Dict[str, Command] = {}
        self._hotkey_map: Dict[str, str] = {}  # hotkey -> command_id
    
    def register_command(self, command: Command) -> None:
        """
        Register a command in the registry.
        
        Args:
            command: Command to register
        """
        self._commands[command.id] = command
        
        if command.hotkey:
            self._hotkey_map[command.hotkey.lower()] = command.id
    
    def unregister_command(self, command_id: str) -> None:
        """
        Unregister a command from the registry.
        
        Args:
            command_id: ID of command to unregister
        """
        if command_id in self._commands:
            command = self._commands[command_id]
            if command.hotkey:
                self._hotkey_map.pop(command.hotkey.lower(), None)
            del self._commands[command_id]
    
    def get_command(self, command_id: str) -> Optional[Command]:
        """
        Get a command by ID.
        
        Args:
            command_id: ID of command to retrieve
            
        Returns:
            Command if found, None otherwise
        """
        return self._commands.get(command_id)
    
    def get_command_by_hotkey(self, hotkey: str) -> Optional[Command]:
        """
        Get a command by hotkey.
        
        Args:
            hotkey: Hotkey to look up
            
        Returns:
            Command if found, None otherwise
        """
        command_id = self._hotkey_map.get(hotkey.lower())
        if command_id:
            return self._commands.get(command_id)
        return None
    
    def get_all_commands(self) -> List[Command]:
        """
        Get all registered commands.
        
        Returns:
            List of all commands
        """
        return list(self._commands.values())
    
    def search_commands(self, query: str) -> List[Command]:
        """
        Search commands by name or description.
        
        Args:
            query: Search query
            
        Returns:
            List of matching commands
        """
        query = query.lower()
        results = []
        
        for command in self._commands.values():
            if not command.enabled:
                continue
                
            if (query in command.name.lower() or 
                query in command.description.lower() or
                query in command.category.lower()):
                results.append(command)
        
        return results
    
    def execute_command(self, command_id: str) -> bool:
        """
        Execute a command by ID.
        
        Args:
            command_id: ID of command to execute
            
        Returns:
            True if command was executed, False otherwise
        """
        command = self.get_command(command_id)
        if command and command.enabled and command.action:
            try:
                command.action()
                return True
            except Exception as e:
                print(f"Error executing command {command_id}: {e}")
                return False
        return False
    
    def execute_hotkey(self, hotkey: str) -> bool:
        """
        Execute a command by hotkey.
        
        Args:
            hotkey: Hotkey to execute
            
        Returns:
            True if command was executed, False otherwise
        """
        command = self.get_command_by_hotkey(hotkey)
        if command:
            return self.execute_command(command.id)
        return False


class CommandPalette:
    """Interactive command palette for searching and executing commands."""
    
    def __init__(self, command_registry: CommandRegistry):
        """
        Initialize the command palette.
        
        Args:
            command_registry: Registry of available commands
        """
        self.registry = command_registry
        self.is_open = False
        self.search_query = ""
        self.selected_index = 0
        self.filtered_commands: List[Command] = []
    
    def open(self) -> None:
        """Open the command palette."""
        self.is_open = True
        self.search_query = ""
        self.selected_index = 0
        self._update_filtered_commands()
    
    def close(self) -> None:
        """Close the command palette."""
        self.is_open = False
        self.search_query = ""
        self.selected_index = 0
        self.filtered_commands = []
    
    def handle_input(self, event: tcod.event.KeyDown) -> bool:
        """
        Handle keyboard input for the command palette.
        
        Args:
            event: Keyboard event
            
        Returns:
            True if event was handled, False otherwise
        """
        if not self.is_open:
            return False
        
        key = event.sym
        
        # Close palette
        if key == tcod.event.KeySym.ESCAPE:
            self.close()
            return True
        
        # Execute selected command
        elif key == tcod.event.KeySym.RETURN:
            if self.filtered_commands and 0 <= self.selected_index < len(self.filtered_commands):
                command = self.filtered_commands[self.selected_index]
                self.registry.execute_command(command.id)
                self.close()
            return True
        
        # Navigate commands
        elif key == tcod.event.KeySym.UP:
            if self.filtered_commands:
                self.selected_index = (self.selected_index - 1) % len(self.filtered_commands)
            return True
        
        elif key == tcod.event.KeySym.DOWN:
            if self.filtered_commands:
                self.selected_index = (self.selected_index + 1) % len(self.filtered_commands)
            return True
        
        # Handle text input for search
        elif key == tcod.event.KeySym.BACKSPACE:
            if self.search_query:
                self.search_query = self.search_query[:-1]
                self._update_filtered_commands()
            return True
        
        # Handle character input - convert key symbols to characters
        elif self._is_printable_key(key):
            char = self._key_to_char(key)
            if char:
                self.search_query += char
                self._update_filtered_commands()
            return True
        
        return False

    def _is_printable_key(self, key: tcod.event.KeySym) -> bool:
        """Check if a key represents a printable character."""
        # Handle letters
        if tcod.event.KeySym.A <= key <= tcod.event.KeySym.Z:
            return True
        # Handle numbers
        if tcod.event.KeySym.N0 <= key <= tcod.event.KeySym.N9:
            return True
        # Handle space
        if key == tcod.event.KeySym.SPACE:
            return True
        return False

    def _key_to_char(self, key: tcod.event.KeySym) -> str:
        """Convert a key symbol to its character representation."""
        # Handle letters
        if tcod.event.KeySym.A <= key <= tcod.event.KeySym.Z:
            return chr(ord('a') + (key - tcod.event.KeySym.A))
        # Handle numbers
        if tcod.event.KeySym.N0 <= key <= tcod.event.KeySym.N9:
            return chr(ord('0') + (key - tcod.event.KeySym.N0))
        # Handle space
        if key == tcod.event.KeySym.SPACE:
            return ' '
        return ''

    def _update_filtered_commands(self) -> None:
        """Update the filtered command list based on search query."""
        if self.search_query:
            self.filtered_commands = self.registry.search_commands(self.search_query)
        else:
            self.filtered_commands = [cmd for cmd in self.registry.get_all_commands() if cmd.enabled]
        
        # Reset selection if out of bounds
        if self.selected_index >= len(self.filtered_commands):
            self.selected_index = 0
    
    def render(self, console: tcod.console.Console) -> None:
        """
        Render the command palette to the console.
        
        Args:
            console: Console to render to
        """
        if not self.is_open:
            return
        
        # Calculate palette dimensions
        palette_width = min(60, console.width - 4)
        palette_height = min(20, console.height - 4)
        palette_x = (console.width - palette_width) // 2
        palette_y = (console.height - palette_height) // 2
        
        # Draw background
        for y in range(palette_y, palette_y + palette_height):
            for x in range(palette_x, palette_x + palette_width):
                console.print(x, y, " ", bg=(40, 40, 40))
        
        # Draw border
        self._draw_border(console, palette_x, palette_y, palette_width, palette_height)
        
        # Draw title
        title = "Command Palette"
        title_x = palette_x + (palette_width - len(title)) // 2
        console.print(title_x, palette_y + 1, title, fg=(255, 255, 255))
        
        # Draw search box
        search_y = palette_y + 3
        console.print(palette_x + 2, search_y, f"Search: {self.search_query}", fg=(200, 200, 200))
        
        # Draw cursor
        cursor_x = palette_x + 2 + len("Search: ") + len(self.search_query)
        console.print(cursor_x, search_y, "_", fg=(255, 255, 255))
        
        # Draw commands
        commands_start_y = palette_y + 5
        max_commands = palette_height - 7
        
        for i, command in enumerate(self.filtered_commands[:max_commands]):
            y = commands_start_y + i
            
            # Highlight selected command
            if i == self.selected_index:
                for x in range(palette_x + 1, palette_x + palette_width - 1):
                    console.print(x, y, " ", bg=(80, 80, 120))
            
            # Draw command info
            hotkey_text = f"[{command.hotkey}]" if command.hotkey else ""
            command_text = f"{hotkey_text:>6} {command.name}"
            
            console.print(palette_x + 2, y, command_text, fg=(255, 255, 255))
            
            # Draw description if there's space
            desc_x = palette_x + 2 + len(command_text) + 2
            if desc_x < palette_x + palette_width - 2:
                max_desc_len = palette_x + palette_width - 2 - desc_x
                description = command.description[:max_desc_len]
                console.print(desc_x, y, description, fg=(150, 150, 150))
    
    def _draw_border(self, console: tcod.console.Console, x: int, y: int, width: int, height: int) -> None:
        """Draw a border around the palette."""
        # Corners
        console.print(x, y, "╭", fg=(200, 200, 200))
        console.print(x + width - 1, y, "╮", fg=(200, 200, 200))
        console.print(x, y + height - 1, "╰", fg=(200, 200, 200))
        console.print(x + width - 1, y + height - 1, "╯", fg=(200, 200, 200))
        
        # Horizontal lines
        for i in range(1, width - 1):
            console.print(x + i, y, "─", fg=(200, 200, 200))
            console.print(x + i, y + height - 1, "─", fg=(200, 200, 200))
        
        # Vertical lines
        for i in range(1, height - 1):
            console.print(x, y + i, "│", fg=(200, 200, 200))
            console.print(x + width - 1, y + i, "│", fg=(200, 200, 200))


def create_default_command_system() -> tuple[CommandRegistry, CommandPalette]:
    """
    Create a default command system with registry and palette.
    
    Returns:
        Tuple of (CommandRegistry, CommandPalette)
    """
    registry = CommandRegistry()
    palette = CommandPalette(registry)
    return registry, palette
