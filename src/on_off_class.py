from periphery import GPIO
import time

# P9_12 is gpiochip0, line 28

class ParentOnOff:
    def __init__(self, chip_name, line, direction):
        print("*************c1")
        self.P9_12 = GPIO(chip_name, line, direction)
        print("*************c2")
    def start(self):
        try:
            while True:
                # Set the line value to 1 (High)
                self.P9_12.write(True)
                time.sleep(0.7)
                print("ACTIVE")
                # Set the line value to 0 (Low)
                self.P9_12.write(False)
                time.sleep(0.6)
                print("INACTIVE")
        except KeyboardInterrupt:
            print("\nStopping...")
            self.P9_12.close()
        except Exception as e:
            print(f"Error: {e}")
            self.P9_12.close()

    # except KeyboardInterrupt:
    #     print("\nExiting.")
    #     # The 'with' block will automatically release the line.