#version 330 core

in float v_height;
in vec2 v_position;

// Only require the essential uniforms that are always set
uniform float widget_width;
uniform float widget_height;

out vec4 fragment_color;

void main() {
    fragment_color = vec4(0.0, 0.0, v_height, 1.0); // Default to black
}
