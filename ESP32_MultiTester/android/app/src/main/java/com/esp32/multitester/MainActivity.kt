package com.esp32.multitester

import android.Manifest
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothSocket
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageManager
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import java.io.IOException
import java.io.InputStream
import java.io.OutputStream
import java.util.UUID

class MainActivity : AppCompatActivity() {

    private lateinit var logView: TextView
    private lateinit var connectBtn: Button
    private lateinit var readNfcBtn: Button
    private lateinit var writeNfcBtn: Button
    private lateinit var btDeauthBtn: Button
    private lateinit var pingBtn: Button
    private lateinit var inputField: EditText
    private lateinit var sendDataBtn: Button

    private var bluetoothAdapter: BluetoothAdapter? = null
    private var btSocket: BluetoothSocket? = null
    private var btOutputStream: OutputStream? = null
    private var btInputStream: InputStream? = null
    private var connectedDevice: BluetoothDevice? = null

    private val handler = Handler(Looper.getMainLooper())
    private var readThread: Thread? = null
    private var isReading = false
    private var writeModeActive = false

    companion object {
        private const val REQUEST_BLUETOOTH_PERMISSIONS = 1
        private const val REQUEST_ENABLE_BT = 2
        private val MY_UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        logView = findViewById(R.id.logView)
        connectBtn = findViewById(R.id.connectBtn)
        readNfcBtn = findViewById(R.id.readNfcBtn)
        writeNfcBtn = findViewById(R.id.writeNfcBtn)
        btDeauthBtn = findViewById(R.id.btDeauthBtn)
        pingBtn = findViewById(R.id.pingBtn)
        inputField = findViewById(R.id.inputField)
        sendDataBtn = findViewById(R.id.sendDataBtn)

        bluetoothAdapter = BluetoothAdapter.getDefaultAdapter()

        if (bluetoothAdapter == null) {
            appendLog("ERROR: Device does not support Bluetooth")
            return
        }

        checkPermissions()
        setupButtons()
    }

    private fun checkPermissions() {
        val permissions = mutableListOf<String>()
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH)
            != PackageManager.PERMISSION_GRANTED
        ) permissions.add(Manifest.permission.BLUETOOTH)
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_ADMIN)
            != PackageManager.PERMISSION_GRANTED
        ) permissions.add(Manifest.permission.BLUETOOTH_ADMIN)
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
            != PackageManager.PERMISSION_GRANTED
        ) permissions.add(Manifest.permission.ACCESS_FINE_LOCATION)
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_CONNECT)
            != PackageManager.PERMISSION_GRANTED
        ) permissions.add(Manifest.permission.BLUETOOTH_CONNECT)
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_SCAN)
            != PackageManager.PERMISSION_GRANTED
        ) permissions.add(Manifest.permission.BLUETOOTH_SCAN)

        if (permissions.isNotEmpty()) {
            ActivityCompat.requestPermissions(
                this, permissions.toTypedArray(), REQUEST_BLUETOOTH_PERMISSIONS
            )
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int, permissions: Array<String>, grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQUEST_BLUETOOTH_PERMISSIONS) {
            if (grantResults.all { it == PackageManager.PERMISSION_GRANTED }) {
                appendLog("Permissions granted")
            } else {
                appendLog("WARNING: Some permissions denied. BT may not work.")
            }
        }
    }

    private fun setupButtons() {
        connectBtn.setOnClickListener { connectToDevice() }
        readNfcBtn.setOnClickListener { sendCommand("READ_NFC") }
        writeNfcBtn.setOnClickListener {
            if (!writeModeActive) {
                writeModeActive = true
                appendLog("Enter text to write and press Send")
                inputField.visibility = EditText.VISIBLE
                sendDataBtn.visibility = Button.VISIBLE
            } else {
                val text = inputField.text.toString().trim()
                if (text.isNotEmpty()) {
                    sendCommand("WRITE_NFC:$text")
                    inputField.text.clear()
                    writeModeActive = false
                    inputField.visibility = EditText.GONE
                    sendDataBtn.visibility = Button.GONE
                } else {
                    Toast.makeText(this, "Enter text first", Toast.LENGTH_SHORT).show()
                }
            }
        }
        btDeauthBtn.setOnClickListener { showDeauthDialog() }
        pingBtn.setOnClickListener { sendCommand("PING") }
        sendDataBtn.setOnClickListener {
            val text = inputField.text.toString().trim()
            if (text.isNotEmpty()) {
                sendCommand("WRITE_NFC:$text")
                inputField.text.clear()
                writeModeActive = false
                inputField.visibility = EditText.GONE
                sendDataBtn.visibility = Button.GONE
            }
        }
    }

    private fun connectToDevice() {
        if (bluetoothAdapter?.isEnabled == false) {
            val enableIntent = Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE)
            startActivityForResult(enableIntent, REQUEST_ENABLE_BT)
            return
        }

        if (isConnected()) {
            disconnect()
            return
        }

        startDiscovery()
    }

    private fun isConnected(): Boolean {
        return btSocket?.isConnected == true
    }

    private fun disconnect() {
        try {
            isReading = false
            readThread?.interrupt()
            btInputStream?.close()
            btOutputStream?.close()
            btSocket?.close()
        } catch (_: Exception) {
        }
        btSocket = null
        btInputStream = null
        btOutputStream = null
        connectedDevice = null
        connectBtn.text = "Connect to ESP32"
        appendLog("Disconnected")
    }

    private fun startDiscovery() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_SCAN)
            != PackageManager.PERMISSION_GRANTED
        ) {
            appendLog("No BLUETOOTH_SCAN permission")
            return
        }

        appendLog("Scanning for devices...")

        val receiver = object : BroadcastReceiver() {
            override fun onReceive(context: Context, intent: Intent) {
                val action = intent.action
                if (BluetoothDevice.ACTION_FOUND == action) {
                    val device = intent.getParcelableExtra<BluetoothDevice>(BluetoothDevice.EXTRA_DEVICE)
                    if (device != null && device.name != null) {
                        showDeviceDialog(device)
                    }
                }
            }
        }

        registerReceiver(receiver, IntentFilter(BluetoothDevice.ACTION_FOUND))
        bluetoothAdapter?.startDiscovery()

        handler.postDelayed({
            try { unregisterReceiver(receiver) } catch (_: Exception) {}
            bluetoothAdapter?.cancelDiscovery()
        }, 12000)
    }

    private fun showDeviceDialog(device: BluetoothDevice) {
        val devices = mutableListOf<BluetoothDevice>()
        devices.add(device)

        val names = devices.map { "${it.name}\n${it.address}" }
        AlertDialog.Builder(this)
            .setTitle("Select ESP32 Device")
            .setItems(names.toTypedArray()) { _, which ->
                connectToESP32(devices[which])
            }
            .setNegativeButton("Cancel") { _, _ -> appendLog("Scan cancelled") }
            .show()
    }

    private fun connectToESP32(device: BluetoothDevice) {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_CONNECT)
            != PackageManager.PERMISSION_GRANTED
        ) {
            appendLog("No BLUETOOTH_CONNECT permission")
            return
        }

        appendLog("Connecting to ${device.name} (${device.address})...")

        Thread {
            try {
                val socket = device.createRfcommSocketToServiceRecord(MY_UUID)
                bluetoothAdapter?.cancelDiscovery()
                socket.connect()

                btSocket = socket
                btOutputStream = socket.outputStream
                btInputStream = socket.inputStream
                connectedDevice = device

                handler.post {
                    connectBtn.text = "Disconnect"
                    appendLog("Connected to ${device.name}")
                }

                startReading()
            } catch (e: IOException) {
                handler.post {
                    appendLog("Connection failed: ${e.message}")
                }
            }
        }.start()
    }

    private fun startReading() {
        isReading = true
        readThread = Thread {
            val buffer = ByteArray(1024)
            while (isReading && btInputStream != null) {
                try {
                    val bytes = btInputStream!!.read(buffer)
                    if (bytes > 0) {
                        val data = String(buffer, 0, bytes)
                        handler.post { appendLog(data) }
                    }
                } catch (e: IOException) {
                    if (isReading) {
                        handler.post { appendLog("Connection lost: ${e.message}") }
                    }
                    break
                }
            }
        }
        readThread?.start()
    }

    private fun sendCommand(command: String) {
        if (!isConnected()) {
            appendLog("ERROR: Not connected to ESP32")
            return
        }

        appendLog(">> $command")

        Thread {
            try {
                btOutputStream?.write((command + "\n").toByteArray())
                btOutputStream?.flush()
            } catch (e: IOException) {
                handler.post { appendLog("Send failed: ${e.message}") }
            }
        }.start()
    }

    private fun showDeauthDialog() {
        if (!isConnected()) {
            appendLog("ERROR: Not connected to ESP32")
            return
        }

        AlertDialog.Builder(this)
            .setTitle("WARNING: Bluetooth Deauth")
            .setMessage(
                "Using Bluetooth deauthentication on devices you do not own\n" +
                        "is ILLEGAL in most jurisdictions.\n\n" +
                        "This is for EDUCATIONAL PURPOSES only.\n" +
                        "Use ONLY on devices you own!\n\n" +
                        "Enter target MAC address:"
            )
            .setView(EditText(this).apply {
                hint = "XX:XX:XX:XX:XX:XX"
                inputType = android.text.InputType.TYPE_CLASS_TEXT
            })
            .setPositiveButton("Send") { _, _ ->
                val editText = (this as? AlertDialog)?.findViewById<EditText>(android.R.id.custom)
                val mac = editText?.text?.toString()?.trim()
                if (mac != null && mac.isNotEmpty()) {
                    sendCommand("BT_DEAUTH:$mac")
                }
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    private fun appendLog(message: String) {
        logView.append("$message\n")
        // Auto-scroll to bottom
        val scroll = logView.layout
        if (scroll != null) {
            val scrollAmount = scroll.getLineTop(logView.lineCount) - logView.height
            if (scrollAmount > 0) {
                logView.scrollTo(0, scrollAmount)
            } else {
                logView.scrollTo(0, 0)
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        disconnect()
    }
}
