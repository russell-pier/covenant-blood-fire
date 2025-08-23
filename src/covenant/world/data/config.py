"""
Configuration system for world generation.

This module handles loading configuration from files and providing
default values for world generation parameters including seeds.
"""

import os
import random
import time
from typing import Optional, Dict, Any
import toml


class WorldConfig:
    """Configuration manager for world generation system."""
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize configuration system.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = config_dir
        self._config_cache: Dict[str, Any] = {}
        self._load_configs()
    
    def _load_configs(self) -> None:
        """Load all configuration files from config directory."""
        config_files = [
            "environmental.toml",
            "visual.toml",
            "world.toml"  # New config file for world generation
        ]
        
        for config_file in config_files:
            config_path = os.path.join(self.config_dir, config_file)
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        config_data = toml.load(f)
                        self._config_cache[config_file] = config_data
                except Exception as e:
                    print(f"Warning: Could not load {config_file}: {e}")
    
    def get_world_seed(self) -> int:
        """
        Get world generation seed from config or generate random one.
        
        Returns:
            Seed value for world generation
        """
        # Check if world.toml exists and has a seed
        world_config = self._config_cache.get("world.toml", {})
        if "world" in world_config and "seed" in world_config["world"]:
            return world_config["world"]["seed"]
        
        # Check for dev seed in environmental config
        env_config = self._config_cache.get("environmental.toml", {})
        if "development" in env_config and "seed" in env_config["development"]:
            return env_config["development"]["seed"]
        
        # Generate random seed based on current time
        return int(time.time() * 1000) % (2**31 - 1)
    
    def get_world_size(self) -> tuple[int, int]:
        """
        Get world size in sectors from config.
        
        Returns:
            Tuple of (width, height) in sectors
        """
        world_config = self._config_cache.get("world.toml", {})
        if "world" in world_config and "size" in world_config["world"]:
            size = world_config["world"]["size"]
            if isinstance(size, list) and len(size) == 2:
                return tuple(size)
        
        # Default world size
        return (16, 16)
    
    def get_noise_config(self) -> Dict[str, Any]:
        """
        Get noise generation configuration.
        
        Returns:
            Dictionary of noise configuration parameters
        """
        env_config = self._config_cache.get("environmental.toml", {})
        return env_config.get("noise", {})
    
    def get_environmental_mapping(self) -> Dict[str, Any]:
        """
        Get environmental mapping configuration.
        
        Returns:
            Dictionary of environmental mapping rules
        """
        env_config = self._config_cache.get("environmental.toml", {})
        return env_config.get("environmental_mapping", {})
    
    def is_development_mode(self) -> bool:
        """
        Check if running in development mode.
        
        Returns:
            True if development mode is enabled
        """
        world_config = self._config_cache.get("world.toml", {})
        if "development" in world_config:
            return world_config["development"].get("enabled", False)
        
        # Check environmental config as fallback
        env_config = self._config_cache.get("environmental.toml", {})
        if "development" in env_config:
            return env_config["development"].get("enabled", False)
        
        return False
    
    def get_cache_settings(self) -> Dict[str, Any]:
        """
        Get caching configuration.
        
        Returns:
            Dictionary of cache settings
        """
        world_config = self._config_cache.get("world.toml", {})
        return world_config.get("cache", {
            "world_lifetime": 300.0,
            "regional_lifetime": 60.0,
            "local_lifetime": 10.0,
            "max_world_maps": 1,
            "max_regional_maps": 4,
            "max_local_chunks": 64
        })


# Global configuration instance
_global_config: Optional[WorldConfig] = None


def get_world_config() -> WorldConfig:
    """
    Get the global world configuration instance.
    
    Returns:
        WorldConfig instance
    """
    global _global_config
    if _global_config is None:
        _global_config = WorldConfig()
    return _global_config


def create_world_config_file() -> None:
    """Create a default world.toml configuration file if it doesn't exist."""
    config_path = os.path.join("config", "world.toml")
    
    if not os.path.exists(config_path):
        os.makedirs("config", exist_ok=True)
        
        default_config = """# World Generation Configuration

[world]
# World seed for reproducible generation (comment out for random)
# seed = 12345

# World size in sectors (each sector is 16,384 x 16,384 tiles)
size = [16, 16]

[development]
# Enable development mode features
enabled = true

# Development seed (used if world.seed is not set)
seed = 42

[cache]
# Cache lifetimes in seconds
world_lifetime = 300.0
regional_lifetime = 60.0
local_lifetime = 10.0

# Maximum cached items
max_world_maps = 1
max_regional_maps = 4
max_local_chunks = 64

[performance]
# Performance tuning
enable_multithreading = false
chunk_generation_batch_size = 4
background_generation = true
"""
        
        with open(config_path, 'w') as f:
            f.write(default_config)
        
        print(f"Created default world configuration at {config_path}")


# Initialize config file on import if in development
if __name__ != "__main__":
    try:
        config = get_world_config()
        if config.is_development_mode():
            create_world_config_file()
    except Exception:
        pass  # Ignore errors during import
