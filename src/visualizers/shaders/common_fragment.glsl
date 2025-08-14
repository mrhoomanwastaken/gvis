/*
 * gvis - Common fragment shader
 * Copyright (C) 2025 mrhooman
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

#version 330 core

in float v_height;
in vec2 v_position;

uniform bool use_gradient;
uniform vec4 solid_color;
uniform int num_gradient_colors;
uniform float widget_width;
uniform float widget_height;
uniform vec4 gradient_points;  // x1, y1, x2, y2

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
        // Calculate gradient direction based on gradient_points
        // gradient_points = (x1, y1, x2, y2) in normalized coordinates
        vec2 grad_start = vec2(gradient_points.x * widget_width, gradient_points.y * widget_height);
        vec2 grad_end = vec2(gradient_points.z * widget_width, gradient_points.w * widget_height);
        
        // Current fragment position in screen coordinates
        vec2 frag_pos = vec2(gl_FragCoord.x, widget_height - gl_FragCoord.y);
        
        // Project fragment position onto gradient line
        vec2 grad_vec = grad_end - grad_start;
        vec2 frag_vec = frag_pos - grad_start;
        
        float grad_length_sq = dot(grad_vec, grad_vec);
        float gradient_t = 0.0;
        
        if (grad_length_sq > 0.0) {
            gradient_t = dot(frag_vec, grad_vec) / grad_length_sq;
        }
        
        gradient_t = clamp(gradient_t, 0.0, 1.0);
        
        // Calculate which segment we're in
        float segment_size = 1.0 / float(num_gradient_colors - 1);
        int segment = int(gradient_t / segment_size);
        segment = min(segment, num_gradient_colors - 2);
        
        // Calculate local t within the segment
        float local_t = (gradient_t - float(segment) * segment_size) / segment_size;
        
        // Get the two colors to interpolate between
        vec4 color1 = get_gradient_color(segment);
        vec4 color2 = get_gradient_color(segment + 1);
        
        // Interpolate
        fragment_color = mix(color1, color2, local_t);
    } else {
        fragment_color = solid_color;
    }
}
