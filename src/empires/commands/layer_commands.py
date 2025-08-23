"""
Layer switching commands for the 3D layered world system.

This module provides commands for switching between underground, surface,
and mountain layers with hotkey support.
"""

from typing import Optional

from .command_system import Command, CommandRegistry
from ..world.layered import WorldLayer


class LayerCommands:
    """Commands for layer switching functionality."""
    
    def __init__(self, world_generator):
        """
        Initialize layer commands.
        
        Args:
            world_generator: WorldGenerator instance with layered system
        """
        self.world_generator = world_generator
    
    def go_to_surface(self) -> None:
        """Switch to the surface layer."""
        if (hasattr(self.world_generator, 'use_layered_system') and 
            self.world_generator.use_layered_system and 
            self.world_generator.camera_3d):
            
            success = self.world_generator.camera_3d.change_layer(WorldLayer.SURFACE)
            if success:
                print("Switched to Surface layer")
            else:
                print("Already on Surface layer")
        else:
            print("Layered system not available")
    
    def go_underground(self) -> None:
        """Switch to the underground layer."""
        if (hasattr(self.world_generator, 'use_layered_system') and 
            self.world_generator.use_layered_system and 
            self.world_generator.camera_3d):
            
            success = self.world_generator.camera_3d.change_layer(WorldLayer.UNDERGROUND)
            if success:
                print("Switched to Underground layer")
            else:
                print("Already on Underground layer")
        else:
            print("Layered system not available")
    
    def go_to_mountains(self) -> None:
        """Switch to the mountain layer."""
        if (hasattr(self.world_generator, 'use_layered_system') and 
            self.world_generator.use_layered_system and 
            self.world_generator.camera_3d):
            
            success = self.world_generator.camera_3d.change_layer(WorldLayer.MOUNTAINS)
            if success:
                print("Switched to Mountain layer")
            else:
                print("Already on Mountain layer")
        else:
            print("Layered system not available")
    
    def get_current_layer_info(self) -> str:
        """
        Get information about the current layer.
        
        Returns:
            String describing current layer
        """
        if (hasattr(self.world_generator, 'use_layered_system') and 
            self.world_generator.use_layered_system and 
            self.world_generator.camera_3d):
            
            current_layer = self.world_generator.camera_3d.get_current_layer()
            if current_layer:
                return f"Current layer: {current_layer.name.title()}"
        
        return "Layered system not available"


def register_layer_commands(registry: CommandRegistry, world_generator, instructions_panel=None, status_bar=None) -> LayerCommands:
    """
    Register all layer switching commands with the command registry.

    Args:
        registry: CommandRegistry to register commands with
        world_generator: WorldGenerator instance with layered system
        instructions_panel: Optional instructions panel for toggle command
        status_bar: Optional status bar for toggle command

    Returns:
        LayerCommands instance for direct access
    """
    layer_commands = LayerCommands(world_generator)
    
    # Register surface command
    surface_command = Command(
        id="layer.surface",
        name="Go to Surface",
        description="Switch to the surface layer",
        hotkey="z",
        category="Layers",
        action=layer_commands.go_to_surface
    )
    registry.register_command(surface_command)
    
    # Register underground command
    underground_command = Command(
        id="layer.underground", 
        name="Go Underground",
        description="Switch to the underground cave layer",
        hotkey="x",
        category="Layers",
        action=layer_commands.go_underground
    )
    registry.register_command(underground_command)
    
    # Register mountain command
    mountain_command = Command(
        id="layer.mountains",
        name="Go to Elevation", 
        description="Switch to the mountain/elevation layer",
        hotkey="c",
        category="Layers",
        action=layer_commands.go_to_mountains
    )
    registry.register_command(mountain_command)
    
    # Register layer info command
    info_command = Command(
        id="layer.info",
        name="Current Layer Info",
        description="Show information about the current layer",
        hotkey="i",
        category="Layers",
        action=lambda: print(layer_commands.get_current_layer_info())
    )
    registry.register_command(info_command)

    # Register UI panel toggle commands if panels are provided
    if instructions_panel:
        panel_command = Command(
            id="ui.toggle_instructions",
            name="Toggle Instructions Panel",
            description="Show/hide the instructions panel",
            hotkey="h",
            category="UI",
            action=instructions_panel.toggle_visibility
        )
        registry.register_command(panel_command)

    if status_bar:
        status_command = Command(
            id="ui.toggle_status",
            name="Toggle Status Bar",
            description="Show/hide the status bar",
            hotkey="t",
            category="UI",
            action=status_bar.toggle_visibility
        )
        registry.register_command(status_command)



    return layer_commands


def create_layer_command_system(world_generator) -> tuple[CommandRegistry, LayerCommands]:
    """
    Create a command system with layer commands registered.
    
    Args:
        world_generator: WorldGenerator instance with layered system
        
    Returns:
        Tuple of (CommandRegistry, LayerCommands)
    """
    from .command_system import CommandRegistry
    
    registry = CommandRegistry()
    layer_commands = register_layer_commands(registry, world_generator)
    
    return registry, layer_commands
