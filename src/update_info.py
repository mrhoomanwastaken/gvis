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

import threading
import urllib.request
from gi.repository import GdkPixbuf, GLib, Gio
from src.scrobbler import scrobble_track


def _extract_metadata(metadata_variant):
    metadata = metadata_variant.unpack()
    if isinstance(metadata, tuple) and metadata:
        metadata = metadata[0]
    if hasattr(metadata, 'unpack'):
        metadata = metadata.unpack()
    if isinstance(metadata, dict):
        return metadata
    return {}


def _start_album_art_fetch(self, album_image_url):
    request_id = getattr(self, '_album_art_request_id', 0) + 1
    self._album_art_request_id = request_id
    self._album_art_loading_url = album_image_url

    def _apply_album_art(current_request_id, current_url, image_data):
        if getattr(self, '_album_art_request_id', 0) != current_request_id:
            return False
        try:
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

            relative_size = min(relative_height, relative_width, 1)
            scaled_size = int(300 * relative_size)
            scaled_pixbuf = self.album_art_pixbuf.scale_simple(scaled_size, scaled_size, GdkPixbuf.InterpType.BILINEAR)
            self.album_art.set_from_pixbuf(scaled_pixbuf)
            self._album_art_current_url = current_url
        except Exception as e:
            print(f"Failed to load album image: {e}")
        finally:
            if getattr(self, '_album_art_loading_url', None) == current_url:
                self._album_art_loading_url = None
        return False

    def _report_album_art_error(current_request_id, current_url, error_message):
        if getattr(self, '_album_art_request_id', 0) != current_request_id:
            return False
        if getattr(self, '_album_art_loading_url', None) == current_url:
            self._album_art_loading_url = None
        print(f"Failed to load album image: {error_message}")
        return False

    def _fetch_album_art():
        try:
            with urllib.request.urlopen(album_image_url, timeout=2.0) as response:
                image_data = response.read()
                GLib.idle_add(_apply_album_art, request_id, album_image_url, image_data)
        except Exception as e:
            GLib.idle_add(_report_album_art_error, request_id, album_image_url, str(e))

    threading.Thread(target=_fetch_album_art, daemon=True).start()

def update_info(self , scrobble_enabled , network):
    # sometimes update_info is called when there is no source
    # that happens the first time the app is opened before a player is detected
    if not self.source:
        return

    try:
        metadata_variant = self.source.get_cached_property("Metadata")
        if metadata_variant is None:
            metadata_variant = self.source.call_sync(
                "org.freedesktop.DBus.Properties.Get",
                GLib.Variant("(ss)", ("org.mpris.MediaPlayer2.Player", "Metadata")),
                Gio.DBusCallFlags.NONE,
                500,
                None
            )
    except GLib.GError as e:
        print(f"Failed to fetch metadata: {e}")
        return
    metadata = _extract_metadata(metadata_variant)

    song_name = metadata.get('xesam:title')
    self.song_name.set_label(song_name)

    # NOTE: dont touch this code it is cursed and haunted
    # this took the longest time to debug because of the mess of if else statements
    # see next comment block for more info
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
    #2. the update_progress function will overestimate the position if the song is longer than 100000 seconds
    #3. kde is somehow even worse than this is and just gives the wrong song length (I have no idea where it gets its numbers from it seems like its just the amount of time that songs have been playing plus 1 minute)
    #4. sometimes it will spam 'cant find accurate position in song assuming song just started' and I don't know why
    #6. rate does not work with any apps i have tested, but that does not matter because who listens to music at 2x speed anyway
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

    #sometimes it will load a really low res image so it looks pixelated
    #I don't know why it does this
    #it only seems to happen with the first song of the session
    #also on youtube music if the song is a video it will not load the image at all but only on kde
    #on anything but kde it will squish the thumbnail to fit the 300x300 size
    album_image_url = metadata.get("mpris:artUrl")
    if album_image_url:
        current_art_url = getattr(self, '_album_art_current_url', None)
        loading_art_url = getattr(self, '_album_art_loading_url', None)
        if album_image_url != current_art_url and album_image_url != loading_art_url:
            _start_album_art_fetch(self, album_image_url)
    else:
        print("No album image available.")

    if scrobble_enabled and self.new_song:
        # Scrobble the track
        # this fails if any of the metadata is missing
        # this happens on websites that are not for music (ie most social media sites)
        try:
            print(f"Attempting to scrobble: {artist_name[0]} - {song_name} - {album_name}")
            threading.Thread(
                target=scrobble_track,
                args=(network, artist_name, song_name, album_name, metadata.get('mpris:length')/1000000),
                daemon=True
            ).start()
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