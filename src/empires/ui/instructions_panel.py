"""
Instructions panel for displaying current game instructions and hotkeys.

This module provides a clean 3-line panel at the bottom of the screen
showing essential commands and instructions.
"""

import tcod


class InstructionsPanel:
    """A 3-line panel at the bottom showing current instructions."""
    
    def __init__(self):
        """Initialize the instructions panel."""
        self.is_visible = True
        self.content_height = 3  # 3 lines of content
        self.height = 5  # 3 content + 2 border = 5 total
    
    def toggle_visibility(self) -> None:
        """Toggle the visibility of the instructions panel."""
        self.is_visible = not self.is_visible
    
    def render(self, console: tcod.console.Console) -> None:
        """
        Render the instructions panel at the bottom of the console.
        
        Args:
            console: Console to render to
        """
        if not self.is_visible:
            return
        
        # Calculate floating panel position (1 line margin from bottom)
        panel_y = console.height - self.height - 1  # -1 for bottom margin
        panel_width = console.width - 4  # 2 chars margin on each side
        panel_x = 2  # Left margin

        # Background color for the floating panel
        panel_bg = (60, 60, 60)  # Dark gray
        border_fg = (120, 120, 120)  # Light gray for border
        text_fg = (255, 255, 255)  # White text on dark background

        # No need to clear margins - the world renders behind and panels render on top

        # Draw panel background (only the panel area)
        for y in range(panel_y, panel_y + self.height):
            for x in range(panel_x, panel_x + panel_width):
                console.print(x, y, " ", bg=panel_bg)

        # Draw rounded border
        # Top border
        console.print(panel_x, panel_y, "╭", fg=border_fg, bg=panel_bg)  # Top-left corner
        for x in range(panel_x + 1, panel_x + panel_width - 1):
            console.print(x, panel_y, "─", fg=border_fg, bg=panel_bg)  # Top line
        console.print(panel_x + panel_width - 1, panel_y, "╮", fg=border_fg, bg=panel_bg)  # Top-right corner

        # Side borders
        for y in range(panel_y + 1, panel_y + self.height - 1):
            console.print(panel_x, y, "│", fg=border_fg, bg=panel_bg)  # Left side
            console.print(panel_x + panel_width - 1, y, "│", fg=border_fg, bg=panel_bg)  # Right side

        # Bottom border
        console.print(panel_x, panel_y + self.height - 1, "╰", fg=border_fg, bg=panel_bg)  # Bottom-left corner
        for x in range(panel_x + 1, panel_x + panel_width - 1):
            console.print(x, panel_y + self.height - 1, "─", fg=border_fg, bg=panel_bg)  # Bottom line
        console.print(panel_x + panel_width - 1, panel_y + self.height - 1, "╯", fg=border_fg, bg=panel_bg)  # Bottom-right corner

        # Content area starts at panel_y + 1 (inside the border)
        content_y = panel_y + 1
        content_x = panel_x + 2  # 2 chars inside the border for padding

        # Line 1: Command palette instruction
        console.print(
            content_x, content_y,
            "⌘ CMD+K or CTRL+K to open command palette",
            fg=text_fg, bg=panel_bg
        )

        # Line 2: Layer switching instructions
        console.print(
            content_x, content_y + 1,
            "🔄 Layers: [Z] Surface | [X] Underground | [C] Mountains",
            fg=(150, 200, 255), bg=panel_bg  # Light blue text for variety
        )

        # Line 3: Help instruction
        console.print(
            content_x, content_y + 2,
            "📖 Press [H] to toggle this help panel",
            fg=(180, 180, 180), bg=panel_bg  # Light gray text
        )
    
    def get_height(self) -> int:
        """
        Get the total height including margin when visible.

        Returns:
            Height in lines including 1 line margin, or 0 if not visible
        """
        return (self.height + 1) if self.is_visible else 0  # +1 for bottom margin


def create_instructions_panel() -> InstructionsPanel:
    """
    Create a default instructions panel.
    
    Returns:
        InstructionsPanel instance
    """
    return InstructionsPanel()
