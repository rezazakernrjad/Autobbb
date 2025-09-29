#!/usr/bin/env python3
"""
Test all available PWM chips on BeagleBone Black
Find which chips and channels work
"""

from periphery import PWM
import time
import os

def get_available_pwm_chips():
    """Get list of available PWM chips"""
    pwm_chips = []
    pwm_dir = "/sys/class/pwm"
    
    if os.path.exists(pwm_dir):
        for item in os.listdir(pwm_dir):
            if item.startswith("pwmchip"):
                chip_num = int(item.replace("pwmchip", ""))
                
                # Get number of channels
                try:
                    with open(f"{pwm_dir}/{item}/npwm", "r") as f:
                        channels = int(f.read().strip())
                except:
                    channels = 1  # Default assumption
                    
                pwm_chips.append((chip_num, channels))
                
    return sorted(pwm_chips)

def test_pwm_chip_channel(chip_num, channel):
    """Test a specific PWM chip and channel"""
    try:
        print(f"  Testing pwmchip{chip_num}, channel {channel}...", end=" ")
        
        # Initialize PWM
        pwm = PWM(chip_num, channel)
        
        # Configure PWM
        pwm.frequency = 1000  # 1kHz
        pwm.duty_cycle = 0.5  # 50%
        
        # Enable PWM
        pwm.enable()
        
        # Quick test - change duty cycle
        pwm.duty_cycle = 0.25
        time.sleep(0.1)
        pwm.duty_cycle = 0.75
        time.sleep(0.1)
        pwm.duty_cycle = 0.5
        
        # Disable and close
        pwm.disable()
        pwm.close()
        
        print("✅ WORKING")
        return True
        
    except Exception as e:
        print(f"❌ FAILED ({str(e)[:50]}...)")
        return False

def identify_pwm_pins():
    """Try to identify which pins correspond to which PWM chips"""
    print("\n=== PWM Pin Identification ===")
    print("BeagleBone Black PWM pins are typically:")
    print("P9_14 (EHRPWM1A), P9_16 (EHRPWM1B)")  
    print("P8_19 (EHRPWM2A), P8_13 (EHRPWM2B)")
    print("P9_31 (EHRPWM0A), P9_29 (EHRPWM0B)")
    print("\nWith 5 PWM chips, you likely have access to multiple PWM subsystems!")

def demonstrate_working_pwm(working_configs):
    """Demonstrate PWM functionality with working configurations"""
    if not working_configs:
        print("\n❌ No working PWM configurations found!")
        return
        
    print(f"\n=== PWM Demonstration ===")
    print(f"Using first working configuration: pwmchip{working_configs[0][0]}, channel {working_configs[0][1]}")
    
    chip, channel = working_configs[0]
    
    try:
        pwm = PWM(chip, channel)
        pwm.frequency = 1000
        pwm.enable()
        
        print("Running LED brightness demo...")
        
        # Breathing effect
        import math
        for i in range(100):
            # Sine wave brightness
            brightness = (math.sin(i * 0.0628) + 1) / 2  # 0 to 1
            pwm.duty_cycle = brightness
            time.sleep(0.05)
            
        pwm.disable()
        pwm.close()
        
        print("✅ PWM demonstration completed!")
        
    except Exception as e:
        print(f"❌ Demonstration failed: {e}")

def create_pwm_mapping_table(working_configs):
    """Create a reference table of working PWM configurations"""
    print("\n=== Your Working PWM Configurations ===")
    print("Chip   | Channel | Status | Recommended Use")
    print("-------|---------|--------|------------------")
    
    for chip, channel in working_configs:
        uses = [
            "LED control", "Motor speed", "Servo control", 
            "Audio generation", "Dimming", "Signal generation"
        ]
        recommended = uses[min(len(working_configs)-1, len(uses)-1)]
        print(f"pwmchip{chip:<2} | {channel:<7} | ✅ OK   | {recommended}")
        
    print("\n=== Usage Example ===")
    if working_configs:
        chip, channel = working_configs[0]
        print(f"""
from periphery import PWM

# Initialize PWM
pwm = PWM({chip}, {channel})
pwm.frequency = 1000  # 1kHz
pwm.duty_cycle = 0.5  # 50%
pwm.enable()

# Your PWM is now running!
# Change duty cycle: pwm.duty_cycle = 0.25
# Change frequency: pwm.frequency = 2000

# Clean up when done
pwm.disable()
pwm.close()
        """)

def main():
    """Main PWM testing function"""
    print("=" * 60)
    print("BeagleBone Black PWM Chip Testing")
    print("=" * 60)
    
    # Get available PWM chips
    pwm_chips = get_available_pwm_chips()
    
    if not pwm_chips:
        print("❌ No PWM chips found!")
        return
        
    print(f"Found {len(pwm_chips)} PWM chips:")
    for chip_num, channels in pwm_chips:
        print(f"  pwmchip{chip_num}: {channels} channel{'s' if channels != 1 else ''}")
    
    print(f"\n=== Testing PWM Functionality ===")
    
    working_configs = []
    
    # Test each chip and channel
    for chip_num, channels in pwm_chips:
        print(f"\nTesting pwmchip{chip_num}:")
        
        for channel in range(channels):
            if test_pwm_chip_channel(chip_num, channel):
                working_configs.append((chip_num, channel))
    
    # Summary
    print(f"\n=== Test Results ===")
    print(f"Total PWM chips: {len(pwm_chips)}")
    print(f"Working configurations: {len(working_configs)}")
    
    if working_configs:
        print("✅ Working PWM configs:")
        for chip, channel in working_configs:
            print(f"  - pwmchip{chip}, channel {channel}")
    else:
        print("❌ No working PWM configurations found!")
        return
    
    # Identify pins
    identify_pwm_pins()
    
    # Create mapping table
    create_pwm_mapping_table(working_configs)
    
    # Ask user if they want a demo
    try:
        demo = input(f"\nRun PWM demonstration? (y/n): ").strip().lower()
        if demo in ['y', 'yes']:
            demonstrate_working_pwm(working_configs)
    except KeyboardInterrupt:
        print("\nExiting...")
    
    print(f"\n🎉 You have {len(working_configs)} working PWM channels available!")
    print("Use any of the working configurations for your PWM projects.")

if __name__ == "__main__":
    main()
