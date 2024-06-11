import logging
import serial
import serial.tools.list_ports
import time
from numpy import interp

log = logging.getLogger(__name__)


class Grip:
    """
    Class that exposes abstract grip functionality.
    The state is calculated using AD-converted sensor readings from an Arduino.
    (Is looking for FT232R USB UART by default)
    """

    def __init__(self, comport=None, description="FT232R USB UART"):
        self.trigger_state = 0  # int [0,100]
        self.button_state = 0  # int {0,1}

        self.open_serial(comport, description)
        # input("### Please actuate the full range of the trigger and confirm ###")

    def get_trigger_state(self):
        return self.trigger_state

    def get_button_state(self):
        return self.button_state

    def get_data(self):
        line = self.read_serial()

        try:
            trigger_state, button_state = line.split(",")
            self.trigger_state = int(trigger_state)
            self.button_state = int(button_state)
            return True

        except ValueError as e:
            log.warn(f"False value received: {line}")
        except TypeError as e:
            log.warn(f"Non-integer type received: {type(line)}")

    def open_serial(self, comport, description, baudrate=115200):
        if comport == None:
            log.info(f"Scanning comports for {description}")
            ports = serial.tools.list_ports.comports()

            for port, desc, _ in sorted(ports):
                log.debug(f"{port}: {desc}")
                if description in desc:
                    log.info(f"Found {description} at {port}")
                    comport = port

            if comport == None:
                raise Exception(
                    f"No comport found for {description}. Is your Arduino connected?"
                )
        else:
            log.info(f"Comport specified as {comport}")

        if comport:
            try:
                self.ser = serial.Serial(comport, baudrate, timeout=1)
                log.info(f"Connected to {description} at {comport}")
                self.ser.reset_input_buffer()
                time.sleep(1)
                if self.ser.in_waiting > 0:
                    log.info(f"Reading initial lines to clear buffer")
                    for i in range(10):
                        _ = self.ser.readline()
                else:
                    log.error(f"No bytes received... ABORTING")
                    raise SystemExit
                    # raise Exception("No bytes received.")

                # if not data:
                #     log.warn(f'No data received. Retrying connection')
                #     self.ser.close()
                #     time.sleep(1)
                #     self.open_serial(comport, description, baudrate)

            except serial.SerialException as e:
                log.error(e)
        else:
            raise Exception(f"No comport defined for {description}")

    def read_serial(self):
        try:
            line = self.ser.readline().decode().rstrip()
            log.debug("Serial read line: " + line)
            return line
        except UnicodeDecodeError as e:
            log.error(e)

    def close_serial(self):
        log.info(f"Closing serial connection")
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        self.ser.close()
        time.sleep(2)  # time to reset buffer
        log.info(f"Connection closed")
