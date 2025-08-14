"""
gvis - UI control functions
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

from gi.repository import Gio

def on_pause_button_clicked(source, button): #TODO: remove all of the random unused parameters that copilot put in here
    if source:
        source.call_sync(
            "org.mpris.MediaPlayer2.Player.PlayPause",  # D-Bus method to call
            None,                                      # No arguments for PlayPause
            Gio.DBusCallFlags.NONE,                    # No special flags
            -1,                                        # No timeout
            None                                       # No cancellable
        )

def on_back_button_clicked(source, button, progress_bar):
    """Skip to the previous track."""
    if source:
        source.call_sync(
            "org.mpris.MediaPlayer2.Player.Previous",  # D-Bus method to call
            None,                                      # No arguments for PlayPause
            Gio.DBusCallFlags.NONE,                    # No special flags
            -1,                                        # No timeout
            None                                       # No cancellable
        )  # Call the Previous method from the MPRIS interface
        progress_bar.set_fraction(0)

def on_skip_button_clicked(source, button):
    """Skip to the next track."""
    if source:
        source.call_sync(
            "org.mpris.MediaPlayer2.Player.Next",  # D-Bus method to call
            None,                                      # No arguments for PlayPause
            Gio.DBusCallFlags.NONE,                    # No special flags
            -1,                                        # No timeout
            None                                       # No cancellable
        )  # Call the Previous method from the MPRIS interface
