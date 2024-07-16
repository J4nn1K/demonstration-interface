# Demonstration Interface
![](https://github.com/J4nn1K/demonstration-interface/blob/main/media/graphic.png)

## Basic Setup
Configuration can be found in `src/config.py`

## Data Collection
Record a session using `record_session.py`:
```
$ python scripts/record_session.py
```
This will save the recordings in the following format:
```
data/
└─ session_YYYYMMDD_HHMMSS/
   └─ episode_YYYYMMDD_HHMMSS.h5
```

## Development
Install the package in "editable" mode. This creates a symbolic link from the site-package directory to your development directory, allowing for direct changes.
```
$ pip install -e .
```

When working in ARM-based architectures (Jetson etc.) install HDF5 manually because h5py will try to build from source. Because there's no pre-built package for ARM computers yet.

```
$ sudo apt-get install libhdf5-dev
$ pip install h5py
```

Install Libcanberra for cv2 visualization

### RealSense SDK on Jetson
[Convenience script from JetsonHacks](https://jetsonhacks.com/2019/12/22/install-realsense-camera-in-5-minutes-jetson-nano/)

## Camera Web Viewer
Running the server and making it publicly available on your network:
```
$ export FLASK_APP=web_viewer/app.py
$ flask run --host=0.0.0.0 
```