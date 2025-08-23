#!/usr/bin/env python3
"""
Test script to demonstrate responsive grid functionality.
This creates windows of different sizes to show how the grid expands.
"""

import time
import tcod
import tcod.event
import shutil


class ResponsiveGridDemo:
    """Demo showing responsive grid sizing."""
    
    def __init__(self, width=None, height=None):
        # Get terminal size or use provided dimensions
        if width is None or height is None:
            try:
                size = shutil.get_terminal_size()
                self.screen_width = size.columns
                self.screen_height = size.lines
            except (OSError, AttributeError):
                self.screen_width = 80
                self.screen_height = 50
        else:
            self.screen_width = width
            self.screen_height = height
        
        # Ensure minimum dimensions
        self.screen_width = max(self.screen_width, 40)
        self.screen_height = max(self.screen_height, 20)
        
        self.console = tcod.console.Console(self.screen_width, self.screen_height)
        self.running = True
        
        print(f"Created grid: {self.screen_width}x{self.screen_height} characters")
    
    def render(self):
        """Render the demo grid."""
        self.console.clear(fg=(255, 255, 255), bg=(0, 0, 0))
        
        # Draw border
        for x in range(self.screen_width):
            self.console.print(x, 0, "═", fg=(100, 100, 255))
            self.console.print(x, self.screen_height - 1, "═", fg=(100, 100, 255))
        
        for y in range(self.screen_height):
            self.console.print(0, y, "║", fg=(100, 100, 255))
            self.console.print(self.screen_width - 1, y, "║", fg=(100, 100, 255))
        
        # Draw corners
        self.console.print(0, 0, "╔", fg=(100, 100, 255))
        self.console.print(self.screen_width - 1, 0, "╗", fg=(100, 100, 255))
        self.console.print(0, self.screen_height - 1, "╚", fg=(100, 100, 255))
        self.console.print(self.screen_width - 1, self.screen_height - 1, "╝", fg=(100, 100, 255))
        
        # Show grid dimensions
        info_text = f"Grid Size: {self.screen_width} x {self.screen_height}"
        info_x = (self.screen_width - len(info_text)) // 2
        info_y = 2
        self.console.print(info_x, info_y, info_text, fg=(255, 255, 0))
        
        # Show instructions
        instructions = [
            "This demonstrates responsive grid sizing",
            "Grid expands to fill available terminal space",
            "Press Q to quit, R to show different sizes"
        ]
        
        start_y = self.screen_height // 2 - len(instructions) // 2
        for i, instruction in enumerate(instructions):
            x = (self.screen_width - len(instruction)) // 2
            y = start_y + i
            if 0 <= x < self.screen_width and 0 <= y < self.screen_height:
                self.console.print(x, y, instruction, fg=(200, 200, 200))
        
        # Fill some grid with pattern to show the expanded area
        for y in range(4, self.screen_height - 4, 2):
            for x in range(4, self.screen_width - 4, 3):
                if x < self.screen_width - 1 and y < self.screen_height - 1:
                    self.console.print(x, y, "·", fg=(80, 80, 80))
    
    def handle_events(self):
        """Handle input events."""
        for event in tcod.event.get():
            if event.type == "QUIT":
                self.running = False
            elif event.type == "KEYDOWN":
                if event.sym == tcod.event.KeySym.Q:
                    self.running = False
                elif event.sym == tcod.event.KeySym.R:
                    # Demonstrate different sizes
                    self.demo_different_sizes()
    
    def demo_different_sizes(self):
        """Show different grid sizes in sequence."""
        sizes = [(60, 30), (100, 40), (120, 50), (80, 25)]
        
        for width, height in sizes:
            print(f"Switching to {width}x{height}")
            demo = ResponsiveGridDemo(width, height)
            demo.run_briefly()
    
    def run_briefly(self):
        """Run for a short time to demonstrate size."""
        with tcod.context.new(
            columns=self.screen_width,
            rows=self.screen_height,
            title=f"Responsive Grid Demo - {self.screen_width}x{self.screen_height}",
            vsync=True,
        ) as context:
            
            start_time = time.time()
            while time.time() - start_time < 2.0:  # Show for 2 seconds
                for event in tcod.event.get():
                    if event.type == "QUIT":
                        return
                
                self.render()
                context.present(self.console)
                time.sleep(0.016)
    
    def run(self):
        """Main demo loop."""
        with tcod.context.new(
            columns=self.screen_width,
            rows=self.screen_height,
            title=f"Responsive Grid Demo - {self.screen_width}x{self.screen_height}",
            vsync=True,
        ) as context:
            
            while self.running:
                self.handle_events()
                self.render()
                context.present(self.console)
                time.sleep(0.016)


def main():
    """Run the responsive grid demo."""
    print("Starting Responsive Grid Demo...")
    print("The grid will automatically size to your terminal.")
    print("Try resizing your terminal before running to see different sizes!")
    
    demo = ResponsiveGridDemo()
    demo.run()


if __name__ == "__main__":
    main()
