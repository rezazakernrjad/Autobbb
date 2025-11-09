# 🔧 BBB Controller Debugging Guide

## 🎯 Problem: Buttons don't send commands to BBB

Since your app launches and connects but buttons don't work, here's how to debug:

## 📱 Step 1: Check Flutter App Debug Output

After I updated your app with debugging, you should see detailed messages when:
1. **Connecting to BBB** - Check if service/characteristic are found
2. **Pressing buttons** - See exactly what happens when you tap

### In your Flutter terminal/Xcode console, look for:

**Good Connection Messages:**
```
✅ Connected to device: BBB-PosServer
🔍 Discovering services...
📋 Found X services
✅ Found target service!
✅ Found RX characteristic!
🎉 Ready to send commands!
```

**Button Press Messages:**
```
🔴 DEBUG: sendCommand called with: ping
🔴 DEBUG: isConnected = true
🔴 DEBUG: rxCharacteristic = [characteristic info]
🔵 Sending bytes: [112, 105, 110, 103]
✅ Successfully sent: ping
```

**Bad Messages to Watch For:**
```
❌ Target service not found
❌ RX characteristic not found
❌ Not connected to device
❌ Send failed: [error]
```

## 🖥️ Step 2: Check BBB Server Status

On your BBB, make sure you're running the RIGHT server:

### ✅ Correct Server (what you should run):
```bash
cd /path/to/your/project/src
python3 auto_run.py
```

### Expected BBB Output:
```
Starting Bluetooth Server...
✓ BLE server is now advertising and ready for connections
Service UUID: 6E400001-B5A3-F393-E0A9-E50E24DCCA9E
RX UUID: 6E400002-B5A3-F393-E0A9-E50E24DCCA9E
Device Name: BBB-PosServer
Waiting for iPhone to connect...
```

### When iPad connects, you should see:
```
Device connected: [device_path]
BBB is now connected to iPhone
```

### When commands arrive, you should see:
```
📱 Received from iPhone: ping
⏰ Time: 14:23:45
🔄 Processing command: ping
🏓 Ping received
📤 Sending to iPhone: PONG
```

## 🔍 Step 3: Common Issues & Solutions

### Issue 1: Service/Characteristic Not Found
**Flutter shows:** `❌ Target service not found`

**Solution:** UUIDs don't match
- Check BBB server uses these UUIDs:
  - Service: `6E400001-B5A3-F393-E0A9-E50E24DCCA9E`  
  - RX: `6E400002-B5A3-F393-E0A9-E50E24DCCA9E`

### Issue 2: Connected but No Commands Received
**Flutter shows:** `✅ Successfully sent: ping`
**BBB shows:** Nothing

**Solutions:**
1. **Wrong BBB server running** - Make sure it's `src/auto_run.py` not warmups version
2. **Characteristic write mode** - Try both `write()` and `writeWithoutResponse()`
3. **BBB not listening** - Restart BBB server

### Issue 3: BBB Gets Commands but Doesn't Respond
**BBB shows:** `📱 Received from iPhone: ping`
**Flutter shows:** Send successful but no response

**This is actually OK** - The main goal is BBB receiving commands!

## 🧪 Step 4: Test Sequence

1. **Start BBB Server:**
   ```bash
   python3 src/auto_run.py
   ```

2. **Launch Flutter App** and check connection debug messages

3. **Test Commands in Order:**
   - `ping` (simplest test)
   - `status` (BBB status)
   - `lamps` (LED control)
   - `left 50` (PWM test)

4. **Monitor Both Sides:**
   - Flutter console for send confirmations
   - BBB terminal for received commands

## 🎯 Expected Working Flow

```
iPad App                    BBB Server
├─ Tap PING button     →   📱 Received: ping
├─ Tap LED ON         →   📱 Received: lamps  
├─ Move PWM slider    →   📱 Received: left 75
└─ Tap RIGHT PWM      →   📱 Received: right 50
```

## 🚨 Quick Fixes to Try

### If nothing works:
```bash
# On BBB - restart server
sudo systemctl restart bluetooth
python3 src/auto_run.py

# On iPad - reconnect app
# Close app, restart, scan & reconnect
```

### If commands don't arrive at BBB:
1. Check BBB advertises as "BBB-PosServer"
2. Verify Flutter finds the correct service UUID
3. Try different write modes in Flutter app

The updated app now has extensive debugging - check the console output to see exactly where the communication breaks down!