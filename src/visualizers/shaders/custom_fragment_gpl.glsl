/*
 * gvis - GPL-compatible custom fragment shader
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

uniform float iTime;
uniform vec2 iResolution;
uniform float avg_height;

out vec4 fragColor;

// Simple audio-reactive wave pattern
void main()
{
    vec2 fragCoord = gl_FragCoord.xy;
    vec2 uv = fragCoord / iResolution.xy;
    
    // Create a wave pattern based on audio input
    float wave = sin(uv.x * 10.0 + iTime * 2.0) * avg_height;
    wave += sin(uv.x * 20.0 + iTime * 3.0) * avg_height * 0.5;
    
    // Color based on wave intensity and position
    vec3 color = vec3(0.0);
    float intensity = abs(wave - (uv.y - 0.5)) * 10.0;
    intensity = 1.0 - smoothstep(0.0, 0.1, intensity);
    
    // Colorful gradient
    color.r = sin(uv.x + iTime) * 0.5 + 0.5;
    color.g = sin(uv.x + iTime + 2.094) * 0.5 + 0.5;
    color.b = sin(uv.x + iTime + 4.188) * 0.5 + 0.5;
    
    fragColor = vec4(color * intensity, 1.0);
}
