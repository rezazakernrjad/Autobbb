import gpiod
import time

# Define the GPIO chip and line number for pin P9_12 (gpio1[28])
GPIO_CHIP = '/dev/gpiochip1' # The fix is here: provide the full path
LED_LINE_OFFSET = 28

# The 'with' statement handles opening and closing the line securely
with gpiod.request_lines(
    GPIO_CHIP,
    consumer="my-led-script",
    config={
        LED_LINE_OFFSET: gpiod.LineSettings(
            direction=gpiod.line.Direction.OUTPUT
        )
    }
) as lines:
    print(f"Blinking LED on {GPIO_CHIP} line {LED_LINE_OFFSET}...")
    try:
        while True:
            # Set the line value to 1 (High)
            lines.set_values({LED_LINE_OFFSET: gpiod.line.Value.ACTIVE})
            time.sleep(0.7)
            print("ACTIVE")
            # Set the line value to 0 (Low)
            lines.set_values({LED_LINE_OFFSET: gpiod.line.Value.INACTIVE})
            time.sleep(0.6)
            print("INACTIVE")
    except KeyboardInterrupt:
        print("\nExiting.")
        # The 'with' block will automatically release the line.
