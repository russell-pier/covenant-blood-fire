# Resource Generation Design Document

## Overview
This document outlines the design and implementation plan for adding clustered resource generation to the world generation pipeline. Resources will be distributed in realistic clusters across three layers (Surface, Underground, Mountains) with terrain-appropriate placement, creating strategic vertical resource competition where players must control territory across all layers for optimal economy.

## Strategic Resource Distribution

### Surface Layer Resources (Easy Access, Renewable)
- 🌲 **MASSIVE FORESTS**: Dense wood clusters (♠♣🌲) in grassland/forest areas
- 🌾 **FERTILE VALLEYS**: Food clusters (•●🍄) in fertile plains and forests
- 🪨 **SURFACE QUARRIES**: Stone deposits (○●▲) for basic construction
- 🐟 **FISHING GROUNDS**: Water resources (◦🐟🐚) in lakes and rivers

### Underground Layer Resources (Requires Cave Access, Finite but Valuable)
- 💰 **GOLD VEINS**: Rich gold clusters (*♦💰) in cave systems
- ⛏️ **IRON MINES**: Dense iron deposits (▲■⬛) for tools/weapons
- 🔥 **COAL SEAMS**: Fuel clusters (●■⬛) for smelting and energy
- 💎 **GEM CAVERNS**: Precious stone formations (◊♦💎) for trade
- 🔮 **CRYSTAL CAVES**: Rare magical crystals (◊✦🔮) for advanced tech
- 💧 **UNDERGROUND SPRINGS**: Fresh water sources (~≈💧) independent of surface

### Mountain Layer Resources (Requires Mountain Access, High-Quality but Dangerous)
- 🏔️ **MASSIVE QUARRIES**: Huge stone deposits (▲⩙⛰️) for fortifications
- ⚡ **SURFACE METAL**: Exposed ore veins (▲♦⬛) easier to access than underground
- 💎 **MOUNTAIN GEMS**: High-quality gems (♦✦💎) in mountain peaks
- ❄️ **ETERNAL ICE**: Glacial ice (∘●❄️) for preservation, special uses

## Strategic Gameplay Implications

### Economic Progression
- **Early Game**: Surface wood/food for basic survival and initial settlements
- **Mid Game**: Underground metals for military equipment and advanced tools
- **Late Game**: Mountain quarries for massive construction projects, rare gems for trade

### Territorial Control Strategy
- **Surface Control**: Dominate forests and fertile valleys for sustainable resources
- **Underground Control**: Secure gold mines and iron deposits for military advantage
- **Mountain Control**: Command high-quality quarries and rare gem sites for late-game power

### Vertical Resource Competition
Players must control territory across all three layers for optimal economy, creating strategic depth where:
- Surface resources provide sustainability and growth
- Underground resources enable military and technological advancement
- Mountain resources unlock massive construction and rare trade goods

## Step-by-Step Implementation Plan

### Phase 1: Core Infrastructure Setup
1. **Create Resource Type Definitions**
   - Define ResourceType enum with surface, underground, and mountain resources
   - Create ResourceCluster and ResourceNode dataclasses
   - Set up resource character mappings by rarity level

2. **Implement Noise-Based Cluster Generation**
   - Create ClusteredResourceGenerator class with multiple noise generators
   - Implement cluster center detection using octave noise
   - Add layer-specific cluster properties (size, density, spawn rates)

3. **Add Terrain Compatibility System**
   - Define terrain-resource compatibility rules
   - Implement terrain filtering for cluster placement
   - Ensure resources only spawn on appropriate terrain types

### Phase 2: Layer-Specific Resource Generation
4. **Surface Layer Resources (Renewable & Accessible)**
   - 🌲 Massive forest clusters (♠♣🌲) with high density in grassland/forest biomes
   - 🌾 Fertile valley food clusters (•●🍄) in plains and forest areas
   - 🪨 Surface stone quarries (○●▲) for basic construction materials
   - 🐟 Fishing ground clusters (◦🐟🐚) in water-adjacent terrain
   - Implement renewable resource mechanics for wood and food

5. **Underground Layer Resources (Finite & Valuable)**
   - 💰 Rich gold vein clusters (*♦💰) in cave systems with high value density
   - ⛏️ Dense iron mine deposits (▲■⬛) for military/tool production
   - 🔥 Coal seam clusters (●■⬛) for smelting and energy systems
   - 💎 Gem cavern formations (◊♦💎) for trade and luxury goods
   - 🔮 Rare crystal caves (◊✦🔮) for advanced technology/magic
   - 💧 Underground spring clusters (~≈💧) independent of surface water

6. **Mountain Layer Resources (High-Quality & Dangerous)**
   - 🏔️ Massive quarry clusters (▲⩙⛰️) for fortification construction
   - ⚡ Surface metal deposits (▲♦⬛) easier to access than underground
   - 💎 Mountain gem clusters (♦✦💎) with higher quality than underground
   - ❄️ Eternal ice formations (∘●❄️) for preservation and special uses

### Phase 3: Integration with World Generator
7. **Modify Chunk Generation Pipeline**
   - Add resource generation step after terrain generation
   - Integrate with existing layered world system
   - Ensure resources respect chunk boundaries

8. **Resource Node Placement**
   - Implement density-based node placement within clusters
   - Add rarity calculation based on cluster intensity
   - Apply distance-based spawn probability

9. **Visual Integration**
   - Update terrain characters to show resource nodes
   - Implement resource data storage in terrain objects
   - Add resource harvesting metadata

### Phase 4: Testing and Balancing
10. **Resource Distribution Testing**
    - Verify appropriate resource density across biomes
    - Test cluster generation consistency across chunk boundaries
    - Validate terrain compatibility rules

11. **Performance Optimization**
    - Profile resource generation performance
    - Optimize noise calculations for large-scale generation
    - Implement caching for cluster data

12. **Game Balance Tuning**
    - Adjust resource spawn rates and cluster sizes
    - Balance rarity distributions
    - Fine-tune yield amounts and respawn mechanics

## Technical Implementation Details

### Resource Type System
```python
class ResourceType(Enum):
    # SURFACE LAYER resources
    WOOD = "wood"           # Trees, lumber
    FOOD_SURFACE = "food"   # Berries, crops, animals
    STONE_SURFACE = "stone" # Surface rocks, small quarries
    WATER = "water"         # Fish, kelp

    # UNDERGROUND LAYER resources
    GOLD = "gold"           # Gold veins, nuggets
    IRON = "iron"           # Iron ore deposits
    COAL = "coal"           # Coal seams for fuel/smelting
    GEMS = "gems"           # Precious stones
    CRYSTAL = "crystal"     # Magic crystals, rare minerals
    UNDERGROUND_WATER = "underground_water"  # Springs, underground lakes

    # MOUNTAIN LAYER resources
    STONE_MOUNTAIN = "stone_mountain"  # Large stone quarries
    METAL_MOUNTAIN = "metal"           # Surface metal deposits
    RARE_GEMS = "rare_gems"            # Mountain gem deposits
    ICE = "ice"                        # High altitude ice/snow

@dataclass
class ResourceCluster:
    """Defines a resource-rich area"""
    center_x: int
    center_y: int
    resource_type: ResourceType
    radius: float
    density: float  # 0.0 to 1.0, how packed with resources
    intensity: float  # How valuable the resources are

@dataclass
class ResourceNode:
    """Individual resource character on the map"""
    x: int
    y: int
    resource_type: ResourceType
    char: str
    yield_amount: int
    respawns: bool
```

### Integration Points with Existing World Generator

#### 1. Modify WorldGenerator Class
- Add resource generation step after terrain generation
- Call `add_resources_to_chunk()` for each generated chunk
- Pass layered terrain data to resource generator

#### 2. Update Chunk Generation Pipeline
```python
def generate_chunk(self, chunk_x: int, chunk_y: int) -> Dict:
    # Existing terrain generation
    layered_terrain = self.generate_layered_terrain(chunk_x, chunk_y)

    # NEW: Add resource generation step
    layered_resources = self.generate_resources(chunk_x, chunk_y, layered_terrain)

    # Apply resources to terrain
    self.apply_resources_to_terrain(layered_terrain, layered_resources)

    return layered_terrain
```

#### 3. Resource-Terrain Integration
- Resources modify terrain character display
- Resource data stored in terrain objects for harvesting
- Maintain terrain passability while showing resources

### Algorithm Flow

#### Phase 1: Cluster Detection
1. Sample world coordinates using noise at cluster scale (0.003)
2. Identify high-noise areas as potential cluster centers
3. Apply layer-specific thresholds and sampling patterns
4. Generate cluster properties (radius, density, resource type)

#### Phase 2: Terrain Filtering
1. Check cluster centers against terrain compatibility rules
2. Sample terrain around cluster center to verify suitability
3. Filter out clusters that don't match terrain requirements
4. Maintain only viable clusters for population

#### Phase 3: Node Population
1. For each valid cluster, iterate through radius area
2. Apply distance-based spawn probability
3. Use density noise for fine-grained placement variation
4. Calculate rarity based on cluster intensity and distance
5. Generate resource nodes with appropriate characters and yields

### Performance Considerations

#### Optimization Strategies
- **Chunk Boundary Handling**: Sample larger area to catch cross-chunk clusters
- **Noise Caching**: Reuse noise calculations where possible
- **Early Filtering**: Check terrain compatibility before expensive calculations
- **Batch Processing**: Generate multiple clusters efficiently

#### Memory Management
- Store only essential cluster data during generation
- Clean up temporary cluster objects after node generation
- Use efficient data structures for resource node storage

### Configuration Parameters

#### Cluster Generation
- `cluster_scale = 0.003`: Controls cluster spacing (lower = more spread out)
- `density_scale = 0.02`: Variation within clusters
- `rarity_scale = 0.05`: Fine-grained rarity variation

#### Layer-Specific Settings
- **Surface**: Large, moderate density clusters (massive forests, fertile valleys)
  - Renewable resources (wood/food regrow over time)
  - High accessibility, lower individual value
  - Cluster radius: 10-25 tiles, density: 15-40%
- **Underground**: Small, very high density clusters (rich veins, caverns)
  - Finite but extremely valuable resources
  - Requires cave access, higher individual value
  - Cluster radius: 6-14 tiles, density: 25-60%
- **Mountains**: Medium size, high density clusters (massive quarries, peaks)
  - Highest quality resources, dangerous access
  - Premium construction materials and rare gems
  - Cluster radius: 8-18 tiles, density: 20-50%

#### Strategic Spawn Thresholds
- **Surface**: 0.3 (abundant for sustainability)
- **Underground**: 0.5 (rare for strategic value)
- **Mountains**: 0.4 (moderately rare for end-game content)

#### Economic Balance Parameters
- **Surface Resource Values**: Low individual value, high sustainability
- **Underground Resource Values**: High individual value, finite supply
- **Mountain Resource Values**: Premium value, quality bonus multipliers

## Implementation Checklist

### Prerequisites
- [ ] Existing layered world generation system is working
- [ ] Terrain types and WorldLayer enum are defined
- [ ] Chunk-based generation pipeline is established
- [ ] Noise generation utilities are available

### Core Implementation Tasks

#### Phase 1: Infrastructure (Estimated: 4-6 hours)
- [ ] Create `ResourceType` enum with all resource categories
- [ ] Implement `ResourceCluster` and `ResourceNode` dataclasses
- [ ] Define resource character mappings for all rarity levels
- [ ] Set up terrain compatibility rules dictionary
- [ ] Create `ClusteredResourceGenerator` class skeleton

#### Phase 2: Cluster Generation (Estimated: 6-8 hours)
- [ ] Implement noise-based cluster center detection
- [ ] Add layer-specific cluster finding with different sampling patterns
- [ ] Create cluster property calculation (radius, density, intensity)
- [ ] Implement resource type determination based on noise and layer
- [ ] Add terrain filtering for cluster validation

#### Phase 3: Node Population (Estimated: 4-6 hours)
- [ ] Implement cluster population with distance-based probability
- [ ] Add density noise for fine-grained placement variation
- [ ] Create rarity calculation system
- [ ] Implement resource character selection
- [ ] Add resource node creation with proper metadata

#### Phase 4: Integration (Estimated: 3-4 hours)
- [ ] Modify world generator to call resource generation
- [ ] Update chunk generation pipeline
- [ ] Implement resource application to terrain objects
- [ ] Add resource data storage for harvesting system
- [ ] Test cross-chunk cluster consistency

#### Phase 5: Testing & Balancing (Estimated: 4-6 hours)
- [ ] Create unit tests for cluster generation
- [ ] Test resource distribution across different biomes
- [ ] Validate terrain compatibility rules
- [ ] Performance test with large world generation
- [ ] Balance resource spawn rates and cluster sizes
- [ ] Fine-tune rarity distributions

### File Structure
```
src/
├── world_generation/
│   ├── resource_generation.py     # Main resource generator
│   ├── resource_types.py          # Enums and data classes
│   └── resource_config.py         # Configuration constants
├── tests/
│   └── test_resource_generation.py
└── docs/
    └── resource_generation.md     # This document
```

### Testing Strategy

#### Unit Tests
- Test cluster center detection with known noise values
- Verify terrain compatibility filtering
- Test resource node placement within clusters
- Validate rarity calculation algorithms

#### Integration Tests
- Generate test chunks and verify resource distribution
- Test resource application to terrain objects
- Verify cross-chunk cluster consistency
- Performance test with various chunk sizes

#### Visual Testing
- Generate test worlds and inspect resource placement
- Verify appropriate resource density in different biomes
- Check visual character selection and display
- Test resource clustering patterns

### Configuration Tuning

#### Resource Density
- Adjust cluster spawn thresholds per layer
- Modify cluster size and density parameters
- Balance resource node spawn probability
- Fine-tune rarity distribution curves

#### Performance Optimization
- Profile noise generation performance
- Optimize cluster detection algorithms
- Implement caching for repeated calculations
- Consider parallel processing for large chunks

## Reference Implementation

The complete algorithm implementation is provided below for reference during development.

### Resource Configuration
```python
RESOURCE_YIELDS = {
    'common': 1,
    'rare': 2,
    'epic': 4
}

# Resource character mappings by layer and rarity
RESOURCE_CHARACTERS = {
    # SURFACE LAYER
    ResourceType.WOOD: {
        'common': ['♣', '♠', 'T'],
        'rare': ['🌲', 'Y', '†'],
        'epic': ['🌳', '♧', 'ᛏ']
    },
    ResourceType.FOOD_SURFACE: {
        'common': ['•', '∘', '○'],           # Berries, small game
        'rare': ['●', '◉', '❀'],            # Fruit trees, larger game
        'epic': ['🍄', '🌸', '🍇']           # Special foods, rare plants
    },
    # ... (additional resource character mappings)
}
```

### Core Generator Class
The `ClusteredResourceGenerator` class implements the main algorithm with these key methods:

- `generate_layered_resource_clusters()`: Main entry point for generating resources across all layers
- `_find_layer_specific_clusters()`: Detects cluster centers using layer-specific noise patterns
- `_get_layer_threshold()`: Returns appropriate spawn thresholds for each layer
- `_get_layer_cluster_properties()`: Calculates layer-specific cluster size and density
- `_determine_cluster_resource_type()`: Selects resource type based on noise and layer
- `_filter_clusters_by_layer_terrain()`: Validates clusters against terrain compatibility
- `_populate_layer_cluster()`: Generates individual resource nodes within clusters

### Integration Function
```python
def add_resources_to_chunk(chunk_terrain_data, chunk_x, chunk_y, seed, chunk_size=32):
    """Add this to your existing world generation pipeline"""

    resource_generator = ClusteredResourceGenerator(seed)
    resource_nodes = resource_generator.generate_layered_resource_clusters(
        chunk_x, chunk_y, chunk_terrain_data, chunk_size
    )

    # Apply resources to terrain data for each layer
    for layer, nodes in resource_nodes.items():
        for node in nodes:
            if (node.x, node.y) in chunk_terrain_data[layer]:
                terrain = chunk_terrain_data[layer][(node.x, node.y)]
                terrain.char = node.char  # Update display character
                terrain.resource = node   # Store resource data

    return chunk_terrain_data
```

## Next Steps

1. **Start with Phase 1**: Create the basic data structures and enums
2. **Implement Core Algorithm**: Build the cluster generation logic step by step
3. **Test Early and Often**: Create simple test cases for each component
4. **Integrate Gradually**: Add resource generation to world pipeline incrementally
5. **Balance and Tune**: Adjust parameters based on gameplay testing

## Success Criteria

### Technical Requirements
- Resources appear in realistic clusters rather than scattered randomly
- Different layers have appropriate resource types and densities
- Resources only spawn on compatible terrain types
- Performance remains acceptable for large world generation
- Cross-chunk cluster consistency maintained

### Strategic Gameplay Requirements
- **Vertical Resource Competition**: Players must control territory across all three layers
- **Economic Progression**: Clear early/mid/late game resource pathways
- **Strategic Depth**: Meaningful choices between surface sustainability vs underground wealth vs mountain quality
- **Territorial Value**: Different regions valuable for different layer combinations
- **Resource Accessibility**: Surface easy, underground requires caves, mountains dangerous

### Balance Validation
- Surface resources provide sustainable early-game foundation
- Underground resources enable military/technological advancement
- Mountain resources unlock massive late-game construction projects
- No single layer dominates optimal strategy
- Resource scarcity creates meaningful territorial competition

## Implementation Impact

This layered resource system will transform empire-building strategy by:

1. **Creating Vertical Territory Control**: Players must think in 3D about territorial expansion
2. **Enabling Economic Specialization**: Different empires can focus on different layer strategies
3. **Adding Strategic Depth**: Resource accessibility vs value trade-offs
4. **Encouraging Exploration**: Players must scout all three layers for optimal settlements
5. **Balancing Risk vs Reward**: Dangerous mountain/underground access for premium resources

The result is a rich, strategically deep resource system that maintains the organic feel of procedural generation while adding meaningful empire-building decisions at every stage of the game.
    
    def _find_cluster_centers(self, world_x: int, world_y: int, size: int) -> List[ResourceCluster]:
        """Find potential cluster centers using noise - creates large resource areas"""
        clusters = []
        
        # Sample a larger area to catch clusters that extend into this chunk
        search_radius = size // 2
        
        for sample_y in range(-search_radius, size + search_radius, 8):  # Sample every 8 tiles
            for sample_x in range(-search_radius, size + search_radius, 8):
                check_x = world_x + sample_x
                check_y = world_y + sample_y
                
                # Use noise to determine if this is a cluster center
                cluster_noise = self.noise_cluster.octave_noise(
                    check_x * self.cluster_scale,
                    check_y * self.cluster_scale,
                    octaves=3,
                    persistence=0.6
                )
                
                # Only create clusters at noise peaks (creates separation)
                if cluster_noise > 0.4:  # High threshold for sparse, large clusters
                    
                    # Determine cluster properties based on noise
                    radius = 8 + (cluster_noise * 12)  # 8-20 tile radius
                    density = 0.1 + (abs(cluster_noise) * 0.3)  # 10-40% density
                    
                    # Resource type based on noise frequency
                    resource_type = self._determine_cluster_resource_type(check_x, check_y, cluster_noise)
                    
                    clusters.append(ResourceCluster(
                        center_x=check_x,
                        center_y=check_y,
                        resource_type=resource_type,
                        radius=radius,
                        density=density,
                        intensity=cluster_noise
                    ))
        
        return clusters
    
    def _determine_cluster_resource_type(self, x: int, y: int, base_noise: float, layer: WorldLayer) -> ResourceType:
        """Determine what type of resource cluster based on layer and noise"""
        
        type_noise = self.noise_cluster.noise(x * 0.001, y * 0.001)
        
        if layer == WorldLayer.SURFACE:
            # Surface resources - life and basic materials
            if base_noise > 0.7:  # Rich surface areas
                if type_noise > 0.3:
                    return ResourceType.WOOD  # Dense forests
                elif type_noise > 0:
                    return ResourceType.FOOD_SURFACE  # Fertile valleys
                else:
                    return ResourceType.STONE_SURFACE  # Surface quarries
            else:  # Common surface resources
                if type_noise > 0:
                    return ResourceType.WOOD
                else:
                    return ResourceType.FOOD_SURFACE
                    
        elif layer == WorldLayer.UNDERGROUND:
            # Underground resources - valuable minerals and metals
            if base_noise > 0.8:  # Very rich underground areas
                if type_noise > 0.5:
                    return ResourceType.CRYSTAL  # Rare magical crystals
                elif type_noise > 0:
                    return ResourceType.GOLD  # Gold veins
                else:
                    return ResourceType.GEMS  # Gem deposits
            elif base_noise > 0.6:  # Rich underground
                if type_noise > 0.3:
                    return ResourceType.GOLD
                elif type_noise > 0:
                    return ResourceType.IRON
                else:
                    return ResourceType.COAL
            else:  # Common underground
                if type_noise > 0.5:
                    return ResourceType.IRON
                elif type_noise > 0:
                    return ResourceType.COAL
                else:
                    return ResourceType.UNDERGROUND_WATER
                    
        elif layer == WorldLayer.MOUNTAINS:
            # Mountain resources - high-quality stone and rare materials
            if base_noise > 0.7:  # Rich mountain areas
                if type_noise > 0.5:
                    return ResourceType.RARE_GEMS  # Mountain gem veins
                elif type_noise > 0:
                    return ResourceType.METAL_MOUNTAIN  # Surface metal deposits
                else:
                    return ResourceType.STONE_MOUNTAIN  # Massive quarries
            else:  # Common mountain resources
                if type_noise > 0.3:
                    return ResourceType.STONE_MOUNTAIN
                elif type_noise > 0:
                    return ResourceType.ICE  # High altitude ice
                else:
                    return ResourceType.METAL_MOUNTAIN
        
        # Fallback
        return ResourceType.WOOD
    
    def _filter_clusters_by_terrain(self, clusters: List[ResourceCluster], 
                                  terrain_data: Dict, world_x: int, world_y: int, 
                                  chunk_size: int) -> List[ResourceCluster]:
        """Only keep clusters that match appropriate terrain"""
        
        # Terrain compatibility rules
        TERRAIN_COMPATIBILITY = {
            ResourceType.WOOD: [TerrainType.GRASSLAND, TerrainType.FOREST],
            ResourceType.STONE: [TerrainType.HILLS, TerrainType.GRASSLAND],
            ResourceType.FOOD: [TerrainType.FERTILE, TerrainType.GRASSLAND, TerrainType.FOREST],
            ResourceType.GOLD: [TerrainType.CAVES, TerrainType.HILLS],
            ResourceType.IRON: [TerrainType.CAVES, TerrainType.HILLS],
            ResourceType.GEMS: [TerrainType.CAVES]
        }
        
        valid_clusters = []
        
        for cluster in clusters:
            # Check if cluster center or nearby area has suitable terrain
            suitable_terrain_found = False
            
            # Sample terrain around cluster center
            sample_radius = min(5, int(cluster.radius // 2))
            for dy in range(-sample_radius, sample_radius + 1, 2):
                for dx in range(-sample_radius, sample_radius + 1, 2):
                    sample_x = cluster.center_x + dx
                    sample_y = cluster.center_y + dy
                    
                    # Convert to chunk-local coordinates
                    local_x = sample_x - world_x
                    local_y = sample_y - world_y
                    
                    # Check if this position is in our chunk and has terrain data
                    if 0 <= local_x < chunk_size and 0 <= local_y < chunk_size:
                        if (local_x, local_y) in terrain_data:
                            terrain_type = terrain_data[(local_x, local_y)].terrain_type
                            if terrain_type in TERRAIN_COMPATIBILITY.get(cluster.resource_type, []):
                                suitable_terrain_found = True
                                break
                
                if suitable_terrain_found:
                    break
            
            if suitable_terrain_found:
                valid_clusters.append(cluster)
        
        return valid_clusters
    
    def _populate_cluster(self, cluster: ResourceCluster, terrain_data: Dict,
                         world_x: int, world_y: int, chunk_size: int) -> List[ResourceNode]:
        """Fill a cluster with individual resource nodes"""
        
        resource_nodes = []
        cluster_radius_squared = cluster.radius * cluster.radius
        
        # Check every position within the cluster radius
        min_x = max(0, int(cluster.center_x - cluster.radius) - world_x)
        max_x = min(chunk_size, int(cluster.center_x + cluster.radius) - world_x + 1)
        min_y = max(0, int(cluster.center_y - cluster.radius) - world_y)  
        max_y = min(chunk_size, int(cluster.center_y + cluster.radius) - world_y + 1)
        
        for local_y in range(min_y, max_y):
            for local_x in range(min_x, max_x):
                world_pos_x = world_x + local_x
                world_pos_y = world_y + local_y
                
                # Check if position is within cluster radius
                dx = world_pos_x - cluster.center_x
                dy = world_pos_y - cluster.center_y
                distance_squared = dx * dx + dy * dy
                
                if distance_squared <= cluster_radius_squared:
                    # Check terrain compatibility
                    if (local_x, local_y) not in terrain_data:
                        continue
                    
                    terrain_type = terrain_data[(local_x, local_y)].terrain_type
                    if not self._is_terrain_suitable(cluster.resource_type, terrain_type):
                        continue
                    
                    # Use density noise to determine if resource spawns here
                    density_noise = self.noise_density.noise(
                        world_pos_x * self.density_scale,
                        world_pos_y * self.density_scale
                    )
                    
                    # Distance from cluster center affects spawn probability
                    distance_factor = 1.0 - (math.sqrt(distance_squared) / cluster.radius)
                    spawn_probability = cluster.density * distance_factor
                    
                    # Apply noise variation
                    final_probability = spawn_probability + (density_noise * 0.2)
                    
                    if final_probability > 0.3:  # Spawn resource node
                        
                        # Determine resource rarity based on cluster intensity and distance
                        rarity_noise = self.noise_rarity.noise(
                            world_pos_x * self.rarity_scale,
                            world_pos_y * self.rarity_scale
                        )
                        
                        rarity_score = cluster.intensity * distance_factor + rarity_noise
                        
                        if rarity_score > 0.8:
                            rarity = 'epic'
                        elif rarity_score > 0.6:
                            rarity = 'rare'  
                        else:
                            rarity = 'common'
                        
                        # Select character and create resource node
                        char = self._select_resource_character(cluster.resource_type, rarity)
                        
                        resource_nodes.append(ResourceNode(
                            x=local_x,
                            y=local_y, 
                            resource_type=cluster.resource_type,
                            char=char,
                            yield_amount=RESOURCE_YIELDS[rarity],
                            respawns=cluster.resource_type in [ResourceType.WOOD, ResourceType.FOOD]
                        ))
        
        return resource_nodes
    
    def _is_terrain_suitable(self, resource_type: ResourceType, terrain_type) -> bool:
        """Check if terrain can support this resource type"""
        compatibility = {
            ResourceType.WOOD: ['grassland', 'forest'],
            ResourceType.STONE: ['hills', 'grassland', 'mountains'],
            ResourceType.FOOD: ['fertile', 'grassland', 'forest'],
            ResourceType.GOLD: ['caves', 'hills'],
            ResourceType.IRON: ['caves', 'hills'],  
            ResourceType.GEMS: ['caves']
        }
        
        return terrain_type.value in compatibility.get(resource_type, [])
    
    def _select_resource_character(self, resource_type: ResourceType, rarity: str) -> str:
        """Select appropriate character for resource type and rarity"""
        chars = RESOURCE_CHARACTERS.get(resource_type, {}).get(rarity, ['○'])
        return random.choice(chars)

# Simple noise generator (use your existing implementation)
class NoiseGenerator:
    def __init__(self, seed):
        random.seed(seed)
        
    def noise(self, x, y):
        return math.sin(x * 12.9898 + y * 78.233) * 43758.5453 % 1.0 * 2 - 1
        
    def octave_noise(self, x, y, octaves=4, persistence=0.5):
        value = 0
        amplitude = 1
        frequency = 1
        max_value = 0
        
        for _ in range(octaves):
            value += self.noise(x * frequency, y * frequency) * amplitude
            max_value += amplitude
            amplitude *= persistence
            frequency *= 2
        
        return value / max_value

# Integration with existing world generator
def add_resources_to_chunk(chunk_terrain_data, chunk_x, chunk_y, seed, chunk_size=32):
    """Add this to your existing world generation pipeline"""
    
    resource_generator = ClusteredResourceGenerator(seed)
    resource_nodes = resource_generator.generate_resource_clusters_for_chunk(
        chunk_x, chunk_y, chunk_terrain_data, chunk_size
    )
    
    # Apply resources to terrain data
    for node in resource_nodes:
        if (node.x, node.y) in chunk_terrain_data:
            terrain = chunk_terrain_data[(node.x, node.y)]
            # Modify terrain character to show resource
            terrain.char = node.char
            # Store resource data for harvesting
            terrain.resource = node
    
    return chunk_terrain_data

# Usage example:
# After generating terrain in your world generator:
# chunk_data = generator.generate_chunk(chunk_x=0, chunk_y=0)
# chunk_data = add_resources_to_chunk(chunk_data, 0, 0, seed=12345), '●'],            # Gold nuggets, small veins
        'epic': ['💰', '⭐', '♦']            # Rich gold veins, motherlodes
    },
    ResourceType.IRON: {
        'common': ['▲', '▼', '◦'],          # Iron ore chunks
        'rare': ['■', '◆', '●'],           # Iron ore seams
        'epic': ['⬛', '♦', '▣']            # Rich iron deposits
    },
    ResourceType.COAL: {
        'common': ['●', '◘', '○'],          # Coal chunks
        'rare': ['■', '▪', '◙'],           # Coal seams
        'epic': ['⬛', '▓', '█']            # Rich coal veins
    },
    ResourceType.GEMS: {
        'common': ['◊', '◇', '○'],          # Small gems
        'rare': ['♦', '✦', '●'],           # Quality gems
        'epic': ['💎', '★', '✧']           # Precious gems
    },
    ResourceType.CRYSTAL: {
        'common': ['◊', '○', '∘'],          # Crystal shards
        'rare': ['♦', '✦', '◆'],           # Crystal formations
        'epic': ['🔮', '⭐', '✨']           # Rare magical crystals
    },
    ResourceType.UNDERGROUND_WATER: {
        'common': ['~', '∼', '◦'],          # Underground streams
        'rare': ['≈', '●', '○'],           # Underground pools
        'epic': ['💧', '🌊', '◉']          # Underground lakes
    },
    
    # MOUNTAIN LAYER
    ResourceType.STONE_MOUNTAIN: {
        'common': ['▲', '^', '◦'],          # Mountain stone
        'rare': ['▲', '⩙', '●'],          # Quality stone quarries
        'epic': ['⛰️', '▲', '■']            # Massive stone deposits
    },
    ResourceType.METAL_MOUNTAIN: {
        'common': ['▲', '▼', '◦'],         # Surface metal ore
        'rare': ['♦', '◆', '●'],          # Rich surface deposits
        'epic': ['⬛', '▣', '■']           # Massive surface mines
    },
    ResourceType.RARE_GEMS: {
        'common': ['◊', '◇', '○'],         # Mountain gems
        'rare': ['♦', '✦', '●'],          # Rare mountain gems
        'epic': ['💎', '⭐', '✨']          # Legendary mountain gems
    },
    ResourceType.ICE: {
        'common': ['∘', '○', '◦'],         # Ice chunks
        'rare': ['●', '◉', '◎'],          # Ice formations
        'epic': ['❄️', '🧊', '⭐']          # Eternal ice, glaciers
    }
}

RESOURCE_YIELDS = {
    'common': 1,
    'rare': 2, 
    'epic': 4
}

class ClusteredResourceGenerator:
    """Generates large resource clusters instead of scattered individual nodes"""
    
    def __init__(self, seed: int):
        self.seed = seed
        self.noise_cluster = NoiseGenerator(seed + 6000)
        self.noise_density = NoiseGenerator(seed + 7000) 
        self.noise_rarity = NoiseGenerator(seed + 8000)
        
        # Cluster generation parameters
        self.cluster_scale = 0.003  # How spread out cluster centers are
        self.density_scale = 0.02   # Variation within clusters
        self.rarity_scale = 0.05    # Fine-grained rarity variation
        
    def generate_resource_clusters_for_chunk(self, chunk_x: int, chunk_y: int, 
                                           terrain_data: Dict, chunk_size: int = 32) -> List[ResourceNode]:
        """Generate clustered resources for a chunk"""
        
        world_offset_x = chunk_x * chunk_size
        world_offset_y = chunk_y * chunk_size
        
        # Phase 1: Identify potential cluster centers in and around this chunk
        potential_clusters = self._find_cluster_centers(world_offset_x, world_offset_y, chunk_size)
        
        # Phase 2: Filter clusters by terrain suitability  
        valid_clusters = self._filter_clusters_by_terrain(potential_clusters, terrain_data, 
                                                        world_offset_x, world_offset_y, chunk_size)
        
        # Phase 3: Generate individual resource nodes within clusters
        resource_nodes = []
        for cluster in valid_clusters:
            nodes = self._populate_cluster(cluster, terrain_data, world_offset_x, world_offset_y, chunk_size)
            resource_nodes.extend(nodes)
        
        return resource_nodes
    
    def _find_cluster_centers(self, world_x: int, world_y: int, size: int) -> List[ResourceCluster]:
        """Find potential cluster centers using noise - creates large resource areas"""
        clusters = []
        
        # Sample a larger area to catch clusters that extend into this chunk
        search_radius = size // 2
        
        for sample_y in range(-search_radius, size + search_radius, 8):  # Sample every 8 tiles
            for sample_x in range(-search_radius, size + search_radius, 8):
                check_x = world_x + sample_x
                check_y = world_y + sample_y
                
                # Use noise to determine if this is a cluster center
                cluster_noise = self.noise_cluster.octave_noise(
                    check_x * self.cluster_scale,
                    check_y * self.cluster_scale,
                    octaves=3,
                    persistence=0.6
                )
                
                # Only create clusters at noise peaks (creates separation)
                if cluster_noise > 0.4:  # High threshold for sparse, large clusters
                    
                    # Determine cluster properties based on noise
                    radius = 8 + (cluster_noise * 12)  # 8-20 tile radius
                    density = 0.1 + (abs(cluster_noise) * 0.3)  # 10-40% density
                    
                    # Resource type based on noise frequency
                    resource_type = self._determine_cluster_resource_type(check_x, check_y, cluster_noise)
                    
                    clusters.append(ResourceCluster(
                        center_x=check_x,
                        center_y=check_y,
                        resource_type=resource_type,
                        radius=radius,
                        density=density,
                        intensity=cluster_noise
                    ))
        
        return clusters
    
    def _determine_cluster_resource_type(self, x: int, y: int, base_noise: float) -> ResourceType:
        """Determine what type of resource cluster this should be"""
        
        # Use different noise frequency to determine resource type
        type_noise = self.noise_cluster.noise(x * 0.001, y * 0.001)
        
        # Bias resource types based on the noise value ranges
        if base_noise > 0.7:  # Very high noise = precious resources
            return ResourceType.GOLD if type_noise > 0 else ResourceType.GEMS
        elif base_noise > 0.6:  # High noise = metals
            return ResourceType.IRON if type_noise > 0 else ResourceType.STONE  
        elif base_noise > 0.5:  # Medium-high = common resources
            return ResourceType.WOOD if type_noise > 0 else ResourceType.FOOD
        else:  # Lower values = basic resources
            return ResourceType.WOOD
    
    def _filter_clusters_by_terrain(self, clusters: List[ResourceCluster], 
                                  terrain_data: Dict, world_x: int, world_y: int, 
                                  chunk_size: int) -> List[ResourceCluster]:
        """Only keep clusters that match appropriate terrain"""
        
        # Terrain compatibility rules
        TERRAIN_COMPATIBILITY = {
            ResourceType.WOOD: [TerrainType.GRASSLAND, TerrainType.FOREST],
            ResourceType.STONE: [TerrainType.HILLS, TerrainType.GRASSLAND],
            ResourceType.FOOD: [TerrainType.FERTILE, TerrainType.GRASSLAND, TerrainType.FOREST],
            ResourceType.GOLD: [TerrainType.CAVES, TerrainType.HILLS],
            ResourceType.IRON: [TerrainType.CAVES, TerrainType.HILLS],
            ResourceType.GEMS: [TerrainType.CAVES]
        }
        
        valid_clusters = []
        
        for cluster in clusters:
            # Check if cluster center or nearby area has suitable terrain
            suitable_terrain_found = False
            
            # Sample terrain around cluster center
            sample_radius = min(5, int(cluster.radius // 2))
            for dy in range(-sample_radius, sample_radius + 1, 2):
                for dx in range(-sample_radius, sample_radius + 1, 2):
                    sample_x = cluster.center_x + dx
                    sample_y = cluster.center_y + dy
                    
                    # Convert to chunk-local coordinates
                    local_x = sample_x - world_x
                    local_y = sample_y - world_y
                    
                    # Check if this position is in our chunk and has terrain data
                    if 0 <= local_x < chunk_size and 0 <= local_y < chunk_size:
                        if (local_x, local_y) in terrain_data:
                            terrain_type = terrain_data[(local_x, local_y)].terrain_type
                            if terrain_type in TERRAIN_COMPATIBILITY.get(cluster.resource_type, []):
                                suitable_terrain_found = True
                                break
                
                if suitable_terrain_found:
                    break
            
            if suitable_terrain_found:
                valid_clusters.append(cluster)
        
        return valid_clusters
    
    def _populate_cluster(self, cluster: ResourceCluster, terrain_data: Dict,
                         world_x: int, world_y: int, chunk_size: int) -> List[ResourceNode]:
        """Fill a cluster with individual resource nodes"""
        
        resource_nodes = []
        cluster_radius_squared = cluster.radius * cluster.radius
        
        # Check every position within the cluster radius
        min_x = max(0, int(cluster.center_x - cluster.radius) - world_x)
        max_x = min(chunk_size, int(cluster.center_x + cluster.radius) - world_x + 1)
        min_y = max(0, int(cluster.center_y - cluster.radius) - world_y)  
        max_y = min(chunk_size, int(cluster.center_y + cluster.radius) - world_y + 1)
        
        for local_y in range(min_y, max_y):
            for local_x in range(min_x, max_x):
                world_pos_x = world_x + local_x
                world_pos_y = world_y + local_y
                
                # Check if position is within cluster radius
                dx = world_pos_x - cluster.center_x
                dy = world_pos_y - cluster.center_y
                distance_squared = dx * dx + dy * dy
                
                if distance_squared <= cluster_radius_squared:
                    # Check terrain compatibility
                    if (local_x, local_y) not in terrain_data:
                        continue
                    
                    terrain_type = terrain_data[(local_x, local_y)].terrain_type
                    if not self._is_terrain_suitable(cluster.resource_type, terrain_type):
                        continue
                    
                    # Use density noise to determine if resource spawns here
                    density_noise = self.noise_density.noise(
                        world_pos_x * self.density_scale,
                        world_pos_y * self.density_scale
                    )
                    
                    # Distance from cluster center affects spawn probability
                    distance_factor = 1.0 - (math.sqrt(distance_squared) / cluster.radius)
                    spawn_probability = cluster.density * distance_factor
                    
                    # Apply noise variation
                    final_probability = spawn_probability + (density_noise * 0.2)
                    
                    if final_probability > 0.3:  # Spawn resource node
                        
                        # Determine resource rarity based on cluster intensity and distance
                        rarity_noise = self.noise_rarity.noise(
                            world_pos_x * self.rarity_scale,
                            world_pos_y * self.rarity_scale
                        )
                        
                        rarity_score = cluster.intensity * distance_factor + rarity_noise
                        
                        if rarity_score > 0.8:
                            rarity = 'epic'
                        elif rarity_score > 0.6:
                            rarity = 'rare'  
                        else:
                            rarity = 'common'
                        
                        # Select character and create resource node
                        char = self._select_resource_character(cluster.resource_type, rarity)
                        
                        resource_nodes.append(ResourceNode(
                            x=local_x,
                            y=local_y, 
                            resource_type=cluster.resource_type,
                            char=char,
                            yield_amount=RESOURCE_YIELDS[rarity],
                            respawns=cluster.resource_type in [ResourceType.WOOD, ResourceType.FOOD]
                        ))
        
        return resource_nodes
    
    def _is_terrain_suitable(self, resource_type: ResourceType, terrain_type) -> bool:
        """Check if terrain can support this resource type"""
        compatibility = {
            ResourceType.WOOD: ['grassland', 'forest'],
            ResourceType.STONE: ['hills', 'grassland', 'mountains'],
            ResourceType.FOOD: ['fertile', 'grassland', 'forest'],
            ResourceType.GOLD: ['caves', 'hills'],
            ResourceType.IRON: ['caves', 'hills'],  
            ResourceType.GEMS: ['caves']
        }
        
        return terrain_type.value in compatibility.get(resource_type, [])
    
    def _select_resource_character(self, resource_type: ResourceType, rarity: str) -> str:
        """Select appropriate character for resource type and rarity"""
        chars = RESOURCE_CHARACTERS.get(resource_type, {}).get(rarity, ['○'])
        return random.choice(chars)

# Simple noise generator (use your existing implementation)
class NoiseGenerator:
    def __init__(self, seed):
        random.seed(seed)
        
    def noise(self, x, y):
        return math.sin(x * 12.9898 + y * 78.233) * 43758.5453 % 1.0 * 2 - 1
        
    def octave_noise(self, x, y, octaves=4, persistence=0.5):
        value = 0
        amplitude = 1
        frequency = 1
        max_value = 0
        
        for _ in range(octaves):
            value += self.noise(x * frequency, y * frequency) * amplitude
            max_value += amplitude
            amplitude *= persistence
            frequency *= 2
        
        return value / max_value

# Integration with existing world generator
def add_resources_to_chunk(chunk_terrain_data, chunk_x, chunk_y, seed, chunk_size=32):
    """Add this to your existing world generation pipeline"""
    
    resource_generator = ClusteredResourceGenerator(seed)
    resource_nodes = resource_generator.generate_resource_clusters_for_chunk(
        chunk_x, chunk_y, chunk_terrain_data, chunk_size
    )
    
    # Apply resources to terrain data
    for node in resource_nodes:
        if (node.x, node.y) in chunk_terrain_data:
            terrain = chunk_terrain_data[(node.x, node.y)]
            # Modify terrain character to show resource
            terrain.char = node.char
            # Store resource data for harvesting
            terrain.resource = node
    
    return chunk_terrain_data

# Usage example:
# After generating terrain in your world generator:
# chunk_data = generator.generate_chunk(chunk_x=0, chunk_y=0)
# chunk_data = add_resources_to_chunk(chunk_data, 0, 0, seed=12345)