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
  bool isConnecting = false;
  List<BluetoothDevice> devicesList = [];
  double pwmValue = 0;
  double turnValue = 0;

  BluetoothAdapterState _adapterState = BluetoothAdapterState.unknown;
  StreamSubscription<BluetoothAdapterState>? _adapterStateSubscription;
  bool _isBluetoothReady = false;
  
  int _mtu = 23; // Default BLE MTU

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

    if (Theme.of(context).platform == TargetPlatform.iOS) {
      await _initBluetoothIOS();
    }
  }

  Future<void> _initBluetoothIOS() async {
    print('📱 iOS/iPadOS Bluetooth initialization');
    try {
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
    await Permission.locationWhenInUse.request();
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
    if (isConnecting) return;
    
    setState(() {
      isConnecting = true;
    });

    try {
      print('🔵 Connecting to: ${device.name}');
      
      // Disconnect first if already connected to another device
      if (connectedDevice != null && connectedDevice != device) {
        await _disconnect();
      }
      
      await device.connect(timeout: Duration(seconds: 15));
      
      print('✅ Connected to device');
      
      setState(() {
        connectedDevice = device;
        isConnected = true;
        isConnecting = false;
      });

      // Request MTU increase (important for iOS)
      try {
        print('📶 Requesting MTU...');
        final mtu = await device.mtu.first;
        print('📶 Current MTU: $mtu');
        
        // Try to increase MTU
        await device.requestMtu(512);
        final newMtu = await device.mtu.first;
        setState(() {
          _mtu = newMtu;
        });
        print('📶 New MTU: $newMtu');
      } catch (e) {
        print('⚠️ MTU request failed: $e');
      }

      // Discover services with retry
      await _discoverServicesWithRetry(device);
      
    } catch (e) {
      print('❌ Connection error: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Connection failed: $e')),
      );
      setState(() {
        isConnecting = false;
      });
      await _disconnect();
    }
  }

  Future<void> _discoverServicesWithRetry(BluetoothDevice device) async {
    int retries = 3;
    
    for (int i = 0; i < retries; i++) {
      try {
        print('🔎 Discovering services (attempt ${i + 1}/$retries)...');
        List<BluetoothService> services = await device.discoverServices();
        print('📋 Found ${services.length} services');
        
        bool serviceFound = false;
        bool characteristicFound = false;
        
        for (BluetoothService service in services) {
          print('🔧 Service UUID: ${service.uuid.toString().toUpperCase()}');
          
          if (service.uuid.toString().toUpperCase() == SERVICE_UUID.toUpperCase()) {
            serviceFound = true;
            print('✅ Found target service!');
            
            for (BluetoothCharacteristic characteristic in service.characteristics) {
              print('🔍 Characteristic UUID: ${characteristic.uuid.toString().toUpperCase()}');
              
              if (characteristic.uuid.toString().toUpperCase() == RX_UUID.toUpperCase()) {
                rxCharacteristic = characteristic;
                characteristicFound = true;
                print('✅ Found RX characteristic!');
                
                // Print characteristic properties
                print('📊 Characteristic properties:');
                print('   Write: ${characteristic.properties.write}');
                print('   WriteWithoutResponse: ${characteristic.properties.writeWithoutResponse}');
                print('   Notify: ${characteristic.properties.notify}');
                print('   Read: ${characteristic.properties.read}');
                
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
          return;
        } else if (!characteristicFound) {
          print('❌ RX characteristic not found');
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('❌ RX characteristic not found')),
          );
          await _disconnect();
          return;
        } else {
          // Add delay for iOS stability
          print('⏳ Waiting for connection to stabilize...');
          await Future.delayed(Duration(milliseconds: 500));
          
          print('🎉 Ready to send commands!');
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('🎉 Connected and ready!')),
          );
          return; // Success
        }
      } catch (e) {
        print('❌ Service discovery error (attempt ${i + 1}): $e');
        if (i < retries - 1) {
          print('🔄 Retrying service discovery...');
          await Future.delayed(Duration(seconds: 1));
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('❌ Service discovery failed after $retries attempts')),
          );
          await _disconnect();
        }
      }
    }
  }

  Future<void> sendCommand(String command) async {
    if (!isConnected || rxCharacteristic == null) {
      print('❌ Cannot send: Not connected or no RX characteristic');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('❌ Not connected to device')),
      );
      return;
    }
    
    try {
      // Format command - try newline terminator (most common for UART)
      String formattedCommand = command + '\n';
      List<int> bytes = utf8.encode(formattedCommand);
      
      print('📤 Sending command: "$command"');
      print('📤 Bytes: $bytes (length: ${bytes.length})');
      print('📤 MTU: $_mtu');
      
      // Check if command fits in MTU (leave 3 bytes for ATT overhead)
      if (bytes.length > (_mtu - 3)) {
        print('⚠️ Command too long for MTU!');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('⚠️ Command too long')),
        );
        return;
      }
      
      // CRITICAL: Use writeWithoutResponse and add delay for iOS BLE
      // iOS needs time between writes, and BBB might need writeWithoutResponse
      if (rxCharacteristic!.properties.writeWithoutResponse) {
        try {
          print('📝 Writing WITHOUT response (iOS/BBB compatible mode)...');
          
          // Split into smaller chunks if needed (max 20 bytes for compatibility)
          const int maxChunkSize = 20;
          
          if (bytes.length <= maxChunkSize) {
            // Send in one go
            await rxCharacteristic!.write(bytes, withoutResponse: true);
            print('✅ Sent ${bytes.length} bytes');
          } else {
            // Send in chunks
            print('📦 Splitting into chunks...');
            for (int i = 0; i < bytes.length; i += maxChunkSize) {
              int end = (i + maxChunkSize < bytes.length) ? i + maxChunkSize : bytes.length;
              List<int> chunk = bytes.sublist(i, end);
              
              await rxCharacteristic!.write(chunk, withoutResponse: true);
              print('✅ Sent chunk ${(i / maxChunkSize).floor() + 1}: ${chunk.length} bytes');
              
              // Small delay between chunks
              if (end < bytes.length) {
                await Future.delayed(Duration(milliseconds: 50));
              }
            }
          }
          
          // Add delay after sending to ensure BBB processes it
          await Future.delayed(Duration(milliseconds: 100));
          
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('✅ Sent: $command'),
              duration: Duration(seconds: 1),
            ),
          );
          
        } catch (e) {
          print('❌ Write failed: $e');
          throw e;
        }
      } else {
        print('❌ WriteWithoutResponse not supported by characteristic');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('❌ Device does not support required write mode')),
        );
      }
      
    } catch (e) {
      print('❌ Send error: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('❌ Send failed: $e')),
      );
    }
  }

  Future<void> _testSendFormat(String data, String formatName) async {
    if (rxCharacteristic == null) return;
    
    try {
      List<int> bytes = utf8.encode(data);
      print('🧪 TEST [$formatName]: bytes=$bytes');
      await rxCharacteristic!.write(bytes, withoutResponse: true);
      await Future.delayed(Duration(milliseconds: 100));
    } catch (e) {
      print('❌ TEST [$formatName] failed: $e');
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
        isConnecting = false;
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
                color: isConnected ? Colors.green[100] : (isConnecting ? Colors.orange[100] : Colors.red[100]),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                children: [
                  Icon(
                    isConnected ? Icons.bluetooth_connected : 
                         (isConnecting ? Icons.bluetooth_searching : Icons.bluetooth_disabled),
                    color: isConnected ? Colors.green : (isConnecting ? Colors.orange : Colors.red),
                  ),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      isConnected 
                          ? 'Connected to Auto BBB (MTU: $_mtu)' 
                          : (isConnecting ? 'Connecting to Auto BBB...' : 'Not Connected to Auto BBB'),
                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                  ),
                ],
              ),
            ),
            
            SizedBox(height: 20),
            
            // Scan Button
            if (!isConnected && !isConnecting) ...[
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
                                  trailing: isConnecting 
                                      ? CircularProgressIndicator()
                                      : Icon(Icons.chevron_right, color: Colors.blue),
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
                onChangeEnd: (value) {
                  double newValue = 0;
                  setState(() => turnValue = newValue);
                  //sendCommand("forward ${pwmValue.round()/10}");
                  print('Ended change on $pwmValue');
              },
              ),
              
              SizedBox(height: 30),
              
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  ElevatedButton(
                    onPressed: () => sendCommand("brake"),
                    child: Text('BRAKE', style: TextStyle(fontWeight: FontWeight.bold)),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.red,
                      foregroundColor: Colors.white,
                    ),
                  ),
                  ElevatedButton(
                    onPressed: () => sendCommand("status"),
                    child: Text('STATUS', style: TextStyle(fontWeight: FontWeight.bold)),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blue,
                      foregroundColor: Colors.white,
                    ),
                  ),
                  ElevatedButton(
                    onPressed: () => sendCommand("illumination 1"),
                    child: Text('LAMPS', style: TextStyle(fontWeight: FontWeight.bold)),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green,
                      foregroundColor: Colors.white,
                    ),
                  ),
                ],
              ),
              
              SizedBox(height: 20),
              
              // Test different formats button
              /* ElevatedButton(
                onPressed: () async {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Testing different formats...')),
                  );
                  
                  // Test 1: Just "ping" with newline
                  await _testSendFormat("ping\n", "newline only");
                  await Future.delayed(Duration(seconds: 2));
                  
                  // Test 2: "ping" with CR+LF
                  await _testSendFormat("ping\r\n", "CR+LF");
                  await Future.delayed(Duration(seconds: 2));
                  
                  // Test 3: Just "ping" no terminator
                  await _testSendFormat("ping", "no terminator");
                  await Future.delayed(Duration(seconds: 2));
                  
                  // Test 4: Single character
                  await _testSendFormat("p", "single char");
                  
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Format test complete! Check BBB logs')),
                  );
                },
                child: Text('TEST FORMATS'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.purple,
                  foregroundColor: Colors.white,
                ),
              ), */

              SizedBox(height: 20),
              
              ElevatedButton(
                onPressed: _disconnect,
                child: Text('DISCONNECT'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.orange,
                  foregroundColor: Colors.white,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}