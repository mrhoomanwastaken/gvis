import cairo

#this still uses the cpu
#will change when I feel like it
class LinesVisualizer:
    def __init__(self, background_col, number_of_bars, fill, gradient, colors_list=None, num_colors=None, gradient_points=None, color=None):
        self.background_col = background_col
        self.number_of_bars = number_of_bars
        self.fill = fill
        self.gradient = gradient
        self.colors_list = colors_list
        self.num_colors = num_colors
        self.gradient_points = gradient_points
        self.color = color
        self.sample = None
        self.bar_width = None
        self.gradient_pattern = None
        self.widget_width = None
        self.widget_height = None

    def initialize(self, widget):
        """Initialize calculations that only need to be done once."""
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

    def on_draw(self, widget, cr):
        # Set the transparent background
        cr.set_source_rgba(*self.background_col)
        cr.paint()

        # Reinitialize if widget dimensions have changed
        if (self.widget_width != widget.get_allocated_width() or 
            self.widget_height != widget.get_allocated_height()):
            self.initialize(widget)

        # Draw the lines visualization
        if self.sample is not None:
            if not self.gradient:
                cr.set_source_rgba(*self.color)
            else:
                cr.set_source(self.gradient_pattern)

            cr.set_line_width(2)
            for i, value in enumerate(self.sample):
                if i < self.number_of_bars:
                    i = (self.number_of_bars - i)
                    flip = -1
                else:
                    flip = 1
                if i == self.number_of_bars:
                    cr.move_to(i * self.bar_width, self.widget_height * (1 - self.sample[0]))
                cr.line_to((i + flip) * self.bar_width, self.widget_height * (1 - value))
                if i == 1 or i == self.number_of_bars * 2 - 1:
                    cr.line_to((i + flip) * self.bar_width, self.widget_height)
                    cr.line_to(self.widget_width / 2, self.widget_height)

            if self.fill:
                cr.fill()
            else:
                cr.stroke()