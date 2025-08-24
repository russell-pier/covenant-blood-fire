# Migration Plan: Three-Tier World Generation System

## Overview

This document outlines the migration from the current single-scale world system to a three-tier hierarchical world generation system with multi-scale camera views. The new system will provide:

- **World View**: 16×16 sectors showing continental features
- **Regional View**: 32×32 blocks showing regional terrain 
- **Local View**: 32×32 chunks showing detailed terrain (current system)

## Phase 1: Core Infrastructure Setup

### 1.1 New Directory Structure

Create the new hierarchical generation system alongside existing code:

```
src/covenant/world/
├── generators/
│   ├── __init__.py
│   ├── world_scale.py          # NEW: Pipeline 1 - Continental features
│   ├── regional_scale.py       # NEW: Pipeline 2 - Regional terrain  
│   ├── local_scale.py          # NEW: Pipeline 3 - Local chunks
│   └── base_generator.py       # NEW: Shared noise/utility functions
├── camera/
│   ├── __init__.py
│   ├── multi_scale_camera.py   # NEW: Three-tier camera system
│   └── viewport_renderer.py    # NEW: Scale-aware rendering
├── data/
│   ├── __init__.py
│   ├── world_data.py           # NEW: World sector data structures
│   ├── regional_data.py        # NEW: Regional block data structures
│   └── scale_types.py          # NEW: Enums and shared types
└── legacy/                     # TEMPORARY: Move existing files here
    ├── generator.py            # Current WorldGenerator
    ├── layered_generator.py    # Current 3D layer system
    └── environmental.py        # Current environmental system
```

### 1.2 Scale Type Definitions

**File**: `src/covenant/world/data/scale_types.py`

```python
from enum import Enum
from dataclasses import dataclass
from typing import Tuple

class ViewScale(Enum):
    """Three viewing scales."""
    WORLD = "world"      # 1 pixel = 1 sector (16,384×16,384 tiles)
    REGIONAL = "regional" # 1 pixel = 1 block (1,024×1,024 tiles)  
    LOCAL = "local"      # 1 pixel = 1 chunk (32×32 tiles)

class WorldLayer(Enum):
    """3D world layers (keep existing)."""
    UNDERGROUND = 0
    SURFACE = 1  
    MOUNTAINS = 2

@dataclass
class ScaleConfig:
    """Configuration for each viewing scale."""
    name: str
    pixels_per_unit: int     # How many tiles per pixel
    map_size: Tuple[int, int]  # Width×height in units
    cache_lifetime: float    # Seconds to cache data
```

### 1.3 World Scale Data Structures

**File**: `src/covenant/world/data/world_data.py`

```python
from dataclasses import dataclass
from typing import Tuple, Optional

@dataclass
class WorldSectorData:
    """Continental-scale data for world map display."""
    sector_x: int
    sector_y: int
    
    # Geographic features (simplified for world view)
    dominant_terrain: str  # "ocean", "continent", "mountains", "desert"
    average_elevation: float
    climate_zone: str  # "tropical", "temperate", "polar"
    
    # Visual representation
    display_char: str
    display_color: Tuple[int, int, int]
    display_bg_color: Tuple[int, int, int]
    
    # Continental features
    has_major_mountain_range: bool
    has_major_river_system: bool
    continental_plate_id: int
    
    # Metadata
    generation_time: float  # When this was generated
    parent_seed: int       # World seed used

@dataclass
class WorldMapData:
    """Complete world map data."""
    world_seed: int
    world_size_sectors: Tuple[int, int]  # Default: (16, 16)
    sectors: Dict[Tuple[int, int], WorldSectorData]
    generation_complete: bool = False
```

## Phase 2: World Scale Generator Implementation

### 2.1 Base Noise System

**File**: `src/covenant/world/generators/base_generator.py`

```python
import math
from typing import Dict, Tuple

class HierarchicalNoiseGenerator:
    """Noise system that works consistently across all scales."""
    
    def __init__(self, seed: int):
        self.seed = seed
        # Different noise layers for different world features
        self.continental_noise_seed = seed
        self.tectonic_noise_seed = seed + 1000
        self.climate_noise_seed = seed + 2000
        
    def continental_noise(self, world_x: float, world_y: float) -> float:
        """Very low frequency noise for continental shapes."""
        return self._noise(
            world_x * 0.00001 + self.continental_noise_seed,
            world_y * 0.00001
        )
    
    def tectonic_noise(self, world_x: float, world_y: float) -> float:
        """Low frequency noise for mountain ranges.""" 
        return self._noise(
            world_x * 0.0001 + self.tectonic_noise_seed,
            world_y * 0.0001
        )
    
    def climate_noise(self, world_x: float, world_y: float) -> float:
        """Medium frequency noise for climate variation."""
        return self._noise(
            world_x * 0.001 + self.climate_noise_seed,
            world_y * 0.001
        )
    
    def _noise(self, x: float, y: float) -> float:
        """Core noise function."""
        return math.sin(x * 12.9898 + y * 78.233) * 43758.5453 % 1.0 * 2 - 1
    
    def octave_noise(self, x: float, y: float, octaves: int = 3, 
                     base_seed: int = 0) -> float:
        """Multi-octave noise for complex patterns."""
        value = 0
        amplitude = 1
        frequency = 1
        max_value = 0
        
        for i in range(octaves):
            noise_val = self._noise(x * frequency + base_seed + i * 1000, 
                                   y * frequency)
            value += noise_val * amplitude
            max_value += amplitude
            amplitude *= 0.5
            frequency *= 2
        
        return value / max_value
```

### 2.2 World Scale Generator

**File**: `src/covenant/world/generators/world_scale.py`

```python
from typing import Dict, Tuple
from ..data.world_data import WorldSectorData, WorldMapData
from ..data.scale_types import ViewScale
from .base_generator import HierarchicalNoiseGenerator

class WorldScaleGenerator:
    """Generates continental-scale world features."""
    
    def __init__(self, seed: int):
        self.seed = seed
        self.noise = HierarchicalNoiseGenerator(seed)
        
        # World configuration
        self.world_size_sectors = (16, 16)  # 16×16 world map
        self.sector_size_tiles = 16384      # Each sector = 16,384×16,384 tiles
        
        # Generation cache
        self.world_map_data: Optional[WorldMapData] = None
    
    def generate_complete_world_map(self) -> WorldMapData:
        """Generate entire 16×16 world map."""
        if self.world_map_data and self.world_map_data.generation_complete:
            return self.world_map_data
        
        sectors = {}
        
        # Generate all sectors
        for sector_y in range(self.world_size_sectors[1]):
            for sector_x in range(self.world_size_sectors[0]):
                sectors[(sector_x, sector_y)] = self.generate_world_sector(
                    sector_x, sector_y
                )
        
        self.world_map_data = WorldMapData(
            world_seed=self.seed,
            world_size_sectors=self.world_size_sectors,
            sectors=sectors,
            generation_complete=True
        )
        
        return self.world_map_data
    
    def generate_world_sector(self, sector_x: int, sector_y: int) -> WorldSectorData:
        """Generate single world sector using deterministic noise."""
        
        # Calculate world coordinates for sector center
        center_world_x = sector_x * self.sector_size_tiles + (self.sector_size_tiles // 2)
        center_world_y = sector_y * self.sector_size_tiles + (self.sector_size_tiles // 2)
        
        # Sample continental features
        continental = self.noise.continental_noise(center_world_x, center_world_y)
        tectonic = self.noise.tectonic_noise(center_world_x, center_world_y)
        climate_var = self.noise.climate_noise(center_world_x, center_world_y)
        
        # Determine base elevation
        base_elevation = continental * 2000  # ±2000m base
        tectonic_elevation = abs(tectonic) * 1500  # 0-1500m from tectonics
        total_elevation = base_elevation + tectonic_elevation
        
        # Classify terrain
        if total_elevation < -500:
            terrain_type = "deep_ocean"
            char, fg, bg = "~", (0, 100, 200), (0, 50, 100)
        elif total_elevation < 0:
            terrain_type = "shallow_ocean"  
            char, fg, bg = "≈", (50, 150, 255), (25, 75, 150)
        elif total_elevation > 2500:
            terrain_type = "high_mountains"
            char, fg, bg = "▲", (200, 180, 160), (120, 100, 80)
        elif total_elevation > 1000:
            terrain_type = "mountains"
            char, fg, bg = "^", (160, 140, 120), (100, 80, 60)
        else:
            # Land classification based on climate
            # Simplified latitude: distance from world center
            latitude_factor = abs(center_world_y) / (self.world_size_sectors[1] * self.sector_size_tiles // 2)
            
            if latitude_factor > 0.8:  # Polar
                terrain_type = "tundra"
                char, fg, bg = "∘", (200, 200, 255), (150, 150, 200)
            elif latitude_factor < 0.3 and climate_var > 0:  # Tropical
                terrain_type = "tropical"
                char, fg, bg = "♠", (0, 150, 0), (0, 80, 0) 
            elif climate_var < -0.3:  # Dry
                terrain_type = "desert"
                char, fg, bg = "·", (218, 165, 32), (184, 134, 11)
            else:  # Temperate
                terrain_type = "temperate_land"
                char, fg, bg = ".", (100, 180, 100), (50, 120, 50)
        
        # Determine major features
        has_mountains = abs(tectonic) > 0.6  # High tectonic activity
        has_rivers = 200 < total_elevation < 1500 and continental > -0.3  # Good river conditions
        plate_id = int((sector_x // 4) * 4 + (sector_y // 4)) % 8  # 8 major plates
        
        # Climate zone
        if latitude_factor > 0.7:
            climate_zone = "polar"
        elif latitude_factor < 0.3:
            climate_zone = "tropical" 
        else:
            climate_zone = "temperate"
        
        return WorldSectorData(
            sector_x=sector_x,
            sector_y=sector_y,
            dominant_terrain=terrain_type,
            average_elevation=total_elevation,
            climate_zone=climate_zone,
            display_char=char,
            display_color=fg,
            display_bg_color=bg,
            has_major_mountain_range=has_mountains,
            has_major_river_system=has_rivers,
            continental_plate_id=plate_id,
            generation_time=time.time(),
            parent_seed=self.seed
        )
```

## Phase 3: Multi-Scale Camera System

### 3.1 Multi-Scale Camera

**File**: `src/covenant/world/camera/multi_scale_camera.py`

```python
from typing import Tuple
from ..data.scale_types import ViewScale, ScaleConfig
from ..data.world_data import WorldMapData
import time

class MultiScaleCameraSystem:
    """Manages camera across three viewing scales."""
    
    def __init__(self, seed: int):
        self.current_scale = ViewScale.LOCAL  # Start at detailed view
        
        # Scale configurations
        self.scale_configs = {
            ViewScale.WORLD: ScaleConfig("World", 16384, (16, 16), 300.0),
            ViewScale.REGIONAL: ScaleConfig("Regional", 1024, (32, 32), 60.0), 
            ViewScale.LOCAL: ScaleConfig("Local", 32, (32, 32), 10.0)
        }
        
        # Independent camera positions for each scale
        self.world_camera_x = 8      # Center of 16×16 world
        self.world_camera_y = 8
        self.regional_camera_x = 16  # Center of 32×32 region
        self.regional_camera_y = 16
        self.local_camera_x = 16     # Center of 32×32 local area
        self.local_camera_y = 16
        
        # Last position update times
        self.last_movement_time = time.time()
        self.movement_velocity = 0.0
        
    def get_current_scale(self) -> ViewScale:
        """Get current viewing scale."""
        return self.current_scale
    
    def change_scale(self, new_scale: ViewScale):
        """Switch to different viewing scale."""
        if new_scale != self.current_scale:
            self.current_scale = new_scale
            self.last_movement_time = time.time()
    
    def get_camera_position(self) -> Tuple[int, int]:
        """Get camera position for current scale."""
        if self.current_scale == ViewScale.WORLD:
            return self.world_camera_x, self.world_camera_y
        elif self.current_scale == ViewScale.REGIONAL:
            return self.regional_camera_x, self.regional_camera_y
        else:  # LOCAL
            return self.local_camera_x, self.local_camera_y
    
    def move_camera(self, dx: int, dy: int):
        """Move camera within current scale bounds."""
        current_time = time.time()
        
        # Calculate movement velocity for potential auto-scaling
        time_delta = current_time - self.last_movement_time
        if time_delta > 0:
            distance = (dx*dx + dy*dy) ** 0.5
            self.movement_velocity = distance / time_delta
        
        if self.current_scale == ViewScale.WORLD:
            self.world_camera_x = max(0, min(15, self.world_camera_x + dx))
            self.world_camera_y = max(0, min(15, self.world_camera_y + dy))
            
        elif self.current_scale == ViewScale.REGIONAL:
            self.regional_camera_x = max(0, min(31, self.regional_camera_x + dx))
            self.regional_camera_y = max(0, min(31, self.regional_camera_y + dy))
            
        else:  # LOCAL
            # Local movement uses existing camera system movement speed
            self.local_camera_x = max(0, min(31, self.local_camera_x + dx))
            self.local_camera_y = max(0, min(31, self.local_camera_y + dy))
        
        self.last_movement_time = current_time
    
    def convert_position_to_world_coordinates(self, scale: ViewScale, 
                                            camera_x: int, camera_y: int) -> Tuple[int, int]:
        """Convert scale position to world tile coordinates."""
        config = self.scale_configs[scale]
        
        world_x = camera_x * config.pixels_per_unit
        world_y = camera_y * config.pixels_per_unit
        
        return world_x, world_y
    
    def get_current_world_coordinates(self) -> Tuple[int, int]:
        """Get current camera position in world tile coordinates."""
        camera_x, camera_y = self.get_camera_position()
        return self.convert_position_to_world_coordinates(
            self.current_scale, camera_x, camera_y
        )
```

### 3.2 Scale-Aware Viewport Renderer

**File**: `src/covenant/world/camera/viewport_renderer.py`

```python
import tcod
from typing import Tuple, Optional
from ..generators.world_scale import WorldScaleGenerator
from .multi_scale_camera import MultiScaleCameraSystem
from ..data.scale_types import ViewScale

class MultiScaleViewportRenderer:
    """Renders world at different scales with consistent UI."""
    
    def __init__(self, world_generator: WorldScaleGenerator, 
                 camera_system: MultiScaleCameraSystem):
        self.world_generator = world_generator
        self.camera_system = camera_system
        
        # Console dimensions (maintain existing layout)
        self.console_width = 80
        self.console_height = 50
        
        # UI space reservations (keep existing floating bar layout)
        self.status_bar_height = 3
        self.instructions_height = 5
        self.ui_margin = 1
        
        # Available rendering area
        self.render_start_y = self.status_bar_height + self.ui_margin
        self.render_end_y = self.console_height - self.instructions_height - self.ui_margin
        self.render_height = self.render_end_y - self.render_start_y
        self.render_width = self.console_width
    
    def render_current_scale(self, console: tcod.console.Console):
        """Render world at current camera scale."""
        
        current_scale = self.camera_system.get_current_scale()
        camera_x, camera_y = self.camera_system.get_camera_position()
        
        if current_scale == ViewScale.WORLD:
            self._render_world_view(console, camera_x, camera_y)
        elif current_scale == ViewScale.REGIONAL:
            self._render_regional_view(console, camera_x, camera_y)
        else:  # LOCAL
            self._render_local_view(console, camera_x, camera_y)
        
        # Always render scale indicator
        self._render_scale_ui(console)
    
    def _render_world_view(self, console: tcod.console.Console, 
                          camera_x: int, camera_y: int):
        """Render 16×16 world sector view."""
        
        world_map = self.world_generator.generate_complete_world_map()
        
        # Calculate rendering offset to center the world map
        world_width, world_height = world_map.world_size_sectors
        start_x = (self.render_width - world_width) // 2
        start_y = self.render_start_y + (self.render_height - world_height) // 2
        
        # Render world sectors
        for (sector_x, sector_y), sector_data in world_map.sectors.items():
            render_x = start_x + sector_x
            render_y = start_y + sector_y
            
            if (0 <= render_x < self.console_width and 
                0 <= render_y < self.console_height):
                
                console.print(
                    render_x, render_y,
                    sector_data.display_char,
                    fg=sector_data.display_color,
                    bg=sector_data.display_bg_color
                )
        
        # Render camera crosshair
        crosshair_x = start_x + camera_x
        crosshair_y = start_y + camera_y
        
        if (0 <= crosshair_x < self.console_width and 
            0 <= crosshair_y < self.console_height):
            console.print(crosshair_x, crosshair_y, "+", 
                         fg=(255, 255, 0), bg=(0, 0, 0))
    
    def _render_regional_view(self, console: tcod.console.Console,
                             camera_x: int, camera_y: int):
        """Render 32×32 regional block view."""
        
        # TODO: Implement in Phase 4
        # For now, show placeholder
        self._render_placeholder(console, "REGIONAL VIEW", "32×32 Blocks")
        
        # Render camera crosshair at center
        crosshair_x = self.render_width // 2
        crosshair_y = self.render_start_y + self.render_height // 2
        console.print(crosshair_x, crosshair_y, "+", 
                     fg=(255, 255, 0), bg=(0, 0, 0))
    
    def _render_local_view(self, console: tcod.console.Console,
                          camera_x: int, camera_y: int):
        """Render 32×32 local chunk view."""
        
        # TODO: Integrate with existing detailed rendering system
        # For now, show placeholder
        self._render_placeholder(console, "LOCAL VIEW", "32×32 Chunks")
        
        # Render camera crosshair at center
        crosshair_x = self.render_width // 2
        crosshair_y = self.render_start_y + self.render_height // 2
        console.print(crosshair_x, crosshair_y, "+", 
                     fg=(255, 255, 0), bg=(0, 0, 0))
    
    def _render_placeholder(self, console: tcod.console.Console, 
                           title: str, subtitle: str):
        """Render placeholder content for unimplemented views."""
        
        # Clear rendering area
        for y in range(self.render_start_y, self.render_end_y):
            for x in range(self.render_width):
                console.print(x, y, " ", fg=(0, 0, 0), bg=(40, 40, 40))
        
        # Center text
        center_x = self.render_width // 2
        center_y = self.render_start_y + self.render_height // 2
        
        # Title
        title_x = center_x - len(title) // 2
        console.print(title_x, center_y - 1, title, fg=(255, 255, 255))
        
        # Subtitle
        subtitle_x = center_x - len(subtitle) // 2
        console.print(subtitle_x, center_y + 1, subtitle, fg=(150, 150, 150))
    
    def _render_scale_ui(self, console: tcod.console.Console):
        """Render scale indicator and controls."""
        
        current_scale = self.camera_system.get_current_scale()
        camera_x, camera_y = self.camera_system.get_camera_position()
        
        # Scale indicator (top-right of rendering area)
        scale_text = f"Scale: {current_scale.value.title()}"
        position_text = f"Pos: {camera_x},{camera_y}"
        
        console.print(self.console_width - 25, self.render_start_y, 
                     scale_text, fg=(255, 255, 0))
        console.print(self.console_width - 25, self.render_start_y + 1, 
                     position_text, fg=(200, 200, 200))
        
        # Controls reminder (bottom-right of rendering area)
        controls_y = self.render_end_y - 3
        console.print(self.console_width - 30, controls_y,
                     "1=World 2=Region 3=Local", fg=(150, 150, 150))
```

## Phase 4: Integration with Existing System

### 4.1 Modified Main Game Class

**File**: `src/covenant/main.py` (modifications)

```python
# Add these imports
from .world.generators.world_scale import WorldScaleGenerator
from .world.camera.multi_scale_camera import MultiScaleCameraSystem
from .world.camera.viewport_renderer import MultiScaleViewportRenderer

class Game:
    def __init__(self):
        # ... existing initialization ...
        
        # NEW: Multi-scale world generation
        self.world_scale_generator = WorldScaleGenerator(seed=12345)
        self.multi_scale_camera = MultiScaleCameraSystem(seed=12345)
        self.multi_scale_renderer = MultiScaleViewportRenderer(
            self.world_scale_generator, 
            self.multi_scale_camera
        )
        
        # Keep existing systems for Local scale integration
        self.world_generator = WorldGenerator(seed=12345)  # Existing
        self.camera = Camera(40, 25)  # Existing
        self.viewport = Viewport(self.camera)  # Existing
        
        # UI systems remain the same
        self.status_bar = StatusBar()
        self.instructions_panel = InstructionsPanel()
        
    def render(self):
        """Modified render pipeline."""
        self.console.clear()
        
        current_scale = self.multi_scale_camera.get_current_scale()
        
        if current_scale == ViewScale.LOCAL:
            # Use existing detailed rendering system
            self._render_detailed_local_view()
        else:
            # Use new multi-scale rendering
            self.multi_scale_renderer.render_current_scale(self.console)
        
        # Always render UI (maintains existing layout)
        if current_scale == ViewScale.LOCAL:
            # Full UI for detailed view
            cursor_pos = self.camera.get_position()
            self.status_bar.render(self.console, self.world_generator, cursor_pos)
            self.instructions_panel.render(self.console)
        else:
            # Simplified UI for world/regional views
            self._render_scale_navigation_ui()
    
    def _render_detailed_local_view(self):
        """Existing detailed rendering pipeline."""
        self.viewport.render_world(self.console, self.world_generator)
        self.viewport.render_crosshair(self.console, self.world_generator)
        # Animals, resources, etc. (existing systems)
    
    def _render_scale_navigation_ui(self):
        """UI for world/regional scales."""
        # Render floating status bar with scale info
        scale = self.multi_scale_camera.get_current_scale()
        camera_x, camera_y = self.multi_scale_camera.get_camera_position()
        
        # Top status bar
        status_text = f"Scale: {scale.value.title()} | Position: {camera_x},{camera_y}"
        self.console.print(2, 2, status_text, fg=(255, 255, 255), bg=(60, 60, 60))
        
        # Bottom instructions
        instructions = "1=World  2=Regional  3=Local  |  WASD=Move  Enter=Drill Down"
        self.console.print(2, 47, instructions, fg=(200, 200, 200), bg=(60, 60, 60))
    
    def handle_keydown(self, event):
        """Modified input handling."""
        
        # Scale switching (always available)
        if event.sym == tcod.event.KeySym.N1:
            self.multi_scale_camera.change_scale(ViewScale.WORLD)
            return
        elif event.sym == tcod.event.KeySym.N2:
            self.multi_scale_camera.change_scale(ViewScale.REGIONAL)
            return
        elif event.sym == tcod.event.KeySym.N3:
            self.multi_scale_camera.change_scale(ViewScale.LOCAL)
            return
        
        current_scale = self.multi_scale_camera.get_current_scale()
        
        # Movement
        dx, dy = 0, 0
        if event.sym in [tcod.event.KeySym.w, tcod.event.KeySym.UP]:
            dy = -1
        elif event.sym in [tcod.event.KeySym.s, tcod.event.KeySym.DOWN]:
            dy = 1
        elif event.sym in [tcod.event.KeySym.a, tcod.event.KeySym.LEFT]:
            dx = -1
        elif event.sym in [tcod.event.KeySym.d, tcod.event.KeySym.RIGHT]:
            dx = 1
        
        if dx != 0 or dy != 0:
            if current_scale == ViewScale.LOCAL:
                # Use existing camera system for detailed view
                self.camera.move(dx, dy)
            else:
                # Use multi-scale camera for world/regional
                self.multi_scale_camera.move_camera(dx, dy)
            return
        
        # Drill down functionality
        if event.sym == tcod.event.KeySym.RETURN:
            if current_scale == ViewScale.WORLD:
                self.multi_scale_camera.change_scale(ViewScale.REGIONAL)
            elif current_scale == ViewScale.REGIONAL:
                self.multi_scale_camera.change_scale(ViewScale.LOCAL)
            return
        
        # Existing controls (only in LOCAL scale)
        if current_scale == ViewScale.LOCAL:
            # Layer switching, command palette, etc.
            # ... existing input handling ...
            pass
```

## Phase 5: Testing and Validation

### 5.1 Basic Functionality Tests

Create test files to validate each component:

**File**: `tests/test_world_scale.py`

```python
def test_world_generation():
    generator = WorldScaleGenerator(seed=12345)
    world_map = generator.generate_complete_world_map()
    
    assert world_map.world_size_sectors == (16, 16)
    assert len(world_map.sectors) == 256  # 16×16
    assert world_map.generation_complete
    
    # Test deterministic generation
    world_map_2 = generator.generate_complete_world_map()
    assert world_map.sectors == world_map_2.sectors

def test_camera_system():
    camera = MultiScaleCameraSystem(seed=12345)
    
    # Test scale switching
    assert camera.get_current_scale() == ViewScale.LOCAL
    camera.change_scale(ViewScale.WORLD)
    assert camera.get_current_scale() == ViewScale.WORLD
    
    # Test movement bounds
    camera.move_camera(-10, -10)  # Should clamp to bounds
    x, y = camera.get_camera_position()
    assert x >= 0 and y >= 0
```

### 5.2 Integration Testing

1. **Launch game and verify World view renders**
2. **Test scale switching with 1/2/3 keys**
3. **Verify UI layout preservation**
4. **Test camera movement in each scale**
5. **Validate same seed produces same world**

## Phase 6: Deployment Strategy

### 6.1 Rollback Plan

Keep existing system in `legacy/` directory:
- If issues arise, can quickly revert to legacy system
- Gradual migration of features
- Preserve existing save compatibility

### 6.2 Feature Flags

Add configuration to control new system:

```python
# config.py
USE_MULTI_SCALE_WORLD = True  # Set to False to use legacy system
ENABLE_WORLD_VIEW = True
ENABLE_REGIONAL_VIEW = True
```

### 6.3 Performance Monitoring

- Monitor frame rates in each scale
- Track memory usage of world data caching  
- Measure world generation times
- Profile camera switching performance

## Success Criteria

**Phase 1 Complete When:**
- ✅ World view (16×16) renders continental features
- ✅ Camera system switches between scales smoothly
- ✅ UI layout remains consistent with existing design
- ✅ Basic navigation works in all scales

**Ready for Phase 2 (Regional Scale) When:**
- ✅ World generation is stable and deterministic
- ✅ No performance regressions in Local scale
- ✅ Input handling works correctly across scales
- ✅ UI provides clear feedback about current scale

This migration plan provides a structured approach to implementing the three-tier world generation system while preserving existing functionality and UI design.