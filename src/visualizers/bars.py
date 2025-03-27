import cairo

class BarsVisualizer:
    def __init__(self, background_col, number_of_bars, fill, gradient, colors_list=None, num_colors=None, color=None):
        self.background_col = background_col
        self.number_of_bars = number_of_bars
        self.fill = fill
        self.gradient = gradient
        self.colors_list = colors_list
        self.num_colors = num_colors
        self.color = color
        self.sample = None

    def on_draw(self, widget, cr):
        # Set the transparent background
        cr.set_source_rgba(*self.background_col)
        cr.paint()

        # Draw the bars visualization
        if self.sample is not None:
            screen_height = widget.get_allocated_height()
            bar_width = widget.get_allocated_width() / (self.number_of_bars * 2)

            if not self.gradient:
                cr.set_source_rgba(*self.color)
            else:
                # Gradient calculations
                pattern = cairo.LinearGradient(0, 0, widget.get_allocated_width(), screen_height)
                for i, color in enumerate(self.colors_list):
                    stop_position = i / (self.num_colors - 1)  # Normalize between 0 and 1
                    pattern.add_color_stop_rgba(stop_position, *color)
                cr.set_source(pattern)

            for i, value in enumerate(self.sample):
                if i < self.number_of_bars:
                    i = (self.number_of_bars - i)
                    flip = -1
                else:
                    flip = 1
                if i == self.number_of_bars:
                    cr.move_to(i * bar_width, screen_height * (1 - self.sample[0]))
                height = value * screen_height
                cr.line_to(i * bar_width, screen_height * (1 - value))
                cr.line_to((i + flip) * bar_width, screen_height * (1 - value))

                if i == 1 or i == self.number_of_bars * 2 - 1:
                    cr.line_to((i + flip) * bar_width, screen_height)
                    cr.line_to(widget.get_allocated_width() / 2, screen_height)

            if self.fill:
                cr.fill()
            else:
                cr.stroke()