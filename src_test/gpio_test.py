#!/usr/bin/env python3
from periphery import GPIO
import time
import os

def test_pin_sysfs(gpio_num, name):
    """Test a GPIO pin using sysfs interface"""
    try:
        # Toggle using sysfs
        for i in range(3):
            print(f"\nTest {i+1}/3 (sysfs):")
            with open(f"/sys/class/gpio/gpio{gpio_num}/value", "w") as f:
                f.write("1")
            print(f"{name} -> HIGH (should see LED on or measure 3.3V)")
            time.sleep(1)
            with open(f"/sys/class/gpio/gpio{gpio_num}/value", "w") as f:
                f.write("0")
            print(f"{name} -> LOW (should see LED off or measure 0V)")
            time.sleep(1)
        
        # Cleanup
        try:
            with open("/sys/class/gpio/unexport", "w") as f:
                f.write(str(gpio_num))
        except:
            pass
        return True
    except Exception as e:
        print(f"❌ Error controlling GPIO {gpio_num}: {e}")
        return False

def read_gpio_info(chip_num):
    """Read GPIO chip information"""
    try:
        with open(f"/sys/class/gpio/gpiochip{chip_num}/ngpio") as f:
            ngpio = f.read().strip()
        with open(f"/sys/class/gpio/gpiochip{chip_num}/label") as f:
            label = f.read().strip()
        return f"Chip {chip_num}: {label} ({ngpio} GPIOs)"
    except Exception as e:
        return f"Error reading chip {chip_num}: {e}"

def test_pin(chip, line, name):
    try:
        print(f"\nAttempting to access {name} on {chip} line {line}")
        
        # Try both /dev/gpiochip* and direct sysfs access
        gpio_num = None
        if chip.startswith("/dev/gpiochip"):
            gpio_num = int(chip.replace("/dev/gpiochip", "")) + line
            
        # Try direct sysfs export if device node doesn't exist
        if not os.path.exists(chip):
            print(f"Device {chip} not found, trying sysfs interface...")
            if gpio_num is not None:
                try:
                    # Export GPIO
                    if not os.path.exists(f"/sys/class/gpio/gpio{gpio_num}"):
                        with open("/sys/class/gpio/export", "w") as f:
                            f.write(str(gpio_num))
                    # Set direction
                    with open(f"/sys/class/gpio/gpio{gpio_num}/direction", "w") as f:
                        f.write("out")
                    print(f"✅ Exported GPIO {gpio_num} via sysfs")
                    return test_pin_sysfs(gpio_num, name)
                except Exception as e:
                    print(f"❌ Sysfs export failed: {e}")
                    return False
            return False
            
        pin = GPIO(chip, line, "out")
        print(f"✅ Successfully opened {name} on {chip} line {line}")
        
        # Test toggle with verification
        for i in range(3):
            print(f"\nTest {i+1}/3:")
            pin.write(True)
            print(f"{name} -> HIGH (should see LED on or measure 3.3V)")
            time.sleep(1)
            pin.write(False)
            print(f"{name} -> LOW (should see LED off or measure 0V)")
            time.sleep(1)
            
        pin.close()
        return True
    except Exception as e:
        print(f"❌ Error with {name} on {chip} line {line}: {e}")
        if "Permission denied" in str(e):
            print("💡 Try running with sudo")
        elif "Device or resource busy" in str(e):
            print("💡 Pin might be in use by another process or kernel driver")
        return False

# Print GPIO chip information
print("GPIO Chip Information:")
for chip_num in range(4):  # gpiochip0 through gpiochip3
    try:
        with open(f"/sys/class/gpio/gpiochip{chip_num}/ngpio") as f:
            ngpio = f.read().strip()
        with open(f"/sys/class/gpio/gpiochip{chip_num}/label") as f:
            label = f.read().strip()
        with open(f"/sys/class/gpio/gpiochip{chip_num}/base") as f:
            base = f.read().strip()
        print(f"Chip {chip_num}: {label} (base: {base}, {ngpio} GPIOs)")
    except Exception as e:
        print(f"Error reading chip {chip_num}: {e}")

# BeagleBone Black P8_11 and P8_16 mapping
# P8_11 is GPIO1_13 (chip 1, line 13)
# P8_16 is GPIO1_14 (chip 1, line 14)

print("\nChecking GPIO permissions...")
for path in ["/dev/gpiochip1", "/sys/class/gpio/export", "/sys/class/gpio"]:
    try:
        print(f"Access to {path}: ", end="")
        if os.path.exists(path):
            print("exists, ", end="")
            if os.access(path, os.R_OK):
                print("readable, ", end="")
            if os.access(path, os.W_OK):
                print("writable")
            else:
                print("not writable")
        else:
            print("does not exist")
    except Exception as e:
        print(f"error: {e}")

chips = ["/dev/gpiochip1"]  # Start with GPIO1
backup_chips = ["/dev/gpiochip0", "/dev/gpiochip2", "/dev/gpiochip3"]

# Test P8_11 first
print("\nTesting P8_11 (expected: chip 544, line 13)...")
if not test_pin("/dev/gpiochip544", 13, "P8_11"):
    print("\nTrying backup chips for P8_11...")
    for chip in backup_chips:
        if test_pin(chip, 13, "P8_11"):
            print(f"✅ Found alternate working configuration for P8_11: {chip}")
            break

# Test P8_16
print("\nTesting P8_16 (expected: chip 544, line 14)...")
if not test_pin("/dev/gpiochip544", 14, "P8_16"):
    print("\nTrying backup configurations for P8_16...")
    # Try other likely line numbers on chip 544
    likely_lines = [14, 46, 78]
    for line in likely_lines:
        if test_pin("/dev/gpiochip544", line, "P8_16"):
            print(f"✅ Found working configuration for P8_16 on alternate line")
            break
    else:
        # Try other chips
        print("\nTrying other GPIO chips for P8_16...")
        for chip in backup_chips:
            for line in likely_lines:
                if test_pin(chip, line, "P8_16"):
                    print(f"✅ Found working configuration for P8_16")
                    break