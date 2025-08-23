# World Generation System Design

## Overview

This document outlines the design for a chunk-based world generation system for Covenant: Blood & Fire. The system provides infinite procedural world generation using Perlin noise, with a camera/viewport system that replaces direct player movement with map scrolling.

## Architecture Overview

### Core Components

1. **Noise Generation Module** (`src/empires/world/noise.py`)
2. **Chunk Management System** (`src/empires/world/chunks.py`)
3. **World Generation Module** (`src/empires/world/generator.py`)
4. **Camera/Viewport System** (`src/empires/camera/viewport.py`)
5. **Terrain Types** (`src/empires/world/terrain.py`)

### Module Dependencies

```files
Game Class
    ├── Camera/Viewport System
    │   └── World Generation Module
    │       ├── Chunk Management System
    │       ├── Noise Generation Module
    │       └── Terrain Types
    └── Rendering Pipeline (existing tcod)
```

## Detailed Component Design

### 1. Noise Generation Module

**File**: `src/empires/world/noise.py`

**Purpose**: Provides Perlin noise generation for procedural terrain creation.

**Key Classes**:

- `NoiseGenerator`: Main noise generation class
- `NoiseConfig`: Configuration for noise parameters

**Key Features**:

- Multiple octaves for detailed terrain
- Configurable frequency, amplitude, and persistence
- Seamless noise generation across chunk boundaries
- Seed-based generation for reproducible worlds

### 2. Chunk Management System

**File**: `src/empires/world/chunks.py`

**Purpose**: Manages world chunks for efficient memory usage and loading.

**Key Classes**:

- `Chunk`: Individual world chunk containing terrain data
- `ChunkManager`: Manages chunk loading, unloading, and caching
- `ChunkCoordinate`: Coordinate system for chunk addressing

**Key Features**:

- Configurable chunk size (default: 32x32 tiles)
- LRU cache for chunk management
- Efficient chunk loading/unloading based on camera position
- Thread-safe chunk generation for performance

### 3. World Generation Module

**File**: `src/empires/world/generator.py`

**Purpose**: Coordinates terrain generation using noise and manages world state.

**Key Classes**:

- `WorldGenerator`: Main world generation coordinator
- `TerrainMapper`: Maps noise values to terrain types

**Key Features**:

- Infinite world generation
- Biome-based terrain generation
- Seamless chunk transitions
- Configurable terrain thresholds

### 4. Camera/Viewport System

**File**: `src/empires/camera/viewport.py`

**Purpose**: Manages camera position and viewport rendering.

**Key Classes**:

- `Camera`: Camera position and movement logic
- `Viewport`: Rendering viewport management
- `Crosshair`: Fixed crosshair cursor display

**Key Features**:

- Fixed crosshair at screen center (40, 25)
- Smooth camera movement with arrow keys
- World-to-screen coordinate conversion
- Efficient viewport culling

### 5. Terrain Types

**File**: `src/empires/world/terrain.py`

**Purpose**: Defines terrain types and their visual properties.

**Key Classes**:

- `TerrainType`: Enumeration of terrain types
- `TerrainProperties`: Visual and gameplay properties for each terrain

**Terrain Types**:

- `WATER`: Deep blue, impassable
- `SHALLOW_WATER`: Light blue, slow movement
- `SAND`: Yellow/tan, normal movement
- `GRASS`: Green variations, normal movement
- `FOREST`: Dark green, slow movement
- `HILLS`: Brown/gray, slow movement
- `MOUNTAINS`: Dark gray, impassable

## Coordinate Systems

### World Coordinates

- Infinite 2D plane with integer coordinates
- Origin at (0, 0) with positive X east, positive Y south
- Used for absolute positioning in the world

### Chunk Coordinates

- Chunks addressed by (chunk_x, chunk_y)
- Each chunk covers CHUNK_SIZE × CHUNK_SIZE world tiles
- Conversion: `chunk_x = world_x // CHUNK_SIZE`

### Screen Coordinates

- 80×50 console with (0,0) at top-left
- Crosshair fixed at (40, 25)
- Viewport shows world tiles around camera position

## Configuration Parameters

### Noise Generation

```python
NOISE_CONFIG = {
    'octaves': 4,
    'frequency': 0.05,
    'amplitude': 1.0,
    'persistence': 0.5,
    'lacunarity': 2.0,
    'seed': 12345
}
```

### Chunk Management

```python
CHUNK_CONFIG = {
    'chunk_size': 32,
    'cache_size': 64,  # Number of chunks to keep in memory
    'load_radius': 3,  # Chunks to load around camera
    'unload_radius': 5  # Distance to unload chunks
}
```

### Camera System

```python
CAMERA_CONFIG = {
    'crosshair_x': 40,
    'crosshair_y': 25,
    'movement_speed': 1,  # Tiles per key press
    'smooth_scrolling': False  # For future enhancement
}
```

## Performance Considerations

### Memory Management

- LRU cache for chunks prevents unlimited memory growth
- Chunks unloaded when camera moves beyond unload radius
- Terrain data stored efficiently as byte arrays

### Rendering Optimization

- Only visible chunks are rendered
- Viewport culling reduces unnecessary drawing
- Chunk boundaries pre-calculated for fast lookup

### Generation Performance

- Noise generation cached per chunk
- Background chunk loading for smooth experience
- Minimal garbage collection through object reuse

## Integration with Existing Game Class

### Modified Game Loop

1. **Event Handling**: Arrow keys move camera instead of player
2. **Update Phase**: Update camera position and chunk loading
3. **Rendering**: Render visible world tiles through viewport
4. **UI**: Display world coordinates instead of screen coordinates

### Backward Compatibility

- Maintains 80×50 console size
- Preserves existing tcod rendering pipeline
- Keeps 60 FPS target performance
- Retains existing input handling patterns

## Future Enhancements

### Phase 2 Features

- Smooth scrolling animation
- Multiple biomes with transition zones
- Rivers and roads generation
- Resource node placement

### Phase 3 Features

- Multiplayer world synchronization
- Save/load world state
- Dynamic world modification
- Advanced terrain features (caves, cliffs)

## Implementation Order

1. **Noise Generation**: Foundation for all terrain
2. **Terrain Types**: Define visual and gameplay properties
3. **Chunk System**: Memory-efficient world management
4. **World Generator**: Coordinate terrain creation
5. **Camera System**: Replace player movement
6. **Integration**: Connect all systems with Game class
7. **Testing**: Comprehensive unit and integration tests
8. **Optimization**: Performance tuning for 60 FPS

## Testing Strategy

### Unit Tests

- Noise generation consistency
- Chunk loading/unloading logic
- Coordinate system conversions
- Terrain type mapping

### Integration Tests

- Camera movement with world scrolling
- Chunk boundaries and seamless transitions
- Performance under continuous movement
- Memory usage during extended play

### Performance Tests

- 60 FPS maintenance during rapid movement
- Memory usage with large cache sizes
- Chunk generation time benchmarks
- Rendering performance with full viewport
