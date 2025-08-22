"""
Autonomous Animals with Flocking Behavior System.

This module implements autonomous animals (sheep and cows) with realistic flocking
behavior based on boid algorithms. Animals exhibit natural behaviors like grazing,
wandering, and group cohesion while avoiding obstacles and responding to environmental factors.
"""

import math
import random
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .organic import OrganicTerrainData

# Import config system
try:
    from ..config import get_animal_visual
except ImportError:
    # Fallback if config system not available
    get_animal_visual = None


class AnimalType(Enum):
    """Types of animals in the world."""
    SHEEP = "sheep"
    COW = "cow"
    WOLF = "wolf"  # Future predator


class AnimalState(Enum):
    """Behavioral states for animals."""
    GRAZING = "grazing"    # Eating, minimal movement
    MOVING = "moving"      # Active flocking behavior
    FLEEING = "fleeing"    # Panic response to threats
    IDLE = "idle"          # Brief pauses between activities


@dataclass
class Vector2D:
    """Simple 2D vector for movement calculations."""
    x: float
    y: float
    
    def __add__(self, other: 'Vector2D') -> 'Vector2D':
        return Vector2D(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Vector2D') -> 'Vector2D':
        return Vector2D(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar: float) -> 'Vector2D':
        return Vector2D(self.x * scalar, self.y * scalar)
    
    def magnitude(self) -> float:
        """Calculate the magnitude (length) of the vector."""
        return math.sqrt(self.x * self.x + self.y * self.y)
    
    def normalize(self) -> 'Vector2D':
        """Return a normalized (unit length) version of this vector."""
        mag = self.magnitude()
        if mag > 0:
            return Vector2D(self.x / mag, self.y / mag)
        return Vector2D(0, 0)
    
    def limit(self, max_magnitude: float) -> 'Vector2D':
        """Limit the vector to a maximum magnitude."""
        if self.magnitude() > max_magnitude:
            normalized = self.normalize()
            return normalized * max_magnitude
        return self


@dataclass
class Animal(ABC):
    """
    Abstract base class for all animals with shared flocking behavior.
    
    This class implements the core boid algorithms that are shared between
    all herd animals (sheep, cows, etc.) while allowing for animal-specific
    customization through parameters and overrides.
    """
    
    # Identity
    id: int
    animal_type: AnimalType
    
    # Position and movement
    x: float
    y: float
    velocity: Vector2D = field(default_factory=lambda: Vector2D(0, 0))
    
    # Movement parameters (to be set by subclasses)
    max_speed: float = 0.3
    max_force: float = 0.1
    
    # Flocking behavior radii (to be set by subclasses)
    separation_radius: float = 2.0
    alignment_radius: float = 4.0
    cohesion_radius: float = 6.0
    
    # Behavior weights (to be set by subclasses)
    separation_weight: float = 2.0
    alignment_weight: float = 1.0
    cohesion_weight: float = 1.5
    wander_weight: float = 0.5
    
    # State management
    state: AnimalState = AnimalState.GRAZING
    state_timer: float = 0
    energy: float = 100.0  # For future hunger system
    last_update: float = field(default_factory=time.time)
    
    def update(self, nearby_animals: List['Animal'], terrain_data: Dict, delta_time: float) -> None:
        """
        Update animal behavior and position.
        
        Args:
            nearby_animals: List of animals within flocking range
            terrain_data: Dictionary of terrain data for obstacle avoidance
            delta_time: Time elapsed since last update
        """
        # Update state timer
        self.state_timer += delta_time
        
        # Handle state transitions (animal-specific)
        self._update_state()
        
        # Calculate flocking forces based on current state
        forces = []
        
        if self.state == AnimalState.MOVING:
            forces.extend([
                self._separation(nearby_animals),
                self._alignment(nearby_animals),
                self._cohesion(nearby_animals),
                self._wander()
            ])
        elif self.state == AnimalState.GRAZING:
            # Only gentle forces while grazing
            forces.extend([
                self._separation(nearby_animals) * 0.5,
                self._cohesion(nearby_animals) * 0.3
            ])
        elif self.state == AnimalState.FLEEING:
            # Panic mode - flee from threats
            forces.extend([
                self._separation(nearby_animals) * 3.0,
                self._flee_from_threats([])  # Empty for now
            ])
        
        # Apply terrain avoidance
        forces.append(self._avoid_obstacles(terrain_data))
        
        # Sum all forces and apply
        total_force = Vector2D(0, 0)
        for force in forces:
            if force:
                total_force = total_force + force
        
        # Update velocity and position
        self.velocity = (self.velocity + total_force).limit(self.max_speed)
        
        # Only move if we have significant velocity
        if self.velocity.magnitude() > 0.05:
            new_x = self.x + self.velocity.x
            new_y = self.y + self.velocity.y
            
            # Boundary and terrain checking
            if self._can_move_to(new_x, new_y, terrain_data):
                self.x = new_x
                self.y = new_y
    
    @abstractmethod
    def _update_state(self) -> None:
        """Handle state transitions (animal-specific implementation)."""
        pass
    
    @abstractmethod
    def get_render_char(self) -> str:
        """Get character to render based on current state."""
        pass
    
    @abstractmethod
    def get_color(self) -> Tuple[int, int, int]:
        """Get color for rendering this animal."""
        pass
    
    def _separation(self, nearby_animals: List['Animal']) -> Vector2D:
        """Steer away from nearby animals to avoid crowding."""
        separation_force = Vector2D(0, 0)
        count = 0
        
        for other in nearby_animals:
            distance = math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
            if 0 < distance < self.separation_radius:
                # Calculate vector away from other animal
                diff = Vector2D(self.x - other.x, self.y - other.y)
                diff = diff.normalize()
                # Weight by distance (closer = stronger force)
                diff = diff * (1.0 / distance)
                separation_force = separation_force + diff
                count += 1
        
        if count > 0:
            separation_force = separation_force * (1.0 / count)  # Average
            separation_force = separation_force.normalize() * self.max_speed
            separation_force = separation_force - self.velocity
            separation_force = separation_force.limit(self.max_force)
            return separation_force * self.separation_weight
        
        return Vector2D(0, 0)
    
    def _alignment(self, nearby_animals: List['Animal']) -> Vector2D:
        """Align velocity with nearby animals."""
        average_velocity = Vector2D(0, 0)
        count = 0
        
        for other in nearby_animals:
            distance = math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
            if 0 < distance < self.alignment_radius:
                average_velocity = average_velocity + other.velocity
                count += 1
        
        if count > 0:
            average_velocity = average_velocity * (1.0 / count)
            average_velocity = average_velocity.normalize() * self.max_speed
            alignment_force = average_velocity - self.velocity
            alignment_force = alignment_force.limit(self.max_force)
            return alignment_force * self.alignment_weight
        
        return Vector2D(0, 0)
    
    def _cohesion(self, nearby_animals: List['Animal']) -> Vector2D:
        """Steer toward the center of nearby animals."""
        center_of_mass = Vector2D(0, 0)
        count = 0
        
        for other in nearby_animals:
            distance = math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
            if 0 < distance < self.cohesion_radius:
                center_of_mass = center_of_mass + Vector2D(other.x, other.y)
                count += 1
        
        if count > 0:
            center_of_mass = center_of_mass * (1.0 / count)
            # Steer toward center
            desired = center_of_mass - Vector2D(self.x, self.y)
            desired = desired.normalize() * self.max_speed
            cohesion_force = desired - self.velocity
            cohesion_force = cohesion_force.limit(self.max_force)
            return cohesion_force * self.cohesion_weight
        
        return Vector2D(0, 0)
    
    def _wander(self) -> Vector2D:
        """Add random wandering behavior."""
        # Random direction with some smoothing
        angle = random.uniform(0, 2 * math.pi)
        wander_force = Vector2D(math.cos(angle), math.sin(angle))
        wander_force = wander_force * 0.1  # Small random force
        return wander_force * self.wander_weight
    
    def _avoid_obstacles(self, terrain_data: Dict) -> Vector2D:
        """Avoid water, cliffs, and other obstacles."""
        avoidance_force = Vector2D(0, 0)
        
        # Check terrain in a small radius around the animal
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                check_x = int(self.x + dx)
                check_y = int(self.y + dy)
                
                if (check_x, check_y) in terrain_data:
                    terrain = terrain_data[(check_x, check_y)]
                    
                    # Avoid water and other impassable terrain
                    if hasattr(terrain, 'terrain_type') and terrain.terrain_type.value in ['water', 'cave_wall']:
                        # Push away from obstacle
                        push = Vector2D(self.x - check_x, self.y - check_y)
                        if push.magnitude() > 0:
                            push = push.normalize() * 2.0
                            avoidance_force = avoidance_force + push
        
        return avoidance_force.limit(self.max_force)
    
    def _flee_from_threats(self, threats: List) -> Vector2D:
        """Flee from predators (future feature)."""
        # Placeholder for predator avoidance
        return Vector2D(0, 0)
    
    def _can_move_to(self, x: float, y: float, terrain_data: Dict) -> bool:
        """Check if animal can move to this position."""
        tile_x, tile_y = int(x), int(y)
        
        if (tile_x, tile_y) not in terrain_data:
            return False
        
        terrain = terrain_data[(tile_x, tile_y)]
        
        # Animals can't walk on water, through walls, etc.
        if hasattr(terrain, 'terrain_type'):
            impassable = ['water', 'cave_wall', 'mountain_cliff']
            return terrain.terrain_type.value not in impassable
        
        return True


class Sheep(Animal):
    """
    Sheep implementation with fast, nervous flocking behavior.

    Sheep are smaller, faster, and more nervous than cows. They exhibit
    tight flocking behavior with quick state transitions.
    """

    def __init__(self, id: int, x: float, y: float):
        """Initialize a sheep with sheep-specific parameters."""
        super().__init__(
            id=id,
            animal_type=AnimalType.SHEEP,
            x=x,
            y=y,
            max_speed=random.uniform(0.3, 0.4),  # Fast movement
            max_force=0.1,
            separation_radius=2.0,   # Tight flocking
            alignment_radius=4.0,
            cohesion_radius=6.0,
            separation_weight=random.uniform(1.5, 2.5),  # High separation (nervous)
            alignment_weight=1.0,
            cohesion_weight=random.uniform(1.0, 2.0),
            wander_weight=0.5
        )

    def _update_state(self) -> None:
        """Handle sheep state transitions (quick, nervous)."""
        if self.state == AnimalState.GRAZING:
            if self.state_timer > random.uniform(3, 8):  # Graze for 3-8 seconds
                self.state = AnimalState.MOVING
                self.state_timer = 0

        elif self.state == AnimalState.MOVING:
            if self.state_timer > random.uniform(2, 5):  # Move for 2-5 seconds
                if random.random() < 0.7:  # 70% chance to graze
                    self.state = AnimalState.GRAZING
                else:
                    self.state = AnimalState.IDLE
                self.state_timer = 0

        elif self.state == AnimalState.IDLE:
            if self.state_timer > random.uniform(1, 3):  # Idle briefly
                self.state = AnimalState.GRAZING
                self.state_timer = 0

    def get_render_char(self) -> str:
        """Get character to render based on state."""
        if get_animal_visual:
            visual_config = get_animal_visual("sheep", self.state.value)
            if visual_config and visual_config.characters:
                return visual_config.characters[0]

        # Fallback to hardcoded values
        if self.state == AnimalState.GRAZING:
            return "s"  # Grazing sheep (simple char for visibility)
        elif self.state == AnimalState.MOVING:
            return "S"  # Moving sheep
        elif self.state == AnimalState.FLEEING:
            return "!"  # Panicked sheep
        else:
            return "s"  # Idle sheep

    def get_color(self) -> Tuple[int, int, int]:
        """Get sheep color."""
        if get_animal_visual:
            visual_config = get_animal_visual("sheep", self.state.value)
            if visual_config:
                return visual_config.foreground_color

        # Fallback to white
        return (255, 255, 255)


class Cow(Animal):
    """
    Cow implementation with slow, deliberate flocking behavior.

    Cows are larger, slower, and more deliberate than sheep. They exhibit
    loose flocking behavior with longer state transitions.
    """

    def __init__(self, id: int, x: float, y: float):
        """Initialize a cow with cow-specific parameters."""
        super().__init__(
            id=id,
            animal_type=AnimalType.COW,
            x=x,
            y=y,
            max_speed=random.uniform(0.1, 0.2),  # Slow movement
            max_force=0.05,  # Less agile
            separation_radius=3.0,   # Loose flocking
            alignment_radius=6.0,
            cohesion_radius=8.0,
            separation_weight=random.uniform(0.8, 1.2),  # Low separation (comfortable closer)
            alignment_weight=0.8,
            cohesion_weight=random.uniform(1.5, 2.5),  # High cohesion
            wander_weight=0.3  # Less wandering
        )

    def _update_state(self) -> None:
        """Handle cow state transitions (slow, deliberate)."""
        if self.state == AnimalState.GRAZING:
            if self.state_timer > random.uniform(8, 15):  # Graze for 8-15 seconds
                self.state = AnimalState.MOVING
                self.state_timer = 0

        elif self.state == AnimalState.MOVING:
            if self.state_timer > random.uniform(3, 8):  # Move for 3-8 seconds
                if random.random() < 0.8:  # 80% chance to graze (love eating)
                    self.state = AnimalState.GRAZING
                else:
                    self.state = AnimalState.IDLE
                self.state_timer = 0

        elif self.state == AnimalState.IDLE:
            if self.state_timer > random.uniform(2, 5):  # Idle longer
                self.state = AnimalState.GRAZING
                self.state_timer = 0

    def get_render_char(self) -> str:
        """Get character to render based on state."""
        if get_animal_visual:
            visual_config = get_animal_visual("cow", self.state.value)
            if visual_config and visual_config.characters:
                return visual_config.characters[0]

        # Fallback to hardcoded values
        if self.state == AnimalState.GRAZING:
            return "c"  # Grazing cow (simple char for visibility)
        elif self.state == AnimalState.MOVING:
            return "C"  # Moving cow
        elif self.state == AnimalState.FLEEING:
            return "!"  # Panicked cow
        else:
            return "c"  # Idle cow

    def get_color(self) -> Tuple[int, int, int]:
        """Get cow color."""
        if get_animal_visual:
            visual_config = get_animal_visual("cow", self.state.value)
            if visual_config:
                return visual_config.foreground_color

        # Fallback to black
        return (0, 0, 0)


class Herd:
    """
    Manages a group of animals with flocking behavior.

    This class is generic and can manage any animal type, handling updates,
    spawning, and position tracking for groups of animals.
    """

    def __init__(self, animal_type: AnimalType, center_x: float, center_y: float, herd_size: int = 8):
        """
        Initialize a herd of animals.

        Args:
            animal_type: Type of animals in this herd
            center_x: Center X position for spawning
            center_y: Center Y position for spawning
            herd_size: Number of animals to spawn
        """
        self.animal_type = animal_type
        self.animals: List[Animal] = []
        self.last_update = time.time()

        # Create initial herd spread around center
        for i in range(herd_size):
            # Random position around center
            angle = random.uniform(0, 2 * math.pi)
            radius = random.uniform(1, 4)

            animal_x = center_x + math.cos(angle) * radius
            animal_y = center_y + math.sin(angle) * radius

            # Create animal based on type
            if animal_type == AnimalType.SHEEP:
                animal = Sheep(id=i, x=animal_x, y=animal_y)
            elif animal_type == AnimalType.COW:
                animal = Cow(id=i, x=animal_x, y=animal_y)
            else:
                raise ValueError(f"Unsupported animal type: {animal_type}")

            self.animals.append(animal)

    def update(self, terrain_data: Dict) -> None:
        """Update all animals in the herd."""
        current_time = time.time()
        delta_time = current_time - self.last_update
        self.last_update = current_time

        # Update each animal
        for animal in self.animals:
            # Find nearby animals for flocking calculations
            nearby_animals = []
            for other in self.animals:
                if other.id != animal.id:
                    distance = math.sqrt((animal.x - other.x)**2 + (animal.y - other.y)**2)
                    if distance < animal.cohesion_radius:  # Within flocking range
                        nearby_animals.append(other)

            animal.update(nearby_animals, terrain_data, delta_time)

    def get_animal_positions(self) -> List[Tuple[int, int, str, Tuple[int, int, int]]]:
        """Get positions and render data for all animals."""
        positions = []
        for animal in self.animals:
            positions.append((
                int(animal.x),
                int(animal.y),
                animal.get_render_char(),
                animal.get_color()
            ))
        return positions

    def add_animal(self, x: float, y: float) -> None:
        """Add a new animal to the herd."""
        new_id = max([a.id for a in self.animals]) + 1 if self.animals else 0

        if self.animal_type == AnimalType.SHEEP:
            new_animal = Sheep(id=new_id, x=x, y=y)
        elif self.animal_type == AnimalType.COW:
            new_animal = Cow(id=new_id, x=x, y=y)
        else:
            raise ValueError(f"Unsupported animal type: {self.animal_type}")

        self.animals.append(new_animal)

    def remove_animal(self, animal_id: int) -> None:
        """Remove an animal from the herd (for harvesting/predation)."""
        self.animals = [a for a in self.animals if a.id != animal_id]


class AnimalManager:
    """
    Manages all animals in the world.

    This class coordinates all herds across the world, handles spawning,
    updates, and provides rendering data to the main game system.
    Includes performance optimizations like spatial partitioning and culling.
    """

    def __init__(self):
        """Initialize the animal manager."""
        self.herds: Dict[str, Herd] = {}
        self.update_frequency = 0.1  # Update 10 times per second
        self.last_update = time.time()

        # Performance optimization settings
        self.spatial_grid_size = 8  # Size of spatial grid cells
        self.max_update_distance = 50  # Don't update animals beyond this distance from camera
        self.performance_stats = {
            'total_animals': 0,
            'updated_animals': 0,
            'culled_animals': 0,
            'spatial_queries': 0
        }

    def spawn_herd(
        self,
        animal_type: AnimalType,
        center_x: float,
        center_y: float,
        herd_id: str,
        size: int = 8
    ) -> None:
        """
        Spawn a new herd at location.

        Args:
            animal_type: Type of animals to spawn
            center_x: Center X position for spawning
            center_y: Center Y position for spawning
            herd_id: Unique identifier for this herd
            size: Number of animals in the herd
        """
        self.herds[herd_id] = Herd(animal_type, center_x, center_y, size)

    def update_animals(self, terrain_data: Dict, camera_x: int = 0, camera_y: int = 0) -> None:
        """
        Update all animals if enough time has passed, with performance optimizations.

        Args:
            terrain_data: Dictionary of terrain data for obstacle avoidance
            camera_x: Camera X position for culling distant animals
            camera_y: Camera Y position for culling distant animals
        """
        current_time = time.time()
        if current_time - self.last_update >= self.update_frequency:
            # Reset performance stats
            self.performance_stats['total_animals'] = 0
            self.performance_stats['updated_animals'] = 0
            self.performance_stats['culled_animals'] = 0
            self.performance_stats['spatial_queries'] = 0

            # Build spatial grid for efficient neighbor finding
            spatial_grid = self._build_spatial_grid()

            # Update each herd with optimizations
            for herd in self.herds.values():
                self._update_herd_optimized(herd, terrain_data, camera_x, camera_y, spatial_grid)

            self.last_update = current_time

    def _build_spatial_grid(self) -> Dict[Tuple[int, int], List[Animal]]:
        """
        Build a spatial grid for efficient neighbor finding.

        Returns:
            Dictionary mapping grid coordinates to lists of animals
        """
        spatial_grid = defaultdict(list)

        for herd in self.herds.values():
            for animal in herd.animals:
                # Calculate grid coordinates
                grid_x = int(animal.x // self.spatial_grid_size)
                grid_y = int(animal.y // self.spatial_grid_size)
                spatial_grid[(grid_x, grid_y)].append(animal)
                self.performance_stats['total_animals'] += 1

        return spatial_grid

    def _update_herd_optimized(
        self,
        herd: Herd,
        terrain_data: Dict,
        camera_x: int,
        camera_y: int,
        spatial_grid: Dict[Tuple[int, int], List[Animal]]
    ) -> None:
        """
        Update a herd with performance optimizations.

        Args:
            herd: The herd to update
            terrain_data: Terrain data for collision detection
            camera_x: Camera X position for culling
            camera_y: Camera Y position for culling
            spatial_grid: Spatial grid for efficient neighbor finding
        """
        current_time = time.time()
        delta_time = current_time - herd.last_update
        herd.last_update = current_time

        for animal in herd.animals:
            # Cull animals that are too far from camera
            distance_to_camera = math.sqrt(
                (animal.x - camera_x)**2 + (animal.y - camera_y)**2
            )

            if distance_to_camera > self.max_update_distance:
                self.performance_stats['culled_animals'] += 1
                continue

            # Find nearby animals using spatial grid
            nearby_animals = self._find_nearby_animals_spatial(animal, spatial_grid)
            self.performance_stats['spatial_queries'] += 1

            # Update the animal
            animal.update(nearby_animals, terrain_data, delta_time)
            self.performance_stats['updated_animals'] += 1

    def _find_nearby_animals_spatial(
        self,
        animal: Animal,
        spatial_grid: Dict[Tuple[int, int], List[Animal]]
    ) -> List[Animal]:
        """
        Find nearby animals using spatial grid for efficiency.

        Args:
            animal: The animal to find neighbors for
            spatial_grid: Spatial grid containing all animals

        Returns:
            List of nearby animals within flocking range
        """
        nearby_animals = []

        # Calculate which grid cells to check
        grid_x = int(animal.x // self.spatial_grid_size)
        grid_y = int(animal.y // self.spatial_grid_size)

        # Check surrounding grid cells (3x3 area)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                check_grid = (grid_x + dx, grid_y + dy)
                if check_grid in spatial_grid:
                    for other_animal in spatial_grid[check_grid]:
                        if other_animal.id != animal.id:
                            distance = math.sqrt(
                                (animal.x - other_animal.x)**2 +
                                (animal.y - other_animal.y)**2
                            )
                            if distance < animal.cohesion_radius:
                                nearby_animals.append(other_animal)

        return nearby_animals

    def get_all_animal_positions(self) -> List[Tuple[int, int, str, Tuple[int, int, int]]]:
        """
        Get render data for all animals.

        Returns:
            List of tuples (x, y, character, color) for rendering
        """
        all_positions = []
        for herd in self.herds.values():
            all_positions.extend(herd.get_animal_positions())
        return all_positions

    def get_animals_at_position(self, x: int, y: int) -> List[Animal]:
        """
        Get any animals at specific tile position.

        Args:
            x: World X coordinate
            y: World Y coordinate

        Returns:
            List of animals at the specified position
        """
        animals = []
        for herd in self.herds.values():
            for animal in herd.animals:
                if int(animal.x) == x and int(animal.y) == y:
                    animals.append(animal)
        return animals

    def remove_herd(self, herd_id: str) -> None:
        """Remove a herd from the world."""
        if herd_id in self.herds:
            del self.herds[herd_id]

    def get_herd_count(self) -> int:
        """Get the total number of herds."""
        return len(self.herds)

    def get_total_animal_count(self) -> int:
        """Get the total number of animals across all herds."""
        return sum(len(herd.animals) for herd in self.herds.values())

    def get_performance_stats(self) -> Dict[str, int]:
        """
        Get performance statistics for monitoring.

        Returns:
            Dictionary with performance metrics
        """
        return self.performance_stats.copy()

    def set_performance_settings(
        self,
        spatial_grid_size: Optional[int] = None,
        max_update_distance: Optional[int] = None
    ) -> None:
        """
        Adjust performance settings.

        Args:
            spatial_grid_size: Size of spatial grid cells for neighbor finding
            max_update_distance: Maximum distance from camera to update animals
        """
        if spatial_grid_size is not None:
            self.spatial_grid_size = spatial_grid_size
        if max_update_distance is not None:
            self.max_update_distance = max_update_distance
