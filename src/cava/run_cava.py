import subprocess
import selectors
import numpy as np
import ctypes
from gi.repository import GLib, Gio
#uuuh I forgot the licanse for cava
#TODO: add it later
#please dont sue me

def run_cava(input_source, buffer_size, channels, number_of_bars, cava_lib, plan, update_visualization, source):
    if input_source == "Auto":
        print("input_source set to Auto. attempting to detect source.")
        # Get the music app that MPRIS is connected to.
        identity_variant = source.call_sync(
            "org.freedesktop.DBus.Properties.Get",
            GLib.Variant("(ss)", ("org.mpris.MediaPlayer2", "Identity")),
            Gio.DBusCallFlags.NONE,
            -1,  # No timeout
            None  # No cancellable
        )
        app = identity_variant.unpack()[0]

        # Use the app name to get the PipeWire node.name of the music app
        print(f"detected app: {app}")
        if app == "Mozilla firefox" or app == "Firefox":
            input_source = "Firefox"
        elif app == "VLC media player":
            input_source = 'VLC media player (LibVLC 3.0.21)'
        else:
            print(f"unsupported app {app} falling back to 'auto'")
            input_source = "auto"
        print(f"setting audio target to {input_source}")

    # Open pw-cat to stream audio data from the app or microphone.
    process = subprocess.Popen(
        ["pw-cat", "-ra", "--target", str(input_source), "--format", "f32", "-"],
        stdout=subprocess.PIPE,
        bufsize=buffer_size * channels,
    )

    selector = selectors.DefaultSelector()

    # Start processing the audio data
    while True:
        data = process.stdout.read(buffer_size * channels)
        if not data:
            break
        # Process audio data
        samples = np.frombuffer(data, dtype=np.float32).astype(np.float64)
        cava_output = np.zeros((number_of_bars * channels,), dtype=np.float64)

        # Execute Cava visualization
        cava_lib.cava_execute(
            samples.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            len(samples),
            cava_output.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            plan
        )
        update_visualization(cava_output)
