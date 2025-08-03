import time
import json
import spidev  # SPI interface
import socket
import paho.mqtt.client as mqtt

# MQTT Configuration
MQTT_BROKER = "34.227.178.72"
MQTT_PORT = 1883
MQTT_TOPIC = "sensor/soil"
MQTT_CLIENT_ID = f"soil-sensor-{socket.gethostname()}"

# Setup SPI for MCP3008
spi = spidev.SpiDev()
spi.open(0, 0)  # Bus 0, Device 0 (CE0)
spi.max_speed_hz = 1350000

def read_adc(channel):
    """Read SPI data from MCP3008 (0-7)."""
    if not 0 <= channel <= 7:
        raise ValueError("ADC channel must be between 0 and 7")
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    value = ((adc[1] & 3) << 8) + adc[2]
    return value

# Connect to MQTT
client = mqtt.Client(MQTT_CLIENT_ID)
client.connect(MQTT_BROKER, MQTT_PORT, 60)

def read_soil_sensor():
    adc_value = read_adc(0)  # Read from CH0
    percent = round((1023 - adc_value) / 1023 * 100, 2)  # Convert to %
    return {
        "hostname": socket.gethostname(),
        "moisture_raw": adc_value,
        "moisture_percent": percent,
        "timestamp": time.time()
    }

try:
    while True:
        data = read_soil_sensor()
        payload = json.dumps(data)
        result = client.publish(MQTT_TOPIC, payload)
        status = result[0]
        if status == 0:
            print(f"Sent soil data: {payload}")
        else:
            print("MQTT publish failed.")
        time.sleep(10)
except KeyboardInterrupt:
    print("Stopping sensor...")
    spi.close()
    client.disconnect()
