import os
import select
import struct
import subprocess
import tempfile
import threading
import gi
import configparser
from pydbus import SessionBus
import urllib.request
import cairo
import time
import selectors
import ctypes
import sys
import numpy as np
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf , Gdk , GLib

#get cavacore ready
cava_lib = ctypes.CDLL('./cavacore/build/libcavacore.so')

cava_lib.cava_init.argtypes = [
    ctypes.c_int, ctypes.c_uint, ctypes.c_int, ctypes.c_int, 
    ctypes.c_double, ctypes.c_int, ctypes.c_int
]
cava_lib.cava_init.restype = ctypes.POINTER(ctypes.c_void_p)

cava_lib.cava_execute.argtypes = [
    ctypes.POINTER(ctypes.c_double), ctypes.c_int, 
    ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_void_p)
]

cava_lib.cava_destroy.argtypes = [ctypes.POINTER(ctypes.c_void_p)]

config = configparser.ConfigParser()

try:
    config.read('config.ini')
except:
    print('cant find main config file. falling back to example config file')
    config.read('config_example.ini')

debug = config['General'].getboolean('debug')
if debug:
    print("debug mode")

#configure cavacore
number_of_bars = int(config['gvis']['bars'])
rate = int(config['gvis']['rate'])
channels = int(config['gvis']['channels'])
autosens = int(config['gvis']['autosens'])
noise_reduction = float(config['gvis']['noise_reduction'])
low_cut_off = int(config['gvis']['low_cut_off'])
high_cut_off = int(config['gvis']['high_cut_off'])
buffer_size = int(config['gvis']['buffer_size'])
input_source = str(config['gvis']['input_source'])

gradient = config.getboolean('gvis' ,'gradient')
draw_pending_check = config.getboolean('gvis' , 'draw_pending_check')

if gradient:
    colors = config['gvis']['color_gradent'].split(',')
    colors = [float(i) for i in colors]
    colors_list = []
    if len(colors) % 4 == 0:
        colors_amount = len(colors) // 4
        for i in range(colors_amount):
            color = tuple(colors[(i*4):((i+1)*4)])
            colors_list.append(color)
        
        gradient_colors = []
        for i in range(number_of_bars * channels):
            t = i / ((number_of_bars * 2) - 1)
            """Linearly interpolate between a list of colors (RGBA) based on t in [0, 1]."""
            num_colors = len(colors_list)
                        
            # Find the interval in which t falls
            if num_colors < 2:
                raise ValueError("At least two colors are required for interpolation.")
                        
            # Calculate the index of the first color
            index = min(int(t * (num_colors - 1)), num_colors - 2)
            ratio = t * (num_colors - 1) - index  # Calculate the ratio between the two colors
                            
            # Interpolate between the two colors
            gradient_colors.append (tuple(
                colors_list[index][i] + ratio * (colors_list[index + 1][i] - colors_list[index][i])
                for i in range(4)  # RGBA has 4 components
                ))
    
    
                
else:
    #turn color1 into a list
    color1 = config['gvis']['color1'].split(',')
    if len(color1) < 3:
        print('color1 needs at least 3 vaules to work. setting color to default (cyan).')
        color1 = ['0','1','1','1']
    elif len(color1) > 4:
        print('more than 4 values found. discarding extra values')
        color1 = color1[:4]
    color = []
    #turn all of the items in color1 into floats and add them to color
    color.extend(float(i) for i in color1)
    color = tuple(color)
    

plan = cava_lib.cava_init(number_of_bars, rate, channels, autosens, noise_reduction, low_cut_off, high_cut_off)
if plan == -1:
    print("Error initializing cava")
    exit(1)

draw_pending = False

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
        
        self.back_image = Gtk.Image.new_from_file('back.png')
        self.back_button = Gtk.Button(image = self.back_image)
        self.back_button.get_style_context().add_class("transparent-button")
        self.back_button.set_relief(Gtk.ReliefStyle.NONE)
        self.song_box.pack_start(self.back_button, True, True, 0)



        # Add the album art holder to the window
        self.info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.info_box.set_valign(1)
        self.song_box.pack_start(self.info_box, True, True, 0)
        

        self.skip_image = Gtk.Image.new_from_file('skip.png')
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

        self.back_button.connect("clicked", self.on_back_button_clicked)
        self.skip_button.connect("clicked", self.on_skip_button_clicked)
        self.pause_buttion.connect("clicked", self.on_pause_button_clicked)

        self.overlay.add_overlay(self.song_box)
        
        # Connect to MPRIS service and update the album art
        self.source = self.get_mpris_service()
        # Start CAVA processing in a separate thread
        threading.Thread(target=self.run_cava, daemon=True).start()

        self.drawing_area.connect("draw", self.on_draw)
        if self.source:
            self.source.onPropertiesChanged = self.on_properties_changed
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

    def on_pause_button_clicked(self, button):
        if self.source:
            self.source.PlayPause()

    def on_back_button_clicked(self, button):
        """Skip to the previous track."""
        if self.source:
            self.source.Previous()  # Call the Previous method from the MPRIS interface

    def on_skip_button_clicked(self, button):
        """Skip to the next track."""
        if self.source:
            self.source.Next()  # Call the Next method from the MPRIS interface

    def on_draw(self, widget, cr):
        global draw_pending
        # Set the transparent background
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.5) 
        cr.paint()

        # Draw the visualization
        if hasattr(self, 'sample'):
            bar_width = widget.get_allocated_width() / (number_of_bars * 2)
            for i, value in enumerate(self.sample):
                if i < number_of_bars:
                    i = ((number_of_bars - 1) - i)
                # Calculate height based on the sample value
                height = value * widget.get_allocated_height()
                # Set bar color (e.g., red)
                if debug:
                    #color the start and end bars red
                    if i == 0 or i == (number_of_bars * 2) - 1:
                        cr.set_source_rgba(1,0,0,1)
                    else:
                        cr.set_source_rgba(0,(1 - (i / ((number_of_bars * 2) - 1))),(i / ((number_of_bars * 2) - 1)),1)
                else:
                    if not gradient:
                        cr.set_source_rgba(*color)
                    else:
                        cr.set_source_rgba(*gradient_colors[i])
                    
                cr.rectangle(i * bar_width, widget.get_allocated_height() - height, bar_width, height)
                cr.fill()
            draw_pending = False
    
    def get_mpris_service(self):
        bus = SessionBus()
        dbus = bus.get(".DBus")

        # List available services
        available_services = dbus.ListNames()
        mpris_services = [s for s in available_services if s.startswith("org.mpris.MediaPlayer2.")]

        source = None

        Failed_sources = []
        working_sources = []
        for i in mpris_services:
            try:     
                working_sources.append(bus.get(i, "/org/mpris/MediaPlayer2"))
            except:
                Failed_sources.append(i)
        
        print(len(mpris_services))
        print(len(working_sources))
        
        if len(working_sources) == 1:
            source = working_sources[0]
        elif len(working_sources) > 1:
            if sys.stdin.isatty():
                print("please choose a mpris service 0 is the first option and 1 is the second and so on")
                print([s.Identity for s in working_sources])

                i, o, e = select.select( [sys.stdin], [], [], 5 )

                if (i):
                    source = working_sources[int(sys.stdin.readline().strip())]
                else:
                    print('input timed out chooseing first option')
                    source = working_sources[0]
        elif len(working_sources) == 0:
            raise ValueError("there needs to be at least one working mpris source")

        return source

    def on_properties_changed(self, interface_name, changed_properties, invalidated_properties):
        # Check if the changed properties include 'mpris:artUrl' or other relevant metadata
        print(changed_properties)
        if 'Metadata' in changed_properties:
            print("update")
            self.update_info()

    def update_info(self):
        if not self.source:
            return

        metadata = self.source.Metadata


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
            if self.source.Position / self.source.Metadata.get('mpris:length') > 1:
                self.progress_bar.set_fraction(self.source.Position / self.source.Metadata.get('mpris:length'))
            elif self.new_song:
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

        try:
            Rate = self.source.Rate
        except:
            Rate = 1.0
        try:
            self.progress_rate = ((100000 / self.source.Metadata.get('mpris:length')) * Rate)
        except TypeError:
            print('cant find song length. progress bar will not work')
            self.progress_rate = 0
        album_image_url = metadata.get("mpris:artUrl")
        if album_image_url:
            # Download the image
            try:
                response = urllib.request.urlopen(album_image_url)
                image_data = response.read()

                # Load image data into GdkPixbuf
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
        if self.just_updated:
            self.just_updated = False
        elif self.source.PlaybackStatus == 'Playing':
            self.progress_bar.set_fraction(self.progress_bar.get_fraction() + self.progress_rate)
        return True

    
    def run_cava(self):
        global input_source
        if input_source == "Auto":
            print("input_source set to Auto. attempting to detect source.")
            app = str(self.source.Identity)
            print(f"detected app: {app}")
            if app == "Mozilla firefox":
                input_source = "Firefox"
            elif app == "VLC media player":
                input_source = 'VLC media player (LibVLC 3.0.21)'
            else:
                print(f"unsupported app {app} falling back to 'auto'")
                input_source = "auto"
            print(f"setting audio target to {input_source}")
        
        process = subprocess.Popen(
            ["pw-cat", "-r", "--target", str(input_source), "--format" , "f32" , "-"],
            stdout=subprocess.PIPE,
            bufsize=buffer_size * channels,
        )

        selector = selectors.DefaultSelector()
        global draw_pending
        while True:
            data = process.stdout.read(buffer_size * channels)
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
        self.sample = sample
        global draw_pending , draw_pending_check
        if not draw_pending or not draw_pending_check:
            draw_pending = True
            self.drawing_area.queue_draw()  # Request to redraw the area



win = MyWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
