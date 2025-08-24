Create a professional-grade three-tier world generation and visualization system in Python using uv and libtcod.
Project Setup

Initialize a Python project using uv package manager
Add libtcod and pytest as dependencies
Create proper module structure with __init__.py files
Follow Python best practices: type hints, docstrings, PEP 8 compliance

Code Quality Requirements

Professional Standards: Clean, maintainable, well-documented code
Type Safety: Full type annotations throughout
Documentation: Comprehensive docstrings for all classes and functions
Error Handling: Proper exception handling and validation
Modular Design: Loosely coupled, highly cohesive components
Single Responsibility: Each class/function has one clear purpose

Testing Strategy

Comprehensive Test Suite: Unit tests for all core functionality
CLI Testing Interface: Command-line tools to verify generation output
Text-Based Validation: Since everything is text/characters, create testable output
Deterministic Testing: Same seed produces identical, verifiable results
Performance Testing: Verify 60 FPS targets and generation speed
Integration Testing: Test scale switching, camera movement, UI rendering

Testing Examples:
```
python# CLI testing commands
python -m world_gen test-world-generation --seed 12345
python -m world_gen validate-sectors --expected-output sectors.txt
python -m world_gen benchmark-performance --iterations 1000

# Automated testing
pytest tests/ -v --coverage
```

Game Architecture
Create a main game loop with two core systems:
1. UI System (Modular Components)

Top Bar Module: Display current scale, coordinates, terrain info, elevation
Bottom Bar Module: Show controls (1=World, 2=Regional, 3=Local, WASD=Move)
Left Sidebar Module: BLANK for now (placeholder module)
Right Sidebar Module: BLANK for now (placeholder module)
Each UI component should be a separate, testable module that can render to specific console areas

2. Map System (Three Perspectives)
World View: 8×6 sector grid displayed as 128×96 tiles (16×16 pixels per sector)
Regional View: Full screen responsive, showing 32×32 blocks within selected sector
Local View: Full screen responsive, showing 32×32 chunks within selected block
Three-Tier World Generation Pipeline
Pipeline 1: World Scale Generator

Generate 8×6 sectors (48 total sectors)
Each sector represents 16,384×16,384 world tiles
Use continental-scale noise for: ocean/land, mountain ranges, climate zones
Determine: dominant_terrain, elevation, has_mountains, has_rivers, climate_zone
Visual: single character + color per sector
Testable: Export sector data to text format for validation

Pipeline 2: Regional Scale Generator

Input: Parent world sector data
Generate 32×32 blocks within a sector (1,024×1,024 tiles per block)
Refine terrain based on parent sector constraints
Add: regional rivers, biome variations, elevation details
Visual: single character + color per block
Testable: Validate hierarchical consistency with parent sector

Pipeline 3: Local Scale Generator

Input: Parent regional block + world sector data
Generate 32×32 chunks within a block (32×32 tiles per chunk)
Create detailed terrain respecting hierarchical constraints
Add: resources, detailed terrain variation, micro-features
Visual: dominant terrain representation per chunk
Testable: Verify terrain matches parent regional biome

Camera System

Three independent camera positions (world_cam, regional_cam, local_cam)
Scale switching with 1/2/3 keys
WASD movement within current scale
Coordinate conversion between scales
Testable: Verify coordinate conversions and boundary checking

Technical Requirements

Deterministic generation (same seed = same world)
Hierarchical consistency (local terrain matches regional biome matches world climate)
Efficient rendering (only draw current perspective)
60 FPS target performance
All requirements must be testable and verifiable

Noise-Based Generation
Use multi-octave noise for realistic terrain:

Continental scale (0.00001 frequency): Major landmasses
Regional scale (0.001 frequency): Mountain ranges, river systems
Local scale (0.01 frequency): Terrain variation
Testable: Verify noise produces expected distributions and patterns

Development Approach

Test-Driven Development: Write tests alongside implementation
Incremental Validation: Each component must be testable in isolation
CLI Debug Tools: Command-line utilities for manual verification
Automated Validation: Pytest suite covering all functionality
Performance Benchmarks: Measurable performance targets

Initial Implementation Focus
Start with basic world view working first, then add regional and local. Include placeholder rendering for incomplete scales. Prioritize getting the UI layout, camera switching, and basic world generation working with solid test coverage before adding complexity.
Success Criteria

All tests pass with >90% coverage
CLI tools can verify generation output matches expectations
Performance benchmarks meet 60 FPS target
Same seed produces identical, reproducible results
Hierarchical consistency validated across all scales
Professional code quality suitable for production

Task Breakdown: Three-Tier World Generation System
Phase 1: Project Foundation
Task 1.1: Project Initialization

 Initialize Python project using uv init
 Add dependencies: uv add libtcod pytest pytest-cov
 Create basic directory structure:
```text
src/
├── __init__.py
├── main.py
tests/
├── __init__.py
README.md
pyproject.toml
```

Task 1.2: Basic Game Loop Setup

 Create minimal libtcod game loop in main.py
 Set up 128x96 console (world view size)
 Add basic event handling (quit on ESC)
 Add FPS limiting (60 FPS target)
 Test: Game launches and runs without errors

Task 1.3: Core Type Definitions

 Create src/types.py with enums and dataclasses:

 ViewScale enum (WORLD, REGIONAL, LOCAL)
 WorldLayer enum (UNDERGROUND, SURFACE, MOUNTAINS)
 Basic coordinate types


 Add comprehensive type hints
 Test: All types import and instantiate correctly

Phase 2: Noise Generation System
Task 2.1: Base Noise Generator

 Create src/noise.py with NoiseGenerator class
 Implement deterministic noise function
 Implement octave noise (multi-frequency)
 Add seed-based initialization
 Test: Same seed produces identical output

Task 2.2: Hierarchical Noise System

 Create HierarchicalNoiseGenerator class
 Add continental_noise() method (0.00001 frequency)
 Add regional_noise() method (0.001 frequency)
 Add local_noise() method (0.01 frequency)
 Test: Different frequencies produce expected variation

Task 2.3: Noise Testing Suite

 Create tests/test_noise.py
 Test deterministic behavior (same input = same output)
 Test frequency separation (continental vs regional vs local)
 Test value ranges (-1.0 to 1.0)
 CLI tool: python -m src.noise test-noise --seed 12345

Phase 3: World Scale Generator
Task 3.1: World Sector Data Structure

 Create src/world_data.py
 Define WorldSectorData dataclass with all required fields
 Define WorldMapData container class
 Add validation methods
 Test: Data structures serialize/deserialize correctly

Task 3.2: World Scale Generation Logic

 Create src/world_generator.py
 Implement WorldScaleGenerator class
 Add generate_world_sector() method
 Add terrain classification logic (ocean, land, mountains, etc.)
 Add climate zone determination
 Test: Generates valid sector data

Task 3.3: Complete World Map Generation

 Implement generate_complete_world_map() method
 Generate 8x6 sector grid (48 total sectors)
 Add caching to avoid regeneration
 Add tectonic plate assignment
 Test: Generates complete 48-sector world

Task 3.4: World Generation Testing

 Create tests/test_world_generator.py
 Test deterministic generation (same seed = same world)
 Test all 48 sectors are generated
 Test terrain distribution is reasonable
 Test climate zones follow latitude patterns
 CLI tool: python -m src.world_generator export-world --seed 12345

Phase 4: Camera System
Task 4.1: Basic Camera Class

 Create src/camera.py
 Define Camera class with position tracking
 Add movement methods with bounds checking
 Add coordinate conversion methods
 Test: Camera moves within bounds correctly

Task 4.2: Multi-Scale Camera System

 Implement MultiScaleCameraSystem class
 Add three independent camera positions
 Add scale switching logic
 Add coordinate conversion between scales
 Test: Scale switching preserves relative positions

Task 4.3: Camera Testing Suite

 Create tests/test_camera.py
 Test movement bounds checking
 Test scale switching behavior
 Test coordinate conversions are accurate
 CLI tool: python -m src.camera test-movement

Phase 5: UI System Foundation
Task 5.1: Base UI Components

 Create src/ui/ directory structure
 Create src/ui/base.py with UIComponent base class
 Add render area calculation methods
 Add text centering utilities
 Test: Base component renders correctly

Task 5.2: Top Bar Implementation

 Create src/ui/top_bar.py
 Implement location info display
 Add current scale indicator
 Add coordinate display
 Add terrain info display
 Test: Top bar renders with correct info

Task 5.3: Bottom Bar Implementation

 Create src/ui/bottom_bar.py
 Add control instructions display
 Add scale switching help (1=World, 2=Regional, 3=Local)
 Add movement help (WASD=Move)
 Test: Bottom bar renders correctly

Task 5.4: Sidebar Placeholders

 Create src/ui/left_sidebar.py (blank placeholder)
 Create src/ui/right_sidebar.py (blank placeholder)
 Add proper spacing and borders
 Test: Sidebars render without interfering with main content

Task 5.5: UI System Integration

 Create src/ui/ui_manager.py
 Combine all UI components
 Handle console area allocation
 Add UI update methods
 Test: Complete UI layout renders correctly

Phase 6: World View Rendering
Task 6.1: World Map Renderer

 Create src/renderers/world_renderer.py
 Implement sector-to-pixel rendering (16x16 per sector)
 Add color mapping for terrain types
 Add camera crosshair rendering
 Test: World map displays correctly

Task 6.2: World View Integration

 Integrate world renderer with camera system
 Add camera movement in world view
 Add world map scrolling
 Handle screen-to-world coordinate conversion
 Test: Camera movement works in world view

Task 6.3: World Rendering Testing

 Create tests/test_world_renderer.py
 Test sector rendering positions
 Test color assignments are correct
 Test camera crosshair position
 CLI tool: python -m src.renderers.world_renderer render-test

Phase 7: Regional & Local Placeholders
Task 7.1: Regional Generator Stub

 Create src/regional_generator.py
 Add placeholder RegionalScaleGenerator class
 Return dummy 32x32 block data
 Add parent sector constraint checking
 Test: Regional generator returns valid placeholder data

Task 7.2: Local Generator Stub

 Create src/local_generator.py
 Add placeholder LocalScaleGenerator class
 Return dummy 32x32 chunk data
 Add hierarchical constraint validation
 Test: Local generator returns valid placeholder data

Task 7.3: Placeholder Renderers

 Create src/renderers/regional_renderer.py (placeholder)
 Create src/renderers/local_renderer.py (placeholder)
 Add "NOT IMPLEMENTED" messaging
 Test: Placeholder renderers display correctly

Phase 8: Scale Switching System
Task 8.1: Input Handler

 Create src/input_handler.py
 Add scale switching (1/2/3 keys)
 Add movement handling (WASD)
 Add mode-specific input routing
 Test: All input combinations work correctly

Task 8.2: View Manager

 Create src/view_manager.py
 Coordinate camera, renderer, and UI systems
 Handle scale transition logic
 Update UI based on current scale
 Test: Scale transitions work smoothly

Task 8.3: Integration Testing

 Create tests/test_integration.py
 Test complete scale switching workflow
 Test UI updates during scale changes
 Test camera position preservation
 Performance test: Verify 60 FPS maintained

Phase 9: Testing & Quality Assurance
Task 9.1: Comprehensive Test Suite

 Ensure all modules have test coverage >90%
 Add property-based testing for noise generation
 Add performance benchmarks
 Add memory usage tests
 Run: pytest tests/ -v --cov=src --cov-report=html

Task 9.2: CLI Testing Tools

 Create src/cli_tools.py
 Add world export functionality
 Add performance benchmarking
 Add determinism validation
 Test: All CLI tools produce expected output

Task 9.3: Documentation & Code Quality

 Add comprehensive docstrings to all classes/methods
 Ensure PEP 8 compliance throughout
 Add type hints to all functions
 Create usage examples
 Run: mypy src/ (no errors)

Task 9.4: Final Integration Test

 Test complete system end-to-end
 Verify all requirements are met
 Confirm 60 FPS performance target
 Validate deterministic behavior
 Test: Complete system works as specified

Success Criteria Checklist

 All 48 tasks completed successfully
 Test suite passes with >90% coverage
 Performance benchmarks meet 60 FPS target
 Same seed produces identical results across runs
 Professional code quality (type hints, docstrings, PEP 8)
 World view displays 8x6 sector grid correctly
 Scale switching works between all three views
 UI components render in correct positions
 Hierarchical world generation pipeline is established