"""
Map commands for the world map system.

This module provides commands for toggling and controlling the world map display.
"""

from .command_system import Command, CommandRegistry


class MapCommands:
    """Commands for map functionality."""
    
    def __init__(self, map_system):
        """
        Initialize map commands.
        
        Args:
            map_system: MapSystem instance
        """
        self.map_system = map_system
    
    def toggle_map(self) -> None:
        """Toggle the world map display."""
        self.map_system.toggle()
        if self.map_system.is_open:
            print("World map opened (M to close)")
        else:
            print("World map closed")
    
    def open_map(self) -> None:
        """Open the world map display."""
        self.map_system.open()
        print("World map opened (M to close)")
    
    def close_map(self) -> None:
        """Close the world map display."""
        self.map_system.close()
        print("World map closed")


def register_map_commands(registry: CommandRegistry, map_system) -> MapCommands:
    """
    Register all map commands with the command registry.

    Args:
        registry: CommandRegistry to register commands with
        map_system: MapSystem instance

    Returns:
        MapCommands instance for direct access
    """
    map_commands = MapCommands(map_system)
    
    # Register map toggle command
    map_command = Command(
        id="map.toggle",
        name="Toggle World Map",
        description="Show/hide the world map overview",
        hotkey="m",
        category="Map",
        action=map_commands.toggle_map
    )
    registry.register_command(map_command)
    
    # Register map open command (for command palette)
    open_command = Command(
        id="map.open",
        name="Open World Map",
        description="Open the world map overview",
        category="Map",
        action=map_commands.open_map
    )
    registry.register_command(open_command)
    
    # Register map close command (for command palette)
    close_command = Command(
        id="map.close",
        name="Close World Map",
        description="Close the world map overview",
        category="Map",
        action=map_commands.close_map
    )
    registry.register_command(close_command)
    
    return map_commands
