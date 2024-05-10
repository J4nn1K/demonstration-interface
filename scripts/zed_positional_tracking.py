import pyzed.sl as sl
import click
import numpy as np
import h5py
from tqdm import tqdm
import cv2


@click.command()
@click.option('--fps', default=60, type=int)
@click.option('--frames', default=300, type=int)
#@click.option('--frames', prompt='Frames to record', type=int)
@click.option('--filename', default='recording_without_cv', type=str)
#@click.option('--filename', prompt='Filename (without .hdf5)', type=str)


def main(fps, frames, filename):
    
    print('Setting up camera...')
    # Create a Camera object
    zed = sl.Camera()

    # Create a InitParameters object and set configuration parameters
    init_params = sl.InitParameters()
    init_params.camera_resolution = sl.RESOLUTION.AUTO # Use HD720 or HD1200 video mode (default fps: 60)
    init_params.camera_fps = fps
    init_params.coordinate_system = sl.COORDINATE_SYSTEM.RIGHT_HANDED_Y_UP # Use a right-handed Y-up coordinate system
    init_params.coordinate_units = sl.UNIT.METER  # Set units in meters

    # Open the camera
    err = zed.open(init_params)
    if err != sl.ERROR_CODE.SUCCESS:
        print("Camera Open : "+repr(err)+". Exit program.")
        exit()


    # Enable positional tracking with default parameters
    py_transform = sl.Transform()  # First create a Transform object for TrackingParameters object
    tracking_parameters = sl.PositionalTrackingParameters(_init_pos=py_transform)
    err = zed.enable_positional_tracking(tracking_parameters)
    if err != sl.ERROR_CODE.SUCCESS:
        print("Enable positional tracking : "+repr(err)+". Exit program.")
        zed.close()
        exit()

    # Record images and track camera pose
    #i = 0
    image = sl.Mat()
    pose = sl.Pose()

    images = []
    image_timesteps = []
    poses = []
    pose_timesteps = []

    runtime_parameters = sl.RuntimeParameters()

    #win_name = "Camera Control"
    #cv2.startWindowThread()
    #cv2.namedWindow(win_name)

    print(f'Recording {frames} frames...')
    for _ in tqdm(range(frames)):
    #while i < frames:
        if zed.grab(runtime_parameters) == sl.ERROR_CODE.SUCCESS:
            
            # A new image is available if grab() returns SUCCESS
            zed.retrieve_image(image, sl.VIEW.LEFT)
            image_timesteps.append(image.timestamp.get_milliseconds())
            
            #cv2.imshow(win_name, image.get_data()) #Display image
            #image_rgb = cv2.cvtColor(image.get_data(), cv2.COLOR_BGR2RGB)
            #images.append(image_rgb)
            images.append(image.get_data())

        
            # Get the pose of the left eye of the camera with reference to the world frame
            zed.get_position(pose, sl.REFERENCE_FRAME.WORLD)
            py_translation = sl.Translation()
            py_orientation = sl.Orientation()

            pose_timesteps.append(pose.timestamp.get_milliseconds())
            poses.append(np.concatenate((
                pose.get_translation(py_translation).get(),
                pose.get_orientation(py_orientation).get()
            )))
            
    # Close the camera
    zed.close()

    print('Saving data...')
    path = filename + '.hdf5'
    f = h5py.File(path, 'w')
    
    dset_image_timesteps = f.create_dataset('image_timesteps', data=np.array(image_timesteps))
    dset_images = f.create_dataset('images', data=np.array(images))
    dset_pose_timesteps = f.create_dataset('pose_timesteps', data=np.array(pose_timesteps))
    dset_poses = f.create_dataset('poses', data=np.array(poses))
    
    f.close()
    print(f'Saved data to {path}')

if __name__ == "__main__":
    main()