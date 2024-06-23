from src.config import DATA_DIR
import h5py
import numpy as np
np.set_printoptions(precision=3, suppress=True)
import matplotlib 
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
import glob
import cv2
from tqdm import tqdm
from src.utils import set_axes_equal
import click


@click.command()
@click.option('-f', '--file_path', required=True, help='Absolute path to the episode file.')
def main(file_path):
    episode_name = os.path.splitext(os.path.basename(file_path))[0]
    output_dir = os.path.dirname(file_path)
    output_file_path = os.path.join(output_dir, f'{episode_name}.mp4')
    f = h5py.File(file_path,'r')

    color_images = np.array(f['color_images'])
    color_images = np.array([cv2.cvtColor(image, cv2.COLOR_BGR2RGB) for image in color_images])

    poses = np.array(f['pose_values'])
    pose_confidences = np.array(f['pose_confidences'])

    translations = np.array([pose[:3, 3] for pose in poses])
    orientations = np.array([pose[:3, :3] for pose in poses])
    
    # Create figure and axis for plotting
    
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    # Initialize video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec for mp4
    frame_height = fig.canvas.get_width_height()[1]
    frame_width = fig.canvas.get_width_height()[0] * 2  # double the width to accommodate both images
    out = cv2.VideoWriter(output_file_path, fourcc, 30.0, (frame_width, frame_height))

    # Generate and save frames
    print("Generating video...")
    for i in tqdm(range(len(translations))):
        color_image = color_images[i]
        frame = create_frame(fig, ax, translations, orientations, color_image, i)
        out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))  # Convert RGB to BGR for OpenCV

    # Release the video writer
    out.release()
    plt.close(fig)

    print(f"Video saved as {output_file_path}")

def create_frame(fig, ax, translations, orientations, color_image, frame_idx):
    ax.cla()  # Clear the previous frame
    ax.set_box_aspect([1.0, 1.0, 1.0])

    # Plot trajectory
    ax.plot(translations[:, 0], translations[:, 1], translations[:, 2], '-', c="lightgrey", label='Trajectory')

    # Plot orientation arrows
    t = translations[frame_idx]
    R = orientations[frame_idx]

    ax.quiver(t[0], t[1], t[2], R[0, 0], R[1, 0], R[2, 0], length=0.04, color='r', arrow_length_ratio=0)
    ax.quiver(t[0], t[1], t[2], R[0, 1], R[1, 1], R[2, 1], length=0.04, color='g', arrow_length_ratio=0)
    ax.quiver(t[0], t[1], t[2], R[0, 2], R[1, 2], R[2, 2], length=0.04, color='b', arrow_length_ratio=0)

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')

    ax.grid(True)
    ax.view_init(elev=-30, azim=-90, roll=0)
    
    set_axes_equal(ax)

    fig.canvas.draw()
    # plt.show()

    # Convert the plot to a numpy array
    trajectory_frame = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8)
    trajectory_frame = trajectory_frame.reshape(fig.canvas.get_width_height()[::-1] + (4,))[:, :, :3]


    # Resize color image to match the height of the trajectory plot
    color_image_resized = cv2.resize(color_image, (trajectory_frame.shape[1], trajectory_frame.shape[0]))

    # Concatenate the two images side by side
    combined_frame = np.concatenate((trajectory_frame, color_image_resized), axis=1)

    return combined_frame

if __name__ == '__main__':
    main()