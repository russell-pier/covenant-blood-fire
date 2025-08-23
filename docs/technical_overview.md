# Technical Overview: Camera, UI, and World Systems

## Table of Contents
1. [Camera System Architecture](#camera-system-architecture)
2. [UI System Architecture](#ui-system-architecture)
3. [World Generation System](#world-generation-system)
4. [System Integration](#system-integration)
5. [Performance Considerations](#performance-considerations)

---

## Camera System Architecture

### Overview
The camera system provides a viewport-based approach where the world scrolls beneath a fixed crosshair cursor, creating an intuitive exploration experience.

### Core Components

#### 1. Camera (`src/covenant/camera/viewport.py`)
```python
class Camera:
    - world_x, world_y: int          # Camera position in world coordinates
    - screen_width, screen_height: int  # Viewport dimensions
    - config: CameraConfig           # Movement speed, crosshair position
```

**Key Features:**
- **Fixed Crosshair**: Always positioned at `(40, 25)` screen coordinates
- **World Scrolling**: Camera moves through world, not player character
- **Coordinate Conversion**: Bidirectional world ↔ screen coordinate mapping
- **Movement System**: WASD/arrow key movement with configurable speed

#### 2. 3D Camera System (`src/covenant/world/camera_3d.py`)
```python
class CameraSystem:
    - current_layer: WorldLayer      # SURFACE, UNDERGROUND, MOUNTAINS
    - world_x, world_y: int         # 3D camera position
    - is_transitioning: bool        # Layer transition state
```

**Layer Management:**
- **Surface Layer**: Shows terrain with mountain cliffs as walls
- **Underground Layer**: Cave systems with darker lighting
- **Mountain Layer**: High-altitude terrain with lightened surface below
- **Layer Transitions**: Z/X/C keys for instant layer switching

#### 3. Viewport System (`src/covenant/camera/viewport.py`)
```python
class Viewport:
    - camera: Camera                 # Associated camera instance
    - render_world()                # Main world rendering
    - render_crosshair()            # Cursor rendering
    - render_animals()              # Animal overlay rendering
```

**Rendering Pipeline:**
1. Calculate visible world bounds from camera position
2. Iterate through screen coordinates
3. Convert to world coordinates
4. Fetch terrain data (layered or basic)
5. Apply 3D camera layer filtering
6. Render terrain tiles to console
7. Overlay animals and crosshair

### Coordinate Systems

#### World Coordinates
- **Origin**: `(0, 0)` at world center
- **Range**: Infinite in all directions
- **Units**: Individual tiles

#### Screen Coordinates
- **Origin**: `(0, 0)` at top-left of console
- **Range**: `(0, 0)` to `(console.width-1, console.height-1)`
- **Crosshair**: Fixed at `(40, 25)`

#### Chunk Coordinates
- **Origin**: `(0, 0)` contains world `(0, 0)`
- **Size**: 32×32 tiles per chunk
- **Conversion**: `chunk_x = world_x // 32`

---

## UI System Architecture

### Overview
The UI system uses floating panels that render on top of the world, providing game information without blocking the view.

### Core Components

#### 1. Status Bar (`src/covenant/ui/status_bar.py`)
```python
class StatusBar:
    - is_visible: bool              # Toggle visibility
    - content_height: int = 1       # Content lines
    - height: int = 3              # Total with borders
```

**Features:**
- **Position**: Top of screen with 1-line margin
- **Content**: Terrain info, resources, elevation, temperature
- **Layer Display**: Current layer (Surface/Underground/Mountains)
- **Floating Design**: Dark gray background with rounded borders

#### 2. Instructions Panel (`src/covenant/ui/instructions_panel.py`)
```python
class InstructionsPanel:
    - is_visible: bool              # Toggle visibility
    - content_height: int = 3       # Content lines
    - height: int = 5              # Total with borders
```

**Features:**
- **Position**: Bottom of screen with 1-line margin
- **Content**: Command palette help, layer switching, help toggle
- **Responsive**: Adapts to console width
- **Styled**: Rounded borders with color-coded text

#### 3. Command Palette (`src/covenant/commands/command_system.py`)
```python
class CommandPalette:
    - is_open: bool                 # Visibility state
    - search_query: str            # Current search text
    - selected_index: int          # Selected command
    - filtered_commands: List      # Search results
```

**Features:**
- **Activation**: Cmd+K/Ctrl+K hotkey
- **Search**: Real-time command filtering
- **Navigation**: Arrow keys + Enter to execute
- **Categories**: Organized command grouping
- **Hotkey Display**: Shows keyboard shortcuts

#### 4. Zoomed Map System (`src/covenant/ui/zoomed_map.py`)
```python
class ZoomedMapRenderer:
    - current_mode: MapMode         # DETAILED or OVERVIEW
    - camera_x, camera_y: int      # Detailed camera position
    - zoom_camera_x, zoom_camera_y: int  # Overview camera position
```

**Dual-Mode Rendering:**
- **Detailed Mode**: Full tile-by-tile world rendering
- **Overview Mode**: 4×4 pixel chunks for strategic view
- **Performance**: 97% faster with single-sample chunk analysis
- **Controls**: M key toggle, WASD navigation, Enter fast travel

### UI Rendering Pipeline

#### Layered Rendering Order
1. **World Background**: Full-screen terrain rendering
2. **Animals**: Creature overlays on terrain
3. **Crosshair**: Fixed cursor at screen center
4. **Status Bar**: Floating panel at top
5. **Instructions Panel**: Floating panel at bottom
6. **Command Palette**: Modal overlay (when open)
7. **Map System**: Full-screen override (overview mode)

#### Floating Panel System
- **Background**: Dark gray `(60, 60, 60)` with transparency effect
- **Borders**: Light gray `(120, 120, 120)` rounded corners
- **Text**: White `(255, 255, 255)` with color-coded highlights
- **Margins**: 2-character padding from screen edges
- **Responsive**: Adapts to different console sizes

---

## World Generation System

### Overview
The world generation system creates infinite, procedural worlds using layered noise generation, environmental systems, and chunk-based loading.

### Core Components

#### 1. World Generator (`src/covenant/world/generator.py`)
```python
class WorldGenerator:
    - chunk_manager: ChunkManager           # Chunk loading/caching
    - noise_generator: NoiseGenerator       # Base terrain noise
    - environmental_generator: EnvironmentalGenerator  # Climate system
    - layered_generator: LayeredWorldGenerator  # 3D layer system
    - terrain_mapper: TerrainMapper         # Noise → terrain conversion
    - animal_manager: AnimalManager         # Creature spawning
    - camera_3d: CameraSystem              # Layer management
```

**Generation Pipeline:**
1. **Chunk Request**: Camera movement triggers chunk loading
2. **Environmental Data**: Generate elevation, moisture, temperature
3. **Layered Terrain**: Create underground, surface, mountain layers
4. **Terrain Mapping**: Convert environmental data to terrain types
5. **Resource Placement**: Add clustered resource nodes
6. **Animal Spawning**: Place herds based on terrain suitability
7. **Chunk Caching**: Store in LRU cache for performance

#### 2. Chunk Management (`src/covenant/world/chunks.py`)
```python
class ChunkManager:
    - chunk_size: int = 32              # Tiles per chunk
    - cache_size: int = 64             # Max chunks in memory
    - _chunks: Dict[ChunkCoordinate, Chunk]  # Active chunks
    - _access_order: List              # LRU tracking
```

**Chunk Lifecycle:**
1. **Loading**: Generate when camera approaches
2. **Caching**: Keep in memory for fast access
3. **LRU Eviction**: Remove oldest chunks when cache full
4. **Persistence**: No disk storage - pure procedural generation

#### 3. Environmental System (`src/covenant/world/environmental.py`)
```python
class EnvironmentalGenerator:
    - elevation_noise: NoiseGenerator       # Terrain height
    - moisture_noise: NoiseGenerator        # Rainfall/humidity
    - temperature_noise: NoiseGenerator     # Climate zones
```

**Environmental Factors:**
- **Elevation**: -200m (caves) to 3000m (peaks)
- **Moisture**: 0.0 (desert) to 1.0 (swamp)
- **Temperature**: -20°C (arctic) to 40°C (desert)
- **Latitude Effects**: Temperature decreases with distance from equator
- **Elevation Effects**: Temperature drops 6.5°C per 1000m altitude

#### 4. Layered Generation (`src/covenant/world/layered_generator.py`)
```python
class LayeredWorldGenerator:
    - noise_elevation: NoiseGenerator       # Base elevation
    - noise_caves: NoiseGenerator          # Underground systems
    - noise_mountains: NoiseGenerator      # Mountain ranges
    - resource_generator: ClusteredResourceGenerator  # Resource placement
```

**Layer Generation:**
- **Underground**: Cave systems, ore veins, underground water
- **Surface**: Primary terrain layer with entrances/exits
- **Mountains**: High-altitude terrain, only where elevation permits
- **Connectivity**: Cave entrances and mountain access points

### Terrain Types and Mapping

#### Environmental → Terrain Mapping
```python
def environmental_to_terrain(env_data: EnvironmentalData) -> TerrainType:
    if env_data.elevation < -50:
        return DEEP_WATER if env_data.moisture > 0.3 else CAVE_WALL
    elif env_data.elevation < 0:
        return SHALLOW_WATER if env_data.moisture > 0.5 else SAND
    elif env_data.temperature > 30 and env_data.moisture < 0.2:
        return DESERT
    elif env_data.moisture > 0.7:
        return SWAMP if env_data.temperature > 10 else GRASS
    elif env_data.elevation > 1500:
        return MOUNTAIN_PEAK if env_data.elevation > 2500 else HILLS
    else:
        return FOREST if env_data.moisture > 0.4 else GRASS
```

#### Terrain Properties
Each terrain type defines:
- **Visual**: Character variants, foreground/background colors
- **Gameplay**: Passability, movement cost, resource potential
- **Environmental**: Elevation range, moisture requirements
- **Layer Specific**: Different appearance per layer

---

## System Integration

### Main Game Loop (`src/covenant/main.py`)

#### Initialization Sequence
1. **Console Setup**: Create tcod console with font loading
2. **World Generation**: Initialize generators and chunk manager
3. **Camera System**: Create camera and viewport
4. **UI Components**: Initialize panels and command system
5. **Map Renderer**: Setup dual-mode map system
6. **Command Registration**: Register layer switching and UI commands

#### Render Pipeline
```python
def render(self):
    # 1. Clear console
    self.console.clear()
    
    # 2. Update camera position
    camera_x, camera_y = self.camera.get_position()
    self.map_renderer.set_camera_position(camera_x, camera_y)
    
    # 3. Update world state
    self.world_generator.update_animals_continuous()
    
    # 4. Mode-specific rendering
    if self.map_renderer.is_detailed_mode():
        # Detailed mode: full world + UI
        self.viewport.render_world(console, world_generator)
        self.viewport.render_crosshair(console, world_generator)
        self.status_bar.render(console, world_generator, cursor_pos)
        self.instructions_panel.render(console)
    else:
        # Overview mode: strategic map only
        self.map_renderer.render_current_mode(console)
    
    # 5. Always render command palette
    self.command_palette.render(console)
```

#### Input Handling
```python
def handle_keydown(self, key):
    # Movement (both modes)
    if key in [UP, DOWN, LEFT, RIGHT, W, A, S, D]:
        if self.map_renderer.is_detailed_mode():
            self.camera.move(dx, dy)
        else:
            self.map_renderer.handle_movement(dx, dy)
    
    # Layer switching (detailed mode only)
    elif key == Z: world_generator.change_layer(SURFACE)
    elif key == X: world_generator.change_layer(UNDERGROUND)
    elif key == C: world_generator.change_layer(MOUNTAINS)
    
    # Map toggle
    elif key == M: self.map_renderer.toggle_map_mode()
    
    # Fast travel (overview mode)
    elif key == ENTER and self.map_renderer.is_overview_mode():
        self.map_renderer.fast_travel_to_cursor()
    
    # UI toggles
    elif key == H: self.instructions_panel.toggle_visibility()
    elif key == CMD_K: self.command_palette.toggle()
```

### Data Flow Architecture

#### Camera → World → Rendering
```
Camera Position → Chunk Loading → Terrain Generation → Layer Filtering → Screen Rendering
     ↓                ↓                 ↓                  ↓               ↓
  (world_x,y)    ChunkManager    Environmental Data   3D Camera      Console Output
                                      ↓
                                 Layered Terrain
                                      ↓
                                 Resource Placement
                                      ↓
                                 Animal Spawning
```

#### UI → Command → Action
```
User Input → Command Palette → Command Registry → Action Execution → State Update
     ↓             ↓               ↓                    ↓              ↓
  Keyboard      Search Filter   Command Lookup    Layer Change    UI Refresh
```

---

## Performance Considerations

### Chunk Management Optimizations
- **LRU Caching**: Keep 64 chunks in memory with automatic eviction
- **Load Radius**: Generate chunks 3 units ahead of camera
- **Unload Radius**: Remove chunks 5 units behind camera
- **Lazy Generation**: Only generate chunks when actually needed

### Map System Optimizations
- **Single Sampling**: 1 sample per chunk instead of 9 (90% reduction)
- **Aggressive Caching**: 60-second TTL cache for chunk summaries
- **Pre-computed Colors**: Terrain appearance lookup tables
- **Background Processing**: Async chunk analysis with limited workers
- **Reduced Thread Contention**: Targeted locking only for generation queue

### Rendering Optimizations
- **Viewport Culling**: Only render visible screen area
- **Layer Filtering**: Apply 3D camera effects during rendering
- **Batch Operations**: Group similar rendering operations
- **Floating UI**: Render panels on top without clearing world

### Memory Management
- **Chunk Eviction**: Automatic cleanup of distant chunks
- **Resource Pooling**: Reuse terrain and environmental data objects
- **Lazy Loading**: Generate data only when accessed
- **Cache Limits**: Bounded memory usage with configurable limits

### Threading Architecture
- **Main Thread**: UI, input handling, primary rendering
- **Background Thread**: Map chunk analysis, animal updates
- **Thread Safety**: RLock protection for shared data structures
- **Lock Minimization**: Reduce contention with targeted synchronization

---

This technical overview provides a comprehensive understanding of how the camera, UI, and world systems work together to create a seamless, performant game experience. Each system is designed with modularity, performance, and maintainability in mind.
