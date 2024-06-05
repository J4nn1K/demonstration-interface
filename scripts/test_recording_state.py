from src.components.grip import Grip
import logging
import sys

logging.basicConfig(level=logging.INFO)

def main():
    grip = Grip()
    is_recording = False

    prev_button_state = 0
    
    try:
      while True:
        grip.get_data()
        button_state = grip.get_button_state()
        if not button_state == None: 
          
          # Transition on button press
          if prev_button_state == 0 and button_state == 1:
            is_recording = not is_recording

          prev_button_state = button_state
          
          sys.stdout.write('\r')
          sys.stdout.write(f"Recording: {is_recording}")
          sys.stdout.flush()
    
    except KeyboardInterrupt:
      print('\n')
      grip.close_serial()


if __name__ == "__main__":
    main()