"""
251122-1548
Bluetooth BLE server using bluez-peripheral for BBB
Receives commands from iPad and controls hardware
Commands via BT:
    Forward:    ("forward" speed)
    Reverse:    ("reverse")
    Turn Left:  ("turn_left" angle)
    Turn Right: ("turn_right" angle)
    Brake:      ("brake")
    Lamps:      ("illumination" effect)
"""
import asyncio
import subprocess
import re
import time
from bluez_peripheral.gatt.service import Service
from bluez_peripheral.gatt.characteristic import characteristic, CharacteristicFlags as CharFlags
from bluez_peripheral.advert import Advertisement
from bluez_peripheral.agent import NoIoAgent
from bluez_peripheral.util import get_message_bus
from dbus_next import Message, MessageType


class BLEPositionServer(Service):
    """BLE GATT Service for position control"""
    
    def __init__(self, bt_instance):
        # Nordic UART Service UUID
        super().__init__("6E400001-B5A3-F393-E0A9-E50E24DCCA9E", True)
        self.bt = bt_instance
        self.tx_value = b''  # Store value for TX characteristic
        
    async def on_connect(self, device_path):
        """Called when a device connects"""
        print(f"📱 Device connected: {device_path}")
        print(f"   Time: {time.strftime('%H:%M:%S')}")
        self.bt.is_connected = True
        self.bt.disconnect_in_progress = False
        
        # Send a test notification to verify connection
        asyncio.create_task(self._send_connection_ack())
    
    async def _send_connection_ack(self):
        """Send acknowledgment after connection"""
        try:
            await asyncio.sleep(1)  # Wait for characteristics to be ready
            await self.send_notification("BBB_READY")
        except Exception as e:
            print(f"⚠️ Could not send connection ack: {e}")
        
    async def on_disconnect(self, device_path):
        """Called when a device disconnects"""
        print(f"📱 Device disconnected: {device_path}")
        self.bt.is_connected = False
        # Clean up any pending operations
        await self.bt.handle_disconnect()
        
    @characteristic("6E400002-B5A3-F393-E0A9-E50E24DCCA9E", CharFlags.WRITE | CharFlags.WRITE_WITHOUT_RESPONSE)
    def rx_characteristic(self, options):
        """RX Characteristic - receives data from iPad"""
        return self.tx_value
    
    @rx_characteristic.setter
    def rx_characteristic(self, value, options):
        """Called when iPad writes data to RX characteristic"""
        # Auto-detect connection on first write
        if not self.bt.is_connected:
            print("📱 Device connected (detected via write)")
            self.bt.is_connected = True
            self.bt.disconnect_in_progress = False
        
        try:
            # Decode and clean the received data
            decoded = value.decode('utf-8').strip('\x00\n\r')
            print(f"📱 Received from iPhone: '{decoded}'")
            print(f"📱 RAW BYTES: {value}")
            print(f"📱 RAW HEX: {value.hex()}")
            print(f"⏰ Time: {time.strftime('%H:%M:%S')}")
            
            # Process the command asynchronously
            if decoded:
                asyncio.create_task(self.bt.process_received_data(decoded))
            else:
                print("⚠️ Empty command received, ignoring")
                
        except Exception as e:
            print(f"❌ Error decoding received data: {e}")
            print(f"   Raw bytes: {value}")
    
    @characteristic("6E400003-B5A3-F393-E0A9-E50E24DCCA9E", CharFlags.READ | CharFlags.NOTIFY | CharFlags.INDICATE)
    def tx_characteristic(self, options):
        """TX Characteristic - sends data to iPad"""
        print(f"📤 iPad reading TX characteristic: {self.tx_value}")
        return self.tx_value
    
    async def send_notification(self, message):
        """Send notification to iPad"""
        # Don't try to send if disconnected
        if not self.bt.is_connected:
            return False
            
        try:
            self.tx_value = message.encode('utf-8')
            print(f"📤 Sending notification: {message}")
            
            # Notify connected devices - changed() is not async in some versions
            try:
                result = self.tx_characteristic.changed(self.tx_value)
                # Check if result is awaitable
                if result is not None and hasattr(result, '__await__'):
                    await result
            except TypeError:
                # Method doesn't return awaitable, just call it
                self.tx_characteristic.changed(self.tx_value)
            
            print(f"✅ Notification sent successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error sending notification: {e}")
            # Mark as disconnected if send fails
            self.bt.is_connected = False
            return False


class BT:
    def __init__(self):
        # Configuration
        self.SERVICE_UUID = '6E400001-B5A3-F393-E0A9-E50E24DCCA9E'
        self.RX_UUID = '6E400002-B5A3-F393-E0A9-E50E24DCCA9E'
        self.TX_UUID = '6E400003-B5A3-F393-E0A9-E50E24DCCA9E'
        
        # State tracking
        self.is_connected = False
        self.current_rssi = None
        self.rssi_monitoring = False
        
        # BLE objects
        self.service = None
        self.advertisement = None
        self.agent = None
        self.bus = None  # D-Bus connection
        
        # Control function callbacks
        self.start_control = None
        self.move_forward = None
        self.move_reverse = None
        self.turn_left = None
        self.turn_right = None
        self.turn_end = None
        self.illumination = None
        self.lamps_control = None
        self.brake_movement = None
        self.left_control = None
        self.right_control = None
        self.dance = None
        
        # Main event loop and shutdown flag
        self.loop = None
        self.shutdown_flag = False
        self.disconnect_in_progress = False
        self.services_registered = False
    
    async def process_received_data(self, message):
        """Process the received data"""
        print(f"🔄 Processing command: '{message}'")
        
        # Split command into parts
        parts = message.split()
        if not parts:
            print("⚠️ Empty command after split")
            return
            
        key = parts[0].lower()
        value = None
        
        # Parse value if present
        if len(parts) > 1:
            try:
                value = float(parts[1])
            except ValueError:
                print(f"⚠️ Could not parse value: {parts[1]}")
                value = None
        
        print(f"Command: '{key}', Value: {value}")
        
        # Process basic commands
        if key == "status":
            print("📊 Status request received")
            await self.send_to_iphone("BBB_READY")
            return
        elif key == "ping":
            print("🏓 Ping received")
            await self.send_to_iphone("PONG")
            return
        elif key == "rssi":
            print("📶 RSSI request received")
            rssi = self.get_current_rssi()
            await self.send_to_iphone(f"RSSI_{rssi}")
            return
        elif key == "stop":
            print("🛑 Stop command received")
            if self.brake_movement:
                self.brake_movement()
                await self.send_to_iphone("STOP_OK")
            else:
                await self.send_to_iphone("STOP_NO_HANDLER")
            return
        
        # Handle control commands
        if key == "illumination":
            print(f"💡 Controlling lamps with value: {value}")
            if self.lamps_control:
                self.lamps_control(20, value)
                await self.send_to_iphone("LAMPS_OK")
            elif self.illumination:
                self.illumination(value)
                await self.send_to_iphone("LAMPS_OK")
            else:
                print("⚠️ No lamp control function set")
                await self.send_to_iphone("LAMPS_NO_HANDLER")
                
        elif key == "turn_left":
            print(f"⬅️ Controlling turn_left with angle: {value}")
            if self.turn_left:
                self.turn_left(value)
                await self.send_to_iphone(f"LEFT_{value}_OK")
            else:
                print("⚠️ No turn_left function set")
                await self.send_to_iphone("LEFT_NO_HANDLER")
                
        elif key == "turn_right":
            print(f"➡️ Controlling right with value: {value}")
            if self.turn_right:
                self.turn_right(value)
                await self.send_to_iphone(f"RIGHT_{value}_OK")
            else:
                print("⚠️ No turn_right function set")
                await self.send_to_iphone("RIGHT_NO_HANDLER")
                
        elif key == "turn_end" or key == "turn_stop":
            print(f"🔄 Controlling turn_end")
            if self.turn_end:
                self.turn_end()
                await self.send_to_iphone("TURN_END_OK")
            else:
                print("⚠️ No turn_end function set")
                await self.send_to_iphone("TURN_END_NO_HANDLER")
                
        elif key == "forward":
            print(f"⬆️ Controlling forward with speed: {value}")
            if self.move_forward:
                self.move_forward(value)
                await self.send_to_iphone(f"FORWARD_{value}_OK")
            else:
                print("⚠️ No move_forward function set")
                await self.send_to_iphone("FORWARD_NO_HANDLER")
                
        elif key == "reverse":
            print(f"⬇️ Controlling reverse")
            if self.move_reverse:
                self.move_reverse()
                await self.send_to_iphone("REVERSE_OK")
            else:
                print("⚠️ No move_reverse function set")
                await self.send_to_iphone("REVERSE_NO_HANDLER")
                
        elif key == "brake":
            print(f"🛑 Controlling brake")
            if self.brake_movement:
                self.brake_movement()
                await self.send_to_iphone("BRAKE_OK")
            else:
                print("⚠️ No brake_movement function set")
                await self.send_to_iphone("BRAKE_NO_HANDLER")
                
        else:
            print(f"❓ Unknown command: '{key}'")
            await self.send_to_iphone(f"UNKNOWN_COMMAND_{key}")
    
    async def send_to_iphone(self, message):
        """Send data to iPhone via notification"""
        try:
            if not self.is_connected:
                print("⚠️ Warning: No device connected. Cannot send message.")
                return False
            
            if self.service:
                return await self.service.send_notification(message)
            else:
                print("⚠️ Service not initialized")
                return False
                
        except Exception as e:
            print(f"❌ Error sending to iPhone: {e}")
            # If send fails, device might have disconnected
            if "not connected" in str(e).lower() or "disconnected" in str(e).lower():
                self.is_connected = False
            return False
    
    def get_current_rssi(self):
        """Get current RSSI of connected device"""
        try:
            result = subprocess.run(['hcitool', 'con'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 3:
                            device_addr = parts[2]
                            rssi = self.get_rssi_via_hcitool(device_addr)
                            if rssi:
                                self.current_rssi = rssi
                                return rssi
            
            if self.current_rssi:
                return self.current_rssi
            
            return -999
            
        except Exception as e:
            print(f"Error getting current RSSI: {e}")
            return -999
    
    def get_rssi_via_hcitool(self, device_address):
        """Get RSSI using hcitool command"""
        try:
            result = subprocess.run(['hcitool', 'rssi', device_address], 
                                  capture_output=True, text=True, timeout=3)
            
            if result.returncode == 0:
                rssi_match = re.search(r'RSSI return value: (-?\d+)', result.stdout)
                if rssi_match:
                    rssi = int(rssi_match.group(1))
                    print(f"RSSI for {device_address}: {rssi} dBm")
                    return rssi
            
            return None
        except Exception as e:
            print(f"Error getting RSSI via hcitool: {e}")
            return None
    
    async def start_rssi_monitoring(self, interval=5):
        """Start monitoring RSSI in background"""
        self.rssi_monitoring = True
        
        async def monitor_loop():
            while self.rssi_monitoring:
                rssi = self.get_current_rssi()
                if rssi and rssi != -999:
                    print(f"Current RSSI: {rssi} dBm")
                await asyncio.sleep(interval)
        
        asyncio.create_task(monitor_loop())
        print("RSSI monitoring started")
    
    def stop_rssi_monitoring(self):
        """Stop RSSI monitoring"""
        self.rssi_monitoring = False
        print("RSSI monitoring stopped")
    
    async def on_connect(self):
        """Callback when device connects"""
        print("📱 Device connected!")
        self.is_connected = True
        self.disconnect_in_progress = False
        print("BBB is now connected to iPhone")
    
    async def on_disconnect(self):
        """Callback when device disconnects"""
        print("📱 Device disconnected")
        self.is_connected = False
        # Stop any ongoing RSSI monitoring
        self.stop_rssi_monitoring()
        print("✅ Disconnect cleanup completed")
    
    async def start_server_async(self):
        """Start the BLE server (async version)"""
        try:
            print("Initializing BLE Peripheral...")
            
            # Check Bluetooth adapter first
            print("Checking Bluetooth adapter...")
            adapter_check = subprocess.run(['hciconfig', 'hci0'], 
                                         capture_output=True, text=True)
            if adapter_check.returncode != 0:
                print("❌ Bluetooth adapter hci0 not found!")
                print("Run: sudo hciconfig hci0 up")
                return
            
            # Ensure adapter is up
            subprocess.run(['sudo', 'hciconfig', 'hci0', 'up'], check=False)
            print("✅ Bluetooth adapter is up")
            
            # Get D-Bus connection
            self.bus = await get_message_bus()
            print("✅ D-Bus connection established")
            
            # Register the agent for pairing
            self.agent = NoIoAgent()
            await self.agent.register(self.bus)
            print("✅ Agent registered")
            
            # Create and register the service
            self.service = BLEPositionServer(self)
            print(f"📝 Registering GATT service: {self.SERVICE_UUID}")
            
            # Register with specific application path for iOS compatibility
            service_path = await self.service.register(self.bus)
            self.services_registered = True
            print(f"✅ Service registered at path: {service_path}")
            
            # Small delay to ensure registration completes
            await asyncio.sleep(1.0)
            
            # Verify service registration
            await asyncio.sleep(0.5)
            try:
                result = subprocess.run(
                    ['busctl', 'introspect', 'org.bluez', '/org/bluez/hci0'],
                    capture_output=True, text=True, timeout=5
                )
                if '6e400001' in result.stdout.lower():
                    print("✅ Service verified in D-Bus")
                else:
                    print("⚠️ WARNING: Service not found in D-Bus!")
                    print("   This may cause service discovery to fail")
            except Exception as e:
                print(f"⚠️ Could not verify service registration: {e}")
            
            # Create advertisement
            self.advertisement = Advertisement(
                "AutoBBB",  # Match the name iOS sees
                [self.SERVICE_UUID],
                0x0340,  # Appearance: Generic Remote Control
                60      # Timeout (seconds)
            )
            
            # Start advertising
            print(f"📢 Starting advertisement as 'AutoBBB'")
            await self.advertisement.register(self.bus)
            print("✅ Advertisement started")
            
            print("\n" + "="*50)
            print("🎯 BBB BLE Server Ready!")
            print("="*50)
            print(f"Service UUID: {self.SERVICE_UUID}")
            print(f"RX UUID: {self.RX_UUID}")
            print(f"TX UUID: {self.TX_UUID}")
            print(f"Device Name: BBB-PosServer")
            print("Waiting for iPhone to connect...")
            print("="*50 + "\n")
            
            # Keep the server running and handle reconnections
            connection_lost_count = 0
            while not self.shutdown_flag:
                # Check connection status periodically
                await asyncio.sleep(2)
                
                # Monitor connection state
                if not self.is_connected:
                    connection_lost_count += 1
                    if connection_lost_count % 15 == 0:  # Every 30 seconds
                        print(f"⏳ Waiting for connection... ({connection_lost_count * 2}s)")
                        print(f"   Services registered: {self.services_registered}")
                        print(f"   Advertisement active: {self.advertisement is not None}")
                else:
                    connection_lost_count = 0
                
        except KeyboardInterrupt:
            print("\n🛑 BLE server stopped by user")
        except Exception as e:
            print(f"❌ Error during server operation: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.cleanup()
    
    def start_server(self):
        """Start the BLE server (blocking call)"""
        try:
            # Create event loop
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # Run the async server
            self.loop.run_until_complete(self.start_server_async())
            
        except KeyboardInterrupt:
            print("\n🛑 Stopped by user")
            print("Shutting down gracefully...")
            # Set shutdown flag and let the loop finish naturally
            self.shutdown_flag = True
            # Give it a moment to process
            if self.loop and not self.loop.is_closed():
                try:
                    self.loop.run_until_complete(self.cleanup())
                except Exception as e:
                    print(f"Cleanup error: {e}")
        finally:
            if self.loop and not self.loop.is_closed():
                self.loop.close()
    
    def stop_server(self):
        """Stop the server gracefully (can be called from signal handler)"""
        print("\n🛑 Stopping server...")
        self.shutdown_flag = True
    
    async def handle_disconnect(self):
        """Handle client disconnect - called when iPad disconnects"""
        if self.disconnect_in_progress:
            print("⚠️ Disconnect already in progress, skipping")
            return
        
        self.disconnect_in_progress = True
        print("🔄 Handling client disconnect...")
        
        try:
            # Stop any ongoing operations
            self.stop_rssi_monitoring()
            
            # Call brake if available to stop any movement
            if self.brake_movement:
                try:
                    self.brake_movement()
                    print("🛑 Emergency brake applied")
                except Exception as e:
                    print(f"⚠️ Error applying brake: {e}")
            
            # Give time for brake to complete
            await asyncio.sleep(0.2)
            
            # Re-register services for next connection
            await self._reregister_services()
            
            print("✅ Disconnect handling completed")
            
        except Exception as e:
            print(f"❌ Error during disconnect handling: {e}")
        finally:
            self.disconnect_in_progress = False
    
    async def _reregister_services(self):
        """Re-register GATT services to fix iOS service discovery after disconnect"""
        try:
            if not self.bus:
                print("❌ No D-Bus connection available")
                return
            
            print("🔄 Re-registering services and advertisement...")
            
            # Unregister old service
            if self.service:
                try:
                    await self.service.unregister()
                    print("✅ Old service unregistered")
                except Exception as e:
                    print(f"⚠️ Service unregister warning: {e}")
            
            # Unregister old advertisement
            if self.advertisement:
                try:
                    # Use unregister, not stop
                    await self.advertisement.unregister(self.bus)
                    print("✅ Old advertisement unregistered")
                except AttributeError:
                    # Older version might not have unregister
                    print("⚠️ Advertisement cleanup skipped (no unregister method)")
                except Exception as e:
                    print(f"⚠️ Advertisement unregister warning: {e}")
            
            # Small delay to let BlueZ settle
            await asyncio.sleep(0.8)
            
            # Create and register new service instance
            self.service = BLEPositionServer(self)
            print("📝 Re-registering service...")
            await self.service.register(self.bus)
            print("✅ Service re-registered")
            
            # Verify service registration
            await asyncio.sleep(0.3)
            try:
                result = subprocess.run(
                    ['busctl', 'introspect', 'org.bluez', '/org/bluez/hci0'],
                    capture_output=True, text=True, timeout=3
                )
                if '6e400001' in result.stdout.lower():
                    print("✅ Service verified in D-Bus after re-registration")
                else:
                    print("⚠️ WARNING: Service not found in D-Bus after re-registration!")
            except:
                pass
            
            # Re-create and start advertisement
            self.advertisement = Advertisement(
                "AutoBBB",  # Match the name iOS sees
                [self.SERVICE_UUID],
                0x0340,  # Appearance: Generic Remote Control
                60      # Timeout (seconds)
            )
            print("📢 Re-starting advertisement...")
            await self.advertisement.register(self.bus)
            self.services_registered = True
            print("✅ Advertisement re-started - BBB is discoverable again")
            
        except Exception as e:
            print(f"❌ Error re-registering services: {e}")
            import traceback
            traceback.print_exc()
            self.services_registered = False
    
    async def cleanup(self):
        """Clean up resources - called on shutdown"""
        try:
            print("Cleaning up BLE resources...")
            self.stop_rssi_monitoring()
            
            # Mark as disconnected
            self.is_connected = False
            self.services_registered = False
            
            # Small delay to let ongoing operations complete
            await asyncio.sleep(0.3)
            
            # Unregister advertisement
            if self.advertisement and self.bus:
                try:
                    await self.advertisement.unregister(self.bus)
                    print("✅ Advertisement unregistered")
                except AttributeError:
                    print("⚠️ Advertisement cleanup skipped (no unregister method)")
                except Exception as e:
                    print(f"⚠️ Advertisement cleanup error: {e}")
            
            # Unregister service
            if self.service:
                try:
                    await self.service.unregister()
                    print("✅ Service unregistered")
                except Exception as e:
                    print(f"⚠️ Service cleanup error: {e}")
            
            # Unregister agent
            if self.agent and self.bus:
                try:
                    await self.agent.unregister(self.bus)
                    print("✅ Agent unregistered")
                except Exception as e:
                    print(f"⚠️ Agent cleanup error: {e}")
            
            print("Cleanup completed.")
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    def cleanup_sync(self):
        """Synchronous cleanup for external calls - DO NOT USE from signal handlers"""
        print("⚠️ cleanup_sync() is deprecated - use stop_server() instead")
        self.stop_server()
    
    def get_connection_status(self):
        """Get detailed connection status"""
        status = {
            'connected': self.is_connected,
            'current_rssi': self.current_rssi,
            'server_running': self.service is not None
        }
        
        print("=== BLE Connection Status ===")
        for key, value in status.items():
            print(f"{key}: {value}")
        print("============================")
        
        return status
    
    async def test_communication(self):
        """Test communication capabilities"""
        print("=== Testing BLE Communication ===")
        
        if not self.service:
            print("❌ BLE server not started")
            return False
        else:
            print("✅ BLE server is running")
        
        if not self.is_connected:
            print("❌ No device connected")
            print("   → Make sure iPhone app is scanning and connecting")
            return False
        else:
            print("✅ Device connected")
        
        try:
            test_result = await self.send_to_iphone("TEST_MESSAGE")
            if test_result:
                print("✅ Test message sent successfully")
            else:
                print("❌ Failed to send test message")
        except Exception as e:
            print(f"❌ Error sending test message: {e}")
        
        print("=================================")
        return True


# Example usage
# if __name__ == "__main__":
#     bt = BT()
    
#     # Set up control callbacks (example)
#     def example_forward(speed):
#         print(f"Moving forward at speed: {speed}")
    
#     def example_brake():
#         print("Braking!")
    
#     bt.move_forward = example_forward
#     bt.brake_movement = example_brake
    
#     # Start the server
#     bt.start_server()