"""
Performance Optimized Zoomed Map System for strategic world overview.

MAIN PERFORMANCE FIXES:
1. Single terrain sample per chunk instead of 9 samples
2. Aggressive caching with TTL expiration
3. Pre-computed terrain color lookup tables
4. Reduced thread contention with targeted locking
5. Fast noise-based terrain classification
"""

import threading
import time
from typing import Dict, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import tcod

from ..world.layered import WorldLayer
from ..world.terrain import TerrainType
from ..world.chunks import ChunkCoordinate


class MapMode(Enum):
    """Map rendering modes."""
    DETAILED = "detailed"  # Normal tile-by-tile view
    OVERVIEW = "overview"  # 4x4 pixel per chunk view


@dataclass
class ChunkSummary:
    """Compact representation of a chunk for overview rendering."""
    dominant_terrain: str
    average_elevation: float
    has_water: bool
    has_resources: bool
    population_level: int  # 0=empty, 1=few, 2=moderate, 3=high
    char: str  # Representative character for this chunk
    color: Tuple[int, int, int]


class ZoomedMapRenderer:
    """Handles both detailed and overview map rendering."""
    
    def __init__(self, world_generator, console_width=80, console_height=50):
        """Initialize the performance-optimized zoomed map renderer."""
        self.world_generator = world_generator
        self.console_width = console_width
        self.console_height = console_height

        # Map state
        self.current_mode = MapMode.DETAILED
        self.camera_x = 0
        self.camera_y = 0
        self.zoom_camera_x = 0  # Separate camera for overview mode
        self.zoom_camera_y = 0
        self.last_detailed_cursor_x = 0  # Last cursor position in detailed mode
        self.last_detailed_cursor_y = 0

        # PERFORMANCE FIX 1: Aggressive caching with expiration
        self.chunk_summaries: Dict[Tuple[int, int], ChunkSummary] = {}
        self.summary_timestamps: Dict[Tuple[int, int], float] = {}
        self.cache_ttl = 60.0  # Cache for 60 seconds

        # PERFORMANCE FIX 2: Pre-computed terrain lookup
        self.terrain_colors = self._precompute_terrain_colors()

        # PERFORMANCE FIX 3: Batch generation queue
        self.background_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="MapGen")
        self.generation_queue: Set[Tuple[int, int]] = set()
        self.currently_generating: Set[Tuple[int, int]] = set()

        # Settings
        self.overview_chunk_size = 4  # 4x4 pixels per chunk in overview
        self.background_radius = 2    # Reduced for less background work

        # PERFORMANCE FIX 4: Reduce lock contention
        self._generation_lock = threading.Lock()  # Only lock generation queue

        # PERFORMANCE FIX 5: Fast noise samplers
        self._setup_fast_noise_samplers()

    def _precompute_terrain_colors(self) -> Dict[str, Tuple[str, Tuple[int, int, int]]]:
        """Pre-compute terrain appearances to avoid repeated calculations."""
        return {
            "water": ("~", (100, 150, 255)),
            "shallow_water": ("~", (120, 170, 255)),
            "deep_water": ("~", (80, 130, 255)),
            "grass": (".", (50, 120, 50)),
            "grassland": (".", (50, 120, 50)),
            "light_grass": (".", (60, 140, 60)),
            "dark_grass": (".", (40, 100, 40)),
            "forest": ("♠", (0, 100, 0)),
            "hills": ("^", (139, 99, 49)),
            "mountains": ("▲", (120, 100, 80)),
            "desert": ("·", (218, 165, 32)),
            "swamp": ("≈", (100, 120, 80)),
            "fertile": ("*", (50, 200, 50)),
            "sand": (".", (194, 178, 128)),
            "caves": ("○", (100, 100, 100)),
        }

    def _setup_fast_noise_samplers(self):
        """Setup optimized noise sampling for fast terrain determination."""
        # Cache references to avoid repeated attribute lookups
        if hasattr(self.world_generator, 'environmental_generator'):
            self.env_gen = self.world_generator.environmental_generator
        else:
            self.env_gen = None

        if hasattr(self.world_generator, 'noise_generator'):
            self.noise_gen = self.world_generator.noise_generator
        else:
            self.noise_gen = None
    
    def toggle_map_mode(self):
        """Switch between detailed and overview modes."""
        if self.current_mode == MapMode.DETAILED:
            # Save current detailed cursor position
            self.last_detailed_cursor_x = self.camera_x
            self.last_detailed_cursor_y = self.camera_y

            self.current_mode = MapMode.OVERVIEW
            # Convert current camera position to overview coordinates
            chunk_size = self.world_generator.chunk_manager.chunk_size
            chunk_x = self.camera_x // chunk_size
            chunk_y = self.camera_y // chunk_size

            # Center the overview view on the current camera position
            visible_chunks_x = self.console_width // self.overview_chunk_size
            visible_chunks_y = self.console_height // self.overview_chunk_size

            # Position view so camera is in center
            self.zoom_camera_x = (chunk_x - visible_chunks_x // 2) * self.overview_chunk_size
            self.zoom_camera_y = (chunk_y - visible_chunks_y // 2) * self.overview_chunk_size
        else:
            self.current_mode = MapMode.DETAILED
            # Don't change camera position when switching back to detailed mode
            # The user might want to stay where they were before opening overview
    
    def render_current_mode(self, console: tcod.console.Console):
        """Render the map in current mode."""
        if self.current_mode == MapMode.DETAILED:
            self.render_detailed_view(console)
        else:
            self.render_overview_mode(console)
    
    def render_detailed_view(self, console: tcod.console.Console):
        """Render normal detailed view using existing world generator."""
        # Don't clear console here - let the main render method handle it

        # Use the existing viewport system for detailed rendering
        if hasattr(self.world_generator, 'viewport'):
            # Update camera position
            if hasattr(self.world_generator, 'camera'):
                self.world_generator.camera.set_position(self.camera_x, self.camera_y)

            # Render using existing system
            self.world_generator.viewport.render_world(console, self.world_generator)
            self.world_generator.viewport.render_crosshair(console, self.world_generator)
        else:
            # Fallback: simple terrain rendering with crosshair
            self._render_detailed_fallback(console)
            # Render crosshair in center
            center_x = console.width // 2
            center_y = console.height // 2
            console.print(center_x, center_y, "+", fg=(255, 255, 255), bg=(0, 0, 0))
    
    def _render_detailed_fallback(self, console: tcod.console.Console):
        """Fallback detailed rendering if viewport not available."""
        console.clear()
        
        # Render visible tiles
        for screen_y in range(console.height):
            for screen_x in range(console.width):
                world_x = self.camera_x + screen_x - console.width // 2
                world_y = self.camera_y + screen_y - console.height // 2
                
                # Get terrain at this position
                if hasattr(self.world_generator, 'get_layered_terrain_at'):
                    layered_data = self.world_generator.get_layered_terrain_at(world_x, world_y)
                    if layered_data and self.world_generator.camera_3d:
                        rendered_terrain = self.world_generator.camera_3d.get_render_data(layered_data)
                        console.print(screen_x, screen_y, rendered_terrain.char, 
                                    fg=rendered_terrain.fg_color, bg=rendered_terrain.bg_color)
                        continue
                
                # Fallback to basic terrain
                terrain_type = self.world_generator.get_terrain_at(world_x, world_y)
                terrain_props = self.world_generator.terrain_mapper.get_terrain_properties(terrain_type)
                console.print(screen_x, screen_y, terrain_props.character,
                            fg=terrain_props.foreground_color, bg=terrain_props.background_color)
    
    def render_overview_mode(self, console: tcod.console.Console):
        """OPTIMIZED: Overview rendering with batch operations."""
        console.clear()

        visible_chunks_x = self.console_width // self.overview_chunk_size
        visible_chunks_y = self.console_height // self.overview_chunk_size

        start_chunk_x = self.zoom_camera_x // self.overview_chunk_size
        start_chunk_y = self.zoom_camera_y // self.overview_chunk_size

        # OPTIMIZATION: Pre-calculate which chunks are visible
        visible_summaries = {}
        for chunk_y in range(visible_chunks_y + 1):
            for chunk_x in range(visible_chunks_x + 1):
                world_chunk_x = start_chunk_x + chunk_x
                world_chunk_y = start_chunk_y + chunk_y
                summary = self.get_or_generate_chunk_summary(world_chunk_x, world_chunk_y)
                visible_summaries[(chunk_x, chunk_y)] = summary

        # OPTIMIZATION: Batch render chunks
        for (local_x, local_y), summary in visible_summaries.items():
            self._render_chunk_block(console, summary, local_x, local_y)

        # UI elements
        self.render_overview_cursor(console, start_chunk_x, start_chunk_y)
        self.render_camera_marker(console, start_chunk_x, start_chunk_y)
        self.render_overview_ui(console)

        # Queue background generation after rendering
        self._queue_background_generation(start_chunk_x, start_chunk_y, visible_chunks_x, visible_chunks_y)

    def _render_chunk_block(self, console: tcod.console.Console, summary: ChunkSummary, local_x: int, local_y: int):
        """OPTIMIZED: Fast 4x4 block rendering."""
        base_x = local_x * self.overview_chunk_size
        base_y = local_y * self.overview_chunk_size

        # Simple pattern for the 4x4 block
        for dy in range(self.overview_chunk_size):
            for dx in range(self.overview_chunk_size):
                screen_x = base_x + dx
                screen_y = base_y + dy

                if 0 <= screen_x < self.console_width and 0 <= screen_y < self.console_height:
                    # Simple character variation
                    if summary.has_water:
                        char = "~" if (dx + dy) % 2 == 0 else "≈"
                    elif summary.has_resources and dx == 1 and dy == 1:
                        char = "●"
                    elif summary.population_level > 0 and dx == 1 and dy == 1:
                        char = "■" if summary.population_level > 2 else "□"
                    else:
                        char = summary.char

                    # Simple color variation
                    r, g, b = summary.color
                    variation = ((dx + dy) % 3) - 1  # -1, 0, 1
                    fg_color = (
                        max(0, min(255, r + variation * 5)),
                        max(0, min(255, g + variation * 5)),
                        max(0, min(255, b + variation * 5))
                    )

                    # Simple background color
                    bg_color = self.get_overview_bg_color(summary, dx, dy)

                    console.print(screen_x, screen_y, char, fg=fg_color, bg=bg_color)
    
    def render_chunk_overview(self, console: tcod.console.Console, summary: ChunkSummary, local_x: int, local_y: int):
        """Render a single chunk as a 4x4 pixel block."""
        base_x = local_x * self.overview_chunk_size
        base_y = local_y * self.overview_chunk_size
        
        # Fill the 4x4 area with the chunk's dominant characteristics
        for dy in range(self.overview_chunk_size):
            for dx in range(self.overview_chunk_size):
                screen_x = base_x + dx
                screen_y = base_y + dy
                
                if screen_x < self.console_width and screen_y < self.console_height:
                    # Use different patterns for variety within the chunk
                    char = self.get_overview_char(summary, dx, dy)
                    fg_color = self.get_overview_color(summary, dx, dy)
                    bg_color = self.get_overview_bg_color(summary, dx, dy)

                    console.print(screen_x, screen_y, char, fg=fg_color, bg=bg_color)
    
    def get_overview_char(self, summary: ChunkSummary, dx: int, dy: int) -> str:
        """Get character for specific position within 4x4 chunk representation."""
        # Add some variation within chunks
        if summary.has_water:
            return "~" if (dx + dy) % 2 == 0 else "≈"
        elif summary.has_resources:
            return "●" if dx == 1 and dy == 1 else summary.char  # Resource in center
        elif summary.population_level > 0:
            if dx == 1 and dy == 1:  # Center position
                return "■" if summary.population_level > 2 else "□"
            else:
                return summary.char
        else:
            # Terrain variation
            variations = {
                "grassland": [".", "·", ","],
                "forest": ["♠", "♣", "T"],
                "hills": ["^", "▲", "∩"],
                "desert": ["·", "∘", "°"],
                "mountains": ["▲", "⩙", "∩"]
            }
            chars = variations.get(summary.dominant_terrain, [summary.char])
            return chars[(dx + dy) % len(chars)]
    
    def get_overview_color(self, summary: ChunkSummary, dx: int, dy: int) -> Tuple[int, int, int]:
        """Get color with slight variation for visual texture."""
        r, g, b = summary.color
        
        # Add slight random variation based on position
        variation = ((dx * 3 + dy * 7) % 11) - 5  # -5 to +5 variation
        
        r = max(0, min(255, r + variation))
        g = max(0, min(255, g + variation))
        b = max(0, min(255, b + variation))
        
        return (r, g, b)

    def get_overview_bg_color(self, summary: ChunkSummary, dx: int, dy: int) -> Tuple[int, int, int]:
        """Get background color for overview tiles."""
        # Background colors based on terrain type
        bg_colors = {
            # Water types - darker blues
            "water": (20, 40, 80),
            "shallow_water": (25, 45, 85),
            "deep_water": (15, 35, 75),

            # Land types - darker versions of terrain colors
            "grass": (10, 25, 10),
            "grassland": (10, 25, 10),
            "light_grass": (12, 28, 12),
            "dark_grass": (8, 20, 8),
            "forest": (0, 20, 0),
            "hills": (25, 18, 8),
            "mountains": (20, 15, 12),
            "desert": (35, 25, 5),
            "swamp": (15, 20, 12),
            "fertile": (8, 30, 8),
            "sand": (30, 25, 18),
            "caves": (15, 15, 15),
        }

        base_bg = bg_colors.get(summary.dominant_terrain, (5, 10, 5))

        # Add slight variation based on position
        variation = ((dx * 2 + dy * 3) % 7) - 3  # -3 to +3 variation

        r, g, b = base_bg
        r = max(0, min(50, r + variation))
        g = max(0, min(50, g + variation))
        b = max(0, min(50, b + variation))

        return (r, g, b)
    
    def get_or_generate_chunk_summary(self, chunk_x: int, chunk_y: int) -> ChunkSummary:
        """Get chunk summary, generating if needed."""
        key = (chunk_x, chunk_y)
        
        with self._cache_lock:
            if key not in self.chunk_summaries:
                # Create fast summary without generating full detail
                self.chunk_summaries[key] = self.create_fast_chunk_summary(chunk_x, chunk_y)
        
        return self.chunk_summaries[key]

    def create_fast_chunk_summary(self, chunk_x: int, chunk_y: int) -> ChunkSummary:
        """OPTIMIZED: Create chunk summary using minimal sampling."""
        chunk_size = getattr(self.world_generator.chunk_manager, 'chunk_size', 32)
        center_x = chunk_x * chunk_size + chunk_size // 2
        center_y = chunk_y * chunk_size + chunk_size // 2

        # OPTIMIZATION: Single center sample instead of 9 samples
        dominant_terrain, average_elevation = self._fast_terrain_sample(center_x, center_y)

        # OPTIMIZATION: Quick estimates without complex calculations
        has_water = "water" in dominant_terrain
        has_resources = self._quick_resource_check(center_x, center_y)
        population_level = self._quick_population_check(chunk_x, chunk_y)

        # OPTIMIZATION: Use pre-computed colors
        char, color = self._get_cached_terrain_appearance(dominant_terrain, average_elevation)

        return ChunkSummary(
            dominant_terrain=dominant_terrain,
            average_elevation=average_elevation,
            has_water=has_water,
            has_resources=has_resources,
            population_level=population_level,
            char=char,
            color=color
        )

    def _fast_terrain_sample(self, world_x: int, world_y: int) -> Tuple[str, float]:
        """OPTIMIZED: Single fast terrain sample without full generation."""

        # Try environmental generator first (should be fastest)
        if self.env_gen:
            try:
                env_data = self.env_gen.generate_environmental_data(world_x, world_y)
                elevation = (env_data.elevation + 200) / 3200  # Normalize

                # Simple terrain classification
                if elevation < 0.25:
                    return "water", elevation
                elif elevation > 0.75:
                    return "mountains", elevation
                elif elevation > 0.55:
                    return "hills", elevation
                else:
                    # Use noise for variety in lowlands
                    if self.noise_gen:
                        variety = self.noise_gen.generate(world_x * 0.01, world_y * 0.01)
                        if variety > 0.3:
                            return "forest", elevation
                        elif variety < -0.3:
                            return "desert", elevation
                    return "grassland", elevation

            except Exception:
                pass  # Fall through to backup method

        # BACKUP: Simple noise-based terrain (no complex generation)
        if self.noise_gen:
            elevation_noise = self.noise_gen.generate(world_x * 0.003, world_y * 0.003)
            elevation = (elevation_noise + 1) * 0.5  # 0-1 range

            if elevation < 0.3:
                return "water", elevation
            elif elevation > 0.7:
                return "hills", elevation
            else:
                return "grassland", elevation

        # ULTIMATE FALLBACK
        return "grassland", 0.5

    def get_or_generate_chunk_summary(self, chunk_x: int, chunk_y: int) -> ChunkSummary:
        """OPTIMIZED: Get chunk summary with smart caching."""
        key = (chunk_x, chunk_y)
        current_time = time.time()

        # Check if we have a valid cached summary
        if key in self.chunk_summaries:
            if key in self.summary_timestamps:
                age = current_time - self.summary_timestamps[key]
                if age < self.cache_ttl:
                    return self.chunk_summaries[key]

        # Generate new summary
        summary = self.create_fast_chunk_summary(chunk_x, chunk_y)
        self.chunk_summaries[key] = summary
        self.summary_timestamps[key] = current_time

        return summary

    def _get_cached_terrain_appearance(self, terrain_type: str, elevation: float) -> Tuple[str, Tuple[int, int, int]]:
        """OPTIMIZED: Use pre-computed terrain colors."""
        char, base_color = self.terrain_colors.get(terrain_type, (".", (100, 150, 100)))

        # Quick elevation modification
        elevation_mod = int((elevation - 0.5) * 30)
        color = (
            max(0, min(255, base_color[0] + elevation_mod)),
            max(0, min(255, base_color[1] + elevation_mod)),
            max(0, min(255, base_color[2] + elevation_mod))
        )

        return char, color

    def _quick_resource_check(self, world_x: int, world_y: int) -> bool:
        """OPTIMIZED: Quick resource estimation."""
        if not self.noise_gen:
            return False

        # Single noise sample
        try:
            resource_noise = self.noise_gen.generate(world_x * 0.01, world_y * 0.01)
            return abs(resource_noise) > 0.6
        except:
            return False

    def _quick_population_check(self, chunk_x: int, chunk_y: int) -> int:
        """OPTIMIZED: Quick population check."""
        # For now, just return 0 - this would be replaced with
        # a fast lookup in a population grid or similar
        return 0

    def _queue_background_generation(self, start_x: int, start_y: int, width: int, height: int):
        """OPTIMIZED: Background generation with limits."""
        with self._generation_lock:
            # Limit concurrent generations
            if len(self.currently_generating) > 5:
                return

            # Queue nearby chunks (skip every other for performance)
            for y in range(start_y - self.background_radius, start_y + height + self.background_radius, 2):
                for x in range(start_x - self.background_radius, start_x + width + self.background_radius, 2):
                    key = (x, y)

                    if key not in self.chunk_summaries and key not in self.currently_generating:
                        self.currently_generating.add(key)
                        self.background_executor.submit(self._generate_summary_background, x, y)

    def _generate_summary_background(self, chunk_x: int, chunk_y: int):
        """Background summary generation."""
        try:
            summary = self.create_fast_chunk_summary(chunk_x, chunk_y)
            self.chunk_summaries[(chunk_x, chunk_y)] = summary
            self.summary_timestamps[(chunk_x, chunk_y)] = time.time()
        except Exception as e:
            print(f"Background generation error: {e}")
        finally:
            with self._generation_lock:
                self.currently_generating.discard((chunk_x, chunk_y))

    def _determine_fast_terrain(self, elevation: float, moisture: float, temperature: float) -> str:
        """Fast terrain determination without full chunk generation."""
        if elevation > 0.8:
            return "mountains"
        elif elevation > 0.6:
            return "hills"
        elif temperature > 0.7 and moisture < 0.3:
            return "desert"
        elif moisture > 0.6 and 0.3 < temperature < 0.8:
            return "forest"
        elif moisture > 0.7:
            return "swamp"
        else:
            return "grassland"

    def _estimate_resources(self, world_x: int, world_y: int) -> bool:
        """Estimate if chunk has resources using noise sampling."""
        # Use resource generation logic if available
        if hasattr(self.world_generator, 'resource_generator'):
            # Sample a few points in the chunk
            for dx in [-8, 0, 8]:
                for dy in [-8, 0, 8]:
                    sample_x = world_x + dx
                    sample_y = world_y + dy

                    # Check if this position would have resources
                    if hasattr(self.world_generator.resource_generator, 'noise_cluster'):
                        cluster_noise = self.world_generator.resource_generator.noise_cluster.generate(
                            sample_x * 0.003, sample_y * 0.003
                        )
                        if abs(cluster_noise) > 0.4:
                            return True

        # Fallback: simple noise-based estimation
        resource_noise = self.world_generator.noise_generator.generate(world_x * 0.01, world_y * 0.01)
        return abs(resource_noise) > 0.6

    def _estimate_population(self, chunk_x: int, chunk_y: int) -> int:
        """Estimate population level from animal herds."""
        if not hasattr(self.world_generator, 'animal_manager'):
            return 0

        chunk_size = self.world_generator.chunk_manager.chunk_size
        chunk_world_x = chunk_x * chunk_size
        chunk_world_y = chunk_y * chunk_size

        animal_count = 0

        # Check for herds in this chunk area
        with self.world_generator.animal_manager._herds_lock:
            herds_snapshot = list(self.world_generator.animal_manager.herds.values())

        for herd in herds_snapshot:
            if not herd.animals:
                continue

            # Check if herd center is in this chunk
            herd_center_x = sum(animal.x for animal in herd.animals) / len(herd.animals)
            herd_center_y = sum(animal.y for animal in herd.animals) / len(herd.animals)

            if (chunk_world_x <= herd_center_x < chunk_world_x + chunk_size and
                chunk_world_y <= herd_center_y < chunk_world_y + chunk_size):
                animal_count += len(herd.animals)

        # Convert to population level
        if animal_count >= 15:
            return 3  # High
        elif animal_count >= 8:
            return 2  # Moderate
        elif animal_count >= 3:
            return 1  # Few
        else:
            return 0  # Empty

    def _get_terrain_appearance(self, terrain_type: str, elevation: float) -> Tuple[str, Tuple[int, int, int]]:
        """Get representative character and color for terrain type."""
        appearances = {
            # Water types
            "water": ("~", (100, 150, 255)),
            "shallow_water": ("~", (120, 170, 255)),
            "deep_water": ("~", (80, 130, 255)),

            # Land types
            "grass": (".", (50, 120, 50)),
            "grassland": (".", (50, 120, 50)),
            "light_grass": (".", (60, 140, 60)),
            "dark_grass": (".", (40, 100, 40)),
            "forest": ("♠", (0, 100, 0)),
            "hills": ("^", (139, 99, 49)),
            "mountains": ("▲", (120, 100, 80)),
            "desert": ("·", (218, 165, 32)),
            "swamp": ("≈", (100, 120, 80)),
            "fertile": ("*", (50, 200, 50)),
            "sand": (".", (194, 178, 128)),
            "caves": ("○", (100, 100, 100)),
        }

        char, base_color = appearances.get(terrain_type, (".", (100, 150, 100)))

        # Modify color based on elevation
        elevation_mod = int((elevation - 0.5) * 30)
        color = tuple(max(0, min(255, c + elevation_mod)) for c in base_color)

        return char, color

    def render_overview_cursor(self, console: tcod.console.Console, start_chunk_x: int, start_chunk_y: int):
        """No cursor in overview mode - camera moves freely."""
        # No cursor rendering - the view moves directly with arrow keys
        pass

    def render_camera_marker(self, console: tcod.console.Console, start_chunk_x: int, start_chunk_y: int):
        """Render marker showing where the detailed cursor was last positioned."""
        # Calculate which chunk the last detailed cursor is in
        chunk_size = getattr(self.world_generator.chunk_manager, 'chunk_size', 32)
        cursor_chunk_x = self.last_detailed_cursor_x // chunk_size
        cursor_chunk_y = self.last_detailed_cursor_y // chunk_size

        # Convert to screen coordinates
        screen_x = (cursor_chunk_x - start_chunk_x) * self.overview_chunk_size + self.overview_chunk_size // 2
        screen_y = (cursor_chunk_y - start_chunk_y) * self.overview_chunk_size + self.overview_chunk_size // 2

        # Render camera marker if on screen
        if 0 <= screen_x < console.width and 0 <= screen_y < console.height:
            console.print(screen_x, screen_y, "@", fg=(255, 0, 0), bg=(80, 80, 80))

    def render_overview_ui(self, console: tcod.console.Console):
        """Render UI elements for overview mode."""
        # Show current mode in corner
        console.print(1, 1, "OVERVIEW MODE", fg=(255, 255, 0))
        console.print(1, 2, "Press M to zoom in", fg=(200, 200, 200))
        console.print(1, 3, "Press ENTER to fast travel to center", fg=(200, 200, 200))

        # Show scale and controls
        console.print(1, console.height - 4, "█ = 32x32 area", fg=(150, 150, 150))
        console.print(1, console.height - 3, "@ = Last detailed position", fg=(150, 150, 150))
        console.print(1, console.height - 2, "WASD = Move camera view", fg=(150, 150, 150))

    def queue_nearby_chunk_summaries(self, start_x: int, start_y: int, width: int, height: int):
        """Queue nearby chunk summaries for background generation."""
        for y in range(start_y - self.background_radius, start_y + height + self.background_radius):
            for x in range(start_x - self.background_radius, start_x + width + self.background_radius):
                key = (x, y)
                if key not in self.chunk_summaries:
                    self.background_executor.submit(self._generate_summary_background, x, y)

    def _generate_summary_background(self, chunk_x: int, chunk_y: int):
        """Background thread summary generation."""
        try:
            summary = self.create_fast_chunk_summary(chunk_x, chunk_y)
            with self._cache_lock:
                self.chunk_summaries[(chunk_x, chunk_y)] = summary
        except Exception as e:
            print(f"Background summary generation error for chunk ({chunk_x}, {chunk_y}): {e}")

    def handle_movement(self, dx: int, dy: int):
        """Handle camera movement in current mode."""
        if self.current_mode == MapMode.DETAILED:
            self.camera_x += dx
            self.camera_y += dy
        else:
            # In overview mode, move the view (cursor stays centered)
            # Move by chunk units for faster navigation
            move_speed = self.overview_chunk_size
            self.zoom_camera_x += dx * move_speed
            self.zoom_camera_y += dy * move_speed

            # Update cursor position to match center of view
            visible_chunks_x = self.console_width // self.overview_chunk_size
            visible_chunks_y = self.console_height // self.overview_chunk_size
            center_chunk_x = self.zoom_camera_x // self.overview_chunk_size + visible_chunks_x // 2
            center_chunk_y = self.zoom_camera_y // self.overview_chunk_size + visible_chunks_y // 2

            self.overview_cursor_x = center_chunk_x
            self.overview_cursor_y = center_chunk_y

    def get_current_mode(self) -> MapMode:
        """Get the current map mode."""
        return self.current_mode

    def is_overview_mode(self) -> bool:
        """Check if currently in overview mode."""
        return self.current_mode == MapMode.OVERVIEW

    def is_detailed_mode(self) -> bool:
        """Check if currently in detailed mode."""
        return self.current_mode == MapMode.DETAILED

    def get_camera_position(self) -> Tuple[int, int]:
        """Get current camera position for the active mode."""
        if self.current_mode == MapMode.DETAILED:
            return self.camera_x, self.camera_y
        else:
            return self.zoom_camera_x, self.zoom_camera_y

    def set_camera_position(self, x: int, y: int):
        """Set camera position for the active mode."""
        if self.current_mode == MapMode.DETAILED:
            self.camera_x = x
            self.camera_y = y
        else:
            self.zoom_camera_x = x
            self.zoom_camera_y = y

    def fast_travel_to_cursor(self):
        """Fast travel the detailed camera to the center of current overview view."""
        if self.current_mode == MapMode.OVERVIEW:
            # Calculate center of current view
            visible_chunks_x = self.console_width // self.overview_chunk_size
            visible_chunks_y = self.console_height // self.overview_chunk_size

            center_chunk_x = self.zoom_camera_x // self.overview_chunk_size + visible_chunks_x // 2
            center_chunk_y = self.zoom_camera_y // self.overview_chunk_size + visible_chunks_y // 2

            # Convert to world coordinates
            chunk_size = getattr(self.world_generator.chunk_manager, 'chunk_size', 32)
            target_world_x = center_chunk_x * chunk_size + chunk_size // 2
            target_world_y = center_chunk_y * chunk_size + chunk_size // 2

            # Update detailed camera position
            self.camera_x = target_world_x
            self.camera_y = target_world_y

            print(f"Fast traveled to chunk ({center_chunk_x}, {center_chunk_y})")

    def cleanup(self):
        """Cleanup background threads."""
        self.background_executor.shutdown(wait=True)
