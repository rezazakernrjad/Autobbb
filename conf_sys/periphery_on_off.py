from periphery import GPIO
import time

# P9_12 is gpiochip0, line 28
gpio = GPIO("/dev/gpiochip0", 28, "out")

try:
    # Blink 5 times
    for i in range(500):
        print(f"Blink {i+1}: ON")
        gpio.write(True)
        time.sleep(1)  # 1 second delay
        
        print(f"Blink {i+1}: OFF") 
        gpio.write(False)
        time.sleep(1)  # 1 second delay
        
    print("Blinking complete")
    
finally:
    gpio.close()
