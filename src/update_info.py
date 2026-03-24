"""
gvis - Information update functions
Copyright (C) 2025 mrhooman

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import urllib.request
from gi.repository import GdkPixbuf, GLib, Gio
from src.scrobbler import scrobble_track

def update_info(self , scrobble_enabled , network):
    # sometimes update_info is called when there is no source
    # that happens the first time the app is opened before a player is detected
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

    # Track whether the song has changed since the last update.
    # AttributeError is expected on the very first call before self.old_song is set.
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
    except Exception:
        pass

    # Known MPRIS position/progress limitations:
    # 1. Many players do not expose Position reliably, so the bar defaults to 0 on a new song.
    # 2. update_progress() will drift for songs longer than 100 000 seconds (not a real concern).
    # 3. Some desktop environments (e.g. KDE) report incorrect song lengths.
    # 4. The "Rate" property is ignored by most tested players, so playback speed is assumed 1.0.
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
        # MPRIS "Rate" is the playback speed multiplier (1.0 = normal speed).
        rate = self.source.get_cached_property("Rate").unpack()
    except Exception:
        rate = 1.0

    try:
        # mpris:length is in microseconds; divide by 1 000 000 to convert to seconds.
        self.progress_rate = (100000 / metadata.get('mpris:length')) * rate
    except TypeError:
        print('Cannot find song length; progress bar will not update.')
        self.progress_rate = 0

    #sometimes it will load a really low res image so it looks pixelated
    #I don't know why it does this
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
            self.album_art_pixbuf = loader.get_pixbuf()

            try:
                relative_height = self.new_height / 500
                relative_width = self.new_width / 821
            except AttributeError:
                relative_height = self.height / 500
                relative_width = self.width / 821

            relative_size = min(relative_height , relative_width , 1) # dont let it get bigger than 1x size
            scaled_size = int(300 * relative_size)

            scaled_pixbuf = self.album_art_pixbuf.scale_simple(scaled_size, scaled_size, GdkPixbuf.InterpType.BILINEAR)
            self.album_art.set_from_pixbuf(scaled_pixbuf)
        except Exception as e:
            print(f"Failed to load album image: {e}")
    else:
        print("No album image available.")

    if scrobble_enabled and self.new_song:
        # Scrobble the track
        # this fails if any of the metadata is missing
        # this happens on websites that are not for music (ie most social media sites)
        try:
            print(f"Attempting to scrobble: {artist_name[0]} - {song_name} - {album_name}")
            scrobble_track(network,artist_name,song_name , album_name , metadata.get('mpris:length')/1000000)
        except Exception as e:
            print(f"Failed to scrobble: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            traceback.print_exc()


    self.new_song = False

def update_progress(self):
    # there is a bit of inaccuracy here because of floating point nonsense
    # but it should be close enough for a progress bar
    # if you are on kde and it seems way off, its not my fault, blame kde (see above comments for more info)
    if self.just_updated:
        self.just_updated = False
    elif self.source.get_cached_property("PlaybackStatus").unpack() == 'Playing':
        self.progress_bar.set_fraction(self.progress_bar.get_fraction() + self.progress_rate)
    return True