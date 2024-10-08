import os
import struct
import subprocess
import tempfile
import threading
import gi
from pydbus import SessionBus
import urllib.request
import cairo
import time
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf , Gdk , GLib

BARS_NUMBER = 250
OUTPUT_BIT_FORMAT = "16bit"
RAW_TARGET = "/dev/stdout"

conpat = """
[general]
bars = %d
[output]
method = raw
raw_target = %s
bit_format = %s
"""

config = conpat % (BARS_NUMBER, RAW_TARGET, OUTPUT_BIT_FORMAT)
bytetype, bytesize, bytenorm = ("H", 2, 65535) if OUTPUT_BIT_FORMAT == "16bit" else ("B", 1, 255)

class MyWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="gvis")
        screen = self.get_screen()
        width = screen.get_width()
        height = screen.get_height()
        self.set_default_size(width // 2, height // 2)

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
        self.album_art_holder = Gtk.Image()
        self.info_box.pack_start(self.album_art_holder, True, True, 0)  # Add the image to the box

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

        self.overlay.add_overlay(self.song_box)
        
        # Start CAVA processing in a separate thread
        threading.Thread(target=self.run_cava, daemon=True).start()

        self.drawing_area.connect("draw", self.on_draw)
        GLib.timeout_add(100, self.refresh_drawing_area)
        # Connect to MPRIS service and update the album art
        self.source = self.get_mpris_service()
        if self.source:
            self.source.onPropertiesChanged = self.on_properties_changed
            self.update_info()
    def refresh_drawing_area(self):
        # Redraw the drawing area
        self.drawing_area.queue_draw()
        return True  # Keep the timeout active

    def on_back_button_clicked(self, button):
        """Skip to the previous track."""
        if self.source:
            self.source.Previous()  # Call the Previous method from the MPRIS interface

    def on_skip_button_clicked(self, button):
        """Skip to the next track."""
        if self.source:
            self.source.Next()  # Call the Next method from the MPRIS interface

    def on_draw(self, widget, cr):
        # Set the transparent background
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.5) 
        cr.paint()

        # Draw the visualization
        if hasattr(self, 'sample'):
            bar_width = widget.get_allocated_width() / BARS_NUMBER
            for i, value in enumerate(self.sample):
                # Calculate height based on the sample value
                height = value * widget.get_allocated_height()
                # Set bar color (e.g., red)
                cr.set_source_rgba(1, 0, 0, 1)  # Red color
                cr.rectangle(i * bar_width, widget.get_allocated_height() - height, bar_width, height)
                cr.fill()
    
    def get_mpris_service(self):
        bus = SessionBus()
        dbus = bus.get(".DBus")

        # List available services
        available_services = dbus.ListNames()
        mpris_services = [s for s in available_services if s.startswith("org.mpris.MediaPlayer2.")]

        source = None

        try:
            if mpris_services:
                source = bus.get(mpris_services[0], "/org/mpris/MediaPlayer2")
                print(f"Connected to {mpris_services[0]}")
            else:
                print("No MPRIS service found.")
        except:
            if len(mpris_services) > 1:
                source = bus.get(mpris_services[1], "/org/mpris/MediaPlayer2")
                print(f"Connected to {mpris_services[1]}")
            else:
                print("No MPRIS service found.")

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

        album_name = metadata.get('xesam:album')
        self.album_name.set_label(album_name)

        artist_name = metadata.get('xesam:artist')
        self.artist_name.set_label(artist_name[0])


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
                self.album_art_holder.set_from_pixbuf(scaled_pixbuf)

            except Exception as e:
                print(f"Failed to load album image: {e}")
        else:
            print("No album image available.")
    
    def run_cava(self):
        with tempfile.NamedTemporaryFile() as config_file:
            config_file.write(config.encode())
            config_file.flush()

            process = subprocess.Popen(["cava", "-p", config_file.name], stdout=subprocess.PIPE)
            chunk = bytesize * BARS_NUMBER
            fmt = bytetype * BARS_NUMBER

            source = process.stdout

            while True:
                data = source.read(chunk)
                if len(data) < chunk:
                    break
                sample = [i / bytenorm for i in struct.unpack(fmt, data)]
                self.update_visualization(sample)

    def update_visualization(self, sample):
        # Update the visualization data and redraw
        self.sample = sample
        self.drawing_area.queue_draw()  # Request to redraw the area



win = MyWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
