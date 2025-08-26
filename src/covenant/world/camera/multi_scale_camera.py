"""
Multi-Scale Camera System for the 3-tiered world generation system.

This module provides a unified camera system that handles smooth transitions
between World, Regional, and Local scales with proper coordinate mapping.
Based on examples/camera.py but integrated with the new architecture.
"""

import time
import math
from enum import Enum
from dataclasses import dataclass
from typing import Tuple, Dict, List, Optional, Any

from ..data.scale_types import ViewScale, CoordinateSystem, ScaleTransition


class TransitionState(Enum):
    """Camera transition states"""
    NONE = "none"
    ZOOMING_IN = "zooming_in"
    ZOOMING_OUT = "zooming_out"
    DRILLING_DOWN = "drilling_down"
    DRILLING_UP = "drilling_up"


@dataclass
class CameraPosition:
    """Camera position data for each scale"""
    x: float
    y: float
    target_x: float  # For smooth movement
    target_y: float
    bounds_min: Tuple[int, int]
    bounds_max: Tuple[int, int]


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


@dataclass
class ViewportInfo:
    """Information about the current viewport"""
    scale: ViewScale
    camera_x: float
    camera_y: float
    viewport_width: int
    viewport_height: int
    viewport_start_x: int
    viewport_start_y: int
    tiles_visible: List[List[Any]]  # The actual tile data to display


class MultiScaleCameraSystem:
    """Unified camera system handling all three scales with smooth transitions"""

    def __init__(self, console_width: int = 80, console_height: int = 50, seed: Optional[int] = None):
        self.console_width = console_width
        self.console_height = console_height
        self.seed = seed  # Store seed for compatibility (currently unused)

        # Reserve space for UI (preserve existing UI layout)
        self.ui_top_height = 3     # Status bar
        self.ui_bottom_height = 5  # Instructions
        self.ui_side_margin = 1

        # Calculate actual viewport size
        self.viewport_width = console_width - (2 * self.ui_side_margin)
        self.viewport_height = console_height - self.ui_top_height - self.ui_bottom_height
        self.viewport_start_x = self.ui_side_margin
        self.viewport_start_y = self.ui_top_height

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

        # Context for coordinate mapping
        self.current_world_sector = (64, 48)  # Center of world map
        self.current_regional_block = (16, 16)  # Center of regional map
    
    def _initialize_camera_positions(self):
        """Initialize camera positions for all scales"""
        # World scale: 128×96 sectors
        world_bounds = CoordinateSystem.WORLD_SIZE
        self.camera_positions[ViewScale.WORLD] = CameraPosition(
            x=world_bounds[0] / 2, y=world_bounds[1] / 2,
            target_x=world_bounds[0] / 2, target_y=world_bounds[1] / 2,
            bounds_min=(0, 0),
            bounds_max=(world_bounds[0] - 1, world_bounds[1] - 1)
        )

        # Regional scale: 32×32 blocks per sector
        regional_bounds = CoordinateSystem.REGIONAL_SIZE
        self.camera_positions[ViewScale.REGIONAL] = CameraPosition(
            x=regional_bounds[0] / 2, y=regional_bounds[1] / 2,
            target_x=regional_bounds[0] / 2, target_y=regional_bounds[1] / 2,
            bounds_min=(0, 0),
            bounds_max=(regional_bounds[0] - 1, regional_bounds[1] - 1)
        )

        # Local scale: 32×32 meters per block
        local_bounds = CoordinateSystem.LOCAL_SIZE
        self.camera_positions[ViewScale.LOCAL] = CameraPosition(
            x=local_bounds[0] / 2, y=local_bounds[1] / 2,
            target_x=local_bounds[0] / 2, target_y=local_bounds[1] / 2,
            bounds_min=(0, 0),
            bounds_max=(local_bounds[0] - 1, local_bounds[1] - 1)
        )

    def get_current_camera_position(self) -> CameraPosition:
        """Get camera position for current scale"""
        return self.camera_positions[self.current_scale]

    def get_current_scale_config(self):
        """Get configuration for current scale"""
        from ..data.scale_types import get_scale_config
        return get_scale_config(self.current_scale)

    def get_current_scale(self) -> ViewScale:
        """Get current viewing scale"""
        return self.current_scale
    
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

        # Update target camera position for new scale
        new_camera = self.camera_positions[new_scale]
        new_camera.target_x = new_position[0]
        new_camera.target_y = new_position[1]

        # Set up transition
        transition_duration = ScaleTransition.get_transition_duration(self.current_scale, new_scale)

        self.transition = ViewTransition(
            state=TransitionState.ZOOMING_OUT if self._is_zooming_out(self.current_scale, new_scale) else TransitionState.ZOOMING_IN,
            progress=0.0,
            duration=transition_duration,
            start_time=time.time(),
            from_scale=self.current_scale,
            to_scale=new_scale,
            from_position=(current_camera.x, current_camera.y),
            to_position=new_position
        )
    
    def _is_zooming_out(self, from_scale: ViewScale, to_scale: ViewScale) -> bool:
        """Check if transition is zooming out (to larger scale)"""
        scale_order = [ViewScale.LOCAL, ViewScale.REGIONAL, ViewScale.WORLD]
        return scale_order.index(to_scale) > scale_order.index(from_scale)

    def _calculate_equivalent_position(self, from_scale: ViewScale, to_scale: ViewScale,
                                     from_x: float, from_y: float) -> Tuple[float, float]:
        """Calculate equivalent position when transitioning between scales"""
        if from_scale == to_scale:
            return from_x, from_y

        # Use the coordinate system to convert between scales
        # This is a simplified version - in practice you'd need full context
        if from_scale == ViewScale.LOCAL and to_scale == ViewScale.REGIONAL:
            # Convert local position to regional position within current block
            return from_x / CoordinateSystem.LOCAL_SIZE[0], from_y / CoordinateSystem.LOCAL_SIZE[1]

        elif from_scale == ViewScale.REGIONAL and to_scale == ViewScale.WORLD:
            # Convert regional position to world position within current sector
            return from_x / CoordinateSystem.REGIONAL_SIZE[0], from_y / CoordinateSystem.REGIONAL_SIZE[1]

        elif from_scale == ViewScale.WORLD and to_scale == ViewScale.REGIONAL:
            # Convert world position to regional position
            return from_x * CoordinateSystem.REGIONAL_SIZE[0], from_y * CoordinateSystem.REGIONAL_SIZE[1]

        elif from_scale == ViewScale.REGIONAL and to_scale == ViewScale.LOCAL:
            # Convert regional position to local position
            return from_x * CoordinateSystem.LOCAL_SIZE[0], from_y * CoordinateSystem.LOCAL_SIZE[1]

        # For direct world-local transitions, go through regional
        elif from_scale == ViewScale.WORLD and to_scale == ViewScale.LOCAL:
            regional_pos = self._calculate_equivalent_position(from_scale, ViewScale.REGIONAL, from_x, from_y)
            return self._calculate_equivalent_position(ViewScale.REGIONAL, to_scale, regional_pos[0], regional_pos[1])

        elif from_scale == ViewScale.LOCAL and to_scale == ViewScale.WORLD:
            regional_pos = self._calculate_equivalent_position(from_scale, ViewScale.REGIONAL, from_x, from_y)
            return self._calculate_equivalent_position(ViewScale.REGIONAL, to_scale, regional_pos[0], regional_pos[1])

        return from_x, from_y  # Fallback
    
    def update(self, dt: float):
        """Update camera system (smooth movement, transitions)"""
        # Update smooth camera movement
        self._update_smooth_movement(dt)

        # Update transitions
        self._update_transitions(dt)

    def _update_smooth_movement(self, dt: float):
        """Update smooth camera movement toward target"""
        for scale, camera in self.camera_positions.items():
            # Smooth interpolation toward target
            dx = camera.target_x - camera.x
            dy = camera.target_y - camera.y

            # Apply smoothing
            smoothing_factor = 1.0 - math.exp(-self.movement_smoothing * dt * 60)  # 60 FPS reference

            camera.x += dx * smoothing_factor
            camera.y += dy * smoothing_factor

    def _update_transitions(self, dt: float):
        """Update scale transitions"""
        if self.transition.state == TransitionState.NONE:
            return

        # Update transition progress
        elapsed = time.time() - self.transition.start_time
        self.transition.progress = min(1.0, elapsed / self.transition.duration)

        # Check if transition is complete
        if self.transition.progress >= 1.0:
            # Complete the transition
            self.current_scale = self.transition.to_scale
            self.transition.state = TransitionState.NONE

            # Snap camera to final position
            final_camera = self.camera_positions[self.current_scale]
            final_camera.x = self.transition.to_position[0]
            final_camera.y = self.transition.to_position[1]
    
    def get_viewport_info(self) -> ViewportInfo:
        """Get current viewport information for rendering"""
        camera = self.get_current_camera_position()

        return ViewportInfo(
            scale=self.current_scale,
            camera_x=camera.x,
            camera_y=camera.y,
            viewport_width=self.viewport_width,
            viewport_height=self.viewport_height,
            viewport_start_x=self.viewport_start_x,
            viewport_start_y=self.viewport_start_y,
            tiles_visible=[]  # Will be populated by renderer
        )

    def set_world_context(self, world_x: int, world_y: int):
        """Set current world sector context for coordinate mapping"""
        self.current_world_sector = (world_x, world_y)

    def set_regional_context(self, block_x: int, block_y: int):
        """Set current regional block context for coordinate mapping"""
        self.current_regional_block = (block_x, block_y)

    def zoom_in(self):
        """Manually zoom in to more detailed scale"""
        if self.current_scale == ViewScale.WORLD:
            self.transition_to_scale(ViewScale.REGIONAL)
        elif self.current_scale == ViewScale.REGIONAL:
            self.transition_to_scale(ViewScale.LOCAL)

    def zoom_out(self):
        """Manually zoom out to less detailed scale"""
        if self.current_scale == ViewScale.LOCAL:
            self.transition_to_scale(ViewScale.REGIONAL)
        elif self.current_scale == ViewScale.REGIONAL:
            self.transition_to_scale(ViewScale.WORLD)

    def is_transitioning(self) -> bool:
        """Check if camera is currently transitioning between scales"""
        return self.transition.state != TransitionState.NONE

    def get_transition_progress(self) -> float:
        """Get current transition progress (0.0 to 1.0)"""
        return self.transition.progress if self.is_transitioning() else 0.0
    
    # Legacy compatibility methods
    def get_camera_position(self) -> Tuple[float, float]:
        """Get camera position for current scale (legacy compatibility)"""
        camera = self.get_current_camera_position()
        return camera.x, camera.y

    def change_scale(self, new_scale: ViewScale) -> bool:
        """Change to different scale (legacy compatibility)"""
        if new_scale != self.current_scale:
            self.transition_to_scale(new_scale)
            return True
        return False
