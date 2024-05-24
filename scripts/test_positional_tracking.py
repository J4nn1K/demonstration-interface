from src.components.camera import Camera
import logging
import sys

logging.basicConfig(level=logging.INFO)

def main():
  try:
    cam = Camera()
    print('\n')
    
    while True:
      cam.grab_frame()
      timestamp, confidence, pose = cam.get_pose()
      pos = pose[:3,3]
    
      sys.stdout.write('\r')
      sys.stdout.write(f'x:{pos[0]:.4f} y:{pos[1]:.4f} z:{pos[2]:.4f}')
      sys.stdout.flush()
  
  except KeyboardInterrupt:
    cam.close()
  
if __name__ == "__main__":
    main()