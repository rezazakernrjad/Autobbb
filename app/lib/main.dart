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
  BluetoothCharacteristic? txCharacteristic;
  bool isScanning = false;
  bool isConnected = false;
  bool isConnecting = false;
  List<BluetoothDevice> devicesList = [];
  double pwmValue = 0;
  double turnValue = 0;

  BluetoothAdapterState _adapterState = BluetoothAdapterState.unknown;
  StreamSubscription<BluetoothAdapterState>? _adapterStateSubscription;
  StreamSubscription<List<int>>? txSubscription;
  StreamSubscription<BluetoothConnectionState>? _connectionStateSubscription;
  bool _isBluetoothReady = false;
  bool _isDisconnecting = false; // Flag to track intentional disconnect
  
  int _mtu = 23; // Default BLE MTU
  String lastResponse = '';
  List<String> responseHistory = [];

  final String SERVICE_UUID = '6E400001-B5A3-F393-E0A9-E50E24DCCA9E';
  final String RX_UUID = '6E400002-B5A3-F393-E0A9-E50E24DCCA9E';
  final String TX_UUID = '6E400003-B5A3-F393-E0A9-E50E24DCCA9E';

  @override
  void initState() {
    super.initState();
    _initBluetooth();
  }

  @override
  void dispose() {
    print('🗑️ Disposing widget...');
    _adapterStateSubscription?.cancel();
    txSubscription?.cancel();
    _connectionStateSubscription?.cancel();
    // Disconnect if still connected
    if (connectedDevice != null) {
      connectedDevice!.disconnect().catchError((e) {
        print('⚠️ Error disconnecting during dispose: $e');
      });
    }
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
      await FlutterBluePlus.startScan(timeout: const Duration(seconds: 6));

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

      await Future.delayed(const Duration(seconds: 6));
      await FlutterBluePlus.stopScan();
      
      if (!mounted) return;
      
      if (devicesList.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('No Auto BBB devices found. Ensure device is on and nearby.'),
            duration: Duration(seconds: 3),
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Found ${devicesList.length} Auto BBB device(s)'),
            duration: const Duration(seconds: 2),
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
    print('🔵 Connect requested for: ${device.name}');
    
    // Prevent multiple simultaneous connections
    if (isConnecting) {
      print('⚠️ Already connecting, please wait...');
      return;
    }
    
    setState(() {
      isConnecting = true;
    });

    try {
      print('🔵 Connecting to: ${device.name}');
      
      // Disconnect first if already connected to another device
      if (connectedDevice != null && connectedDevice != device) {
        print('🔄 Disconnecting from previous device...');
        await _disconnect();
        // Small delay after disconnect before reconnecting
        await Future.delayed(const Duration(milliseconds: 500));
      }
      
      // Ensure device is not already connected
      var currentState = await device.connectionState.first;
      if (currentState == BluetoothConnectionState.connected) {
        print('⚠️ Device already connected, disconnecting first...');
        await device.disconnect();
        await Future.delayed(const Duration(milliseconds: 500));
      }
      
      print('📡 Initiating connection...');
      await device.connect(
        timeout: const Duration(seconds: 15),
        autoConnect: false, // Disable auto-connect to have more control
      );
      
      print('✅ Connected to device');
      
      // Verify connection established
      var verifyState = await device.connectionState.first.timeout(Duration(seconds: 2));
      print('📊 Connection state verified: $verifyState');
      
      // Monitor connection state for unexpected disconnects
      _connectionStateSubscription?.cancel(); // Cancel any existing subscription
      _connectionStateSubscription = device.connectionState.listen((state) {
        final timestamp = DateTime.now().toString().substring(11, 23);
        print('🔗 [$timestamp] Connection state changed: $state');
        if (state == BluetoothConnectionState.disconnected) {
          print('⚠️ [$timestamp] Device disconnected!');
          // Only handle unexpected disconnects, not intentional ones
          if (mounted && !_isDisconnecting) {
            print('⚠️ [$timestamp] Unexpected disconnect detected');
            _resetState();
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('⚠️ Device disconnected unexpectedly'),
                backgroundColor: Colors.orange,
              ),
            );
          } else {
            print('ℹ️ [$timestamp] Intentional disconnect, ignoring');
          }
        }
      });
      
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

      // Longer delay to let BBB GATT services become fully available
      print('⏳ Waiting for GATT services to become available...');
      await Future.delayed(const Duration(seconds: 3));
      
      // Check if still connected
      var connectionState = await device.connectionState.first;
      if (connectionState != BluetoothConnectionState.connected) {
        throw Exception('Device disconnected before service discovery');
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
    int retries = 5; // Increased retries
    
    for (int i = 0; i < retries; i++) {
      try {
        print('🔎 Discovering services (attempt ${i + 1}/$retries)...');
        
        // Add a delay before retry (except first attempt)
        if (i > 0) {
          print('⏳ Waiting before retry...');
          await Future.delayed(Duration(milliseconds: 500)); // Shorter delay
        }
        
        // Check connection state before attempting discovery
        var state = await device.connectionState.first.timeout(Duration(seconds: 2));
        if (state != BluetoothConnectionState.connected) {
          throw Exception('Device not connected (state: $state)');
        }
        
        print('📡 Starting service discovery...');
        // Don't add timeout - let flutter_blue_plus handle it
        // The internal timeout is 15s on iOS
        List<BluetoothService> services = await device.discoverServices();
        print('📋 Found ${services.length} services');
        
        bool serviceFound = false;
        bool rxFound = false;
        bool txFound = false;
        
        for (BluetoothService service in services) {
          print('🔧 Service UUID: ${service.uuid.toString().toUpperCase()}');
          
          if (service.uuid.toString().toUpperCase() == SERVICE_UUID.toUpperCase()) {
            serviceFound = true;
            print('✅ Found target service!');
            
            for (BluetoothCharacteristic characteristic in service.characteristics) {
              String charUuid = characteristic.uuid.toString().toUpperCase();
              print('🔍 Characteristic UUID: $charUuid');
              
              // Find RX characteristic (for sending TO BBB)
              if (charUuid == RX_UUID.toUpperCase()) {
                rxCharacteristic = characteristic;
                rxFound = true;
                print('✅ Found RX characteristic (write to BBB)');
                print('   Write: ${characteristic.properties.write}');
                print('   WriteWithoutResponse: ${characteristic.properties.writeWithoutResponse}');
              }
              
              // Find TX characteristic (for receiving FROM BBB)
              if (charUuid == TX_UUID.toUpperCase()) {
                txCharacteristic = characteristic;
                txFound = true;
                print('✅ Found TX characteristic (receive from BBB)');
                print('   Notify: ${characteristic.properties.notify}');
                print('   Read: ${characteristic.properties.read}');
                
                // Subscribe to notifications from BBB
                try {
                  await txCharacteristic!.setNotifyValue(true);
                  print('📡 Enabled notifications on TX characteristic');
                  
                  // Listen for data from BBB
                  txSubscription?.cancel(); // Cancel any existing subscription
                  txSubscription = txCharacteristic!.lastValueStream.listen((value) {
                    if (value.isNotEmpty) {
                      String response = utf8.decode(value);
                      print('📥 Response from BBB: "$response"');
                      
                      if (mounted) {
                        setState(() {
                          lastResponse = response;
                          responseHistory.insert(0, '${DateTime.now().toString().substring(11, 19)}: $response');
                          if (responseHistory.length > 10) {
                            responseHistory.removeLast();
                          }
                        });
                        
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text('BBB: $response'),
                            duration: Duration(seconds: 2),
                            backgroundColor: Colors.green[700],
                          ),
                        );
                      }
                    }
                  }, onError: (error) {
                    print('❌ TX subscription error: $error');
                  });
                  
                  print('✅ Subscribed to TX notifications');
                } catch (e) {
                  print('⚠️ Failed to subscribe to TX notifications: $e');
                }
              }
            }
            break; // Found our service, no need to continue
          }
        }
        
        if (!serviceFound) {
          print('❌ Target service not found');
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('❌ BBB service not found. Check UUIDs.')),
          );
          await _disconnect();
          return;
        } else if (!rxFound) {
          print('❌ RX characteristic not found');
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('❌ RX characteristic not found')),
          );
          await _disconnect();
          return;
        } else if (!txFound) {
          print('⚠️ TX characteristic not found - no responses from BBB');
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('⚠️ Connected but cannot receive responses'),
              backgroundColor: Colors.orange,
            ),
          );
        }
        
        // Add delay for iOS stability
        print('⏳ Waiting for connection to stabilize...');
        await Future.delayed(const Duration(milliseconds: 500));
        
        print('🎉 Ready to send commands!');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('🎉 Connected! RX:${rxFound ? "✓" : "✗"} TX:${txFound ? "✓" : "✗"}'),
            backgroundColor: Colors.green,
          ),
        );
        return; // Success
        
      } catch (e) {
        print('❌ Service discovery error (attempt ${i + 1}): $e');
        if (i < retries - 1) {
          print('🔄 Retrying service discovery...');
          await Future.delayed(const Duration(seconds: 1));
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
        const SnackBar(content: Text('❌ Not connected to device')),
      );
      return;
    }
    
    try {
      // Format command - newline terminator for UART
      String formattedCommand = command + '\n';
      List<int> bytes = utf8.encode(formattedCommand);
      
      print('📤 Sending command: "$command"');
      print('📤 Bytes: $bytes (length: ${bytes.length})');
      print('📤 MTU: $_mtu');
      
      // Check if command fits in MTU (leave 3 bytes for ATT overhead)
      if (bytes.length > (_mtu - 3)) {
        print('⚠️ Command too long for MTU!');
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('⚠️ Command too long')),
        );
        return;
      }
      
      // Use writeWithoutResponse (iOS/BBB compatible)
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
                await Future.delayed(const Duration(milliseconds: 50));
              }
            }
          }
          
          // Add delay after sending to ensure BBB processes it
          await Future.delayed(const Duration(milliseconds: 20));
          
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('✅ Sent: $command'),
              duration: const Duration(seconds: 1),
            ),
          );
          
        } catch (e) {
          print('❌ Write failed: $e');
          throw e;
        }
      } else {
        print('❌ WriteWithoutResponse not supported by characteristic');
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('❌ Device does not support required write mode')),
        );
      }
      
    } catch (e) {
      print('❌ Send error: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('❌ Send failed: $e')),
      );
    }
  }

  Future<void> _disconnect() async {
    print('🔴 Disconnect requested...');
    
    // Set flag to indicate intentional disconnect
    _isDisconnecting = true;
    
    // Prevent multiple simultaneous disconnect calls
    if (!isConnected && connectedDevice == null) {
      print('⚠️ Already disconnected');
      _resetState();
      _isDisconnecting = false;
      return;
    }
    
    // Store reference before clearing
    final deviceToDisconnect = connectedDevice;
    final txSub = txSubscription;
    final connStateSub = _connectionStateSubscription;
    
    // Cancel connection state listener FIRST to prevent triggering during disconnect
    if (connStateSub != null) {
      print('🚫 Cancelling connection state subscription first...');
      try {
        await connStateSub.cancel();
        _connectionStateSubscription = null;
      } catch (e) {
        print('⚠️ Error cancelling connection subscription: $e');
      }
    }
    
    // Clear state immediately to prevent UI interaction
    if (mounted) {
      setState(() {
        isConnected = false;
        isConnecting = false;
      });
    }
    
    try {
      // 1. Disable notifications first (critical for iOS)
      if (txCharacteristic != null && deviceToDisconnect != null) {
        try {
          print('🔕 Disabling TX notifications...');
          await txCharacteristic!.setNotifyValue(false).timeout(
            const Duration(seconds: 1),
          );
          print('✅ Notifications disabled');
        } on TimeoutException catch (_) {
          print('⚠️ Disable notifications timeout');
        } catch (e) {
          print('⚠️ Error disabling notifications: $e');
        }
      }
      
      // 2. Cancel TX subscription
      if (txSub != null) {
        print('🚫 Cancelling TX subscription...');
        try {
          await txSub.cancel();
        } catch (e) {
          print('⚠️ Error cancelling TX subscription: $e');
        }
      }
      
      // 3. Small delay to let BLE stack settle
      await Future.delayed(const Duration(milliseconds: 200));
      
      // 4. Disconnect from device
      if (deviceToDisconnect != null) {
        print('🔌 Disconnecting from device...');
        
        try {
          await deviceToDisconnect.disconnect().timeout(
            const Duration(seconds: 2),
          );
          print('✅ Device disconnected');
        } on TimeoutException catch (_) {
          print('⚠️ Disconnect timeout - forcing cleanup');
        } catch (e) {
          print('⚠️ Disconnect error (continuing cleanup): $e');
        }
      }
      
      print('✅ Disconnect sequence completed');
      
    } catch (e) {
      print('❌ Disconnect error: $e');
    } finally {
      // Always reset state regardless of errors
      _resetState();
      // Reset disconnect flag
      _isDisconnecting = false;
    }
  }
  
  void _resetState() {
    print('🔄 Resetting connection state...');
    
    // Clear characteristics first to prevent access
    rxCharacteristic = null;
    txCharacteristic = null;
    
    // Cancel subscriptions (already should be done, but safety measure)
    _connectionStateSubscription?.cancel();
    _connectionStateSubscription = null;
    txSubscription = null;
    
    if (mounted) {
      setState(() {
        isConnected = false;
        isConnecting = false;
        connectedDevice = null;
        pwmValue = 0;
        turnValue = 0;
        // Don't clear devicesList - keep scan results for reconnection
        // devicesList.clear();
        lastResponse = '';
        responseHistory.clear();
      });
    }
    print('✅ State reset complete');
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
        title: const Text('Auto BBB Controller'),
        backgroundColor: Colors.blue,
        actions: [
          if (isConnected)
            IconButton(
              icon: const Icon(Icons.bluetooth_disabled),
              onPressed: _disconnect,
              tooltip: 'Disconnect',
            ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            // Bluetooth Status Banner
            Container(
              padding: const EdgeInsets.all(16),
              margin: const EdgeInsets.only(bottom: 16),
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
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      _getBluetoothStateMessage(),
                      style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                    ),
                  ),
                ],
              ),
            ),
            
            // Connection Status
            Container(
              padding: const EdgeInsets.all(16),
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
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      isConnected 
                          ? 'Connected (MTU: $_mtu)' 
                          : (isConnecting ? 'Connecting...' : 'Not Connected'),
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    ),
                  ),
                ],
              ),
            ),
            
            const SizedBox(height: 20),
            
            // Scan Button
            if (!isConnected && !isConnecting) ...[
              ElevatedButton(
                onPressed: isScanning ? null : scanForDevices,
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    if (isScanning) 
                      const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                    const SizedBox(width: 8),
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
                        const Text(
                          'Found Auto BBB Devices:',
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 8),
                        Expanded(
                          child: ListView.builder(
                            itemCount: devicesList.length,
                            itemBuilder: (context, index) {
                              return Card(
                                margin: const EdgeInsets.symmetric(vertical: 4),
                                child: ListTile(
                                  leading: const Icon(Icons.bluetooth, color: Colors.blue),
                                  title: Text(
                                    devicesList[index].name.isEmpty 
                                        ? 'Auto BBB Device' 
                                        : devicesList[index].name,
                                    style: const TextStyle(fontWeight: FontWeight.bold),
                                  ),
                                  subtitle: const Text('Tap to connect'),
                                  trailing: isConnecting 
                                      ? const CircularProgressIndicator()
                                      : const Icon(Icons.chevron_right, color: Colors.blue),
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
              // Display last response from BBB
              if (lastResponse.isNotEmpty)
                Container(
                  padding: const EdgeInsets.all(12),
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: Colors.green[50],
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.green),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.message, color: Colors.green),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'BBB: $lastResponse',
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                            color: Colors.green[900],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              
              const SizedBox(height: 10),
              const Text('Auto BBB Motor Control', 
                   style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.blue)),
              const SizedBox(height: 20),
              
              Text('Forward Speed: ${pwmValue.round()}%', 
                   style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
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

              const SizedBox(height: 30),
              
              Text('Turning: ${turnValue.round()}%', 
                   style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              Slider(
                value: turnValue,
                min: -100,
                max: 100,
                divisions: 200,
                label: "Maneuvering",
                activeColor: turnValue < 0 ? Colors.blue : (turnValue > 0 ? Colors.red : Colors.grey[300]),
                inactiveColor: Colors.grey[300], 
                onChanged: (value) {
                  setState(() => turnValue = value);
                  if (value < 0) {
                    sendCommand("turn_left ${(-value).round()}");
                  } else if (value > 0) {
                    sendCommand("turn_right ${value.round()}");
                  } else {
                    sendCommand("turn_dummy");
                  }
                },
                onChangeEnd: (value) {
                  double zeroValue = 0;
                  setState(() => turnValue = zeroValue);
                  sendCommand("turn_end");
                  print('Ended change on $pwmValue');
                },
              ),
              
              const SizedBox(height: 30),
              
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  ElevatedButton(
                    onPressed: () => sendCommand("brake"),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.red,
                      foregroundColor: Colors.white,
                    ),
                    child: const Text('BRAKE', style: TextStyle(fontWeight: FontWeight.bold)),
                  ),
                  ElevatedButton(
                    onPressed: () => sendCommand("status"),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blue,
                      foregroundColor: Colors.white,
                    ),
                    child: const Text('STATUS', style: TextStyle(fontWeight: FontWeight.bold)),
                  ),
                  ElevatedButton(
                    onPressed: () => sendCommand("illumination 1"),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green,
                      foregroundColor: Colors.white,
                    ),
                    child: const Text('LAMPS', style: TextStyle(fontWeight: FontWeight.bold)),
                  ),
                ],
              ),

              const SizedBox(height: 20),
              
              ElevatedButton(
                onPressed: _disconnect,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.orange,
                  foregroundColor: Colors.white,
                ),
                child: const Text('DISCONNECT'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}