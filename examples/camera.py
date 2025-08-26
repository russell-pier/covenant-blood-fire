# Unified Multi-Scale Camera and Viewport System
# Handles World (128x96) → Regional (32x32) → Local (32x32) scales seamlessly

import tcod
import math
import time
from enum import Enum
from dataclasses import dataclass
from typing import Tuple, Dict, List, Optional, Any

class ViewScale(Enum):
    WORLD = "world"        # 1 pixel = 1 world sector (16,384×16,384 tiles)
    REGIONAL = "regional"  # 1 pixel = 1 regional block (1,024×1,024 tiles)  
    LOCAL = "local"       # 1 pixel = 1 local tile (1×1 meter)

@dataclass
class ScaleConfig:
    """Configuration for each viewing scale"""
    name: str
    tiles_per_pixel: int     # How many world tiles per screen pixel
    map_dimensions: Tuple[int, int]  # Width×height of the map at this scale
    movement_speed: float    # Camera movement speed
    zoom_threshold: float    # How close to edge before auto-transitioning

@dataclass
class CameraPosition:
    """Camera position data for each scale"""
    x: float
    y: float
    target_x: float  # For smooth movement
    target_y: float
    bounds_min: Tuple[int, int]
    bounds_max: Tuple[int, int]

class TransitionState(Enum):
    NONE = "none"
    ZOOMING_IN = "zooming_in"
    ZOOMING_OUT = "zooming_out" 
    DRILLING_DOWN = "drilling_down"
    DRILLING_UP = "drilling_up"

@dataclass
class ViewTransition:
    """Manages smooth transitions between scales"""
    state: TransitionState
    progress: float  # 0.0 to 1.0
    duration: float  # Total transition time in seconds
    start_time: float
    from_scale: ViewScale
    to_scale: ViewScale
    from_position: Tuple[float, float]
    to_position: Tuple[float, float]

class UnifiedCameraSystem:
    """Unified camera system handling all three scales with smooth transitions"""
    
    def __init__(self, console_width: int = 80, console_height: int = 50):
        self.console_width = console_width
        self.console_height = console_height
        
        # Reserve space for UI
        self.ui_top_height = 3     # Status bar
        self.ui_bottom_height = 5  # Instructions
        self.ui_side_margin = 1
        
        # Calculate actual viewport size
        self.viewport_width = console_width - (2 * self.ui_side_margin)
        self.viewport_height = console_height - self.ui_top_height - self.ui_bottom_height
        self.viewport_start_x = self.ui_side_margin
        self.viewport_start_y = self.ui_top_height
        
        # Scale configurations
        self.scale_configs = {
            ViewScale.WORLD: ScaleConfig(
                "World", 16384, (128, 96), 1.0, 0.1
            ),
            ViewScale.REGIONAL: ScaleConfig(
                "Regional", 1024, (32, 32), 0.8, 0.15
            ),
            ViewScale.LOCAL: ScaleConfig(
                "Local", 1, (32, 32), 0.6, 0.2
            )
        }
        
        # Current state
        self.current_scale = ViewScale.LOCAL  # Start at most detailed level
        self.camera_positions = {}
        self.transition = ViewTransition(
            TransitionState.NONE, 0.0, 0.3, 0.0,
            ViewScale.LOCAL, ViewScale.LOCAL, (0, 0), (0, 0)
        )
        
        # Initialize camera positions for each scale
        self._initialize_camera_positions()
        
        # Movement smoothing
        self.movement_smoothing = 0.15
        self.last_movement_time = time.time()
        
        # Auto-transition settings
        self.auto_transition_enabled = True
        self.edge_trigger_distance = 3  # Tiles from edge to trigger transition
        
        # Visual effects
        self.show_scale_indicators = True
        self.show_transition_effects = True
        self.crosshair_enabled = True
    
    def _initialize_camera_positions(self):
        """Initialize camera positions for all scales"""
        for scale in ViewScale:
            config = self.scale_configs[scale]
            map_w, map_h = config.map_dimensions
            
            # Start at center of each map
            center_x = map_w / 2
            center_y = map_h / 2
            
            self.camera_positions[scale] = CameraPosition(
                x=center_x, y=center_y,
                target_x=center_x, target_y=center_y,
                bounds_min=(0, 0),
                bounds_max=(map_w - 1, map_h - 1)
            )
    
    def get_current_camera_position(self) -> CameraPosition:
        """Get camera position for current scale"""
        return self.camera_positions[self.current_scale]
    
    def get_current_scale_config(self) -> ScaleConfig:
        """Get configuration for current scale"""
        return self.scale_configs[self.current_scale]
    
    def move_camera(self, dx: int, dy: int):
        """Move camera in current scale with bounds checking"""
        if self.transition.state != TransitionState.NONE:
            return  # Don't allow movement during transitions
        
        camera = self.get_current_camera_position()
        config = self.get_current_scale_config()
        
        # Apply movement speed scaling
        actual_dx = dx * config.movement_speed
        actual_dy = dy * config.movement_speed
        
        # Update target position with bounds checking
        new_target_x = camera.target_x + actual_dx
        new_target_y = camera.target_y + actual_dy
        
        # Clamp to bounds
        new_target_x = max(camera.bounds_min[0], min(camera.bounds_max[0], new_target_x))
        new_target_y = max(camera.bounds_min[1], min(camera.bounds_max[1], new_target_y))
        
        camera.target_x = new_target_x
        camera.target_y = new_target_y
        
        # Check for auto-transitions at map edges
        if self.auto_transition_enabled:
            self._check_auto_transition(dx, dy)
        
        self.last_movement_time = time.time()
    
    def _check_auto_transition(self, movement_dx: int, movement_dy: int):
        """Check if we should auto-transition to different scale"""
        camera = self.get_current_camera_position()
        config = self.get_current_scale_config()
        
        # Calculate distance from edges
        dist_from_left = camera.x - camera.bounds_min[0]
        dist_from_right = camera.bounds_max[0] - camera.x
        dist_from_top = camera.y - camera.bounds_min[1]
        dist_from_bottom = camera.bounds_max[1] - camera.y
        
        edge_threshold = self.edge_trigger_distance
        
        # Moving toward edge and getting close?
        if (movement_dx < 0 and dist_from_left < edge_threshold) or \
           (movement_dx > 0 and dist_from_right < edge_threshold) or \
           (movement_dy < 0 and dist_from_top < edge_threshold) or \
           (movement_dy > 0 and dist_from_bottom < edge_threshold):
            
            # Try to zoom out to larger scale
            if self.current_scale == ViewScale.LOCAL:
                self.transition_to_scale(ViewScale.REGIONAL)
            elif self.current_scale == ViewScale.REGIONAL:
                self.transition_to_scale(ViewScale.WORLD)
    
    def transition_to_scale(self, new_scale: ViewScale):
        """Initiate smooth transition to different scale"""
        if (self.transition.state != TransitionState.NONE or 
            new_scale == self.current_scale):
            return
        
        current_camera = self.get_current_camera_position()
        
        # Calculate equivalent position in new scale
        new_position = self._calculate_equivalent_position(
            self.current_scale, new_scale, 
            current_camera.x, current_camera.y
        )
        
        # Set up transition
        self.transition = ViewTransition(
            state=TransitionState.DRILLING_DOWN if self._is_zooming_in(self.current_scale, new_scale) else TransitionState.DRILLING_UP,
            progress=0.0,
            duration=0.4,  # 400ms transition
            start_time=time.time(),
            from_scale=self.current_scale,
            to_scale=new_scale,
            from_position=(current_camera.x, current_camera.y),
            to_position=new_position
        )
    
    def _is_zooming_in(self, from_scale: ViewScale, to_scale: ViewScale) -> bool:
        """Check if transition is zooming in (to more detailed scale)"""
        scale_order = [ViewScale.WORLD, ViewScale.REGIONAL, ViewScale.LOCAL]
        return scale_order.index(to_scale) > scale_order.index(from_scale)
    
    def _calculate_equivalent_position(self, from_scale: ViewScale, to_scale: ViewScale, 
                                     from_x: float, from_y: float) -> Tuple[float, float]:
        """Calculate equivalent position when changing scales"""
        
        # Conversion ratios between scales
        if from_scale == ViewScale.WORLD and to_scale == ViewScale.REGIONAL:
            # Each world pixel represents a 4x3 area of regional map (128/32 = 4, 96/32 = 3)
            new_x = (from_x / 128) * 32
            new_y = (from_y / 96) * 32
        
        elif from_scale == ViewScale.REGIONAL and to_scale == ViewScale.LOCAL:
            # Direct 1:1 mapping - regional tile becomes local chunk center
            new_x = 16  # Center of 32x32 local chunk
            new_y = 16
        
        elif from_scale == ViewScale.LOCAL and to_scale == ViewScale.REGIONAL:
            # Local position becomes regional tile coordinate
            new_x = from_x / 32  # Approximate
            new_y = from_y / 32
        
        elif from_scale == ViewScale.REGIONAL and to_scale == ViewScale.WORLD:
            # Regional position maps back to world coordinates
            new_x = (from_x / 32) * 128
            new_y = (from_y / 32) * 96
        
        elif from_scale == ViewScale.WORLD and to_scale == ViewScale.LOCAL:
            # World directly to local (skip regional)
            new_x = 16  # Center of chunk
            new_y = 16
        
        elif from_scale == ViewScale.LOCAL and to_scale == ViewScale.WORLD:
            # Local directly to world
            new_x = 64  # Center of world map (128/2)
            new_y = 48  # Center of world map (96/2)
        
        else:
            # Fallback to center
            config = self.scale_configs[to_scale]
            new_x = config.map_dimensions[0] / 2
            new_y = config.map_dimensions[1] / 2
        
        return (new_x, new_y)
    
    def update(self, dt: float):
        """Update camera system (call every frame)"""
        # Update smooth camera movement
        self._update_smooth_movement(dt)
        
        # Update transitions
        self._update_transitions(dt)
    
    def _update_smooth_movement(self, dt: float):
        """Update smooth camera movement toward target"""
        camera = self.get_current_camera_position()
        
        # Smooth movement toward target
        diff_x = camera.target_x - camera.x
        diff_y = camera.target_y - camera.y
        
        # Use exponential smoothing
        smoothing_factor = 1.0 - math.exp(-dt / self.movement_smoothing)
        
        camera.x += diff_x * smoothing_factor
        camera.y += diff_y * smoothing_factor
    
    def _update_transitions(self, dt: float):
        """Update scale transition animations"""
        if self.transition.state == TransitionState.NONE:
            return
        
        # Update transition progress
        elapsed = time.time() - self.transition.start_time
        self.transition.progress = min(1.0, elapsed / self.transition.duration)
        
        # Transition complete?
        if self.transition.progress >= 1.0:
            self._complete_transition()
    
    def _complete_transition(self):
        """Complete the current transition"""
        # Switch to new scale
        self.current_scale = self.transition.to_scale
        
        # Set camera position
        camera = self.get_current_camera_position()
        camera.x = self.transition.to_position[0]
        camera.y = self.transition.to_position[1]
        camera.target_x = camera.x
        camera.target_y = camera.y
        
        # Clear transition
        self.transition.state = TransitionState.NONE
        self.transition.progress = 0.0
    
    def get_viewport_bounds(self) -> Tuple[int, int, int, int]:
        """Get current viewport bounds in map coordinates"""
        camera = self.get_current_camera_position()
        
        # Calculate viewport bounds
        half_width = self.viewport_width // 2
        half_height = self.viewport_height // 2
        
        min_x = int(camera.x - half_width)
        min_y = int(camera.y - half_height)
        max_x = min_x + self.viewport_width
        max_y = min_y + self.viewport_height
        
        return (min_x, min_y, max_x, max_y)
    
    def world_to_screen(self, world_x: int, world_y: int) -> Tuple[int, int]:
        """Convert world coordinates to screen coordinates"""
        camera = self.get_current_camera_position()
        
        # Offset by camera position
        screen_x = world_x - int(camera.x) + (self.viewport_width // 2)
        screen_y = world_y - int(camera.y) + (self.viewport_height // 2)
        
        # Add viewport offset
        screen_x += self.viewport_start_x
        screen_y += self.viewport_start_y
        
        return (screen_x, screen_y)
    
    def screen_to_world(self, screen_x: int, screen_y: int) -> Tuple[int, int]:
        """Convert screen coordinates to world coordinates"""
        camera = self.get_current_camera_position()
        
        # Remove viewport offset
        screen_x -= self.viewport_start_x
        screen_y -= self.viewport_start_y
        
        # Convert to world coordinates
        world_x = screen_x - (self.viewport_width // 2) + int(camera.x)
        world_y = screen_y - (self.viewport_height // 2) + int(camera.y)
        
        return (world_x, world_y)
    
    def is_in_viewport(self, world_x: int, world_y: int) -> bool:
        """Check if world coordinates are visible in current viewport"""
        min_x, min_y, max_x, max_y = self.get_viewport_bounds()
        return min_x <= world_x < max_x and min_y <= world_y < max_y

class UnifiedViewportRenderer:
    """Renders all three scales with appropriate detail and UI"""
    
    def __init__(self, camera_system: UnifiedCameraSystem):
        self.camera = camera_system
        self.show_debug_info = False
        self.show_grid = False
        self.show_coordinates = True
        
        # Cached data to avoid regenerating every frame
        self.cached_world_data = None
        self.cached_regional_data = {}
        self.cached_local_data = {}
        self.cache_invalidate_time = 0
        self.cache_lifetime = 1.0  # seconds
    
    def render_frame(self, console: tcod.console.Console, 
                    world_generator, regional_generator, local_generator):
        """Render complete frame with current scale and UI"""
        
        # Clear console
        console.clear()
        
        # Render based on current scale
        if self.camera.current_scale == ViewScale.WORLD:
            self._render_world_scale(console, world_generator)
        elif self.camera.current_scale == ViewScale.REGIONAL:
            self._render_regional_scale(console, regional_generator, world_generator)
        else:  # LOCAL
            self._render_local_scale(console, local_generator, regional_generator)
        
        # Render transition effects
        if self.camera.transition.state != TransitionState.NONE:
            self._render_transition_effects(console)
        
        # Render crosshair/cursor
        if self.camera.crosshair_enabled:
            self._render_crosshair(console)
        
        # Render UI elements
        self._render_ui(console)
        
        # Debug information
        if self.show_debug_info:
            self._render_debug_info(console)
    
    def _render_world_scale(self, console: tcod.console.Console, world_generator):
        """Render world scale view (128x96 world map)"""
        
        # Get or generate world data
        if not self.cached_world_data:
            self.cached_world_data = world_generator.generate_complete_world()
        
        camera_pos = self.camera.get_current_camera_position()
        viewport_bounds = self.camera.get_viewport_bounds()
        min_x, min_y, max_x, max_y = viewport_bounds
        
        # Render world tiles
        for world_y in range(max(0, min_y), min(96, max_y)):
            for world_x in range(max(0, min_x), min(128, max_x)):
                
                # Get screen coordinates
                screen_x, screen_y = self.camera.world_to_screen(world_x, world_y)
                
                # Check bounds
                if (screen_x < self.camera.viewport_start_x or 
                    screen_x >= self.camera.viewport_start_x + self.camera.viewport_width or
                    screen_y < self.camera.viewport_start_y or 
                    screen_y >= self.camera.viewport_start_y + self.camera.viewport_height):
                    continue
                
                # Get world tile data
                if 0 <= world_y < len(self.cached_world_data) and 0 <= world_x < len(self.cached_world_data[world_y]):
                    world_tile = self.cached_world_data[world_y][world_x]
                    char = world_tile.char
                    fg = world_tile.fg_color
                    bg = world_tile.bg_color
                else:
                    # Out of bounds
                    char, fg, bg = " ", (0, 0, 0), (0, 0, 0)
                
                console.print(screen_x, screen_y, char, fg=fg, bg=bg)
        
        # Add scale-specific decorations
        self._add_world_scale_decorations(console)
    
    def _render_regional_scale(self, console: tcod.console.Console, 
                             regional_generator, world_generator):
        """Render regional scale view (32x32 regional tiles)"""
        
        camera_pos = self.camera.get_current_camera_position()
        
        # Determine which world tile we're viewing regionally
        world_camera = self.camera.camera_positions[ViewScale.WORLD]
        world_tile_x = int(world_camera.x)
        world_tile_y = int(world_camera.y)
        
        # Get or generate regional data for this world tile
        cache_key = f"{world_tile_x}_{world_tile_y}"
        if cache_key not in self.cached_regional_data:
            # Generate regional map (this would use actual world tile data)
            self.cached_regional_data[cache_key] = self._generate_placeholder_regional_data()
        
        regional_data = self.cached_regional_data[cache_key]
        viewport_bounds = self.camera.get_viewport_bounds()
        min_x, min_y, max_x, max_y = viewport_bounds
        
        # Render regional tiles
        for reg_y in range(max(0, min_y), min(32, max_y)):
            for reg_x in range(max(0, min_x), min(32, max_x)):
                
                screen_x, screen_y = self.camera.world_to_screen(reg_x, reg_y)
                
                if (screen_x < self.camera.viewport_start_x or 
                    screen_x >= self.camera.viewport_start_x + self.camera.viewport_width or
                    screen_y < self.camera.viewport_start_y or 
                    screen_y >= self.camera.viewport_start_y + self.camera.viewport_height):
                    continue
                
                # Get regional tile data
                if 0 <= reg_y < len(regional_data) and 0 <= reg_x < len(regional_data[reg_y]):
                    regional_tile = regional_data[reg_y][reg_x]
                    char = regional_tile.char
                    fg = regional_tile.fg_color
                    bg = regional_tile.bg_color
                else:
                    char, fg, bg = "?", (255, 255, 255), (0, 0, 0)
                
                console.print(screen_x, screen_y, char, fg=fg, bg=bg)
        
        self._add_regional_scale_decorations(console)
    
    def _render_local_scale(self, console: tcod.console.Console, 
                          local_generator, regional_generator):
        """Render local scale view (32x32 meter tiles)"""
        
        camera_pos = self.camera.get_current_camera_position()
        
        # Determine which regional tile we're viewing locally
        regional_camera = self.camera.camera_positions[ViewScale.REGIONAL]
        regional_tile_x = int(regional_camera.x)
        regional_tile_y = int(regional_camera.y)
        
        # Get or generate local data
        cache_key = f"{regional_tile_x}_{regional_tile_y}"
        if cache_key not in self.cached_local_data:
            self.cached_local_data[cache_key] = self._generate_placeholder_local_data()
        
        local_data = self.cached_local_data[cache_key]
        viewport_bounds = self.camera.get_viewport_bounds()
        min_x, min_y, max_x, max_y = viewport_bounds
        
        # Render local tiles
        for local_y in range(max(0, min_y), min(32, max_y)):
            for local_x in range(max(0, min_x), min(32, max_x)):
                
                screen_x, screen_y = self.camera.world_to_screen(local_x, local_y)
                
                if (screen_x < self.camera.viewport_start_x or 
                    screen_x >= self.camera.viewport_start_x + self.camera.viewport_width or
                    screen_y < self.camera.viewport_start_y or 
                    screen_y >= self.camera.viewport_start_y + self.camera.viewport_height):
                    continue
                
                # Get local tile data
                if 0 <= local_y < len(local_data) and 0 <= local_x < len(local_data[local_y]):
                    local_tile = local_data[local_y][local_x]
                    char = local_tile.char
                    fg = local_tile.fg_color
                    bg = local_tile.bg_color
                else:
                    char, fg, bg = "?", (255, 255, 255), (0, 0, 0)
                
                console.print(screen_x, screen_y, char, fg=fg, bg=bg)
        
        self._add_local_scale_decorations(console)
    
    def _generate_placeholder_regional_data(self):
        """Generate placeholder regional data for demonstration"""
        # This would normally call the actual regional generator
        regional_map = []
        for y in range(32):
            row = []
            for x in range(32):
                # Create placeholder tile with variety
                if (x + y) % 7 == 0:
                    char, fg, bg = "♠", (0, 120, 0), (0, 80, 0)  # Trees
                elif (x * y) % 11 == 0:
                    char, fg, bg = "^", (128, 128, 128), (80, 80, 80)  # Rocks
                elif x % 15 == 0 or y % 15 == 0:
                    char, fg, bg = "~", (100, 150, 255), (50, 100, 200)  # Water
                else:
                    char, fg, bg = ".", (50, 150, 50), (20, 100, 20)  # Grass
                
                tile = type('RegionalTile', (), {
                    'char': char, 'fg_color': fg, 'bg_color': bg
                })()
                row.append(tile)
            regional_map.append(row)
        return regional_map
    
    def _generate_placeholder_local_data(self):
        """Generate placeholder local data for demonstration"""
        # This would normally call the actual local generator
        local_map = []
        for y in range(32):
            row = []
            for x in range(32):
                # Create detailed placeholder with sub-terrain variety
                if (x + y) % 5 == 0:
                    char, fg, bg = "*", (255, 215, 0), (50, 150, 50)  # Flowers
                elif (x * 2 + y) % 8 == 0:
                    char, fg, bg = "○", (139, 69, 19), (101, 67, 33)  # Stones
                elif x == 16 or y == 16:  # Cross pattern
                    char, fg, bg = "≈", (100, 150, 255), (50, 100, 200)  # Stream
                else:
                    # Grass with slight variations
                    grass_chars = [".", "'", ",", "`"]
                    char = grass_chars[(x + y) % len(grass_chars)]
                    fg = (40 + (x % 20), 140 + (y % 20), 40 + ((x+y) % 15))
                    bg = (15 + (x % 10), 90 + (y % 15), 15 + ((x+y) % 8))
                
                tile = type('LocalTile', (), {
                    'char': char, 'fg_color': fg, 'bg_color': bg
                })()
                row.append(tile)
            local_map.append(row)
        return local_map
    
    def _add_world_scale_decorations(self, console: tcod.console.Console):
        """Add world-scale specific visual decorations"""
        # Add continent labels, major geographic features, etc.
        pass
    
    def _add_regional_scale_decorations(self, console: tcod.console.Console):
        """Add regional-scale specific visual decorations"""
        # Add terrain type indicators, landmarks, etc.
        pass
    
    def _add_local_scale_decorations(self, console: tcod.console.Console):
        """Add local-scale specific visual decorations"""
        # Add resource indicators, elevation contours, etc.
        pass
    
    def _render_transition_effects(self, console: tcod.console.Console):
        """Render smooth transition effects between scales"""
        transition = self.camera.transition
        
        if transition.state == TransitionState.NONE:
            return
        
        # Create zoom/fade effect
        progress = transition.progress
        
        # Fade overlay
        fade_alpha = int(50 * math.sin(progress * math.pi))  # Peak at middle
        if fade_alpha > 0:
            # Create subtle fade effect around viewport edges
            for edge_y in range(self.camera.viewport_start_y, 
                              self.camera.viewport_start_y + self.camera.viewport_height):
                for edge_x in range(self.camera.viewport_start_x, 
                                  self.camera.viewport_start_x + self.camera.viewport_width):
                    
                    # Distance from center
                    center_x = self.camera.viewport_start_x + self.camera.viewport_width // 2
                    center_y = self.camera.viewport_start_y + self.camera.viewport_height // 2
                    
                    distance = math.sqrt((edge_x - center_x)**2 + (edge_y - center_y)**2)
                    max_distance = math.sqrt((self.camera.viewport_width/2)**2 + (self.camera.viewport_height/2)**2)
                    
                    # Fade more at edges
                    edge_factor = distance / max_distance
                    if edge_factor > 0.7:  # Only affect outer 30%
                        fade_strength = int(fade_alpha * (edge_factor - 0.7) / 0.3)
                        
                        # Darken existing background
                        existing_bg = console.bg[edge_y, edge_x]
                        new_bg = tuple(max(0, c - fade_strength) for c in existing_bg)
                        console.print(edge_x, edge_y, " ", bg=new_bg)
        
        # Transition direction indicator
        if transition.state in [TransitionState.DRILLING_DOWN, TransitionState.DRILLING_UP]:
            center_x = self.camera.viewport_start_x + self.camera.viewport_width // 2
            center_y = self.camera.viewport_start_y + self.camera.viewport_height // 2
            
            if transition.state == TransitionState.DRILLING_DOWN:
                indicator = "↓" if progress < 0.5 else "↓↓"
                color = (255, 255, 0)
            else:
                indicator = "↑" if progress < 0.5 else "↑↑"
                color = (0, 255, 255)
            
            console.print(center_x, center_y, indicator, fg=color)
    
    def _render_crosshair(self, console: tcod.console.Console):
        """Render crosshair/cursor at camera center"""
        center_x = self.camera.viewport_start_x + self.camera.viewport_width // 2
        center_y = self.camera.viewport_start_y + self.camera.viewport_height // 2
        
        # Different crosshair styles for different scales
        if self.camera.current_scale == ViewScale.WORLD:
            console.print(center_x, center_y, "+", fg=(255, 255, 0), bg=(0, 0, 0))
        elif self.camera.current_scale == ViewScale.REGIONAL:
            console.print(center_x, center_y, "⊕", fg=(255, 128, 0), bg=(0, 0, 0))
        else:  # LOCAL
            console.print(center_x, center_y, "●", fg=(255, 0, 0), bg=(0, 0, 0))
    
    def _render_ui(self, console: tcod.console.Console):
        """Render UI elements (status bar, instructions, etc.)"""
        
        # Top status bar
        self._render_status_bar(console)
        
        # Bottom instructions
        self._render_instructions(console)
        
        # Side panels (if needed)
        if self.camera.current_scale == ViewScale.LOCAL:
            self._render_local_info_panel(console)
    
    def _render_status_bar(self, console: tcod.console.Console):
        """Render top status bar with current scale and position info"""
        camera = self.camera.get_current_camera_position()
        config = self.camera.get_current_scale_config()
        
        # Background bar
        for x in range(self.camera.console_width):
            for y in range(self.camera.ui_top_height):
                console.print(x, y, " ", bg=(60, 60, 60))
        
        # Scale indicator
        scale_text = f"Scale: {config.name}"
        console.print(2, 1, scale_text, fg=(255, 255, 255), bg=(60, 60, 60))
        
        # Position indicator
        if self.camera.show_coordinates:
            pos_text = f"Position: ({camera.x:.1f}, {camera.y:.1f})"
            console.print(25, 1, pos_text, fg=(200, 200, 200), bg=(60, 60, 60))
        
        # Transition indicator
        if self.camera.transition.state != TransitionState.NONE:
            trans_text = f"Transitioning to {self.camera.transition.to_scale.value}..."
            console.print(2, 2, trans_text, fg=(255, 255, 0), bg=(60, 60, 60))
        
        # Scale availability
        available_scales = "Available: 1=World 2=Regional 3=Local"
        console.print(self.camera.console_width - len(available_scales) - 2, 1, 
                     available_scales, fg=(150, 150, 150), bg=(60, 60, 60))
    
    def _render_instructions(self, console: tcod.console.Console):
        """Render bottom instruction panel"""
        start_y = self.camera.console_height - self.camera.ui_bottom_height
        
        # Background
        for x in range(self.camera.console_width):
            for y in range(start_y, self.camera.console_height):
                console.print(x, y, " ", bg=(40, 40, 40))
        
        # Instructions based on current scale
        if self.camera.current_scale == ViewScale.WORLD:
            instructions = [
                "WORLD VIEW - Continental Overview",
                "WASD/Arrows: Move camera  |  2: Zoom to Regional  |  3: Zoom to Local",
                "Enter: Drill down to Regional view  |  Tab: Toggle auto-transitions"
            ]
        elif self.camera.current_scale == ViewScale.REGIONAL:
            instructions = [
                "REGIONAL VIEW - Terrain Detail", 
                "WASD/Arrows: Move camera  |  1: Zoom to World  |  3: Zoom to Local",
                "Enter: Drill down to Local view  |  Backspace: Up to World"
            ]
        else:  # LOCAL
            instructions = [
                "LOCAL VIEW - Meter-Level Detail",
                "WASD/Arrows: Move camera  |  1: World  |  2: Regional  |  Space: Interact",
                "Enter: Use/Harvest  |  Tab: Z-levels  |  I: Inventory  |  M: Map"
            ]
        
        for i, instruction in enumerate(instructions):
            console.print(2, start_y + 1 + i, instruction, 
                         fg=(200, 200, 200), bg=(40, 40, 40))
    
    def _render_local_info_panel(self, console: tcod.console.Console):
        """Render additional info panel for local view"""
        # This could show tile details, resources, etc.
        pass
    
    def _render_debug_info(self, console: tcod.console.Console):
        """Render debug information overlay"""
        debug_y = 5
        
        debug_info = [
            f"Viewport: {self.camera.viewport_width}x{self.camera.viewport_height}",
            f"Bounds: {self.camera.get_viewport_bounds()}",
            f"Transition: {self.camera.transition.state.value} ({self.camera.transition.progress:.2f})",
            f"Auto-transition: {self.camera.auto_transition_enabled}"
        ]
        
        for i, info in enumerate(debug_info):
            console.print(2, debug_y + i, info, fg=(255, 255, 0), bg=(0, 0, 0))

# Input handler for the unified camera system
class CameraInputHandler:
    """Handles input for the unified camera system"""
    
    def __init__(self, camera_system: UnifiedCameraSystem):
        self.camera = camera_system
        self.key_repeat_delay = 0.15  # Seconds between repeats
        self.last_key_time = {}
    
    def handle_keydown(self, event: tcod.event.KeyDown) -> bool:
        """Handle keyboard input for camera control"""
        current_time = time.time()
        key = event.sym
        
        # Check for key repeat limiting
        if key in self.last_key_time:
            if current_time - self.last_key_time[key] < self.key_repeat_delay:
                return False  # Skip this key press
        
        self.last_key_time[key] = current_time
        
        # Movement keys
        dx, dy = 0, 0
        if key in [tcod.event.KeySym.w, tcod.event.KeySym.UP]:
            dy = -1
        elif key in [tcod.event.KeySym.s, tcod.event.KeySym.DOWN]:
            dy = 1
        elif key in [tcod.event.KeySym.a, tcod.event.KeySym.LEFT]:
            dx = -1
        elif key in [tcod.event.KeySym.d, tcod.event.KeySym.RIGHT]:
            dx = 1
        
        if dx != 0 or dy != 0:
            self.camera.move_camera(dx, dy)
            return True
        
        # Scale switching
        if key == tcod.event.KeySym.N1:
            self.camera.transition_to_scale(ViewScale.WORLD)
            return True
        elif key == tcod.event.KeySym.N2:
            self.camera.transition_to_scale(ViewScale.REGIONAL)
            return True
        elif key == tcod.event.KeySym.N3:
            self.camera.transition_to_scale(ViewScale.LOCAL)
            return True
        
        # Drilling transitions
        if key == tcod.event.KeySym.RETURN:
            self._handle_drill_down()
            return True
        elif key == tcod.event.KeySym.BACKSPACE:
            self._handle_drill_up()
            return True
        
        # Toggle features
        if key == tcod.event.KeySym.TAB:
            self.camera.auto_transition_enabled = not self.camera.auto_transition_enabled
            return True
        
        return False
    
    def _handle_drill_down(self):
        """Handle drilling down to more detailed scale"""
        if self.camera.current_scale == ViewScale.WORLD:
            self.camera.transition_to_scale(ViewScale.REGIONAL)
        elif self.camera.current_scale == ViewScale.REGIONAL:
            self.camera.transition_to_scale(ViewScale.LOCAL)
    
    def _handle_drill_up(self):
        """Handle drilling up to less detailed scale"""
        if self.camera.current_scale == ViewScale.LOCAL:
            self.camera.transition_to_scale(ViewScale.REGIONAL)
        elif self.camera.current_scale == ViewScale.REGIONAL:
            self.camera.transition_to_scale(ViewScale.WORLD)

# Example usage and integration
if __name__ == "__main__":
    # Example of how to integrate the unified camera system
    
    class ExampleGame:
        def __init__(self):
            self.console_width = 80
            self.console_height = 50
            
            # Initialize camera and viewport
            self.camera_system = UnifiedCameraSystem(self.console_width, self.console_height)
            self.viewport = UnifiedViewportRenderer(self.camera_system)
            self.input_handler = CameraInputHandler(self.camera_system)
            
            # Initialize generators (placeholders)
            self.world_generator = None
            self.regional_generator = None
            self.local_generator = None
        
        def handle_events(self, events):
            for event in events:
                if event.type == "KEYDOWN":
                    if self.input_handler.handle_keydown(event):
                        continue  # Camera handled it
                    
                    # Handle other game events
                    if event.sym == tcod.event.KeySym.ESCAPE:
                        return False  # Quit game
        
        def update(self, dt: float):
            # Update camera system
            self.camera_system.update(dt)
            
            # Update other game systems
            pass
        
        def render(self, console: tcod.console.Console):
            # Render complete frame
            self.viewport.render_frame(
                console, 
                self.world_generator,
                self.regional_generator, 
                self.local_generator
            )
    
    print("Unified Camera/Viewport System Features:")
    print("• Seamless transitions between World (128×96) → Regional (32×32) → Local (32×32) scales")
    print("• Smooth camera movement with bounds checking at each scale")
    print("• Automatic scale transitions when approaching map edges")
    print("• Visual transition effects and scale-appropriate crosshairs")  
    print("• Comprehensive UI showing current scale, position, and controls")
    print("• Input handling for movement, scale switching, and drilling up/down")
    print("• Coordinate system conversion between scales and screen positions")
    print("• Cached data management to avoid regenerating maps every frame")
    print("• Debug information and customizable visual options")
    print("\nKey bindings:")
    print("• WASD/Arrows: Move camera")
    print("• 1/2/3: Jump to World/Regional/Local scale")
    print("• Enter: Drill down to more detailed scale")
    print("• Backspace: Drill up to less detailed scale") 
    print("• Tab: Toggle auto-transitions at map edges")