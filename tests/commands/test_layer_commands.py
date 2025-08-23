"""
Tests for layer switching commands.

This module tests the layer command functionality including
command registration and layer switching operations.
"""

import pytest
from unittest.mock import Mock, MagicMock

from covenant.commands.command_system import CommandRegistry
from covenant.commands.layer_commands import (
    LayerCommands, register_layer_commands, create_layer_command_system
)
from covenant.world.layered import WorldLayer


class TestLayerCommands:
    """Test the LayerCommands class."""
    
    def test_layer_commands_creation(self):
        """Test creating layer commands."""
        world_generator = Mock()
        layer_commands = LayerCommands(world_generator)
        
        assert layer_commands.world_generator == world_generator
    
    def test_go_to_surface(self):
        """Test going to surface layer."""
        world_generator = Mock()
        world_generator.use_layered_system = True
        world_generator.camera_3d = Mock()
        world_generator.camera_3d.change_layer.return_value = True
        
        layer_commands = LayerCommands(world_generator)
        layer_commands.go_to_surface()
        
        world_generator.camera_3d.change_layer.assert_called_once_with(WorldLayer.SURFACE)
    
    def test_go_underground(self):
        """Test going to underground layer."""
        world_generator = Mock()
        world_generator.use_layered_system = True
        world_generator.camera_3d = Mock()
        world_generator.camera_3d.change_layer.return_value = True
        
        layer_commands = LayerCommands(world_generator)
        layer_commands.go_underground()
        
        world_generator.camera_3d.change_layer.assert_called_once_with(WorldLayer.UNDERGROUND)
    
    def test_go_to_mountains(self):
        """Test going to mountain layer."""
        world_generator = Mock()
        world_generator.use_layered_system = True
        world_generator.camera_3d = Mock()
        world_generator.camera_3d.change_layer.return_value = True
        
        layer_commands = LayerCommands(world_generator)
        layer_commands.go_to_mountains()
        
        world_generator.camera_3d.change_layer.assert_called_once_with(WorldLayer.MOUNTAINS)
    
    def test_layer_commands_without_layered_system(self):
        """Test layer commands when layered system is not available."""
        world_generator = Mock()
        world_generator.use_layered_system = False
        
        layer_commands = LayerCommands(world_generator)
        
        # These should not raise exceptions
        layer_commands.go_to_surface()
        layer_commands.go_underground()
        layer_commands.go_to_mountains()
    
    def test_get_current_layer_info(self):
        """Test getting current layer information."""
        world_generator = Mock()
        world_generator.use_layered_system = True
        world_generator.camera_3d = Mock()
        world_generator.camera_3d.get_current_layer.return_value = WorldLayer.SURFACE
        
        layer_commands = LayerCommands(world_generator)
        info = layer_commands.get_current_layer_info()
        
        assert "Surface" in info
    
    def test_get_current_layer_info_without_system(self):
        """Test getting layer info when system is not available."""
        world_generator = Mock()
        world_generator.use_layered_system = False
        
        layer_commands = LayerCommands(world_generator)
        info = layer_commands.get_current_layer_info()
        
        assert "not available" in info


class TestRegisterLayerCommands:
    """Test the register_layer_commands function."""
    
    def test_register_layer_commands(self):
        """Test registering layer commands."""
        registry = CommandRegistry()
        world_generator = Mock()

        layer_commands = register_layer_commands(registry, world_generator)

        assert isinstance(layer_commands, LayerCommands)
        assert layer_commands.world_generator == world_generator

        # Check that commands were registered (without instructions panel)
        commands = registry.get_all_commands()
        assert len(commands) == 4  # surface, underground, mountains, info
        
        # Check specific commands
        surface_cmd = registry.get_command("layer.surface")
        assert surface_cmd is not None
        assert surface_cmd.name == "Go to Surface"
        assert surface_cmd.hotkey == "z"
        
        underground_cmd = registry.get_command("layer.underground")
        assert underground_cmd is not None
        assert underground_cmd.name == "Go Underground"
        assert underground_cmd.hotkey == "x"
        
        mountain_cmd = registry.get_command("layer.mountains")
        assert mountain_cmd is not None
        assert mountain_cmd.name == "Go to Elevation"
        assert mountain_cmd.hotkey == "c"
        
        info_cmd = registry.get_command("layer.info")
        assert info_cmd is not None
        assert info_cmd.name == "Current Layer Info"
        assert info_cmd.hotkey == "i"
    
    def test_hotkey_mapping(self):
        """Test that hotkeys are properly mapped."""
        registry = CommandRegistry()
        world_generator = Mock()
        
        register_layer_commands(registry, world_generator)
        
        # Test hotkey mappings
        assert registry.get_command_by_hotkey("z").id == "layer.surface"
        assert registry.get_command_by_hotkey("x").id == "layer.underground"
        assert registry.get_command_by_hotkey("c").id == "layer.mountains"
        assert registry.get_command_by_hotkey("i").id == "layer.info"
    
    def test_command_execution(self):
        """Test that registered commands can be executed."""
        registry = CommandRegistry()
        world_generator = Mock()
        world_generator.use_layered_system = True
        world_generator.camera_3d = Mock()
        world_generator.camera_3d.change_layer.return_value = True
        
        register_layer_commands(registry, world_generator)
        
        # Test executing surface command
        result = registry.execute_command("layer.surface")
        assert result is True
        world_generator.camera_3d.change_layer.assert_called_with(WorldLayer.SURFACE)
        
        # Test executing underground command
        result = registry.execute_command("layer.underground")
        assert result is True
        world_generator.camera_3d.change_layer.assert_called_with(WorldLayer.UNDERGROUND)
        
        # Test executing mountain command
        result = registry.execute_command("layer.mountains")
        assert result is True
        world_generator.camera_3d.change_layer.assert_called_with(WorldLayer.MOUNTAINS)
    
    def test_hotkey_execution(self):
        """Test that hotkeys execute the correct commands."""
        registry = CommandRegistry()
        world_generator = Mock()
        world_generator.use_layered_system = True
        world_generator.camera_3d = Mock()
        world_generator.camera_3d.change_layer.return_value = True
        
        register_layer_commands(registry, world_generator)
        
        # Test hotkey execution
        result = registry.execute_hotkey("z")
        assert result is True
        world_generator.camera_3d.change_layer.assert_called_with(WorldLayer.SURFACE)
        
        result = registry.execute_hotkey("x")
        assert result is True
        world_generator.camera_3d.change_layer.assert_called_with(WorldLayer.UNDERGROUND)
        
        result = registry.execute_hotkey("c")
        assert result is True
        world_generator.camera_3d.change_layer.assert_called_with(WorldLayer.MOUNTAINS)


class TestCreateLayerCommandSystem:
    """Test the create_layer_command_system function."""
    
    def test_create_layer_command_system(self):
        """Test creating a complete layer command system."""
        world_generator = Mock()

        registry, layer_commands = create_layer_command_system(world_generator)

        assert isinstance(registry, CommandRegistry)
        assert isinstance(layer_commands, LayerCommands)
        assert layer_commands.world_generator == world_generator

        # Check that commands are registered (without instructions panel)
        commands = registry.get_all_commands()
        assert len(commands) == 4

    def test_register_with_instructions_panel(self):
        """Test registering commands with instructions panel."""
        registry = CommandRegistry()
        world_generator = Mock()
        instructions_panel = Mock()

        layer_commands = register_layer_commands(registry, world_generator, instructions_panel)

        # Check that UI toggle command was added
        commands = registry.get_all_commands()
        assert len(commands) == 5  # 4 layer commands + 1 UI command

        # Check that UI toggle command exists
        ui_command = registry.get_command("ui.toggle_instructions")
        assert ui_command is not None
        assert ui_command.name == "Toggle Instructions Panel"
        assert ui_command.hotkey == "h"


class TestLayerCommandsIntegration:
    """Integration tests for layer commands."""
    
    def test_full_layer_switching_workflow(self):
        """Test a complete layer switching workflow."""
        # Create mock world generator with layered system
        world_generator = Mock()
        world_generator.use_layered_system = True
        world_generator.camera_3d = Mock()
        
        # Track layer changes
        layer_changes = []
        def track_layer_change(layer):
            layer_changes.append(layer)
            return True
        
        world_generator.camera_3d.change_layer.side_effect = track_layer_change
        world_generator.camera_3d.get_current_layer.return_value = WorldLayer.SURFACE
        
        # Create command system
        registry, layer_commands = create_layer_command_system(world_generator)
        
        # Test switching to underground
        registry.execute_hotkey("x")
        assert len(layer_changes) == 1
        assert layer_changes[0] == WorldLayer.UNDERGROUND
        
        # Test switching to mountains
        registry.execute_hotkey("c")
        assert len(layer_changes) == 2
        assert layer_changes[1] == WorldLayer.MOUNTAINS
        
        # Test switching back to surface
        registry.execute_hotkey("z")
        assert len(layer_changes) == 3
        assert layer_changes[2] == WorldLayer.SURFACE
    
    def test_command_search_and_execution(self):
        """Test searching for and executing layer commands."""
        world_generator = Mock()
        world_generator.use_layered_system = True
        world_generator.camera_3d = Mock()
        world_generator.camera_3d.change_layer.return_value = True
        
        registry, _ = create_layer_command_system(world_generator)
        
        # Search for layer commands
        results = registry.search_commands("layer")
        assert len(results) == 4
        
        # Search for specific commands
        surface_results = registry.search_commands("surface")
        assert len(surface_results) == 1
        assert surface_results[0].id == "layer.surface"
        
        underground_results = registry.search_commands("underground")
        assert len(underground_results) == 1
        assert underground_results[0].id == "layer.underground"
        
        elevation_results = registry.search_commands("elevation")
        assert len(elevation_results) == 1
        assert elevation_results[0].id == "layer.mountains"
