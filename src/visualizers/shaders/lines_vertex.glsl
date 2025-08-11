#version 330 core

layout(location = 0) in float x_position;
layout(location = 1) in float height;

uniform float widget_width;
uniform float widget_height;

out float v_height;
out vec2 v_position;

void main() {
    // Scale x to screen width, scale y by audio height (don't flip Y)
    vec2 final_pos = vec2(x_position * widget_width, 
                        height * widget_height);
    
    // Convert to normalized device coordinates
    gl_Position = vec4((final_pos.x / widget_width) * 2.0 - 1.0, 
                      1.0 - (final_pos.y / widget_height) * 2.0, 
                      0.0, 1.0);
    
    v_height = height;
    v_position = final_pos;
}
