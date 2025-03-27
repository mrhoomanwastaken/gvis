import urllib.request
from gi.repository import GdkPixbuf, GLib, Gio

def update_info(self):
    if not self.source:
        return

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
        position_variant = self.source.get_cached_property("Position")
        current_position = position_variant.unpack()
    except:
        pass

    try:
        if current_position / metadata.get('mpris:length') > 1:
            self.progress_bar.set_fraction(current_position / metadata.get('mpris:length'))
        elif self.new_song:
            print('cant find accurate position in song assuming song just started')
            self.progress_bar.set_fraction(0)
    except (UnboundLocalError, GLib.GError):
        if self.new_song:
            print('cant find accurate position in song assuming song just started')
            self.progress_bar.set_fraction(0)
    self.just_updated = True

    try:
        Rate = self.source.get_cached_property("rate").unpack
    except:
        Rate = 1.0

    try:
        self.progress_rate = ((100000 / metadata.get('mpris:length')) * Rate)
    except TypeError:
        print('cant find song length. progress bar will not work')
        self.progress_rate = 0

    album_image_url = metadata.get("mpris:artUrl")
    if album_image_url:
        try:
            response = urllib.request.urlopen(album_image_url)
            image_data = response.read()

            loader = GdkPixbuf.PixbufLoader.new()
            loader.write(image_data)
            loader.close()
            pixbuf = loader.get_pixbuf()

            scaled_pixbuf = pixbuf.scale_simple(300, 300, GdkPixbuf.InterpType.BILINEAR)
            self.album_art.set_from_pixbuf(scaled_pixbuf)
        except Exception as e:
            print(f"Failed to load album image: {e}")
    else:
        print("No album image available.")

    self.new_song = False

def update_progress(self):
    if self.just_updated:
        self.just_updated = False
    elif self.source.get_cached_property("PlaybackStatus").unpack() == 'Playing':
        self.progress_bar.set_fraction(self.progress_bar.get_fraction() + self.progress_rate)
    return True