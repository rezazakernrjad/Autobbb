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
      await device.connect(
        //timeout: const Duration(seconds: 10),
        autoConnect: true,
        mtu:null
        //License: license.free,
      );
      setState(() {
        connectedDevice = device;
        isConnected = true;
      });

      // Discover services
      List<BluetoothService> services = await device.discoverServices();
      
      for (BluetoothService service in services) {
        if (service.uuid.toString().toUpperCase() == SERVICE_UUID.toUpperCase()) {
          for (BluetoothCharacteristic characteristic in service.characteristics) {
            if (characteristic.uuid.toString().toUpperCase() == RX_UUID.toUpperCase()) {
              rxCharacteristic = characteristic;
              break;
            }
          }
        }
      }
    } catch (e) {
      print('Connection error: $e');
    }
  }

  Future<void> sendCommand(String command) async {
    if (rxCharacteristic != null) {
      try {
        List<int> bytes = utf8.encode(command);
        await rxCharacteristic!.write(bytes);
        print('Sent: $command');
      } catch (e) {
        print('Send error: $e');
      }
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
                    onPressed: () => sendCommand("pin 1"),
                    child: Text('LED ON'),
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                  ),
                  ElevatedButton(
                    onPressed: () => sendCommand("pin 0"),
                    child: Text('LED OFF'),
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
                  ),
                ],
              ),
              
              SizedBox(height: 20),
              
              ElevatedButton(
                onPressed: () => sendCommand("pin 2"),
                child: Text('Start Motor'),
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
                  sendCommand("pwmb ${value.round()}");
                },
              ),
              
              SizedBox(height: 20),
              
              ElevatedButton(
                onPressed: () => sendCommand("pwma"),
                child: Text('PWM Demo'),
                style: ElevatedButton.styleFrom(backgroundColor: Colors.purple),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
