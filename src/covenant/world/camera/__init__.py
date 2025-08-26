"""
Multi-scale camera system for three-tier world generation.

This package contains the camera and rendering systems for managing
view across World, Regional, and Local scales.
"""

from .multi_scale_camera import MultiScaleCameraSystem

# Note: viewport_renderer requires tcod and is not imported by default
# from .viewport_renderer import MultiScaleViewportRenderer

__all__ = [
    'MultiScaleCameraSystem',
    # 'MultiScaleViewportRenderer'  # Commented out due to tcod dependency
]
