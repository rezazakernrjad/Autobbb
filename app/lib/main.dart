import 'package:flutter/material.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:permission_handler/permission_handler.dart';
import 'dart:convert';
import 'dart:async';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'BBB Controller',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: BBBController(),
    );
  }
}

class BBBController extends StatefulWidget {
  @override
  _BBBControllerState createState() => _BBBControllerState();
}

class _BBBControllerState extends State<BBBController> {
  BluetoothDevice? connectedDevice;
  BluetoothCharacteristic? rxCharacteristic;
  bool isScanning = false;
  bool isConnected = false;
  List<BluetoothDevice> devicesList = [];
  double pwmValue = 0;
  double turnValue = 0;

  BluetoothAdapterState _adapterState = BluetoothAdapterState.unknown;
  StreamSubscription<BluetoothAdapterState>? _adapterStateSubscription;
  bool _isBluetoothReady = false;

  final String SERVICE_UUID = '6E400001-B5A3-F393-E0A9-E50E24DCCA9E';
  final String RX_UUID = '6E400002-B5A3-F393-E0A9-E50E24DCCA9E';

  @override
  void initState() {
    super.initState();
    _initBluetooth();
  }

  @override
  void dispose() {
    _adapterStateSubscription?.cancel();
    super.dispose();
  }

  Future<void> _initBluetooth() async {
    print('🔵 Initializing Bluetooth...');
    await _requestPermissions();
    
    _adapterStateSubscription = FlutterBluePlus.adapterState.listen((state) {
      print('🔵 Bluetooth adapter state changed: $state');
      setState(() {
        _adapterState = state;
        _isBluetoothReady = (state == BluetoothAdapterState.on);
      });
    });

    // Special handling for iOS
    if (Theme.of(context).platform == TargetPlatform.iOS) {
      await _initBluetoothIOS();
    }
  }

  Future<void> _initBluetoothIOS() async {
    print('📱 iOS/iPadOS Bluetooth initialization');
    try {
      // Wait a bit for iOS Bluetooth to initialize
      await Future.delayed(Duration(seconds: 2));
    } catch (e) {
      print('❌ iOS Bluetooth init error: $e');
    }
  }

  Future<void> _requestPermissions() async {
    print('📋 Requesting permissions...');
    await Permission.bluetooth.request();
    await Permission.bluetoothScan.request();
    await Permission.bluetoothConnect.request();
    await Permission.locationWhenInUse.request(); // Important for iOS
    print('✅ Permissions requested');
  }

  Future<void> scanForDevices() async {
    if (isScanning) return;
    
    setState(() {
      isScanning = true;
      devicesList.clear();
    });

    try {
      print('🔍 Starting BLE scan...');
      await FlutterBluePlus.startScan(timeout: Duration(seconds: 6));

      FlutterBluePlus.scanResults.listen((results) {
        for (ScanResult result in results) {
          // Only look for Auto BBB devices
          if (result.device.name.isNotEmpty && 
              result.device.name.toLowerCase().contains('bbb')) {
            if (!devicesList.any((d) => d.id == result.device.id)) {
              print('✅ Found Auto BBB device: ${result.device.name}');
              setState(() {
                devicesList.add(result.device);
              });
            }
          }
        }
      });

      await Future.delayed(Duration(seconds: 6));
      await FlutterBluePlus.stopScan();
      
      if (devicesList.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('No Auto BBB devices found. Ensure device is on and nearby.'),
            duration: Duration(seconds: 3),
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Found ${devicesList.length} Auto BBB device(s)'),
            duration: Duration(seconds: 2),
          ),
        );
      }
      
    } catch (e) {
      print('❌ Scan error: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Scan failed: $e')),
      );
    } finally {
      setState(() => isScanning = false);
    }
  }

  Future<void> connectToDevice(BluetoothDevice device) async {
    try {
      print('🔵 Connecting to: ${device.name}');
      
      // FIX: Remove autoConnect to avoid MTU conflict
      await device.connect(
        timeout: Duration(seconds: 15),
        // autoConnect: true, // REMOVED - causes MTU conflict
      );
      
      setState(() {
        connectedDevice = device;
        isConnected = true;
      });

      print('🔍 Discovering services...');
      List<BluetoothService> services = await device.discoverServices();
      
      bool serviceFound = false;
      bool characteristicFound = false;
      
      for (BluetoothService service in services) {
        print('🔧 Service UUID: ${service.uuid.toString().toUpperCase()}');
        
        if (service.uuid.toString().toUpperCase() == SERVICE_UUID.toUpperCase()) {
          serviceFound = true;
          print('✅ Found BBB service');
          
          for (BluetoothCharacteristic characteristic in service.characteristics) {
            print('🔍 Characteristic UUID: ${characteristic.uuid.toString().toUpperCase()}');
            
            if (characteristic.uuid.toString().toUpperCase() == RX_UUID.toUpperCase()) {
              rxCharacteristic = characteristic;
              characteristicFound = true;
              print('✅ Found RX characteristic');
              
              // Print characteristic properties for debugging
              print('📊 Characteristic properties:');
              print('   Write: ${characteristic.properties.write}');
              print('   WriteWithoutResponse: ${characteristic.properties.writeWithoutResponse}');
              print('   Read: ${characteristic.properties.read}');
              print('   Notify: ${characteristic.properties.notify}');
              
              break;
            }
          }
          break;
        }
      }
      
      if (!serviceFound) {
        print('❌ Target service not found');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('❌ BBB service not found. Check UUIDs.')),
        );
        await _disconnect();
      } else if (!characteristicFound) {
        print('❌ RX characteristic not found');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('❌ RX characteristic not found')),
        );
        await _disconnect();
      } else {
        print('🎉 Ready to send commands!');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('🎉 Connected to Auto BBB!')),
        );
      }
      
    } catch (e) {
      print('❌ Connection error: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Connection failed: $e')),
      );
      await _disconnect();
    }
  }

  Future<void> sendCommand(String command) async {
    if (!isConnected || rxCharacteristic == null) {
      print('❌ Not connected or characteristic not ready');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('❌ Not connected to Auto BBB')),
      );
      return;
    }
    
    try {
      List<int> bytes = utf8.encode(command);
      print('🔵 Sending command: "$command" as bytes: $bytes');
      
      // Try with response first, fallback to without response
      if (rxCharacteristic!.properties.write) {
        await rxCharacteristic!.write(bytes, withoutResponse: false);
      } else if (rxCharacteristic!.properties.writeWithoutResponse) {
        await rxCharacteristic!.write(bytes, withoutResponse: true);
      } else {
        throw Exception('Characteristic does not support write operations');
      }
      
      print('✅ Successfully sent: $command');
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('✅ Sent: $command')),
      );
    } catch (e) {
      print('❌ Send error: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('❌ Send failed: $e')),
      );
    }
  }

  Future<void> _disconnect() async {
    try {
      if (connectedDevice != null) {
        await connectedDevice!.disconnect();
      }
    } catch (e) {
      print('⚠️ Disconnect error: $e');
    } finally {
      setState(() {
        isConnected = false;
        connectedDevice = null;
        rxCharacteristic = null;
        pwmValue = 0;
        turnValue = 0;
        devicesList.clear();
      });
    }
  }

  String _getBluetoothStateMessage() {
    switch (_adapterState) {
      case BluetoothAdapterState.on: return 'Bluetooth is ON - Ready to scan';
      case BluetoothAdapterState.off: return 'Bluetooth is OFF - Please enable in Settings';
      case BluetoothAdapterState.unknown: return 'Bluetooth Initializing...';
      default: return 'Bluetooth Status';
    }
  }

  Color _getBluetoothStateColor() {
    switch (_adapterState) {
      case BluetoothAdapterState.on: return Colors.green[100]!;
      case BluetoothAdapterState.off: return Colors.orange[100]!;
      default: return Colors.blue[100]!;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Auto BBB Controller'),
        backgroundColor: Colors.blue,
        actions: [
          if (isConnected)
            IconButton(
              icon: Icon(Icons.bluetooth_disabled),
              onPressed: _disconnect,
              tooltip: 'Disconnect',
            ),
        ],
      ),
      body: Padding(
        padding: EdgeInsets.all(16.0),
        child: Column(
          children: [
            // Bluetooth Status Banner
            Container(
              padding: EdgeInsets.all(16),
              margin: EdgeInsets.only(bottom: 16),
              decoration: BoxDecoration(
                color: _getBluetoothStateColor(),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  Icon(
                    _isBluetoothReady 
                        ? Icons.bluetooth 
                        : Icons.bluetooth_disabled,
                    color: _isBluetoothReady ? Colors.green : Colors.orange,
                  ),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      _getBluetoothStateMessage(),
                      style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                    ),
                  ),
                ],
              ),
            ),
            
            // Connection Status
            Container(
              padding: EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: isConnected ? Colors.green[100] : Colors.red[100],
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  Icon(
                    isConnected ? Icons.bluetooth_connected : Icons.bluetooth_disabled,
                    color: isConnected ? Colors.green : Colors.red,
                  ),
                  SizedBox(width: 8),
                  Text(
                    isConnected ? 'Connected to Auto BBB' : 'Not Connected to Auto BBB',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                ],
              ),
            ),
            
            SizedBox(height: 20),
            
            // Scan Button
            if (!isConnected) ...[
              ElevatedButton(
                onPressed: isScanning ? null : scanForDevices,
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (isScanning) 
                      SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                    SizedBox(width: 8),
                    Text(isScanning ? 'Scanning...' : 'Scan for Auto BBB'),
                  ],
                ),
              ),
              
              SizedBox(height: 8),
              
              if (_adapterState == BluetoothAdapterState.unknown && 
                  Theme.of(context).platform == TargetPlatform.iOS)
                Text(
                  'On iOS, you can try scanning even if Bluetooth shows "Initializing"',
                  style: TextStyle(fontSize: 12, color: Colors.grey, fontStyle: FontStyle.italic),
                  textAlign: TextAlign.center,
                ),
              
              // Device List
              if (devicesList.isNotEmpty)
                Expanded(
                  child: Container(
                    margin: EdgeInsets.only(top: 16),
                    child: Column(
                      children: [
                        Text(
                          'Found Auto BBB Devices:',
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                        ),
                        SizedBox(height: 8),
                        Expanded(
                          child: ListView.builder(
                            itemCount: devicesList.length,
                            itemBuilder: (context, index) {
                              return Card(
                                margin: EdgeInsets.symmetric(vertical: 4),
                                child: ListTile(
                                  leading: Icon(Icons.bluetooth, color: Colors.blue),
                                  title: Text(
                                    devicesList[index].name.isEmpty 
                                        ? 'Auto BBB Device' 
                                        : devicesList[index].name,
                                    style: TextStyle(fontWeight: FontWeight.bold),
                                  ),
                                  subtitle: Text('Tap to connect'),
                                  trailing: Icon(Icons.chevron_right, color: Colors.blue),
                                  onTap: () => connectToDevice(devicesList[index]),
                                ),
                              );
                            },
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
            ],
            
            // Control Buttons (only show when connected)
            if (isConnected) ...[
              SizedBox(height: 20),
              Text('Auto BBB Motor Control', 
                   style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.blue)),
              SizedBox(height: 20),
              
              Text('Forward Speed: ${pwmValue.round()}%', 
                   style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              Slider(
                value: pwmValue,
                min: 0,
                max: 100,
                divisions: 100,
                onChanged: (value) {
                  setState(() => pwmValue = value);
                  sendCommand("forward ${value.round()}");
                },
              ),

              SizedBox(height: 30),
              
              Text('Turning: ${turnValue.round()}%', 
                   style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              Slider(
                value: turnValue,
                min: -100,
                max: 100,
                divisions: 200,
                onChanged: (value) {
                  setState(() => turnValue = value);
                  if (value < 0) {
                    sendCommand("turn_left ${(-value).round()}");
                  } else if (value > 0) {
                    sendCommand("turn_right ${value.round()}");
                  } else {
                    sendCommand("turn_stop");
                  }
                },
              ),
              
              SizedBox(height: 30),
              
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  ElevatedButton(
                    onPressed: () => sendCommand("stop"),
                    child: Text('STOP', style: TextStyle(fontWeight: FontWeight.bold)),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.red,
                      foregroundColor: Colors.white,
                      padding: EdgeInsets.symmetric(horizontal: 20, vertical: 15),
                    ),
                  ),
                  ElevatedButton(
                    onPressed: () => sendCommand("status"),
                    child: Text('STATUS', style: TextStyle(fontWeight: FontWeight.bold)),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blue,
                      foregroundColor: Colors.white,
                      padding: EdgeInsets.symmetric(horizontal: 20, vertical: 15),
                    ),
                  ),
                ],
              ),

              SizedBox(height: 20),
              
              ElevatedButton(
                onPressed: _disconnect,
                child: Text('DISCONNECT FROM BBB', style: TextStyle(fontWeight: FontWeight.bold)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.orange,
                  foregroundColor: Colors.white,
                  padding: EdgeInsets.symmetric(horizontal: 20, vertical: 15),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}