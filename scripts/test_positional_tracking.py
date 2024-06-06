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
    
    while True:
      cam.grab_frame()
      timestamp, confidence, cam_pose = cam.get_pose()
      
      # y-axis rotation by -90 degrees 
      # ZED overrides 2 of the 3 rotations from initial_world_transform using the IMU gravity
      rotation_matrix = np.array([
        [ 0.0,  0.0, -1.0],
        [ 0.0,  1.0,  0.0], 
        [ 1.0,  0.0,  0.0],  
      ])
     
      transformation_matrix = np.eye(4)
      transformation_matrix[:3, :3] = rotation_matrix
      
      ee_pose = np.dot(transformation_matrix, cam_pose)
      
      pos = ee_pose[:3,3]
      # pos = cam_pose[:3,3]
      
      
      # r = Rotation.from_matrix(ee_pose[:3,:3])
      # angles = r.as_euler("zyx", degrees=True)
    
      sys.stdout.write('\r')
      sys.stdout.write(f'x:{pos[0]:5.1f} y:{pos[1]:5.1f} z:{pos[2]:5.1f} - CONFIDENCE: {confidence:2.0f}')
      # sys.stdout.write(f'x:{angles[0]:5.1f} y:{angles[1]:5.1f} z:{angles[2]:5.1f} - CONFIDENCE: {confidence:2.0f}')
      sys.stdout.flush()
  
  except KeyboardInterrupt:
    cam.close()
  
if __name__ == "__main__":
    main()