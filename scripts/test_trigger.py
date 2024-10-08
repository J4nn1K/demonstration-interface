from src.components.grip import Grip
import logging
import sys

logging.basicConfig(level=logging.INFO)

def main():
    grip = Grip()

    try:
        while True:
            grip.get_data()
            trigger_state = grip.get_trigger_state()
            
            if trigger_state: 
                sys.stdout.write('\r')
                sys.stdout.write("[%-100s] %d%%" % ('='*trigger_state, trigger_state))
                sys.stdout.flush()

    except KeyboardInterrupt:
        print('\n')
        grip.close_serial()


if __name__ == "__main__":
    main()