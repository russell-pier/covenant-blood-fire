"""
Base UI component for the three-tier world generation system.

This module provides the base UIComponent class that all UI elements
inherit from, providing common functionality for rendering and layout.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional
import tcod

try:
    from ..world_types import ColorRGB, Coordinate
except ImportError:
    from world_types import ColorRGB, Coordinate


class UIComponent(ABC):
    """
    Abstract base class for all UI components.
    
    Provides common functionality for UI elements including
    position management, rendering area calculation, and
    text utilities.
    
    Attributes:
        x: X position of the component
        y: Y position of the component  
        width: Width of the component
        height: Height of the component
        visible: Whether the component should be rendered
    """
    
    def __init__(
        self, 
        x: int, 
        y: int, 
        width: int, 
        height: int,
        visible: bool = True
    ) -> None:
        """
        Initialize the UI component.
        
        Args:
            x: X position of the component
            y: Y position of the component
            width: Width of the component
            height: Height of the component
            visible: Whether the component is visible
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.visible = visible
    
    @abstractmethod
    def render(self, console: tcod.console.Console) -> None:
        """
        Render the component to the console.
        
        Args:
            console: Console to render to
        """
        pass
    
    def get_bounds(self) -> Tuple[int, int, int, int]:
        """
        Get the bounding rectangle of the component.
        
        Returns:
            Tuple of (x, y, width, height)
        """
        return self.x, self.y, self.width, self.height
    
    def contains_point(self, x: int, y: int) -> bool:
        """
        Check if a point is within the component bounds.
        
        Args:
            x: X coordinate to check
            y: Y coordinate to check
            
        Returns:
            True if point is within bounds
        """
        return (self.x <= x < self.x + self.width and 
                self.y <= y < self.y + self.height)
    
    def set_position(self, x: int, y: int) -> None:
        """
        Set the position of the component.
        
        Args:
            x: New X position
            y: New Y position
        """
        self.x = x
        self.y = y
    
    def set_size(self, width: int, height: int) -> None:
        """
        Set the size of the component.
        
        Args:
            width: New width
            height: New height
        """
        self.width = width
        self.height = height
    
    def show(self) -> None:
        """Make the component visible."""
        self.visible = True
    
    def hide(self) -> None:
        """Hide the component."""
        self.visible = False
    
    def clear_area(self, console: tcod.console.Console) -> None:
        """
        Clear the component's area on the console.
        
        Args:
            console: Console to clear
        """
        for y in range(self.height):
            for x in range(self.width):
                console_x = self.x + x
                console_y = self.y + y
                if (0 <= console_x < console.width and 
                    0 <= console_y < console.height):
                    console.print(console_x, console_y, " ", fg=(255, 255, 255), bg=(0, 0, 0))
    
    def draw_border(
        self, 
        console: tcod.console.Console,
        color: Optional[ColorRGB] = None,
        double_line: bool = False
    ) -> None:
        """
        Draw a border around the component.
        
        Args:
            console: Console to draw on
            color: Border color (default: white)
            double_line: Use double-line border characters
        """
        if color is None:
            color = ColorRGB(255, 255, 255)
        
        color_tuple = color.as_tuple()
        
        # Choose border characters
        if double_line:
            h_line, v_line = "═", "║"
            top_left, top_right = "╔", "╗"
            bottom_left, bottom_right = "╚", "╝"
        else:
            h_line, v_line = "─", "│"
            top_left, top_right = "┌", "┐"
            bottom_left, bottom_right = "└", "┘"
        
        # Draw horizontal lines
        for x in range(1, self.width - 1):
            console.print(self.x + x, self.y, h_line, fg=color_tuple)
            console.print(self.x + x, self.y + self.height - 1, h_line, fg=color_tuple)
        
        # Draw vertical lines
        for y in range(1, self.height - 1):
            console.print(self.x, self.y + y, v_line, fg=color_tuple)
            console.print(self.x + self.width - 1, self.y + y, v_line, fg=color_tuple)
        
        # Draw corners
        console.print(self.x, self.y, top_left, fg=color_tuple)
        console.print(self.x + self.width - 1, self.y, top_right, fg=color_tuple)
        console.print(self.x, self.y + self.height - 1, bottom_left, fg=color_tuple)
        console.print(self.x + self.width - 1, self.y + self.height - 1, bottom_right, fg=color_tuple)
    
    def center_text(self, text: str, y_offset: int = 0) -> Tuple[int, int]:
        """
        Calculate position to center text within the component.
        
        Args:
            text: Text to center
            y_offset: Vertical offset from center
            
        Returns:
            Tuple of (x, y) position for centered text
        """
        text_x = self.x + (self.width - len(text)) // 2
        text_y = self.y + self.height // 2 + y_offset
        return text_x, text_y
    
    def print_centered(
        self, 
        console: tcod.console.Console,
        text: str,
        y_offset: int = 0,
        fg: Optional[Tuple[int, int, int]] = None,
        bg: Optional[Tuple[int, int, int]] = None
    ) -> None:
        """
        Print text centered within the component.
        
        Args:
            console: Console to print to
            text: Text to print
            y_offset: Vertical offset from center
            fg: Foreground color
            bg: Background color
        """
        if fg is None:
            fg = (255, 255, 255)
        if bg is None:
            bg = (0, 0, 0)
        
        text_x, text_y = self.center_text(text, y_offset)
        
        # Ensure position is within console bounds
        if (0 <= text_x < console.width and 
            0 <= text_y < console.height):
            console.print(text_x, text_y, text, fg=fg, bg=bg)
    
    def print_text(
        self,
        console: tcod.console.Console,
        x: int,
        y: int,
        text: str,
        fg: Optional[Tuple[int, int, int]] = None,
        bg: Optional[Tuple[int, int, int]] = None,
        clip: bool = True
    ) -> None:
        """
        Print text at relative position within the component.
        
        Args:
            console: Console to print to
            x: X position relative to component
            y: Y position relative to component
            text: Text to print
            fg: Foreground color
            bg: Background color
            clip: Whether to clip text to component bounds
        """
        if fg is None:
            fg = (255, 255, 255)
        if bg is None:
            bg = (0, 0, 0)
        
        abs_x = self.x + x
        abs_y = self.y + y
        
        # Check bounds
        if clip and not self.contains_point(abs_x, abs_y):
            return
        
        # Clip text if it extends beyond component
        if clip and abs_x + len(text) > self.x + self.width:
            max_length = self.x + self.width - abs_x
            text = text[:max_length]
        
        # Ensure position is within console bounds
        if (0 <= abs_x < console.width and 
            0 <= abs_y < console.height):
            console.print(abs_x, abs_y, text, fg=fg, bg=bg)
    
    def fill_background(
        self,
        console: tcod.console.Console,
        bg_color: Optional[ColorRGB] = None,
        char: str = " "
    ) -> None:
        """
        Fill the component background with a color.
        
        Args:
            console: Console to fill
            bg_color: Background color (default: black)
            char: Character to fill with
        """
        if bg_color is None:
            bg_color = ColorRGB(0, 0, 0)
        
        bg_tuple = bg_color.as_tuple()
        
        for y in range(self.height):
            for x in range(self.width):
                console_x = self.x + x
                console_y = self.y + y
                if (0 <= console_x < console.width and 
                    0 <= console_y < console.height):
                    console.print(console_x, console_y, char, fg=(255, 255, 255), bg=bg_tuple)


def calculate_layout_areas(
    console_width: int,
    console_height: int,
    top_bar_height: int = 3,
    bottom_bar_height: int = 3,
    sidebar_width: int = 20
) -> dict:
    """
    Calculate layout areas for UI components.
    
    Args:
        console_width: Total console width
        console_height: Total console height
        top_bar_height: Height of top bar
        bottom_bar_height: Height of bottom bar
        sidebar_width: Width of sidebars
        
    Returns:
        Dictionary with area definitions for each component
    """
    # Calculate main content area
    content_y = top_bar_height
    content_height = console_height - top_bar_height - bottom_bar_height
    content_x = sidebar_width
    content_width = console_width - 2 * sidebar_width
    
    return {
        'top_bar': {
            'x': 0, 'y': 0,
            'width': console_width, 'height': top_bar_height
        },
        'bottom_bar': {
            'x': 0, 'y': console_height - bottom_bar_height,
            'width': console_width, 'height': bottom_bar_height
        },
        'left_sidebar': {
            'x': 0, 'y': content_y,
            'width': sidebar_width, 'height': content_height
        },
        'right_sidebar': {
            'x': console_width - sidebar_width, 'y': content_y,
            'width': sidebar_width, 'height': content_height
        },
        'main_content': {
            'x': content_x, 'y': content_y,
            'width': content_width, 'height': content_height
        }
    }


if __name__ == "__main__":
    # Basic testing
    print("Testing UI base components...")
    
    # Test layout calculation
    layout = calculate_layout_areas(128, 96)
    print(f"✓ Layout calculated: main content area {layout['main_content']['width']}x{layout['main_content']['height']}")
    
    # Test color creation
    color = ColorRGB(100, 150, 200)
    print(f"✓ Color created: {color.as_tuple()}")
    
    print("UI base components ready!")
