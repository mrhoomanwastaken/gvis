#version 330 core

in float v_height;
in vec2 v_position;

uniform bool use_gradient;
uniform vec4 solid_color;
uniform int num_gradient_colors;
uniform float widget_width;
uniform float widget_height;
// gradient_points not needed for height-based gradient

// Simple approach: pass up to 8 gradient colors as individual uniforms
uniform vec4 gradient_color0;
uniform vec4 gradient_color1;
uniform vec4 gradient_color2;
uniform vec4 gradient_color3;
uniform vec4 gradient_color4;
uniform vec4 gradient_color5;
uniform vec4 gradient_color6;
uniform vec4 gradient_color7;

out vec4 fragment_color;

vec4 get_gradient_color(int index) {
    if (index == 0) return gradient_color0;
    if (index == 1) return gradient_color1;
    if (index == 2) return gradient_color2;
    if (index == 3) return gradient_color3;
    if (index == 4) return gradient_color4;
    if (index == 5) return gradient_color5;
    if (index == 6) return gradient_color6;
    if (index == 7) return gradient_color7;
    return vec4(1.0, 0.0, 1.0, 1.0); // Magenta for error
}

void main() {
    if (use_gradient && num_gradient_colors > 1) {
        // Use v_height directly for height-based gradient instead of position-based
        float gradient_t = clamp(v_height, 0.0, 1.0);
        
        // Use the exact same segment calculation as the working position-based version
        float segment_size = 1.0 / float(num_gradient_colors - 1);
        int segment = int(gradient_t / segment_size);
        segment = min(segment, num_gradient_colors - 2);
        
        // Calculate local t within the segment
        float local_t = (gradient_t - float(segment) * segment_size) / segment_size;
        
        // Get the two colors to interpolate between (same as working version)
        vec4 color1 = get_gradient_color(segment);
        vec4 color2 = get_gradient_color(segment + 1);
        
        // Interpolate
        fragment_color = mix(color1, color2, local_t);
    } else {
        fragment_color = solid_color;
    }
}
