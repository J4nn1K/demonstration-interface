from src.components.grip import Grip
import logging
import sys

logging.basicConfig(level=logging.INFO)

def main():
    grip = Grip()

    try:
        while True:
            grip.get_data()
            button_state = grip.get_button_state()
            if not button_state == None: 
                sys.stdout.write('\r')
                sys.stdout.write(f"{button_state}")
                sys.stdout.flush()
    
    except KeyboardInterrupt:
        print('\n')
        grip.close_serial()


if __name__ == "__main__":
    main()