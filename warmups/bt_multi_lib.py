from bluezero import peripheral
import signal

class BT:
    def __init__(self):
        # UUIDs
        self.SERVICE_UUID = '6E400001-B5A3-F393-E0A9-E50E24DCCA9E'
        self.RX_UUID      = '6E400002-B5A3-F393-E0A9-E50E24DCCA9E'
        self.ble_periph = None
        self.custom_processor = None  # For custom data processing function
        
    def rx_write_cb(self, value, options):
        print("Received:", value.decode())
        # Process your data here directly
        self.process_received_data(value.decode())
    
    def process_received_data(self, message):
        """Process the received data - use custom processor if available"""
        if self.custom_processor:
            # Use custom processor function
            self.custom_processor(message)
        else:
            # Default processing
            print(f"Processing: {message}")
            
            # Add your custom logic here:
            if message == "LED_ON":
                # Turn on LED
                print("LED ON command received")
            elif message == "LED_OFF":
                # Turn off LED
                print("LED OFF command received")
            elif message.startswith("MOVE_"):
                # Control motors
                print(f"Motor control command received: {message}")
            # Add more conditions as needed

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