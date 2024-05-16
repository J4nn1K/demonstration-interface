# demonstration-interface
```
pip install .
```

When working in ARM-based architectures (Jetson etc.) install HDF5 manually because h5py will try to build from source. Because there's no pre-built package for ARM computers yet.

```
  sudo apt-get install libhdf5-dev
  pip install h5py
```


Install Libcanberra for cv2 visualization