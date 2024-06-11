from src.components.grip import Grip
from src.components.tracker import Tracker
from src.components.gripper import Gripper
from src.components.camera import Camera

import multiprocessing as mp
import time
import sys
import numpy as np

import logging

log = logging.getLogger()
log.setLevel(logging.INFO)
logging.info("INFO")

# Frequencies for process execution loops
logging_dt = 1 / 30
control_dt = 1 / 30

# Global variables to store and read values using Manager
manager = mp.Manager()
trigger_state = manager.Value("i", 0)
button_state = manager.Value("i", 0)

pose = manager.Array("d", [0.0] * 16)  # 4x4 matrix stored in a flat list
pose_confidence = manager.Value("i", 0)

color_image = manager.Value("i", 0)  # This would be updated differently in actual usage
depth_image = manager.Value("i", 0)  # This would be updated differently in actual usage


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

        # Simplified handling; actual implementation would differ
        color_image.value = color
        depth_image.value = depth


def send_to_gripper(trigger_state, dt):
    gripper = Gripper()
    gripper.activate()
    
    while True:
        if trigger_state.value:
            gripper.go_to(trigger_state.value)
        time.sleep(dt)


def log_data(
    trigger_state, button_state, pose, pose_confidence, dt
):
    time.sleep(8)
    log.info("Waited 8 seconds - Starting logging process")
    
    while True:
        try:
            pose_matrix = np.array(pose).reshape((4, 4))
            
            sys.stdout.write("\r \r")
            sys.stdout.write(
                f"Trigger: {trigger_state.value:2.0f} | Button: {button_state.value:1.0f} | X: {pose_matrix[0,3]:5.1f}  Y: {pose_matrix[1,3]:5.1f} Z: {pose_matrix[2,3]:5.1f} | Confidence: {pose_confidence.value:2.0f}"
            )
            sys.stdout.flush()
        except Exception as e:
            log.info("Waiting for data:" + str(e))

        time.sleep(dt)


def main():
    try:        
        log.info("Starting process for grip")
        grip_process = mp.Process(
            target=read_grip, args=(trigger_state, button_state)
        )
        grip_process.start()

        log.info("Starting process for tracker")
        tracker_process = mp.Process(
            target=read_tracker, args=(pose, pose_confidence)
        )
        tracker_process.start()

        # log.info("Starting process for camera")
        # camera_process = mp.Process(
        #     target=read_camera, args=(camera, color_image, depth_image)
        # )
        # camera_process.start()

        # log.info('Starting process for gripper')
        # gripper_process = mp.Process(target=send_to_gripper, args=(gripper, trigger_state, control_dt))
        # gripper_process.start()

        log.info("Starting process for logging")
        logger_process = mp.Process(
            target=log_data,
            args=(
                trigger_state,
                button_state,
                pose,
                pose_confidence,
                logging_dt,
            ),
        )
        logger_process.start()

        grip_process.join()
        tracker_process.join()
        # camera_process.join()
        # gripper_process.join()
        logger_process.join()

    except KeyboardInterrupt:
        print("\n Closing")


if __name__ == "__main__":
    main()
