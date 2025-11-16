"""
combination of pin_lib, bt_lib and auto_run receive message via bluetooth
and control P9_14.
Commands via BT:
    Forward:    ("forward" speed)
    Reverse:    ("reverse")
    Turn Left:  ("left" angle)
    Turn Right: ("right" angle)
    Brake:      ("brake")
    Lamps:      ("illumination" effect)
"""
from bluezero import peripheral
import signal
import subprocess
import re
import threading
import time

class BT:
    def __init__(self):
        # UUIDs
        self.SERVICE_UUID = '6E400001-B5A3-F393-E0A9-E50E24DCCA9E'
        self.RX_UUID      = '6E400002-B5A3-F393-E0A9-E50E24DCCA9E'
        self.TX_UUID      = '6E400003-B5A3-F393-E0A9-E50E24DCCA9E'  # For sending to iPhone
        self.ble_periph = None
        self.response_message = b''  # Store the response message
        self.start_control = None  # For custom data processing function
        self.move_forward = None
        self.move_reverse = None
        self.turn_left = None
        self.turn_right = None
        self.turn_end = None
        self.illumination = None
        self.lamps_control = None  # ← FIXED: Added missing variable
        self.brake_movement = None
        self.left_control = None
        self.right_control = None
        self.dance = None

        self.connected_devices = []  # Track connected devices
        self.rssi_monitoring = False  # Flag for RSSI monitoring
        self.current_rssi = None  # Store current RSSI value
        self.is_connected = False  # Track connection state
        self.notifications_enabled = False  # Track if notifications are enabled
        self.tx_characteristic = None  # Store TX characteristic reference

    def connection_cb(self, device_path):
        """Callback when a device connects"""
        print(f"Device connected: {device_path}")
        self.is_connected = True
        self.connected_devices.append(device_path)
        print("BBB is now connected to iPhone")

    def disconnection_cb(self, device_path):
        """Callback when a device disconnects"""
        print(f"Device disconnected: {device_path}")
        self.is_connected = False
        if device_path in self.connected_devices:
            self.connected_devices.remove(device_path)
        print("BBB disconnected from iPhone")

    def notification_cb(self, characteristic_path, enabled):
        """Callback when notifications are enabled/disabled"""
        print(f"Notifications {'enabled' if enabled else 'disabled'} for {characteristic_path}")
        self.notifications_enabled = enabled

    def rx_write_cb(self, value, options):
        """Callback when data is received from iPhone via BLE"""
        # Decode and clean the received data
        try:
            # Strip any whitespace and null terminators
            decoded = value.decode('utf-8').strip('\x00\n\r')
            print(f"📱 Received from iPhone: '{decoded}'")
            print(f"📱 RAW BYTES: {value}")
            print(f"📱 RAW HEX: {value.hex()}")
            print(f"⏰ Time: {time.strftime('%H:%M:%S')}")
            
            # Process the command
            if decoded:  # Only process non-empty commands
                self.process_received_data(decoded)
            else:
                print("⚠️  Empty command received, ignoring")
                
        except Exception as e:
            print(f"❌ Error decoding received data: {e}")
            print(f"   Raw bytes: {value}")

    def process_received_data(self, message):
        """Process the received data - use custom processor if available"""
        print(f"🔄 Processing command: '{message}'")
        
        # Split command into parts
        parts = message.split()
        if not parts:
            print("⚠️  Empty command after split")
            return
            
        key = parts[0].lower()  # Make command case-insensitive
        value = None
        
        # Parse value if present
        if len(parts) > 1:
            try:
                value = float(parts[1])
            except ValueError:
                print(f"⚠️  Could not parse value: {parts[1]}")
                value = None

        print(f"Command: '{key}', Value: {value}")

        # Process commands regardless of lamps_control status
        # Handle basic commands that don't require external control functions
        if key == "status":
            print("📊 Status request received")
            self.send_to_iphone("BBB_READY")
            return
        elif key == "ping":
            print("🏓 Ping received")
            self.send_to_iphone("PONG")
            return
        elif key == "rssi":
            print("📶 RSSI request received")
            rssi = self.get_current_rssi()
            self.send_to_iphone(f"RSSI_{rssi}")
            return
        elif key == "stop":
            print("🛑 Stop command received")
            if self.brake_movement:
                self.brake_movement()
                self.send_to_iphone("STOP_OK")
            else:
                self.send_to_iphone("STOP_NO_HANDLER")
            return

        # Handle control commands that need external functions
        if key == "illumination":
            print(f"💡 Controlling lamps with value: {value}")
            if self.lamps_control:
                self.lamps_control(20, value)
                self.send_to_iphone("LAMPS_OK")
            elif self.illumination:
                self.illumination(value)
                self.send_to_iphone("LAMPS_OK")
            else:
                print("⚠️  No lamp control function set")
                self.send_to_iphone("LAMPS_NO_HANDLER")
                
        elif key == "turn_left":
            print(f"⬅️  Controlling turn_left with angle: {value}")
            if self.turn_left:
                self.turn_left(value)
                self.send_to_iphone(f"LEFT_{value}_OK")
            else:
                print("⚠️  No turn_left function set")
                self.send_to_iphone("LEFT_NO_HANDLER")
                
        elif key == "turn_right":
            print(f"➡️  Controlling right with value: {value}")
            if self.turn_right:
                self.turn_right(value)
                self.send_to_iphone(f"RIGHT_{value}_OK")
            else:
                print("⚠️  No turn_right function set")
                self.send_to_iphone("RIGHT_NO_HANDLER")
                
        elif key == "turn_end" or key == "turn_stop":
            print(f"🔄 Controlling turn_end")
            if self.turn_end:
                self.turn_end()
                self.send_to_iphone("TURN_END_OK")
            else:
                print("⚠️  No turn_end function set")
                self.send_to_iphone("TURN_END_NO_HANDLER")
                
        elif key == "forward":
            print(f"⬆️  Controlling forward with speed: {value}")
            if self.move_forward:
                self.move_forward(value)
                self.send_to_iphone(f"FORWARD_{value}_OK")
            else:
                print("⚠️  No move_forward function set")
                self.send_to_iphone("FORWARD_NO_HANDLER")
                
        elif key == "reverse":
            print(f"⬇️  Controlling reverse")
            if self.move_reverse:
                self.move_reverse()
                self.send_to_iphone("REVERSE_OK")
            else:
                print("⚠️  No move_reverse function set")
                self.send_to_iphone("REVERSE_NO_HANDLER")
                
        elif key == "brake":
            print(f"🛑 Controlling brake")
            if self.brake_movement:
                self.brake_movement()
                self.send_to_iphone("BRAKE_OK")
            else:
                print("⚠️  No brake_movement function set")
                self.send_to_iphone("BRAKE_NO_HANDLER")
                
        else:
            print(f"❓ Unknown command: '{key}'")
            self.send_to_iphone(f"UNKNOWN_COMMAND_{key}")

    def get_current_rssi(self):
        """Get current RSSI of connected device"""
        try:
            # Method 1: Try using hcitool for active connections
            result = subprocess.run(['hcitool', 'con'], 
                                  capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 3:
                            device_addr = parts[2]
                            rssi = self.get_rssi_via_hcitool(device_addr)
                            if rssi:
                                self.current_rssi = rssi
                                return rssi

            # Method 2: Return cached value if available
            if self.current_rssi:
                return self.current_rssi

            return -999  # Return error value if no RSSI available

        except Exception as e:
            print(f"Error getting current RSSI: {e}")
            return -999

    def get_rssi_via_hcitool(self, device_address):
        """Get RSSI using hcitool command"""
        try:
            result = subprocess.run(['hcitool', 'rssi', device_address], 
                                  capture_output=True, text=True, timeout=3)

            if result.returncode == 0:
                # Parse RSSI from output
                rssi_match = re.search(r'RSSI return value: (-?\d+)', result.stdout)
                if rssi_match:
                    rssi = int(rssi_match.group(1))
                    print(f"RSSI for {device_address}: {rssi} dBm")
                    return rssi

            return None
        except Exception as e:
            print(f"Error getting RSSI via hcitool: {e}")
            return None

    def start_rssi_monitoring(self, interval=5):
        """Start monitoring RSSI in background"""
        self.rssi_monitoring = True
        
        def monitor_loop():
            while self.rssi_monitoring:
                rssi = self.get_current_rssi()
                if rssi and rssi != -999:
                    print(f"Current RSSI: {rssi} dBm")
                time.sleep(interval)
        
        monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitoring_thread.start()
        print("RSSI monitoring started")
    
    def stop_rssi_monitoring(self):
        """Stop RSSI monitoring"""
        self.rssi_monitoring = False
        print("RSSI monitoring stopped")
    
    def tx_read_cb(self, options):
        """Callback when iPhone reads the TX characteristic"""
        print(f"iPhone reading TX characteristic: {self.response_message.decode()}")
        return self.response_message
    
    def send_to_iphone(self, message):
        """Send data from BBB to iPhone"""
        try:
            if not self.is_connected:
                print("⚠️  Warning: No device connected. Cannot send message.")
                return False
            
            # Store the message in our response variable
            self.response_message = message.encode('utf-8')
            print(f"📤 Sending to iPhone: {message}")
            
            # Try to send notification if enabled
            if self.notifications_enabled and self.tx_characteristic:
                try:
                    # Update the characteristic value
                    self.tx_characteristic.set_value(self.response_message)
                    print(f"✅ Notification sent successfully!")
                except Exception as notify_error:
                    print(f"⚠️  Notification failed, data available for read: {notify_error}")
            else:
                print(f"📋 Data prepared for iPhone to read (notifications not enabled)")
            
            return True
            
        except Exception as e:
            print(f"❌ Error preparing message for iPhone: {e}")
            return False

    def start_server(self):
        try:
            print("Initializing BLE Peripheral...")
            # Create Peripheral
            self.ble_periph = peripheral.Peripheral(adapter_address='EC:75:0C:F7:12:43',
                                                    local_name='BBB-PosServer')
            
            # Set connection callbacks
            self.ble_periph.on_connect = self.connection_cb
            self.ble_periph.on_disconnect = self.disconnection_cb
            
            # Add service
            print("Adding BLE service...")
            self.ble_periph.add_service(srv_id=0, uuid=self.SERVICE_UUID, primary=True)
        except Exception as e:
            print(f"Error initializing BLE peripheral: {e}")
            raise

        # Add RX characteristic (write) - for receiving data from iPhone
        self.ble_periph.add_characteristic(srv_id=0,
                                    chr_id=0,
                                    uuid=self.RX_UUID,
                                    value=b'',
                                    notifying=False,
                                    flags=['write', 'write-without-response'],
                                    write_callback=self.rx_write_cb)
        
        # Add TX characteristic (notify) - for sending data to iPhone
        self.tx_characteristic = self.ble_periph.add_characteristic(srv_id=0,
                                    chr_id=1,
                                    uuid=self.TX_UUID,
                                    value=b'',
                                    notifying=True,
                                    flags=['read', 'notify', 'indicate'],
                                    read_callback=self.tx_read_cb,
                                    notify_callback=self.notification_cb)
        
        print("Starting BLE Position Server...")
        print(f"Service UUID: {self.SERVICE_UUID}")
        print(f"RX UUID: {self.RX_UUID}")
        print(f"TX UUID: {self.TX_UUID}")
        print(f"Device Name: BBB-PosServer")
        print(f"Adapter Address: EC:75:0C:F7:12:43")
        print("\n" + "="*50)
        print("🎯 BBB BLE Server Ready!")
        print("="*50)

        try:
            # Start advertising and publishing GATT service
            self.ble_periph.publish()
            print("✅ BLE server is now advertising and ready for connections")
            print("Waiting for iPhone to connect...")
            
            signal.pause()
        except KeyboardInterrupt:
            print("\nBLE server stopped by user.")
        except Exception as e:
            print(f"Error during server operation: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        try:
            self.stop_rssi_monitoring()
            if self.ble_periph:
                print("Cleaning up BLE resources...")
            print("Cleanup completed.")
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    def get_connection_status(self):
        """Get detailed connection status"""
        status = {
            'connected': self.is_connected,
            'notifications_enabled': self.notifications_enabled,
            'connected_devices_count': len(self.connected_devices),
            'current_rssi': self.current_rssi,
            'server_running': self.ble_periph is not None
        }
        
        print("=== BLE Connection Status ===")
        for key, value in status.items():
            print(f"{key}: {value}")
        print("============================")
        
        return status
    
    def test_communication(self):
        """Test communication capabilities"""
        print("=== Testing BLE Communication ===")
        
        # Test 1: Check if server is running
        if not self.ble_periph:
            print("❌ BLE server not started")
            return False
        else:
            print("✅ BLE server is running")
        
        # Test 2: Check connection
        if not self.is_connected:
            print("❌ No device connected")
            print("   → Make sure iPhone app is scanning and connecting")
            return False
        else:
            print("✅ Device connected")
        
        # Test 3: Test sending data
        try:
            test_result = self.send_to_iphone("TEST_MESSAGE")
            if test_result:
                print("✅ Test message prepared successfully")
            else:
                print("❌ Failed to prepare test message")
        except Exception as e:
            print(f"❌ Error sending test message: {e}")
        
        print("=================================")
        return True
    
    def debug_bluetooth_status(self):
        """Debug Bluetooth adapter status"""
        try:
            print("=== Bluetooth System Status ===")
            
            # Check hciconfig
            result = subprocess.run(['hciconfig'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("Bluetooth adapter status:")
                print(result.stdout)
            else:
                print("❌ Could not get Bluetooth adapter status")
            
            # Check active connections
            result = subprocess.run(['hcitool', 'con'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("Active connections:")
                print(result.stdout)
                
                # Analyze connections
                self.analyze_existing_connections(result.stdout)
            else:
                print("❌ Could not get connection status")
                
        except Exception as e:
            print(f"Error getting Bluetooth status: {e}")
        
        print("===============================")
    
    def analyze_existing_connections(self, hcitool_output):
        """Analyze existing Bluetooth connections"""
        lines = hcitool_output.strip().split('\n')
        connection_found = False
        
        for line in lines:
            if 'ACL' in line and 'handle' in line:
                connection_found = True
                # Parse: "> ACL B0:67:B5:7C:41:CA handle 1 state 1 lm PERIPHERAL AUTH ENCRYPT"
                parts = line.strip().split()
                if len(parts) >= 3:
                    device_addr = parts[2]  # The MAC address is the 3rd element
                    print(f"\n🔍 Found existing connection:")
                    print(f"   Device: {device_addr}")
                    
                    # Get RSSI for this device
                    rssi = self.get_rssi_via_hcitool(device_addr)
                    if rssi:
                        print(f"   Signal: {rssi} dBm")
                        self.current_rssi = rssi
                    
                    # Check connection properties
                    if 'PERIPHERAL' in line:
                        print(f"   ✅ This device is connected as PERIPHERAL")
                        print(f"   💡 This could be your iPhone!")
                    
                    if 'AUTH' in line and 'ENCRYPT' in line:
                        print(f"   🔒 Connection is authenticated and encrypted")
                    
                    break
        
        if not connection_found:
            print("\n📱 No existing BLE connections found")
            print("   iPhone will need to connect to your BLE server")