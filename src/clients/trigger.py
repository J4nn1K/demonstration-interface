import logging
import serial
import serial.tools.list_ports
import time
from numpy import interp

log = logging.getLogger(__name__)


class TriggerClient:
    '''
    Client that exposes a trigger state. 
    The state is calculated using AD-converted sensor readings from an Arduino. 
    (Is looking for FT232R USB UART by default)
    '''
    def __init__(self, comport=None, description='FT232R USB UART'):            
        self.calibrated = False
        self.open_serial(comport, description)


    def get_trigger_state(self):
        '''
        Returns the trigger state on a range of [0,1].
        '''
        if self.calibrated:
            value = self.get_adc_value()
            if value:
                return interp(value, [self.min_value, self.max_value], [0,1])
                
        else:
            raise Exception('Trigger is not calibrated')

    
    def calibrate(self, seconds=5):
        self.min_value = 1023
        self.max_value = 0
        
        t_end = time.time() + seconds
        log.info(f'Please actuate the full range of the trigger')
        while time.time() < t_end:
            value = self.get_adc_value()
            if value:
                if value < self.min_value: self.min_value = value
                if value > self.max_value: self.max_value = value
        
        self.calibrated = True
        log.info(f'Calibrated trigger with: min_value={self.min_value}, max_value={self.max_value}')
    

    def get_adc_value(self):
        line = self.read_serial()
        try:
            value = int(line)
            return value
        except ValueError:
            log.warn(f'Non-integer value received: {line}')


    def open_serial(self, comport, description, baudrate=9600):
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
            self.ser = serial.Serial(comport, baudrate, timeout=1)
            time.sleep(2) 
        
            log.info(f'Connected to {description} at {comport}')
        else:
            raise Exception(f'No comport defined for {description}') 
    

    def read_serial(self):
        line = self.ser.readline().decode().rstrip()
        log.debug(line)
        return line
        

    def close_serial(self):
        self.ser.close()
        log.info(f'Connection closed')