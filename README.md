A music visualizer based on cavacore and built with Gtk+3.

<img width="1920" height="1080" alt="Screenshot From 2026-01-19 14-44-25" src="https://github.com/user-attachments/assets/8de758e6-e1a3-4d48-8aa7-fd24b103836e" />

# Features

## No Limits!
This app removes the limitations of normal cava!  
Want to have 1,000 bars and push your GPU to its limits? Now you can!  

Be cautious, though—setting the bar count too high may cause segmentation faults and crashes. It's almost as if cavacore wasn't designed for that.

## Lower-Level Customization
In cava, the configuration file restricts access to many low-level settings to promote "stability."  
I don't care about stability.  

Want to set the buffer size to 1?  
Well, you can't—numpy gets mad if you do that.  
But you can set it to 2.  
**Warning:** Don't do this if you have epilepsy.

## 32-Bit Audio
Cava in raw mode only supports 16-bit integers.  
gvis uses 32-bit floats!  
(It can also use 64-bit floats, but that causes issues.)

## Direct Audio Capture
Capture audio directly from individual apps instead of the entire system!  
This means things like Discord pings won't show up in the visualization.

## Music Control
Control any app that supports MPRIS MediaPlayer2 (e.g., any app you can pause without switching to it).  
Even some CLI music players might work.

## Song Progress Bar
A progress bar shows your position in the song.  
It used to be unreliable, but now it's fixed.  
Note: It works better if the app supports retrieving the current position.

## Scrobbling with last.fm!
If you have a last.fm account, you can hook it up to gvis and it will scrobble automatically.

# scrobble setup
Make sure `scrobble` is set to `True` in your config.
Run gvis in the terminal.
Open the link it provides and follow the directions on last.fm.
You're done!
You can now run gvis normally, and it will continue to work.

# Supported Apps
1. Firefox  
2. VLC (but only when it feels like it)  
3. Any app where you know the PipeWire ID or `node.name`.

# Installation 
## via pre built binarys
You can find (a) pre built binary in github releases (only works for x86)
as long as you have GTK+3 and pipewire it should work

## Makefile
Download the source files and run `make install` and your done!
Needs python,pip and gtk.

## PKGBUILD
If your on arch you can use the pkgbuild! Its under /pkg/arch.
There is a normal PKGBUILD and PKGBUILD-bin (untested and unsupported for now )
Its still a WIP and breaks a lot of rules (not one that damage anything just NOT best practice) so thats why its not on the aur.

If you want to use last.fm with it you will have to supply a .env file in the root dir (the same folder as your PKGBUILD) with an API_KEY and API_SECRET from last.fm https://www.last.fm/api/account/create

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

### Third-Party Components

- **libcavacore.so** (in `src/cava/`): Licensed under MIT License by Karl Stavestrand
- **All other files**: Licensed under GPL-3.0 unless otherwise noted

## Copyright

Copyright (C) 2025 mrhooman

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
