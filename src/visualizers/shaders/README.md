# GLSL Shaders for gvis Visualizers

This directory contains GPU shaders for the gvis audio visualization application.

## Shader Files

### `common_fragment.glsl`
The shared fragment shader used by both bars and lines visualizers. Supports:
- Solid color rendering
- Linear gradient rendering with up to 8 colors
- Configurable gradient direction via gradient_points uniform

### `bars_vertex.glsl`
Vertex shader for the bars visualizer. Handles:
- Bar positioning and instancing
- Per-bar height scaling
- Mirrored layout (left and right sides)

### `lines_vertex.glsl`
Vertex shader for the lines visualizer. Handles:
- Line point positioning
- Height-based Y coordinate scaling
- Linear interpolation between audio sample points

## Uniforms Used

### Common Fragment Shader Uniforms
- `use_gradient` (bool): Whether to use gradient or solid color
- `solid_color` (vec4): RGBA color for solid rendering
- `num_gradient_colors` (int): Number of gradient colors (max 8)
- `widget_width` (float): Widget width in pixels
- `widget_height` (float): Widget height in pixels
- `gradient_points` (vec4): Gradient direction (x1, y1, x2, y2) in normalized coordinates
- `gradient_color0` to `gradient_color7` (vec4): Individual gradient colors

### Vertex Shader Uniforms
- `widget_width` (float): Widget width in pixels
- `widget_height` (float): Widget height in pixels
- `number_of_bars` (int): Number of bars (bars visualizer only)

## Attributes/Inputs

### Bars Vertex Shader
- `position` (vec2): Quad vertex position (0-1 range)
- `height` (float): Audio sample height (0-1 range)
- `bar_index` (float): Index of the current bar for positioning

### Lines Vertex Shader
- `x_position` (float): X position along the line (0-1 range)
- `height` (float): Audio sample height (0-1 range)

## Output Variables
- `v_height` (float): Interpolated height value passed to fragment shader
- `v_position` (vec2): Screen position passed to fragment shader
- `v_bar_index` (float): Bar index (bars only, passed to fragment shader)
