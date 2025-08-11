import sys
import select
from gi.repository import Gio

#note: I dont like dbus_proxy but the good versions are deprecated

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