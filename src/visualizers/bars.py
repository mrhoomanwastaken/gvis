"""
gvis - Bars visualizer
Copyright (C) 2025 mrhooman

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

# this was revamped to use gpu acceleration with moderngl
# by copilot because I am bad at opengl and shaders
# so because of that I would like someone to review this because it looks very inefficient
# same applies to lines.py 

import cairo
import numpy as np
from .shaders import COMMON_FRAGMENT_SHADER, BARS_VERTEX_SHADER, get_shaders_for_config
from .common import Set_uniforms, initialize_gpu, on_draw_common

try:
    import moderngl
    MODERNGL_AVAILABLE = True
except ImportError:
    MODERNGL_AVAILABLE = False
    print("ModernGL not available - falling back to CPU rendering")

class BarsVisualizer:
    def __init__(self, background_col, number_of_bars, fill, gradient, colors_list=None, num_colors=None, gradient_points=None, color=None, config=None, start_time=None):
        self.background_col = background_col
        self.number_of_bars = number_of_bars
        self.fill = fill
        self.gradient = gradient
        self.colors_list = colors_list
        self.num_colors = num_colors
        self.color = color
        self.gradient_points = gradient_points
        self.config = config  # Store config for shader loading
        self.sample = None
        self.bar_width = None
        self.gradient_pattern = None
        self.widget_width = None
        self.widget_height = None
        self.start_time = start_time

        # GPU resources
        self.ctx = None
        self.program = None
        self.vao = None
        self.vbo = None
        self.texture = None
        self.fbo = None
        self.initialized = False
        self.gpu_failed = False
        self.use_gpu = MODERNGL_AVAILABLE

    def _setup_shaders(self, config=None):
        """Set up GPU shaders with flexible loading."""
        if config and config.get('custom_shader', False):
            # Use config-based loading for custom shaders
            vertex_shader, fragment_shader = get_shaders_for_config(config, 'bars')
        else:
            # Use default shaders
            vertex_shader = BARS_VERTEX_SHADER
            fragment_shader = COMMON_FRAGMENT_SHADER
        
        self.program = self.ctx.program(
            vertex_shader=vertex_shader,
            fragment_shader=fragment_shader
        )

    def _setup_buffers(self):
        """Set up GPU buffers."""
        # Create vertex buffer for a single quad (will be instanced for each bar)
        vertices = np.array([
            # Position (x, y)
            0.0, 0.0,  # Bottom-left
            1.0, 0.0,  # Bottom-right
            1.0, 1.0,  # Top-right
            0.0, 1.0,  # Top-left
        ], dtype=np.float32)
        
        indices = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32)
        
        # Only create vertex buffer once
        if not hasattr(self, 'vbo') or self.vbo is None:
            self.vbo = self.ctx.buffer(vertices.tobytes())
            self.ibo = self.ctx.buffer(indices.tobytes())
        
        # Always recreate framebuffer with current dimensions
        if hasattr(self, 'texture') and self.texture:
            self.texture.release()
        if hasattr(self, 'fbo') and self.fbo:
            self.fbo.release()
            
        self.texture = self.ctx.texture((self.widget_width, self.widget_height), 4)
        self.fbo = self.ctx.framebuffer(self.texture)

    

    #note: I have not tested this yet so it might just break
    #I also might never test it because I don't feel like it
    def _initialize_cpu_fallback(self, widget):
        """Initialize CPU fallback rendering."""
        self.widget_width = widget.get_allocated_width()
        self.widget_height = widget.get_allocated_height()
        self.bar_width = self.widget_width / (self.number_of_bars * 2)

        if self.gradient:
            if len(self.gradient_points) != 4:
                print("gradient_points must contain exactly 4 elements. Falling back to default values.")
                self.gradient_points = [0, 0, 1, 1]  # Fallback to default values
            try:
                gp0 = float(self.gradient_points[0])
                gp1 = float(self.gradient_points[1])
                gp2 = float(self.gradient_points[2])
                gp3 = float(self.gradient_points[3])
            except (ValueError, TypeError):
                print("All elements in gradient_points must be numeric values. Falling back to default values.")
                self.gradient_points = [0, 0, 1, 1]  # Fallback to default values
                gp0 = float(self.gradient_points[0])
                gp1 = float(self.gradient_points[1])
                gp2 = float(self.gradient_points[2])
                gp3 = float(self.gradient_points[3])
            self.gradient_pattern = cairo.LinearGradient(
                self.widget_height * gp0,
                self.widget_height * gp1,
                self.widget_height * gp2,
                self.widget_height * gp3
            )
            for i, color in enumerate(self.colors_list):
                stop_position = i / (self.num_colors - 1)  # Normalize between 0 and 1
                self.gradient_pattern.add_color_stop_rgba(stop_position, *color)

    def update_gpu_data(self):
        """Upload bar height data to GPU."""
        if not self.initialized or self.sample is None:
            return
            
        # Prepare instance data for each bar - create mirrored layout
        instance_data = []
        
        # Left side bars (reversed order)
        for i in range(self.number_of_bars):
            if i < self.number_of_bars:
                height = self.sample[i]
                bar_index = float(self.number_of_bars - 1 - i)  # Reverse for left side
                instance_data.extend([height, bar_index])
        
        # Right side bars (normal order)  
        for i in range(self.number_of_bars):
            sample_index = self.number_of_bars + i
            if sample_index < self.number_of_bars * 2:
                height = self.sample[sample_index]
                bar_index = float(self.number_of_bars + i)  # Continue from center
                instance_data.extend([height, bar_index])
        
        instance_array = np.array(instance_data, dtype=np.float32)
        
        # Update or create instance buffer
        if hasattr(self, 'instance_vbo'):
            self.instance_vbo.write(instance_array.tobytes())
        else:
            self.instance_vbo = self.ctx.buffer(instance_array.tobytes())
            
            # Create VAO with instanced rendering
            self.vao = self.ctx.vertex_array(
                self.program,
                [(self.vbo, '2f', 'position'),
                 (self.instance_vbo, '1f 1f/i', 'height', 'bar_index')],
                self.ibo
            )

    def render_to_texture(self):
        """Render bars to GPU texture."""
        if not self.initialized:
            return None
            
        # Bind framebuffer and clear
        self.fbo.use()
        self.ctx.viewport = (0, 0, self.widget_width, self.widget_height)
        self.ctx.clear(*self.background_col)
        
        if self.sample is None:
            return self.texture

        Set_uniforms(self)

        if self.vao:
            if self.fill:
                self.ctx.enable(moderngl.BLEND)
                self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
                # Render filled bars
                self.vao.render(instances=self.number_of_bars * 2)
            else:
                # Render as wireframe (outline only)
                self.ctx.wireframe = True
                self.vao.render(instances=self.number_of_bars * 2)
                self.ctx.wireframe = False
        
        return self.texture

    def initialize(self, widget):
        """Initialize calculations that only need to be done once."""
        if self.use_gpu and not self.gpu_failed:
            # Try GPU initialization first
            initialize_gpu(self, widget, moderngl)
        
        if not self.use_gpu or self.gpu_failed:
            # Fall back to CPU initialization
            self._initialize_cpu_fallback(widget)

    def on_draw(self, widget, cr):
        return on_draw_common(self, widget, cr)

    #untested
    def _fallback_cpu_render(self, widget, cr):
        """Fallback to CPU rendering if GPU fails."""
        # Set the transparent background
        cr.set_source_rgba(*self.background_col)
        cr.paint()

        # Draw the bars visualization using CPU
        if self.sample is not None:
            bar_width = self.widget_width / (self.number_of_bars * 2)
            
            if not self.gradient:
                cr.set_source_rgba(*self.color)
            else:
                # Create gradient pattern for CPU fallback
                if self.gradient_points and len(self.gradient_points) >= 4:
                    gp = [float(x) for x in self.gradient_points[:4]]
                else:
                    gp = [0, 0, 1, 1]
                    
                gradient_pattern = cairo.LinearGradient(
                    self.widget_height * gp[0],
                    self.widget_height * gp[1], 
                    self.widget_height * gp[2],
                    self.widget_height * gp[3]
                )
                
                for i, color in enumerate(self.colors_list):
                    stop_position = i / (len(self.colors_list) - 1)
                    gradient_pattern.add_color_stop_rgba(stop_position, *color)
                
                cr.set_source(gradient_pattern)

            # this is bad and awful and I hate it
            # might rewrite this later but we have cool gpu shaders now so I might not
            for i, value in enumerate(self.sample):
                if i < self.number_of_bars:
                    i = (self.number_of_bars - i)
                    flip = -1
                else:
                    flip = 1
                if i == self.number_of_bars:
                    cr.move_to(i * bar_width, self.widget_height * (1 - self.sample[0]))
                cr.line_to(i * bar_width, self.widget_height * (1 - value))
                cr.line_to((i + flip) * bar_width, self.widget_height * (1 - value))

                if i == 1 or i == self.number_of_bars * 2 - 1:
                    cr.line_to((i + flip) * bar_width, self.widget_height)
                    cr.line_to(widget.get_allocated_width() / 2, self.widget_height)

            if self.fill:
                cr.fill()
            else:
                cr.stroke()

    #this looks like it might cause a memory leak.
    #but I dont know enough about openGL and modernGL to know if it does
    def cleanup(self):
        """Clean up GPU resources."""
        if hasattr(self, 'texture') and self.texture:
            self.texture.release()
            self.texture = None
        if hasattr(self, 'fbo') and self.fbo:
            self.fbo.release()
            self.fbo = None
        if hasattr(self, 'vao') and self.vao:
            self.vao.release()
            self.vao = None
        if hasattr(self, 'vbo') and self.vbo:
            self.vbo.release()
            self.vbo = None
        if hasattr(self, 'ibo') and self.ibo:
            self.ibo.release()
            self.ibo = None
        if hasattr(self, 'instance_vbo') and self.instance_vbo:
            self.instance_vbo.release()
            self.instance_vbo = None
        if self.ctx:
            try:
                self.ctx.release()
                self.ctx = None
            except:
                pass  # Ignore cleanup errors

    def get_performance_info(self):
        #I need to make the debug flag work so this wont spam the console
        """Return information about GPU acceleration status."""
        return {
            "moderngl_available": MODERNGL_AVAILABLE,
            "gpu_initialized": self.initialized and self.use_gpu and not self.gpu_failed,
            "gpu_failed": self.gpu_failed,
            "current_mode": "GPU" if (self.use_gpu and not self.gpu_failed) else "CPU",
            "context_info": str(self.ctx.info) if self.ctx else "No context"
        }
