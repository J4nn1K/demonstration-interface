import logging
import serial
import serial.tools.list_ports
import time
import re

log = logging.getLogger(__name__)

class TriggerClient:
    '''
    Client that exposes sensor readings of an Arduino. 
    '''
    def __init__(self, comport=None ,baudrate=9600):

        if comport==None:    
            log.info('Scanning comports for FT232R USB UART')
            ports = serial.tools.list_ports.comports()
    
            for port, desc, _ in sorted(ports):
                if 'FT232R USB UART' in desc:
                    log.info(f'Found FT232R USB UART at {port}')
                    comport = port
        else:
            log.info(f'Comport specified as {comport}')


        self.ser = serial.Serial(comport, baudrate, timeout=1)
        time.sleep(2) 
        
        log.info(f'Connected to FT232R USB UART at {comport}')


    def get_trigger_state(self):
        '''
        TBD - filter for correct data
        '''
        return self.ser.readline().decode().rstrip()
        

    def close(self):
        self.ser.close()