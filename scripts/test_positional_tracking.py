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
        print("\n")

        while True:
            cam.grab_frame()
            _, confidence, ee_pose = cam.get_ee_pose()

            pos = ee_pose[:3, 3]

            sys.stdout.write("\r")
            sys.stdout.write(
                f"x:{pos[0]:4.0f} y:{pos[1]:4.0f} z:{pos[2]:4.0f} - CONFIDENCE: {confidence:2.0f}"
            )
            # sys.stdout.write(f'x:{angles[0]:5.1f} y:{angles[1]:5.1f} z:{angles[2]:5.1f} - CONFIDENCE: {confidence:2.0f}')
            sys.stdout.flush()

    except KeyboardInterrupt:
        cam.close()


if __name__ == "__main__":
    main()
