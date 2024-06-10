import logging
import pyrealsense2 as rs
import numpy as np

from src.config import REALSENSE

log = logging.getLogger(__name__)

class Camera:
  def __init__(self):
    try:
      log.info('Opening RealSense camera stream')
      
      self.pipeline = rs.pipeline()
      config = rs.config()
      config.enable_stream(rs.stream.color, REALSENSE["color_width"], REALSENSE["color_height"], rs.format.bgr8, REALSENSE["color_fps"])
      config.enable_stream(rs.stream.depth, REALSENSE["depth_width"], REALSENSE["depth_height"], rs.format.z16, REALSENSE["depth_fps"])
      self.pipeline.start(config)
      
      self.frames = None
      
    except Exception as e:
      raise Exception('Error opening RealSense camera stream: ' + str(e))

  def wait_for_frames(self):
    self.frames = self.pipeline.wait_for_frames()


  def get_image(self):
    '''
    Returns 8-bit blue, green, and red channels channels - suitable for OpenCV
    '''
    try:
      return np.asanyarray(self.frames.get_color_frame().get_data())
    except AttributeError:
      raise Exception('Did you call wait_for_frames before get_image?')
    except RuntimeError:
      raise Exception('Did you enable the color stream?')

  
  def get_depth(self):
    '''
    Returns 16 bit linear depth values. The depth is meters is equal to depth scale * pixel value.
    '''
    try:
      return np.asanyarray(self.frames.get_depth_frame().get_data())
    except AttributeError:
      raise Exception('Did you call wait_for_frames before get_depth_frame?')
    except RuntimeError:
      raise Exception('Did you enable the depth stream?')
