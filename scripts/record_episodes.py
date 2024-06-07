from src.components.grip import Grip
from src.components.tracker import Tracker
from src.components.gripper import Gripper
import threading
import time
import sys

import logging
log = logging.getLogger()
log.setLevel(logging.INFO)
logging.info("INFO")

# Frequencies for thread execution loops
logging_dt = 0.02
control_dt = 0.02

# Global variables to store and read values
lock = threading.Lock()
trigger_state = None
button_state = None
pose = None
pose_confidence = None


def read_grip(grip):
    global trigger_state
    global button_state

    while True:
        if grip.get_data():
            with lock:
                trigger_state = grip.get_trigger_state()
                button_state = grip.get_button_state()
                

def read_tracker(tracker, dt=0.1):
    global pose
    global pose_confidence
    
    while True:
        if tracker.grab_frame():
            _, _confidence, _pose = tracker.get_pose()
            with lock:
                pose = _pose
                pose_confidence = _confidence
        
        time.sleep(dt) # otherwise this threads locks the global variables


def send_to_gripper(gripper, dt):
    global trigger_state
    while True: 
      with lock:
        if trigger_state:
          gripper.go_to(trigger_state)
      
      time.sleep(dt)


def log_data(dt):
    global trigger_state
    global button_state
    global pose
    global pose_confidence
    
    while True:
        with lock:
            current_trigger_state = trigger_state
            current_button_state = button_state
        try:
            sys.stdout.write('\r \r')
            sys.stdout.write(f"Trigger: {current_trigger_state:3.0f} | Button: {current_button_state:1.0f} | X: {pose[0,3]:5.1f}  Y: {pose[1,3]:5.1f} Z: {pose[2,3]:5.1f}")
            sys.stdout.flush()
        except Exception:
            log.info("Waiting for data")
        
        time.sleep(dt)
          

def main():
  grip = Grip()
  tracker = Tracker()
  tracker.enable_tracking()
  
  gripper = Gripper()
  gripper.activate()
  
  try:
        log.info('Starting thread for grip')
        grip_thread = threading.Thread(target=read_grip, args=(grip,), daemon=True)
        grip_thread.start()

        log.info('Starting thread for tracker')
        tracker_thread = threading.Thread(target=read_tracker, args=(tracker,), daemon=True)
        tracker_thread.start()
        
        log.info('Starting thread for gripper')
        gripper_thread = threading.Thread(target=send_to_gripper, args=(gripper, control_dt), daemon=True)
        gripper_thread.start()
        
        log.info('Starting thread for logging')
        logger_thread = threading.Thread(target=log_data, args=(logging_dt,), daemon=True)
        logger_thread.start()

        grip_thread.join()
        tracker_thread.join()
        gripper_thread.join()
        logger_thread.join()
    
  except KeyboardInterrupt:
        # tracker.close()
        print('\n')
        grip.close_serial()
        gripper.gripper.shutdown()


if __name__ == '__main__':
    main()
