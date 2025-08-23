#!/usr/bin/env python3
"""
Three-Tier World Generation System Demo

This script demonstrates the three-tier world generation system without
requiring graphics, showing world generation, navigation, and data access.
"""

import time
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from covenant.world.generators.world_scale import WorldScaleGenerator
from covenant.world.generators.regional_scale import RegionalScaleGenerator
from covenant.world.camera.multi_scale_camera import MultiScaleCameraSystem
from covenant.world.data.scale_types import ViewScale
from covenant.world.data.config import get_world_config


def print_separator(title: str):
    """Print a section separator."""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)


def demo_world_generation():
    """Demonstrate world generation."""
    print_separator("WORLD GENERATION DEMO")
    
    # Get configuration
    config = get_world_config()
    seed = config.get_world_seed()
    print(f"Using seed: {seed}")
    
    # Create world generator
    print("Creating world generator...")
    world_generator = WorldScaleGenerator(seed=seed)
    
    # Generate complete world
    print("Generating complete world map...")
    start_time = time.time()
    world_map = world_generator.generate_complete_world_map()
    generation_time = time.time() - start_time
    
    print(f"World generation completed in {generation_time:.2f} seconds")
    print(f"Generated {len(world_map.sectors)} sectors")
    
    # Show world statistics
    world_info = world_generator.get_world_info()
    print(f"\nWorld Statistics:")
    print(f"  Seed: {world_info['seed']}")
    print(f"  Size: {world_info['world_size'][0]}×{world_info['world_size'][1]} sectors")
    print(f"  Average Elevation: {world_info['average_elevation']:.1f}m")
    print(f"  Mountain Ranges: {world_info['major_mountain_ranges']}")
    print(f"  River Systems: {world_info['major_river_systems']}")
    
    print(f"\nTerrain Distribution:")
    for terrain, count in world_info['terrain_distribution'].items():
        percentage = (count / world_info['total_sectors']) * 100
        print(f"  {terrain}: {count} sectors ({percentage:.1f}%)")
    
    print(f"\nClimate Distribution:")
    for climate, count in world_info['climate_distribution'].items():
        percentage = (count / world_info['total_sectors']) * 100
        print(f"  {climate}: {count} sectors ({percentage:.1f}%)")
    
    return world_generator


def demo_regional_generation(world_generator):
    """Demonstrate regional generation."""
    print_separator("REGIONAL GENERATION DEMO")
    
    # Create regional generator
    regional_generator = RegionalScaleGenerator(world_generator)
    
    # Generate regional map for a few sectors
    test_sectors = [(0, 0), (5, 5), (10, 10)]
    
    for sector_x, sector_y in test_sectors:
        print(f"\nGenerating regional map for sector ({sector_x}, {sector_y})...")
        
        start_time = time.time()
        regional_map = regional_generator.generate_regional_map(sector_x, sector_y)
        generation_time = time.time() - start_time
        
        print(f"Regional generation completed in {generation_time:.2f} seconds")
        print(f"Generated {len(regional_map.blocks)} blocks")
        
        # Analyze regional terrain
        terrain_counts = {}
        feature_counts = {"rivers": 0, "forests": 0, "hills": 0, "settlements": 0}
        
        for block_data in regional_map.blocks.values():
            terrain = block_data.terrain_type
            terrain_counts[terrain] = terrain_counts.get(terrain, 0) + 1
            
            if block_data.has_river:
                feature_counts["rivers"] += 1
            if block_data.has_forest:
                feature_counts["forests"] += 1
            if block_data.has_hills:
                feature_counts["hills"] += 1
            if block_data.has_settlement:
                feature_counts["settlements"] += 1
        
        print(f"  Regional Terrain Distribution:")
        for terrain, count in terrain_counts.items():
            percentage = (count / len(regional_map.blocks)) * 100
            print(f"    {terrain}: {count} blocks ({percentage:.1f}%)")
        
        print(f"  Regional Features:")
        for feature, count in feature_counts.items():
            print(f"    {feature}: {count}")
    
    return regional_generator


def demo_camera_system():
    """Demonstrate multi-scale camera system."""
    print_separator("CAMERA SYSTEM DEMO")
    
    # Create camera system
    camera = MultiScaleCameraSystem(seed=12345)
    
    print("Testing camera movement across scales...")
    
    for scale in ViewScale:
        print(f"\n--- {scale.value.upper()} SCALE ---")
        camera.change_scale(scale)
        
        # Show initial position
        pos = camera.get_camera_position()
        world_coords = camera.get_current_world_coordinates()
        print(f"Initial position: {pos} (world: {world_coords})")
        
        # Test movement
        print("Testing movement...")
        for direction, (dx, dy) in [("right", (1, 0)), ("down", (0, 1)), ("left", (-1, 0)), ("up", (0, -1))]:
            success = camera.move_camera(dx, dy)
            new_pos = camera.get_camera_position()
            print(f"  Move {direction}: {success} -> {new_pos}")
        
        # Test bounds
        print("Testing bounds...")
        camera.set_camera_position(0, 0)
        blocked = not camera.move_camera(-1, -1)
        print(f"  Movement blocked at bounds: {blocked}")
        
        # Show movement stats
        stats = camera.get_movement_stats()
        print(f"  Total distance moved: {stats['total_distance_moved']:.2f}")
        print(f"  Scale changes: {stats['scale_changes']}")
    
    return camera


def demo_coordinate_conversion():
    """Demonstrate coordinate conversion between scales."""
    print_separator("COORDINATE CONVERSION DEMO")
    
    camera = MultiScaleCameraSystem(seed=12345)
    
    # Test coordinate conversion
    test_positions = [
        (ViewScale.WORLD, 3, 4),
        (ViewScale.REGIONAL, 10, 15),
        (ViewScale.LOCAL, 20, 25)
    ]
    
    print("Testing coordinate conversion:")
    for scale, x, y in test_positions:
        camera.change_scale(scale)
        camera.set_camera_position(x, y)
        
        scale_pos = camera.get_camera_position()
        world_coords = camera.get_current_world_coordinates()
        
        print(f"{scale.value.title()} scale:")
        print(f"  Scale position: {scale_pos}")
        print(f"  World coordinates: {world_coords}")
        print(f"  Tiles per unit: {camera.scale_configs[scale].pixels_per_unit}")


def demo_navigation_flow():
    """Demonstrate complete navigation flow."""
    print_separator("NAVIGATION FLOW DEMO")
    
    camera = MultiScaleCameraSystem(seed=12345)
    
    print("Simulating user navigation through scales...")
    
    # Start at world scale
    print("\n1. Starting at World scale")
    camera.change_scale(ViewScale.WORLD)
    camera.set_camera_position(5, 7)
    pos = camera.get_camera_position()
    world_coords = camera.get_current_world_coordinates()
    print(f"   World position: {pos} -> World coordinates: {world_coords}")
    
    # Drill down to regional
    print("\n2. Drilling down to Regional scale")
    camera.change_scale(ViewScale.REGIONAL)
    camera.center_camera_on_world_coordinates(*world_coords)
    pos = camera.get_camera_position()
    world_coords = camera.get_current_world_coordinates()
    print(f"   Regional position: {pos} -> World coordinates: {world_coords}")
    
    # Move around in regional
    print("\n3. Moving in Regional scale")
    camera.move_camera(3, -2)
    pos = camera.get_camera_position()
    world_coords = camera.get_current_world_coordinates()
    print(f"   New regional position: {pos} -> World coordinates: {world_coords}")
    
    # Drill down to local
    print("\n4. Drilling down to Local scale")
    camera.change_scale(ViewScale.LOCAL)
    camera.center_camera_on_world_coordinates(*world_coords)
    pos = camera.get_camera_position()
    world_coords = camera.get_current_world_coordinates()
    print(f"   Local position: {pos} -> World coordinates: {world_coords}")
    
    print("\nNavigation flow complete!")


def main():
    """Run the complete demo."""
    print("Three-Tier World Generation System Demo")
    print("======================================")
    
    try:
        # Demo world generation
        world_generator = demo_world_generation()
        
        # Demo regional generation
        regional_generator = demo_regional_generation(world_generator)
        
        # Demo camera system
        camera = demo_camera_system()
        
        # Demo coordinate conversion
        demo_coordinate_conversion()
        
        # Demo navigation flow
        demo_navigation_flow()
        
        print_separator("DEMO COMPLETE")
        print("All systems working correctly!")
        print("\nTo run the full game with graphics:")
        print("  python -m src.covenant.main")
        print("\nControls in the game:")
        print("  1/2/3 - Switch between World/Regional/Local scales")
        print("  WASD - Move camera")
        print("  Enter - Drill down to next scale")
        print("  I - Show world information")
        print("  ESC - Quit")
        
    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
