#!/usr/bin/env python3
"""
Multi-Channel Hardware PWM Example for BeagleBone Black
Demonstrates controlling multiple PWM channels simultaneously
Based on actual pin mappings discovered through testing
"""

import os
import time
import threading

class MultiChannelPWM:
    """Control multiple hardware PWM channels simultaneously"""
    
    def __init__(self):
        # Actual pin mappings from detective work
        self.channels = {
            "P9_14": {"chip": 0, "channel": 0, "pwm": None, "active": False},
            "P8_19": {"chip": 1, "channel": 0, "pwm": None, "active": False}, 
            "P8_13": {"chip": 1, "channel": 1, "pwm": None, "active": False},
        }
        
        self.frequency = 1000  # 1kHz default
        
    def _setup_pwm_channel(self, pin_name, frequency=None):
        """Setup a single PWM channel"""
        if pin_name not in self.channels:
            return False
            
        channel_info = self.channels[pin_name]
        chip = channel_info["chip"]
        channel = channel_info["channel"]
        freq = frequency or self.frequency
        
        try:
            pwm_path = f"/sys/class/pwm/pwmchip{chip}/pwm{channel}"
            chip_path = f"/sys/class/pwm/pwmchip{chip}"
            
            # Export if needed
            if not os.path.exists(pwm_path):
                with open(f"{chip_path}/export", "w") as f:
                    f.write(str(channel))
                time.sleep(0.1)
            
            # Configure period
            period_ns = int(1000000000 / freq)
            with open(f"{pwm_path}/period", "w") as f:
                f.write(str(period_ns))
            
            # Set initial duty cycle to 0
            with open(f"{pwm_path}/duty_cycle", "w") as f:
                f.write("0")
            
            # Enable PWM
            with open(f"{pwm_path}/enable", "w") as f:
                f.write("1")
            
            # Store PWM info
            channel_info["pwm"] = {
                "path": pwm_path,
                "chip_path": chip_path,
                "period_ns": period_ns
            }
            channel_info["active"] = True
            
            print(f"✅ {pin_name} PWM initialized: {freq}Hz")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup {pin_name}: {e}")
            return False
    
    def start_channel(self, pin_name, frequency=None):
        """Start PWM on a specific channel"""
        return self._setup_pwm_channel(pin_name, frequency)
    
    def start_all_channels(self, frequency=None):
        """Start PWM on all available channels"""
        freq = frequency or self.frequency
        success_count = 0
        
        print(f"🚀 Starting all PWM channels at {freq}Hz...")
        
        for pin_name in self.channels.keys():
            if self.start_channel(pin_name, freq):
                success_count += 1
        
        print(f"✅ {success_count}/{len(self.channels)} channels started")
        return success_count > 0
    
    def set_duty_cycle(self, pin_name, percent):
        """Set duty cycle for a specific channel"""
        if pin_name not in self.channels or not self.channels[pin_name]["active"]:
            return False
        
        try:
            pwm_info = self.channels[pin_name]["pwm"]
            duty_ns = int(pwm_info["period_ns"] * max(0, min(100, percent)) / 100)
            
            with open(f"{pwm_info['path']}/duty_cycle", "w") as f:
                f.write(str(duty_ns))
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting {pin_name} duty cycle: {e}")
            return False
    
    def set_all_duty_cycles(self, percent):
        """Set same duty cycle for all active channels"""
        success_count = 0
        for pin_name, channel_info in self.channels.items():
            if channel_info["active"]:
                if self.set_duty_cycle(pin_name, percent):
                    success_count += 1
        return success_count
    
    def stop_channel(self, pin_name):
        """Stop PWM on a specific channel"""
        if pin_name not in self.channels or not self.channels[pin_name]["active"]:
            return
        
        try:
            channel_info = self.channels[pin_name]
            pwm_info = channel_info["pwm"]
            
            # Set duty cycle to 0
            with open(f"{pwm_info['path']}/duty_cycle", "w") as f:
                f.write("0")
            
            # Disable PWM
            with open(f"{pwm_info['path']}/enable", "w") as f:
                f.write("0")
            
            # Unexport
            with open(f"{pwm_info['chip_path']}/unexport", "w") as f:
                f.write(str(channel_info["channel"]))
            
            channel_info["active"] = False
            print(f"⏹️ {pin_name} PWM stopped")
            
        except Exception as e:
            print(f"❌ Error stopping {pin_name}: {e}")
    
    def stop_all_channels(self):
        """Stop all PWM channels"""
        for pin_name in self.channels.keys():
            self.stop_channel(pin_name)
        print("⏹️ All PWM channels stopped")
    
    def get_active_channels(self):
        """Get list of active channel names"""
        return [pin for pin, info in self.channels.items() if info["active"]]

# Demo functions
def demo_synchronized_fade(pwm_controller, duration=10):
    """Demo: All channels fade in sync"""
    print(f"\n🎭 Demo: Synchronized Fade ({duration}s)")
    print("All LEDs should fade up and down together")
    
    steps = 50
    step_time = duration / (steps * 2)
    
    # Fade up
    for i in range(steps + 1):
        duty = int(i * 100 / steps)
        pwm_controller.set_all_duty_cycles(duty)
        time.sleep(step_time)
    
    # Fade down
    for i in range(steps, -1, -1):
        duty = int(i * 100 / steps)
        pwm_controller.set_all_duty_cycles(duty)
        time.sleep(step_time)

def demo_sequential_fade(pwm_controller, duration=12):
    """Demo: Channels fade one after another"""
    print(f"\n🎭 Demo: Sequential Fade ({duration}s)")
    print("LEDs should fade one after another in sequence")
    
    active_channels = pwm_controller.get_active_channels()
    if not active_channels:
        print("❌ No active channels for demo")
        return
    
    channel_time = duration / len(active_channels)
    steps = 30
    step_time = channel_time / (steps * 2)
    
    for pin_name in active_channels:
        print(f"  💡 Fading {pin_name}")
        
        # Fade up this channel
        for i in range(steps + 1):
            duty = int(i * 100 / steps)
            pwm_controller.set_duty_cycle(pin_name, duty)
            time.sleep(step_time)
        
        # Fade down this channel
        for i in range(steps, -1, -1):
            duty = int(i * 100 / steps)
            pwm_controller.set_duty_cycle(pin_name, duty)
            time.sleep(step_time)

def demo_wave_pattern(pwm_controller, duration=15):
    """Demo: Wave pattern across channels"""
    print(f"\n🎭 Demo: Wave Pattern ({duration}s)")
    print("LEDs should create a wave/breathing pattern")
    
    active_channels = pwm_controller.get_active_channels()
    if len(active_channels) < 2:
        print("❌ Need at least 2 channels for wave demo")
        return
    
    import math
    
    steps = int(duration * 10)  # 10 steps per second
    
    for step in range(steps):
        t = step / 10.0  # Time in seconds
        
        for i, pin_name in enumerate(active_channels):
            # Create phase-shifted sine waves
            phase = (i * 2 * math.pi) / len(active_channels)
            duty = int(50 + 45 * math.sin(t * 2 + phase))  # 5-95% range
            pwm_controller.set_duty_cycle(pin_name, duty)
        
        time.sleep(0.1)
    
    # Return to off
    pwm_controller.set_all_duty_cycles(0)

def main():
    print("🌈 Multi-Channel Hardware PWM Demo")
    print("==================================")
    print("This demo controls multiple PWM channels simultaneously")
    print()
    print("📋 Hardware Setup:")
    print("  - Connect LEDs (with 220Ω resistors) to:")
    print("    • P9_14 (PWM0.0)")
    print("    • P8_19 (PWM1.0)") 
    print("    • P8_13 (PWM1.1)")
    print()
    
    # Create multi-channel PWM controller
    pwm = MultiChannelPWM()
    
    try:
        # Start all available channels
        if not pwm.start_all_channels(frequency=1000):
            print("❌ Failed to start PWM channels")
            return
        
        active = pwm.get_active_channels()
        print(f"🎯 Active channels: {', '.join(active)}")
        
        if not active:
            print("❌ No PWM channels are active")
            return
        
        # Run demos
        print("\n🎬 Starting PWM demos...")
        
        # Demo 1: Synchronized fade
        demo_synchronized_fade(pwm, duration=8)
        time.sleep(2)
        
        # Demo 2: Sequential fade
        demo_sequential_fade(pwm, duration=10)
        time.sleep(2)
        
        # Demo 3: Wave pattern
        demo_wave_pattern(pwm, duration=12)
        
        print("\n✅ All demos complete!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted by user")
    
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
    
    finally:
        # Always cleanup
        pwm.stop_all_channels()
        print("\n👋 Multi-channel PWM demo finished!")

if __name__ == "__main__":
    main()
