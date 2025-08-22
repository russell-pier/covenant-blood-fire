"""
Configuration system for Covenant: Blood & Fire.

Loads and manages all configuration files using TOML format.
Provides centralized access to environmental, visual, and other configs.
"""

import os
import tomllib
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any, Union
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"


@dataclass
class VisualConfig:
    """Configuration for visual representation of a tile or entity."""
    characters: List[str]
    foreground_color: Tuple[int, int, int]
    background_color: Optional[Tuple[int, int, int]] = None
    passable: Optional[bool] = None
    movement_cost: Optional[Union[float, str]] = None


@dataclass
class EnvironmentalRule:
    """Rule for mapping environmental conditions to terrain types."""
    name: str
    terrain_type: str
    conditions: Dict[str, float]


class ConfigManager:
    """Manages all configuration loading and access."""
    
    def __init__(self):
        """Initialize the config manager and load all configs."""
        self.environmental_config: Dict[str, Any] = {}
        self.visual_config: Dict[str, Any] = {}
        self._load_all_configs()
    
    def _load_all_configs(self) -> None:
        """Load all TOML configuration files."""
        try:
            # Load environmental config
            env_path = CONFIG_DIR / "environmental.toml"
            if env_path.exists():
                with open(env_path, "rb") as f:
                    self.environmental_config = tomllib.load(f)
            
            # Load visual config
            visual_path = CONFIG_DIR / "visual.toml"
            if visual_path.exists():
                with open(visual_path, "rb") as f:
                    self.visual_config = tomllib.load(f)
                    
        except Exception as e:
            print(f"Warning: Failed to load config files: {e}")
            # Fall back to empty configs - systems should handle this gracefully
            self.environmental_config = {}
            self.visual_config = {}
    
    def get_terrain_visual(self, terrain_type: str) -> Optional[VisualConfig]:
        """Get visual configuration for a terrain type."""
        terrain_configs = self.visual_config.get("terrain", {})
        terrain_config = terrain_configs.get(terrain_type)
        
        if not terrain_config:
            return None
        
        # Convert movement_cost string to float if needed
        movement_cost = terrain_config.get("movement_cost")
        if movement_cost == "inf":
            movement_cost = float('inf')
        
        return VisualConfig(
            characters=terrain_config.get("characters", ["?"]),
            foreground_color=tuple(terrain_config.get("foreground_color", [255, 255, 255])),
            background_color=tuple(terrain_config.get("background_color")) if terrain_config.get("background_color") else None,
            passable=terrain_config.get("passable"),
            movement_cost=movement_cost
        )
    
    def get_animal_visual(self, animal_type: str, state: str) -> Optional[VisualConfig]:
        """Get visual configuration for an animal in a specific state."""
        animal_configs = self.visual_config.get("animals", {})
        animal_config = animal_configs.get(animal_type, {})
        state_config = animal_config.get(state)
        
        if not state_config:
            return None
        
        return VisualConfig(
            characters=state_config.get("characters", ["?"]),
            foreground_color=tuple(state_config.get("foreground_color", [255, 255, 255])),
            background_color=tuple(state_config.get("background_color")) if state_config.get("background_color") else None
        )
    
    def get_ui_visual(self, element: str) -> Optional[VisualConfig]:
        """Get visual configuration for a UI element."""
        ui_configs = self.visual_config.get("ui", {})
        element_config = ui_configs.get(element)
        
        if not element_config:
            return None
        
        return VisualConfig(
            characters=element_config.get("characters", ["?"]),
            foreground_color=tuple(element_config.get("foreground_color", [255, 255, 255])),
            background_color=tuple(element_config.get("background_color")) if element_config.get("background_color") else None
        )
    
    def get_environmental_rules(self) -> List[EnvironmentalRule]:
        """Get environmental mapping rules."""
        rules = []
        mapping_config = self.environmental_config.get("environmental_mapping", {})
        
        # Get main rules
        for rule_data in mapping_config.get("rules", []):
            rules.append(EnvironmentalRule(
                name=rule_data["name"],
                terrain_type=rule_data["terrain_type"],
                conditions=rule_data["conditions"]
            ))
        
        # Get default rules
        defaults = mapping_config.get("defaults", {})
        for rule_data in defaults.get("rules", []):
            rules.append(EnvironmentalRule(
                name=rule_data["name"],
                terrain_type=rule_data["terrain_type"],
                conditions=rule_data["conditions"]
            ))
        
        return rules
    
    def get_noise_config(self) -> Dict[str, Any]:
        """Get noise generation configuration."""
        return self.environmental_config.get("noise", {})
    
    def reload_configs(self) -> None:
        """Reload all configuration files (useful for development)."""
        self._load_all_configs()


# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global config manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def reload_configs() -> None:
    """Reload all configuration files."""
    global _config_manager
    if _config_manager is not None:
        _config_manager.reload_configs()


# Convenience functions for common config access
def get_terrain_visual(terrain_type: str) -> Optional[VisualConfig]:
    """Get visual configuration for a terrain type."""
    return get_config_manager().get_terrain_visual(terrain_type)


def get_animal_visual(animal_type: str, state: str) -> Optional[VisualConfig]:
    """Get visual configuration for an animal in a specific state."""
    return get_config_manager().get_animal_visual(animal_type, state)


def get_ui_visual(element: str) -> Optional[VisualConfig]:
    """Get visual configuration for a UI element."""
    return get_config_manager().get_ui_visual(element)
