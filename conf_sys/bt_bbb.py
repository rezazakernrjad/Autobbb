from bluezero import peripheral

# UUIDs
SERVICE_UUID = '6E400001-B5A3-F393-E0A9-E50E24DCCA9E'
RX_UUID      = '6E400002-B5A3-F393-E0A9-E50E24DCCA9E'

def rx_write_cb(value, options):
    print("Received:", value.decode())

# Create Peripheral
ble_periph = peripheral.Peripheral(adapter_address='EC:75:0C:F7:12:43',
                                   local_name='BBB-PosServer')

# Add service
ble_periph.add_service(srv_id=0, uuid=SERVICE_UUID, primary=True)

# Add RX characteristic (write)
ble_periph.add_characteristic(srv_id=0,
                              chr_id=0,
                              uuid=RX_UUID,
                              value=b'',
                              notifying=True,
                              flags=['write'],
                              write_callback=rx_write_cb)

print("Starting BLE Position Server...")

# Start advertising and publishing GATT service
ble_periph.publish()

# Keep the script running
try:
    import signal
    signal.pause()
except KeyboardInterrupt:
    print("BLE server stopped.")
