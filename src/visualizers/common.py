"""
Simple common functions for visualizers.
"""
import time
import numpy as np
import cairo

def Set_uniforms(self):
    """
    Set shader uniforms for the visualizer.
    Inputs:
        self: The visualizer instance with attributes:
            - widget_width (float): Width of the widget.
            - widget_height (float): Height of the widget.
            - number_of_bars (int): Number of bars in the visualizer.
            - gradient (bool): Whether to use gradient colors.
            - colors_list (list of tuples): List of RGBA color tuples for the gradient.
            - gradient_points (list of 4 floats): List of 4 floats defining gradient points.
            - color (tuple): Solid color as an RGBA tuple.
            - program: The shader program object with a dictionary-like interface for uniforms.
    Outputs:
        None. Sets uniforms in the shader program and updates GPU data.
    Currently sets the following uniforms:
        - widget_width (float)
        - widget_height (float)
        - number_of_bars (int) (the amount of bars (points) in the visualizer)
        - use_gradient (bool)
        - num_gradient_colors (int)
        - gradient_points (tuple of 4 floats)
        - gradient_color0 to gradient_color7 (tuple of 4 floats)
        - solid_color (tuple of 4 floats)
    """

    # most of this stuff is from shader toy so that they can be ported easily

    # Set widget dimensions
    try:
        self.program['widget_width'] = float(self.widget_width)
        self.program['widget_height'] = float(self.widget_height)
    except KeyError:
        pass  # Custom shader might not use these uniforms
    
    # Set number of bars
    try:
        self.program['number_of_bars'] = self.number_of_bars
    except KeyError:
        pass  # Custom shader might not use this uniform
    

    # Set gradient uniforms
    try:
        if self.gradient and self.colors_list: 
            self.program['use_gradient'] = True
            self.program['num_gradient_colors'] = min(len(self.colors_list), 8)
            
            # Set gradient points
            try:
                if self.gradient_points and len(self.gradient_points) >= 4:
                    gp = [float(x) for x in self.gradient_points[:4]]
                    self.program['gradient_points'] = tuple(gp)
                else:
                    self.program['gradient_points'] = (0.0, 0.0, 1.0, 1.0)
            except KeyError:
                pass  # gradient_points uniform not found (probably optimized out)
            
            # Set individual gradient color uniforms
            for i in range(8):
                try:
                    if i < len(self.colors_list):
                        self.program[f'gradient_color{i}'] = self.colors_list[i]
                    else:
                        # Pad with the last color
                        last_color = self.colors_list[-1] if self.colors_list else (0.0, 0.0, 0.0, 1.0)
                        self.program[f'gradient_color{i}'] = last_color
                except KeyError:
                    pass  # gradient_color uniform not found
        else:
            self.program['use_gradient'] = False
            self.program['solid_color'] = self.color if self.color else (0.0, 1.0, 1.0, 1.0)
    except KeyError:
        # Custom shader doesn't use gradient uniforms, that's fine
        try:
            self.program['solid_color'] = self.color if self.color else (0.0, 1.0, 1.0, 1.0)
        except KeyError:
            pass  # Custom shader doesn't use solid_color either

    # average the height of the bars
    try:
        self.program['avg_height'] = np.mean(self.sample)
    except KeyError:
        pass

    #Set common uniforms (commonly used in shadertoy shaders)
    try:
        self.program['iTime'] = time.time() - self.start_time
    except KeyError:
        pass  # Custom shader might not use this uniform
    try:
        self.program['iResolution'] = (self.widget_width, self.widget_height)
    except KeyError:
        pass # Custom shader might not use this uniform


    # Update GPU data and render
    self.update_gpu_data()

def initialize_gpu(self, widget , moderngl):
    """Initialize GPU resources for rendering."""
    if self.gpu_failed or not self.use_gpu:
        return
        
    try:
        new_width = widget.get_allocated_width()
        new_height = widget.get_allocated_height()
        
        # Store the current fill setting to detect changes
        self._last_fill_setting = self.fill
        
        # Check if we need to create context or just update size
        if not self.ctx:
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
                
            
            # Setup shaders (only need to do this once)
            self._setup_shaders(self.config)
        
        # Update dimensions
        self.widget_width = new_width
        self.widget_height = new_height
        
        # Setup or update buffers with new dimensions
        self._setup_buffers()
        
        self.initialized = True
        print("GPU initialization successful")
        
    except Exception as e:
        print(f"GPU initialization failed: {e}")
        self.gpu_failed = True
        self.use_gpu = False
        # Fall back to CPU rendering
        self._initialize_cpu_fallback(widget)

def on_draw_common(self, widget, cr):
    """
    Common on_draw function for visualizers.
    This function handles the rendering pipeline for both GPU and CPU rendering.
    """
    current_width = widget.get_allocated_width()
    current_height = widget.get_allocated_height()
    
    # Check if we need to reinitialize due to size change
    if (not self.initialized or 
        self.widget_width != current_width or 
        self.widget_height != current_height):
        
        # Reset initialized flag so GPU resources are properly updated
        if (self.widget_width != current_width or 
            self.widget_height != current_height):
            self.initialized = False
            
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
