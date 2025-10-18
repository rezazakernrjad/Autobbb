#!/usr/bin/env python3
"""
Hardcoded PWM Controllers for BeagleBone Black
Direct control of specific PWM pins: P9_14, P8_13, P8_19
Simplified version with dedicated controllers for each pin
"""

import os
import time
import math

class PWMController:
    """Direct PWM control with hardcoded pin configurations"""
    
    def __init__(self):
        # Hardcoded PWM configurations
        self.p9_14 = PWMPin("P9_14", chip=0, channel=0)  # PWM0.0
        self.p8_13 = PWMPin("P8_13", chip=1, channel=1)  # PWM1.1  
        self.p8_19 = PWMPin("P8_19", chip=1, channel=0)  # PWM1.0
        
        self.pins = [self.p9_14, self.p8_13, self.p8_19]
        self.frequency = 1000  # 1kHz default
        
    def start_all(self, frequency=None):
        """Start all PWM pins"""
        freq = frequency or self.frequency
        success_count = 0
        
        print(f"🚀 Starting hardcoded PWM pins at {freq}Hz...")
        
        for pin in self.pins:
            if pin.start(freq):
                success_count += 1
        
        print(f"✅ {success_count}/{len(self.pins)} pins started")
        return success_count > 0
    
    def set_p9_14_duty(self, percent):
        """Set duty cycle for P9_14"""
        return self.p9_14.set_duty_cycle(percent)
    
    def set_p8_13_duty(self, percent):
        """Set duty cycle for P8_13"""
        return self.p8_13.set_duty_cycle(percent)
    
    def set_p8_19_duty(self, percent):
        """Set duty cycle for P8_19"""
        return self.p8_19.set_duty_cycle(percent)
    
    def set_all_duty(self, percent):
        """Set same duty cycle for all pins"""
        success_count = 0
        for pin in self.pins:
            if pin.is_active and pin.set_duty_cycle(percent):
                success_count += 1
        return success_count
    
    def stop_all(self):
        """Stop all PWM pins"""
        for pin in self.pins:
            pin.stop()
        print("⏹️ All PWM pins stopped")
    
    def get_active_pins(self):
        """Get list of active pin names"""
        return [pin.name for pin in self.pins if pin.is_active]
    
    def set_pin_9_14(self, duration=20, key=""):
        """Demo: Control each pin individually"""
        print(f"\n🎭 Demo: Individual Pin Control ({key})")
        print("  💡 Fading P9_14...")
        print("Message ", key)
        if key == "lamps":
            steps = 30
            step_time = duration / (steps * 3 * 2)  # 3 pins, fade up and down
            self.set_p9_14_duty(100)  # Start fully on
            time.sleep(0.2)
            self.set_p9_14_duty(0)    # Then off
            time.sleep(0.2)
            self.set_p9_14_duty(100)  # Start fully on
            time.sleep(0.2)
            self.set_p9_14_duty(0)    # Then off
            time.sleep(0.5)
            # P9_14 fade
            for i in range(steps + 1):
                duty = int(i * 100 / steps)
                self.set_p9_14_duty(duty)
                time.sleep(step_time)
            for i in range(steps, -1, -1):
                duty = int(i * 100 / steps)
                self.set_p9_14_duty(duty)
                time.sleep(step_time)

    def set_pin_8_13 (self, side, duty):
        print("Control PIN8_13", side)
        self.set_p8_13_duty(duty)

    def set_pin_8_19 (self, side, duty):
        print("Control PIN8_19", side)
        self.set_p8_19_duty(duty)

    def dance(self):
        try:
            print("Dance in pwm...")
            self.set_p8_13_duty(100)
            time.sleep(0.05)
            self.set_p8_19_duty(100)
            time.sleep(0.2)
            self.set_p8_13_duty(0)
            time.sleep(0.1)
            self.set_p8_19_duty(50)
            time.sleep(0.2)
            self.set_p8_13_duty(100)
            time.sleep(0.05)
            self.set_p8_19_duty(100)
            time.sleep(0.1)
            self.set_p8_13_duty(50)
            time.sleep(0.05)
            self.set_p8_19_duty(50)
            time.sleep(0.5)
            self.set_p8_13_duty(0)
            time.sleep(0.05)
            self.set_p8_19_duty(0)
        except Exception as e:
            print(f"\n BLE faled: {e}")
    def start_pwm(self):
        try:
            # Start all pins
            if not self.start_all(frequency=1000):
                print("❌ Failed to start PWM pins")
                return
            
            active = self.get_active_pins()
            print(f"🎯 Active pins: {', '.join(active)}")
            
            if not active:
                print("❌ No PWM pins are active")
                return
        except KeyboardInterrupt:
            print("\n⏹️ Demo interrupted by user")
        
        except Exception as e:
            print(f"\n❌ Demo error: {e}")

class PWMPin:
    """Individual PWM pin controller"""
    
    def __init__(self, name, chip, channel):
        self.name = name
        self.chip = chip
        self.channel = channel
        self.is_active = False
        self.pwm_path = None
        self.chip_path = None
        self.period_ns = None
    
    def start(self, frequency):
        """Start this PWM pin"""
        try:
            self.pwm_path = f"/sys/class/pwm/pwmchip{self.chip}/pwm{self.channel}"
            self.chip_path = f"/sys/class/pwm/pwmchip{self.chip}"
            
            # Export if needed
            if not os.path.exists(self.pwm_path):
                with open(f"{self.chip_path}/export", "w") as f:
                    f.write(str(self.channel))
                time.sleep(0.1)
            
            # Configure period
            self.period_ns = int(1000000000 / frequency)
            with open(f"{self.pwm_path}/period", "w") as f:
                f.write(str(self.period_ns))
            
            # Set initial duty cycle to 0
            with open(f"{self.pwm_path}/duty_cycle", "w") as f:
                f.write("0")
            
            # Enable PWM
            with open(f"{self.pwm_path}/enable", "w") as f:
                f.write("1")
            
            self.is_active = True
            print(f"✅ {self.name} PWM initialized: {frequency}Hz")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup {self.name}: {e}")
            return False
    
    def set_duty_cycle(self, percent):
        """Set duty cycle for this pin"""
        if not self.is_active:
            return False
        
        try:
            duty_ns = int(self.period_ns * max(0, min(100, percent)) / 100)
            with open(f"{self.pwm_path}/duty_cycle", "w") as f:
                f.write(str(duty_ns))
            return True
            
        except Exception as e:
            print(f"❌ Error setting {self.name} duty cycle: {e}")
            return False
    
    def stop(self):
        """Stop this PWM pin"""
        if not self.is_active:
            return
        
        try:
            # Set duty cycle to 0
            with open(f"{self.pwm_path}/duty_cycle", "w") as f:
                f.write("0")
            
            # Disable PWM
            with open(f"{self.pwm_path}/enable", "w") as f:
                f.write("0")
            
            # Unexport
            with open(f"{self.chip_path}/unexport", "w") as f:
                f.write(str(self.channel))
            
            self.is_active = False
            print(f"⏹️ {self.name} PWM stopped")
            
        except Exception as e:
            print(f"❌ Error stopping {self.name}: {e}")
