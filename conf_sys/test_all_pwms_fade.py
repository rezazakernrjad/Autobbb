#!/usr/bin/env python3
"""
Help identify which physical pins have PWM output
This script will activate each PWM channel one at a time
"""

from periphery import PWM
import time

def test_pwm_pin_mapping():
    """Test each PWM channel individually to help identify physical pins"""
    
    # All working PWM configurations from your test
    pwm_configs = [
        (0, 0),  # pwmchip0, channel 0
        (1, 0),  # pwmchip1, channel 0  
        (1, 1),  # pwmchip1, channel 1
        (2, 0),  # pwmchip2, channel 0
        (2, 1),  # pwmchip2, channel 1
        (3, 0),  # pwmchip3, channel 0
        (4, 0),  # pwmchip4, channel 0
        (4, 1),  # pwmchip4, channel 1
    ]
    
    # Common PWM pins to check on BeagleBone Black
    pins_to_check = [
        "P9_14", "P9_16",  # EHRPWM1A, EHRPWM1B
        "P8_19", "P8_13",  # EHRPWM2A, EHRPWM2B  
        "P9_31", "P9_29",  # EHRPWM0A, EHRPWM0B
        "P9_42", "P8_36",  # ECAP0, ECAP1
        "P8_07", "P8_08", "P8_09", "P8_10",  # Timer PWMs
    ]
    
    print("=" * 70)
    print("PWM PIN MAPPING TEST")
    print("=" * 70)
    print("This will activate each PWM channel for 10 seconds.")
    print("Use a multimeter, oscilloscope, or connect an LED to test pins.")
    print()
    print("Pins to check for PWM output:")
    for i, pin in enumerate(pins_to_check, 1):
        print(f"{i:2}. {pin}")
    print()
    
    for i, (chip, channel) in enumerate(pwm_configs):
        print(f"=" * 50)
        print(f"Test {i+1}/8: PWM Chip {chip}, Channel {channel}")
        print(f"=" * 50)
        
        try:
            # Initialize PWM for LED fading
            pwm = PWM(chip, channel)
            pwm.frequency = 1000  # 1kHz - good for LED fading
            pwm.duty_cycle = 0.0  # Start at 0%
            
            print(f"🔄 Activating pwmchip{chip}, channel {channel}...")
            pwm.enable()
            
            print("📍 Check these pins for PWM output:")
            print("   - Connect LED between pin and GND")  
            print("   - Use multimeter on AC voltage mode")
            print("   - Use oscilloscope for precise measurement")
            print()
            print("   Likely candidates based on chip number:")
            
            # Educated guesses based on typical BeagleBone mapping
            if chip == 0:
                print("   🎯 Try: P9_31 (EHRPWM0A)")
            elif chip == 1 and channel == 0:
                print("   🎯 Try: P9_29 (EHRPWM0B)")
            elif chip == 1 and channel == 1:
                print("   🎯 Try: P9_42 or timer pins (P8_07, P8_08, P8_09, P8_10)")
            elif chip == 2 and channel == 0:
                print("   🎯 Try: P9_14 (EHRPWM1A)")
            elif chip == 2 and channel == 1:  
                print("   🎯 Try: P9_16 (EHRPWM1B)")
            elif chip == 3:
                print("   🎯 Try: P8_19 (EHRPWM2A)")
            elif chip == 4 and channel == 0:
                print("   🎯 Try: P8_13 (EHRPWM2B)")
            elif chip == 4 and channel == 1:
                print("   🎯 Try: P8_36 (ECAP1) or timer pins")
            
            print()
            print("⏱️  PWM running for 10 seconds...")
            print("   You should see:")
            print("   - LED smoothly fading in and out 3 times")
            print("   - Brightness gradually changing from OFF → BRIGHT → OFF")
            print("   - Complete fade cycle takes about 3 seconds")
            print("   - Pattern repeats 3 times over 10 seconds")
            
            # LED fade pattern - much more obvious than static PWM
            print("   🔄 Starting LED fade pattern...")
            
            # Fade in and out 3 times over 10 seconds
            for cycle in range(3):
                print(f"\r   💡 Fade cycle {cycle+1}/3", end="", flush=True)
                
                # Fade in (0% to 100%)
                for brightness in range(0, 101, 5):
                    pwm.duty_cycle = brightness / 100.0
                    time.sleep(0.05)  # 50ms steps
                
                # Hold at full brightness briefly
                time.sleep(0.2)
                
                # Fade out (100% to 0%)  
                for brightness in range(100, -1, -5):
                    pwm.duty_cycle = brightness / 100.0
                    time.sleep(0.05)
                
                # Hold at off briefly
                time.sleep(0.2)
            
            print(f"\r   ✅ Test complete for pwmchip{chip}, channel {channel}     ")
            
            # Turn off PWM
            pwm.disable()
            pwm.close()
            
            # Ask user for results
            print()
            found_pin = input("❓ Which pin had PWM output? (or press Enter if none): ").strip().upper()
            
            if found_pin:
                print(f"✅ FOUND: pwmchip{chip}, channel {channel} → {found_pin}")
                
                # Save to file for reference
                with open("pwm_pin_mapping.txt", "a") as f:
                    f.write(f"pwmchip{chip}, channel {channel} → {found_pin}\n")
            else:
                print("❌ No PWM found on expected pins")
                
            print()
            
            # Ask if user wants to continue
            if i < len(pwm_configs) - 1:  # Not the last test
                continue_test = input("Continue to next PWM test? (y/n): ").strip().lower()
                if continue_test not in ['y', 'yes', '']:
                    break
                    
        except Exception as e:
            print(f"❌ Error testing pwmchip{chip}, channel {channel}: {e}")
            continue
    
    print("\n" + "=" * 50)
    print("PWM PIN MAPPING COMPLETE")
    print("=" * 50)
    
    # Show saved mappings
    try:
        with open("pwm_pin_mapping.txt", "r") as f:
            mappings = f.read().strip()
        if mappings:
            print("📝 Found PWM pin mappings:")
            print(mappings)
        else:
            print("❌ No PWM pin mappings found")
    except FileNotFoundError:
        print("❌ No PWM pin mappings saved")

def quick_test_specific_pins():
    """Quick test for specific pins that are most likely to work"""
    print("=" * 50)
    print("QUICK TEST - Most Likely PWM Pins")
    print("=" * 50)
    
    # Most likely mappings based on typical BeagleBone configuration
    likely_mappings = [
        (2, 0, "P9_14"),  # EHRPWM1A
        (2, 1, "P9_16"),  # EHRPWM1B
        (3, 0, "P8_19"),  # EHRPWM2A
        (4, 0, "P8_13"),  # EHRPWM2B
        (0, 0, "P9_31"),  # EHRPWM0A
        (1, 0, "P9_29"),  # EHRPWM0B
    ]
    
    print("Testing most common PWM pins...")
    print("Connect an LED between the pin and GND to see PWM output.")
    print()
    
    for chip, channel, expected_pin in likely_mappings:
        try:
            print(f"🔍 Testing {expected_pin} (should be pwmchip{chip}, channel {channel})")
            
            pwm = PWM(chip, channel)
            pwm.frequency = 2000  # 2kHz - more noticeable
            pwm.enable()
            
            # Smooth fade in/out pattern - very obvious
            print(f"   🔄 Running smooth LED fade on {expected_pin}...")
            print("   (LED should fade in and out smoothly)")
            
            # Smooth fade cycles - much more noticeable than breathing
            for cycle in range(2):  # 2 complete fade cycles
                # Fade in (0% to 100%)
                for brightness in range(0, 101, 2):
                    pwm.duty_cycle = brightness / 100.0
                    time.sleep(0.02)  # 20ms steps for smooth fade
                
                # Fade out (100% to 0%)
                for brightness in range(100, -1, -2):
                    pwm.duty_cycle = brightness / 100.0  
                    time.sleep(0.02)
                
                # Brief pause between cycles
                time.sleep(0.3)
            
            pwm.disable()
            pwm.close()
            
            result = input(f"   ❓ Did you see PWM on {expected_pin}? (y/n): ").strip().lower()
            if result in ['y', 'yes']:
                print(f"   ✅ CONFIRMED: {expected_pin} = pwmchip{chip}, channel {channel}")
            else:
                print(f"   ❌ No PWM seen on {expected_pin}")
            print()
            
        except Exception as e:
            print(f"   ❌ Error testing {expected_pin}: {e}")

def main():
    """Main function"""
    print("BeagleBone Black PWM Pin Finder")
    print("Choose test method:")
    print("1. Full systematic test (all 8 PWM channels)")
    print("2. Quick test (most likely pins only)")
    
    try:
        choice = input("Enter choice (1 or 2): ").strip()
        
        if choice == "1":
            test_pwm_pin_mapping()
        elif choice == "2":
            quick_test_specific_pins()
        else:
            print("Invalid choice")
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
