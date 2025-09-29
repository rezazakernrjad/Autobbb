# combination of pin_lib, bt_lib and auto_run receive message via bluetooth
# and control P9_14.

from bluezero import peripheral
import signal

class BT:
    def __init__(self):
        # UUIDs
        self.SERVICE_UUID = '6E400001-B5A3-F393-E0A9-E50E24DCCA9E'
        self.RX_UUID      = '6E400002-B5A3-F393-E0A9-E50E24DCCA9E'
        self.ble_periph = None
        self.pin_control = None  # For custom data processing function
        self.pwma_control = None
        self.pwmb_control = None
        self.duty = None
        
    def rx_write_cb(self, value, options):
        print("Received:", value.decode())
        # Process your data here directly
        self.process_received_data(value.decode())
    
    def process_received_data(self, message):
        """Process the received data - use custom processor if available"""
        print(f"Custom pin control executed for message: {message}")
        parts = message.split()
        key = parts[0]
        value = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None

        if self.pin_control:
            # Use custom processor functions
            if key == "pwma":
                self.pwma_control(20, key)
            elif key == "pwmb":
                self.pwmb_control(value, key)
            elif key == "pin":
                self.pin_control(value)

    def start_server(self):
        # Create Peripheral
        self.ble_periph = peripheral.Peripheral(adapter_address='EC:75:0C:F7:12:43',
                                                local_name='BBB-PosServer')
        # Add service
        self.ble_periph.add_service(srv_id=0, uuid=self.SERVICE_UUID, primary=True)

        # Add RX characteristic (write)
        self.ble_periph.add_characteristic(srv_id=0,
                                    chr_id=0,
                                    uuid=self.RX_UUID,
                                    value=b'',
                                    notifying=True,
                                    flags=['write'],
                                    write_callback=self.rx_write_cb)
        print("Starting BLE Position Server...")

        # Start advertising and publishing GATT service
        self.ble_periph.publish()
        
        try:
            signal.pause()
        except KeyboardInterrupt:
            print("BLE server stopped.")