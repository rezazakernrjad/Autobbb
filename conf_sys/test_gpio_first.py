#!/usr/bin/env python3
"""
Hardware PWM Examples for BeagleBone Black
Now that hardware PWM is working, here are practical examples
"""

from periphery import PWM
import time
import signal
import sys

class HardwarePWMController:
    def __init__(self, chip=0, channel=0):
        """
        Initialize Hardware PWM Controller
        
        Args:
            chip: PWM chip number (0, 1, 2, etc.)
            channel: PWM channel (0 or 1 typically)
        """
        self.pwm = PWM(chip, channel)
        self.chip = chip
        self.channel = channel
        print(f"Hardware PWM initialized: chip {chip}, channel {channel}")
        
    def set_frequency(self, frequency):
        """Set PWM frequency in Hz"""
        self.pwm.frequency = frequency
        print(f"Frequency set to {frequency}Hz")
        
    def set_duty_cycle(self, percent):
        """Set duty cycle as percentage (0-100)"""
        duty = max(0, min(100, percent)) / 100.0
        self.pwm.duty_cycle = duty
        print(f"Duty cycle set to {percent}%")
        
    def enable(self):
        """Enable PWM output"""
        self.pwm.enable()
        print("PWM enabled")
        
    def disable(self):
        """Disable PWM output"""
        self.pwm.disable()
        print("PWM disabled")
        
    def close(self):
        """Clean up PWM resources"""
        self.pwm.disable()
        self.pwm.close()
        print("PWM closed")

def led_brightness_control():
    """Example 1: LED brightness control"""
    print("=== LED Brightness Control Example ===")
    
    pwm = HardwarePWMController(0, 0)
    pwm.set_frequency(1000)  # 1kHz for LED control
    pwm.enable()
    
    try:
        # Smooth brightness transitions
        brightness_levels = [0, 10, 25, 50, 75, 90, 100, 75, 50, 25, 10, 0]
        
        for brightness in brightness_levels:
            print(f"LED brightness: {brightness}%")
            pwm.set_duty_cycle(brightness)
            time.sleep(1)
            
    finally:
        pwm.close()

def servo_motor_control():
    """Example 2: Servo motor control"""
    print("\n=== Servo Motor Control Example ===")
    
    pwm = HardwarePWMController(0, 0)
    pwm.set_frequency(50)  # 50Hz for servo control
    pwm.enable()
    
    try:
        # Servo positions (duty cycles for standard servos)
        positions = {
            "center": 7.5,   # 1.5ms pulse width
            "left": 5.0,     # 1.0ms pulse width  
            "right": 10.0,   # 2.0ms pulse width
        }
        
        # Move servo to different positions
        for position_name, duty in positions.items():
            print(f"Moving servo to {position_name} position")
            pwm.set_duty_cycle(duty)
            time.sleep(2)
        
        # Smooth sweep
        print("Performing smooth sweep...")
        for duty in range(50, 101, 2):  # 5% to 10% duty cycle
            pwm.set_duty_cycle(duty / 10.0)
            time.sleep(0.1)
            
        for duty in range(100, 49, -2):  # 10% to 5% duty cycle
            pwm.set_duty_cycle(duty / 10.0)
            time.sleep(0.1)
            
    finally:
        pwm.close()

def motor_speed_control():
    """Example 3: DC motor speed control"""
    print("\n=== DC Motor Speed Control Example ===")
    
    pwm = HardwarePWMController(0, 0)
    pwm.set_frequency(1000)  # 1kHz for motor control
    pwm.enable()
    
    try:
        # Gradual speed increase
        print("Accelerating motor...")
        for speed in range(0, 101, 10):
            print(f"Motor speed: {speed}%")
            pwm.set_duty_cycle(speed)
            time.sleep(0.5)
        
        # Hold at full speed
        time.sleep(2)
        
        # Gradual speed decrease
        print("Decelerating motor...")
        for speed in range(100, -1, -10):
            print(f"Motor speed: {speed}%")
            pwm.set_duty_cycle(speed)
            time.sleep(0.5)
            
    finally:
        pwm.close()

def breathing_led_effect():
    """Example 4: Smooth breathing LED effect"""
    print("\n=== Breathing LED Effect Example ===")
    
    pwm = HardwarePWMController(0, 0)
    pwm.set_frequency(1000)  # 1kHz
    pwm.enable()
    
    try:
        import math
        
        cycles = 3
        print(f"Running breathing effect for {cycles} cycles...")
        
        for cycle in range(cycles):
            print(f"Breathing cycle {cycle + 1}/{cycles}")
            
            # Use sine wave for smooth breathing
            for i in range(100):
                # Create sine wave from 0 to π (half cycle)
                angle = (i / 99.0) * math.pi
                brightness = (math.sin(angle) ** 2) * 100  # Square for smoother curve
                pwm.set_duty_cycle(brightness)
                time.sleep(0.05)  # 50ms steps
                
            time.sleep(0.5)  # Pause between cycles
            
    finally:
        pwm.close()

def pwm_frequency_demo():
    """Example 5: PWM frequency demonstration"""
    print("\n=== PWM Frequency Demonstration ===")
    print("(Connect a buzzer or speaker to hear different frequencies)")
    
    pwm = HardwarePWMController(0, 0)
    pwm.set_duty_cycle(50)  # 50% duty cycle for audio
    pwm.enable()
    
    try:
        # Musical notes frequencies (Hz)
        notes = {
            "C4": 262,
            "D4": 294, 
            "E4": 330,
            "F4": 349,
            "G4": 392,
            "A4": 440,
            "B4": 494,
            "C5": 523
        }
        
        for note_name, frequency in notes.items():
            print(f"Playing {note_name} ({frequency}Hz)")
            pwm.set_frequency(frequency)
            time.sleep(0.5)
            
        # Frequency sweep
        print("Frequency sweep from 100Hz to 2000Hz...")
        for freq in range(100, 2001, 50):
            pwm.set_frequency(freq)
            time.sleep(0.1)
            
    finally:
        pwm.close()

def interactive_pwm_control():
    """Example 6: Interactive PWM control"""
    print("\n=== Interactive PWM Control ===")
    print("Commands: f<freq> (set frequency), d<duty> (set duty cycle), q (quit)")
    print("Examples: f1000, d50, q")
    
    pwm = HardwarePWMController(0, 0)
    pwm.set_frequency(1000)
    pwm.set_duty_cycle(0)
    pwm.enable()
    
    try:
        while True:
            try:
                command = input("PWM> ").strip().lower()
                
                if command == 'q' or command == 'quit':
                    break
                elif command.startswith('f'):
                    freq = int(command[1:])
                    pwm.set_frequency(freq)
                elif command.startswith('d'):
                    duty = float(command[1:])
                    pwm.set_duty_cycle(duty)
                else:
                    print("Invalid command. Use f<freq>, d<duty>, or q")
                    
            except (ValueError, KeyboardInterrupt):
                break
                
    finally:
        pwm.close()

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\nShutting down PWM...")
    sys.exit(0)

def main():
    """Run PWM examples"""
    signal.signal(signal.SIGINT, signal_handler)
    
    print("=" * 60)
    print("BeagleBone Black Hardware PWM Examples")
    print("🎉 Hardware PWM is working!")
    print("=" * 60)
    
    examples = [
        ("LED Brightness Control", led_brightness_control),
        ("Servo Motor Control", servo_motor_control), 
        ("DC Motor Speed Control", motor_speed_control),
        ("Breathing LED Effect", breathing_led_effect),
        ("PWM Frequency Demo", pwm_frequency_demo),
        ("Interactive PWM Control", interactive_pwm_control),
    ]
    
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i}. {name}")
    print("0. Run all examples")
    
    try:
        choice = input("\nSelect example (0-6): ").strip()
        
        if choice == "0":
            # Run all examples except interactive
            for name, func in examples[:-1]:  # Skip interactive
                print(f"\n{'='*20}")
                func()
                input("\nPress Enter to continue to next example...")
                
        elif choice.isdigit() and 1 <= int(choice) <= len(examples):
            examples[int(choice) - 1][1]()
            
        else:
            print("Invalid choice")
            
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()