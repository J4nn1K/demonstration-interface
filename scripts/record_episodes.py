from src.components.grip import Grip
from src.components.tracker import Tracker
from src.components.gripper import Gripper
from src.components.camera import Camera
from src.config import REALSENSE, GRIPPER, RECORDER, DATA_DIR
from src.utils import CustomFormatter

import multiprocessing as mp
import time
import sys
import numpy as np
import logging
import h5py
from datetime import datetime

# Logger and console handler
log = logging.getLogger()
log.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(CustomFormatter())
log.addHandler(console_handler)


# Frequencies for process execution loops
logging_dt = 1 / 30
recording_dt = 1 / RECORDER["frequency"]
control_dt = 1 / GRIPPER["control_frequency"]


# Global variables to store and read values using Manager
# TODO RENAME VARIABLES
manager = mp.Manager()
trigger_state = manager.Value("i", 0)
button_state = manager.Value("i", 0)

pose = manager.Array("d", [0.0] * 16)  # 4x4 matrix stored in a flat list
pose_confidence = manager.Value("i", 0)

color_image = mp.Array(
    "B", REALSENSE["color_width"] * REALSENSE["color_height"] * 3
)  # 3 channels (RGB) and 8-bit depth
depth_image = mp.Array(
    "H", REALSENSE["depth_width"] * REALSENSE["depth_height"]
)  # 16-bit depth


def read_grip(trigger_state, button_state):
    grip = Grip()

    while True:
        if grip.get_data():
            _trigger_state = grip.get_trigger_state()
            _button_state = grip.get_button_state()
            trigger_state.value = _trigger_state
            button_state.value = _button_state


def read_tracker(pose, pose_confidence):
    tracker = Tracker()
    tracker.enable_tracking()

    while True:
        if tracker.grab_frame():
            _, _confidence, _pose = tracker.get_ee_pose()
            pose_confidence.value = _confidence
            # collapse 4x4 pose matrix into a flat list
            for i in range(len(_pose.flatten())):
                pose[i] = _pose.flatten()[i]


def read_camera(color_image, depth_image):
    camera = Camera()

    while True:
        camera.wait_for_frames()
        color = camera.get_image()
        depth = camera.get_depth()

        if (color is None) or (depth is None):
            continue

        # Create a np array view of the shared memory
        np_color = np.frombuffer(color_image.get_obj(), dtype=np.uint8).reshape(
            480, 640, 3
        )
        # Copy the image data into the shared memory array
        np.copyto(np_color, color)

        np_depth = np.frombuffer(depth_image.get_obj(), dtype=np.uint16).reshape(
            480, 640
        )
        np.copyto(np_depth, depth)


def send_to_gripper(trigger_state, dt):
    gripper = Gripper()
    gripper.activate()

    while True:
        if trigger_state.value:
            gripper.go_to(trigger_state.value)
        time.sleep(dt)  # TODO: Implement a better control loop


def log_data(
    trigger_state, button_state, pose, pose_confidence, color_image, depth_image, dt
):
    while True:
        try:
            pose_matrix = np.array(pose).reshape(4, 4)

            color_image_np = np.frombuffer(
                color_image.get_obj(), dtype=np.uint8
            ).reshape(480, 640, 3)

            sys.stdout.write("\r \r")
            sys.stdout.write(
                f"First pixel: {color_image_np[0,0]} | Trigger: {trigger_state.value:2.0f} | Button: {button_state.value:1.0f} | X: {pose_matrix[0,3]:5.1f}  Y: {pose_matrix[1,3]:5.1f} Z: {pose_matrix[2,3]:5.1f} | Confidence: {pose_confidence.value:2.0f}"
            )
            sys.stdout.flush()
        except Exception as e:
            log.info("Waiting for data:" + str(e))

        time.sleep(dt)


def record_data(
    trigger_state, button_state, pose, pose_confidence, color_image, depth_image, dt
):
    recording = False
    prev_button_state = 0
    
    timestamps = []
    images = []
    poses = []

    log.warning("### Press the button to start recording ###")

    try:
        while True:
            start_time = time.time()
            current_button_state = button_state.value

            if prev_button_state == 0 and current_button_state == 1:
                recording = not recording  # Toggle on button press

                if recording:
                    log.info("Started recording")
                else:
                    log.info("Stopped recording")

                    session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    with h5py.File(f"{DATA_DIR}/recording_{session_timestamp}.h5", "w") as f:
                        f.create_dataset("timestamps", data=np.array(timestamps))
                        f.create_dataset("images", data=np.array(images))
                        f.create_dataset("poses", data=np.array(poses))
                    log.warning(f"Saved recording_{session_timestamp}.h5")
                    
                    timestamps.clear()
                    images.clear()
                    poses.clear()

            prev_button_state = current_button_state

            if recording:                
                timestamp = round(time.time() * 1000)
                log.info(f"Recording frame {timestamp}")
                
                latest_trigger_state = trigger_state.value
                latest_pose_matrix = np.array(pose).reshape((4, 4))
                latest_pose_confidence = pose_confidence.value
                latest_color_image = np.copy(np.frombuffer(
                    color_image.get_obj(), dtype=np.uint8
                ).reshape(480, 640, 3))
                
                timestamps.append(timestamp)
                images.append(latest_color_image)
                poses.append(latest_pose_matrix)


            elapsed_time = time.time() - start_time
            sleep_time = dt - elapsed_time
            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                log.warning(f"Recording loop took longer than {dt:.2} seconds: {elapsed_time:.2f}")

    except KeyboardInterrupt:
        print("Aborting recording...")


def main():
    try:
        grip_process = mp.Process(target=read_grip, args=(trigger_state, button_state))
        grip_process.start()

        tracker_process = mp.Process(target=read_tracker, args=(pose, pose_confidence))
        tracker_process.start()

        camera_process = mp.Process(target=read_camera, args=(color_image, depth_image))
        camera_process.start()

        gripper_process = mp.Process(
            target=send_to_gripper, args=(trigger_state, control_dt)
        )
        gripper_process.start()

        time.sleep(8)

        # logger_process = mp.Process(
        #     target=log_data,
        #     args=(
        #         trigger_state,
        #         button_state,
        #         pose,
        #         pose_confidence,
        #         color_image,
        #         depth_image,
        #         logging_dt,
        #     ),
        # )
        # logger_process.start()

        recorder = mp.Process(
            target=record_data,
            args=(
                trigger_state,
                button_state,
                pose,
                pose_confidence,
                color_image,
                depth_image,
                recording_dt,
            ),
        )
        recorder.start()

        grip_process.join()
        tracker_process.join()
        camera_process.join()
        gripper_process.join()
        # logger_process.join()
        recorder.join()

    except KeyboardInterrupt:
        print("\n Closing")


if __name__ == "__main__":
    main()
