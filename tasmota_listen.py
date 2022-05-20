#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from gmqtt import Client as MQTTClient
import math
import asyncio
import signal
from time import time
import json
from dateutil.parser import isoparse
from dateutil.tz import gettz
from datetime import datetime
import uvloop
import os
from tasmota_configuration import tasmota_id, host, port, user, pwrd, data_dir, tasmota_to_acp_id

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

STOP = asyncio.Event()

# db is where captured data is stored, indexed by device identifier (called 'acp_id' in our code)
db = {}

# hacky global variable to keep track of most recent tasmota power reading
latest_tasmota_msg = None

def get_stats(xs):
    avgx = sum(xs) / len(xs)
    minx = min(xs)
    maxx = max(xs)
    stdx = math.sqrt(sum([(x - avgx)**2 for x in xs])/len(xs))
    return {'avg': avgx, 'min': minx, 'max': maxx, 'std': stdx}

# useful line for debugging:
#    print("{}: n={} avg={:.2f}ms min={:.2f}ms max={:.2f}ms std={:.2f}ms".format(prefix, len(times), avgdt, mindt, maxdt, stddt))


# Used by the deepdish example
def dump_stats(msgs):
    frame_count = 0
    timings = {}
    temps = []
    powers = []
    for m in msgs:
        if m['acp_event'] == 'frame':
            frame_count+=1
            for k,t in m['timing'].items():
                if k not in timings: timings[k] = []
                timings[k].append(t)
            temps.append(m['temp'])
        elif m['acp_event'] == 'tasmota':
            powers.append(m['ENERGY']['Power'])

    for k,ts in timings.items():
        print(k, get_stats(ts))
    print('temp', get_stats(temps))
    print('power', get_stats(powers))

def on_connect(client, flags, rc, properties):
    print('Connected')
    client.subscribe(f'tele/{tasmota_id}/SENSOR', qos=0)
    # Example (also see below)
    #client.subscribe(f'deepdish/#', qos=0)

async def on_message(client, topic, payload, qos, properties):
    global latest_tasmota_msg
    # Tasmota power sensor message processing. The topic is expected
    # to be: 'tele/<tasmota_id>/SENSOR'. We later convert tasmota_id
    # into acp_id for lookup in the db.
    if topic.startswith('tele') and topic.endswith('SENSOR'):
        t_id = topic[5:-7]
        try:
            msg = json.loads(payload)
            t = msg['Time']
            msg['acp_ts'] = isoparse(t).timestamp()
            msg['acp_event'] = 'tasmota'
            msg['received_ts'] = str(time())
            e = msg['ENERGY']
            w = e['Voltage'] * e['Current'] * e['Factor']

            # Find the currently running entry in the database and add
            # a tasmota-power-reading entry to it. The
            # tasmota_to_acp_id dictionary maps tasmota sensor
            # identifiers to their associated test harness sensor. In
            # other words, it maps the tasmota power sensor to the
            # experimental sensor that is receiving the power.
            if t_id in tasmota_to_acp_id:
                acp_id = tasmota_to_acp_id[t_id]
                if acp_id in db:
                    db[acp_id]['tasmota'].append(msg)
            latest_tasmota_msg = msg
            print('{}: {} {} {:.2f} W {:.2f} W'.format(topic, t, msg['acp_ts'], w, e['Power']))
        except:
            print(topic, payload)

    # Example of gathering data from experimental harness that sends
    # MQTT messages with the topic 'deepdish/...'

    # An important thing it does is to create an entry in the 'db'
    # dictionary as 'db[acp_id]' where acp_id is a unique identifier
    # for the sensor sending out our test data. It then creates a list
    # inside of the entry called db[acp_id]['tasmota'], and that is
    # where the tasmota readings will be stored. If you want to change
    # that then you should also change the code above that is
    # currently .append()ing into that list.

    # Another important thing it does is save the data when the
    # experiment concludes. See the 'shutdown' event.

    #    if topic.startswith('deepdish'):
    #        msg = json.loads(payload)
    #        if 'acp_id' in msg:
    #            id = msg['acp_id']
    #            event = msg['acp_event']
    #            msg['received_ts'] = str(time())
    #            if event == 'initialisation':
    #                db[id] = {'frames': [], 'init': msg, 'tasmota': [latest_tasmota_msg] if latest_tasmota_msg else []}
    #            elif event == 'frame':
    #                db[id]['frames'].append(msg)
    #            elif event == 'shutdown':
    #                # Save gathered data
    #                db[id]['shutdown'] = msg
    #                msgdir = os.path.join(data_dir, id, datetime.fromtimestamp(float(db[id]['init']['received_ts'])).strftime('%Y-%m-%d_%H:%M:%S'))
    #                os.makedirs(msgdir, exist_ok=True)
    #                dbfile = os.path.join(msgdir, 'db.json')
    #                with open(dbfile, 'w') as f:
    #                    json.dump(db[id], f, indent=2)
    #                all_msgs = [db[id]['init'], db[id]['shutdown']] + db[id]['frames'] + db[id]['tasmota']
    #                all_msgs.sort(key=lambda m: m['received_ts'])
    #                #print(json.dumps(db[id],indent=2))
    #                # for m in all_msgs:
    #                #     print(json.dumps(m,indent=2))
    #                dump_stats(all_msgs)


    return 0


def on_disconnect(client, packet, exc=None):
    print('Disconnected')

def on_subscribe(client, mid, qos, properties):
    print('SUBSCRIBED')

def ask_exit(*args):
    STOP.set()

async def main():
    client = MQTTClient("tasmota_listen")

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.on_subscribe = on_subscribe
    client.set_config({'reconnect_retries': 10, 'reconnect_delay': 1})
    client.set_auth_credentials(user, pwrd)
    await client.connect(host, port)

    tz = datetime.now(gettz()).strftime('%z')
    tz = tz[:3] + ':' + tz[3:]
    t = str(int(time()))

    # Some configuration of the power sensor. These can also be
    # configured on the sensor's 'command line' that can be found in
    # the sensor's web-based admin portal.

    # 1. Change sensor's timezone to this machine's timezone setting.
    client.publish(f'cmnd/{tasmota_id}/TimeZone', tz, qos=1)
    # 2. Set the clock on the sensor.
    client.publish(f'cmnd/{tasmota_id}/TIME', t, qos=1)
    # 3. Ask for wattage information to 2 decimal places.
    client.publish(f'cmnd/{tasmota_id}/WattRes', '2', qos=1)
    # 4. Ask for the sensor to publish MQTT updates whenever the power reading changes by 0.1 W or more.
    client.publish(f'cmnd/{tasmota_id}/PowerDelta', '1', qos=1)

    await STOP.wait() # Wait for the stop signal.
    await client.disconnect()
    # Terminate.

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGINT, ask_exit)
    loop.add_signal_handler(signal.SIGTERM, ask_exit)
    loop.run_until_complete(main())
