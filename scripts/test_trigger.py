from src.components.trigger import Trigger
import logging
import sys

logging.basicConfig(level=logging.INFO)

def main():
    trigger = Trigger()
    trigger.calibrate()

    try:
        while True:
            state = trigger.get_trigger_state()
            if state: 
                sys.stdout.write('\r')
                sys.stdout.write("[%-100s] %d%%" % ('='*int(100*state), int(100*state)))
                sys.stdout.flush()
                # print(f'{state}')
    except KeyboardInterrupt:
        print('\n')
        trigger.close_serial()


if __name__ == "__main__":
    main()