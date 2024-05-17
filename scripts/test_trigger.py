from src.clients.trigger import TriggerClient
import logging

logging.basicConfig(level=logging.INFO)

def main():
    trigger = TriggerClient()
    trigger.calibrate()

    try:
        while True:
            state = trigger.get_trigger_state()
            if state: 
                print(f'{state:.2f}')
    finally:
        trigger.close_serial()


if __name__ == "__main__":
    main()