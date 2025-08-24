"""
Left sidebar UI component for the three-tier world generation system.

This module provides the LeftSidebar component as a placeholder for
future functionality. Currently displays a blank panel with proper
spacing and borders.
"""

import tcod

try:
    from .base import UIComponent
    from ..world_types import ColorRGB
except ImportError:
    from base import UIComponent
    from world_types import ColorRGB


class LeftSidebar(UIComponent):
    """
    Left sidebar component - placeholder for future functionality.
    
    This component is currently blank but provides the proper layout
    structure for future features such as:
    - Minimap display
    - Resource information
    - Unit/building lists
    - Tool palette
    
    Attributes:
        title: Title text for the sidebar
        placeholder_text: Text to display in the placeholder
    """
    
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        title: str = "Tools"
    ) -> None:
        """
        Initialize the left sidebar component.
        
        Args:
            x: X position
            y: Y position
            width: Width of the sidebar
            height: Height of the sidebar
            title: Title for the sidebar
        """
        super().__init__(x, y, width, height)
        self.title = title
        self.placeholder_text = "Future functionality"
        
        # Colors
        self.background_color = ColorRGB(20, 20, 40)
        self.border_color = ColorRGB(80, 80, 120)
        self.title_color = ColorRGB(200, 200, 255)
        self.text_color = ColorRGB(150, 150, 180)
    
    def render(self, console: tcod.console.Console) -> None:
        """
        Render the left sidebar to the console.
        
        Args:
            console: Console to render to
        """
        if not self.visible:
            return
        
        # Fill background
        self.fill_background(console, self.background_color)
        
        # Draw border
        self.draw_border(console, self.border_color)
        
        # Draw title if there's space
        if self.height > 2:
            title_x, title_y = self.center_text(self.title, -(self.height // 2) + 2)
            self.print_text(
                console, 
                title_x - self.x, 
                title_y - self.y, 
                self.title,
                fg=self.title_color.as_tuple()
            )
        
        # Draw placeholder text
        if self.height > 4:
            placeholder_lines = [
                "[ BLANK ]",
                "",
                "Reserved for",
                "future features:",
                "",
                "• Minimap",
                "• Resources", 
                "• Tools",
                "• Statistics"
            ]
            
            start_y = 3
            for i, line in enumerate(placeholder_lines):
                if start_y + i >= self.height - 1:
                    break
                
                if line:  # Skip empty lines for centering
                    line_x = 2 if line.startswith("•") else (self.width - len(line)) // 2
                    self.print_text(
                        console,
                        line_x,
                        start_y + i,
                        line,
                        fg=self.text_color.as_tuple()
                    )
    
    def set_title(self, title: str) -> None:
        """
        Set the sidebar title.
        
        Args:
            title: New title text
        """
        self.title = title
    
    def set_placeholder_text(self, text: str) -> None:
        """
        Set the placeholder text.
        
        Args:
            text: New placeholder text
        """
        self.placeholder_text = text


if __name__ == "__main__":
    # Basic testing
    print("Testing left sidebar component...")
    
    # Test component creation
    sidebar = LeftSidebar(0, 0, 20, 50)
    print(f"✓ Left sidebar created: {sidebar.width}x{sidebar.height}")
    print(f"✓ Title: {sidebar.title}")
    print(f"✓ Placeholder: {sidebar.placeholder_text}")
    
    print("Left sidebar component ready!")
