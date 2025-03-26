import os
import select
import struct
import subprocess
import tempfile
import threading
import gi
import configparser
import urllib.request
import cairo
import time
import selectors
import ctypes
import sys
import numpy as np
gi.require_version("Gtk", "3.0")
gi.require_version('Gst', '1.0')
gi.require_version('Gio', '2.0')
from gi.repository import Gtk, GdkPixbuf , Gdk , GLib , Gst , Gio
from configmaker import create_config


if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))


#get cavacore ready
cava_lib = ctypes.CDLL(os.path.join(base_path , 'libcavacore.so'))

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

if os.path.exists('config.ini'):
    config.read('config.ini')
else:
    print('Cannot find main config file. Falling back to example config file.')
    if os.path.exists('config_example.ini'):
        config.read('config_example.ini')
    else:
        print("Could not find the config example file. Creating one now.")
        create_config()
        config.read('config_example.ini')

debug = config['General'].getboolean('debug', fallback=False)
if debug:
    print("Debug mode")



# Configure cavacore
try:
    number_of_bars = int(config['gvis']['bars'])
    rate = int(config['gvis']['rate'])
    channels = int(config['gvis']['channels'])
    autosens = int(config['gvis']['autosens'])
    noise_reduction = float(config['gvis']['noise_reduction'])
    low_cut_off = int(config['gvis']['low_cut_off'])
    high_cut_off = int(config['gvis']['high_cut_off'])
    buffer_size = int(config['gvis']['buffer_size'])
    input_source = str(config['gvis']['input_source'])
    vis_type = str(config['gvis']['vis_type'])
    fill = config.getboolean('gvis' ,'fill')
except KeyError as e:
    print(f"Missing key in config file: {e}")
    sys.exit(1)
except ValueError as e:
    print(f"Invalid value in config file: {e}")
    sys.exit(1)

gradient = config.getboolean('gvis' ,'gradient')

#get the background color
background_rgba = config['gvis']['background_col'].split(',')
if len(background_rgba) == 4:
    background_rgba = [float(i) for i in background_rgba]
    background_col = tuple(background_rgba)
else:
    background_col = (0,0,0,0.5)
 
if gradient:
    colors = config['gvis']['color_gradent'].split(',')
    colors = [float(i) for i in colors]
    colors_list = []
    if len(colors) % 4 == 0:
        num_colors = len(colors) // 4
        for i in range(num_colors):
            color = tuple(colors[(i*4):((i+1)*4)])
            colors_list.append(color)      
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
            self.back_image = Gtk.Image.new_from_file(os.path.join(sys._MEIPASS, 'back.png'))
        else:
            self.back_image = Gtk.Image.new_from_file(os.path.join(base_path , 'back.png'))
        self.back_button = Gtk.Button(image = self.back_image)
        self.back_button.get_style_context().add_class("transparent-button")
        self.back_button.set_relief(Gtk.ReliefStyle.NONE)
        self.song_box.pack_start(self.back_button, True, True, 0)



        # Add the album art holder to the window
        self.info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.info_box.set_valign(1)
        self.song_box.pack_start(self.info_box, True, True, 0)
        

        if hasattr(sys, '_MEIPASS'):
            self.skip_image = Gtk.Image.new_from_file(os.path.join(sys._MEIPASS, 'skip.png'))
        else:
            self.skip_image = Gtk.Image.new_from_file(os.path.join(base_path , 'skip.png'))
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
        # Start CAVA processing in a separate thread so it can begin processing audio
        threading.Thread(target=self.run_cava, daemon=True).start()

        self.drawing_area.connect("draw", self.on_draw)
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

    def on_pause_button_clicked(self, button):
        if self.source:
            self.source.call_sync(
                "org.mpris.MediaPlayer2.Player.PlayPause",  # D-Bus method to call
                None,                                      # No arguments for PlayPause
                Gio.DBusCallFlags.NONE,                    # No special flags
                -1,                                        # No timeout
                None                                       # No cancellable
            )

    def on_back_button_clicked(self, button):
        """Skip to the previous track."""
        if self.source:
            self.source.call_sync(
                "org.mpris.MediaPlayer2.Player.Previous",  # D-Bus method to call
                None,                                      # No arguments for PlayPause
                Gio.DBusCallFlags.NONE,                    # No special flags
                -1,                                        # No timeout
                None                                       # No cancellable
            ) # Call the Previous method from the MPRIS interface
            self.progress_bar.set_fraction(0)


    def on_skip_button_clicked(self, button):
        """Skip to the next track."""
        if self.source:
            self.source.call_sync(
                "org.mpris.MediaPlayer2.Player.Next",  # D-Bus method to call
                None,                                      # No arguments for PlayPause
                Gio.DBusCallFlags.NONE,                    # No special flags
                -1,                                        # No timeout
                None                                       # No cancellable
            ) # Call the Previous method from the MPRIS interface

    def on_draw(self, widget, cr):
        # Set the transparent background
        cr.set_source_rgba(*background_col)
        cr.paint()

        # Draw the visualization
        if hasattr(self, 'sample'):
            #all of this stuff may be able to be calculated in advance.
            #the only issue is that resizing the window would mess it up.
            screen_height = widget.get_allocated_height()
            bar_width = widget.get_allocated_width() / (number_of_bars * 2)
            global vis_type

            if not gradient:
                cr.set_source_rgba(*color)
            else:
                #gradient calculations
                pattern = cairo.LinearGradient(0, 0, widget.get_allocated_width(), screen_height)
                for i, color in enumerate(colors_list):
                    stop_position = i / (num_colors - 1)  # Normalize between 0 and 1
                    pattern.add_color_stop_rgba(stop_position, *color)
                cr.set_source(pattern)
    
            if vis_type == 'bars':
                    for i, value in enumerate(self.sample):
                        #this whole block of code assumes that 2 channels are being used.
                        #granted no one uses mono audio so it does not matter that much.
                        if i < number_of_bars:
                            i = (number_of_bars - i)
                            flip = -1
                        else:
                            flip = 1
                        if i == number_of_bars:
                            #this attaches the two channels together.
                            #it does use a diagnal line but its impossible to see above 10 bars.
                            #we also need it or the filler will go crazy
                            cr.move_to(i*bar_width , screen_height*(1-self.sample[0]))
                        # Calculate height based on the sample value
                        height = value * screen_height
                        #draw just the tops and one side of the bars.
                        #cuts the amount of lines in half making it FAST
                        cr.line_to(i*bar_width,screen_height*(1-value))
                        cr.line_to((i+flip)*bar_width,screen_height*(1-value))

                        if i == 1 or i == number_of_bars * 2 - 1:
                            #draws lines on the sides and bottom.
                            #if we did not do this it would fill in a straight line twords the middle.
                            cr.line_to((i+flip)*bar_width , screen_height)
                            cr.line_to(widget.get_allocated_width()/2 , screen_height)
                    
                    #stroke is mostly for debugging but you can use it if you want
                    if fill:
                        cr.fill()
                    else:
                        cr.stroke()
                
            elif vis_type == 'lines':
                    cr.set_line_width(2)

                    for i, value in enumerate(self.sample):
                        #this is almost the same as the bar function but it draws only 1 line per bar.
                        if i < number_of_bars:
                            i = (number_of_bars - i)
                            flip = -1
                        else:
                            flip = 1
                        if i == number_of_bars:
                            cr.move_to(i*bar_width , screen_height*(1-self.sample[0]))
                        #Calculate height based on the sample value
                        height = value * screen_height
                        cr.line_to((i+flip)*bar_width , screen_height*(1-value))
                        if i == 1 or i == number_of_bars * 2 - 1:
                            cr.line_to((i+flip)*bar_width , screen_height)
                            cr.line_to(widget.get_allocated_width()/2 , screen_height)

                    if fill:
                        cr.fill()
                    else:
                        cr.stroke()
            else:
                #fallback if there is something weird in the config.
                vis_type = 'bars'
                self.queue_draw()

    def get_mpris_service(self):
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)

        dbus_proxy = Gio.DBusProxy.new_sync(
            bus,
            Gio.DBusProxyFlags.NONE,
            None,
            "org.freedesktop.DBus",
            "/org/freedesktop/DBus",
            "org.freedesktop.DBus",
            None
        )
        # Call the ListNames method on the D-Bus interface
        available_services = dbus_proxy.call_sync(
            "ListNames",              # Method name
            None,                     # No parameters
            Gio.DBusCallFlags.NONE,    # No special flags
            -1,                        # No timeout
            None                       # No cancellable
        )
        # Extract the names from the result
        available_services = available_services[0]  # The result is a tuple, we want the first element
        # List available services
        mpris_services = [s for s in available_services if s.startswith("org.mpris.MediaPlayer2.")]
        if 'org.mpris.MediaPlayer2.plasma-browser-integration' in mpris_services:
            mpris_services = ['org.mpris.MediaPlayer2.plasma-browser-integration']

        source = None

        Failed_sources = []
        working_sources = []
        for i in mpris_services:
            try:     
                # Create a proxy for each MPRIS service
                mpris_proxy = Gio.DBusProxy.new_sync(
                    bus,
                    Gio.DBusProxyFlags.NONE,
                    None,
                    i,  # Use the MPRIS service name
                    "/org/mpris/MediaPlayer2",
                    "org.mpris.MediaPlayer2.Player",  # Correct interface for MPRIS
                    None
                )
                working_sources.append(mpris_proxy)
            except:
                Failed_sources.append(i)
        

        print(mpris_services)
        print(working_sources)
        
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
        self.sample = sample
        GLib.idle_add(self.drawing_area.queue_draw)  # Request to redraw the area



win = MyWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
