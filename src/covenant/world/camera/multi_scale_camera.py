"""
Multi-scale camera system for three-tier world generation.

This module manages camera movement and positioning across the three
viewing scales: World, Regional, and Local.
"""

import time
from typing import Tuple, Optional

from ..data.scale_types import ViewScale, ScaleConfig, get_scale_config


class MultiScaleCameraSystem:
    """Manages camera across three viewing scales."""
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the multi-scale camera system.
        
        Args:
            seed: Seed for any random camera behavior (currently unused)
        """
        self.current_scale = ViewScale.LOCAL  # Start at detailed view
        
        # Scale configurations
        self.scale_configs = {
            ViewScale.WORLD: get_scale_config(ViewScale.WORLD),
            ViewScale.REGIONAL: get_scale_config(ViewScale.REGIONAL), 
            ViewScale.LOCAL: get_scale_config(ViewScale.LOCAL)
        }
        
        # Independent camera positions for each scale (in scale units)
        self.world_camera_x = 8      # Center of 16×16 world
        self.world_camera_y = 8
        self.regional_camera_x = 16  # Center of 32×32 region
        self.regional_camera_y = 16
        self.local_camera_x = 16     # Center of 32×32 local area
        self.local_camera_y = 16
        
        # Movement tracking
        self.last_movement_time = time.time()
        self.movement_velocity = 0.0
        self.total_distance_moved = 0.0
        
        # Scale transition tracking
        self.last_scale_change_time = time.time()
        self.scale_change_count = 0
    
    def get_current_scale(self) -> ViewScale:
        """
        Get current viewing scale.
        
        Returns:
            Current ViewScale
        """
        return self.current_scale
    
    def change_scale(self, new_scale: ViewScale) -> bool:
        """
        Switch to different viewing scale.
        
        Args:
            new_scale: Scale to switch to
            
        Returns:
            True if scale was changed, False if already at that scale
        """
        if new_scale != self.current_scale:
            old_scale = self.current_scale
            self.current_scale = new_scale
            self.last_scale_change_time = time.time()
            self.scale_change_count += 1
            
            print(f"Camera scale changed: {old_scale.value} → {new_scale.value}")
            return True
        
        return False
    
    def get_camera_position(self) -> Tuple[int, int]:
        """
        Get camera position for current scale.
        
        Returns:
            Tuple of (x, y) coordinates in current scale units
        """
        if self.current_scale == ViewScale.WORLD:
            return self.world_camera_x, self.world_camera_y
        elif self.current_scale == ViewScale.REGIONAL:
            return self.regional_camera_x, self.regional_camera_y
        else:  # LOCAL
            return self.local_camera_x, self.local_camera_y
    
    def set_camera_position(self, x: int, y: int) -> None:
        """
        Set camera position for current scale.
        
        Args:
            x: X coordinate in current scale units
            y: Y coordinate in current scale units
        """
        config = self.scale_configs[self.current_scale]
        max_x, max_y = config.map_size
        
        # Clamp to bounds
        x = max(0, min(max_x - 1, x))
        y = max(0, min(max_y - 1, y))
        
        if self.current_scale == ViewScale.WORLD:
            self.world_camera_x, self.world_camera_y = x, y
        elif self.current_scale == ViewScale.REGIONAL:
            self.regional_camera_x, self.regional_camera_y = x, y
        else:  # LOCAL
            self.local_camera_x, self.local_camera_y = x, y
    
    def move_camera(self, dx: int, dy: int) -> bool:
        """
        Move camera within current scale bounds.
        
        Args:
            dx: Change in X coordinate
            dy: Change in Y coordinate
            
        Returns:
            True if camera moved, False if movement was blocked
        """
        current_time = time.time()
        
        # Get current position
        current_x, current_y = self.get_camera_position()
        
        # Calculate new position
        new_x = current_x + dx
        new_y = current_y + dy
        
        # Check bounds
        config = self.scale_configs[self.current_scale]
        max_x, max_y = config.map_size
        
        # Clamp to bounds
        clamped_x = max(0, min(max_x - 1, new_x))
        clamped_y = max(0, min(max_y - 1, new_y))
        
        # Check if movement was blocked
        movement_blocked = (clamped_x != new_x or clamped_y != new_y)
        
        # Update position
        old_x, old_y = current_x, current_y
        self.set_camera_position(clamped_x, clamped_y)
        
        # Calculate actual movement for velocity tracking
        actual_dx = clamped_x - old_x
        actual_dy = clamped_y - old_y
        
        if actual_dx != 0 or actual_dy != 0:
            # Update movement tracking
            time_delta = current_time - self.last_movement_time
            if time_delta > 0:
                distance = (actual_dx * actual_dx + actual_dy * actual_dy) ** 0.5
                self.movement_velocity = distance / time_delta
                self.total_distance_moved += distance
            
            self.last_movement_time = current_time
        
        return not movement_blocked
    
    def get_camera_bounds(self) -> Tuple[int, int, int, int]:
        """
        Get camera movement bounds for current scale.
        
        Returns:
            Tuple of (min_x, min_y, max_x, max_y)
        """
        config = self.scale_configs[self.current_scale]
        max_x, max_y = config.map_size
        return 0, 0, max_x - 1, max_y - 1
    
    def convert_position_to_world_coordinates(self, scale: ViewScale, 
                                            camera_x: int, camera_y: int) -> Tuple[int, int]:
        """
        Convert scale position to world tile coordinates.
        
        Args:
            scale: The viewing scale
            camera_x: X coordinate in scale units
            camera_y: Y coordinate in scale units
            
        Returns:
            Tuple of (world_x, world_y) in tile coordinates
        """
        config = self.scale_configs[scale]
        
        world_x = camera_x * config.pixels_per_unit
        world_y = camera_y * config.pixels_per_unit
        
        return world_x, world_y
    
    def get_current_world_coordinates(self) -> Tuple[int, int]:
        """
        Get current camera position in world tile coordinates.
        
        Returns:
            Tuple of (world_x, world_y) in tile coordinates
        """
        camera_x, camera_y = self.get_camera_position()
        return self.convert_position_to_world_coordinates(
            self.current_scale, camera_x, camera_y
        )
    
    def center_camera_on_world_coordinates(self, world_x: int, world_y: int) -> None:
        """
        Center camera on specific world coordinates for current scale.
        
        Args:
            world_x: World X coordinate in tiles
            world_y: World Y coordinate in tiles
        """
        config = self.scale_configs[self.current_scale]
        
        # Convert world coordinates to scale coordinates
        scale_x = world_x // config.pixels_per_unit
        scale_y = world_y // config.pixels_per_unit
        
        self.set_camera_position(scale_x, scale_y)
    
    def get_movement_stats(self) -> dict:
        """
        Get movement statistics for debugging/analytics.
        
        Returns:
            Dictionary with movement statistics
        """
        return {
            "current_scale": self.current_scale.value,
            "current_position": self.get_camera_position(),
            "world_coordinates": self.get_current_world_coordinates(),
            "movement_velocity": self.movement_velocity,
            "total_distance_moved": self.total_distance_moved,
            "scale_changes": self.scale_change_count,
            "time_since_last_movement": time.time() - self.last_movement_time,
            "time_since_last_scale_change": time.time() - self.last_scale_change_time
        }
    
    def reset_position(self, scale: Optional[ViewScale] = None) -> None:
        """
        Reset camera to center position for specified or current scale.
        
        Args:
            scale: Scale to reset (None for current scale)
        """
        if scale is None:
            scale = self.current_scale
        
        config = self.scale_configs[scale]
        center_x = config.map_size[0] // 2
        center_y = config.map_size[1] // 2
        
        if scale == ViewScale.WORLD:
            self.world_camera_x, self.world_camera_y = center_x, center_y
        elif scale == ViewScale.REGIONAL:
            self.regional_camera_x, self.regional_camera_y = center_x, center_y
        else:  # LOCAL
            self.local_camera_x, self.local_camera_y = center_x, center_y
        
        print(f"Camera reset to center for {scale.value} scale: ({center_x}, {center_y})")
    
    def reset_all_positions(self) -> None:
        """Reset all camera positions to their respective centers."""
        for scale in ViewScale:
            self.reset_position(scale)
