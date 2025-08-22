"""
Tests for the command system and command palette.

This module tests the core command system functionality including
command registration, execution, hotkeys, and the command palette.
"""

import pytest
from unittest.mock import Mock, MagicMock
import tcod

from empires.commands.command_system import (
    Command, CommandRegistry, CommandPalette, create_default_command_system
)


class TestCommand:
    """Test the Command dataclass."""
    
    def test_command_creation(self):
        """Test creating a command."""
        action = Mock()
        command = Command(
            id="test.command",
            name="Test Command",
            description="A test command",
            hotkey="t",
            category="Test",
            action=action,
            enabled=True
        )
        
        assert command.id == "test.command"
        assert command.name == "Test Command"
        assert command.description == "A test command"
        assert command.hotkey == "t"
        assert command.category == "Test"
        assert command.action == action
        assert command.enabled is True
    
    def test_command_defaults(self):
        """Test command with default values."""
        command = Command(
            id="test.simple",
            name="Simple Command",
            description="A simple command"
        )
        
        assert command.hotkey is None
        assert command.category == "General"
        assert command.action is None
        assert command.enabled is True


class TestCommandRegistry:
    """Test the CommandRegistry class."""
    
    def test_registry_creation(self):
        """Test creating a command registry."""
        registry = CommandRegistry()
        
        assert len(registry.get_all_commands()) == 0
    
    def test_register_command(self):
        """Test registering a command."""
        registry = CommandRegistry()
        action = Mock()
        command = Command(
            id="test.command",
            name="Test Command",
            description="A test command",
            hotkey="t",
            action=action
        )
        
        registry.register_command(command)
        
        assert len(registry.get_all_commands()) == 1
        assert registry.get_command("test.command") == command
        assert registry.get_command_by_hotkey("t") == command
    
    def test_unregister_command(self):
        """Test unregistering a command."""
        registry = CommandRegistry()
        command = Command(
            id="test.command",
            name="Test Command",
            description="A test command",
            hotkey="t"
        )
        
        registry.register_command(command)
        assert len(registry.get_all_commands()) == 1
        
        registry.unregister_command("test.command")
        assert len(registry.get_all_commands()) == 0
        assert registry.get_command("test.command") is None
        assert registry.get_command_by_hotkey("t") is None
    
    def test_hotkey_case_insensitive(self):
        """Test that hotkeys are case insensitive."""
        registry = CommandRegistry()
        command = Command(
            id="test.command",
            name="Test Command",
            description="A test command",
            hotkey="T"
        )
        
        registry.register_command(command)
        
        assert registry.get_command_by_hotkey("t") == command
        assert registry.get_command_by_hotkey("T") == command
    
    def test_search_commands(self):
        """Test searching commands."""
        registry = CommandRegistry()
        
        command1 = Command(
            id="test.first",
            name="First Command",
            description="First test command",
            category="Test"
        )
        command2 = Command(
            id="test.second", 
            name="Second Command",
            description="Second test command",
            category="Test"
        )
        command3 = Command(
            id="other.command",
            name="Other Command",
            description="Different command",
            category="Other"
        )
        
        registry.register_command(command1)
        registry.register_command(command2)
        registry.register_command(command3)
        
        # Search by name
        results = registry.search_commands("first")
        assert len(results) == 1
        assert results[0] == command1
        
        # Search by description
        results = registry.search_commands("test")
        assert len(results) == 2
        assert command1 in results
        assert command2 in results
        
        # Search by category
        results = registry.search_commands("other")
        assert len(results) == 1
        assert results[0] == command3
    
    def test_execute_command(self):
        """Test executing a command."""
        registry = CommandRegistry()
        action = Mock()
        command = Command(
            id="test.command",
            name="Test Command",
            description="A test command",
            action=action
        )
        
        registry.register_command(command)
        
        result = registry.execute_command("test.command")
        assert result is True
        action.assert_called_once()
    
    def test_execute_nonexistent_command(self):
        """Test executing a nonexistent command."""
        registry = CommandRegistry()
        
        result = registry.execute_command("nonexistent")
        assert result is False
    
    def test_execute_disabled_command(self):
        """Test executing a disabled command."""
        registry = CommandRegistry()
        action = Mock()
        command = Command(
            id="test.command",
            name="Test Command",
            description="A test command",
            action=action,
            enabled=False
        )
        
        registry.register_command(command)
        
        result = registry.execute_command("test.command")
        assert result is False
        action.assert_not_called()
    
    def test_execute_hotkey(self):
        """Test executing a command by hotkey."""
        registry = CommandRegistry()
        action = Mock()
        command = Command(
            id="test.command",
            name="Test Command",
            description="A test command",
            hotkey="t",
            action=action
        )
        
        registry.register_command(command)
        
        result = registry.execute_hotkey("t")
        assert result is True
        action.assert_called_once()


class TestCommandPalette:
    """Test the CommandPalette class."""
    
    def test_palette_creation(self):
        """Test creating a command palette."""
        registry = CommandRegistry()
        palette = CommandPalette(registry)
        
        assert palette.registry == registry
        assert palette.is_open is False
        assert palette.search_query == ""
        assert palette.selected_index == 0
    
    def test_open_close_palette(self):
        """Test opening and closing the palette."""
        registry = CommandRegistry()
        palette = CommandPalette(registry)
        
        palette.open()
        assert palette.is_open is True
        
        palette.close()
        assert palette.is_open is False
        assert palette.search_query == ""
        assert palette.selected_index == 0
    
    def test_handle_input_when_closed(self):
        """Test that input is not handled when palette is closed."""
        registry = CommandRegistry()
        palette = CommandPalette(registry)
        
        event = Mock()
        event.sym = tcod.event.KeySym.ESCAPE
        
        result = palette.handle_input(event)
        assert result is False
    
    def test_handle_escape_key(self):
        """Test handling escape key to close palette."""
        registry = CommandRegistry()
        palette = CommandPalette(registry)
        
        palette.open()
        
        event = Mock()
        event.sym = tcod.event.KeySym.ESCAPE
        
        result = palette.handle_input(event)
        assert result is True
        assert palette.is_open is False
    
    def test_handle_return_key(self):
        """Test handling return key to execute command."""
        registry = CommandRegistry()
        action = Mock()
        command = Command(
            id="test.command",
            name="Test Command",
            description="A test command",
            action=action
        )
        registry.register_command(command)
        
        palette = CommandPalette(registry)
        palette.open()
        
        event = Mock()
        event.sym = tcod.event.KeySym.RETURN
        
        result = palette.handle_input(event)
        assert result is True
        assert palette.is_open is False
        action.assert_called_once()
    
    def test_handle_navigation_keys(self):
        """Test handling up/down navigation keys."""
        registry = CommandRegistry()
        command1 = Command(id="test.1", name="Command 1", description="First")
        command2 = Command(id="test.2", name="Command 2", description="Second")
        registry.register_command(command1)
        registry.register_command(command2)
        
        palette = CommandPalette(registry)
        palette.open()
        
        # Test down key
        event = Mock()
        event.sym = tcod.event.KeySym.DOWN
        
        result = palette.handle_input(event)
        assert result is True
        assert palette.selected_index == 1
        
        # Test up key
        event.sym = tcod.event.KeySym.UP
        result = palette.handle_input(event)
        assert result is True
        assert palette.selected_index == 0
    
    def test_handle_text_input(self):
        """Test handling text input for search."""
        registry = CommandRegistry()
        palette = CommandPalette(registry)
        palette.open()

        # Test character input (letter)
        event = Mock()
        event.sym = tcod.event.KeySym.T

        result = palette.handle_input(event)
        assert result is True
        assert palette.search_query == "t"

        # Test backspace
        event.sym = tcod.event.KeySym.BACKSPACE

        result = palette.handle_input(event)
        assert result is True
        assert palette.search_query == ""


class TestCommandSystemIntegration:
    """Integration tests for the command system."""
    
    def test_create_default_command_system(self):
        """Test creating default command system."""
        registry, palette = create_default_command_system()
        
        assert isinstance(registry, CommandRegistry)
        assert isinstance(palette, CommandPalette)
        assert palette.registry == registry
    
    def test_full_workflow(self):
        """Test a complete command workflow."""
        registry = CommandRegistry()
        palette = CommandPalette(registry)
        
        # Create and register a command
        executed = []
        def test_action():
            executed.append("test")
        
        command = Command(
            id="test.workflow",
            name="Workflow Test",
            description="Test workflow command",
            hotkey="w",
            action=test_action
        )
        registry.register_command(command)
        
        # Test direct execution
        result = registry.execute_command("test.workflow")
        assert result is True
        assert len(executed) == 1
        
        # Test hotkey execution
        result = registry.execute_hotkey("w")
        assert result is True
        assert len(executed) == 2
        
        # Test palette execution
        palette.open()
        palette.search_query = "workflow"
        palette._update_filtered_commands()
        
        assert len(palette.filtered_commands) == 1
        assert palette.filtered_commands[0] == command
        
        # Simulate return key press
        event = Mock()
        event.sym = tcod.event.KeySym.RETURN
        
        result = palette.handle_input(event)
        assert result is True
        assert palette.is_open is False
        assert len(executed) == 3
