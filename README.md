# Covenant: Blood & Fire

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-66%20passed-green.svg)](tests/)

A terminal-based strategy game built with Python and libtcod, featuring infinite procedural world generation and real-time strategy gameplay in your console.

![Covenant: Blood & Fire Game Screenshot](docs/screenshot.png)

## ✨ Features

### 🌍 **Infinite World Generation**
- **Procedural terrain** using Perlin noise algorithms
- **Chunk-based system** for efficient memory management
- **9 terrain types**: Deep water, shallow water, sand, grasslands, forests, hills, and mountains
- **Seamless exploration** with no loading screens

### 🎮 **Intuitive Controls**
- **Fixed crosshair cursor** at screen center
- **Smooth world scrolling** with arrow keys or WASD
- **Real-time performance monitoring** with FPS display
- **Responsive 60 FPS gameplay**

### 🏗️ **Modern Architecture**
- **Modular design** with clean separation of concerns
- **Comprehensive test suite** (66 tests, 100% pass rate)
- **Type hints** throughout for better IDE support
- **Performance optimized** for smooth gameplay

## 🚀 Quick Start

### Prerequisites

- **Python 3.13+** (required)
- **uv** package manager (recommended) or pip

### Installation

#### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/empires.git
cd empires

# Install dependencies
uv sync

# Run the game
uv run python -m src.empires.main
```

#### Using pip

```bash
# Clone the repository
git clone https://github.com/yourusername/empires.git
cd empires

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Run the game
python -m src.empires.main
```

### Controls

| Key | Action |
|-----|--------|
| `↑` `↓` `←` `→` | Scroll the world |
| `W` `A` `S` `D` | Alternative scroll controls |
| `ESC` or `Q` | Quit game |

## 🎯 Gameplay

- **Explore** an infinite procedurally generated world
- **Navigate** using the golden crosshair cursor
- **Discover** diverse terrain types from deep oceans to mountain peaks
- **Monitor** performance with real-time FPS display
- **Experience** smooth 60 FPS gameplay

## 🏗️ Architecture

### Core Components

```
src/empires/
├── main.py                 # Game loop and main application
├── world/                  # World generation system
│   ├── noise.py           # Perlin noise generation
│   ├── terrain.py         # Terrain types and properties
│   ├── chunks.py          # Chunk management system
│   └── generator.py       # World generation coordinator
└── camera/                # Camera and viewport system
    └── viewport.py        # Camera movement and rendering
```

### Key Features

- **Chunk System**: 32×32 tile chunks with LRU caching
- **Noise Generation**: Multi-octave Perlin noise for natural terrain
- **Camera System**: Fixed crosshair with world scrolling
- **Performance**: Optimized rendering with viewport culling

## 🧪 Development

### Running Tests

```bash
# Install dev dependencies first
uv sync --extra dev

# Run all tests
uv run python -m pytest tests/ -v

# Run specific test module
uv run python -m pytest tests/world/test_noise.py -v

# Run with coverage (requires pytest-cov)
uv run python -m pytest tests/ --cov=src/empires
```

### Code Quality

```bash
# Format code
uv run black src/ tests/

# Lint code
uv run ruff check src/ tests/

# Type checking
uv run mypy src/
```

### Project Structure

```
covenant-blood-fire/
├── src/empires/           # Source code
│   ├── main.py           # Main application entry point
│   ├── world/            # World generation modules
│   └── camera/           # Camera and viewport modules
├── tests/                # Test suite
│   ├── world/            # World generation tests
│   └── camera/           # Camera system tests
├── docs/                 # Documentation
│   └── world_generation_design.md
├── pyproject.toml        # Project configuration
└── README.md            # This file
```

## 📖 Documentation

- **[Design Document](docs/world_generation_design.md)** - Comprehensive system architecture
- **[API Reference](src/empires/)** - Inline documentation in source code
- **[Test Coverage](tests/)** - 66 comprehensive unit tests

## 🎯 Roadmap

### Phase 1: Core Systems ✅
- [x] Infinite world generation
- [x] Chunk-based memory management
- [x] Camera and viewport system
- [x] Performance optimization
- [x] Comprehensive testing

### Phase 2: Gameplay (Planned)
- [ ] Unit system (villagers, military units)
- [ ] Resource management (food, wood, stone, gold)
- [ ] Building construction
- [ ] Technology research tree

### Phase 3: Advanced Features (Future)
- [ ] Multiplayer support
- [ ] AI opponents
- [ ] Save/load functionality
- [ ] Mod support
- [ ] Advanced graphics options

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/empires.git
cd empires

# Install development dependencies
uv sync --extra dev

# Run tests to ensure everything works
uv run python -m pytest tests/
```

## 📋 Requirements

### System Requirements
- **Python**: 3.13 or higher
- **Memory**: 100MB+ RAM
- **Storage**: 50MB+ disk space
- **Terminal**: Any modern terminal with color support

### Dependencies
- **tcod**: Terminal graphics and input handling
- **Development**: pytest, black, ruff, mypy (optional)

## 🐛 Troubleshooting

### Common Issues

**Font loading warnings**: The game may show font loading warnings but will work with system defaults.

**Performance issues**: If experiencing low FPS:
- Ensure Python 3.13+ is being used
- Close other resource-intensive applications
- Check terminal performance settings

**Import errors**: Make sure you're running from the project root directory.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **libtcod** - Excellent terminal graphics library
- **Python community** - For amazing tools and libraries
- **Age of Empires** - Inspiration for gameplay mechanics
- **Perlin noise** - Ken Perlin's noise algorithm for terrain generation

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/covenant-blood-fire/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/covenant-blood-fire/discussions)
- **Documentation**: [Project Wiki](https://github.com/yourusername/covenant-blood-fire/wiki)

---

**Made with ❤️ by the Covenant: Blood & Fire development team**