import pyzed.sl as sl
import numpy as np

DATA_DIR = "/home/jannik/Repos/demonstration-interface/data"

RECORDER = {    
    "frequency": 30, # Hz
    "batch_size": 20,
}

REALSENSE = {
    "color_width": 640,
    "color_height": 480,
    "color_fps": 30,
    "depth_width": 640,
    "depth_height": 480,
    "depth_fps": 30,
}

ZED = {
    "resolution": sl.RESOLUTION.AUTO,
    "fps": 30,
    "coordinate_system": sl.COORDINATE_SYSTEM.IMAGE,
    "units": sl.UNIT.METER,
    "depth_mode": sl.DEPTH_MODE.ULTRA,
}

GRIPPER = {
    "control_frequency": 30 # Hz
}


# EE POSE (relative to ZED Coordinate System "IMAGE")
R_x = np.array(
    [
        [1, 0, 0],
        [0, -np.sqrt(2) / 2, -np.sqrt(2) / 2],
        [0, np.sqrt(2) / 2, -np.sqrt(2) / 2],
    ]
)
R_y = np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]])

rotation = np.dot(R_y, R_x)
translation = np.array([25, 0, -72])

transformation = np.eye(4)
transformation[:3,:3] = rotation
# transformation[:3,3] = translation # not needed yet, requires other init frame for ZED 

EE_TRANSFORMATION = {
    "R_x": R_x,
    "R_y": R_y,
    "from_ZED": transformation
}
