# Custom Fragment Shader System

The `gvis` project supports loading custom GLSL fragment shaders for visual effects while always using stable default vertex shaders.

## Features

### 1. Default Shaders
- `bars`: Uses `bars_vertex.glsl` + `common_fragment.glsl`
- `lines`: Uses `lines_vertex.glsl` + `common_fragment.glsl`

### 2. Custom Fragment Shaders
Specify a custom fragment shader in your `config.ini`:

```ini
[gvis]
CustomShader = True
FragmentShader = src/visualizers/shaders/my_custom_fragment.glsl
```

**Vertex shaders are always the appropriate defaults for stability.**

## Usage Examples

### Basic Configuration
```ini
[gvis]
vis_type = bars
CustomShader = True
FragmentShader = src/visualizers/shaders/rainbow_effect.glsl
```

### Fragment Shader Template
```glsl
#version 330 core

in float v_height;      // Audio amplitude (0.0 to 1.0)
in vec2 v_position;     // Screen position

uniform float widget_width;
uniform float widget_height;

out vec4 fragment_color;

void main() {
    vec2 uv = gl_FragCoord.xy / vec2(widget_width, widget_height);
    
    // Your custom effect here
    vec3 color = vec3(uv.x, v_height, uv.y);
    fragment_color = vec4(color, 1.0);
}
```

## Available Inputs

### Vertex Shader Outputs (Fragment Inputs)
- `v_height`: Audio amplitude (0.0 to 1.0)
- `v_position`: Screen position in pixels
- `v_bar_index`: Bar index (bars only)

### Essential Uniforms
- `widget_width`: Screen width in pixels
- `widget_height`: Screen height in pixels

### Optional Uniforms (may not be available in custom mode)
- `use_gradient`: Whether gradient is enabled
- `solid_color`: Solid color when not using gradient
- `num_gradient_colors`: Number of gradient colors
- `gradient_points`: Gradient direction
- `gradient_color0` to `gradient_color7`: Gradient colors

## Error Handling

The system gracefully handles missing uniforms, so your custom fragment shader only needs to declare the uniforms it actually uses.

## Examples

### Simple Audio-Reactive Color
```glsl
void main() {
    vec3 color = vec3(v_height, 0.5, 1.0 - v_height);
    fragment_color = vec4(color, 1.0);
}
```

### Position-Based Rainbow
```glsl
void main() {
    vec2 uv = gl_FragCoord.xy / vec2(widget_width, widget_height);
    vec3 color = vec3(uv.x, v_height, uv.y);
    fragment_color = vec4(color, 1.0);
}
```

This simplified approach provides visual customization while maintaining system stability!