import logging
import pyzed.sl as sl
import numpy as np
from src.config import ZED, TRANSFORMATIONS

log = logging.getLogger(__name__)


class Tracker:
    def __init__(self, fps=60):
        log.info("Creating and opening tracker camera")
        self.zed = sl.Camera()

        init_params = sl.InitParameters()
        init_params.camera_resolution = ZED["resolution"]
        init_params.camera_fps = ZED["fps"]
        init_params.coordinate_system = ZED["coordinate_system"]
        init_params.coordinate_units = ZED["units"]
        init_params.depth_mode = ZED["depth_mode"]

        err = self.zed.open(init_params)
        if err != sl.ERROR_CODE.SUCCESS:
            print("Camera Open : " + repr(err) + ". Exit program.")
            exit()
        log.info("Camera succesfully opened")

        self.runtime_parameters = sl.RuntimeParameters()

        log.info("Grabbing initial frames")
        # Doing this because on the first frame the POSITIONAL_TRACKING_STATE is not OK
        for _ in range(30):
            self.zed.grab(self.runtime_parameters)

    def enable_tracking(self):
        log.info("Enabling positional tracking")
        py_transform = (
            sl.Transform()
        )  # First create a Transform object for TrackingParameters object
        tracking_parameters = sl.PositionalTrackingParameters(
            _init_pos=py_transform, _set_gravity_as_origin=False
        )
        err = self.zed.enable_positional_tracking(tracking_parameters)
        if err != sl.ERROR_CODE.SUCCESS:
            print("Enable positional tracking : " + repr(err) + ". Exit program.")
            self.zed.close()
            exit()

    def grab_frame(self):
        return self.zed.grab(self.runtime_parameters) == sl.ERROR_CODE.SUCCESS

    def get_image(self):
        image = sl.Mat()

        self.zed.retrieve_image(image, sl.VIEW.LEFT)
        timestamp = image.timestamp.get_milliseconds()

        return timestamp, image.get_data(deep_copy=True)

    def get_ee_pose(self):
        timestamp, confidence, pose = self.get_pose_in_ee_frame()
        return timestamp, confidence, np.dot(pose, TRANSFORMATIONS["ZED_to_EE"])

    def get_pose_in_ee_frame(self):
        """
        Same as get_pose() but returns pose transformed into EE frame.
        """
        timestamp, confidence, pose = self.get_pose()
        return timestamp, confidence, np.dot(TRANSFORMATIONS["ZED_in_EE_frame"], pose)
        

    def get_pose(self):
        pose = sl.Pose()
        # pose_data = sl.Transform()

        self.zed.get_position(pose, sl.REFERENCE_FRAME.WORLD)
        # tracking_state = self.zed.get_position(pose, sl.REFERENCE_FRAME.WORLD
        # if tracking_state == sl.POSITIONAL_TRACKING_STATE.OK:

        timestamp = pose.timestamp.get_milliseconds()
        confidence = pose.pose_confidence

        return timestamp, confidence, pose.pose_data(sl.Transform()).m

    def close(self):
        self.zed.close()
        log.info("Camera closed")
