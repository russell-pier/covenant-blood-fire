"""
Command system for the Empires game.

This module provides a command palette system with hotkey support for
executing various game commands and actions.
"""

from .command_system import Command, CommandRegistry, CommandPalette
from .layer_commands import register_layer_commands

__all__ = [
    'Command',
    'CommandRegistry', 
    'CommandPalette',
    'register_layer_commands'
]
