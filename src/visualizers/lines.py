import cairo
import numpy as np
from .shaders import COMMON_FRAGMENT_SHADER, LINES_VERTEX_SHADER

try:
    import moderngl
    MODERNGL_AVAILABLE = True
except ImportError:
    MODERNGL_AVAILABLE = False
    print("ModernGL not available - falling back to CPU rendering")

class LinesVisualizer:
    def __init__(self, background_col, number_of_bars, fill, gradient, colors_list=None, num_colors=None,gradient_points=None, color=None):
        self.background_col = background_col
        self.number_of_bars = number_of_bars
        self.fill = fill
        self.gradient = gradient
        self.colors_list = colors_list
        self.num_colors = num_colors
        self.color = color
        self.gradient_points = gradient_points
        self.sample = None
        self.bar_width = None
        self.gradient_pattern = None
        self.widget_width = None
        self.widget_height = None
        
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

    def initialize_gpu(self, widget):
        """Initialize GPU resources for rendering."""
        if self.initialized or self.gpu_failed or not self.use_gpu:
            return
            
        try:
            self.widget_width = widget.get_allocated_width()
            self.widget_height = widget.get_allocated_height()
            
            # Try to create ModernGL context with different backends
            self.ctx = None
            
            # Try different context creation methods
            try:
                # Method 1: Try to create standalone context
                self.ctx = moderngl.create_context(standalone=True)
                print("Created standalone ModernGL context")
            except Exception as e:
                print(f"Standalone context failed: {e}")
                try:
                    # Method 2: Try to create context from existing OpenGL context
                    self.ctx = moderngl.create_context()
                    print("Created ModernGL context from existing OpenGL")
                except Exception as e2:
                    print(f"Regular context creation failed: {e2}")
                    # Method 3: Try with require=False for compatibility
                    try:
                        self.ctx = moderngl.create_context(require=330)
                        print("Created ModernGL context with OpenGL 3.3 requirement")
                    except Exception as e3:
                        print(f"OpenGL 3.3 context failed: {e3}")
                        raise RuntimeError("All ModernGL context creation methods failed")
            
            if self.ctx is None:
                raise RuntimeError("Failed to create ModernGL context")
                
            print(f"ModernGL context info: {self.ctx.info}")
            
            # Continue with shader setup...
            self._setup_shaders()
            self._setup_buffers()
            
            self.initialized = True
            print("GPU initialization successful")
            
        except Exception as e:
            print(f"GPU initialization failed: {e}")
            self.gpu_failed = True
            self.use_gpu = False
            # Fall back to CPU rendering
            self._initialize_cpu_fallback(widget)

    def _setup_shaders(self):
        """Set up GPU shaders."""
        # Create shader program using shared shaders
        self.program = self.ctx.program(
            vertex_shader=LINES_VERTEX_SHADER,
            fragment_shader=COMMON_FRAGMENT_SHADER
        )

    def _setup_buffers(self):
        """Set up GPU buffers."""
        # Create vertex data for line points - just x positions, heights will come from instance data
        vertices = []
        for i in range(self.number_of_bars * 2):
            x_pos = i / (self.number_of_bars * 2 - 1)  # Normalize 0 to 1
            vertices.append(x_pos)
        
        vertices_array = np.array(vertices, dtype=np.float32)
        self.vbo = self.ctx.buffer(vertices_array.tobytes())
        
        # Create framebuffer for rendering to texture
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
            
        # Prepare height data for each point - create mirrored layout
        heights = []
        
        # Left side (reversed order)
        for i in range(self.number_of_bars):
            if i < len(self.sample):
                height = self.sample[self.number_of_bars - 1 - i]  # Reverse for left side
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
            self.height_vbo.write(heights_array.tobytes())
        else:
            self.height_vbo = self.ctx.buffer(heights_array.tobytes())
            
            # Create VAO with line strip rendering
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
        
        # Set uniforms
        self.program['widget_width'] = float(self.widget_width)
        self.program['widget_height'] = float(self.widget_height)
        
        if self.gradient and self.colors_list:
            self.program['use_gradient'] = True
            self.program['num_gradient_colors'] = min(len(self.colors_list), 8)
            
            # Set gradient points
            if self.gradient_points and len(self.gradient_points) >= 4:
                gp = [float(x) for x in self.gradient_points[:4]]
                self.program['gradient_points'] = tuple(gp)
            else:
                self.program['gradient_points'] = (0.0, 0.0, 1.0, 1.0)
            
            # Set individual gradient color uniforms
            for i in range(8):
                if i < len(self.colors_list):
                    self.program[f'gradient_color{i}'] = self.colors_list[i]
                else:
                    # Pad with the last color
                    last_color = self.colors_list[-1] if self.colors_list else (0.0, 0.0, 0.0, 1.0)
                    self.program[f'gradient_color{i}'] = last_color
        else:
            self.program['use_gradient'] = False
            self.program['solid_color'] = self.color if self.color else (0.0, 1.0, 1.0, 1.0)
        
        # Update GPU data and render
        self.update_gpu_data()
        
        if self.vao:
            if self.fill:
                self.ctx.enable(moderngl.BLEND)
                self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
            
            # Set line width for better visibility
            self.ctx.line_width = 2.0
            
            # Render as line strip
            self.vao.render(mode=moderngl.LINE_STRIP)
        
        return self.texture

    def initialize(self, widget):
        """Initialize calculations that only need to be done once."""
        if self.use_gpu and not self.gpu_failed:
            # Try GPU initialization first
            self.initialize_gpu(widget)
        
        if not self.use_gpu or self.gpu_failed:
            # Fall back to CPU initialization
            self._initialize_cpu_fallback(widget)

    def on_draw(self, widget, cr):
        # Check if we need to reinitialize
        if (not self.initialized or 
            self.widget_width != widget.get_allocated_width() or 
            self.widget_height != widget.get_allocated_height()):
            self.initialize(widget)
        
        # Try GPU rendering first if available
        if self.use_gpu and not self.gpu_failed and self.initialized:
            try:
                gpu_texture = self.render_to_texture()
                
                if gpu_texture is not None:
                    # Read GPU texture data
                    texture_data = gpu_texture.read()
                    
                    # Create Cairo surface from GPU texture
                    cairo_surface = cairo.ImageSurface.create_for_data(
                        bytearray(texture_data), 
                        cairo.FORMAT_ARGB32,
                        self.widget_width, 
                        self.widget_height
                    )
                    
                    # Draw the GPU-rendered texture to Cairo context
                    cr.set_source_surface(cairo_surface, 0, 0)
                    cr.paint()
                    return
            except Exception as e:
                print(f"GPU rendering failed, falling back to CPU: {e}")
                self.gpu_failed = True
                self.use_gpu = False
        
        # Fallback to CPU rendering
        self._fallback_cpu_render(widget, cr)

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
        if self.ctx:
            try:
                self.ctx.release()
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
