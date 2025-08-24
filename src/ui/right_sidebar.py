"""
Right sidebar UI component for the three-tier world generation system.

This module provides the RightSidebar component as a placeholder for
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


class RightSidebar(UIComponent):
    """
    Right sidebar component - placeholder for future functionality.
    
    This component is currently blank but provides the proper layout
    structure for future features such as:
    - Detailed information panels
    - Property inspectors
    - Action menus
    - Status displays
    
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
        title: str = "Info"
    ) -> None:
        """
        Initialize the right sidebar component.
        
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
        self.background_color = ColorRGB(40, 20, 20)
        self.border_color = ColorRGB(120, 80, 80)
        self.title_color = ColorRGB(255, 200, 200)
        self.text_color = ColorRGB(180, 150, 150)
    
    def render(self, console: tcod.console.Console) -> None:
        """
        Render the right sidebar to the console.
        
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
                "• Details",
                "• Properties", 
                "• Actions",
                "• Inspector"
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
    print("Testing right sidebar component...")
    
    # Test component creation
    sidebar = RightSidebar(100, 0, 20, 50)
    print(f"✓ Right sidebar created: {sidebar.width}x{sidebar.height}")
    print(f"✓ Title: {sidebar.title}")
    print(f"✓ Placeholder: {sidebar.placeholder_text}")
    
    print("Right sidebar component ready!")
