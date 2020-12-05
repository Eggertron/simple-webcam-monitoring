# simple-webcam-monitoring
Very quick and dirty IP Webcam monitoring to reuse old android phones.

## Setup
You'll need to have python installed in your system. To do that you can run
this script, [Python Setup Script](https://github.com/Eggertron/python-setup). After the script has
installed pyenv you can run the following command to setup your Python version and environment,
```
pyenv install 3.8.5
pyenv virtualenv 3.8.5 webcam-env
pyenv local webcam-env
pip install --upgrade pip
pip install -r requirements.txt
```

#### System Dependencies
You'll need to satisfy some system dependencies for opencv to work
```
sudo apt-get install -y ffmpeg libopenexr-dev
```

### Build OpenCV
Building OpenCV from source can take a lot of time. This will build OpenCV in a Docker
container and leave you with the compiled package. Keep in mind that this script
will pull in Ubuntu lastest and at the time of creating the script python 3.8.5 was
the available package.
```
./build-opencv.sh
```

### Load OpenCV
We need to extract the package into our webcam-env virtual environment.
```
tar -C $(pyenv prefix) -xzvf opencv-bin.tgz
```

### Load Libraries
Since the libraries needed to run OpenCV are in the package we need to have them
exported to be detected by OpenCV
```
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$(pyenv prefix)/lib
```

## Raspberry Pi Webcam Server over VCL HTTP MJPG
Create a script `start_webcam_stream.sh` with the following line
```
 cvlc v412:///dev/video0 --v4l2-width 320 --v4l2-height 240 --v4l2-fps 3 --sout '#transcode{vcodec=mjpg,fps=3}:std{access=http,mux=mpjpeg,dst=<IP>:<PORT>}'
```
make that script executable
```
chmod +x start_webcam_stream.sh
```
Create a Systemd service script to for your new script
```
sudo vi /etc/systemd/system/webcam-server.service
```
add the following to the service script
```
[Unit]
Description=Webcam HTTP Mjpg Server Only
After=network.target

[Service]
PIDFile=/run/webcam-server.pid
ExecStart=/home/pi/start_webcam_stream.sh
ExecStop=/bin/kill -s QUIT $MAINPID
User=pi
Group=pi

[Install]
WantedBy=multi-user.target
```
Make sure to point the `ExecStart=` to the correct path of your script.
Start your script
```
sudo systemctl enable webcam-server && sudo systemctl start webcam-server
```

## Raspberry Pi Webcam Server over VLC RTP
```
cvlc -vv v4l2:///dev/video0:chroma=mp2v --v4l2-width 320 --v4l2-height 240 --sout '#transcode{vcodec=mp2v,acodec=mpga,fps=30}:rtp{mux=ts,sdp=rtsp://:8888/live.sdp}'
```
You can connect to this stream from another computer using VLC. Open VLC and then 
`Open Network Stream...` then enter the URL `rtsp://<<RASPI-IP>>:8888/live.sdp` or you
can launch vlc from the console
```
vlc rtsp://<<RASPI-IP>>:8888/live.sdp
```

## Raspberry Pi Webcam Server (previous)
Use VLC to stream your video [source]("https://chriscarey.com/blog/2017/04/30/achieving-high-frame-rate-with-a-raspberry-pi-camera-system/#:~:text=The%20problem%20with%20using%20motion%20on%20the%20Raspberry%20Pi&text=This%20slow%20frame%20rate%20is,files)%20on%20the%20SD%20card.")
```
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y vlc
```
Run the following to get your server running
```
raspivid -o - -t 0 -w 320 -h 240 -fps 5 -b 250000 | cvlc -vvv stream:///dev/stdin --sout '#rtp{access=udp,sdp=rtsp://:8554/stream}' :demux=h264
```

## Raspberry Pi Webcam Server Alternative
I use raspberry pi's to serve USB cameras in my home network. I use `motion` to
get this setup working since it is relatively simple to setup.

### Install Motion
```
sudo apt-get update && sudo apt-get upgrade -y
sudo install -y motion
```

### Disable motion detection with a mask file
I use a mask to disable the built-in motion detection algorithm. Motion will always
detect motion and save file, unless you explicitly pause or stop it from the UI or API.
I would much rather have detection always disabled to save on the CPU cycles. Here, I
am creating a 320x240 mask.pgm file that will disable detection.
```
./mkpgm 320 240 mask.pgm
```

### Configure Motion
Open up `/etc/motion/motion.conf` and modify the following
- `daemon on`
- `mask_file /home/pi/mask.pgm`
- `stream_quality 100`
- `stream_maxrate 5`
- `stream_localhost off`
- `stream_preview_scale 0`
- `webcontrol_localhost off`

The `mask_file` value will depend on where you save your `mask.pgm` file created by `mkpgm` script.
