"""
gvis - MPRIS service management
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

import sys
import select
from gi.repository import Gio

#NOTE: I dont like dbus_proxy but the good versions are deprecated

def get_mpris_service():
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
    # this will list the pygobject proxies that are working
    # this is an issue because the names are not human readable (looks like base64)
    # and because the user has to choose between them if there are multiple working sources thats bad
    # but the first one is usually the right one so its not a huge issue
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
                print('input timed out choosing first option')
                source = working_sources[0]
    elif len(working_sources) == 0:
        raise ValueError("there needs to be at least one working mpris source")

    return source