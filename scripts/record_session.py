from src.components.grip import Grip
from src.components.tracker import Tracker
from src.components.gripper import Gripper
from src.components.camera import Camera
from src.config import REALSENSE, GRIPPER, RECORDER, DATA_DIR, ZED
from src.utils import CustomFormatter

import pyzed.sl as sl
import multiprocessing as mp
import time
import sys
import numpy as np
import logging
import h5py
import os
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
manager = mp.Manager()

trigger_timestamp = manager.Value("Q", 0)  # uint64
trigger_state = manager.Value("B", 0)  # uint8
button_state = manager.Value("B", 0)  # uint8

gripper_timestamp = manager.Value("Q", 0)  # uint64
gripper_state = manager.Value("B", 0)  # uint8

pose_timestamp = manager.Value("Q", 0)  # uint64
pose = manager.Array("d", [0.0] * 16)  # 4x4 matrix stored in a flat list
pose_confidence = manager.Value("B", 0)  # uint8

if RECORDER["tracking_image"]:
    if ZED["resolution"] == sl.RESOLUTION.HD720:
        tracker_image = mp.Array("B", 1280 * 720 * 4)
else: 
    tracker_image = None

image_timestamp = manager.Value("Q", 0)  # uint64
color_image = mp.Array(  # uint8 
    "B", REALSENSE["color_width"] * REALSENSE["color_height"] * 3
)  # 3 channels (RGB) and 8-bit depth
depth_image = mp.Array(  # uint16
    "H", REALSENSE["depth_width"] * REALSENSE["depth_height"]
)  # 16-bit depth


def read_grip(trigger_timestamp, trigger_state, button_state):
    grip = Grip()

    while True:
        _timestamp = grip.get_data()
        if _timestamp:
            trigger_timestamp.value = _timestamp
            _trigger_state = grip.get_trigger_state()
            _button_state = grip.get_button_state()
            trigger_state.value = _trigger_state
            button_state.value = _button_state


def read_tracker(pose_timestamp, pose_confidence, pose, tracker_image):
    tracker = Tracker()
    tracker.enable_tracking()
    dt = 1/ZED["fps"]
    
    while True:
        start_time = time.time()
        if tracker.grab_frame():
            # _pose_timestamp, _confidence, _pose = tracker.get_pose_in_ee_frame()
            _pose_timestamp, _confidence, _pose = tracker.get_ee_pose()

            pose_timestamp.value = _pose_timestamp
            pose_confidence.value = _confidence
            # collapse 4x4 pose matrix into a flat list
            for i in range(len(_pose.flatten())):
                pose[i] = _pose.flatten()[i]

            if RECORDER["tracking_image"]:
                _, image = tracker.get_image()
                np_tracker = np.frombuffer(tracker_image.get_obj(), dtype=np.uint8).reshape(
                    720,1280,4
                )
                np.copyto(np_tracker, image)
        
        elapsed_time = time.time() - start_time
        sleep_time = dt - elapsed_time
        if sleep_time > 0:
            time.sleep(sleep_time)
        else:
            log.debug(
                f"Tracker loop took longer than {dt:.4} seconds: {elapsed_time:.4f}"
            )


def read_camera(image_timestamp, color_image, depth_image):
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

        image_timestamp.value = time.time_ns()


def send_to_gripper(trigger_state, gripper_timestamp, gripper_state, dt):
    gripper = Gripper()
    gripper.activate()

    while True:
        start_time = time.time()
        # if trigger_state.value:
        try:
            gripper_state.value = gripper.get_state()
            # print(gripper.get_state())
            gripper_timestamp.value = time.time_ns()
        except:
            log.error("Failed to get gripper position")
            continue
        gripper.go_to(trigger_state.value)

        elapsed_time = time.time() - start_time
        sleep_time = dt - elapsed_time
        if sleep_time > 0:
            time.sleep(sleep_time)
        else:
            log.debug(
                f"Gripper control loop took longer than {dt:.4} seconds: {elapsed_time:.4f}"
            )


def log_data(pose, pose_confidence, color_image, trigger_state, button_state, dt):
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
    trigger_timestamp,
    trigger_state,
    button_state,
    gripper_timestamp,
    gripper_state,
    image_timestamp,
    color_image,
    depth_image,
    pose_timestamp,
    pose,
    pose_confidence,
    tracker_image,
    dt,
):

    recording = False
    prev_button_state = 0

    session_dir = os.path.join(
        DATA_DIR, "session_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    os.makedirs(session_dir, exist_ok=True)

    log.warning("### Press the button to start recording ###")

    timestamps = []
    trigger_timestamps = []
    trigger_states = []
    gripper_timestamps = []
    gripper_states = []
    image_timestamps = []
    color_images = []
    depth_images = []
    pose_timestamps = []
    pose_values = []
    pose_confidences = []
    tracker_images = []

    try:
        while True:
            start_time = time.time()
            current_button_state = button_state.value
            
            def get_color(value):
                if value >= 80:
                    return '\033[92m'  # Green
                elif value >= 60:
                    return '\033[93m'  # Yellow
                else:
                    return '\033[91m'  # Red
                
            latest_pose_confidence = pose_confidence.value

            color = get_color(latest_pose_confidence)
            
            sys.stdout.write('\r')
            sys.stdout.write(f"{color}##### Pose Confidence: {latest_pose_confidence:2.0f} ######\033[0m")
            sys.stdout.flush()
            
            if prev_button_state == 0 and current_button_state == 1:
                recording = not recording  # Toggle on button press

                if recording:
                    log.info("Started recording")
                    initial_pose = np.array(pose).reshape((4, 4))
                    initial_pose_inv = np.linalg.inv(initial_pose)

                else:
                    log.info("Stopped recording")

                    episode_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    with h5py.File(
                        f"{session_dir}/episode_{episode_timestamp}.h5", "w"
                    ) as f:

                        f.create_dataset(
                            "timestamps", data=np.array(timestamps), dtype="uint64"
                        )

                        f.create_dataset(
                            "trigger_timestamps",
                            data=np.array(trigger_timestamps),
                            dtype="uint64",
                        )
                        f.create_dataset(
                            "trigger_states",
                            data=np.array(trigger_states),
                            dtype="uint8",
                        )

                        f.create_dataset(
                            "gripper_timestamps",
                            data=np.array(gripper_timestamps),
                            dtype="uint64",
                        )
                        f.create_dataset(
                            "gripper_states",
                            data=np.array(gripper_states),
                            dtype="uint8",
                        )

                        f.create_dataset(
                            "image_timestamps",
                            data=np.array(image_timestamps),
                            dtype="uint64",
                        )
                        f.create_dataset(
                            "color_images", data=np.array(color_images), dtype="uint8"
                        )
                        f.create_dataset(
                            "depth_images", data=np.array(depth_images), dtype="uint16"
                        )

                        f.create_dataset(
                            "pose_timestamps",
                            data=np.array(pose_timestamps),
                            dtype="uint64",
                        )
                        f.create_dataset(
                            "pose_values", data=np.array(pose_values), dtype="float64"
                        )
                        f.create_dataset(
                            "pose_confidences",
                            data=np.array(pose_confidences),
                            dtype="uint8",
                        )
                        
                        if RECORDER["tracking_image"]:
                            f.create_dataset(
                                "tracker_images",
                                data=np.array(tracker_images),
                                dtype="uint8",
                            )

                    log.warning(f"Saved recording_{episode_timestamp}.h5")

                    timestamps.clear()
                    trigger_timestamps.clear()
                    trigger_states.clear()
                    gripper_timestamps.clear()
                    gripper_states.clear()
                    image_timestamps.clear()
                    color_images.clear()
                    depth_images.clear()
                    pose_timestamps.clear()
                    pose_values.clear()
                    pose_confidences.clear()
                    tracker_images.clear()

                    log.warning("### Press the button to start recording ###")

            prev_button_state = current_button_state

            if recording:
                # Retrieve values
                timestamp = time.time_ns()  # round(time.time() * 1000)
                # log.info(f"Recording frame {timestamp}")

                latest_trigger_timestamp = trigger_timestamp.value
                latest_trigger_state = trigger_state.value

                latest_gripper_timestamp = gripper_timestamp.value
                latest_gripper_state = gripper_state.value

                latest_pose_timestep = pose_timestamp.value
                latest_pose_matrix = np.array(pose).reshape((4, 4))
                # Poses recorded are relative to the initial pose
                if initial_pose is not None:
                    relative_pose_matrix = initial_pose_inv @ latest_pose_matrix



                latest_image_timestamp = image_timestamp.value
                latest_color_image = np.copy(
                    np.frombuffer(color_image.get_obj(), dtype=np.uint8).reshape(
                        480, 640, 3
                    )
                )
                latest_depth_image = np.copy(
                    np.frombuffer(depth_image.get_obj(), dtype=np.uint16).reshape(
                        480, 640
                    )
                )

                if RECORDER["tracking_image"]:
                    latest_tracker_image = np.copy(
                        np.frombuffer(tracker_image.get_obj(), dtype=np.uint8).reshape(
                            720,1280,4
                        )
                    )
                    tracker_images.append(latest_tracker_image)
                    

                # Append values
                timestamps.append(timestamp)

                trigger_timestamps.append(latest_trigger_timestamp)
                trigger_states.append(latest_trigger_state)

                gripper_timestamps.append(latest_gripper_timestamp)
                gripper_states.append(latest_gripper_state)

                image_timestamps.append(latest_image_timestamp)
                color_images.append(latest_color_image)
                depth_images.append(latest_depth_image)

                pose_timestamps.append(latest_pose_timestep)
                pose_values.append(relative_pose_matrix)
                # pose_values.append(latest_pose_matrix)
                pose_confidences.append(latest_pose_confidence)


            elapsed_time = time.time() - start_time
            sleep_time = dt - elapsed_time
            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                log.debug(
                    f"Recording loop took longer than {dt:.2} seconds: {elapsed_time:.2f}"
                )

    except KeyboardInterrupt:
        print("Aborting recording...")


def main():
    try:
        grip_process = mp.Process(
            target=read_grip, args=(trigger_timestamp, trigger_state, button_state)
        )
        grip_process.start()

        tracker_process = mp.Process(
            target=read_tracker,
            args=(pose_timestamp, pose_confidence, pose, tracker_image),
        )
        tracker_process.start()

        camera_process = mp.Process(
            target=read_camera, args=(image_timestamp, color_image, depth_image)
        )
        camera_process.start()

        gripper_process = mp.Process(
            target=send_to_gripper,
            args=(trigger_state, gripper_timestamp, gripper_state, control_dt),
        )
        gripper_process.start()

        time.sleep(8)

        # logger_process = mp.Process(
        #     target=log_data,
        #     args=(pose, pose_confidence, color_image, trigger_state, button_state, logging_dt),
        # )
        # logger_process.start()

        recorder = mp.Process(
            target=record_data,
            args=(
                trigger_timestamp,
                trigger_state,
                button_state,
                gripper_timestamp,
                gripper_state,
                image_timestamp,
                color_image,
                depth_image,
                pose_timestamp,
                pose,
                pose_confidence,
                tracker_image,
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
