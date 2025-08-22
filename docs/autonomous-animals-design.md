# Autonomous Animals with Flocking Behavior System

## Overview

This system implements autonomous animals (sheep and cows) with realistic flocking behavior based on boid algorithms. Animals exhibit natural behaviors like grazing, wandering, and group cohesion while avoiding obstacles and responding to environmental factors.

## Core Design Principles

### Shared Boid Logic
All herd animals (sheep, cows) share the same fundamental flocking behaviors:
- **Separation**: Avoid crowding neighbors
- **Alignment**: Match velocity with nearby animals
- **Cohesion**: Move toward group center
- **Obstacle Avoidance**: Navigate around terrain features
- **Wandering**: Random exploration when not following other behaviors

### Animal-Specific Behaviors
While sharing core boid logic, each animal type has unique characteristics:

**Sheep**:
- Smaller, faster, more nervous
- Tighter flocking behavior
- Quick state transitions
- Higher separation weight (avoid crowding)

**Cows**:
- Larger, slower, more deliberate
- Looser flocking behavior
- Longer grazing periods
- Lower separation weight (comfortable closer together)

## System Architecture

### Core Components

#### 1. Vector2D Class
```python
@dataclass
class Vector2D:
    x: float
    y: float
    # Mathematical operations for movement calculations
```

#### 2. Base Animal Class (Abstract)
```python
@dataclass
class Animal:
    # Shared properties and boid behavior methods
    # Abstract methods for animal-specific behaviors
```

#### 3. Specific Animal Classes
```python
class Sheep(Animal):
    # Sheep-specific parameters and behaviors

class Cow(Animal):
    # Cow-specific parameters and behaviors
```

#### 4. Herd Management
```python
class Herd:
    # Manages groups of animals with shared flocking behavior
    # Generic for any animal type

class AnimalManager:
    # World-level management of all animal herds
```

### Animal States

```python
class AnimalState(Enum):
    GRAZING = "grazing"    # Eating, minimal movement
    MOVING = "moving"      # Active flocking behavior
    FLEEING = "fleeing"    # Panic response to threats
    IDLE = "idle"          # Brief pauses between activities
```

### Animal Types

```python
class AnimalType(Enum):
    SHEEP = "sheep"
    COW = "cow"
    WOLF = "wolf"    # Future predator
```

## Behavioral Parameters

### Sheep Configuration
- **Movement**: Fast (0.3-0.4 tiles/update), agile
- **Flocking Radii**: Tight (separation: 2.0, alignment: 4.0, cohesion: 6.0)
- **Behavior Weights**: High separation (2.0), moderate cohesion (1.5)
- **State Timing**: Quick transitions (graze 3-8s, move 2-5s)
- **Visual**: ♪♫♬♩ characters, white color

### Cow Configuration
- **Movement**: Slow (0.1-0.2 tiles/update), deliberate
- **Flocking Radii**: Loose (separation: 3.0, alignment: 6.0, cohesion: 8.0)
- **Behavior Weights**: Low separation (1.0), high cohesion (2.0)
- **State Timing**: Long transitions (graze 8-15s, move 3-8s)
- **Visual**: ♄♅♆♇ characters, brown color

## Implementation Details

### Shared Boid Algorithms

#### Separation Force
```python
def _separation(self, nearby_animals: List['Animal']) -> Vector2D:
    # Calculate force to avoid crowding
    # Weight by distance (closer = stronger force)
    # Apply animal-specific separation radius and weight
```

#### Alignment Force
```python
def _alignment(self, nearby_animals: List['Animal']) -> Vector2D:
    # Match velocity with neighbors
    # Average nearby animal velocities
    # Apply animal-specific alignment radius and weight
```

#### Cohesion Force
```python
def _cohesion(self, nearby_animals: List['Animal']) -> Vector2D:
    # Move toward group center
    # Calculate center of mass of nearby animals
    # Apply animal-specific cohesion radius and weight
```

### Animal-Specific Implementations

#### State Management
Each animal type overrides state transition logic:
- Sheep: Quick, nervous transitions
- Cows: Slow, deliberate transitions

#### Movement Parameters
Animal-specific speed, force, and radius values are set in constructors.

#### Visual Representation
Each animal type has unique characters and colors for different states.

### Terrain Integration

Animals respect terrain constraints:
- **Impassable**: Water, cave walls, mountain cliffs
- **Preferred**: Grassland, plains for grazing
- **Avoided**: Steep slopes, rocky terrain

### Performance Considerations

- **Spatial Partitioning**: Only calculate flocking for nearby animals
- **Update Frequency**: 10 Hz update rate for smooth movement
- **State Caching**: Cache expensive calculations between frames
- **Culling**: Don't update animals far from player view

## Integration with World System

### Spawning
```python
animal_manager.spawn_herd(
    animal_type=AnimalType.SHEEP,
    center_x=15, center_y=20,
    herd_id="sheep_herd_1",
    size=8
)
```

### Rendering
```python
# Get all animal positions for rendering
animal_positions = animal_manager.get_all_animal_positions()
for x, y, char, color in animal_positions:
    console.print(x, y, char, fg=color)
```

### Player Interaction
- Animals flee when player approaches too quickly
- Can be harvested for resources (wool, meat, milk)
- Respond to player-built structures (fences, feeding areas)

## Future Extensions

### Predator-Prey Dynamics
- Wolves hunt sheep/cows
- Enhanced fleeing behavior
- Pack hunting algorithms

### Environmental Responses
- Seek shelter during storms
- Migrate based on seasons
- React to food scarcity

### Breeding and Population
- Natural reproduction
- Population growth/decline
- Genetic variation in behavior

### Player Management
- Domestication mechanics
- Feeding and care systems
- Breeding programs

## Technical Notes

### Dependencies
- Python 3.8+ with dataclasses
- Math library for vector calculations
- Time library for state management
- Random library for behavioral variation

### Performance Targets
- Support 50+ animals simultaneously
- Maintain 60 FPS with active flocking
- Minimal memory footprint per animal

### Testing Strategy
- Unit tests for vector math
- Behavioral tests for flocking algorithms
- Integration tests with terrain system
- Performance benchmarks for large herds
