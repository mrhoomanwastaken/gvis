"""
gvis - Lines visualizer
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

import cairo
import numpy as np
from .shaders import COMMON_FRAGMENT_SHADER, LINES_VERTEX_SHADER, get_shaders_for_config
from .common import Set_uniforms, initialize_gpu, on_draw_common

try:
    import moderngl
    MODERNGL_AVAILABLE = True
except ImportError:
    MODERNGL_AVAILABLE = False
    print("ModernGL not available - falling back to CPU rendering")

class LinesVisualizer:
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
            vertex_shader, fragment_shader = get_shaders_for_config(config, 'lines')
        else:
            # Use default shaders
            vertex_shader = LINES_VERTEX_SHADER
            fragment_shader = COMMON_FRAGMENT_SHADER
        
        self.program = self.ctx.program(
            vertex_shader=vertex_shader,
            fragment_shader=fragment_shader
        )

    def _setup_buffers(self):
        """Set up GPU buffers."""
        if self.fill:
            # For filled mode, create vertices for a triangle strip that forms a filled waveform
            # We need alternating vertices: bottom points (y=0) and waveform points
            vertices = []
            
            # Create pairs of vertices: baseline and waveform point
            for i in range(self.number_of_bars * 2):
                x_pos = i / (self.number_of_bars * 2 - 1)  # Normalize 0 to 1
                vertices.append(x_pos)  # Waveform point
                vertices.append(x_pos)  # Baseline point (same x, different y in height data)
                
            self.vertices_per_point = 2  # Two vertices per audio sample point
        else:
            # For line mode, just create the line points
            vertices = []
            for i in range(self.number_of_bars * 2):
                x_pos = i / (self.number_of_bars * 2 - 1)  # Normalize 0 to 1
                vertices.append(x_pos)
                
            self.vertices_per_point = 1  # One vertex per audio sample point
        
        vertices_array = np.array(vertices, dtype=np.float32)
        
        # Only create vertex buffer once
        if not hasattr(self, 'vbo') or self.vbo is None:
            self.vbo = self.ctx.buffer(vertices_array.tobytes())
        else:
            # Update existing buffer if dimensions changed
            self.vbo.write(vertices_array.tobytes())
        
        # Always recreate framebuffer with current dimensions
        if hasattr(self, 'texture') and self.texture:
            self.texture.release()
        if hasattr(self, 'fbo') and self.fbo:
            self.fbo.release()
            
        self.texture = self.ctx.texture((self.widget_width, self.widget_height), 4)
        self.fbo = self.ctx.framebuffer(self.texture)

    

    #note: I have not tested this yet so it might just break
    #I also might never test it becuase I dont feel like it
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
        """Upload line point data to GPU."""
        if not self.initialized or self.sample is None:
            return
        
        # Check if fill setting changed and rebuild buffers if needed
        if hasattr(self, '_last_fill_setting') and self._last_fill_setting != self.fill:
            self._last_fill_setting = self.fill
            self._setup_buffers()  # Rebuild buffers with new layout
            
        # Prepare height data based on rendering mode
        heights = []
        
        if self.fill:
            # For filled mode, create alternating heights: waveform and baseline
            # Left side (reversed order)
            for i in range(self.number_of_bars):
                if i < len(self.sample):
                    height = self.sample[self.number_of_bars - 1 - i]  # Waveform point
                    heights.append(height)
                    heights.append(0.0)  # Baseline point
            
            # Right side (normal order)  
            for i in range(self.number_of_bars):
                sample_index = i
                if sample_index < len(self.sample):
                    height = self.sample[sample_index]  # Waveform point
                    heights.append(height)
                    heights.append(0.0)  # Baseline point
        else:
            # For line mode, just the waveform points
            # Left side (reversed order)
            for i in range(self.number_of_bars):
                if i < len(self.sample):
                    height = self.sample[self.number_of_bars - 1 - i]
                    heights.append(height)
            
            # Right side (normal order)  
            for i in range(self.number_of_bars):
                sample_index = i
                if sample_index < len(self.sample):
                    height = self.sample[sample_index]
                    heights.append(height)
        
        heights_array = np.array(heights, dtype=np.float32)
        
        # Update or create height buffer
        if hasattr(self, 'height_vbo'):
            # Check if buffer size needs to change
            if len(heights_array) * 4 != self.height_vbo.size:  # 4 bytes per float32
                self.height_vbo.release()
                self.height_vbo = self.ctx.buffer(heights_array.tobytes())
                self._rebuild_vao()
            else:
                self.height_vbo.write(heights_array.tobytes())
        else:
            self.height_vbo = self.ctx.buffer(heights_array.tobytes())
            self._rebuild_vao()
    
    def _rebuild_vao(self):
        """Rebuild VAO when buffer structure changes."""
        if hasattr(self, 'vao') and self.vao:
            self.vao.release()
        
        # Create VAO
        self.vao = self.ctx.vertex_array(
            self.program,
            [(self.vbo, '1f', 'x_position'),
             (self.height_vbo, '1f', 'height')]
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
        
        Set_uniforms(self)  # Set uniforms for shader
         
        if self.vao:
            if self.fill:
                self.ctx.enable(moderngl.BLEND)
                self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
                # Render as triangle strip for proper filled waveform
                self.vao.render(mode=moderngl.TRIANGLE_STRIP)
            else:
                # Set line width for better visibility
                self.ctx.line_width = 2.0
                # Render as line strip
                self.vao.render(mode=moderngl.LINE_STRIP)
        
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

    def _fallback_cpu_render(self, widget, cr):
        """Fallback to CPU rendering if GPU fails."""
        # Set the transparent background
        cr.set_source_rgba(*self.background_col)
        cr.paint()

        # Draw the line visualization using CPU
        if self.sample is not None:
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

            # Set line width
            cr.set_line_width(2.0)
            
            # Draw continuous line
            points_per_side = len(self.sample) // 2
            
            # Start from the left side (reversed)
            first_point = True
            for i in range(points_per_side):
                sample_idx = points_per_side - 1 - i  # Reverse for left side
                if sample_idx < len(self.sample):
                    x = (i / (points_per_side * 2 - 1)) * self.widget_width
                    y = self.widget_height * self.sample[sample_idx]  # Remove the (1 - ...)
                    
                    if first_point:
                        cr.move_to(x, y)
                        first_point = False
                    else:
                        cr.line_to(x, y)
            
            # Continue to the right side (normal order)
            for i in range(points_per_side):
                sample_idx = i
                if sample_idx < len(self.sample):
                    x = ((points_per_side + i) / (points_per_side * 2 - 1)) * self.widget_width
                    y = self.widget_height * self.sample[sample_idx]  # Remove the (1 - ...)
                    cr.line_to(x, y)

            if self.fill:
                # Close the path for filling
                cr.line_to(self.widget_width, 0)  # Go to bottom right
                cr.line_to(0, 0)  # Go to bottom left
                cr.close_path()
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
        if hasattr(self, 'height_vbo') and self.height_vbo:
            self.height_vbo.release()
            self.height_vbo = None
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
