"""
Visualizers package for gvis.
Contains different visualization types and shared shader loading utilities.
"""

# I dont really get the point of having an __init__.py file because this is not a package
# but PEP8 says to have one so here we are

from time import time
from .bars import BarsVisualizer
from .lines import LinesVisualizer
from .shaders import (
    get_common_fragment_shader,
    get_bars_vertex_shader, 
    get_lines_vertex_shader,
    load_shader,
    COMMON_FRAGMENT_SHADER,
    BARS_VERTEX_SHADER,
    LINES_VERTEX_SHADER
)
from .common import (
    Set_uniforms,
    initialize_gpu,
    on_draw_common
)


__all__ = [
    'BarsVisualizer',
    'LinesVisualizer', 
    'get_common_fragment_shader',
    'get_bars_vertex_shader',
    'get_lines_vertex_shader',
    'load_shader',
    'COMMON_FRAGMENT_SHADER',
    'BARS_VERTEX_SHADER',
    'LINES_VERTEX_SHADER',
    'Set_uniforms',
    'initialize_gpu',
    'on_draw_common'
]
