#!/usr/bin/env python3
"""
Simple test to verify window resizing increases character grid size.
"""

import tcod
import tcod.event
import time


def main():
    # Start with a small console
    console = tcod.console.Console(40, 20)
    last_resize_time = 0
    stable_size = (40, 20)

    with tcod.context.new(
        columns=40,
        rows=20,
        title="Resize Test - Watch the character count increase!",
        vsync=True,
    ) as context:

        running = True
        while running:
            # Check for resize with debouncing
            current_time = time.time()
            recommended = context.recommended_console_size()

            if (recommended != stable_size and
                current_time - last_resize_time > 0.1):  # 100ms debounce

                new_width, new_height = recommended
                if new_width > 0 and new_height > 0:
                    # Only resize if significantly different
                    if (abs(new_width - console.width) > 1 or
                        abs(new_height - console.height) > 1):

                        print(f"Resizing console: {console.width}x{console.height} -> {new_width}x{new_height}")
                        console = tcod.console.Console(new_width, new_height)
                        stable_size = (new_width, new_height)
                        last_resize_time = current_time
            
            # Handle events
            for event in tcod.event.get():
                if event.type == "QUIT":
                    running = False
                elif event.type == "KEYDOWN" and event.sym == tcod.event.KeySym.Q:
                    running = False
            
            # Clear and draw
            console.clear()
            
            # Draw border
            for x in range(console.width):
                console.print(x, 0, "═", fg=(100, 100, 255))
                if console.height > 1:
                    console.print(x, console.height - 1, "═", fg=(100, 100, 255))
            
            for y in range(console.height):
                console.print(0, y, "║", fg=(100, 100, 255))
                if console.width > 1:
                    console.print(console.width - 1, y, "║", fg=(100, 100, 255))
            
            # Show dimensions
            info = f"Size: {console.width}x{console.height}"
            if len(info) < console.width and console.height > 2:
                console.print(2, 2, info, fg=(255, 255, 0))
            
            # Fill with dots to show the grid
            for y in range(2, console.height - 2, 2):
                for x in range(2, console.width - 2, 3):
                    console.print(x, y, "·", fg=(80, 80, 80))
            
            # Instructions
            if console.width > 30 and console.height > 10:
                console.print(2, console.height // 2, "Resize the window to see more characters!", fg=(200, 200, 200))
                console.print(2, console.height // 2 + 1, "Press Q to quit", fg=(200, 200, 200))
            
            context.present(console)
            time.sleep(0.016)


if __name__ == "__main__":
    main()
