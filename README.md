A music visulizer based on cavacore and built with Gtk+3
## this app only works with pipewire right now becuase that is what I use and I have no way of testing anything else.


![image](https://github.com/user-attachments/assets/25d1961d-f445-4d02-82cf-bbce99bfbe86)

Im not gay I just like the look of rainbows

# features

## no limits!
this does not have any of the limits that normal cava has!
want to have 1,000 bars and make your gpu explode? now you can!
![image](https://github.com/user-attachments/assets/20ed4d75-984b-411b-92e0-af87b2ddafe4)

dont go too high though or it will seg fault and crash.
its almost like you are not suppost to make cavacore do that.

## lower level customization!

in cava the config file does not let you touch a lot of the lower stuff directly to premote "stability".
well I dont care about stability.
want to set the buffer size to 1?
well you cant. numpy gets mad if you do that.
but you can set it to 2.
dont do that if you have epilepsy though.

## 32 bit audio!
if you put cava in raw mode the most it will let you use is a 16 bit integer.
gvis uses a 32bit float!
(it can also use 64 bit floats but that causes issues)

## directy capture audio from indvitual apps instead of the whole system!
things like discord pings wont show up on the visulisation.

## music control!
any app the supports mpris MediaPlayer2 (aka any app that you can pause without going to the app) can be controlled via gvis.
even some cli music players (might) work.

## song progress bar (less scuffed)!
there is a progress bar that shows your spot in the song and the best part is it does not work (now fixed).
well it might work better if the app supports getting the position but I have not found any.

# supported apps
1.firefox
2.vlc (but only when it feels like it)
3.Any app where you know the PipeWire ID or node.name.

# how to run
the first time you run it make sure to run it in a termnal that you can input stuff into.
if it works without any error you can run it using this command (or just by clicking it)
`nohup ./gvis.bin & disown && exit`
