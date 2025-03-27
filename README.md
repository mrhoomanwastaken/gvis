A music visualizer based on cavacore and built with Gtk+3.

Currently in development and will progress further during school breaks.

## Compatibility
This app only works with PipeWire right now because that is what I use, and I have no way of testing it with other systems.

![image](https://github.com/user-attachments/assets/16135590-98e1-4178-9906-b0680c344506)

# Features

## No Limits!
This app removes the limitations of normal cava!  
Want to have 1,000 bars and push your GPU to its limits? Now you can!  
![image](https://github.com/user-attachments/assets/df734c92-c526-403c-b93c-0e064890679c)

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

# Supported Apps
1. Firefox  
2. VLC (but only when it feels like it)  
3. Any app where you know the PipeWire ID or `node.name`.

# How to Run
The first time you run it, make sure to use a terminal where you can input commands.  
If it works without errors, you can run it using this command (or by clicking it):  
`nohup ./gvis.bin & disown && exit`
