#!/usr/bin/env python3
"""
Direct BlueZ D-Bus GATT Server - bypasses bluez-peripheral
This implementation directly uses D-Bus to register GATT services with BlueZ.
Integrated with motor control, illumination, and RSSI monitoring.
"""

import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib
import sys
import time

# D-Bus constants
BLUEZ_SERVICE = 'org.bluez'
GATT_MANAGER_IFACE = 'org.bluez.GattManager1'
DBUS_OM_IFACE = 'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE = 'org.freedesktop.DBus.Properties'
GATT_SERVICE_IFACE = 'org.bluez.GattService1'
GATT_CHRC_IFACE = 'org.bluez.GattCharacteristic1'
GATT_DESC_IFACE = 'org.bluez.GattDescriptor1'
LE_ADVERTISING_MANAGER_IFACE = 'org.bluez.LEAdvertisingManager1'
LE_ADVERTISEMENT_IFACE = 'org.bluez.LEAdvertisement1'

# Nordic UART Service UUIDs
UART_SERVICE_UUID = '6e400001-b5a3-f393-e0a9-e50e24dcca9e'
UART_RX_CHAR_UUID = '6e400002-b5a3-f393-e0a9-e50e24dcca9e'  # Write (commands from phone)
UART_TX_CHAR_UUID = '6e400003-b5a3-f393-e0a9-e50e24dcca9e'  # Notify (data to phone)


class Application(dbus.service.Object):
    """GATT Application - manages services"""
    
    def __init__(self, bus, path='/com/autobbb/app'):
        self.path = path
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service(self, service):
        self.services.append(service)

    @dbus.service.method(DBUS_OM_IFACE, out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        """Return all managed objects (services, characteristics, descriptors)"""
        response = {}
        for service in self.services:
            response[service.get_path()] = service.get_properties()
            chrcs = service.get_characteristics()
            for chrc in chrcs:
                response[chrc.get_path()] = chrc.get_properties()
                descs = chrc.get_descriptors()
                for desc in descs:
                    response[desc.get_path()] = desc.get_properties()
        return response


class Service(dbus.service.Object):
    """GATT Service"""
    
    PATH_BASE = '/com/autobbb/app/service'

    def __init__(self, bus, index, uuid, primary):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.uuid = uuid
        self.primary = primary
        self.characteristics = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
            GATT_SERVICE_IFACE: {
                'UUID': self.uuid,
                'Primary': self.primary,
                'Characteristics': dbus.Array(
                    [chrc.get_path() for chrc in self.characteristics],
                    signature='o')
            }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_characteristic(self, characteristic):
        self.characteristics.append(characteristic)

    def get_characteristics(self):
        return self.characteristics


class Characteristic(dbus.service.Object):
    """GATT Characteristic"""
    
    def __init__(self, bus, index, uuid, flags, service):
        self.path = service.path + '/char' + str(index)
        self.bus = bus
        self.uuid = uuid
        self.service = service
        self.flags = flags
        self.descriptors = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
            GATT_CHRC_IFACE: {
                'Service': self.service.get_path(),
                'UUID': self.uuid,
                'Flags': self.flags,
                'Descriptors': dbus.Array(
                    [desc.get_path() for desc in self.descriptors],
                    signature='o')
            }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_descriptor(self, descriptor):
        self.descriptors.append(descriptor)

    def get_descriptors(self):
        return self.descriptors

    @dbus.service.method(GATT_CHRC_IFACE, in_signature='a{sv}', out_signature='ay')
    def ReadValue(self, options):
        """Override in subclass"""
        print(f'Default ReadValue called on {self.uuid}')
        return []

    @dbus.service.method(GATT_CHRC_IFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        """Override in subclass"""
        print(f'Default WriteValue called on {self.uuid}: {bytes(value)}')

    @dbus.service.method(GATT_CHRC_IFACE)
    def StartNotify(self):
        """Override in subclass"""
        print(f'StartNotify called on {self.uuid}')

    @dbus.service.method(GATT_CHRC_IFACE)
    def StopNotify(self):
        """Override in subclass"""
        print(f'StopNotify called on {self.uuid}')

    @dbus.service.signal(DBUS_PROP_IFACE, signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed, invalidated):
        pass


class RxCharacteristic(Characteristic):
    """RX Characteristic - receives commands from phone"""
    
    def __init__(self, bus, index, service, command_callback):
        Characteristic.__init__(
            self, bus, index,
            UART_RX_CHAR_UUID,
            ['write', 'write-without-response'],
            service)
        self.command_callback = command_callback

    def WriteValue(self, value, options):
        """Called when phone writes data"""
        try:
            data = bytes(value).decode('utf-8').strip()
            print(f'📥 RX: Received command: {data}')
            if self.command_callback:
                self.command_callback(data)
        except Exception as e:
            print(f'❌ RX Error: {e}')


class TxCharacteristic(Characteristic):
    """TX Characteristic - sends data to phone"""
    
    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            UART_TX_CHAR_UUID,
            ['notify'],
            service)
        self.notifying = False

    def StartNotify(self):
        """Phone has subscribed to notifications"""
        if self.notifying:
            return
        self.notifying = True
        print('📡 TX: Phone subscribed to notifications')

    def StopNotify(self):
        """Phone has unsubscribed"""
        self.notifying = False
        print('📡 TX: Phone unsubscribed from notifications')

    def send_data(self, data):
        """Send data to phone"""
        if not self.notifying:
            print('⚠️ TX: Cannot send - phone not subscribed')
            return False
        
        try:
            value = dbus.Array([dbus.Byte(b) for b in data.encode('utf-8')], signature='y')
            self.PropertiesChanged(GATT_CHRC_IFACE, {'Value': value}, [])
            print(f'📤 TX: Sent: {data}')
            return True
        except Exception as e:
            print(f'❌ TX Error: {e}')
            return False


class Advertisement(dbus.service.Object):
    """BLE Advertisement"""
    
    PATH_BASE = '/com/autobbb/advertisement'

    def __init__(self, bus, index, advertising_type):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.ad_type = advertising_type
        self.service_uuids = []
        self.local_name = 'AutoBBB'
        self.include_tx_power = False  # Set to False to avoid TxPower error
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        properties = {
            LE_ADVERTISEMENT_IFACE: {
                'Type': self.ad_type,
                'ServiceUUIDs': dbus.Array(self.service_uuids, signature='s'),
                'LocalName': dbus.String(self.local_name),
                'IncludeTxPower': dbus.Boolean(self.include_tx_power)
            }
        }
        return properties

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service_uuid(self, uuid):
        self.service_uuids.append(uuid)

    @dbus.service.method(DBUS_PROP_IFACE, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != LE_ADVERTISEMENT_IFACE:
            raise dbus.exceptions.DBusException(
                'org.freedesktop.DBus.Error.InvalidArgs',
                'Invalid interface')
        return self.get_properties()[LE_ADVERTISEMENT_IFACE]

    @dbus.service.method(LE_ADVERTISEMENT_IFACE, in_signature='', out_signature='')
    def Release(self):
        print('Advertisement released')


class BLEServer:
    """Main BLE Server with integrated hardware control"""
    
    def __init__(self, command_callback=None):
        self.command_callback = command_callback
        self.mainloop = None
        self.tx_char = None
        self.connected_device = None
        self.rssi_timer = None
        
        # Motor control state
        self.motor_speed = 0
        self.turn_angle = 0
        self.illumination_level = 0
        
        # Try to import hardware libraries
        try:
            import Adafruit_BBIO.PWM as PWM
            import Adafruit_BBIO.GPIO as GPIO
            self.PWM = PWM
            self.GPIO = GPIO
            self.has_hardware = True
            self._init_hardware()
        except ImportError:
            print("⚠️  Hardware libraries not available - running in simulation mode")
            self.PWM = None
            self.GPIO = None
            self.has_hardware = False
        
        # Setup D-Bus
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SystemBus()
        
        # Get BlueZ adapter
        adapter_path = '/org/bluez/hci0'
        obj = self.bus.get_object(BLUEZ_SERVICE, adapter_path)
        self.adapter_props = dbus.Interface(obj, DBUS_PROP_IFACE)
        self.adapter_obj = obj
        
        # Ensure adapter is powered on and properly configured
        self.adapter_props.Set('org.bluez.Adapter1', 'Powered', dbus.Boolean(True))
        self.adapter_props.Set('org.bluez.Adapter1', 'Discoverable', dbus.Boolean(True))
        self.adapter_props.Set('org.bluez.Adapter1', 'Pairable', dbus.Boolean(False))  # Don't require pairing
        
        print(f"✅ Adapter powered on: {adapter_path}")
        
        # Create application
        self.app = Application(self.bus)
        
        # Create UART service
        service = Service(self.bus, 0, UART_SERVICE_UUID, True)
        self.app.add_service(service)
        
        # Add RX characteristic (write from phone)
        rx_char = RxCharacteristic(self.bus, 0, service, self._handle_command_wrapper)
        service.add_characteristic(rx_char)
        
        # Add TX characteristic (notify to phone)
        self.tx_char = TxCharacteristic(self.bus, 1, service)
        service.add_characteristic(self.tx_char)
        
        # Register GATT application
        gatt_manager = dbus.Interface(obj, GATT_MANAGER_IFACE)
        gatt_manager.RegisterApplication(self.app.get_path(), {},
                                        reply_handler=self._register_app_cb,
                                        error_handler=self._register_app_error_cb)
        
        # Create and register advertisement
        self.adv = Advertisement(self.bus, 0, 'peripheral')
        self.adv.add_service_uuid(UART_SERVICE_UUID)
        
        ad_manager = dbus.Interface(obj, LE_ADVERTISING_MANAGER_IFACE)
        ad_manager.RegisterAdvertisement(self.adv.get_path(), {},
                                        reply_handler=self._register_ad_cb,
                                        error_handler=self._register_ad_error_cb)
        
        # Monitor connections
        self.bus.add_signal_receiver(
            self._on_device_connected,
            signal_name="PropertiesChanged",
            dbus_interface=DBUS_PROP_IFACE,
            path_keyword="path"
        )

    def _init_hardware(self):
        """Initialize hardware pins"""
        print("🔧 Initializing hardware...")
        
        # Motor control pins
        self.MOTOR_PWM_PIN = "P9_14"
        self.MOTOR_DIR_PIN = "P9_12"
        
        # Steering pins  
        self.SERVO_PWM_PIN = "P9_16"
        
        # Illumination pin
        self.ILLUM_PWM_PIN = "P9_21"
        
        # Setup GPIO
        if self.GPIO:
            self.GPIO.setup(self.MOTOR_DIR_PIN, self.GPIO.OUT)
            
        # Setup PWM (frequency in Hz, duty cycle 0-100)
        if self.PWM:
            self.PWM.start(self.MOTOR_PWM_PIN, 0, frequency=1000)
            self.PWM.start(self.SERVO_PWM_PIN, 7.5, frequency=50)  # Neutral position
            self.PWM.start(self.ILLUM_PWM_PIN, 0, frequency=1000)
        
        print("✅ Hardware initialized")

    def _cleanup_hardware(self):
        """Cleanup hardware on shutdown"""
        if self.has_hardware and self.PWM:
            print("🛑 Stopping all motors and PWM...")
            self.PWM.stop(self.MOTOR_PWM_PIN)
            self.PWM.stop(self.SERVO_PWM_PIN)
            self.PWM.stop(self.ILLUM_PWM_PIN)
            self.PWM.cleanup()

    def _handle_command_wrapper(self, command):
        """Wrapper to handle command and send confirmation"""
        result = self._handle_command(command)
        if result:
            self.send_to_phone(result)
        if self.command_callback:
            self.command_callback(command)

    def _handle_command(self, command):
        """Process commands from iPad"""
        try:
            parts = command.split()
            if not parts:
                return "ERROR: Empty command"
            
            cmd = parts[0].upper()
            value = float(parts[1]) if len(parts) > 1 else 0
            
            # Motor control commands
            if cmd == "FW" or cmd == "FORWARD":
                self._set_motor_speed(abs(value))
                return f"✓ Forward {value}"
            
            elif cmd == "BW" or cmd == "BACKWARD":
                self._set_motor_speed(-abs(value))
                return f"✓ Backward {value}"
            
            elif cmd == "STOP" or cmd == "BRAKE":
                self._emergency_stop()
                return "✓ Stopped"
            
            # Steering commands
            elif cmd == "L" or cmd == "LEFT":
                self._set_steering(-abs(value))
                return f"✓ Left {value}"
            
            elif cmd == "R" or cmd == "RIGHT":
                self._set_steering(abs(value))
                return f"✓ Right {value}"
            
            elif cmd == "CENTER":
                self._set_steering(0)
                return "✓ Centered"
            
            # Illumination
            elif cmd == "ILLUM" or cmd == "ILLUMINATION":
                self._set_illumination(value)
                return f"✓ Illum {value}%"
            
            # Status query
            elif cmd == "STATUS":
                return f"Motor:{self.motor_speed} Turn:{self.turn_angle} Illum:{self.illumination_level}"
            
            else:
                return f"ERROR: Unknown command '{cmd}'"
                
        except Exception as e:
            error_msg = f"ERROR: {str(e)}"
            print(f"❌ Command error: {error_msg}")
            return error_msg

    def _set_motor_speed(self, speed):
        """Set motor speed (-100 to +100)"""
        speed = max(-100, min(100, speed))  # Clamp to range
        self.motor_speed = speed
        
        if self.has_hardware:
            # Set direction
            direction = 1 if speed >= 0 else 0
            self.GPIO.output(self.MOTOR_DIR_PIN, direction)
            
            # Set PWM duty cycle
            duty = abs(speed)
            self.PWM.set_duty_cycle(self.MOTOR_PWM_PIN, duty)
            
        print(f"🚗 Motor speed: {speed}%")

    def _set_steering(self, angle):
        """Set steering angle (-100 to +100)"""
        angle = max(-100, min(100, angle))
        self.turn_angle = angle
        
        if self.has_hardware:
            # Convert angle to servo duty cycle (5% = full left, 10% = full right, 7.5% = center)
            # Map -100 to +100 to 5% to 10%
            duty = 7.5 + (angle * 2.5 / 100)
            self.PWM.set_duty_cycle(self.SERVO_PWM_PIN, duty)
            
        print(f"🔄 Steering: {angle}° (duty: {7.5 + (angle * 2.5 / 100)}%)")

    def _set_illumination(self, level):
        """Set illumination level (0 to 100)"""
        level = max(0, min(100, level))
        self.illumination_level = level
        
        if self.has_hardware:
            self.PWM.set_duty_cycle(self.ILLUM_PWM_PIN, level)
            
        print(f"💡 Illumination: {level}%")

    def _emergency_stop(self):
        """Emergency stop - immediately halt all motion"""
        print("🛑 EMERGENCY STOP")
        self._set_motor_speed(0)
        self._set_steering(0)
        
    def _on_device_connected(self, interface, changed, invalidated, path):
        """Handle device connection/disconnection"""
        if "org.bluez.Device1" not in interface:
            return
            
        if "Connected" in changed:
            is_connected = changed["Connected"]
            
            if is_connected:
                print(f"📱 Device connected: {path}")
                self.connected_device = path
                # Give services time to stabilize before client discovers them
                GLib.timeout_add(1000, lambda: self._start_rssi_monitoring())
            else:
                print(f"📴 Device disconnected: {path}")
                if self.connected_device == path:
                    self.connected_device = None
                    self._stop_rssi_monitoring()
                    self._emergency_stop()  # Safety: stop on disconnect

    def _start_rssi_monitoring(self):
        """Start monitoring RSSI"""
        if self.rssi_timer:
            GLib.source_remove(self.rssi_timer)
        
        def check_rssi():
            if not self.connected_device:
                return False
                
            try:
                device_obj = self.bus.get_object(BLUEZ_SERVICE, self.connected_device)
                device_props = dbus.Interface(device_obj, DBUS_PROP_IFACE)
                
                # RSSI is only available during active connection, not always present
                # Try to get it, but don't fail if not available
                try:
                    rssi = device_props.Get("org.bluez.Device1", "RSSI")
                    
                    # Emergency stop if signal too weak
                    if rssi < -85:
                        print(f"⚠️ Weak signal: {rssi} dBm - Emergency stop!")
                        self._emergency_stop()
                        self.send_to_phone(f"⚠️ Signal weak: {rssi}dBm")
                except dbus.exceptions.DBusException as rssi_error:
                    # RSSI not available - this is normal for some connections
                    pass
                    
            except Exception as e:
                print(f"⚠️ RSSI monitoring error: {e}")
                
            return True  # Continue monitoring
        
        self.rssi_timer = GLib.timeout_add_seconds(5, check_rssi)
        print("📡 RSSI monitoring started (checking every 5s)")

    def _stop_rssi_monitoring(self):
        """Stop monitoring RSSI"""
        if self.rssi_timer:
            GLib.source_remove(self.rssi_timer)
            self.rssi_timer = None
            print("📡 RSSI monitoring stopped")

    def _register_app_cb(self):
        print('✅ GATT application registered successfully')
        print(f'   Service path: {self.app.get_path()}')
        print(f'   Services: {len(self.app.services)}')
        for service in self.app.services:
            print(f'   - Service UUID: {service.uuid}')
            print(f'     Characteristics: {len(service.characteristics)}')

    def _register_app_error_cb(self, error):
        print(f'❌ Failed to register GATT application: {error}')
        sys.exit(1)

    def _register_ad_cb(self):
        print('✅ Advertisement registered successfully')
        print('\n' + '='*50)
        print('🎯 Direct D-Bus BLE Server Ready!')
        print('='*50)
        print(f'Service UUID: {UART_SERVICE_UUID}')
        print(f'RX UUID: {UART_RX_CHAR_UUID}')
        print(f'TX UUID: {UART_TX_CHAR_UUID}')
        print(f'Device Name: AutoBBB')
        print('Waiting for iPad to connect...')
        print('='*50)
        
        # Debug: Verify services are accessible via D-Bus
        try:
            managed = self.app.GetManagedObjects()
            print(f'\n🔍 Debug: Managed objects count: {len(managed)}')
            for path, interfaces in managed.items():
                print(f'  Path: {path}')
                for iface, props in interfaces.items():
                    print(f'    Interface: {iface}')
        except Exception as e:
            print(f'⚠️ Could not verify managed objects: {e}')

    def _register_ad_error_cb(self, error):
        print(f'❌ Failed to register advertisement: {error}')
        sys.exit(1)

    def send_to_phone(self, data):
        """Send data to phone via TX characteristic"""
        if self.tx_char:
            return self.tx_char.send_data(data)
        return False

    def run(self):
        """Start the server"""
        self.mainloop = GLib.MainLoop()
        try:
            self.mainloop.run()
        except KeyboardInterrupt:
            print('\n👋 Shutting down...')
            self._emergency_stop()
            self._cleanup_hardware()
            self.mainloop.quit()


def main():
    """Main entry point"""
    print('='*60)
    print('🚗 AutoBBB Direct D-Bus BLE Server')
    print('='*60)
    
    server = BLEServer()
    server.run()


if __name__ == '__main__':
    main()