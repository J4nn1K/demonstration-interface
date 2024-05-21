import logging
import serial
import serial.tools.list_ports
import time
from numpy import interp

log = logging.getLogger(__name__)


class Trigger:
    '''
    Class that exposes abstract trigger functionality.
    The state is calculated using AD-converted sensor readings from an Arduino. 
    (Is looking for FT232R USB UART by default)
    '''
    def __init__(self, comport=None, description='FT232R USB UART', alpha=0.1):            
        self.calibrated = False
        self.open_serial(comport, description)
        
        # Filter parameters for a simple low-pass filter
        self.prev_filtered_value = 0
        self.alpha = alpha

    def get_trigger_state(self):
        '''
        Returns the trigger state on a range of [0,1].
        '''
        if self.calibrated:
            #value = self.get_adc_value()
            value = self.get_filtered_adc_value()
            if value:
                return float(interp(value, [self.min_value, self.max_value], [0,1]))
            else:
                log.warn(f'No value received')
                
        else:
            raise Exception('Trigger is not calibrated')

    
    def calibrate(self, seconds=5):
        # Assuming a 10-bit ADC
        self.min_value = 1023
        self.max_value = 0
        
        t_end = time.time() + seconds
        log.info(f'Please actuate the full range of the trigger for {seconds} seconds to calibrate.')
        while time.time() < t_end:
            value = self.get_adc_value()
            if value:
                if value < self.min_value: self.min_value = value
                if value > self.max_value: self.max_value = value
        
        self.calibrated = True
        log.info(f'Calibrated trigger with: min_value={self.min_value}, max_value={self.max_value}')
    

    def get_filtered_adc_value(self):
        raw_value = self.get_adc_value()
        filtered_value = self.alpha * raw_value + (1 - self.alpha) * self.prev_filtered_value
        self.prev_filtered_value = filtered_value
        return filtered_value


    def get_adc_value(self):    
        line = self.read_serial()
        try:
            value = int(line)
            return value
        except ValueError as e:
            log.warn(f'Non-integer value received: {line}')
        except TypeError as e:
            log.warn(f'Non-integer type received: {type(line)}')


    def open_serial(self, comport, description, baudrate=115200):
        if comport==None:    
            log.info(f'Scanning comports for {description}')
            ports = serial.tools.list_ports.comports()

            for port, desc, _ in sorted(ports):
                log.debug(f'{port}: {desc}')
                if description in desc:
                    log.info(f'Found {description} at {port}')
                    comport = port
            
            if comport==None:
                raise Exception(f'No comport found for {description}. Is your Arduino connected?')
        else:
            log.info(f'Comport specified as {comport}')

        if comport:
            try:
                self.ser = serial.Serial(comport, baudrate, timeout=1)
                log.info(f'Connected to {description} at {comport}')
                log.info(f'Reading initial lines to clear buffer')
                
                
                for i in range(100):
                    _ = self.ser.readline()

                # if not data:
                #     log.warn(f'No data received. Retrying connection')
                #     self.ser.close()
                #     time.sleep(1)
                #     self.open_serial(comport, description, baudrate)

            except serial.SerialException as e:
                log.error(e)
        else:
            raise Exception(f'No comport defined for {description}') 
    

    def read_serial(self):
        try:
            line = self.ser.readline().decode().rstrip()
            log.debug(line)
            return line
        except UnicodeDecodeError as e:
            log.error(e)
        

    def close_serial(self):
        self.ser.close()
        log.info(f'Connection closed')