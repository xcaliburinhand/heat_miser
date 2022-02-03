import copy
import csv
import datetime
import json
import logging
import os
import time

logging.basicConfig(level=logging.INFO)
os.environ['TZ'] = 'US/Eastern'
now = datetime.datetime.fromtimestamp(time.time())

fields = ['time', 'burner']
cols = [
        {"id": "", "label": "Zone", "pattern": "", "type": "string"},
        {"id": "", "label": "Equipment Start", "pattern": "", "type": "date"},
        {"id": "", "label": "Equipment Stop", "pattern": "", "type": "date"}
    ]

config_path = "/etc/heatmiser/config.json"
config_env = os.environ.get('HEATMISER_CONFIG')
if config_env is not None:
    config_path = config_env
with open(config_path) as configfile:
    config = json.load(configfile)

for zone in sorted(config['zones']):
    fields.append(str(zone))

therms = []
for therm in sorted(config['thermostats']):
    fields.append(str(therm))
    therms.append(str(therm))

equip = copy.copy(fields)
equip.remove('time')

form = "%Y-%m-%d %H:%M"


def build_date(stamp):
    yr = datetime.datetime.strptime(stamp, form).strftime('Date(%Y, ')
    mnth = str(datetime.datetime.strptime(stamp, form).month-1)
    tail = datetime.datetime.strptime(stamp, form).strftime(', %d, %H, %M)')
    return yr + mnth + tail


def datapoint_item(title, seg_start, seg_end):
    return {"c": [
                {"v": title, "f": None},
                {"v": build_date(seg_start), "f": None},
                {"v": build_date(seg_end), "f": None}
            ]}


def calc_burner_time(start_time, end_time):
    return (
        datetime.datetime.strptime(end_time, form) -
        datetime.datetime.strptime(start_time, form)).total_seconds()/60


status_store = {}
call_store = {}
device_usage = {}
rows = []
calls = []
burner_time = 0

datefilename = now.strftime('%Y%m%d')

with open(os.path.dirname(
    os.path.realpath(__file__)) +
    '/run_data/' +
    datefilename+'.csv'
) as csvfile:
    reader = csv.DictReader(csvfile, fieldnames=fields)
    for row in reader:
        logging.debug(row)
        for device in equip:
            logging.debug("row value for %s is %s", device, row[device])
            if row[device] == '0':
                # device is now off, close out runtime bar
                logging.debug("status_store: %s", status_store)

                if device not in status_store or status_store[device] is None:
                    # device is already off nothing to process
                    logging.debug('%s is not on in status_store', device)
                    continue

                logging.debug(
                    'writing data point and changing %s to off in status_store',
                    device)
                datapoint = datapoint_item(
                    device.title(),
                    status_store[device],
                    row['time'])
                if device.lower() == 'burner':
                    calls.append(datapoint)
                    burner_time += calc_burner_time(
                        status_store[device],
                        row['time'])
                else:
                    rows.append(datapoint)
                status_store[device] = None  # mark device off
            elif row[device] == '1':
                device_usage[device] = 1
                if device not in therms and device.lower() != 'burner':
                    call_store[row['time']] = 1
                if device not in status_store or status_store[device] is None:
                    # store device start time
                    logging.debug('setting %s to on in status_store', device)
                    status_store[device] = row['time']
        last_time = row['time']

# drain status_store, complete any "on" devices
for device in equip:
    if device not in status_store or status_store[device] is None:
        continue

    datapoint = datapoint_item(
        device.title(),
        status_store[device],
        last_time)
    if device.lower() == 'burner':
        calls.append(datapoint)
        burner_time += calc_burner_time(
            status_store[device],
            last_time)
    else:
        rows.append(datapoint)

# ensure all devices are added to table
for device in equip:
    if device in device_usage:
        # device already in table
        continue

    datapoint = datapoint_item(
        device.title(),
        now.strftime('%Y-%m-%d 00:00'),
        now.strftime('%Y-%m-%d 00:00'))
    if device.lower() == 'burner':
        calls.append(datapoint)
    else:
        rows.append(datapoint)

# no heat calls
if len(device_usage.keys()) == 0:
    calls.append(datapoint_item(
        'Heat Call',
        now.strftime('%Y-%m-%d 00:00'),
        now.strftime('%Y-%m-%d 00:00')))

# any device on results in call_store[timestamp] = 1
calllist = call_store.keys()
calllist = sorted(calllist)
logging.debug(calllist)
end = None
if calllist:
    calllist_end = calllist[-1]
for calltime in calllist:
    if end is None:
        # list start
        beg = calltime
        end = calltime
        continue

    seconds_diff = (
        datetime.datetime.strptime(calltime, form) -
        datetime.datetime.strptime(end, form)).total_seconds()

    if seconds_diff == 60 and calltime != calllist_end:
        # no transition, update end
        end = calltime
        continue

    # break between data points or end of list
    logging.debug(seconds_diff)
    calls.append(datapoint_item(
        "Heat Call",
        beg,
        (datetime.datetime.strptime(end, form) +
            datetime.timedelta(minutes=1)).strftime(form)
    ))
    beg = calltime
    end = calltime

# add spacer
rows.append(datapoint_item(
    " ",
    now.strftime('%Y-%m-%d 00:00'),
    now.strftime('%Y-%m-%d 00:00')
))

# append rollups to table
rows += calls

dataTable = {"cols": cols, "rows": rows}
logging.debug(dataTable)
with open(config['data_dir']+'/'+datefilename+'.json', 'w') as out:
    json.dump(dataTable, out)

dataTable = {
    "cols": cols,
    "rows": calls,
    "burner_runtime": burner_time,
    "query_ecobee": config['query_ecobee']}
with open(config['data_dir']+'/'+datefilename+'_overall.json', 'w') as out:
    json.dump(dataTable, out)
