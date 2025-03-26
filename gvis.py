import os
import select
import subprocess
import threading
import gi
import configparser
import urllib.request
import cairo
import selectors
import ctypes
import sys
import numpy as np
gi.require_version("Gtk", "3.0")
gi.require_version('Gst', '1.0')
gi.require_version('Gio', '2.0')
from gi.repository import Gtk, GdkPixbuf , Gdk , GLib , Gio


import src.cava.cava_init as cava_init
from src.config.config_loader import load_config
from src.cava.cava_init import initialize_plan
from src.ui_controls import on_pause_button_clicked, on_back_button_clicked, on_skip_button_clicked
from src.visualizers.bars import BarsVisualizer
from src.visualizers.lines import LinesVisualizer
from src.mpris_service import get_mpris_service


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
        if not self.source:
            return

        #I love how this pile of garbage replaced pydbus. this looks so much better and I am so glad I have to use it.
        metadata_variant = self.source.call_sync(
                "org.freedesktop.DBus.Properties.Get",
                GLib.Variant("(ss)", ("org.mpris.MediaPlayer2.Player", "Metadata")),
                Gio.DBusCallFlags.NONE,
                -1,  # No timeout
                None
        )
        metadata = metadata_variant.unpack()[0]


        song_name = metadata.get('xesam:title')
        self.song_name.set_label(song_name)

        try:
            if self.old_song != song_name:
                self.new_song = True
                self.old_song = song_name
            else:
                self.old_song = song_name
                self.new_song = False
        except Exception as e:
            print(e)
            self.old_song = song_name
            self.new_song = True

        try:
            album_name = metadata.get('xesam:album')
            self.album_name.set_label(album_name)
        except TypeError:
            pass
        try:
            artist_name = metadata.get('xesam:artist')
            self.artist_name.set_label(artist_name[0])
        except TypeError:
            pass
        
        try:
            #get the current spot in the song. I have yet to see any app that supports this.
            position_variant = self.source.get_cached_property("Position")
            current_position = position_variant.unpack()
        except:
            pass

        #this block of code is evil and has eaten many hours of my life.
        #note: this is broken and also bad
        try:
            if current_position / metadata.get('mpris:length') > 1:
                self.progress_bar.set_fraction(current_position / metadata.get('mpris:length'))
            elif self.new_song:
                #if you see this error being spammed in the terminal be ready for it to consume the rest of your day trying to make it stop.
                print('cant find accurate position in song assuming song just started')
                self.progress_bar.set_fraction(0)
        except UnboundLocalError:
            if self.new_song:
                print('cant find accurate position in song assuming song just started')
                self.progress_bar.set_fraction(0)
        except gi.repository.GLib.GError as e:
            print(e)
            if self.new_song:
                print('cant find accurate position in song assuming song just started')
                self.progress_bar.set_fraction(0)
        self.just_updated = True


        #I know this var does not follow PEP 8 but counterpoint, I dont care. also rate is used by cava.
        #Im derectly calling out sourcey for always telling me that.
        try:
            Rate = self.source.get_cached_property("rate").unpack
        except:
            Rate = 1.0

        
        try:
            #oh boy floats. im sure they will not cause any issues
            #why does mpris use pico seconds? its for things like music, even milliseconds are a bit much.
            self.progress_rate = ((100000 / metadata.get('mpris:length')) * Rate)
        except TypeError:
            print('cant find song length. progress bar will not work')
            self.progress_rate = 0
        
        album_image_url = metadata.get("mpris:artUrl")
        #this will fail the first few times becuase it takes a second for the app to give a image url. 
        #oh well.
        if album_image_url:
            # Download the image
            try:
                response = urllib.request.urlopen(album_image_url)
                image_data = response.read()

                # Load image data into GdkPixbuf
                #GdkPixbuf is depracated in gtk 4 and will be a pain translate over.
                loader = GdkPixbuf.PixbufLoader.new()
                loader.write(image_data)
                loader.close()
                pixbuf = loader.get_pixbuf()

                scaled_pixbuf = pixbuf.scale_simple(300, 300, GdkPixbuf.InterpType.BILINEAR)  

                # Set the Gtk.Image to display the downloaded album art
                self.album_art.set_from_pixbuf(scaled_pixbuf)

            except Exception as e:
                print(f"Failed to load album image: {e}")
        else:
            print("No album image available.")
        
        self.new_song = False
    def update_progress(self):
        #Warning: everything related to the progress bar is cursed and always breaks.
        #this code is the most stable part of handling the progress bar.
        #thats not saying much though
        if self.just_updated:
            self.just_updated = False
        #if its paused you should not update the progress bar.
        elif self.source.get_cached_property("PlaybackStatus").unpack() == 'Playing':
            #this will sometimes end up setting the fraction to a crazy high amount making it always full
            #it will only happen from the second song onwards
            #prob an issue with the progress bar not reseting or self.progress_rate being borked. 
            self.progress_bar.set_fraction(self.progress_bar.get_fraction() + self.progress_rate)
        return True

    
    def run_cava(self):
        global input_source
        if input_source == "Auto":
            print("input_source set to Auto. attempting to detect source.")
            #get the music app that mpris is connected to.
            identity_variant = self.source.call_sync(
                "org.freedesktop.DBus.Properties.Get",
                GLib.Variant("(ss)", ("org.mpris.MediaPlayer2", "Identity")),
                Gio.DBusCallFlags.NONE,
                -1,  # No timeout
                None  # No cancellable
            )
            app = identity_variant.unpack()[0]

            #use the app name to get the pipewire node.name of the music app
            #it only supports firefox and vlc right now becuase there is no pattern or standerd for naming pipewire nodes so they have to be added manually (fun!)
            print(f"detected app: {app}")
            if app == "Mozilla firefox" or "Firefox":
                input_source = "Firefox"
            elif app == "VLC media player":
                input_source = 'VLC media player (LibVLC 3.0.21)'
            else:
                print(f"unsupported app {app} falling back to 'auto'")
                input_source = "auto"
            print(f"setting audio target to {input_source}")

        
        #open pw-cat so we can stream audio data from the app.
        #or if it input_source is auto it will just stream audio from the microphone.
        process = subprocess.Popen(
            ["pw-cat", "-ra", "--target", str(input_source), "--format" , "f32" , "-"],
            stdout=subprocess.PIPE,
            bufsize=buffer_size * channels,
        )

        #I dont know what selector is or how it got here but I am not going to touch it.
        selector = selectors.DefaultSelector()

        #start processing the audio data
        while True:
            #this will hold the thred forever if there is no audio coming through.
            #this does 2 things 1. if the pw-cat crashed and died it will take the app with it
            #2. it makes the visualization pause whenever the music does
            data = process.stdout.read(buffer_size * channels)
            #this is useless becuase data will always be True. I think... Im not going to mess with it right now.
            if not data:
                break
            # Process audio data
            samples = np.frombuffer(data, dtype=np.float32).astype(np.float64)
            cava_output = np.zeros((number_of_bars * channels,), dtype=np.float64)

            # Execute Cava visualization
            cava_lib.cava_execute(samples.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), len(samples), cava_output.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), plan)
            self.update_visualization(cava_output)



    def update_visualization(self, sample):
        # Update the visualization data and redraw
        self.visualizer.sample = sample
        GLib.idle_add(self.drawing_area.queue_draw)  # Request to redraw the area



win = MyWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
