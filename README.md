# simple-webcam-monitoring
Very quick and dirty IP Webcam monitoring to reuse old android phones.

## Setup
You'll need to have python installed in your system. To do that you can run
this script, [Python Setup Script](https://github.com/Eggertron/python-setup]). After the script has
installed pyenv you can run the following command to setup your Python version and environment,
```
pyenv install 3.8.5
pyenv virtualenv 3.8.5 webcam-env
pyenv local webcam-env
pip install --upgrade pip
pip install -r requirements.txt
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
