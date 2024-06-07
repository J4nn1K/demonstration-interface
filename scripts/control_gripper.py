from src.components.gripper import Gripper
from src.components.grip import Grip
import threading

import time
import sys

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.info("INFO")

control_dt = 0.02


lock = threading.Lock()
trigger_state = None
button_state = None


def read_grip(grip):
    global trigger_state
    global button_state

    while True:
        if grip.get_data():
            with lock:
                trigger_state = grip.get_trigger_state()
                button_state = grip.get_button_state()


def send_to_gripper(gripper, dt):
    global trigger_state
    while True:
        with lock:
            if trigger_state:
                gripper.go_to(trigger_state)

        time.sleep(dt)


def main():
    grip = Grip()

    gripper = Gripper()
    gripper.activate()

    try:
        logger.info('Starting thread for grip')
        grip_thread = threading.Thread(target=read_grip, args=(grip,), daemon=True)
        grip_thread.start()

        logger.info('Starting thread for gripper')
        gripper_thread = threading.Thread(target=send_to_gripper, args=(gripper, control_dt), daemon=True)
        gripper_thread.start()

        grip_thread.join()
        gripper_thread.join()
    
    except KeyboardInterrupt:
        print('\n')
        grip.close_serial()
        gripper.gripper.shutdown()

if __name__ == '__main__':
    main()
