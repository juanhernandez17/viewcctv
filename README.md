# viewcctv
PyQt windows application to watch multiple streams using VLC

## viewcctv.py
Used to watch multiple cctv camera streams in one place instead of using the default cctv software that might use up more resources than opening the streams in VLC
Using this inside a virtual environment will require further setup for python-vlc

### requires
>vlc

### Python Requirements
>PyQt5==5.15.7

>pyqtdarktheme==1.1.0

>python-vlc==3.0.16120

## rtsp.py
Used to scan ip of camera dvr for rtsp stream using snapshot in ffmpeg
the output will tell you the format of the streaming url of the rtsp stream
[the paths.csv file comes from here](https://github.com/CamioCam/rtsp)

### requires
>ffmpeg


## comand to pack viewcctv.py into an exe
>pyinstaller --noconsole --onefile viewcctv.py
