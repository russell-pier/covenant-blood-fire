"""
Tests for the autonomous animals system.

This module contains comprehensive tests for the animal flocking behavior,
including Vector2D math, boid algorithms, animal behaviors, and integration tests.
"""

import math
import pytest
import time
from unittest.mock import Mock, patch

from src.covenant.world.animals import (
    Vector2D, Animal, Sheep, Cow, Herd, AnimalManager,
    AnimalType, AnimalState
)
from src.covenant.world.terrain import TerrainType


class TestVector2D:
    """Test the Vector2D class for mathematical operations."""
    
    def test_vector_creation(self):
        """Test vector creation and basic properties."""
        v = Vector2D(3.0, 4.0)
        assert v.x == 3.0
        assert v.y == 4.0
    
    def test_vector_addition(self):
        """Test vector addition."""
        v1 = Vector2D(1.0, 2.0)
        v2 = Vector2D(3.0, 4.0)
        result = v1 + v2
        assert result.x == 4.0
        assert result.y == 6.0
    
    def test_vector_subtraction(self):
        """Test vector subtraction."""
        v1 = Vector2D(5.0, 7.0)
        v2 = Vector2D(2.0, 3.0)
        result = v1 - v2
        assert result.x == 3.0
        assert result.y == 4.0
    
    def test_vector_scalar_multiplication(self):
        """Test vector scalar multiplication."""
        v = Vector2D(2.0, 3.0)
        result = v * 2.5
        assert result.x == 5.0
        assert result.y == 7.5
    
    def test_vector_magnitude(self):
        """Test vector magnitude calculation."""
        v = Vector2D(3.0, 4.0)
        assert v.magnitude() == 5.0
        
        v_zero = Vector2D(0.0, 0.0)
        assert v_zero.magnitude() == 0.0
    
    def test_vector_normalize(self):
        """Test vector normalization."""
        v = Vector2D(3.0, 4.0)
        normalized = v.normalize()
        assert abs(normalized.magnitude() - 1.0) < 1e-10
        assert abs(normalized.x - 0.6) < 1e-10
        assert abs(normalized.y - 0.8) < 1e-10
        
        # Test zero vector normalization
        v_zero = Vector2D(0.0, 0.0)
        normalized_zero = v_zero.normalize()
        assert normalized_zero.x == 0.0
        assert normalized_zero.y == 0.0
    
    def test_vector_limit(self):
        """Test vector magnitude limiting."""
        v = Vector2D(6.0, 8.0)  # magnitude = 10
        limited = v.limit(5.0)
        assert abs(limited.magnitude() - 5.0) < 1e-10
        
        # Test vector already within limit
        v_small = Vector2D(1.0, 1.0)
        limited_small = v_small.limit(5.0)
        assert limited_small.x == 1.0
        assert limited_small.y == 1.0


class TestSheep:
    """Test the Sheep class implementation."""
    
    def test_sheep_creation(self):
        """Test sheep creation with proper parameters."""
        sheep = Sheep(id=1, x=10.0, y=20.0)
        assert sheep.id == 1
        assert sheep.x == 10.0
        assert sheep.y == 20.0
        assert sheep.animal_type == AnimalType.SHEEP
        assert sheep.state == AnimalState.GRAZING
        assert 0.3 <= sheep.max_speed <= 0.4  # Random range
        assert sheep.separation_radius == 2.0
    
    def test_sheep_render_chars(self):
        """Test sheep render characters for different states."""
        sheep = Sheep(id=1, x=0.0, y=0.0)
        
        sheep.state = AnimalState.GRAZING
        assert sheep.get_render_char() == "♪"
        
        sheep.state = AnimalState.MOVING
        assert sheep.get_render_char() == "♫"
        
        sheep.state = AnimalState.FLEEING
        assert sheep.get_render_char() == "♬"
        
        sheep.state = AnimalState.IDLE
        assert sheep.get_render_char() == "♩"
    
    def test_sheep_color(self):
        """Test sheep color."""
        sheep = Sheep(id=1, x=0.0, y=0.0)
        assert sheep.get_color() == (255, 255, 255)  # White
    
    def test_sheep_state_transitions(self):
        """Test sheep state transition logic."""
        sheep = Sheep(id=1, x=0.0, y=0.0)
        
        # Test grazing to moving transition
        sheep.state = AnimalState.GRAZING
        sheep.state_timer = 10.0  # Longer than max grazing time
        sheep._update_state()
        assert sheep.state == AnimalState.MOVING
        assert sheep.state_timer == 0.0
        
        # Test moving to grazing/idle transition
        sheep.state = AnimalState.MOVING
        sheep.state_timer = 10.0  # Longer than max moving time
        with patch('random.random', return_value=0.5):  # 70% chance for grazing
            sheep._update_state()
        assert sheep.state == AnimalState.GRAZING
        assert sheep.state_timer == 0.0


class TestCow:
    """Test the Cow class implementation."""
    
    def test_cow_creation(self):
        """Test cow creation with proper parameters."""
        cow = Cow(id=1, x=10.0, y=20.0)
        assert cow.id == 1
        assert cow.x == 10.0
        assert cow.y == 20.0
        assert cow.animal_type == AnimalType.COW
        assert cow.state == AnimalState.GRAZING
        assert 0.1 <= cow.max_speed <= 0.2  # Slower than sheep
        assert cow.separation_radius == 3.0  # Larger than sheep
    
    def test_cow_render_chars(self):
        """Test cow render characters for different states."""
        cow = Cow(id=1, x=0.0, y=0.0)
        
        cow.state = AnimalState.GRAZING
        assert cow.get_render_char() == "♄"
        
        cow.state = AnimalState.MOVING
        assert cow.get_render_char() == "♅"
        
        cow.state = AnimalState.FLEEING
        assert cow.get_render_char() == "♆"
        
        cow.state = AnimalState.IDLE
        assert cow.get_render_char() == "♇"
    
    def test_cow_color(self):
        """Test cow color."""
        cow = Cow(id=1, x=0.0, y=0.0)
        assert cow.get_color() == (0, 0, 0)  # Black


class TestBoidAlgorithms:
    """Test the core boid flocking algorithms."""
    
    def test_separation_force(self):
        """Test separation behavior."""
        sheep1 = Sheep(id=1, x=0.0, y=0.0)
        sheep2 = Sheep(id=2, x=1.0, y=0.0)  # Close neighbor
        sheep3 = Sheep(id=3, x=10.0, y=0.0)  # Far neighbor
        
        nearby_animals = [sheep2, sheep3]
        separation_force = sheep1._separation(nearby_animals)
        
        # Should push away from close neighbor (sheep2)
        assert separation_force.x < 0  # Push left away from sheep2
        assert abs(separation_force.y) < 0.1  # Minimal Y component
    
    def test_alignment_force(self):
        """Test alignment behavior."""
        sheep1 = Sheep(id=1, x=0.0, y=0.0)
        sheep1.velocity = Vector2D(0.0, 0.0)
        
        sheep2 = Sheep(id=2, x=2.0, y=0.0)
        sheep2.velocity = Vector2D(1.0, 0.0)  # Moving right
        
        nearby_animals = [sheep2]
        alignment_force = sheep1._alignment(nearby_animals)
        
        # Should align with sheep2's velocity
        assert alignment_force.x > 0  # Should move right
    
    def test_cohesion_force(self):
        """Test cohesion behavior."""
        sheep1 = Sheep(id=1, x=0.0, y=0.0)
        sheep2 = Sheep(id=2, x=4.0, y=0.0)  # To the right
        sheep3 = Sheep(id=3, x=4.0, y=4.0)  # To the right and up
        
        nearby_animals = [sheep2, sheep3]
        cohesion_force = sheep1._cohesion(nearby_animals)
        
        # Should move toward center of mass (4, 2)
        assert cohesion_force.x > 0  # Move right
        assert cohesion_force.y > 0  # Move up
    
    def test_obstacle_avoidance(self):
        """Test obstacle avoidance behavior."""
        sheep = Sheep(id=1, x=5.0, y=5.0)
        
        # Create terrain data with water obstacle
        terrain_data = {}
        for x in range(10):
            for y in range(10):
                if x == 4 and y == 5:  # Water to the left
                    terrain_data[(x, y)] = Mock()
                    terrain_data[(x, y)].terrain_type.value = 'water'
                else:
                    terrain_data[(x, y)] = Mock()
                    terrain_data[(x, y)].terrain_type.value = 'grass'
        
        avoidance_force = sheep._avoid_obstacles(terrain_data)
        
        # Should push away from water (to the right)
        assert avoidance_force.x > 0


class TestHerd:
    """Test the Herd class functionality."""
    
    def test_herd_creation(self):
        """Test herd creation and animal spawning."""
        herd = Herd(AnimalType.SHEEP, center_x=10.0, center_y=10.0, herd_size=5)
        
        assert len(herd.animals) == 5
        assert all(animal.animal_type == AnimalType.SHEEP for animal in herd.animals)
        
        # Check animals are spread around center
        for animal in herd.animals:
            distance = math.sqrt((animal.x - 10.0)**2 + (animal.y - 10.0)**2)
            assert distance <= 4.0  # Within spawn radius
    
    def test_herd_update(self):
        """Test herd update functionality."""
        herd = Herd(AnimalType.SHEEP, center_x=0.0, center_y=0.0, herd_size=3)
        
        # Mock terrain data
        terrain_data = {(0, 0): Mock()}
        terrain_data[(0, 0)].terrain_type.value = 'grass'
        
        # Update should not raise errors
        herd.update(terrain_data)
        
        # Animals should have been updated (check that update was called)
        for animal in herd.animals:
            assert animal.last_update > 0
    
    def test_add_remove_animals(self):
        """Test adding and removing animals from herd."""
        herd = Herd(AnimalType.COW, center_x=0.0, center_y=0.0, herd_size=2)
        initial_count = len(herd.animals)
        
        # Add animal
        herd.add_animal(5.0, 5.0)
        assert len(herd.animals) == initial_count + 1
        
        # Remove animal
        animal_id = herd.animals[0].id
        herd.remove_animal(animal_id)
        assert len(herd.animals) == initial_count
        assert not any(animal.id == animal_id for animal in herd.animals)


class TestAnimalManager:
    """Test the AnimalManager class functionality."""
    
    def test_animal_manager_creation(self):
        """Test animal manager creation."""
        manager = AnimalManager()
        assert len(manager.herds) == 0
        assert manager.update_frequency == 0.1
    
    def test_spawn_herd(self):
        """Test herd spawning."""
        manager = AnimalManager()
        manager.spawn_herd(
            animal_type=AnimalType.SHEEP,
            center_x=10.0,
            center_y=10.0,
            herd_id="test_herd",
            size=4
        )
        
        assert "test_herd" in manager.herds
        assert len(manager.herds["test_herd"].animals) == 4
    
    def test_get_animal_positions(self):
        """Test getting animal positions for rendering."""
        manager = AnimalManager()
        manager.spawn_herd(
            animal_type=AnimalType.COW,
            center_x=0.0,
            center_y=0.0,
            herd_id="test_herd",
            size=2
        )
        
        positions = manager.get_all_animal_positions()
        assert len(positions) == 2
        
        # Check position format
        for x, y, char, color in positions:
            assert isinstance(x, int)
            assert isinstance(y, int)
            assert isinstance(char, str)
            assert isinstance(color, tuple)
            assert len(color) == 3  # RGB
    
    def test_update_animals_timing(self):
        """Test that animals only update at specified frequency."""
        manager = AnimalManager()
        manager.spawn_herd(
            animal_type=AnimalType.SHEEP,
            center_x=0.0,
            center_y=0.0,
            herd_id="test_herd",
            size=1
        )
        
        # Mock terrain data
        terrain_data = {(0, 0): Mock()}
        terrain_data[(0, 0)].terrain_type.value = 'grass'
        
        # First update should work
        manager.update_animals(terrain_data)
        first_update_time = manager.last_update
        
        # Immediate second update should be skipped
        manager.update_animals(terrain_data)
        assert manager.last_update == first_update_time
        
        # Update after sufficient time should work
        manager.last_update = time.time() - 0.2  # Force update
        manager.update_animals(terrain_data)
        assert manager.last_update > first_update_time


class TestIntegration:
    """Integration tests for the complete animal system."""

    def test_world_generator_integration(self):
        """Test integration with WorldGenerator."""
        from src.covenant.world.generator import WorldGenerator

        # Create world generator with animals enabled
        world_gen = WorldGenerator(
            chunk_size=16,
            seed=12345,
            enable_animals=True,
            use_organic_system=True
        )

        assert world_gen.animal_manager is not None

        # Generate some chunks to trigger animal spawning
        world_gen.preload_chunks_around(0, 0, radius=1)

        # Check if any animals were spawned
        animal_positions = world_gen.get_animal_positions()
        # Note: Animals spawn randomly, so we can't guarantee they'll spawn
        # but the method should work without errors
        assert isinstance(animal_positions, list)

    def test_animal_movement_over_time(self):
        """Test that animals actually move over multiple updates."""
        manager = AnimalManager()
        manager.spawn_herd(
            animal_type=AnimalType.SHEEP,
            center_x=10.0,
            center_y=10.0,
            herd_id="movement_test",
            size=3
        )

        # Record initial positions
        initial_positions = []
        for animal in manager.herds["movement_test"].animals:
            initial_positions.append((animal.x, animal.y))

        # Create large terrain area
        terrain_data = {}
        for x in range(20):
            for y in range(20):
                terrain_data[(x, y)] = Mock()
                terrain_data[(x, y)].terrain_type.value = 'grass'

        # Force multiple updates
        for _ in range(10):
            manager.last_update = time.time() - 0.2  # Force update
            manager.update_animals(terrain_data)
            time.sleep(0.01)  # Small delay

        # Check that at least some animals moved
        moved_count = 0
        for i, animal in enumerate(manager.herds["movement_test"].animals):
            initial_x, initial_y = initial_positions[i]
            if abs(animal.x - initial_x) > 0.1 or abs(animal.y - initial_y) > 0.1:
                moved_count += 1

        # At least one animal should have moved
        assert moved_count > 0

    def test_flocking_behavior(self):
        """Test that animals exhibit flocking behavior."""
        # Create a herd with animals spread apart
        herd = Herd(AnimalType.SHEEP, center_x=10.0, center_y=10.0, herd_size=4)

        # Manually spread animals apart
        herd.animals[0].x, herd.animals[0].y = 5.0, 5.0
        herd.animals[1].x, herd.animals[1].y = 15.0, 5.0
        herd.animals[2].x, herd.animals[2].y = 5.0, 15.0
        herd.animals[3].x, herd.animals[3].y = 15.0, 15.0

        # Set all animals to moving state
        for animal in herd.animals:
            animal.state = AnimalState.MOVING

        # Create terrain data
        terrain_data = {}
        for x in range(25):
            for y in range(25):
                terrain_data[(x, y)] = Mock()
                terrain_data[(x, y)].terrain_type.value = 'grass'

        # Record initial center of mass
        initial_center_x = sum(animal.x for animal in herd.animals) / len(herd.animals)
        initial_center_y = sum(animal.y for animal in herd.animals) / len(herd.animals)

        # Update multiple times
        for _ in range(20):
            herd.update(terrain_data)
            time.sleep(0.01)

        # Calculate final center of mass
        final_center_x = sum(animal.x for animal in herd.animals) / len(herd.animals)
        final_center_y = sum(animal.y for animal in herd.animals) / len(herd.animals)

        # Animals should have moved toward each other (cohesion)
        # Calculate average distance from center
        initial_avg_distance = sum(
            math.sqrt((animal.x - initial_center_x)**2 + (animal.y - initial_center_y)**2)
            for animal in herd.animals
        ) / len(herd.animals)

        final_avg_distance = sum(
            math.sqrt((animal.x - final_center_x)**2 + (animal.y - final_center_y)**2)
            for animal in herd.animals
        ) / len(herd.animals)

        # Due to cohesion, animals should be closer together
        # (allowing some tolerance for random movement)
        assert final_avg_distance <= initial_avg_distance + 1.0

    def test_terrain_collision(self):
        """Test that animals avoid impassable terrain."""
        sheep = Sheep(id=1, x=5.0, y=5.0)

        # Create terrain with water blocking movement
        terrain_data = {}
        for x in range(10):
            for y in range(10):
                if x == 6:  # Vertical water barrier
                    terrain_data[(x, y)] = Mock()
                    terrain_data[(x, y)].terrain_type.value = 'water'
                else:
                    terrain_data[(x, y)] = Mock()
                    terrain_data[(x, y)].terrain_type.value = 'grass'

        # Try to move sheep toward water
        sheep.velocity = Vector2D(1.0, 0.0)  # Moving right toward water

        # Update sheep
        sheep.update([], terrain_data, 0.1)

        # Sheep should not move into water
        assert sheep.x < 6.0  # Should not cross water barrier
