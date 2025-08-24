"""
Bottom bar UI component for the three-tier world generation system.

This module provides the BottomBar component that displays control
instructions and help information for user interaction.
"""

import tcod
from typing import List, Dict

try:
    from .base import UIComponent
    from ..world_types import ViewScale, ColorRGB
except ImportError:
    from base import UIComponent
    from world_types import ViewScale, ColorRGB


class BottomBar(UIComponent):
    """
    Bottom bar component displaying control instructions and help.
    
    Shows:
    - Scale switching controls (1/2/3 keys)
    - Movement controls (WASD)
    - Additional context-sensitive help
    - System status information
    
    Attributes:
        current_scale: Current viewing scale for context-sensitive help
        show_help: Whether to show detailed help
    """
    
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int = 3,
        current_scale: ViewScale = ViewScale.WORLD
    ) -> None:
        """
        Initialize the bottom bar component.
        
        Args:
            x: X position
            y: Y position
            width: Width of the bottom bar
            height: Height of the bottom bar (default: 3)
            current_scale: Current viewing scale
        """
        super().__init__(x, y, width, height)
        self.current_scale = current_scale
        self.show_help = True
        
        # Colors for different elements
        self.text_color = ColorRGB(200, 200, 200)
        self.key_color = ColorRGB(255, 255, 100)
        self.separator_color = ColorRGB(100, 100, 100)
        self.border_color = ColorRGB(100, 100, 100)
        self.background_color = ColorRGB(0, 0, 50)
        
        # Control definitions
        self.base_controls = [
            ("1", "World View"),
            ("2", "Regional View"), 
            ("3", "Local View"),
            ("WASD", "Move Camera"),
            ("ESC", "Quit")
        ]
        
        self.scale_specific_help = {
            ViewScale.WORLD: [
                "Navigate between world sectors",
                "Press 2 to zoom into selected sector"
            ],
            ViewScale.REGIONAL: [
                "Navigate within sector blocks",
                "Press 3 to zoom into selected block"
            ],
            ViewScale.LOCAL: [
                "Navigate within block chunks",
                "Detailed terrain view"
            ]
        }
    
    def set_current_scale(self, scale: ViewScale) -> None:
        """
        Set the current viewing scale for context-sensitive help.
        
        Args:
            scale: Current viewing scale
        """
        self.current_scale = scale
    
    def toggle_help(self) -> None:
        """Toggle detailed help display."""
        self.show_help = not self.show_help
    
    def get_control_text(self) -> List[str]:
        """
        Get formatted control text lines.
        
        Returns:
            List of text lines for controls
        """
        lines = []
        
        # Main controls line
        control_parts = []
        for key, description in self.base_controls:
            control_parts.append(f"{key}={description}")
        
        controls_line = " | ".join(control_parts)
        
        # Truncate if too long
        if len(controls_line) > self.width - 4:
            # Try shorter descriptions
            short_controls = [
                ("1", "World"), ("2", "Regional"), ("3", "Local"),
                ("WASD", "Move"), ("ESC", "Quit")
            ]
            control_parts = [f"{key}={desc}" for key, desc in short_controls]
            controls_line = " | ".join(control_parts)
            
            # If still too long, truncate
            if len(controls_line) > self.width - 4:
                controls_line = controls_line[:self.width - 7] + "..."
        
        lines.append(controls_line)
        
        # Scale-specific help
        if self.show_help and self.current_scale in self.scale_specific_help:
            help_lines = self.scale_specific_help[self.current_scale]
            for help_line in help_lines:
                if len(help_line) <= self.width - 4:
                    lines.append(help_line)
                else:
                    # Truncate long help lines
                    lines.append(help_line[:self.width - 7] + "...")
        
        return lines
    
    def render(self, console: tcod.console.Console) -> None:
        """
        Render the bottom bar to the console.
        
        Args:
            console: Console to render to
        """
        if not self.visible:
            return
        
        # Clear the area
        self.fill_background(console, self.background_color)
        
        # Draw border
        self.draw_border(console, self.border_color)
        
        # Get control text
        control_lines = self.get_control_text()
        
        # Render control lines
        for i, line in enumerate(control_lines):
            if i >= self.height - 2:  # Leave space for borders
                break
            
            y_pos = 1 + i
            
            # Highlight key combinations
            self.render_highlighted_text(console, 2, y_pos, line)
    
    def render_highlighted_text(self, console: tcod.console.Console, x: int, y: int, text: str) -> None:
        """
        Render text with key combinations highlighted.
        
        Args:
            console: Console to render to
            x: X position
            y: Y position
            text: Text to render with highlighting
        """
        current_x = x
        i = 0
        
        while i < len(text) and current_x < self.x + self.width - 2:
            char = text[i]
            
            # Check for key patterns (single letters, WASD, ESC)
            if self.is_key_start(text, i):
                key_end = self.find_key_end(text, i)
                key_text = text[i:key_end]
                
                # Render key in highlight color
                for key_char in key_text:
                    if current_x < self.x + self.width - 2:
                        console.print(
                            self.x + current_x, 
                            self.y + y, 
                            key_char, 
                            fg=self.key_color.as_tuple()
                        )
                        current_x += 1
                
                i = key_end
            else:
                # Render normal character
                if current_x < self.x + self.width - 2:
                    console.print(
                        self.x + current_x, 
                        self.y + y, 
                        char, 
                        fg=self.text_color.as_tuple()
                    )
                    current_x += 1
                i += 1
    
    def is_key_start(self, text: str, pos: int) -> bool:
        """
        Check if position is the start of a key combination.
        
        Args:
            text: Text to check
            pos: Position to check
            
        Returns:
            True if this is the start of a key combination
        """
        if pos >= len(text):
            return False
        
        # Check for common key patterns
        remaining = text[pos:]
        
        # Single digit keys
        if remaining[0].isdigit():
            return True
        
        # WASD
        if remaining.startswith('WASD'):
            return True
        
        # ESC
        if remaining.startswith('ESC'):
            return True
        
        # Single letter keys (if followed by = or space)
        if (len(remaining) > 1 and 
            remaining[0].isalpha() and 
            remaining[1] in '= '):
            return True
        
        return False
    
    def find_key_end(self, text: str, start: int) -> int:
        """
        Find the end of a key combination starting at position.
        
        Args:
            text: Text to search
            start: Start position
            
        Returns:
            End position of key combination
        """
        remaining = text[start:]
        
        # WASD
        if remaining.startswith('WASD'):
            return start + 4
        
        # ESC
        if remaining.startswith('ESC'):
            return start + 3
        
        # Single character keys
        if len(remaining) > 0:
            return start + 1
        
        return start + 1
    
    def add_status_message(self, message: str) -> None:
        """
        Add a temporary status message (placeholder for future enhancement).
        
        Args:
            message: Status message to display
        """
        # For now, just store it - could be enhanced to show temporary messages
        self._last_status = message
    
    def get_help_for_scale(self, scale: ViewScale) -> List[str]:
        """
        Get help text for a specific scale.
        
        Args:
            scale: Scale to get help for
            
        Returns:
            List of help text lines
        """
        return self.scale_specific_help.get(scale, ["No help available"])


if __name__ == "__main__":
    # Basic testing
    print("Testing bottom bar component...")
    
    # Test component creation
    bottom_bar = BottomBar(0, 90, 128, 3)
    print(f"✓ Bottom bar created: {bottom_bar.width}x{bottom_bar.height}")
    
    # Test control text generation
    controls = bottom_bar.get_control_text()
    print(f"✓ Control text generated: {len(controls)} lines")
    for i, line in enumerate(controls):
        print(f"  Line {i+1}: {line}")
    
    # Test scale-specific help
    for scale in ViewScale:
        help_text = bottom_bar.get_help_for_scale(scale)
        print(f"✓ Help for {scale.name}: {len(help_text)} lines")
    
    print("Bottom bar component ready!")
