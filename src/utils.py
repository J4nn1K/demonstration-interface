import logging
import numpy as np
import pandas as pd


class CustomFormatter(logging.Formatter):
    """
    https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
    """

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    # format = (
    #     "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    # )
    format = (
        "%(levelname)s:%(name)s  %(message)s"
    )

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def compute_rotation_matrix(A, B):
    H = A.T @ B
    U, S, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T
    if np.linalg.det(R) < 0:
        Vt[-1, :] *= -1
        R = Vt.T @ U.T
    return R

def poses_from_vicon(file):

    data = pd.read_csv(file, skiprows=5, header=0)
    
    # Rename columns for better understanding
    columns = [
        'Frame', 'X1', 'Y1', 'Z1', 'X2', 'Y2', 'Z2',
        'X3', 'Y3', 'Z3', 'X4', 'Y4', 'Z4', 'X5', 'Y5', 'Z5',
        'Mag_X1', 'Mag_Y1', 'Mag_Z1', 'Mag_X2', 'Mag_Y2', 'Mag_Z2'
    ]
    data.columns = columns

    # Extract marker coordinates
    marker_columns = ['X1', 'Y1', 'Z1', 'X2', 'Y2', 'Z2', 'X3', 'Y3', 'Z3', 'X4', 'Y4', 'Z4', 'X5', 'Y5', 'Z5']
    markers = data[marker_columns].values
    markers = markers.reshape(-1, 5, 3)

    # Calculate the centroid (center of the rigid body)
    centroid = np.mean(markers, axis=1)

    # Define a reference frame using the initial positions of the markers
    reference_markers = markers[0]

    # Compute the rotation matrix for each frame
    rotation_matrices = []
    for i in range(markers.shape[0]):
        R_i = compute_rotation_matrix(reference_markers, markers[i])
        rotation_matrices.append(R_i)

    rotation_matrices = np.array(rotation_matrices)
    
    poses = np.zeros((len(centroid), 4, 4))
    for i in range(len(centroid)):
        poses[i] = np.eye(4)
        poses[i, :3, :3] = rotation_matrices[i]
        poses[i, :3, 3] = centroid[i]/1000 # to meter
        
        
    return poses


def plot_pose(ax, translation, rotation):
    ax.plot(translation[0], translation[1], translation[2], '-', c="lightgrey", label='Trajectory')
    t = translation
    R = rotation
    
    ax.quiver(t[0], t[1], t[2], R[0, 0], R[1, 0], R[2, 0], length=0.04, color='r', arrow_length_ratio=0)
    ax.quiver(t[0], t[1], t[2], R[0, 1], R[1, 1], R[2, 1], length=0.04, color='g', arrow_length_ratio=0)
    ax.quiver(t[0], t[1], t[2], R[0, 2], R[1, 2], R[2, 2], length=0.04, color='b', arrow_length_ratio=0)


def set_axes_equal(ax):
    """
    Make axes of 3D plot have equal scale so that spheres appear as spheres,
    cubes as cubes, etc.

    Input
      ax: a matplotlib axis, e.g., as output from plt.gca().
    """

    x_limits = ax.get_xlim3d()
    y_limits = ax.get_ylim3d()
    z_limits = ax.get_zlim3d()

    x_range = abs(x_limits[1] - x_limits[0])
    x_middle = np.mean(x_limits)
    y_range = abs(y_limits[1] - y_limits[0])
    y_middle = np.mean(y_limits)
    z_range = abs(z_limits[1] - z_limits[0])
    z_middle = np.mean(z_limits)

    # The plot bounding box is a sphere in the sense of the infinity
    # norm, hence I call half the max range the plot radius.
    plot_radius = 0.5*max([x_range, y_range, z_range])

    ax.set_xlim3d([x_middle - plot_radius, x_middle + plot_radius])
    ax.set_ylim3d([y_middle - plot_radius, y_middle + plot_radius])
    ax.set_zlim3d([z_middle - plot_radius, z_middle + plot_radius])


