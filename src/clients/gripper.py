import logging
import time
import serial
import serial.tools.list_ports
from src.clients.third_party.robotiq_2finger_gripper import Robotiq2FingerGripper

log = logging.getLogger(__name__)


class GripperClient:
    '''
    tbd
    '''
    def __init__(self, comport=None, description='USB TO RS-485'):
        if not comport:
            comport = self.find_comport(description)

        self.gripper = Robotiq2FingerGripper(comport=comport)
        
        if not self.gripper.init_success:
            raise Exception(f"Unable to open comport to {comport}")
        if not self.gripper.getStatus():
            raise Exception(f"Failed to contact gripper on port {comport}... ABORTING")
        
        log.info(f'Connected to {description} at {comport}')

    def go_to(self, position):
        '''
        Go to position: 0=OPEN 1=CLOSED
        '''
        self.gripper.goto(pos=position, vel=1.0, force=1.0)
        self.gripper.sendCommand()


    def get_position(self):
        if self.gripper.getStatus():
            return self.gripper.get_pos()


    def activate(self):
        self.gripper.activate_emergency_release()
        self.gripper.sendCommand()
        time.sleep(1)
        self.gripper.deactivate_emergency_release()
        self.gripper.sendCommand()
        time.sleep(1)
        self.gripper.activate_gripper()
        self.gripper.sendCommand()
        time.sleep(2)
        if (
            self.gripper.is_ready()
            and self.gripper.sendCommand()
            and self.gripper.getStatus()
        ):
            log.info(f'Gripper activated')
        else:
            raise Exception(f"Unable to activate gripper")


    def find_comport(self, description):
        comport = None
        log.info(f'Scanning comports for {description}')
        ports = serial.tools.list_ports.comports()
        for port, desc, _ in sorted(ports):
            log.debug(f'{port}: {desc}')
            if description in desc:
                log.info(f'Found {description} at {port}')
                comport = port
        
        if comport==None:
            raise Exception(f'No comport found for {description}. Is your gripper connected?')
        else:
            log.info(f'Comport specified as {comport}')

        return comport