import urllib.request
from gi.repository import GdkPixbuf, GLib, Gio
from src.scrobbler import scrobble_track

def update_info(self , scrobble_enabled , network):
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

    #this code haunts my nightmares
    #here are all the known issues:
    #1. I have not seen a single player that returns a position so its always going to assume the song just started
    #2. the update_progress function will overestamate the position if the song is longer than 100000 seconds
    #3. kde is somehow even worse then this is and just gives the wrong song length (I have no idea where it gets its numbers from it seems like its just the amount of time that songs have been playing plus 1 minute)
    #4. sometimes it will spam 'cant find accurate position in song assuming song just started' and I dont know why
    #6. rate does not work with any apps i have tested, but that does not matter becuase who listens to music at 2x speed anyway
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
        self.progress_rate = ((100000 / metadata.get('mpris:length')) * Rate) #for some reason mpris gives the length in microseconds I have no idea why we need that level of precision
    except TypeError:
        print('cant find song length. progress bar will not work') # if you see this im sorry for your loss. im not helping you.
        self.progress_rate = 0

    #sometimes it will load a realy low res image so it looks pixelated
    #I dont know why it does this
    #it only seems to happen with the first song of the session
    #also on youtube music if the song is a video it will not load the image at all but only on kde
    #on anything but kde it will squish the thumbnail to fit the 300x300 size
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

    if scrobble_enabled and self.new_song:
        try:
            scrobble_track(network,artist_name,song_name , album_name , metadata.get('mpris:length')/1000000)
        except Exception as e:
            print(f"Failed to scrobble: {e}")


    self.new_song = False

def update_progress(self):
    if self.just_updated:
        self.just_updated = False
    elif self.source.get_cached_property("PlaybackStatus").unpack() == 'Playing':
        self.progress_bar.set_fraction(self.progress_bar.get_fraction() + self.progress_rate)
    return True