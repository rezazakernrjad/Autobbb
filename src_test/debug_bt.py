# debug_bt.py
from bt_lib import BT

def test_callback(value, options):
    print("🎉 CALLBACK WORKED!")
    print(f"   Value: {value}")
    print(f"   Options: {options}")

# Test if callback works when called directly
print("Testing callback directly...")
test_callback([72, 101, 108, 108, 111], {})  # "Hello" in ASCII

# Test with your BT class
bt = BT()
print("\nTesting BT class callback...")
bt.rx_write_cb([102, 111, 114, 119, 97, 114, 100, 32, 53, 48], {})  # "forward 50"
