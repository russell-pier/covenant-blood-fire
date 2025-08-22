# 3D Layered World System Design

## Overview

The 3D Layered World System introduces vertical depth to the game world by implementing three distinct layers: Underground, Surface, and Mountains. Players can transition between these layers through specific entrance points, creating a rich, multi-dimensional exploration experience.

## Core Architecture

### Layer Structure

The world consists of three primary layers:

1. **Underground Layer (Layer 0)**: Cave systems, underground water, and ore veins
2. **Surface Layer (Layer 1)**: Traditional overworld terrain (grasslands, forests, water)
3. **Mountain Layer (Layer 2)**: High-altitude terrain with peaks, slopes, and snow

### Key Components

#### WorldLayer Enum
```python
class WorldLayer(Enum):
    UNDERGROUND = 0
    SURFACE = 1  
    MOUNTAINS = 2
```

#### LayeredTerrainData Structure
Each world position contains terrain data for all three layers:
- `underground`: Underground terrain data
- `surface`: Surface terrain data  
- `mountains`: Mountain terrain data (optional)
- `has_cave_entrance`: Boolean indicating cave access
- `has_mountain_access`: Boolean indicating mountain access

## Terrain Types

### Underground Terrains
- **Cave Floor**: Walkable cave ground with earth tones
- **Cave Wall**: Impassable rock formations
- **Underground Water**: Subterranean water bodies
- **Ore Vein**: Rare mineral deposits with golden highlights

### Surface Terrains
- **Grassland**: Basic ground terrain
- **Forest**: Tree-covered areas
- **Water**: Rivers, lakes, and seas
- **Desert**: Arid regions
- **Cave Entrance**: Access points to underground layer
- **Mountain Base**: Transition zones to mountain layer

### Mountain Terrains
- **Mountain Peak**: High elevation rocky formations
- **Mountain Slope**: Angled terrain on mountainsides
- **Mountain Cliff**: Steep, impassable rock faces
- **Snow**: High-altitude snow-covered areas

## Camera System

### Layer Transitions
The `CameraSystem` manages vertical movement between layers:

- **Layer Validation**: Checks if transitions are possible based on terrain
- **Transition Animation**: Smooth visual transitions between layers
- **Render Management**: Applies appropriate shading and visual effects

### Visual Effects by Layer

#### Surface Layer Rendering
- **Mountain Shadows**: Areas with mountains above show darkened terrain
- **Cave Entrances**: Marked with special symbols and black backgrounds
- **Standard Terrain**: Normal surface terrain rendering

#### Underground Layer Rendering
- **Cave Areas**: Full underground terrain visibility
- **Blocked Areas**: Solid black where no cave entrance exists above
- **Atmospheric Lighting**: Darker color palette for underground feel

#### Mountain Layer Rendering
- **Mountain Terrain**: Full mountain terrain visibility
- **Surface Hints**: Lightened surface terrain visible where no mountains exist
- **Elevation Effects**: Enhanced contrast for high-altitude atmosphere

## World Generation

### Multi-Layer Generation Process

1. **Base Elevation Map**: Primary heightmap drives all layer generation
2. **Underground Generation**: Cave systems based on noise and elevation
3. **Surface Generation**: Traditional terrain generation
4. **Mountain Generation**: High-elevation terrain overlay
5. **Connectivity Analysis**: Determine entrance points between layers

### Noise-Based Generation

Different noise generators create varied terrain:
- **Elevation Noise**: Base world heightmap
- **Cave Noise**: Underground cave system patterns
- **Mountain Noise**: High-altitude terrain features
- **Surface Noise**: Surface terrain variations
- **Detail Noise**: Fine-grained terrain variations

### Layer Connectivity Rules

#### Cave Entrances
- Only exist above elevation threshold (not underwater)
- Require both surface access and underground cave space
- Distributed using detail noise for organic placement

#### Mountain Access
- Automatically available where mountain terrain exists
- Based on elevation thresholds and mountain noise
- Provides seamless transition to high-altitude areas

## Technical Implementation

### Data Structures

#### TerrainData
```python
@dataclass 
class TerrainData:
    terrain_type: TerrainType
    char: str
    fg_color: Tuple[int, int, int]
    bg_color: Tuple[int, int, int]
    elevation: float
    is_passable: bool = True
    is_entrance: bool = False
```

#### LayeredTerrainData
```python
@dataclass
class LayeredTerrainData:
    underground: TerrainData
    surface: TerrainData 
    mountains: Optional[TerrainData]
    has_cave_entrance: bool = False
    has_mountain_access: bool = False
```

### Generation Parameters

- **Cave Scale**: 0.12 (detailed cave systems)
- **Mountain Scale**: 0.006 (large mountain ranges)
- **Surface Scale**: 0.008 (medium surface features)
- **Chunk Size**: 32x32 tiles per chunk

## Gameplay Integration

### Player Movement
- **Horizontal Movement**: Standard movement within current layer
- **Vertical Movement**: Layer transitions at entrance points
- **Movement Validation**: Check passability and entrance availability

### Layer-Specific Features

#### Underground Exploration
- **Resource Gathering**: Ore veins provide valuable materials
- **Navigation Challenges**: Limited visibility and complex cave networks
- **Water Hazards**: Underground water bodies create obstacles

#### Surface Activities
- **Standard Gameplay**: Traditional overworld mechanics
- **Entrance Discovery**: Finding and accessing other layers
- **Terrain Variety**: Diverse biomes and environments

#### Mountain Adventures
- **High-Altitude Challenges**: Unique mountain terrain navigation
- **Scenic Views**: Enhanced visual experience at elevation
- **Weather Effects**: Snow and harsh mountain conditions

## Performance Considerations

### Memory Management
- **Lazy Loading**: Generate layers only when accessed
- **Chunk-Based System**: Load/unload chunks based on player position
- **Layer Caching**: Cache frequently accessed layer data

### Rendering Optimization
- **Layer-Specific Rendering**: Only render current layer with hints
- **Transition Effects**: Smooth but efficient layer switching
- **Color Optimization**: Pre-calculated color variations

## Future Enhancements

### Potential Expansions
- **Deep Underground**: Additional underground layers (mines, caverns)
- **Sky Layer**: Floating islands or aerial terrain
- **Underwater Layer**: Submarine exploration beneath water bodies
- **Dynamic Weather**: Layer-specific weather systems

### Advanced Features
- **Layer Physics**: Different movement rules per layer
- **Environmental Hazards**: Layer-specific dangers and challenges
- **Resource Distribution**: Layer-based resource availability
- **Creature Ecology**: Layer-specific fauna and behavior

## Integration Points

### Existing Systems
- **World Generation**: Extends current terrain generation
- **Rendering Engine**: Enhances current display system
- **Player Movement**: Builds on existing movement mechanics
- **Chunk Management**: Integrates with current chunk system

### Dependencies
- **NoiseGenerator**: Existing noise generation system
- **TerrainData**: Current terrain data structures
- **Chunk System**: Current world chunk management
- **Rendering Pipeline**: Current display and color systems
