#!/usr/bin/env python3
"""
Multiple Software PWM Controller for BeagleBone Black
Controls multiple GPIO pins as PWM channels simultaneously
"""

from periphery import GPIO
import time
import threading
import signal
import sys

class SoftwarePWM:
    def __init__(self, chip_path, line, frequency=1000, name="PWM"):
        self.gpio = GPIO(chip_path, line, "out")
        self.frequency = frequency
        self.duty_cycle = 0.0
        self.running = False
        self.thread = None
        self.name = name
        self._lock = threading.Lock()
        print(f"Initialized {self.name} on {chip_path}, line {line}")
        
    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._pwm_loop, daemon=True)
            self.thread.start()
            print(f"{self.name} started")
            
    def _pwm_loop(self):
        while self.running:
            with self._lock:
                duty = self.duty_cycle
                freq = self.frequency
                
            if freq <= 0:
                time.sleep(0.01)
                continue
                
            period = 1.0 / freq
            
            if duty > 0:
                self.gpio.write(True)
                high_time = period * duty
                if high_time > 0.0001:  # Minimum 0.1ms
                    time.sleep(high_time)
                    
            if duty < 1.0:
                self.gpio.write(False)
                low_time = period * (1.0 - duty)
                if low_time > 0.0001:
                    time.sleep(low_time)
                    
    def set_duty_cycle_percent(self, percent):
        percent = max(0, min(100, percent))
        with self._lock:
            self.duty_cycle = percent / 100.0
        print(f"{self.name}: {percent}%")
        
    def set_frequency(self, frequency):
        if frequency > 0:
            with self._lock:
                self.frequency = frequency
            print(f"{self.name} frequency: {frequency}Hz")
            
    def stop(self):
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join(timeout=1.0)
            self.gpio.write(False)
            print(f"{self.name} stopped")
            
    def close(self):
        self.stop()
        self.gpio.close()
        print(f"{self.name} closed")

class MultiPWMController:
    def __init__(self):
        self.pwm_channels = {}
        self.running = False
        
    def add_pwm(self, name, chip_path, line, frequency=1000):
        """Add a PWM channel"""
        try:
            pwm = SoftwarePWM(chip_path, line, frequency, name)
            self.pwm_channels[name] = pwm
            print(f"Added PWM channel: {name}")
            return True
        except Exception as e:
            print(f"Failed to add {name}: {e}")
            return False
            
    def start_all(self):
        """Start all PWM channels"""
        print("Starting all PWM channels...")
        for name, pwm in self.pwm_channels.items():
            pwm.start()
        self.running = True
        print(f"All {len(self.pwm_channels)} PWM channels started")
        
    def stop_all(self):
        """Stop all PWM channels"""
        print("Stopping all PWM channels...")
        for name, pwm in self.pwm_channels.items():
            pwm.stop()
        self.running = False
        print("All PWM channels stopped")
        
    def close_all(self):
        """Close all PWM channels"""
        print("Closing all PWM channels...")
        for name, pwm in self.pwm_channels.items():
            pwm.close()
        self.pwm_channels.clear()
        print("All PWM channels closed")
        
    def set_duty_cycle(self, name, percent):
        """Set duty cycle for specific PWM channel"""
        if name in self.pwm_channels:
            self.pwm_channels[name].set_duty_cycle_percent(percent)
        else:
            print(f"PWM channel '{name}' not found")
            
    def set_frequency(self, name, frequency):
        """Set frequency for specific PWM channel"""
        if name in self.pwm_channels:
            self.pwm_channels[name].set_frequency(frequency)
        else:
            print(f"PWM channel '{name}' not found")
            
    def get_channel_names(self):
        """Get list of available PWM channel names"""
        return list(self.pwm_channels.keys())

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\nShutting down PWM controller...")
    global controller
    if 'controller' in globals():
        controller.close_all()
    sys.exit(0)

def test_multi_pwm():
    """Test multiple PWM channels"""
    global controller
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print("=" * 50)
    print("Multiple Software PWM Test")
    print("=" * 50)
    
    # Create controller
    controller = MultiPWMController()
    
    # Add PWM channels - using pins we know work
    print("Adding PWM channels...")
    controller.add_pwm("LED1", "/dev/gpiochip0", 18, 1000)  # P9_14
    controller.add_pwm("LED2", "/dev/gpiochip0", 19, 1000)  # P9_16  
    controller.add_pwm("LED3", "/dev/gpiochip0", 17, 1000)  # P9_23
    
    # Start all PWM channels
    controller.start_all()
    
    try:
        # Test 1: Individual control
        print("\n=== Test 1: Individual LED Control ===")
        controller.set_duty_cycle("LED1", 25)   # 25% brightness
        controller.set_duty_cycle("LED2", 50)   # 50% brightness  
        controller.set_duty_cycle("LED3", 75)   # 75% brightness
        time.sleep(3)
        
        # Test 2: Sequential fade
        print("\n=== Test 2: Sequential Fade ===")
        for led in ["LED1", "LED2", "LED3"]:
            print(f"Fading {led}...")
            
            # Fade in
            for brightness in range(0, 101, 10):
                controller.set_duty_cycle(led, brightness)
                time.sleep(0.1)
                
            # Fade out
            for brightness in range(100, -1, -10):
                controller.set_duty_cycle(led, brightness)
                time.sleep(0.1)
                
            time.sleep(0.5)
            
        # Test 3: Synchronized fade
        print("\n=== Test 3: Synchronized Fade ===")
        for cycle in range(2):
            print(f"Sync cycle {cycle + 1}/2")
            
            # All fade in together
            for brightness in range(0, 101, 5):
                for led in ["LED1", "LED2", "LED3"]:
                    controller.set_duty_cycle(led, brightness)
                time.sleep(0.05)
                
            # All fade out together  
            for brightness in range(100, -1, -5):
                for led in ["LED1", "LED2", "LED3"]:
                    controller.set_duty_cycle(led, brightness)
                time.sleep(0.05)
                
        # Test 4: Different frequencies
        print("\n=== Test 4: Different Frequencies ===")
        controller.set_frequency("LED1", 500)   # 500Hz
        controller.set_frequency("LED2", 1000)  # 1kHz
        controller.set_frequency("LED3", 2000)  # 2kHz
        
        # Set all to 50% duty cycle
        for led in ["LED1", "LED2", "LED3"]:
            controller.set_duty_cycle(led, 50)
            
        print("Running different frequencies for 5 seconds...")
        time.sleep(5)
        
        # Turn off all LEDs
        for led in ["LED1", "LED2", "LED3"]:
            controller.set_duty_cycle(led, 0)
            
        print("\n=== Multi-PWM Test Complete ===")
        
    except KeyboardInterrupt:
        print("\nTest interrupted")
    finally:
        controller.close_all()

def interactive_multi_pwm():
    """Interactive multi-PWM control"""
    global controller
    
    signal.signal(signal.SIGINT, signal_handler)
    
    print("=" * 50)
    print("Interactive Multi-PWM Controller")
    print("=" * 50)
    
    controller = MultiPWMController()
    
    # Add PWM channels
    controller.add_pwm("P9_14", "/dev/gpiochip0", 18, 1000)
    controller.add_pwm("P9_16", "/dev/gpiochip0", 19, 1000)  
    controller.add_pwm("P9_23", "/dev/gpiochip0", 17, 1000)
    
    controller.start_all()
    
    print("\nCommands:")
    print("  set <pin> <percent>  - Set duty cycle (e.g., 'set P9_14 50')")
    print("  freq <pin> <hz>      - Set frequency (e.g., 'freq P9_14 2000')")
    print("  list                 - List available pins")
    print("  quit                 - Exit")
    print()
    
    try:
        while True:
            try:
                cmd = input("PWM> ").strip().split()
                
                if not cmd:
                    continue
                    
                if cmd[0] == 'quit' or cmd[0] == 'q':
                    break
                elif cmd[0] == 'list':
                    print(f"Available pins: {', '.join(controller.get_channel_names())}")
                elif cmd[0] == 'set' and len(cmd) == 3:
                    pin, percent = cmd[1], float(cmd[2])
                    controller.set_duty_cycle(pin, percent)
                elif cmd[0] == 'freq' and len(cmd) == 3:
                    pin, frequency = cmd[1], float(cmd[2])
                    controller.set_frequency(pin, frequency)
                else:
                    print("Invalid command")
                    
            except (ValueError, KeyboardInterrupt):
                break
                
    finally:
        controller.close_all()

def main():
    """Main function"""
    print("Multiple Software PWM Controller")
    print("Choose mode:")
    print("1. Automated test")
    print("2. Interactive control")
    
    try:
        choice = input("Enter choice (1 or 2): ").strip()
        
        if choice == "1":
            test_multi_pwm()
        elif choice == "2":
            interactive_multi_pwm()
        else:
            print("Invalid choice")
            
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main()
