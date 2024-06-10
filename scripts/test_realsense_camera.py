from src.components.camera import Camera
import logging
import sys

logging.basicConfig(level=logging.INFO)

def main():
    try:
      cam = Camera()
  
      while True: 
        cam.wait_for_frames()
        image = cam.get_image()      
        
        if image is None: continue
        
        print(image)
        

    except KeyboardInterrupt:
      print('\n')


if __name__ == "__main__":
    main()