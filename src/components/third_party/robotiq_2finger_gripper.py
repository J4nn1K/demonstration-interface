# Obtained from:
# https://github.com/facebookresearch/fairo/blob/main/polymetis/polymetis/python/polymetis/robot_client/robotiq_gripper/third_party/robotiq_2finger_grippers/
# https://github.com/Danfoa/robotiq_2finger_grippers/

import serial
from serial.serialutil import SerialException

from pymodbus.client.sync import ModbusSerialClient
from pymodbus.exceptions import ModbusIOException

from math import ceil

import numpy as np
import array

ACTION_REQ_IDX = 7
POS_INDEX = 10
SPEED_INDEX = 11
FORCE_INDEX = 12

class Communication:
    '''
    Class which communicates with Robotiq Grippers using the Modbus RTU protocol. 
    
    Copyright (c) Facebook, Inc. and its affiliates.
    Copyright (c) 2012, Robotiq, Inc.
    '''
    def __init__(self):
        self.client = None

    def connectToDevice(self, device):
        """Connection to the client - the method takes the IP address (as a string, e.g. '192.168.1.11') as an argument."""
        self.client = ModbusSerialClient(
            method="rtu",
            port=device,
            stopbits=1,
            bytesize=8,
            baudrate=115200,
            timeout=0.2,
        )
        if not self.client.connect():
            print("Unable to connect to %s" % device)
            return False
        return True

    def disconnectFromDevice(self):
        """Close connection"""
        self.client.close()

    def sendCommand(self, data):
        """Send a command to the Gripper - the method takes a list of uint8 as an argument. The meaning of each variable depends on the Gripper model (see support.robotiq.com for more details)"""
        # make sure data has an even number of elements
        if len(data) % 2 == 1:
            data.append(0)

        # Initiate message as an empty list
        message = []

        # Fill message by combining two bytes in one register
        for i in range(0, len(data) // 2):
            message.append((data[2 * i] << 8) + data[2 * i + 1])

        # To do!: Implement try/except
        try:
            self.client.write_registers(0x03E8, message, unit=0x0009)
        except:
            print("Modbus write operation failure")
            return False
        return True

    def getStatus(self, numBytes):
        """Sends a request to read, wait for the response and returns the Gripper status. The method gets the number of bytes to read as an argument"""
        numRegs = int(ceil(numBytes / 2.0))

        # To do!: Implement try/except
        # Get status from the device
        try:
            response = self.client.read_holding_registers(0x07D0, numRegs, unit=0x0009)
        except Exception as e:
            print(e)
            return None

        # When reading failes, response is of type None
        if response is None:
            #   print("Failed to receive status")
            return None
        # Newer versions of pymodbus returns a ModbusIOException instead
        elif type(response) is ModbusIOException:
            return None

        # Instantiate output as an empty list
        output = []

        # Fill the output with the bytes in the appropriate order
        for i in range(0, numRegs):
            output.append((response.getRegister(i) & 0xFF00) >> 8)
            output.append(response.getRegister(i) & 0x00FF)

        # Output the result
        return output

class Robotiq2FingerGripper:
    def __init__(self, device_id=0, stroke=0.05, comport="/dev/ttyUSB0", baud=115200):

        self.client = Communication()

        connected = self.client.connectToDevice(device=comport)
        if not connected:
            raise Exception(
                "Communication with gripper %d on serial port: %s and baud rate: %d not achieved"
                % (device_id, comport, baud)
            )

        self.init_success = True
        self.device_id = device_id + 9
        self.stroke = stroke
        self.initialize_communication_variables()

        self.message = []

    def _update_cmd(self):

        # Initiate command as an empty list
        self.message = []
        # Build the command with each output variable
        self.message.append(self.rACT + (self.rGTO << 3) + (self.rATR << 4))
        self.message.append(0)
        self.message.append(0)
        self.message.append(self.rPR)
        self.message.append(self.rSP)
        self.message.append(self.rFR)

    def sendCommand(self):
        """Send the command to the Gripper."""
        return self.client.sendCommand(self.message)

    def getStatus(self):
        """Request the status from the gripper and return it in the Robotiq2FGripper_robot_input msg type."""

        # Acquire status from the Gripper
        status = self.client.getStatus(6)

        # Check if read was successful
        if status is None:
            return False

        # Assign the values to their respective variables
        self.gACT = (status[0] >> 0) & 0x01
        self.gGTO = (status[0] >> 3) & 0x01
        self.gSTA = (status[0] >> 4) & 0x03
        self.gOBJ = (status[0] >> 6) & 0x03
        self.gFLT = status[2]
        self.gPR = status[3]
        self.gPO = status[4]
        self.gCU = status[5]

        return True

    def initialize_communication_variables(self):
        # Out
        self.rPR = 0
        self.rSP = 255
        self.rFR = 150
        self.rARD = 1
        self.rATR = 0
        self.rGTO = 0
        self.rACT = 0
        # In
        self.gSTA = 0
        self.gACT = 0
        self.gGTO = 0
        self.gOBJ = 0
        self.gFLT = 0
        self.gPO = 0
        self.gPR = 0
        self.gCU = 0

        self._update_cmd()
        self._max_force = 100.0  # [%]

    def shutdown(self):
        self.client.disconnectFromDevice()

    def activate_gripper(self):
        self.rACT = 1
        self.rPR = 0
        self.rSP = 255
        self.rFR = 150
        self._update_cmd()

    def deactivate_gripper(self):
        self.rACT = 0
        self._update_cmd()

    def activate_emergency_release(self, open_gripper=True):
        self.rATR = 1
        self.rARD = 1

        if open_gripper:
            self.rARD = 0
        self._update_cmd()

    def deactivate_emergency_release(self):
        self.rATR = 0
        self._update_cmd()

    def goto(self, pos, vel, force):
        self.rACT = 1
        self.rGTO = 1
        self.rPR = int(np.clip(255.0 * pos, 0, 255))
        self.rSP = int(np.clip(255.0 * vel, 0, 255))
        self.rFR = int(np.clip(255.0 * force, 0, 255))
        # self.rPR = int(np.clip((3.0 - 230.0) / self.stroke * pos + 230.0, 0, 255))
        # self.rSP = int(np.clip(255.0 / (0.1 - 0.013) * vel - 0.013, 0, 255))
        # self.rFR = int(np.clip(255.0 / (self._max_force) * force, 0, 255))
        self._update_cmd()

    def stop(self):
        self.rACT = 1
        self.rGTO = 0
        self._update_cmd()

    def is_ready(self):
        return self.gSTA == 3 and self.gACT == 1

    def is_reset(self):
        return self.gSTA == 0 or self.gACT == 0

    def is_moving(self):
        return self.gGTO == 1 and self.gOBJ == 0

    def is_stopped(self):
        return self.gOBJ != 0

    def object_detected(self):
        return self.gOBJ == 1 or self.gOBJ == 2

    def get_fault_status(self):
        return self.gFLT

    def get_pos(self):
        po = float(self.gPO)
        # return po
        return np.clip(1-(1.0 / (3.0 - 250.0) * (po - 250.0)), 0, 1)
        # return np.clip(self.stroke / (3.0 - 230.0) * (po - 230.0), 0, self.stroke)

    def get_req_pos(self):
        pr = float(self.gPR)
        return np.clip(self.stroke / (3.0 - 230.0) * (pr - 230.0), 0, self.stroke)

    def get_current(self):
        return self.gCU * 0.1