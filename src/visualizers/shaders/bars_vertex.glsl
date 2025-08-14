/*
 * gvis - Bars vertex shader
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

layout(location = 0) in vec2 position;
layout(location = 1) in float height;
layout(location = 2) in float bar_index;

uniform float widget_width;
uniform float widget_height;
uniform int number_of_bars;

out float v_height;
out float v_bar_index;
out vec2 v_position;

void main() {
    float bar_width = widget_width / (number_of_bars * 2.0);
    float x_offset = bar_index * bar_width;
    
    vec2 final_pos = vec2(x_offset + position.x * bar_width, 
                        position.y * widget_height * height);
    
    // Convert to normalized device coordinates
    gl_Position = vec4((final_pos.x / widget_width) * 2.0 - 1.0, 
                      1.0 - (final_pos.y / widget_height) * 2.0, 
                      0.0, 1.0);
    
    v_height = height;
    v_bar_index = bar_index;
    v_position = final_pos;
}
