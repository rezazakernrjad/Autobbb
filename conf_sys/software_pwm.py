from periphery import GPIO
import time
import threading

class SoftwarePWM:
    def __init__(self, chip_path, line, frequency=1000):
        self.gpio = GPIO(chip_path, line, "out")
        self.frequency = frequency
        self.duty_cycle = 0.0
        self.running = False
        self.thread = None
        
    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._pwm_loop, daemon=True)
            self.thread.start()
            
    def _pwm_loop(self):
        period = 1.0 / self.frequency
        while self.running:
            if self.duty_cycle > 0:
                self.gpio.write(True)
                time.sleep(period * self.duty_cycle)
            if self.duty_cycle < 1.0:
                self.gpio.write(False)  
                time.sleep(period * (1.0 - self.duty_cycle))
                
    def set_duty_cycle_percent(self, percent):
        self.duty_cycle = max(0, min(100, percent)) / 100.0
        
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        self.gpio.close()

# Test on P9_14 (confirmed working as GPIO)
pwm = SoftwarePWM("/dev/gpiochip0", 18, 1000)
pwm.start()

print("Testing software PWM fade - you should see LED fading")
for brightness in range(0, 101, 5):
    pwm.set_duty_cycle_percent(brightness)
    time.sleep(0.1)

pwm.stop()
