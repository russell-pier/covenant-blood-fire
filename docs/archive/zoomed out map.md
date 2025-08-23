# Zoomed Out Map System for Empires
# Renders chunks as 4x4 pixel blocks for world overview

import threading
import time
from typing import Dict, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import tcod

class MapMode(Enum):
    DETAILED = "detailed"  # Normal 32x32 chunk view
    OVERVIEW = "overview"  # 4x4 pixel per chunk view

@dataclass
class ChunkSummary:
    """Compact representation of a chunk for overview rendering"""
    dominant_terrain: str
    average_elevation: float
    has_water: bool
    has_resources: bool
    population_level: int  # 0=empty, 1=few, 2=moderate, 3=high
    char: str  # Representative character for this chunk
    color: Tuple[int, int, int]

class ZoomedMapRenderer:
    """Handles both detailed and overview map rendering"""
    
    def __init__(self, world_generator, console_width=80, console_height=50):
        self.world_generator = world_generator
        self.console_width = console_width
        self.console_height = console_height
        
        # Map state
        self.current_mode = MapMode.DETAILED
        self.camera_x = 0
        self.camera_y = 0
        self.zoom_camera_x = 0  # Separate camera for overview mode
        self.zoom_camera_y = 0
        
        # Caching for performance
        self.chunk_summaries: Dict[Tuple[int, int], ChunkSummary] = {}
        self.chunk_cache: Dict[Tuple[int, int], Dict] = {}
        
        # Background generation
        self.background_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="MapGen")
        self.generation_queue: Set[Tuple[int, int]] = set()
        self.generating_chunks: Set[Tuple[int, int]] = set()
        
        # Performance settings
        self.overview_chunk_size = 4  # 4x4 pixels per chunk in overview
        self.background_radius = 3    # Generate chunks 3 units ahead
        
    def toggle_map_mode(self):
        """Switch between detailed and overview modes"""
        if self.current_mode == MapMode.DETAILED:
            self.current_mode = MapMode.OVERVIEW
            # Convert current camera position to overview coordinates
            chunk_x = self.camera_x // 32
            chunk_y = self.camera_y // 32
            self.zoom_camera_x = chunk_x * self.overview_chunk_size
            self.zoom_camera_y = chunk_y * self.overview_chunk_size
        else:
            self.current_mode = MapMode.DETAILED
            # Convert overview position back to detailed coordinates
            chunk_x = self.zoom_camera_x // self.overview_chunk_size
            chunk_y = self.zoom_camera_y // self.overview_chunk_size
            self.camera_x = chunk_x * 32
            self.camera_y = chunk_y * 32
    
    def render_current_mode(self, console: tcod.console.Console):
        """Render the map in current mode"""
        if self.current_mode == MapMode.DETAILED:
            self.render_detailed_view(console)
        else:
            self.render_overview_mode(console)
    
    def render_detailed_view(self, console: tcod.console.Console):
        """Render normal detailed chunk view (existing system)"""
        console.clear()
        
        # Calculate which chunks we need
        chunks_x = (self.console_width // 32) + 1
        chunks_y = (self.console_height // 32) + 1
        start_chunk_x = self.camera_x // 32
        start_chunk_y = self.camera_y // 32
        
        for chunk_y in range(chunks_y):
            for chunk_x in range(chunks_x):
                world_chunk_x = start_chunk_x + chunk_x
                world_chunk_y = start_chunk_y + chunk_y
                
                chunk_data = self.get_or_generate_chunk(world_chunk_x, world_chunk_y)
                self.render_chunk_detailed(console, chunk_data, world_chunk_x, world_chunk_y)
        
        # Start background generation for nearby chunks
        self.queue_nearby_chunks(start_chunk_x, start_chunk_y, chunks_x, chunks_y)
    
    def render_overview_mode(self, console: tcod.console.Console):
        """Render zoomed out view where each chunk = 4x4 pixels"""
        console.clear()
        
        # Calculate how many chunks we can show
        visible_chunks_x = self.console_width // self.overview_chunk_size
        visible_chunks_y = self.console_height // self.overview_chunk_size
        
        # Calculate starting chunk position
        start_chunk_x = self.zoom_camera_x // self.overview_chunk_size
        start_chunk_y = self.zoom_camera_y // self.overview_chunk_size
        
        # Render each chunk as a 4x4 block
        for chunk_y in range(visible_chunks_y + 1):
            for chunk_x in range(visible_chunks_x + 1):
                world_chunk_x = start_chunk_x + chunk_x
                world_chunk_y = start_chunk_y + chunk_y
                
                # Get or generate chunk summary
                summary = self.get_or_generate_chunk_summary(world_chunk_x, world_chunk_y)
                
                # Render 4x4 block for this chunk
                self.render_chunk_overview(console, summary, chunk_x, chunk_y)
        
        # Background generation for overview
        self.queue_nearby_chunk_summaries(start_chunk_x, start_chunk_y, visible_chunks_x, visible_chunks_y)
        
        # Add overview UI
        self.render_overview_ui(console)
    
    def render_chunk_overview(self, console: tcod.console.Console, summary: ChunkSummary, local_x: int, local_y: int):
        """Render a single chunk as a 4x4 pixel block"""
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
                    color = self.get_overview_color(summary, dx, dy)
                    
                    console.print(screen_x, screen_y, char, fg=color)
    
    def get_overview_char(self, summary: ChunkSummary, dx: int, dy: int) -> str:
        """Get character for specific position within 4x4 chunk representation"""
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
                "desert": ["·", "∘", "°"]
            }
            chars = variations.get(summary.dominant_terrain, [summary.char])
            return chars[(dx + dy) % len(chars)]
    
    def get_overview_color(self, summary: ChunkSummary, dx: int, dy: int) -> Tuple[int, int, int]:
        """Get color with slight variation for visual texture"""
        r, g, b = summary.color
        
        # Add slight random variation based on position
        variation = ((dx * 3 + dy * 7) % 11) - 5  # -5 to +5 variation
        
        r = max(0, min(255, r + variation))
        g = max(0, min(255, g + variation))
        b = max(0, min(255, b + variation))
        
        return (r, g, b)
    
    def get_or_generate_chunk_summary(self, chunk_x: int, chunk_y: int) -> ChunkSummary:
        """Get chunk summary, generating if needed"""
        key = (chunk_x, chunk_y)
        
        if key not in self.chunk_summaries:
            # Generate summary from full chunk or create fast summary
            if key in self.chunk_cache:
                # Create summary from cached detailed chunk
                chunk_data = self.chunk_cache[key]
                self.chunk_summaries[key] = self.create_chunk_summary(chunk_data)
            else:
                # Create fast summary without generating full detail
                self.chunk_summaries[key] = self.create_fast_chunk_summary(chunk_x, chunk_y)
        
        return self.chunk_summaries[key]
    
    def create_fast_chunk_summary(self, chunk_x: int, chunk_y: int) -> ChunkSummary:
        """Create chunk summary without generating full detailed data"""
        # Use the world generator's noise to determine chunk characteristics quickly
        world_x = chunk_x * 32 + 16  # Sample center of chunk
        world_y = chunk_y * 32 + 16
        
        # Sample the same noise functions used by the world generator
        elevation = self.world_generator.noise_elevation.octave_noise(
            world_x * 0.001, world_y * 0.001, octaves=3
        )
        elevation = (elevation + 1) / 2
        
        moisture = self.world_generator.noise_moisture.octave_noise(
            world_x * 0.008, world_y * 0.008, octaves=3
        )
        moisture = (moisture + 1) / 2
        
        temperature = self.world_generator.noise_temperature.octave_noise(
            world_x * 0.008, world_y * 0.008, octaves=3
        )
        temperature = (temperature + 1) / 2
        
        # Determine terrain type using same logic as detailed generation
        has_water = elevation < 0.3
        dominant_terrain = "water" if has_water else self._determine_fast_terrain(elevation, moisture, temperature)
        
        # Estimate other characteristics
        has_resources = self._estimate_resources(world_x, world_y)
        population_level = 0  # Would come from game state
        
        # Get appropriate char and color
        char, color = self._get_terrain_appearance(dominant_terrain, elevation)
        
        return ChunkSummary(
            dominant_terrain=dominant_terrain,
            average_elevation=elevation,
            has_water=has_water,
            has_resources=has_resources,
            population_level=population_level,
            char=char,
            color=color
        )
    
    def create_chunk_summary(self, chunk_data: Dict) -> ChunkSummary:
        """Create summary from detailed chunk data"""
        terrain_counts = {}
        total_elevation = 0
        has_water = False
        has_resources = False
        
        # Analyze the detailed chunk data
        for (x, y), terrain in chunk_data.items():
            terrain_type = terrain.terrain_type.value
            terrain_counts[terrain_type] = terrain_counts.get(terrain_type, 0) + 1
            total_elevation += terrain.elevation
            
            if terrain_type == "water":
                has_water = True
            
            if hasattr(terrain, 'resource') and terrain.resource:
                has_resources = True
        
        # Find dominant terrain
        dominant_terrain = max(terrain_counts, key=terrain_counts.get)
        average_elevation = total_elevation / len(chunk_data)
        
        char, color = self._get_terrain_appearance(dominant_terrain, average_elevation)
        
        return ChunkSummary(
            dominant_terrain=dominant_terrain,
            average_elevation=average_elevation,
            has_water=has_water,
            has_resources=has_resources,
            population_level=0,  # Would come from population system
            char=char,
            color=color
        )
    
    def _determine_fast_terrain(self, elevation: float, moisture: float, temperature: float) -> str:
        """Fast terrain determination without full chunk generation"""
        if elevation > 0.7:
            return "hills"
        elif temperature > 0.7 and moisture < 0.3:
            return "desert"
        elif moisture > 0.6 and 0.3 < temperature < 0.8:
            return "forest"
        else:
            return "grassland"
    
    def _estimate_resources(self, world_x: int, world_y: int) -> bool:
        """Estimate if chunk has resources using noise sampling"""
        # Use same resource generation noise if available
        if hasattr(self.world_generator, 'noise_cluster'):
            resource_noise = self.world_generator.noise_cluster.octave_noise(
                world_x * 0.003, world_y * 0.003, octaves=3
            )
            return abs(resource_noise) > 0.4
        return False
    
    def _get_terrain_appearance(self, terrain_type: str, elevation: float) -> Tuple[str, Tuple[int, int, int]]:
        """Get representative character and color for terrain type"""
        appearances = {
            "grassland": (".", (50, 120, 50)),
            "forest": ("♠", (0, 100, 0)),
            "hills": ("^", (139, 99, 49)),
            "water": ("~", (100, 150, 255)),
            "desert": ("·", (218, 165, 32)),
            "fertile": ('"', (50, 200, 50))
        }
        
        char, base_color = appearances.get(terrain_type, ("?", (128, 128, 128)))
        
        # Modify color based on elevation
        elevation_mod = int((elevation - 0.5) * 40)
        color = tuple(max(0, min(255, c + elevation_mod)) for c in base_color)
        
        return char, color
    
    def render_overview_ui(self, console: tcod.console.Console):
        """Render UI elements for overview mode"""
        # Show current mode in corner
        console.print(1, 1, "OVERVIEW MODE", fg=(255, 255, 0))
        console.print(1, 2, "Press TAB to zoom in", fg=(200, 200, 200))
        
        # Show scale
        console.print(1, self.console_height - 3, "█ = 32x32 area", fg=(150, 150, 150))
        console.print(1, self.console_height - 2, f"Viewing {self.zoom_camera_x//4},{self.zoom_camera_y//4}", fg=(150, 150, 150))
    
    def get_or_generate_chunk(self, chunk_x: int, chunk_y: int):
        """Get chunk data, using cache or generating if needed"""
        key = (chunk_x, chunk_y)
        if key not in self.chunk_cache:
            self.chunk_cache[key] = self.world_generator.generate_chunk(chunk_x, chunk_y)
        return self.chunk_cache[key]
    
    def render_chunk_detailed(self, console: tcod.console.Console, chunk_data: Dict, world_chunk_x: int, world_chunk_y: int):
        """Render detailed chunk (your existing rendering logic)"""
        # Implement your existing detailed chunk rendering here
        pass
    
    def queue_nearby_chunks(self, start_x: int, start_y: int, width: int, height: int):
        """Queue nearby chunks for background generation"""
        for y in range(start_y - self.background_radius, start_y + height + self.background_radius):
            for x in range(start_x - self.background_radius, start_x + width + self.background_radius):
                key = (x, y)
                if key not in self.chunk_cache and key not in self.generating_chunks:
                    self.generation_queue.add(key)
                    self.generating_chunks.add(key)
                    self.background_executor.submit(self._generate_chunk_background, x, y)
    
    def queue_nearby_chunk_summaries(self, start_x: int, start_y: int, width: int, height: int):
        """Queue nearby chunk summaries for background generation"""
        for y in range(start_y - self.background_radius, start_y + height + self.background_radius):
            for x in range(start_x - self.background_radius, start_x + width + self.background_radius):
                key = (x, y)
                if key not in self.chunk_summaries:
                    self.background_executor.submit(self._generate_summary_background, x, y)
    
    def _generate_chunk_background(self, chunk_x: int, chunk_y: int):
        """Background thread chunk generation"""
        try:
            chunk_data = self.world_generator.generate_chunk(chunk_x, chunk_y)
            self.chunk_cache[(chunk_x, chunk_y)] = chunk_data
            self.generating_chunks.discard((chunk_x, chunk_y))
        except Exception as e:
            print(f"Background generation error for chunk ({chunk_x}, {chunk_y}): {e}")
            self.generating_chunks.discard((chunk_x, chunk_y))
    
    def _generate_summary_background(self, chunk_x: int, chunk_y: int):
        """Background thread summary generation"""
        try:
            summary = self.create_fast_chunk_summary(chunk_x, chunk_y)
            self.chunk_summaries[(chunk_x, chunk_y)] = summary
        except Exception as e:
            print(f"Background summary generation error for chunk ({chunk_x}, {chunk_y}): {e}")
    
    def handle_movement(self, dx: int, dy: int):
        """Handle camera movement in current mode"""
        if self.current_mode == MapMode.DETAILED:
            self.camera_x += dx
            self.camera_y += dy
        else:
            # In overview mode, movement is faster
            move_speed = 4  # Move by chunk units
            self.zoom_camera_x += dx * move_speed
            self.zoom_camera_y += dy * move_speed
    
    def cleanup(self):
        """Cleanup background threads"""
        self.background_executor.shutdown(wait=True)

# Integration example:
class Game:
    def __init__(self):
        from organic import WorldGenerator  # Your world generator
        self.world_generator = WorldGenerator(seed=12345)
        self.map_renderer = ZoomedMapRenderer(self.world_generator)
        # ... rest of game init
    
    def handle_keydown(self, event):
        if event.sym == tcod.event.KeySym.TAB:
            self.map_renderer.toggle_map_mode()
        elif event.sym == tcod.event.KeySym.UP:
            self.map_renderer.handle_movement(0, -1)
        elif event.sym == tcod.event.KeySym.DOWN:
            self.map_renderer.handle_movement(0, 1)
        elif event.sym == tcod.event.KeySym.LEFT:
            self.map_renderer.handle_movement(-1, 0)
        elif event.sym == tcod.event.KeySym.RIGHT:
            self.map_renderer.handle_movement(1, 0)
    
    def render(self, console):
        self.map_renderer.render_current_mode(console)