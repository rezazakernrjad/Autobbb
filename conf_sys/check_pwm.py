import os

# Check what PWM chips are available
pwm_path = "/sys/class/pwm"
print("Available PWM chips:")

for item in os.listdir(pwm_path):
    if item.startswith("pwmchip"):
        chip_path = os.path.join(pwm_path, item)
        try:
            with open(os.path.join(chip_path, "npwm"), "r") as f:
                channels = f.read().strip()
            print(f"{item}: {channels} channels")
        except:
            pass
