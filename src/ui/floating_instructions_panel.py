"""
Floating instructions panel UI component for the three-tier world generation system.

This module provides a floating instructions panel that overlays on the world view,
matching the original design with rounded borders and dark background.
"""

import tcod
from typing import List

try:
    from .base import UIComponent
    from ..world_types import ViewScale, ColorRGB
except ImportError:
    from base import UIComponent
    from world_types import ViewScale, ColorRGB


class FloatingInstructionsPanel(UIComponent):
    """
    Floating instructions panel component that overlays on the world view.
    
    Shows control instructions and help information in a floating panel
    with rounded borders, matching the original design.
    
    Attributes:
        current_scale: Current viewing scale for context-sensitive help
        instructions: List of instruction strings to display
    """
    
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int = 4,
        current_scale: ViewScale = ViewScale.WORLD
    ) -> None:
        """
        Initialize the floating instructions panel.
        
        Args:
            x: X position
            y: Y position
            width: Width of the instructions panel
            height: Height of the instructions panel (default: 4)
            current_scale: Current viewing scale
        """
        super().__init__(x, y, width, height)
        self.current_scale = current_scale
        
        # Colors matching original design
        self.background_color = ColorRGB(40, 40, 40)  # Dark gray background
        self.border_color = ColorRGB(80, 80, 80)  # Lighter gray border
        self.text_color = ColorRGB(220, 220, 220)  # Light gray text
        self.key_color = ColorRGB(255, 255, 100)  # Yellow key highlights
        
        # Base instructions
        self.base_instructions = [
            "1/2/3: Switch scales  WASD: Move camera  ESC: Quit",
            "Mouse: Click to select location"
        ]
        
        # Scale-specific instructions
        self.scale_instructions = {
            ViewScale.WORLD: [
                "World View - Navigate between sectors",
                "Press 2 to zoom into regional view"
            ],
            ViewScale.REGIONAL: [
                "Regional View - Navigate within sector",
                "Press 3 to zoom into local view"
            ],
            ViewScale.LOCAL: [
                "Local View - Detailed terrain view",
                "Press 1 to return to world view"
            ]
        }
    
    def set_current_scale(self, scale: ViewScale) -> None:
        """
        Set the current viewing scale for context-sensitive help.
        
        Args:
            scale: Current viewing scale
        """
        self.current_scale = scale
    
    def get_instructions(self) -> List[str]:
        """
        Get the current instructions to display.
        
        Returns:
            List of instruction strings
        """
        instructions = []
        
        # Add base instructions
        instructions.extend(self.base_instructions)
        
        # Add scale-specific instructions if there's space
        if self.height > len(self.base_instructions) + 1:
            scale_help = self.scale_instructions.get(self.current_scale, [])
            for instruction in scale_help:
                if len(instructions) < self.height - 2:  # Leave space for borders
                    instructions.append(instruction)
        
        return instructions
    
    def draw_rounded_border(self, console: tcod.console.Console) -> None:
        """
        Draw a rounded border around the instructions panel.
        
        Args:
            console: Console to draw on
        """
        border_color = self.border_color.as_tuple()
        
        # Top and bottom horizontal lines
        for x in range(1, self.width - 1):
            console.print(self.x + x, self.y, "─", fg=border_color)
            console.print(self.x + x, self.y + self.height - 1, "─", fg=border_color)
        
        # Left and right vertical lines
        for y in range(1, self.height - 1):
            console.print(self.x, self.y + y, "│", fg=border_color)
            console.print(self.x + self.width - 1, self.y + y, "│", fg=border_color)
        
        # Rounded corners
        console.print(self.x, self.y, "╭", fg=border_color)
        console.print(self.x + self.width - 1, self.y, "╮", fg=border_color)
        console.print(self.x, self.y + self.height - 1, "╰", fg=border_color)
        console.print(self.x + self.width - 1, self.y + self.height - 1, "╯", fg=border_color)
    
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
            
            # Check for key patterns
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
        
        remaining = text[pos:]
        
        # Check for common key patterns
        if remaining[0].isdigit():
            return True
        
        if remaining.startswith('WASD'):
            return True
        
        if remaining.startswith('ESC'):
            return True
        
        if remaining.startswith('Mouse'):
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
        
        if remaining.startswith('WASD'):
            return start + 4
        elif remaining.startswith('ESC'):
            return start + 3
        elif remaining.startswith('Mouse'):
            return start + 5
        elif remaining[0].isdigit():
            # Handle patterns like "1/2/3"
            end = start + 1
            while end < len(text) and text[end] in '0123456789/':
                end += 1
            return end
        
        return start + 1
    
    def render(self, console: tcod.console.Console) -> None:
        """
        Render the floating instructions panel to the console.
        
        Args:
            console: Console to render to
        """
        if not self.visible:
            return
        
        # Fill background
        self.fill_background(console, self.background_color)
        
        # Draw rounded border
        self.draw_rounded_border(console)
        
        # Get instructions to display
        instructions = self.get_instructions()
        
        # Render instructions
        for i, instruction in enumerate(instructions):
            if i >= self.height - 2:  # Leave space for borders
                break
            
            y_pos = 1 + i
            
            # Truncate if too long
            if len(instruction) > self.width - 4:
                instruction = instruction[:self.width - 7] + "..."
            
            # Render with highlighting
            self.render_highlighted_text(console, 2, y_pos, instruction)


if __name__ == "__main__":
    # Basic testing
    print("Testing floating instructions panel...")
    
    # Test component creation
    instructions_panel = FloatingInstructionsPanel(2, 90, 100, 4)
    print(f"✓ Floating instructions panel created: {instructions_panel.width}x{instructions_panel.height}")
    
    # Test instructions generation
    instructions = instructions_panel.get_instructions()
    print(f"✓ Instructions generated: {len(instructions)} lines")
    for i, line in enumerate(instructions):
        print(f"  Line {i+1}: {line}")
    
    print("Floating instructions panel ready!")
