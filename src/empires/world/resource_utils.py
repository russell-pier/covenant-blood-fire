"""
Utility functions for working with resources in the layered world system.

This module provides helper functions for accessing, harvesting, and managing
resources across the three world layers.
"""

from typing import Optional, List, Dict, Tuple
from .layered import WorldLayer, LayeredTerrainData, TerrainData
from .resource_types import ResourceNode, ResourceType, get_resource_value, is_renewable


def get_resource_at_position(
    layered_terrain: LayeredTerrainData, 
    layer: WorldLayer
) -> Optional[ResourceNode]:
    """
    Get the resource node at a specific position and layer.
    
    Args:
        layered_terrain: Terrain data for the position
        layer: Which layer to check for resources
        
    Returns:
        ResourceNode if present, None otherwise
    """
    if layer == WorldLayer.SURFACE:
        return layered_terrain.surface.resource
    elif layer == WorldLayer.UNDERGROUND:
        return layered_terrain.underground.resource
    elif layer == WorldLayer.MOUNTAINS and layered_terrain.mountains:
        return layered_terrain.mountains.resource
    
    return None


def has_resource_at_position(
    layered_terrain: LayeredTerrainData, 
    layer: WorldLayer
) -> bool:
    """
    Check if there's a resource at a specific position and layer.
    
    Args:
        layered_terrain: Terrain data for the position
        layer: Which layer to check for resources
        
    Returns:
        True if resource exists, False otherwise
    """
    return get_resource_at_position(layered_terrain, layer) is not None


def harvest_resource(
    layered_terrain: LayeredTerrainData, 
    layer: WorldLayer
) -> Optional[Dict]:
    """
    Harvest a resource from a specific position and layer.
    
    Args:
        layered_terrain: Terrain data for the position
        layer: Which layer to harvest from
        
    Returns:
        Dictionary with harvest results or None if no resource
    """
    resource = get_resource_at_position(layered_terrain, layer)
    
    if not resource:
        return None
    
    # Calculate harvest yield
    base_yield = resource.yield_amount
    resource_value = get_resource_value(resource.resource_type, resource.rarity)
    
    harvest_result = {
        'resource_type': resource.resource_type,
        'amount': base_yield,
        'value': resource_value,
        'rarity': resource.rarity,
        'renewable': resource.respawns
    }
    
    # Remove resource if not renewable
    if not resource.respawns:
        _remove_resource_from_terrain(layered_terrain, layer)
    
    return harvest_result


def _remove_resource_from_terrain(
    layered_terrain: LayeredTerrainData, 
    layer: WorldLayer
) -> None:
    """
    Remove a resource from terrain data and restore original character.
    
    Args:
        layered_terrain: Terrain data for the position
        layer: Which layer to remove resource from
    """
    if layer == WorldLayer.SURFACE:
        terrain_data = layered_terrain.surface
    elif layer == WorldLayer.UNDERGROUND:
        terrain_data = layered_terrain.underground
    elif layer == WorldLayer.MOUNTAINS and layered_terrain.mountains:
        terrain_data = layered_terrain.mountains
    else:
        return
    
    # Clear resource data
    terrain_data.resource = None
    
    # Restore original terrain character (this would need terrain type mapping)
    # For now, use a generic character
    terrain_data.char = _get_default_terrain_char(terrain_data.terrain_type)


def _get_default_terrain_char(terrain_type) -> str:
    """
    Get the default character for a terrain type.
    
    Args:
        terrain_type: The terrain type
        
    Returns:
        Default character for the terrain
    """
    # This is a simplified mapping - in practice, you'd use the terrain mapper
    terrain_chars = {
        'grassland': '.',
        'forest': '♠',
        'hills': '^',
        'mountains': '▲',
        'caves': '○',
        'cave_tunnel': '·',
        'water': '~',
        'desert': '∘'
    }
    
    return terrain_chars.get(terrain_type.value if hasattr(terrain_type, 'value') else str(terrain_type), '.')


def get_all_resources_in_chunk(
    chunk_data: Dict[Tuple[int, int], LayeredTerrainData]
) -> Dict[WorldLayer, List[Tuple[Tuple[int, int], ResourceNode]]]:
    """
    Get all resources in a chunk organized by layer.
    
    Args:
        chunk_data: Terrain data for the entire chunk
        
    Returns:
        Dictionary mapping layers to lists of (position, resource) tuples
    """
    layered_resources = {
        WorldLayer.SURFACE: [],
        WorldLayer.UNDERGROUND: [],
        WorldLayer.MOUNTAINS: []
    }
    
    for position, layered_terrain in chunk_data.items():
        for layer in WorldLayer:
            resource = get_resource_at_position(layered_terrain, layer)
            if resource:
                layered_resources[layer].append((position, resource))
    
    return layered_resources


def count_resources_by_type(
    chunk_data: Dict[Tuple[int, int], LayeredTerrainData]
) -> Dict[ResourceType, int]:
    """
    Count resources by type in a chunk.
    
    Args:
        chunk_data: Terrain data for the entire chunk
        
    Returns:
        Dictionary mapping resource types to counts
    """
    resource_counts = {}
    
    for layered_terrain in chunk_data.values():
        for layer in WorldLayer:
            resource = get_resource_at_position(layered_terrain, layer)
            if resource:
                resource_type = resource.resource_type
                resource_counts[resource_type] = resource_counts.get(resource_type, 0) + 1
    
    return resource_counts


def get_resource_summary(
    chunk_data: Dict[Tuple[int, int], LayeredTerrainData]
) -> Dict:
    """
    Get a summary of all resources in a chunk.
    
    Args:
        chunk_data: Terrain data for the entire chunk
        
    Returns:
        Dictionary with resource summary information
    """
    layered_resources = get_all_resources_in_chunk(chunk_data)
    resource_counts = count_resources_by_type(chunk_data)
    
    total_resources = sum(len(resources) for resources in layered_resources.values())
    
    summary = {
        'total_resources': total_resources,
        'by_layer': {
            layer.name: len(resources) 
            for layer, resources in layered_resources.items()
        },
        'by_type': {
            resource_type.value: count 
            for resource_type, count in resource_counts.items()
        },
        'renewable_count': sum(
            1 for layered_terrain in chunk_data.values()
            for layer in WorldLayer
            if (resource := get_resource_at_position(layered_terrain, layer)) 
            and resource.respawns
        ),
        'finite_count': sum(
            1 for layered_terrain in chunk_data.values()
            for layer in WorldLayer
            if (resource := get_resource_at_position(layered_terrain, layer)) 
            and not resource.respawns
        )
    }
    
    return summary


def can_access_layer(
    layered_terrain: LayeredTerrainData, 
    target_layer: WorldLayer
) -> bool:
    """
    Check if a layer can be accessed from the surface.
    
    Args:
        layered_terrain: Terrain data for the position
        target_layer: Layer to check access for
        
    Returns:
        True if layer is accessible, False otherwise
    """
    if target_layer == WorldLayer.SURFACE:
        return True
    elif target_layer == WorldLayer.UNDERGROUND:
        return layered_terrain.has_cave_entrance
    elif target_layer == WorldLayer.MOUNTAINS:
        return layered_terrain.has_mountain_access
    
    return False


def get_accessible_resources(
    layered_terrain: LayeredTerrainData
) -> List[Tuple[WorldLayer, ResourceNode]]:
    """
    Get all accessible resources at a position.
    
    Args:
        layered_terrain: Terrain data for the position
        
    Returns:
        List of (layer, resource) tuples for accessible resources
    """
    accessible_resources = []
    
    for layer in WorldLayer:
        if can_access_layer(layered_terrain, layer):
            resource = get_resource_at_position(layered_terrain, layer)
            if resource:
                accessible_resources.append((layer, resource))
    
    return accessible_resources
