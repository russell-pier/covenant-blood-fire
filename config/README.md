# Configuration System

Covenant: Blood & Fire uses TOML configuration files for easy customization of visual and gameplay elements.

## Configuration Files

### `visual.toml`
Controls the visual representation of all game elements:

- **Terrain**: Characters, colors, movement costs, passability
- **Animals**: Characters and colors for different states
- **UI Elements**: Cursor, crosshair, etc.

### `environmental.toml`
Controls world generation parameters:

- **Environmental Mapping**: Rules for terrain generation based on elevation, moisture, temperature
- **Noise Generation**: Parameters for Perlin noise generation

## Customization Examples

### Changing Animal Appearance

To make sheep use different characters:

```toml
[animals.sheep.grazing]
characters = ["♪"]  # Use musical note instead of 's'
foreground_color = [255, 255, 255]

[animals.sheep.moving]
characters = ["♫"]  # Different musical note for movement
foreground_color = [255, 255, 255]
```

### Adding New Terrain Types

To add a new terrain type, first add it to the `TerrainType` enum in the code, then add its visual config:

```toml
[terrain.lava]
characters = ["~", "≈", "∼"]
foreground_color = [255, 69, 0]  # Red-orange
background_color = [139, 0, 0]   # Dark red
passable = false
movement_cost = "inf"
```

### Modifying World Generation

To make mountains more common:

```toml
[[environmental_mapping.rules]]
name = "mountains"
terrain_type = "mountains"
conditions = { elevation_min = 0.6, temperature_max = 0.5 }  # Lower threshold
```

## Color Format

Colors are specified as RGB arrays: `[red, green, blue]` where each value is 0-255.

Examples:
- White: `[255, 255, 255]`
- Black: `[0, 0, 0]`
- Red: `[255, 0, 0]`
- Green: `[0, 255, 0]`
- Blue: `[0, 0, 255]`

## Character Arrays

Most visual elements support multiple characters for variation:

```toml
characters = [".", ",", "'", "`"]  # Game will randomly choose from these
```

## Hot Reloading

During development, you can reload configs without restarting:

```python
from src.empires.config import reload_configs
reload_configs()
```

## Fallback System

If config files are missing or invalid, the game falls back to hardcoded defaults, ensuring it always runs.

## Theme Support

You can create different visual themes by copying and modifying the config files. The `[theme]` section in `visual.toml` contains metadata about the current theme.
