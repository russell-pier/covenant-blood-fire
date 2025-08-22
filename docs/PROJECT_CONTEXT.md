# Covenant: Blood & Fire

## Project Overview

A terminal-based strategy game built with Python and libtcod. The project aims to deliver an immersive real-time strategy experience in a text-based interface.

## Technical Stack

### Core Libraries

- **tcod (>=19.4.0)**: Primary graphics and input handling library
  - Console rendering and management
  - Event handling (keyboard, mouse, window events)
  - Context management for window creation
- **Python 3.13**: Modern Python with latest features
- **time**: For frame rate control and timing

### Development Tools

- **uv**: Package manager and virtual environment
- **pytest**: Testing framework
- **black**: Code formatting
- **ruff**: Linting and code quality
- **mypy**: Type checking

## Project Structure

```
covenant-blood-fire/
├── src/empires/
│   ├── __init__.py
│   └── main.py          # Main game loop and core logic
├── pyproject.toml       # Project configuration and dependencies
├── uv.lock             # Dependency lock file
└── README.md
```

## Core Architecture

### Game Class

The main `Game` class encapsulates all game state and logic:

```python
class Game:
    def __init__(self):
        # Console dimensions (80x50 terminal)
        # tcod.console.Console instance
        # Game state (running flag)
        # Player position tracking
    
    def handle_events(self) -> None:
        # Non-blocking event processing with tcod.event.get()
        # Handles QUIT and KEYDOWN events
    
    def handle_keydown(self, event: tcod.event.KeyDown) -> None:
        # Movement: Arrow keys and WASD
        # Quit: ESC or Q
    
    def render(self) -> None:
        # Console clearing and drawing
        # Border rendering
        # Terrain generation
        # Player cursor
        # UI information display
    
    def run(self) -> None:
        # Main game loop with tcod.context.new()
        # Event handling -> Rendering -> Present cycle
        # 60 FPS timing control
```

### Game Loop Architecture

1. **Initialization**: Create tcod console and context
2. **Event Processing**: Non-blocking input handling
3. **Game Logic**: Update game state (currently just player movement)
4. **Rendering**: Draw all visual elements to console
5. **Present**: Display frame to screen
6. **Timing**: Sleep for ~16ms (60 FPS)

### Input System

- **Movement**: Arrow keys or WASD for 4-directional movement
- **Quit**: ESC or Q key to exit
- **Boundary Checking**: Player movement constrained to game area
- **Event-Driven**: Uses tcod's event system for responsive input

### Rendering System

- **Console Size**: 80x50 characters
- **Coordinate System**: (0,0) at top-left
- **Layered Rendering**:
  1. Clear console
  2. Draw border
  3. Draw terrain
  4. Draw player
  5. Draw UI elements
- **Color Support**: RGB color values for foreground and background

## Current Features

### Implemented

- ✅ Complete game loop with proper event handling
- ✅ Player movement with boundary checking
- ✅ Terrain generation with varied patterns
- ✅ Border rendering with Unicode box drawing characters
- ✅ UI information display (position, controls)
- ✅ Smooth 60 FPS rendering
- ✅ Proper window management and cleanup

### Visual Elements

- **Border**: Unicode box drawing characters (╭╮╰╯─│)
- **Terrain**: Background color variations for grass/vegetation
- **Player**: Golden background color block
- **UI**: Unicode symbols for enhanced visual feedback

## Configuration

### Console Settings

- **Dimensions**: 80 columns × 50 rows
- **Title**: "Covenant: Blood & Fire"
- **VSync**: Enabled for smooth rendering
- **Context**: SDL-based rendering backend

### Performance

- **Frame Rate**: ~60 FPS (16ms sleep)
- **Event Processing**: Non-blocking for responsiveness
- **Memory**: Minimal footprint with efficient console operations

## Development Practices

### Code Organization

- **Single Responsibility**: Game class handles core logic
- **Type Hints**: Full type annotations for better IDE support
- **Modern Python**: Uses Python 3.13 features and best practices
- **Modular Design**: Separated concerns for events, rendering, and logic

### Error Handling

- **Graceful Degradation**: Handles missing font files
- **Clean Shutdown**: Proper context management
- **Input Validation**: Boundary checking for movement

## Next Development Steps

### Immediate Priorities

1. **Map System**: Replace simple terrain with proper tile-based maps
2. **Entity System**: Add units, buildings, and resources as game objects
3. **Game State Management**: Implement proper game states (menu, playing, paused)

### Future Features

1. **Unit Management**: Selection, movement, and commands
2. **Resource System**: Gathering, storage, and consumption
3. **Building System**: Construction and management
4. **Combat System**: Unit interactions and battles
5. **AI System**: Computer opponents
6. **Save/Load**: Game persistence

## Technical Notes

### tcod Integration

- Uses modern tcod API with context management
- Handles font loading gracefully with fallbacks
- Implements proper event loop patterns
- Leverages tcod's efficient console operations

### Performance Considerations

- Non-blocking event processing prevents UI freezing
- Efficient rendering with minimal console operations
- Frame rate limiting prevents excessive CPU usage
- Memory-efficient with reused console instance

### Cross-Platform Compatibility

- Pure Python implementation
- tcod handles platform-specific rendering
- Standard library dependencies only
- Modern package management with uv
