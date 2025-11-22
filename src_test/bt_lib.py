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
        # Motor control state
        self.motor_speed = 0
        self.turn_angle = 0
        self.illumination_level = 0
        
        # Setup D-Bus
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SystemBus()
        
        # Get BlueZ adapter
        adapter_path = '/org/bluez/hci0'
        obj = self.bus.get_object(BLUEZ_SERVICE, adapter_path)
        self.adapter_props = dbus.Interface(obj, DBUS_PROP_IFACE)
        self.adapter_obj = obj
        
        # Ensure adapter is powered on
        self.adapter_props.Set('org.bluez.Adapter1', 'Powered', dbus.Boolean(True))
        self.adapter_props.Set('org.bluez.Adapter1', 'Discoverable', dbus.Boolean(True))
        
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
            
            cmd = parts[0].lower()
            value = float(parts[1]) if len(parts) > 1 else 0
            print(f"Command: '{cmd}', Value: {value}")

            # Motor control commands
            if cmd == "car_status":
                return f"✓ CAR IS READY"
            
            elif cmd == "illumination":
                print(f"Setting illumination to {value}")
                self.lamps_control(20, value)
                self.illumination_level = value
                return f"✓ Illumination effect {value}"
            
            elif cmd == "turn_left":
                self.turn_left(value)
                self.turn_angle = value
                return f"✓ turn left {value}"
            
            elif cmd == "turn_right":
                self.turn_right(value)
                self.turn_angle = value
                return f"✓ turn right {value}"
            
            elif cmd == "turn_end":
                self.turn_end()
                return "✓ turn end"
            
            elif cmd == "forward":
                self.move_forward(value)
                self.motor_speed = value
                return f"✓ forward {value}"
            
            elif cmd == "reverse":
                self.move_reverse()
                return "✓ reverse"
            
            elif cmd == "brake":
                self.brake_movement()
                return "✓ brake"
            
            # Status query
            elif cmd == "status":
                return f"Motor:{self.motor_speed} Turn:{self.turn_angle} Illum:{self.illumination_level}"
            
            else:
                return f"ERROR: Unknown command '{cmd}'"
                
        except Exception as e:
            error_msg = f"ERROR: {str(e)}"
            print(f"❌ Command error: {error_msg}")
            return error_msg
        
    def _emergency_stop(self):
        """Emergency stop - immediately halt all motion"""
        print("🛑 EMERGENCY STOP")
        self.move_forward(0)
        self.turn_right(0)

    def _on_device_connected(self, interface, changed, invalidated, path):
        """Handle device connection/disconnection"""
        if "org.bluez.Device1" not in interface:
            return
            
        if "Connected" in changed:
            is_connected = changed["Connected"]
            
            if is_connected:
                print(f"📱 Device connected: {path}")
                self.connected_device = path
                self._start_rssi_monitoring()
            else:
                print(f"📴 Device disconnected: {path}")
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