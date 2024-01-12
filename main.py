# TinyTuya Example
# -*- coding: utf-8 -*-
"""
 TinyTuya - Example script to monitor state changes with Tuya devices.

 Author: Jason A. Cox
 For more information see https://github.com/jasonacox/tinytuya

"""
import tinytuya
import time
import json
import os

# tinytuya.set_debug(True)

# Check if device.json exists
DEVICE = None
if os.path.isfile('device.json'):
    with open('device.json') as json_file:
        DEVICE = json.load(json_file)
        print(" > Loaded device.json <")

print(" Device ID: %r" % DEVICE['id'])

# Setting the address to 'Auto' or None will trigger a scan which will auto-detect both the address and version, but this can take up to 8 seconds
d = tinytuya.OutletDevice(DEVICE['id'],
                          'Auto',
                          DEVICE['key'],
                          persist=True)
d.set_version(DEVICE['version'])

# If you know both the address and version then supplying them is a lot quicker
# d = tinytuya.OutletDevice('DEVICEID', 'DEVICEIP', 'DEVICEKEY', version=DEVICEVERSION, persist=True)

STATUS_TIMER = 30
KEEPALIVE_TIMER = 12

DEVICE_MAPPING = DEVICE['mapping']
AvailableDPS = d.detect_available_dps()

for key in list(DEVICE_MAPPING):
    # check if not available
    if key not in AvailableDPS:
        print("Warning: %r is not available on this device, ignoring" % DEVICE_MAPPING[key]['code'])
        del DEVICE_MAPPING[key]

def map_status(status):
    if status is None or 'dps' not in status: return status
    status = status['dps']
    mapped = {}
    for key in DEVICE_MAPPING:
        map_info = DEVICE_MAPPING[key]
        code = map_info['code']
        if key in status:
            mapped[code] = status[key]
        else:

            mapped[key] = None
            print("Missing key %r in status" % key)
    return mapped


print(" > Send Request for Status < ")
data = d.status()
data = map_status(data)
print('Initial Status: %r' % data)
if data and 'Err' in data:
    print("Status request returned an error, is version %r and local key %r correct?" % (d.version, d.local_key))

print(" > Begin Monitor Loop <")
heartbeat_time = time.time() + KEEPALIVE_TIMER
status_time = None

# Uncomment if you want the monitor to constantly request status - otherwise you
# will only get updates when state changes
status_time = time.time() + STATUS_TIMER

while (True):
    if status_time and time.time() >= status_time:
        # Uncomment if your device provides power monitoring data but it is not updating
        # Some devices require a UPDATEDPS command to force measurements of power.
        # print(" > Send DPS Update Request < ")
        # Most devices send power data on DPS indexes 18, 19 and 20
        # d.updatedps(['18','19','20'], nowait=True)
        # Some Tuya devices will not accept the DPS index values for UPDATEDPS - try:
        # payload = d.generate_payload(tinytuya.UPDATEDPS)
        # d.send(payload)

        # poll for status
        print(" > Send Request for Status < ")
        data = d.status()
        data = map_status(data)
        status_time = time.time() + STATUS_TIMER
        heartbeat_time = time.time() + KEEPALIVE_TIMER
    elif time.time() >= heartbeat_time:
        # send a keep-alive
        data = d.heartbeat(nowait=False)
        heartbeat_time = time.time() + KEEPALIVE_TIMER
    else:
        # no need to send anything, just listen for an asynchronous update
        data = d.receive()

        data = map_status(data)

    print('Received Payload: %r' % data)

    if data and 'Err' in data:
        print("Received error!")
        # rate limit retries so we don't hammer the device
        time.sleep(5)
