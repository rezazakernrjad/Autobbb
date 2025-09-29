# combination of pin_lib, bt_lib and auto_run receive message via bluetooth
# and control P9_14.

from periphery import GPIO
import time
import threading

class PIN:
    def __init__(self):
        print("Run Pin Control")
        self.P9_12 = GPIO("/dev/gpiochip0", 28, "out")
        self.motor_stop_event = threading.Event()
        self.motor_thread = None
    def _motor_control_loop(self):
        """Run the motor control loop in a separate thread"""
        while not self.motor_stop_event.is_set():
            self.P9_12.write(True)
            time.sleep(0.5)
            if self.motor_stop_event.is_set():
                break
            self.P9_12.write(False)
            time.sleep(0.5)
    
    def set_pin_9_12(self, message):
        print ("set_p_9_12 invoked with: ", message)
        
        # Stop any ongoing motor control
        self.motor_stop_event.set()
        if self.motor_thread and self.motor_thread.is_alive():
            self.motor_thread.join(timeout=1.0)  # Wait up to 1 second for thread to stop
        self.motor_stop_event.clear()
        
        if message == 1:
            self.P9_12.write(True)
            time.sleep(0.7)
            print("RUN LED ON command received")
        elif message == 0:
            self.P9_12.write(False)
            time.sleep(0.7)
            print("RUN LED OFF command received")
        elif  message == 2:
            print(f"Motor control command received: {message}")
            self.motor_thread = threading.Thread(target=self._motor_control_loop)
            self.motor_thread.daemon = True  # Thread will die when main program exits
            self.motor_thread.start()
    # etc.