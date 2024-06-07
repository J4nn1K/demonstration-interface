from src.components.tracker import Tracker
import logging
import sys
import numpy as np
# from scipy.spatial.transform import Rotation   

logging.basicConfig(level=logging.INFO)

def main():
  try:
    cam = Tracker()
    cam.enable_tracking()
    print('\n')
    
    # 135 deg around x-axis
    R_x = np.array([
      [1, 0, 0],
      [0, -np.sqrt(2)/2, -np.sqrt(2)/2],
      [0, np.sqrt(2)/2, -np.sqrt(2)/2]
    ])
    
    # -90 deg around y-axis
    R_y = np.array([
      [0, 0, -1],
      [0, 1, 0],
      [1, 0, 0]
    ])
    
    # translation to EE-frame
    t = np.array([25, 0, -72])
    
    R = np.dot(R_y, R_x)
    
    while True:
      cam.grab_frame()
      _, confidence, cam_pose = cam.get_pose()
      
      # transformation into EE-frame
      T = np.eye(4)
      T[:3, :3] = R
      # T[:3, 3] = t
      
      ee_pose = np.dot(T, cam_pose)
      
      pos = ee_pose[:3,3]
    
      sys.stdout.write('\r')
      sys.stdout.write(f'x:{pos[0]:4.0f} y:{pos[1]:4.0f} z:{pos[2]:4.0f} - CONFIDENCE: {confidence:2.0f}')
      # sys.stdout.write(f'x:{angles[0]:5.1f} y:{angles[1]:5.1f} z:{angles[2]:5.1f} - CONFIDENCE: {confidence:2.0f}')
      sys.stdout.flush()
  
  except KeyboardInterrupt:
    cam.close()
  
if __name__ == "__main__":
    main()