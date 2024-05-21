from src.components.gripper import Gripper
from src.components.trigger import Trigger
import threading

import time
import sys

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.info("INFO")


lock = threading.Lock()
state = None


def read_trigger(trigger):
    global state

    while True:
        _state = trigger.get_trigger_state()
        if _state:
            # latest_state = int(100*_state)
            # sys.stdout.write('\r')
            # sys.stdout.write("[%-100s] %d%%" % ('='*latest_state, latest_state))
            # sys.stdout.flush()
            with lock:
                state = _state


def send_to_gripper(gripper):
    global state
    while True:
        with lock:
            if state:
                # latest_state = int(100*state)
                # sys.stdout.write('\r')
                # sys.stdout.write("[%-100s] %d%%" % ('='*latest_state, latest_state))
                # sys.stdout.flush()
                gripper.go_to(state)

        time.sleep(0.01)


def main():
    trigger = Trigger(alpha=0.1)
    trigger.calibrate()

    gripper = Gripper()
    gripper.activate()

    try:
        logger.info('Starting thread for trigger')
        trigger_thread = threading.Thread(target=read_trigger, args=(trigger,), daemon=True)
        trigger_thread.start()

        logger.info('Starting thread for gripper')
        gripper_thread = threading.Thread(target=send_to_gripper, args=(gripper,), daemon=True)
        gripper_thread.start()

        trigger_thread.join()
        gripper_thread.join()
    
    except KeyboardInterrupt:
        print('\n')
        trigger.close_serial()
        gripper.gripper.shutdown()
    
#    finally:
#        trigger.close_serial()


if __name__ == '__main__':
    main()
