# Shader Files

This directory contains GLSL shader files for gvis visualizations.

## License Information

### GPL-3.0 Licensed Shaders
The following shaders are part of the main gvis project and licensed under GPL-3.0:
- `bars_vertex.glsl` - Vertex shader for bars visualization
- `common_fragment.glsl` - Common fragment shader functionality
- `lines_vertex.glsl` - Vertex shader for lines visualization  
- `custom_fragment_gpl.glsl` - GPL-compatible custom fragment shader (default)

### Example Shaders (Separate License)
- `custom_fragment.glsl` - **EXAMPLE ONLY** - Licensed under CC BY-NC-SA 3.0
  - Originally from https://www.shadertoy.com/view/tsXBzS
  - Not included in compiled distributions
  - Provided for educational purposes and custom shader demonstration
  - Must comply with CC BY-NC-SA 3.0 license if used

## Usage

The default configuration uses `custom_fragment_gpl.glsl` which is fully GPL-3.0 compatible.

To use the example CC-licensed shader, users must:
1. Understand the CC BY-NC-SA 3.0 license restrictions
2. Manually configure gvis to use `custom_fragment.glsl` 
3. Comply with both licenses appropriately
