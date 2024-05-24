# demonstration-interface
## Development
Install the package in "editable" mode. This creates a symbolic link from the site-package directory to your development directory, allowing for direct changes.
```
pip install -e .
```


When working in ARM-based architectures (Jetson etc.) install HDF5 manually because h5py will try to build from source. Because there's no pre-built package for ARM computers yet.

```
  sudo apt-get install libhdf5-dev
  pip install h5py
```


Install Libcanberra for cv2 visualization

## Flask Streaming Server
```
export FLASK_APP=servers/camera_feed.py
flask run --host=0.0.0.0
```