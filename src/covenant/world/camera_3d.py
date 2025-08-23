"""
3D Camera System for managing layer transitions and rendering.

This module provides the camera system that handles movement between the three
world layers (underground, surface, mountains) with appropriate visual effects
and transition validation.
"""

from typing import Tuple

from .layered import WorldLayer, LayeredTerrainData, TerrainData, create_terrain_data
from .terrain import TerrainType


class CameraSystem:
    """Handles 3D camera movement between layers with visual effects."""
    
    def __init__(self):
        """Initialize the 3D camera system."""
        self.current_layer = WorldLayer.SURFACE
        self.world_x = 0
        self.world_y = 0
        
        # View transition settings
        self.transition_speed = 0.3
        self.is_transitioning = False
        
    def can_change_layer(self, target_layer: WorldLayer, terrain_data: LayeredTerrainData = None) -> bool:
        """
        Check if player can move to target layer from current position.

        Args:
            target_layer: The layer to transition to
            terrain_data: Layered terrain data at current position (optional, not used for free switching)

        Returns:
            True if transition is possible (always True for free layer switching)
        """
        # Allow free layer switching - player controls the camera/viewport, not a character
        return True
    
    def change_layer(self, new_layer: WorldLayer) -> bool:
        """
        Move camera to different vertical layer.
        
        Args:
            new_layer: The layer to transition to
            
        Returns:
            True if layer was changed, False if already on that layer
        """
        if new_layer != self.current_layer:
            self.current_layer = new_layer
            self.is_transitioning = True
            return True
        return False
    
    def get_render_data(self, terrain_data: LayeredTerrainData) -> TerrainData:
        """
        Get terrain data for current camera layer with proper shading.
        
        Args:
            terrain_data: Layered terrain data at the position
            
        Returns:
            TerrainData for rendering based on current layer
        """
        if self.current_layer == WorldLayer.SURFACE:
            return self._apply_surface_shading(terrain_data)
        elif self.current_layer == WorldLayer.UNDERGROUND:
            return self._apply_underground_shading(terrain_data)
        elif self.current_layer == WorldLayer.MOUNTAINS:
            return self._apply_mountain_shading(terrain_data)
        
        # Fallback to surface
        return terrain_data.surface
    
    def _apply_surface_shading(self, terrain_data: LayeredTerrainData) -> TerrainData:
        """
        Render surface layer with subtle hints about other layers.

        Args:
            terrain_data: Layered terrain data

        Returns:
            TerrainData for surface layer rendering
        """
        base_terrain = terrain_data.surface

        # If there's a mountain cliff above, show it as an impassable cliff wall in surface layer
        if terrain_data.mountains and terrain_data.mountains.terrain_type == TerrainType.MOUNTAIN_CLIFF:
            # Render mountain cliff as a solid wall similar to cave walls
            return TerrainData(
                terrain_type=TerrainType.MOUNTAIN_CLIFF,
                char="█",  # Solid block like cave walls
                fg_color=(80, 60, 40),    # Dark cliff colors
                bg_color=(40, 30, 20),    # Very dark background
                elevation=terrain_data.mountains.elevation,
                is_passable=False,  # Impassable from surface layer
                is_entrance=False
            )

        # If there's a mountain above, add subtle shading hint
        if terrain_data.mountains:
            # Slight mountain shadow effect (less pronounced than before)
            darkened_fg = tuple(int(c * 0.9) for c in base_terrain.fg_color)
            darkened_bg = tuple(int(c * 0.9) for c in base_terrain.bg_color)

            return TerrainData(
                terrain_type=base_terrain.terrain_type,
                char=base_terrain.char,
                fg_color=darkened_fg,
                bg_color=darkened_bg,
                elevation=base_terrain.elevation,
                is_passable=base_terrain.is_passable,
                is_entrance=False
            )

        # Show subtle cave hints with slightly darker background
        if terrain_data.has_cave_entrance:
            darkened_bg = tuple(int(c * 0.8) for c in base_terrain.bg_color)

            return TerrainData(
                terrain_type=base_terrain.terrain_type,
                char=base_terrain.char,
                fg_color=base_terrain.fg_color,
                bg_color=darkened_bg,
                elevation=base_terrain.elevation,
                is_passable=base_terrain.is_passable,
                is_entrance=False
            )

        return base_terrain
    
    def _apply_underground_shading(self, terrain_data: LayeredTerrainData) -> TerrainData:
        """
        Render underground layer with enhanced darkness for solid areas.

        Args:
            terrain_data: Layered terrain data

        Returns:
            TerrainData for underground layer rendering
        """
        underground_terrain = terrain_data.underground

        # Make cave walls even darker for better contrast
        if underground_terrain.terrain_type == TerrainType.CAVE_WALL:
            return TerrainData(
                terrain_type=TerrainType.CAVE_WALL,
                char="█",  # Solid block
                fg_color=(8, 8, 8),    # Almost black
                bg_color=(2, 2, 2),    # Nearly black background
                elevation=underground_terrain.elevation,
                is_passable=False
            )

        # Return normal underground terrain for caves
        return underground_terrain
    
    def _apply_mountain_shading(self, terrain_data: LayeredTerrainData) -> TerrainData:
        """
        Render mountain layer with much lighter surface view below (elevation perspective).
        Mountain cliffs become normal passable terrain in the mountain layer.

        Args:
            terrain_data: Layered terrain data

        Returns:
            TerrainData for mountain layer rendering
        """
        if not terrain_data.mountains:
            # No mountain here, show surface with very light coloring (almost white)
            surface_terrain = terrain_data.surface

            # Make surface terrain much lighter - almost white for elevation perspective
            lightened_fg = tuple(min(255, max(200, int(c * 2.5))) for c in surface_terrain.fg_color)
            lightened_bg = tuple(min(255, max(180, int(c * 3.0))) for c in surface_terrain.bg_color)

            return TerrainData(
                terrain_type=surface_terrain.terrain_type,
                char="░",  # Light shading character
                fg_color=lightened_fg,
                bg_color=lightened_bg,
                elevation=surface_terrain.elevation,
                is_passable=False  # Can't walk on surface from mountain layer
            )

        # Handle mountain cliffs specially - they become normal terrain in mountain layer
        if terrain_data.mountains.terrain_type == TerrainType.MOUNTAIN_CLIFF:
            # Convert cliff to passable mountain slope terrain
            return TerrainData(
                terrain_type=TerrainType.MOUNTAIN_SLOPE,
                char="^",  # Mountain slope character
                fg_color=(140, 120, 100),  # Normal mountain slope colors
                bg_color=(100, 80, 60),
                elevation=terrain_data.mountains.elevation,
                is_passable=True,  # Passable in mountain layer
                is_entrance=False
            )

        return terrain_data.mountains
    
    def get_current_layer(self) -> WorldLayer:
        """
        Get the current active layer.
        
        Returns:
            Current WorldLayer
        """
        return self.current_layer
    
    def set_position(self, world_x: int, world_y: int) -> None:
        """
        Set the camera world position.
        
        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
        """
        self.world_x = world_x
        self.world_y = world_y
    
    def get_position(self) -> Tuple[int, int]:
        """
        Get the current camera world position.
        
        Returns:
            Tuple of (world_x, world_y)
        """
        return self.world_x, self.world_y
    
    def update_transition(self, delta_time: float) -> None:
        """
        Update transition animation state.
        
        Args:
            delta_time: Time elapsed since last update
        """
        if self.is_transitioning:
            # Simple transition completion after a short delay
            # In a more complex implementation, this could handle smooth animations
            self.is_transitioning = False


def create_default_camera_3d() -> CameraSystem:
    """
    Create a 3D camera system with default settings.
    
    Returns:
        CameraSystem instance with default configuration
    """
    return CameraSystem()
