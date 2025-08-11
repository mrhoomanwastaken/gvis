import cairo
import numpy as np

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
        # Vertex shader for bar rendering
        vertex_shader = """
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
        """
        
        # Fragment shader with gradient support
        fragment_shader = """
        #version 330 core
        
        in float v_height;
        in float v_bar_index;
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
        """
        
        # Create shader program
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
        
        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.ibo = self.ctx.buffer(indices.tobytes())
        
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
        """Upload bar height data to GPU."""
        if not self.initialized or self.sample is None:
            return
            
        # Prepare instance data for each bar - create mirrored layout
        instance_data = []
        
        # Left side bars (reversed order)
        for i in range(self.number_of_bars):
            if i < len(self.sample):
                height = self.sample[i]
                bar_index = float(self.number_of_bars - 1 - i)  # Reverse for left side
                instance_data.extend([height, bar_index])
        
        # Right side bars (normal order)  
        for i in range(self.number_of_bars):
            sample_index = self.number_of_bars + i
            if sample_index < len(self.sample):
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
        
        # Set uniforms
        self.program['widget_width'] = float(self.widget_width)
        self.program['widget_height'] = float(self.widget_height) 
        self.program['number_of_bars'] = self.number_of_bars
        
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
            
            # Render all bars in one draw call using instancing
            self.vao.render(instances=self.number_of_bars * 2)
        
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
