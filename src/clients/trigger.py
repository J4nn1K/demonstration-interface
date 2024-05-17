import logging
import serial
import serial.tools.list_ports
import time
from numpy import interp

log = logging.getLogger(__name__)

class TriggerClient:
    '''
    Client that exposes sensor readings of an Arduino. 
    '''
    def __init__(self, comport=None ,baudrate=9600):
            
        self.calibrated = False

        if comport==None:    
            log.info('Scanning comports for FT232R USB UART')
            ports = serial.tools.list_ports.comports()

            for port, desc, _ in sorted(ports):
                log.debug(f'{port}: {desc}')
                if 'FT232R USB UART' in desc:
                    log.info(f'Found FT232R USB UART at {port}')
                    comport = port
            
            if comport==None:
                raise Exception('No comport found for FT232R USB UART. Is your Arduino connected?')
        else:
            log.info(f'Comport specified as {comport}')

        if comport:
            self.ser = serial.Serial(comport, baudrate, timeout=1)
            time.sleep(2) 
        
            log.info(f'Connected to FT232R USB UART at {comport}')
        else:
            raise Exception('No comport defined for FT232R USB UART') 
        

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


    def read_serial(self):
        return self.ser.readline().decode().rstrip()
        

    def close_serial(self):
        self.ser.close()