#!/usr/bin/env python3
import subprocess
from pathlib import Path
import time

def list_gpiochips():
    """Return a list of all gpiochip paths"""
    return sorted(Path("/sys/class/gpio").glob("gpiochip*"))

def gpio_lines(chip_path):
    """Return list of lines for a given gpiochip"""
    nlines = int((chip_path / "ngpio").read_text())
    base = int(chip_path.name.replace("gpiochip", ""))
    return [base + i for i in range(nlines)]

def export_gpio(gpio_num):
    gpio_path = Path(f"/sys/class/gpio/gpio{gpio_num}")
    if not gpio_path.exists():
        try:
            Path("/sys/class/gpio/export").write_text(str(gpio_num))
            time.sleep(0.1)
        except OSError as e:
            print(f"Could not export GPIO {gpio_num}: {e}")
    return gpio_path

def set_gpio_direction(gpio_num, direction="out"):
    gpio_path = export_gpio(gpio_num)
    (gpio_path / "direction").write_text(direction)

def gpio_write(gpio_num, value):
    gpio_path = export_gpio(gpio_num)
    (gpio_path / "value").write_text("1" if value else "0")

def gpio_read(gpio_num):
    gpio_path = export_gpio(gpio_num)
    return int((gpio_path / "value").read_text().strip())

def config_pin_to_gpio(pin_name):
    """Use config-pin to set a pin as GPIO and return its linux gpio number"""
    subprocess.run(["sudo", "config-pin", pin_name, "gpio"], check=True)
    # Wait a bit for sysfs to create gpio
    time.sleep(0.1)
    # Check for new gpio in /sys/class/gpio
    exported = [p.name for p in Path("/sys/class/gpio").glob("gpio*") if p.name.startswith("gpio") and p.name != "export" and p.name != "unexport"]
    if exported:
        # Return the highest number (likely the new pin)
        return max([int(p.replace("gpio","")) for p in exported])
    else:
        raise RuntimeError(f"No GPIO appeared after config-pin {pin_name} gpio")

# Example usage
if __name__ == "__main__":
    print("GPIO chips detected:")
    for chip in list_gpiochips():
        print(chip, gpio_lines(chip))

    # Example: configure P9_12
    try:
        gpio_num = config_pin_to_gpio("P9_12")
        print(f"P9_12 is now GPIO {gpio_num}")
        set_gpio_direction(gpio_num, "out")
        gpio_write(gpio_num, 1)
        time.sleep(1)
        gpio_write(gpio_num, 0)
    except Exception as e:
        print(e)
