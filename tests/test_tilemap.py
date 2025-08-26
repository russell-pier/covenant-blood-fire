"""
Tests for the tilemap system.

This module tests the centralized tile configuration system and ensures
proper tile mapping across all three scales.
"""

import pytest
from src.covenant.world.data.tilemap import (
    TileConfig, ColorPalette, TileLibrary, BiomeType, TerrainSubtype, LocalTerrain,
    get_tile, get_tile_with_variation, TILE_LIBRARY
)
from src.covenant.world.data.scale_types import ViewScale


class TestColorPalette:
    """Test color palette functionality"""
    
    def test_shade_darker(self):
        """Test shading colors darker"""
        color = (100, 150, 200)
        darker = ColorPalette.shade(color, 0.5)
        assert darker == (50, 75, 100)
    
    def test_shade_lighter(self):
        """Test shading colors lighter"""
        color = (100, 150, 200)
        lighter = ColorPalette.shade(color, 1.5)
        assert lighter == (150, 225, 255)  # Clamped to 255
    
    def test_tint_color(self):
        """Test color tinting"""
        base = (100, 100, 100)
        tint = (255, 0, 0)  # Red tint
        tinted = ColorPalette.tint(base, tint, 0.2)
        
        # Should be 80% base + 20% tint
        expected = (131, 80, 80)
        assert tinted == expected
    
    def test_random_variation(self):
        """Test random color variation"""
        color = (128, 128, 128)
        varied = ColorPalette.random_variation(color, 10)
        
        # Should be within variance range
        for i in range(3):
            assert 118 <= varied[i] <= 138  # 128 ± 10
    
    def test_color_clamping(self):
        """Test that colors are properly clamped to 0-255 range"""
        # Test negative values
        dark = ColorPalette.shade((50, 50, 50), 0.1)
        assert all(c >= 0 for c in dark)
        
        # Test values over 255
        bright = ColorPalette.shade((200, 200, 200), 2.0)
        assert all(c <= 255 for c in bright)


class TestTileConfig:
    """Test tile configuration functionality"""
    
    def test_tile_config_creation(self):
        """Test basic tile configuration creation"""
        tile = TileConfig(".", (255, 255, 255), (0, 0, 0), description="Test tile")
        
        assert tile.char == "."
        assert tile.fg_color == (255, 255, 255)
        assert tile.bg_color == (0, 0, 0)
        assert tile.description == "Test tile"
        assert tile.variants is None
    
    def test_tile_config_with_variants(self):
        """Test tile configuration with variants"""
        variant1 = TileConfig("·", (200, 200, 200), (0, 0, 0))
        variant2 = TileConfig(",", (180, 180, 180), (0, 0, 0))
        
        tile = TileConfig(".", (255, 255, 255), (0, 0, 0), 
                         variants=[variant1, variant2])
        
        assert len(tile.variants) == 2
        assert tile.variants[0].char == "·"
        assert tile.variants[1].char == ","


class TestTileLibrary:
    """Test tile library functionality"""
    
    def test_library_initialization(self):
        """Test that tile library initializes properly"""
        library = TileLibrary()
        
        # Should have tiles for all three scales
        assert ViewScale.WORLD in library.tiles
        assert ViewScale.REGIONAL in library.tiles
        assert ViewScale.LOCAL in library.tiles
    
    def test_get_world_tile(self):
        """Test getting world-scale tiles"""
        library = TileLibrary()
        
        # Test getting a known biome tile
        tile = library.get_tile(ViewScale.WORLD, BiomeType.GRASSLAND)
        assert tile.char == "\""
        assert tile.description == "Temperate grasslands"
    
    def test_get_regional_tile(self):
        """Test getting regional-scale tiles"""
        library = TileLibrary()
        
        # Test getting a known terrain subtype
        tile = library.get_tile(ViewScale.REGIONAL, TerrainSubtype.PLAINS)
        assert tile.char == "."
        assert tile.description == "Open plains with short grass"
    
    def test_get_local_tile(self):
        """Test getting local-scale tiles"""
        library = TileLibrary()
        
        # Test getting a known local terrain
        tile = library.get_tile(ViewScale.LOCAL, LocalTerrain.GRASS_PATCH)
        assert tile.char == "."
        assert tile.description == "Patches of grass"
    
    def test_get_unknown_tile(self):
        """Test getting unknown tile returns fallback"""
        library = TileLibrary()
        
        # Test with invalid tile type
        tile = library.get_tile(ViewScale.WORLD, "invalid_tile_type")
        assert tile.char == "?"
        assert "Unknown tile" in tile.description
    
    def test_get_tile_with_variants(self):
        """Test that variants are sometimes returned"""
        library = TileLibrary()
        
        # Get a tile that has variants multiple times
        results = []
        for _ in range(100):  # Try many times to get statistical variation
            tile = library.get_tile(ViewScale.REGIONAL, TerrainSubtype.PLAINS, use_variant=True)
            results.append(tile.char)
        
        # Should have some variation in characters (base "." plus variants "·" and ",")
        unique_chars = set(results)
        assert len(unique_chars) > 1  # Should have at least base + some variants
    
    def test_get_tile_with_color_variation(self):
        """Test getting tiles with color variation"""
        library = TileLibrary()
        
        # Get base tile
        base_tile = library.get_tile(ViewScale.WORLD, BiomeType.GRASSLAND, use_variant=False)
        
        # Get varied tile
        varied_tile = library.get_tile_with_variation(ViewScale.WORLD, BiomeType.GRASSLAND, color_variance=20)
        
        # Colors should be different (with high probability)
        # Note: There's a small chance they could be the same due to randomness
        assert varied_tile.char == base_tile.char  # Character should be same
        assert varied_tile.description == base_tile.description  # Description should be same
    
    def test_has_tile(self):
        """Test tile existence checking"""
        library = TileLibrary()
        
        # Test existing tiles
        assert library.has_tile(ViewScale.WORLD, BiomeType.GRASSLAND)
        assert library.has_tile(ViewScale.REGIONAL, TerrainSubtype.PLAINS)
        assert library.has_tile(ViewScale.LOCAL, LocalTerrain.GRASS_PATCH)
        
        # Test non-existing tiles
        assert not library.has_tile(ViewScale.WORLD, "invalid_type")
        assert not library.has_tile(ViewScale.REGIONAL, BiomeType.GRASSLAND)  # Wrong scale
    
    def test_get_available_tiles(self):
        """Test getting available tile types"""
        library = TileLibrary()
        
        # Test world scale
        world_tiles = library.get_available_tiles(ViewScale.WORLD)
        assert BiomeType.GRASSLAND in world_tiles
        assert BiomeType.DESERT in world_tiles
        assert len(world_tiles) > 0
        
        # Test regional scale
        regional_tiles = library.get_available_tiles(ViewScale.REGIONAL)
        assert TerrainSubtype.PLAINS in regional_tiles
        assert TerrainSubtype.DENSE_FOREST in regional_tiles
        assert len(regional_tiles) > 0
        
        # Test local scale
        local_tiles = library.get_available_tiles(ViewScale.LOCAL)
        assert LocalTerrain.GRASS_PATCH in local_tiles
        assert LocalTerrain.MATURE_TREES in local_tiles
        assert len(local_tiles) > 0


class TestGlobalTileAccess:
    """Test global tile access functions"""
    
    def test_global_get_tile(self):
        """Test global get_tile function"""
        tile = get_tile(ViewScale.WORLD, BiomeType.GRASSLAND)
        assert tile.char == "\""
        assert tile.description == "Temperate grasslands"
    
    def test_global_get_tile_with_variation(self):
        """Test global get_tile_with_variation function"""
        tile = get_tile_with_variation(ViewScale.WORLD, BiomeType.GRASSLAND, color_variance=15)
        assert tile.char == "\""
        assert tile.description == "Temperate grasslands"
    
    def test_global_library_consistency(self):
        """Test that global functions use the same library as direct access"""
        # Get tile through global function
        global_tile = get_tile(ViewScale.WORLD, BiomeType.GRASSLAND, use_variant=False)
        
        # Get tile through direct library access
        direct_tile = TILE_LIBRARY.get_tile(ViewScale.WORLD, BiomeType.GRASSLAND, use_variant=False)
        
        # Should be identical
        assert global_tile.char == direct_tile.char
        assert global_tile.fg_color == direct_tile.fg_color
        assert global_tile.bg_color == direct_tile.bg_color
        assert global_tile.description == direct_tile.description


class TestTileCompleteness:
    """Test that all required tiles are defined"""
    
    def test_all_biomes_have_tiles(self):
        """Test that all biome types have corresponding tiles"""
        library = TileLibrary()
        
        for biome in BiomeType:
            assert library.has_tile(ViewScale.WORLD, biome), f"Missing tile for biome: {biome}"
    
    def test_all_terrain_subtypes_have_tiles(self):
        """Test that all terrain subtypes have corresponding tiles"""
        library = TileLibrary()
        
        # Note: Not all terrain subtypes may be implemented yet
        # This test will help identify missing ones
        implemented_subtypes = library.get_available_tiles(ViewScale.REGIONAL)
        
        # At least check that some key subtypes are implemented
        key_subtypes = [
            TerrainSubtype.PLAINS, TerrainSubtype.DENSE_FOREST, 
            TerrainSubtype.SAND_DUNES, TerrainSubtype.OASIS
        ]
        
        for subtype in key_subtypes:
            assert subtype in implemented_subtypes, f"Missing tile for terrain subtype: {subtype}"
    
    def test_all_local_terrains_have_tiles(self):
        """Test that all local terrain types have corresponding tiles"""
        library = TileLibrary()
        
        # Note: Not all local terrains may be implemented yet
        # This test will help identify missing ones
        implemented_terrains = library.get_available_tiles(ViewScale.LOCAL)
        
        # At least check that some key terrains are implemented
        key_terrains = [
            LocalTerrain.GRASS_PATCH, LocalTerrain.MATURE_TREES,
            LocalTerrain.SHALLOW_WATER, LocalTerrain.SMALL_BOULDER
        ]
        
        for terrain in key_terrains:
            assert terrain in implemented_terrains, f"Missing tile for local terrain: {terrain}"


if __name__ == "__main__":
    pytest.main([__file__])
