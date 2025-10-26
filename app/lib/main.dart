import 'package:flutter/material.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:permission_handler/permission_handler.dart';
import 'dart:convert';

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
  // BLE Variables
  BluetoothDevice? connectedDevice;
  BluetoothCharacteristic? rxCharacteristic;
  bool isScanning = false;
  bool isConnected = false;
  List<BluetoothDevice> devicesList = [];
  double pwmValue = 0;

  // Your BBB UUIDs
  final String SERVICE_UUID = '6E400001-B5A3-F393-E0A9-E50E24DCCA9E';
  final String RX_UUID = '6E400002-B5A3-F393-E0A9-E50E24DCCA9E';

  @override
  void initState() {
    super.initState();
    _requestPermissions();
  }

  Future<void> _requestPermissions() async {
    await Permission.bluetooth.request();
    await Permission.bluetoothScan.request();
    await Permission.bluetoothConnect.request();
  }

  Future<void> scanForDevices() async {
    setState(() {
      isScanning = true;
      devicesList.clear();
    });

    FlutterBluePlus.startScan(timeout: Duration(seconds: 4));

    FlutterBluePlus.scanResults.listen((results) {
      for (ScanResult result in results) {
        if (result.device.name.isNotEmpty && 
            result.device.name.contains('BBB')) {
          if (!devicesList.contains(result.device)) {
            setState(() {
              devicesList.add(result.device);
            });
          }
        }
      }
    });

    await Future.delayed(Duration(seconds: 4));
    FlutterBluePlus.stopScan();
    setState(() => isScanning = false);
  }

  Future<void> connectToDevice(BluetoothDevice device) async {
    try {
      print('🔵 Attempting to connect to: ${device.name}');
      
      await device.connect(
        timeout: const Duration(seconds: 15),
        autoConnect: false,
      );
      
      print('✅ Connected to device: ${device.name}');
      
      setState(() {
        connectedDevice = device;
        isConnected = true;
      });

      // Discover services
      print('🔍 Discovering services...');
      List<BluetoothService> services = await device.discoverServices();
      print('📋 Found ${services.length} services');
      
      bool serviceFound = false;
      bool characteristicFound = false;
      
      for (BluetoothService service in services) {
        print('🔧 Service UUID: ${service.uuid.toString().toUpperCase()}');
        
        if (service.uuid.toString().toUpperCase() == SERVICE_UUID.toUpperCase()) {
          print('✅ Found target service!');
          serviceFound = true;
          
          for (BluetoothCharacteristic characteristic in service.characteristics) {
            print('📝 Characteristic UUID: ${characteristic.uuid.toString().toUpperCase()}');
            
            if (characteristic.uuid.toString().toUpperCase() == RX_UUID.toUpperCase()) {
              rxCharacteristic = characteristic;
              characteristicFound = true;
              print('✅ Found RX characteristic!');
              
              // Check characteristic properties
              print('📊 Characteristic properties:');
              print('   Write: ${characteristic.properties.write}');
              print('   WriteWithoutResponse: ${characteristic.properties.writeWithoutResponse}');
              print('   Read: ${characteristic.properties.read}');
              print('   Notify: ${characteristic.properties.notify}');
              
              break;
            }
          }
        }
      }
      
      if (!serviceFound) {
        print('❌ Target service not found');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('❌ BBB service not found. Check UUIDs.')),
        );
      } else if (!characteristicFound) {
        print('❌ RX characteristic not found');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('❌ RX characteristic not found')),
        );
      } else {
        print('🎉 Ready to send commands!');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('🎉 Connected and ready!')),
        );
      }
      
    } catch (e) {
      print('❌ Connection error: $e');
      setState(() {
        isConnected = false;
        connectedDevice = null;
        rxCharacteristic = null;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('❌ Connection failed: $e')),
      );
    }
  }

  Future<void> sendCommand(String command) async {
    print('🔴 DEBUG: sendCommand called with: $command');
    print('🔴 DEBUG: isConnected = $isConnected');
    print('🔴 DEBUG: rxCharacteristic = $rxCharacteristic');
    
    if (!isConnected) {
      print('❌ Not connected to device');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('❌ Not connected to BBB')),
      );
      return;
    }
    
    if (rxCharacteristic == null) {
      print('❌ RX Characteristic not found');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('❌ Bluetooth characteristic not ready')),
      );
      return;
    }
    
    try {
      List<int> bytes = utf8.encode(command);
      print('🔵 Sending bytes: $bytes');
      
      await rxCharacteristic!.write(bytes, withoutResponse: false);
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('BBB Controller'),
        backgroundColor: Colors.blue,
      ),
      body: Padding(
        padding: EdgeInsets.all(16.0),
        child: Column(
          children: [
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
                    isConnected ? 'Connected to BBB' : 'Not Connected',
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
                child: Text(isScanning ? 'Scanning...' : 'Scan for BBB'),
              ),
              
              // Device List
              if (devicesList.isNotEmpty)
                Container(
                  height: 100,
                  child: ListView.builder(
                    itemCount: devicesList.length,
                    itemBuilder: (context, index) {
                      return ListTile(
                        title: Text(devicesList[index].name),
                        subtitle: Text(devicesList[index].id.toString()),
                        onTap: () => connectToDevice(devicesList[index]),
                      );
                    },
                  ),
                ),
            ],
            
            // Control Buttons (only show when connected)
            if (isConnected) ...[
              Text('LED Control', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              SizedBox(height: 10),
              
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  ElevatedButton(
                    onPressed: () => sendCommand("lamps"),
                    child: Text('LED ON'),
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                  ),
                  ElevatedButton(
                    onPressed: () => sendCommand("status"),
                    child: Text('STATUS'),
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.blue),
                  ),
                ],
              ),
              
              SizedBox(height: 20),
              
              ElevatedButton(
                onPressed: () => sendCommand("ping"),
                child: Text('PING BBB'),
                style: ElevatedButton.styleFrom(backgroundColor: Colors.orange),
              ),
              
              SizedBox(height: 20),
              
              Text('PWM Control: ${pwmValue.round()}%', 
                   style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              Slider(
                value: pwmValue,
                min: 0,
                max: 100,
                divisions: 100,
                onChanged: (value) {
                  setState(() => pwmValue = value);
                  sendCommand("left ${value.round()}");
                },
              ),
              
              SizedBox(height: 20),
              
              ElevatedButton(
                onPressed: () => sendCommand("right 50"),
                child: Text('RIGHT PWM'),
                style: ElevatedButton.styleFrom(backgroundColor: Colors.purple),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
