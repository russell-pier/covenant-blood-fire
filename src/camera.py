"""
Camera system for the three-tier world generation system.

This module provides camera classes for handling position tracking,
movement, bounds checking, and coordinate conversion across different
viewing scales.
"""

from typing import Tuple, Optional

try:
    from .world_types import (
        ViewScale, Coordinate, WorldCoordinate, RegionalCoordinate, LocalCoordinate,
        WORLD_SECTORS_X, WORLD_SECTORS_Y, REGIONAL_BLOCKS_SIZE, LOCAL_CHUNKS_SIZE,
        WORLD_VIEW_WIDTH, WORLD_VIEW_HEIGHT
    )
except ImportError:
    from world_types import (
        ViewScale, Coordinate, WorldCoordinate, RegionalCoordinate, LocalCoordinate,
        WORLD_SECTORS_X, WORLD_SECTORS_Y, REGIONAL_BLOCKS_SIZE, LOCAL_CHUNKS_SIZE,
        WORLD_VIEW_WIDTH, WORLD_VIEW_HEIGHT
    )


class Camera:
    """
    Basic camera class for position tracking and movement.

    Handles camera position, movement with bounds checking, and
    coordinate conversion utilities for a single viewing scale.

    Attributes:
        position: Current camera position
        bounds_width: Maximum width for bounds checking
        bounds_height: Maximum height for bounds checking
        view_width: Width of the viewing area
        view_height: Height of the viewing area
    """
    
    def __init__(
        self, 
        initial_position: Coordinate = Coordinate(0, 0),
        bounds_width: int = 100,
        bounds_height: int = 100,
        view_width: int = WORLD_VIEW_WIDTH,
        view_height: int = WORLD_VIEW_HEIGHT
    ) -> None:
        """
        Initialize camera with position and bounds.
        
        Args:
            initial_position: Starting camera position
            bounds_width: Maximum width for camera movement
            bounds_height: Maximum height for camera movement
            view_width: Width of the viewing area
            view_height: Height of the viewing area
        """
        self.position = initial_position
        self.bounds_width = bounds_width
        self.bounds_height = bounds_height
        self.view_width = view_width
        self.view_height = view_height
    
    def move(self, dx: int, dy: int) -> bool:
        """
        Move camera by relative offset with bounds checking.
        
        Args:
            dx: Horizontal movement offset
            dy: Vertical movement offset
            
        Returns:
            True if movement was successful, False if blocked by bounds
        """
        new_x = self.position.x + dx
        new_y = self.position.y + dy
        
        if self.is_position_valid(Coordinate(new_x, new_y)):
            self.position = Coordinate(new_x, new_y)
            return True
        return False
    
    def move_to(self, position: Coordinate) -> bool:
        """
        Move camera to absolute position with bounds checking.
        
        Args:
            position: Target position
            
        Returns:
            True if movement was successful, False if position invalid
        """
        if self.is_position_valid(position):
            self.position = position
            return True
        return False
    
    def is_position_valid(self, position: Coordinate) -> bool:
        """
        Check if a position is within camera bounds.
        
        Args:
            position: Position to check
            
        Returns:
            True if position is valid, False otherwise
        """
        return (0 <= position.x < self.bounds_width and 
                0 <= position.y < self.bounds_height)
    
    def get_view_bounds(self) -> Tuple[Coordinate, Coordinate]:
        """
        Get the bounds of the current view area.
        
        Returns:
            Tuple of (top_left, bottom_right) coordinates of view area
        """
        half_width = self.view_width // 2
        half_height = self.view_height // 2
        
        top_left = Coordinate(
            max(0, self.position.x - half_width),
            max(0, self.position.y - half_height)
        )
        
        bottom_right = Coordinate(
            min(self.bounds_width - 1, self.position.x + half_width),
            min(self.bounds_height - 1, self.position.y + half_height)
        )
        
        return top_left, bottom_right
    
    def world_to_screen(self, world_pos: Coordinate) -> Optional[Coordinate]:
        """
        Convert world coordinates to screen coordinates.
        
        Args:
            world_pos: Position in world coordinates
            
        Returns:
            Screen coordinate if visible, None if outside view
        """
        # Calculate relative position from camera
        rel_x = world_pos.x - self.position.x
        rel_y = world_pos.y - self.position.y
        
        # Convert to screen coordinates (center of screen is camera position)
        screen_x = rel_x + self.view_width // 2
        screen_y = rel_y + self.view_height // 2
        
        # Check if on screen
        if (0 <= screen_x < self.view_width and 
            0 <= screen_y < self.view_height):
            return Coordinate(screen_x, screen_y)
        
        return None
    
    def screen_to_world(self, screen_pos: Coordinate) -> Coordinate:
        """
        Convert screen coordinates to world coordinates.
        
        Args:
            screen_pos: Position in screen coordinates
            
        Returns:
            World coordinate
        """
        # Convert from screen to relative position
        rel_x = screen_pos.x - self.view_width // 2
        rel_y = screen_pos.y - self.view_height // 2
        
        # Add camera position to get world coordinates
        world_x = self.position.x + rel_x
        world_y = self.position.y + rel_y
        
        return Coordinate(world_x, world_y)
    
    def center_on(self, target: Coordinate) -> bool:
        """
        Center camera on a target position.
        
        Args:
            target: Position to center on
            
        Returns:
            True if successful, False if target outside bounds
        """
        return self.move_to(target)
    
    def get_visible_area(self) -> Tuple[Coordinate, int, int]:
        """
        Get the visible area parameters.
        
        Returns:
            Tuple of (top_left_position, width, height) of visible area
        """
        top_left, bottom_right = self.get_view_bounds()
        width = bottom_right.x - top_left.x + 1
        height = bottom_right.y - top_left.y + 1
        
        return top_left, width, height


class CenteredCursorCamera(Camera):
    """
    Camera with centered cursor that scrolls the world instead of moving cursor.

    The cursor stays in the center of the screen. When movement is requested:
    - If there's more world to see in that direction, the world scrolls
    - If at world boundary, the cursor can move from center

    Attributes:
        cursor_position: Current cursor position in world coordinates
        world_width: Total world width
        world_height: Total world height
        screen_center_x: X coordinate of screen center
        screen_center_y: Y coordinate of screen center
    """

    def __init__(
        self,
        initial_cursor_position: Coordinate = Coordinate(32, 24),  # Center of larger world
        world_width: int = WORLD_SECTORS_X,
        world_height: int = WORLD_SECTORS_Y,
        view_width: int = WORLD_VIEW_WIDTH,
        view_height: int = WORLD_VIEW_HEIGHT
    ) -> None:
        """
        Initialize centered cursor camera.

        Args:
            initial_cursor_position: Starting cursor position in world
            world_width: Total world width
            world_height: Total world height
            view_width: Screen view width
            view_height: Screen view height
        """
        # Initialize base camera
        super().__init__(
            initial_position=Coordinate(0, 0),
            bounds_width=world_width,
            bounds_height=world_height,
            view_width=view_width,
            view_height=view_height
        )

        self.cursor_position = initial_cursor_position
        self.world_width = world_width
        self.world_height = world_height
        self.screen_center_x = view_width // 2
        self.screen_center_y = view_height // 2

        # Calculate initial camera position to center cursor
        self._update_camera_to_center_cursor()

    def _update_camera_to_center_cursor(self) -> None:
        """Update camera position to keep cursor centered when possible."""
        # Calculate desired camera position to center the cursor
        desired_cam_x = self.cursor_position.x - self.screen_center_x
        desired_cam_y = self.cursor_position.y - self.screen_center_y

        # Clamp camera to world bounds
        max_cam_x = self.world_width - self.view_width
        max_cam_y = self.world_height - self.view_height

        actual_cam_x = max(0, min(desired_cam_x, max_cam_x))
        actual_cam_y = max(0, min(desired_cam_y, max_cam_y))

        self.position = Coordinate(actual_cam_x, actual_cam_y)

    def move_cursor(self, dx: int, dy: int) -> bool:
        """
        Move cursor with centered scrolling behavior.

        Args:
            dx: Horizontal movement
            dy: Vertical movement

        Returns:
            True if movement occurred
        """
        # Calculate new cursor position
        new_cursor_x = self.cursor_position.x + dx
        new_cursor_y = self.cursor_position.y + dy

        # Check world bounds
        if (new_cursor_x < 0 or new_cursor_x >= self.world_width or
            new_cursor_y < 0 or new_cursor_y >= self.world_height):
            return False

        # Update cursor position
        self.cursor_position = Coordinate(new_cursor_x, new_cursor_y)

        # Update camera to keep cursor centered
        self._update_camera_to_center_cursor()

        return True

    def get_cursor_screen_position(self) -> Coordinate:
        """
        Get cursor position on screen.

        Returns:
            Screen coordinates of cursor
        """
        screen_x = self.cursor_position.x - self.position.x
        screen_y = self.cursor_position.y - self.position.y
        return Coordinate(screen_x, screen_y)

    def get_cursor_world_position(self) -> Coordinate:
        """
        Get cursor position in world coordinates.

        Returns:
            World coordinates of cursor
        """
        return self.cursor_position

    def set_cursor_position(self, world_position: Coordinate) -> bool:
        """
        Set cursor to specific world position.

        Args:
            world_position: Target world position

        Returns:
            True if position is valid
        """
        if (world_position.x < 0 or world_position.x >= self.world_width or
            world_position.y < 0 or world_position.y >= self.world_height):
            return False

        self.cursor_position = world_position
        self._update_camera_to_center_cursor()
        return True


class MultiScaleCameraSystem:
    """
    Multi-scale camera system managing three independent cameras.
    
    Handles camera switching between world, regional, and local scales
    with coordinate conversion and position preservation.
    
    Attributes:
        world_camera: Camera for world scale (8x6 sectors)
        regional_camera: Camera for regional scale (32x32 blocks)
        local_camera: Camera for local scale (32x32 chunks)
        current_scale: Currently active viewing scale
        selected_sector: Currently selected world sector
        selected_block: Currently selected regional block
    """
    
    def __init__(self) -> None:
        """Initialize the multi-scale camera system with centered cursors."""
        # World camera with centered cursor (64x48 sectors)
        self.world_camera = CenteredCursorCamera(
            initial_cursor_position=Coordinate(WORLD_SECTORS_X // 2, WORLD_SECTORS_Y // 2),
            world_width=WORLD_SECTORS_X,
            world_height=WORLD_SECTORS_Y,
            view_width=WORLD_VIEW_WIDTH,
            view_height=WORLD_VIEW_HEIGHT
        )

        # Regional camera with centered cursor (32x32 blocks within a sector)
        self.regional_camera = CenteredCursorCamera(
            initial_cursor_position=Coordinate(REGIONAL_BLOCKS_SIZE // 2, REGIONAL_BLOCKS_SIZE // 2),
            world_width=REGIONAL_BLOCKS_SIZE,
            world_height=REGIONAL_BLOCKS_SIZE,
            view_width=WORLD_VIEW_WIDTH,
            view_height=WORLD_VIEW_HEIGHT
        )

        # Local camera with centered cursor (32x32 chunks within a block)
        self.local_camera = CenteredCursorCamera(
            initial_cursor_position=Coordinate(LOCAL_CHUNKS_SIZE // 2, LOCAL_CHUNKS_SIZE // 2),
            world_width=LOCAL_CHUNKS_SIZE,
            world_height=LOCAL_CHUNKS_SIZE,
            view_width=WORLD_VIEW_WIDTH,
            view_height=WORLD_VIEW_HEIGHT
        )
        
        self.current_scale = ViewScale.WORLD
        self.selected_sector = WorldCoordinate(WORLD_SECTORS_X // 2, WORLD_SECTORS_Y // 2)
        self.selected_block = RegionalCoordinate(REGIONAL_BLOCKS_SIZE // 2, REGIONAL_BLOCKS_SIZE // 2)
    
    def get_current_camera(self) -> Camera:
        """Get the camera for the current scale."""
        if self.current_scale == ViewScale.WORLD:
            return self.world_camera
        elif self.current_scale == ViewScale.REGIONAL:
            return self.regional_camera
        else:  # LOCAL
            return self.local_camera
    
    def switch_to_scale(self, new_scale: ViewScale) -> bool:
        """
        Switch to a different viewing scale.
        
        Args:
            new_scale: Target viewing scale
            
        Returns:
            True if switch was successful
        """
        if new_scale == self.current_scale:
            return True
        
        old_scale = self.current_scale
        self.current_scale = new_scale
        
        # Update selected positions based on current camera positions
        if old_scale == ViewScale.WORLD and new_scale == ViewScale.REGIONAL:
            # Switching from world to regional - update selected sector
            self.selected_sector = WorldCoordinate(
                self.world_camera.position.x,
                self.world_camera.position.y
            )
        elif old_scale == ViewScale.REGIONAL and new_scale == ViewScale.LOCAL:
            # Switching from regional to local - update selected block
            self.selected_block = RegionalCoordinate(
                self.regional_camera.position.x,
                self.regional_camera.position.y
            )
        
        return True
    
    def move_current_camera(self, dx: int, dy: int) -> bool:
        """
        Move the current scale's camera.
        
        Args:
            dx: Horizontal movement
            dy: Vertical movement
            
        Returns:
            True if movement was successful
        """
        return self.get_current_camera().move_cursor(dx, dy)

    def get_current_cursor_position(self) -> Coordinate:
        """
        Get current cursor position in world coordinates.

        Returns:
            Cursor position for current scale
        """
        return self.get_current_camera().get_cursor_world_position()

    def get_current_cursor_screen_position(self) -> Coordinate:
        """
        Get current cursor position on screen.

        Returns:
            Screen coordinates of cursor
        """
        return self.get_current_camera().get_cursor_screen_position()

    def get_current_position_info(self) -> dict:
        """
        Get detailed position information for current scale.
        
        Returns:
            Dictionary with position information
        """
        current_camera = self.get_current_camera()
        
        cursor_pos = current_camera.get_cursor_world_position()
        screen_pos = current_camera.get_cursor_screen_position()

        info = {
            'scale': self.current_scale.name,
            'camera_position': current_camera.position,
            'cursor_position': cursor_pos,
            'cursor_screen_position': screen_pos,
            'selected_sector': self.selected_sector,
            'selected_block': self.selected_block
        }
        
        if self.current_scale == ViewScale.WORLD:
            info['description'] = f"World View - Cursor at Sector ({cursor_pos.x}, {cursor_pos.y})"
        elif self.current_scale == ViewScale.REGIONAL:
            info['description'] = f"Regional View - Cursor at Block ({cursor_pos.x}, {cursor_pos.y})"
        else:  # LOCAL
            info['description'] = f"Local View - Cursor at Chunk ({cursor_pos.x}, {cursor_pos.y})"
        
        return info
    
    def get_absolute_coordinates(self) -> Tuple[float, float]:
        """
        Get absolute world coordinates for current position.
        
        Returns:
            Tuple of (absolute_x, absolute_y) in world coordinates
        """
        if self.current_scale == ViewScale.WORLD:
            return float(self.world_camera.position.x), float(self.world_camera.position.y)
        elif self.current_scale == ViewScale.REGIONAL:
            base_x = self.selected_sector.x * REGIONAL_BLOCKS_SIZE
            base_y = self.selected_sector.y * REGIONAL_BLOCKS_SIZE
            return (base_x + self.regional_camera.position.x, 
                    base_y + self.regional_camera.position.y)
        else:  # LOCAL
            sector_base_x = self.selected_sector.x * REGIONAL_BLOCKS_SIZE * LOCAL_CHUNKS_SIZE
            sector_base_y = self.selected_sector.y * REGIONAL_BLOCKS_SIZE * LOCAL_CHUNKS_SIZE
            block_base_x = self.selected_block.x * LOCAL_CHUNKS_SIZE
            block_base_y = self.selected_block.y * LOCAL_CHUNKS_SIZE
            return (sector_base_x + block_base_x + self.local_camera.position.x,
                    sector_base_y + block_base_y + self.local_camera.position.y)


if __name__ == "__main__":
    # Basic testing
    print("Testing camera system...")
    
    # Test basic camera
    camera = Camera(bounds_width=10, bounds_height=10)
    print(f"Initial position: {camera.position}")
    
    # Test movement
    if camera.move(2, 3):
        print(f"✓ Moved to: {camera.position}")
    else:
        print("✗ Movement failed")
    
    # Test bounds checking
    if not camera.move(20, 20):
        print("✓ Bounds checking works")
    else:
        print("✗ Bounds checking failed")
    
    # Test multi-scale system
    multi_cam = MultiScaleCameraSystem()
    print(f"✓ Multi-scale camera initialized")
    print(f"Current scale: {multi_cam.current_scale.name}")
    
    # Test scale switching
    multi_cam.switch_to_scale(ViewScale.REGIONAL)
    print(f"✓ Switched to: {multi_cam.current_scale.name}")
    
    info = multi_cam.get_current_position_info()
    print(f"Position info: {info['description']}")
    
    print("Camera system ready!")
