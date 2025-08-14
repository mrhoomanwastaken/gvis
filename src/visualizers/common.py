"""
Simple common functions for visualizers.
"""
import time
import numpy as np

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
            - gradient_points (list of floats): List of 4 floats defining gradient points.
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