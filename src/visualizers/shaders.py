"""
GPU shader definitions for gvis visualizers.
Contains shader loading utilities and functions to access shader files.
"""

import os
from pathlib import Path

def get_shader_path() -> Path:
    """Get the path to the shaders directory."""
    return Path(__file__).parent / "shaders"

def load_shader(shader_name: str) -> str:
    """
    Load a shader from a .glsl file.
    
    Args:
        shader_name: Name of the shader file (without .glsl extension)
        
    Returns:
        The shader source code as a string
        
    Raises:
        FileNotFoundError: If the shader file doesn't exist
        IOError: If there's an error reading the file
    """
    shader_path = get_shader_path() / f"{shader_name}.glsl"
    
    if not shader_path.exists():
        raise FileNotFoundError(f"Shader file not found: {shader_path}")
    
    try:
        with open(shader_path, 'r', encoding='utf-8') as f:
            return f.read()
    except IOError as e:
        raise IOError(f"Error reading shader file {shader_path}: {e}")

# Lazy loading of shaders - only load when first accessed
_shader_cache = {}

def get_common_fragment_shader() -> str:
    """Get the common fragment shader source."""
    if 'common_fragment' not in _shader_cache:
        _shader_cache['common_fragment'] = load_shader('common_fragment')
    return _shader_cache['common_fragment']

def get_bars_vertex_shader() -> str:
    """Get the bars vertex shader source."""
    if 'bars_vertex' not in _shader_cache:
        _shader_cache['bars_vertex'] = load_shader('bars_vertex')
    return _shader_cache['bars_vertex']

def get_lines_vertex_shader() -> str:
    """Get the lines vertex shader source."""
    if 'lines_vertex' not in _shader_cache:
        _shader_cache['lines_vertex'] = load_shader('lines_vertex')
    return _shader_cache['lines_vertex']

# For backward compatibility, provide the old constants as module-level variables
# These will be populated when first accessed via __getattr__

# Make them accessible as module-level attributes
def __getattr__(name):
    if name == 'COMMON_FRAGMENT_SHADER':
        return get_common_fragment_shader()
    elif name == 'BARS_VERTEX_SHADER':
        return get_bars_vertex_shader()
    elif name == 'LINES_VERTEX_SHADER':
        return get_lines_vertex_shader()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
