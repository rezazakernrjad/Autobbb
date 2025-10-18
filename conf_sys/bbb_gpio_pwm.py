# bbb_gpio_pwm.py
import time
from pathlib import Path

# BBB pin → Linux GPIO number mapping
PIN_TO_GPIO = {
    "P8_03": 38, "P8_04": 39, "P8_05": 34, "P8_06": 35,
    "P8_07": 66, "P8_08": 67, "P8_09": 69, "P8_10": 68,
    "P8_11": 45, "P8_12": 44, "P8_13": 23, "P8_14": 26,
    "P8_15": 47, "P8_16": 46, "P8_17": 27, "P8_18": 65,
    "P8_19": 22, "P8_20": 63, "P8_21": 62, "P8_22": 37,
    "P8_23": 36, "P8_24": 33, "P8_25": 32, "P8_26": 61,
    "P8_27": 86, "P8_28": 88, "P8_29": 87, "P8_30": 89,
    "P9_11": 30, "P9_12": 60, "P9_13": 31, "P9_14": 50,
    "P9_15": 48, "P9_16": 51, "P9_17": 5,  "P9_18": 4,
    "P9_19": 13, "P9_20": 12, "P9_21": 3,  "P9_22": 2,
    "P9_23": 49, "P9_24": 15, "P9_25": 117,"P9_26": 14,
    "P9_27": 115,"P9_30": 112,"P9_41": 20,"P9_42": 7
}

# --------------------------
# GPIO Handling
# --------------------------
def export_gpio(pin):
    gpio_num = PIN_TO_GPIO[pin]
    gpio_path = Path(f"/sys/class/gpio/gpio{gpio_num}")
    if not gpio_path.exists():
        try:
            Path("/sys/class/gpio/export").write_text(str(gpio_num))
            time.sleep(0.1)
        except OSError as e:
            print(f"Could not export GPIO {gpio_num}: {e}")
    return gpio_path

def set_gpio_direction(pin, direction="out"):
    gpio_path = export_gpio(pin)
    (gpio_path / "direction").write_text(direction)

def gpio_write(pin, value):
    gpio_path = export_gpio(pin)
    (gpio_path / "value").write_text("1" if value else "0")

def gpio_read(pin):
    gpio_path = export_gpio(pin)
    return int((gpio_path / "value").read_text().strip())

# --------------------------
# PWM Handling
# --------------------------
def pwm_enable(pwmchip, pwm_channel, period_ns=20000000, duty_cycle_ns=1500000):
    pwm_base = Path(f"/sys/class/pwm/pwmchip{pwmchip}")
    pwm_path = pwm_base / f"pwm{pwm_channel}"

    if not pwm_path.exists():
        Path(pwm_base / "export").write_text(str(pwm_channel))
        time.sleep(0.1)

    (pwm_path / "period").write_text(str(period_ns))
    (pwm_path / "duty_cycle").write_text(str(duty_cycle_ns))
    (pwm_path / "enable").write_text("1")
    return pwm_path

def pwm_disable(pwmchip, pwm_channel):
    pwm_path = Path(f"/sys/class/pwm/pwmchip{pwmchip}/pwm{pwm_channel}")
    if pwm_path.exists():
        (pwm_path / "enable").write_text("0")

def pwm_set_duty(pwmchip, pwm_channel, duty_cycle_ns):
    pwm_path = Path(f"/sys/class/pwm/pwmchip{pwmchip}/pwm{pwm_channel}")
    (pwm_path / "duty_cycle").write_text(str(duty_cycle_ns))
