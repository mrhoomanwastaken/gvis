import os
import threading
import gi
import configparser
import sys
gi.require_version("Gtk", "3.0")
gi.require_version('Gst', '1.0')
gi.require_version('Gio', '2.0')
from gi.repository import Gtk, Gdk , GLib


import src.cava.cava_init as cava_init
from src.config.config_loader import load_config
from src.cava.cava_init import initialize_plan
from src.ui_controls import on_pause_button_clicked, on_back_button_clicked, on_skip_button_clicked
from src.visualizers.bars import BarsVisualizer
from src.visualizers.lines import LinesVisualizer
from src.mpris_service import get_mpris_service
from src.update_info import update_info, update_progress
from src.run_cava import run_cava


if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

# Initialize cavacore
cava_init.initialize_cava(base_path)
cava_lib = cava_init.cava_lib

config = configparser.ConfigParser()



# Load configuration
gvis_config = load_config()

# Extract configuration values
number_of_bars = gvis_config['number_of_bars']
rate = gvis_config['rate']
channels = gvis_config['channels']
autosens = gvis_config['autosens']
noise_reduction = gvis_config['noise_reduction']
low_cut_off = gvis_config['low_cut_off']
high_cut_off = gvis_config['high_cut_off']
buffer_size = gvis_config['buffer_size']
input_source = gvis_config['input_source']
vis_type = gvis_config['vis_type']
fill = gvis_config['fill']
gradient = gvis_config['gradient']
scrobble_enabled = gvis_config['scrobble']

# Remove background color and gradient parsing logic
background_col = gvis_config['background_col']
if gvis_config['gradient']:
    colors_list = gvis_config['color_gradent']
    num_colors = len(colors_list)
else:
    color = gvis_config['color1']

# Initialize CAVA plan
try:
    plan = initialize_plan(cava_lib, number_of_bars, rate, channels, autosens, noise_reduction, low_cut_off, high_cut_off)
except RuntimeError as e:
    print(e)
    exit(1)




if scrobble_enabled:
    try:
        from src.scrobbler import initialize_lastfm
        network = initialize_lastfm()
        print("Last.fm scrobbling is enabled.")
    except ImportError:
        print("Last.fm scrobbling is enabled but the required library is not installed.")
        network = None
        scrobble_enabled = False
else:
    network = None
    scrobble_enabled = False

class MyWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="gvis")
        self.get_screen_size(self.get_display())
        self.set_default_size(self.width, self.height // 2)

        # Enable support for transparency
        self.set_visual(self.get_screen().get_rgba_visual())
        self.set_app_paintable(True)

        # Connect to draw signal to manually draw the window's background
        self.connect("draw", self.on_draw)
       
        # Create and load CSS to make only specific elements transparent
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            .transparent-button {
                border: none;
                box-shadow: none;
                opacity: 1;
            }
            .white-label {
            color: white;
            }
        """)

        # Apply the CSS to the screen with high priority
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_USER  # High priority to override theme defaults
        )
        
        self.overlay = Gtk.Overlay()
        self.add(self.overlay)


        # Create a DrawingArea and pack it into the main box
        self.drawing_area = Gtk.DrawingArea()
        self.overlay.add(self.drawing_area)


        self.song_box = Gtk.Box(spacing=0)
        self.song_box.set_valign(1)
        self.song_box.set_margin_top(20) 
        
        #lets us find where the buttion images are if it is compiled with pyinstaller. 
        if hasattr(sys, '_MEIPASS'):
            self.back_image = Gtk.Image.new_from_file(os.path.join(sys._MEIPASS, 'src/images/back.png'))
        else:
            self.back_image = Gtk.Image.new_from_file(os.path.join(base_path , 'src/images/back.png'))
        self.back_button = Gtk.Button(image = self.back_image)
        self.back_button.get_style_context().add_class("transparent-button")
        self.back_button.set_relief(Gtk.ReliefStyle.NONE)
        self.song_box.pack_start(self.back_button, True, True, 0)



        # Add the album art holder to the window
        self.info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.info_box.set_valign(1)
        self.song_box.pack_start(self.info_box, True, True, 0)
        

        if hasattr(sys, '_MEIPASS'):
            self.skip_image = Gtk.Image.new_from_file(os.path.join(sys._MEIPASS, 'src/images/skip.png'))
        else:
            self.skip_image = Gtk.Image.new_from_file(os.path.join(base_path , 'src/images/skip.png'))
        self.skip_button = Gtk.Button(image = self.skip_image)
        self.skip_button.get_style_context().add_class("transparent-button")
        self.skip_button.set_relief(Gtk.ReliefStyle.NONE)
        self.song_box.pack_start(self.skip_button, True, True, 0)


        # Add the album art holder to the box
        self.album_art = Gtk.Image()
        self.album_art_holder = Gtk.Overlay()
        self.album_art_holder.add(self.album_art)
        self.info_box.pack_start(self.album_art_holder, True, True, 0)  # Add the image to the box

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_fraction(1)
        self.album_art_holder.add_overlay(self.progress_bar)

        self.pause_buttion = Gtk.Button()
        self.pause_buttion.get_style_context().add_class("transparent-button")
        self.pause_buttion.set_relief(Gtk.ReliefStyle.NONE)
        self.album_art_holder.add_overlay(self.pause_buttion)

        self.song_name = Gtk.Label()
        self.song_name.get_style_context().add_class("white-label")
        self.info_box.pack_start(self.song_name ,True, True, 0)  # Add the song name label to the box

        self.album_name = Gtk.Label()
        self.album_name.get_style_context().add_class("white-label")
        self.info_box.pack_start(self.album_name ,True, True, 0)  # Add the song album label to the box

        self.artist_name = Gtk.Label()
        self.artist_name.get_style_context().add_class("white-label")
        self.info_box.pack_start(self.artist_name ,True, True, 0)  # Add the song artist label to the box

        self.back_button.connect("clicked", lambda button: on_back_button_clicked(self.source, button, self.progress_bar))
        self.skip_button.connect("clicked", lambda button: on_skip_button_clicked(self.source, button))
        self.pause_buttion.connect("clicked", lambda button: on_pause_button_clicked(self.source, button))

        self.overlay.add_overlay(self.song_box)
        
        # Connect to MPRIS service and update the album art
        self.source = get_mpris_service()
        # Start CAVA processing in a separate thread so it can begin processing audio
        threading.Thread(target=self.run_cava, daemon=True).start()

        # Initialize the appropriate visualizer based on the configuration
        if vis_type == 'bars':
            self.visualizer = BarsVisualizer(
                background_col=background_col,
                number_of_bars=number_of_bars,
                fill=fill,
                gradient=gradient,
                colors_list=colors_list if gradient else None,
                num_colors=num_colors if gradient else None,
                color=color if not gradient else None
            )
        elif vis_type == 'lines':
            self.visualizer = LinesVisualizer(
                background_col=background_col,
                number_of_bars=number_of_bars,
                fill=fill,
                gradient=gradient,
                colors_list=colors_list if gradient else None,
                num_colors=num_colors if gradient else None,
                color=color if not gradient else None
            )
        else:
            raise ValueError(f"Unsupported visualization type: {vis_type}")

        self.drawing_area.connect("draw", self.visualizer.on_draw)
        if self.source:
            self.source.connect("g-properties-changed", self.on_properties_changed)
            self.new_song = True
            self.update_info()
            GLib.timeout_add(100, self.update_progress)
    
    def get_screen_size(self , display):
        #from user3840170 on stackoverflow
        mon_geoms = [
            display.get_monitor(i).get_geometry()
            for i in range(display.get_n_monitors())
        ]

        x0 = min(r.x            for r in mon_geoms)
        y0 = min(r.y            for r in mon_geoms)
        x1 = max(r.x + r.width  for r in mon_geoms)
        y1 = max(r.y + r.height for r in mon_geoms)

        self.height = y1 - y0
        self.width = x1 - x0

    def on_draw(self, widget, cr):
        # Set the transparent background
        cr.set_source_rgba(*background_col)
        cr.paint()

    def on_properties_changed(self, interface_name, changed_properties, invalidated_properties):
        print(changed_properties)
        self.update_info()

    def update_info(self):
        global scrobble_enabled, network
        update_info(self , scrobble_enabled, network)

    def update_progress(self):
        return update_progress(self)

    
    def run_cava(self):
        run_cava(
            input_source=input_source,
            buffer_size=buffer_size,
            channels=channels,
            number_of_bars=number_of_bars,
            cava_lib=cava_lib,
            plan=plan,
            update_visualization=self.update_visualization,
            source=self.source
        )


    def update_visualization(self, sample):
        # Update the visualization data and redraw
        self.visualizer.sample = sample
        GLib.idle_add(self.drawing_area.queue_draw)  # Request to redraw the area



win = MyWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
