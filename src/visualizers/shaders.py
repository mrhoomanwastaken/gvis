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

def get_shader(shader_name: str) -> str:
    """
    Get any shader source with caching.
    
    Args:
        shader_name: Name of the shader file (without .glsl extension)
        
    Returns:
        The shader source code as a string
    """
    if shader_name not in _shader_cache:
        _shader_cache[shader_name] = load_shader(shader_name)
    return _shader_cache[shader_name]

def get_common_fragment_shader() -> str:
    """Get the common fragment shader source."""
    return get_shader('common_fragment')

def get_bars_vertex_shader() -> str:
    """Get the bars vertex shader source."""
    return get_shader('bars_vertex')

def get_lines_vertex_shader() -> str:
    """Get the lines vertex shader source."""
    return get_shader('lines_vertex')

def load_custom_shader(file_path: str) -> str:
    """
    Load a custom shader from any file path.
    
    Args:
        file_path: Full path to the shader file (with or without .glsl extension)
        
    Returns:
        The shader source code as a string
        
    Raises:
        FileNotFoundError: If the shader file doesn't exist
        IOError: If there's an error reading the file
    """
    # Add .glsl extension if not present
    if not file_path.endswith('.glsl'):
        file_path = f"{file_path}.glsl"
    
    # Convert to Path object for easier handling
    shader_path = Path(file_path)
    
    # If it's not an absolute path, treat it as relative to project root
    if not shader_path.is_absolute():
        # Get project root (assuming we're in src/visualizers/)
        project_root = Path(__file__).parent.parent.parent
        shader_path = project_root / shader_path
    
    if not shader_path.exists():
        raise FileNotFoundError(f"Custom shader file not found: {shader_path}")
    
    try:
        with open(shader_path, 'r', encoding='utf-8') as f:
            return f.read()
    except IOError as e:
        raise IOError(f"Error reading custom shader file {shader_path}: {e}")

def clear_shader_cache():
    """Clear the shader cache to force reloading of shaders."""
    global _shader_cache
    _shader_cache.clear()

def list_available_shaders() -> list:
    """
    List all available shader files in the shaders directory.
    
    Returns:
        List of shader names (without .glsl extension)
    """
    shader_dir = get_shader_path()
    shader_files = []
    
    if shader_dir.exists():
        for file_path in shader_dir.glob("*.glsl"):
            shader_files.append(file_path.stem)
    
    return sorted(shader_files)

def get_shaders_for_config(config: dict, vis_type: str = 'bars'):
    """
    Get vertex and fragment shaders based on configuration.
    Always uses default vertex shaders, optionally uses custom fragment shader.
    
    Args:
        config: Configuration dictionary from config_loader
        vis_type: Type of visualizer ('bars', 'lines', etc.)
        
    Returns:
        Tuple of (vertex_shader_source, fragment_shader_source)
    """
    # Always use default vertex shader for the given vis_type
    if vis_type == 'bars':
        vertex_shader = get_bars_vertex_shader()
    elif vis_type == 'lines':
        vertex_shader = get_lines_vertex_shader()
    else:
        # Try to load vertex shader for other vis types, fallback to bars
        try:
            vertex_shader = get_shader(f'{vis_type}_vertex')
        except FileNotFoundError:
            print(f"Warning: No vertex shader found for vis_type '{vis_type}', using bars vertex shader")
            vertex_shader = get_bars_vertex_shader()
    
    # Check if custom fragment shader is requested
    if config.get('custom_shader', False):
        fragment_path = config.get('fragment_shader')
        
        if not fragment_path:
            print("Warning: Custom shader enabled but fragment shader path not specified, using default")
            fragment_shader = get_common_fragment_shader()
        else:
            try:
                fragment_shader = load_custom_shader(fragment_path)
                print(f"Loaded custom fragment shader: {fragment_path}")
            except (FileNotFoundError, IOError) as e:
                print(f"Warning: Failed to load custom fragment shader ({e}), using default")
                fragment_shader = get_common_fragment_shader()
    else:
        # Use default fragment shader
        fragment_shader = get_common_fragment_shader()
    
    return vertex_shader, fragment_shader

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
    else:
        # Try to load as a generic shader
        try:
            # Convert constant-style name to shader file name
            shader_name = name.lower().replace('_shader', '').replace('_', '_')
            return get_shader(shader_name)
        except FileNotFoundError:
            pass
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
