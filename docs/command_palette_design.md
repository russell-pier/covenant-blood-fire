# Command Palette and Hotkey System Design

## Overview

The Command Palette system provides a modern, extensible interface for executing game commands through both a searchable command palette (CMD+K) and direct hotkeys. This system replaces terrain-based layer transitions with a more intuitive hotkey-driven approach suitable for a camera/viewport-based game.

## Core Architecture

### Command System Components

1. **Command**: Individual executable actions with metadata
2. **CommandRegistry**: Central registry for command management
3. **CommandPalette**: Interactive search and execution interface
4. **LayerCommands**: Specific commands for 3D layer switching

### Design Philosophy

- **Player as Camera**: The player controls the camera/viewport, not a character
- **Direct Access**: Hotkeys provide immediate access to common actions
- **Discoverability**: Command palette allows exploration of available commands
- **Extensibility**: Easy to add new commands and categories

## Command Structure

### Command Definition
```python
@dataclass
class Command:
    id: str                    # Unique identifier
    name: str                  # Display name
    description: str           # Help text
    hotkey: Optional[str]      # Direct hotkey (optional)
    category: str              # Grouping category
    action: Callable           # Function to execute
    enabled: bool              # Whether command is available
```

### Command Categories
- **Layers**: 3D layer switching commands
- **Navigation**: Camera movement and positioning
- **View**: Display and rendering options
- **System**: Game system controls

## Layer Switching Commands

### Core Layer Commands

| Command | Hotkey | Description |
|---------|--------|-------------|
| Go to Surface | Z | Switch to surface layer |
| Go Underground | X | Switch to underground cave layer |
| Go to Elevation | C | Switch to mountain/elevation layer |
| Current Layer Info | I | Display current layer information |

### Command Implementation
```python
class LayerCommands:
    def go_to_surface(self) -> None
    def go_underground(self) -> None  
    def go_to_mountains(self) -> None
    def get_current_layer_info(self) -> str
```

## Command Palette Interface

### Activation
- **Primary**: CMD+K (macOS) or CTRL+K (Windows/Linux)
- **Alternative**: Through menu system (future enhancement)

### Features
- **Real-time Search**: Filter commands by name, description, or category
- **Keyboard Navigation**: Arrow keys to navigate, Enter to execute
- **Visual Feedback**: Highlighted selection and command information
- **Hotkey Display**: Shows associated hotkeys for quick reference

### UI Layout
```
╭─────────────────────────────────────────────────────────╮
│                    Command Palette                      │
├─────────────────────────────────────────────────────────┤
│ Search: layer                                          _│
├─────────────────────────────────────────────────────────┤
│    [Z] Go to Surface        Switch to surface layer     │
│ >  [X] Go Underground       Switch to underground layer │
│    [C] Go to Elevation      Switch to mountain layer    │
│    [I] Current Layer Info   Show current layer info     │
╰─────────────────────────────────────────────────────────╯
```

## Hotkey System

### Direct Hotkeys
- **Z**: Go to Surface layer
- **X**: Go Underground layer  
- **C**: Go to Mountains layer
- **I**: Current Layer Info

### Hotkey Processing
1. Check if command palette is open (takes priority)
2. Process direct hotkeys through CommandRegistry
3. Fall back to standard game controls (movement, etc.)

### Case Insensitive
All hotkeys are processed case-insensitively for better usability.

## Integration with 3D Layered World

### Free Layer Switching
- **No Terrain Restrictions**: Players can switch layers anywhere
- **Camera-Based**: Layer switching affects the camera view, not player position
- **Instant Transitions**: Immediate layer changes without animation delays

### Visual Feedback
- **Current Layer Display**: UI shows active layer prominently
- **Layer Hints**: Subtle visual cues about terrain in other layers
- **Hotkey Reminders**: UI displays available layer switching hotkeys

## Technical Implementation

### File Structure
```
src/empires/commands/
├── __init__.py              # Package exports
├── command_system.py        # Core command system
└── layer_commands.py        # Layer-specific commands
```

### Key Classes

#### CommandRegistry
- **Purpose**: Central command management
- **Features**: Registration, search, execution, hotkey mapping
- **Thread Safety**: Designed for single-threaded game loop

#### CommandPalette  
- **Purpose**: Interactive command interface
- **Features**: Search, navigation, rendering, input handling
- **Integration**: Renders over game view when active

#### LayerCommands
- **Purpose**: 3D layer switching functionality
- **Features**: Layer validation, transition execution, status reporting
- **Integration**: Works with WorldGenerator and CameraSystem

## User Experience

### For Players
1. **Quick Access**: Press Z/X/C for instant layer switching
2. **Discovery**: CMD+K opens command palette for exploration
3. **Visual Guidance**: UI shows current layer and available commands
4. **Consistent**: Same commands work in palette and as hotkeys

### For Developers
1. **Easy Extension**: Simple command registration process
2. **Flexible Actions**: Commands can execute any function
3. **Categorization**: Logical grouping for organization
4. **Testing**: Comprehensive test coverage for reliability

## Performance Considerations

### Efficient Design
- **Lazy Evaluation**: Commands only execute when triggered
- **Fast Search**: O(n) search through command list
- **Minimal Overhead**: Hotkey processing adds negligible latency
- **Memory Efficient**: Commands stored as lightweight objects

### Rendering Optimization
- **Conditional Rendering**: Palette only renders when open
- **Cached Layout**: Pre-calculated positioning and sizing
- **Minimal Redraws**: Only update changed elements

## Future Enhancements

### Planned Features
- **Command History**: Recently used commands
- **Custom Hotkeys**: User-configurable key bindings
- **Command Aliases**: Multiple names for same command
- **Macro Support**: Sequence multiple commands

### Potential Categories
- **Building**: Construction and placement commands
- **Units**: Entity management and control
- **Resources**: Resource management and trading
- **Diplomacy**: Interaction with other players/AI

## Testing Strategy

### Test Coverage
- **Unit Tests**: Individual component functionality
- **Integration Tests**: Command system interaction
- **UI Tests**: Command palette behavior
- **Performance Tests**: Hotkey response time

### Test Files
- `tests/commands/test_command_system.py`: Core system tests
- `tests/commands/test_layer_commands.py`: Layer command tests

## Configuration

### Default Settings
```python
# Command palette settings
PALETTE_WIDTH = 60
PALETTE_HEIGHT = 20
SEARCH_PLACEHOLDER = "Search commands..."

# Hotkey settings  
CASE_SENSITIVE = False
MODIFIER_KEYS = ["CTRL", "CMD"]
PALETTE_TRIGGER = "K"
```

### Customization Points
- **Visual Theme**: Colors, borders, fonts
- **Key Bindings**: Hotkey assignments
- **Search Behavior**: Fuzzy matching, ranking
- **Display Options**: Command grouping, sorting

## Error Handling

### Graceful Degradation
- **Missing Commands**: Fail silently with logging
- **Invalid Hotkeys**: Ignore unrecognized keys
- **System Errors**: Continue game operation
- **User Feedback**: Clear error messages when appropriate

### Validation
- **Command Registration**: Validate required fields
- **Hotkey Conflicts**: Detect and warn about duplicates
- **Action Execution**: Catch and log exceptions
- **Input Sanitization**: Safe handling of user input

## Accessibility

### Keyboard-First Design
- **Full Keyboard Navigation**: No mouse required
- **Clear Visual Feedback**: Highlighted selections
- **Consistent Shortcuts**: Standard key combinations
- **Help Integration**: Built-in command discovery

### Future Accessibility
- **Screen Reader Support**: Semantic markup
- **High Contrast Mode**: Alternative color schemes
- **Large Text Support**: Scalable UI elements
- **Voice Commands**: Speech recognition integration

## Conclusion

The Command Palette and Hotkey System provides a modern, efficient interface for game control that scales from simple layer switching to complex command sequences. The design prioritizes discoverability, performance, and extensibility while maintaining the intuitive camera-based gameplay model.

The system successfully transforms the 3D layered world from a terrain-restricted exploration model to a free-form camera control system, making the game more accessible and responsive to player intent.
