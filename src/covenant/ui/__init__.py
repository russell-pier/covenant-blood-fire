"""
UI components for Covenant: Blood & Fire.

This module provides user interface components including panels,
status bars, and other UI elements.
"""

from .instructions_panel import InstructionsPanel, create_instructions_panel
from .status_bar import StatusBar, create_status_bar

__all__ = [
    'InstructionsPanel',
    'create_instructions_panel',
    'StatusBar',
    'create_status_bar'
]
